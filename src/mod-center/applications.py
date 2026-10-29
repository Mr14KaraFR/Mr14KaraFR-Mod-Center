"""Verified, versioned Windows app installs shared by Mod Center and ECU Studio."""
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import subprocess
import sys
import tempfile
from urllib.parse import urljoin

from core import MAX_CATALOG, MAX_DOWNLOAD, check_url, install_lock, open_source, sha256, version

EXECUTABLES = {"modcenter": "Mr14KaraFR-Mod-Center.exe", "ecustudio": "ECU-Studio.exe"}
CATALOG_URL = "https://github.com/Mr14KaraFR/Mr14KaraFR-Mod-Center/releases/latest/download/catalog.json"


def storage():
    return Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "Mr14KaraFR/Applications"


def validate(item, url, local=False):
    app = dict(item)
    if app.get("id") not in EXECUTABLES:
        raise ValueError("Application inconnue.")
    version(app.get("version"))
    if not isinstance(app.get("name"), str) or not 1 <= len(app["name"]) <= 150:
        raise ValueError("Nom d’application invalide.")
    if type(app.get("size")) is not int or not 0 < app["size"] <= MAX_DOWNLOAD:
        raise ValueError("Taille d’application invalide.")
    if not isinstance(app.get("sha256"), str) or not re.fullmatch(r"[a-f0-9]{64}", app["sha256"]):
        raise ValueError("Empreinte d’application invalide.")
    if not isinstance(app.get("url"), str) or not app["url"]:
        raise ValueError("Adresse d’application absente.")
    app["url"] = urljoin(url, app["url"])
    check_url(app["url"], local)
    return app


def load_apps(url, local=False):
    with open_source(url, local) as stream:
        raw = stream.read(MAX_CATALOG + 1)
    if len(raw) > MAX_CATALOG:
        raise ValueError("Catalogue trop volumineux.")
    data = json.loads(raw.decode("utf-8-sig"))
    entries = data.get("applications", [])
    if data.get("schema") != 1 or not isinstance(entries, list) or len(entries) > len(EXECUTABLES):
        raise ValueError("Catalogue d’applications incompatible.")
    apps = [validate(item, url, local) for item in entries]
    if len({app["id"] for app in apps}) != len(apps):
        raise ValueError("Application présente deux fois.")
    return apps


def current(ident, root=None):
    if ident not in EXECUTABLES:
        raise ValueError("Application inconnue.")
    base = (Path(root) if root else storage()) / ident
    try:
        info = json.loads((base / "current.json").read_text(encoding="utf-8"))
        version(info["version"])
        if not re.fullmatch(r"[a-f0-9]{64}", info["sha256"]):
            return None
        directory = base / "versions" / (info["version"] + "-" + info["sha256"][:12])
        exe = directory / EXECUTABLES[ident]
        if exe.is_file():
            return {**info, "exe": exe}
    except (OSError, ValueError, KeyError, TypeError):
        pass
    return None


def status(app, root=None):
    info = current(app["id"], root)
    if not info:
        return "Non installé", "—"
    if version(info["version"]) > version(app["version"]):
        return "Version locale plus récente", info["version"]
    return ("À jour" if info["sha256"] == app["sha256"] else "Mise à jour disponible"), info["version"]


def safe_members(archive):
    seen = set()
    entries = archive.infolist()
    reserved = {"CON", "PRN", "AUX", "NUL", *(f"COM{i}" for i in range(1, 10)), *(f"LPT{i}" for i in range(1, 10))}
    if len(entries) > 20000 or sum(e.file_size for e in entries) > 2 * MAX_DOWNLOAD:
        raise ValueError("Archive d’application trop volumineuse.")
    for entry in entries:
        name = entry.filename.rstrip("/")
        path = PurePosixPath(name)
        if (not name or path.is_absolute() or chr(92) in name or
                any(p in ("", ".", "..") or p.endswith((".", " ")) or
                    any(c in p for c in '<>:"|?*') or any(ord(c) < 32 for c in p) or
                    p.split(".")[0].upper() in reserved for p in name.split("/")) or
                stat.S_ISLNK(entry.external_attr >> 16) or name.lower() in seen):
            raise ValueError("Chemin dangereux dans l’archive d’application.")
        seen.add(name.lower())
    return entries


