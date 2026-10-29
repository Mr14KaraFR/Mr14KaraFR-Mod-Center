"""Local diagnostics for the packaged application; never installs or modifies mods."""
import json
import os
from pathlib import Path
import sys
import ssl
import traceback

from core import APP_VERSION, load_catalog, status
from tls_support import tls_context


def read_settings(config_path=None):
    here = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    config = Path(config_path) if config_path else Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "Mr14KaraFR/ModCenter/settings.json"
    settings = json.loads((here / "channel.json").read_text(encoding="utf-8-sig"))
    if config.is_file():
        settings.update(json.loads(config.read_text(encoding="utf-8-sig")))
    return settings


def diagnose(destination, config_path=None, tls_only=False):
    report = {"version": APP_VERSION, "frozen": bool(getattr(sys, "frozen", False)), "stage": "tls"}
    try:
        context = tls_context()
        report["trusted_ca_certificates"] = context.cert_store_stats()["x509_ca"]
        report["mozilla_ca_bundle_included"] = True
        report["tls_verified"] = context.check_hostname and context.verify_mode == ssl.CERT_REQUIRED
        if not report["tls_verified"]:
            raise RuntimeError("La vérification des certificats HTTPS doit rester active.")
        if not tls_only:
            report["stage"] = "settings"
            settings = read_settings(config_path)
            report["stage"] = "catalogue"
            mods = load_catalog(settings["catalog_url"])
            report["stage"] = "installed_mods"
            report["mods"] = [{"id": m["id"], "available_version": m["version"],
                                "status": status(settings.get("mods_dir", ""), m)} for m in mods]
        report.update(success=True, stage="complete")
    except Exception as exc:
        report.update(success=False, error_type=type(exc).__name__, error=str(exc), traceback=traceback.format_exc())
    if str(destination) != "-":
        target = Path(destination)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0 if report["success"] else 1
