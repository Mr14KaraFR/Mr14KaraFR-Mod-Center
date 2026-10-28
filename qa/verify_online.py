"""Verify the public release by installing only into a dedicated QA folder."""
import hashlib
import json
from pathlib import Path
import tempfile
from unittest.mock import patch
import zipfile

from core import install, load_catalog, open_source, sha256, status

ROOT = Path(__file__).resolve().parents[1]
BASE = "https://github.com/Mr14KaraFR/Mr14KaraFR-Mod-Center/releases"


def verify():
    report = {"catalog_url": BASE + "/latest/download/catalog.json", "mods": [], "real_game_modified": False}
    mods = load_catalog(report["catalog_url"])
    if len(mods) != 4:
        raise ValueError("The public catalogue must contain four mods")
    qa_root = ROOT / "outputs/mod-center-online-qa"
    qa_root.mkdir(parents=True, exist_ok=True)
    folder = Path(tempfile.mkdtemp(prefix="verified-", dir=qa_root)) / "mods"
    folder.mkdir()
    folder.resolve().relative_to(qa_root.resolve())
    # Only a new, empty QA directory can bypass the real-game process check.
    # The user's actual mods directory is never read or modified by this script.
    with patch("core.game_running", return_value=False):
        for mod in mods:
            install(folder, mod)
            if status(folder, mod)[0] != "À jour":
                raise ValueError("Downloaded mod was not recognized as installed")
            report["mods"].append(dict(id=mod["id"], version=mod["version"], url=mod["url"],
                                       sha256=sha256(folder / mod["filename"]), installed_status="À jour"))
            print("Downloaded, verified and installed in QA:", mod["id"], mod["version"], flush=True)
    release_base = mods[0]["url"].rsplit("/", 1)[0]
    with open_source(release_base + "/SHA256SUMS.txt") as stream:
        sums = stream.read(10000).decode("ascii")
    checksums = {name: digest for digest, name in (line.split() for line in sums.splitlines())}
    app_names = [name for name in checksums if name.startswith("Mr14KaraFR_Mod_Center_") and name.endswith("_Windows.zip")]
    if len(app_names) != 1:
        raise ValueError("Missing Windows app checksum")
    name = app_names[0]
    download = folder.parent / name
    with open_source(release_base + "/" + name) as source, download.open("wb") as target:
        total = 0
        while block := source.read(256 * 1024):
            total += len(block)
            if total > 100 * 1024 * 1024:
                raise ValueError("Unexpected application size")
            target.write(block)
    if sha256(download) != checksums[name]:
        raise ValueError("Application checksum mismatch")
    with zipfile.ZipFile(download) as archive:
        if archive.testzip() is not None:
            raise ValueError("Damaged application archive")
        channel = json.loads(archive.read("Mr14KaraFR-Mod-Center/_internal/channel.json"))
        if channel["catalog_url"] != report["catalog_url"]:
            raise ValueError("Public application channel mismatch")
    report.update(application=dict(filename=name, sha256=checksums[name], bytes=download.stat().st_size),
                  qa_directory=str(folder), success=True)
    (ROOT / "outputs/mod-center-online-validation.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print("Public application verified:", name)
    return report


if __name__ == "__main__":
    verify()
