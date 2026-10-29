"""Prepare a release directory. This command does not upload anything."""
import argparse
import json
from pathlib import Path
import shutil
import zipfile
from core import archive_info, sha256, version, check_url

PROJECT = Path(__file__).resolve().parents[1]
MODS = [
    ("mr14karaecu", "ECU Studio", "Mr14KaraFR_Programmable_ECU.zip",
     "Calculateur moteur et cartographies personnalisées."),
    ("mr14karaairsuspension", "Suspension pneumatique", "Mr14KaraFR_Air_Suspension.zip",
     "Suspension réglable, profils et commandes pneumatiques."),
    ("mr14karadieselsmoke", "Fumée diesel volumétrique", "Mr14KaraFR_Diesel_Volumetric.zip",
     "Fumée diesel volumétrique et effets d’échappement."),
    ("volumetricbackfire", "Flammes & détonations HQ", "volumetric_backfire_HQ.zip",
     "Flammes volumétriques, retours de flamme et effets sonores."),
]


def publish(output, base_url="", notes="", source=PROJECT):
    output = Path(output).resolve()
    if base_url:
        check_url(base_url)
    output.mkdir(parents=True, exist_ok=True)
    entries = []
    for ident, name, filename, description in MODS:
        path = Path(source) / filename
        info = archive_info(path, ident)
        version(info["version"])
        with zipfile.ZipFile(path) as archive:
            if archive.testzip() is not None:
                raise ValueError(f"ZIP endommagé : {filename}")
        digest = sha256(path)
        # Immutable paths: old clients never see a ZIP from a newer catalogue.
        asset = f"{ident}-{info['version']}-{digest[:12]}.zip"
        target = output / asset
        if target != path.resolve():
            shutil.copy2(path, target)
        entries.append(dict(id=ident, name=name, description=description,
                            filename=filename, version=info["version"], size=path.stat().st_size,
                            sha256=digest, url=(base_url.rstrip("/") + "/" + asset) if base_url else asset,
                            notes=notes))
    temporary = output / "catalog.json.tmp"
    temporary.write_text(json.dumps({"schema": 1, "mods": entries}, ensure_ascii=False, indent=2),
                         encoding="utf-8")
    temporary.replace(output / "catalog.json")
    return entries


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=PROJECT / "outputs/mod-center-release")
    parser.add_argument("--base-url", default="", help="Adresse HTTPS du dossier hébergé (facultatif).")
    parser.add_argument("--notes", default="", help="Nouveautés de cette publication.")
    args = parser.parse_args()
    for mod in publish(args.output, args.base_url, args.notes):
        print(f"{mod['name']} : {mod['version']} ({mod['size']:,} octets)")
    print(f"Prêt à héberger : {args.output.resolve() / 'catalog.json'}")
