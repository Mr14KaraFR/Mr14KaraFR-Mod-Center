"""Prepare a self-contained GitHub release folder, without sending files online."""
import argparse
import json
from pathlib import Path
import re
import zipfile

from core import APP_VERSION, load_catalog, sha256
from applications import load_apps
from publish import PROJECT, publish

REPOSITORY = "Mr14KaraFR/Mr14KaraFR-Mod-Center"


def prepare(tag, notes=""):
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,80}", tag):
        raise ValueError("Nom de publication invalide.")
    output = PROJECT / "outputs/mod-center-github-releases" / tag
    output.mkdir(parents=True, exist_ok=True)
    base = f"https://github.com/{REPOSITORY}/releases/download/{tag}"
    entries = publish(output, base_url=base)
    source = PROJECT / "mod-center/dist" / APP_VERSION / "Mr14KaraFR-Mod-Center"
    exe = source / "Mr14KaraFR-Mod-Center.exe"
    if not exe.is_file():
        raise FileNotFoundError("Compilez l’application avec build.py avant de préparer la publication.")
    (source / "LIRE_MOI.txt").write_text(
        "Mr14KaraFR Mod Center " + APP_VERSION + "\n\n"
        "Extraire tout le ZIP puis ouvrir Mr14KaraFR-Mod-Center.exe.\n"
        "Garder le dossier _internal a cote de l application.\n\n"
        "Le catalogue GitHub officiel est deja configure.\n"
        "Choisir le dossier mods de votre dossier utilisateur BeamNG avec Parcourir.\n"
        "Fermer BeamNG avant toute installation.\n"
        "Installer les mods souhaites avec Installer.\n"
        "Sections Mods et Applications : Tout mettre a jour concerne les elements deja installes.\n"
        "Les sauvegardes sont conservees dans Mr14KaraFR-backups, a cote de mods.\n"
        "Le Mod Center se met a jour automatiquement au lancement. ECU Studio fait de meme.\n"
        "Il ne tourne pas en arriere-plan une fois ferme.\n\n"
        f"Informations : https://github.com/{REPOSITORY}\n", encoding="utf-8")
    app_zip = output / f"Mr14KaraFR_Mod_Center_{APP_VERSION}_Windows.zip"
    with zipfile.ZipFile(app_zip, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(source.rglob("*")):
            if path.is_file():
                archive.write(path, (Path(source.name) / path.relative_to(source)).as_posix())
    with zipfile.ZipFile(app_zip) as archive:
        if archive.testzip() is not None:
            raise ValueError("L’archive Windows est endommagée.")
        channel = json.loads(archive.read("Mr14KaraFR-Mod-Center/_internal/channel.json"))
        if channel["catalog_url"] != f"https://github.com/{REPOSITORY}/releases/latest/download/catalog.json":
            raise ValueError("L’application ne contient pas l’adresse du catalogue officiel.")
    import sys
    sys.path.insert(0, str(PROJECT / "ecu-app"))
    from app_version import VERSION as ECU_VERSION
    apps = []
    for ident, name, app_version, folder, filename, description in (
        ("modcenter", "Mod Center", APP_VERSION, source, f"Mr14KaraFR_Mod_Center_{APP_VERSION}_Update.zip",
         "Gestion des mods et applications. Mise à jour automatique au lancement."),
        ("ecustudio", "ECU Studio pour Windows", ECU_VERSION,
         PROJECT / "ecu-app/dist" / ECU_VERSION / "ECU-Studio",
         f"ECU_Studio_{ECU_VERSION}_Windows.zip",
         "Le tuner ECU dans sa propre fenêtre. BeamNG et le mod ECU doivent être ouverts."),
    ):
        package = output / filename
        if not (folder / "application.json").is_file():
            raise FileNotFoundError("Compilez d’abord " + name)
        with zipfile.ZipFile(package, "w", zipfile.ZIP_DEFLATED) as archive:
            for path in sorted(folder.rglob("*")):
                if path.is_file():
                    archive.write(path, path.relative_to(folder).as_posix())
        apps.append(dict(id=ident, name=name, version=app_version, description=description,
                         url=base + "/" + filename, size=package.stat().st_size, sha256=sha256(package)))
    catalogue = output / "catalog.json"
    data = json.loads(catalogue.read_text(encoding="utf-8"))
    data["applications"] = apps
    catalogue.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    load_apps(catalogue.as_uri(), local=True)
    parsed = load_catalog((output / "catalog.json").as_uri(), local=True)
    if len(parsed) != 4:
        raise ValueError("Les quatre mods doivent être présents.")
    files = [output / m["url"].rsplit("/", 1)[1] for m in entries] + [output / "catalog.json", app_zip] + [output / a["url"].rsplit("/", 1)[1] for a in apps]
    selection_path = PROJECT / "branding/current.json"
    selection = json.loads(selection_path.read_text(encoding="utf-8")) if selection_path.exists() else {
        "directory": "logos-v1", "archive": "Mr14KaraFR_Logos_v1.zip"}
    brand = PROJECT / "branding" / selection["directory"]
    if brand.is_dir():
        logo_zip = output / selection["archive"]
        with zipfile.ZipFile(logo_zip, "w", zipfile.ZIP_DEFLATED) as archive:
            for path in sorted(brand.iterdir()):
                if path.is_file() and path.name != "sources.json":
                    archive.write(path, path.name)
        files.append(logo_zip)
    checksums = output / "SHA256SUMS.txt"
    checksums.write_text("".join(f"{sha256(path)}  {path.name}\n" for path in files), encoding="ascii")
    release_notes = "# Mr14KaraFR Mod Center " + APP_VERSION + "\n\n"
    release_notes += "Application Windows portable pour installer et mettre à jour les mods publics Mr14KaraFR.\n\n"
    if notes:
        release_notes += "## Correction\n\n" + notes + "\n\n"
    release_notes += "## Installation\n\nTélécharger **" + app_zip.name + "**, extraire tout le ZIP, puis ouvrir **Mr14KaraFR-Mod-Center.exe**. Garder le dossier **_internal** à côté de l’EXE.\n\n"
    release_notes += "Le catalogue officiel est déjà connecté. Choisir le dossier **mods** du dossier utilisateur BeamNG et fermer le jeu avant d’installer ou de mettre à jour un mod.\n\n"
    release_notes += "## Mods disponibles\n\n"
    release_notes += "".join(f"- {m['name']} : **{m['version']}**\n" for m in entries)
    release_notes += "\nLes anciennes archives sont sauvegardées à côté du dossier mods, dans **Mr14KaraFR-backups**. Les mods décompressés dans unpacked ne sont pas gérés.\n\n"
    release_notes += "Cette version ajoute les sections Mods et Applications, ECU Studio pour Windows et les mises à jour automatiques des deux applications au lancement. La version 0.1.2 nécessite ce dernier téléchargement manuel pour passer au nouveau système. Les applications ne sont pas signées numériquement.\n"
    (output / "RELEASE_NOTES.md").write_text(release_notes, encoding="utf-8")
    print(json.dumps({"tag": tag, "folder": str(output), "files": [p.name for p in files] + [checksums.name]}, ensure_ascii=False, indent=2))
    return output


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tag", default="modcenter-v" + APP_VERSION)
    parser.add_argument("--notes", default="")
    args = parser.parse_args()
    prepare(args.tag, args.notes)
