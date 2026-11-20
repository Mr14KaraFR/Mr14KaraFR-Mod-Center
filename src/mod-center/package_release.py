"""Package an app update while preserving the current online mod catalogue."""
import hashlib
import json
from pathlib import Path
import sys
from urllib.request import urlopen
import zipfile

from core import APP_VERSION
from tls_support import tls_context

REPOSITORY = "Mr14KaraFR/Mr14KaraFR-Mod-Center"
BASE = "https://github.com/" + REPOSITORY + "/releases/"


def repair_text(value):
    if isinstance(value, dict):
        return {key: repair_text(item) for key, item in value.items()}
    if isinstance(value, list):
        return [repair_text(item) for item in value]
    if isinstance(value, str) and any(marker in value for marker in ("Ã", "Â", "â€")):
        for encoding in ("cp1252", "latin1"):
            try:
                return value.encode(encoding).decode("utf-8")
            except UnicodeError:
                pass
    return value


def package(output):
    root = Path(__file__).resolve().parent
    output.mkdir(parents=True, exist_ok=True)
    for name in ("catalog.json", "catalog-beta.json"):
        with urlopen(BASE + "latest/download/" + name, context=tls_context(), timeout=60) as response:
            data = json.load(response)
        (output / name).write_text(json.dumps(repair_text(data), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    folder = root / "dist" / APP_VERSION / "Mr14KaraFR-Mod-Center"
    for kind in ("Windows", "Update"):
        destination = output / f"Mr14KaraFR_Mod_Center_{APP_VERSION}_{kind}.zip"
        with zipfile.ZipFile(destination, "w", zipfile.ZIP_DEFLATED) as archive:
            for file in sorted(folder.rglob("*")):
                if file.is_file():
                    relative = file.relative_to(folder)
                    archive.write(file, (Path(folder.name) / relative) if kind == "Windows" else relative)
        with zipfile.ZipFile(destination) as archive:
            if archive.testzip():
                raise ValueError("Damaged application archive")
    catalog_path = output / "catalog.json"
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    update = output / f"Mr14KaraFR_Mod_Center_{APP_VERSION}_Update.zip"
    entry = next(item for item in catalog["applications"] if item["id"] == "modcenter")
    entry.update(version=APP_VERSION, url=BASE + f"download/modcenter-v{APP_VERSION}/" + update.name,
                 size=update.stat().st_size, sha256=hashlib.sha256(update.read_bytes()).hexdigest())
    catalog_path.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (output / "RELEASE_NOTES.md").write_text(
        "Cartes plus grandes dans un catalogue défilant à la molette.\n"
        "Disposition automatique sur une ou deux colonnes selon la largeur.\n"
        "Boutons et versions toujours visibles dans chaque carte. Accents du catalogue corrigés.\n\n"
        "Installation manuelle : extraire tout le ZIP Windows et lancer le programme avec son dossier _internal.\n",
        encoding="utf-8")
    sums = [hashlib.sha256(file.read_bytes()).hexdigest() + "  " + file.name
            for file in sorted(output.iterdir()) if file.is_file() and file.name != "SHA256SUMS.txt"]
    (output / "SHA256SUMS.txt").write_text("\n".join(sums) + "\n", encoding="utf-8")


if __name__ == "__main__":
    package(Path(sys.argv[1]))