def install(app, progress=lambda done, total: None, local=False, root=None, probe=True):
    import zipfile
    app = validate(app, app["url"], local)
    base = (Path(root) if root else storage()) / app["id"]
    base.mkdir(parents=True, exist_ok=True)
    with install_lock(base):
        info = current(app["id"], root)
        if info and version(info["version"]) > version(app["version"]):
            raise ValueError("La version installée est plus récente.")
        if info and info["sha256"] == app["sha256"]:
            return info["exe"]
        with tempfile.TemporaryDirectory(prefix="staging-", dir=base) as temporary:
            stage = Path(temporary)
            package = stage / "package.zip"
            with package.open("wb") as target, open_source(app["url"], local) as source:
                total = 0
                while block := source.read(256 * 1024):
                    total += len(block)
                    if total > app["size"]:
                        raise ValueError("Téléchargement trop volumineux.")
                    target.write(block)
                    progress(total, app["size"])
            if total != app["size"] or sha256(package) != app["sha256"]:
                raise ValueError("Téléchargement incomplet ou empreinte SHA-256 incorrecte.")
            extracted = stage / "files"
            with zipfile.ZipFile(package) as archive:
                safe_members(archive)
                if archive.getinfo("application.json").file_size > MAX_CATALOG:
                    raise ValueError("Métadonnées d’application trop volumineuses.")
                manifest = json.loads(archive.read("application.json"))
                if manifest != {"id": app["id"], "version": app["version"], "executable": EXECUTABLES[app["id"]]}:
                    raise ValueError("Identité ou version d’application incorrecte.")
                archive.extractall(extracted)
            exe = extracted / EXECUTABLES[app["id"]]
            if not exe.is_file():
                raise ValueError("Exécutable absent de l’application.")
            if probe:
                subprocess.run([str(exe), "--diagnose-tls", "-"], check=True, timeout=45,
                               creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
            destination = base / "versions" / (app["version"] + "-" + app["sha256"][:12])
            destination.parent.mkdir(exist_ok=True)
            if destination.exists():
                if not (destination / EXECUTABLES[app["id"]]).is_file():
                    raise ValueError("Une installation incomplète bloque cette version.")
            else:
                extracted.rename(destination)
            pointer = base / "current.json.tmp"
            pointer.write_text(json.dumps({"version": app["version"], "sha256": app["sha256"]}), encoding="utf-8")
            pointer.replace(base / "current.json")
            return destination / EXECUTABLES[app["id"]]


def launch(exe, args=()):
    return subprocess.Popen([str(exe), *args], cwd=exe.parent,
                            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))


def handoff(ident, running_version, args=(), root=None):
    """Old shortcuts follow the installed version, including when offline."""
    if not getattr(sys, "frozen", False):
        return False
    info = current(ident, root)
    if info and version(info["version"]) >= version(running_version) and info["exe"].resolve() != Path(sys.executable).resolve():
        launch(info["exe"], args)
        return True
    return False


def create_shortcut(exe, name="ECU Studio"):
    """The first installed version remains a stable launcher for future versions."""
    if os.name != "nt":
        return
    import base64
    literal = lambda value: "'" + str(value).replace("'", "''") + "'"
    script = (
        "$shell = New-Object -ComObject WScript.Shell\n"
        "$desktop = [Environment]::GetFolderPath('Desktop')\n"
        "$link = $shell.CreateShortcut((Join-Path $desktop " + literal(name + ".lnk") + "))\n"
        "$link.TargetPath = " + literal(exe) + "\n"
        "$link.WorkingDirectory = " + literal(exe.parent) + "\n"
        "$link.Save()"
    )
    encoded = base64.b64encode(script.encode("utf-16le")).decode("ascii")
    subprocess.run(["powershell.exe", "-NoProfile", "-NonInteractive", "-EncodedCommand", encoded],
                   check=True, timeout=20, creationflags=subprocess.CREATE_NO_WINDOW)
