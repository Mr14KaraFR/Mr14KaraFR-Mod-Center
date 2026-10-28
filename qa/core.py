"""Download and install BeamNG ZIP mods. No archive is extracted into the game."""
from __future__ import annotations

import contextlib
import csv
import hashlib
import io
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
from datetime import datetime
from urllib.parse import urljoin, urlparse, unquote
from urllib.request import Request, urlopen
import zipfile

APP_VERSION = "0.1.1"
MAX_DOWNLOAD = 1024 * 1024 * 1024
MAX_CATALOG = 1024 * 1024


def version(value):
    if not isinstance(value, str) or not re.fullmatch(r"\d+(?:\.\d+){0,3}(?:-[A-Za-z][A-Za-z0-9.-]*)?", value):
        raise ValueError("Version invalide : utilisez par exemple 1.2.3.")
    parts = tuple(int(n) for n in value.split("-")[0].split("."))
    return parts + (0,) * (4 - len(parts))


def sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def safe_filename(name):
    if (not isinstance(name, str) or len(name) > 120 or
            not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*\.zip", name) or
            name.split(".")[0].upper() in
            {"CON", "PRN", "AUX", "NUL", *(f"COM{i}" for i in range(1, 10)),
             *(f"LPT{i}" for i in range(1, 10))}):
        raise ValueError("Nom de fichier ZIP invalide.")
    return name


def check_url(url, local=False):
    parsed = urlparse(url)
    if parsed.scheme == "https" and parsed.hostname and not parsed.username and not parsed.password:
        return
    if local and parsed.scheme == "file" and parsed.netloc in ("", "localhost"):
        return
    raise ValueError("Une adresse HTTPS est obligatoire (fichier local uniquement en mode test).")


@contextlib.contextmanager
def open_source(url, local=False):
    check_url(url, local)
    if urlparse(url).scheme == "file":
        parsed = urlparse(url)
        path = unquote(parsed.path)
        if os.name == "nt" and re.match(r"^/[A-Za-z]:", path):
            path = path[1:]
        with open(path, "rb") as stream:
            yield stream
    else:
        request = Request(url, headers={"User-Agent": f"Mr14KaraFR-ModCenter/{APP_VERSION}",
                                        "Cache-Control": "no-cache"})
        with urlopen(request, timeout=30) as stream:
            check_url(stream.geturl(), False)
            yield stream


def load_catalog(url, local=False):
    with open_source(url, local) as stream:
        raw = stream.read(MAX_CATALOG + 1)
    if len(raw) > MAX_CATALOG:
        raise ValueError("Catalogue trop volumineux.")
    data = json.loads(raw.decode("utf-8-sig"))
    if data.get("schema") != 1 or not isinstance(data.get("mods"), list) or len(data["mods"]) > 100:
        raise ValueError("Format de catalogue incompatible.")
    result, ids, filenames = [], set(), set()
    for item in data["mods"]:
        mod = dict(item)
        ident = mod.get("id", "")
        if not isinstance(ident, str) or not re.fullmatch(r"[a-z0-9_]{1,80}", ident) or ident in ids:
            raise ValueError("Identifiant de mod invalide ou présent deux fois.")
        filename = safe_filename(mod.get("filename"))
        if filename.lower() in filenames:
            raise ValueError("Deux mods utilisent le même fichier ZIP.")
        version(mod.get("version"))
        if not isinstance(mod.get("name"), str) or not 1 <= len(mod["name"]) <= 150:
            raise ValueError("Nom de mod invalide.")
        if not isinstance(mod.get("sha256"), str) or not re.fullmatch(r"[a-f0-9]{64}", mod["sha256"]):
            raise ValueError("Empreinte SHA-256 manquante ou invalide.")
        if type(mod.get("size")) is not int or not 0 < mod["size"] <= MAX_DOWNLOAD:
            raise ValueError("Taille de téléchargement invalide.")
        if not isinstance(mod.get("url"), str) or not mod["url"]:
            raise ValueError("Adresse du téléchargement manquante.")
        mod["url"] = urljoin(url, mod["url"])
        check_url(mod["url"], local)
        ids.add(ident)
        filenames.add(filename.lower())
        result.append(mod)
    return result


def archive_info(path, ident):
    with zipfile.ZipFile(path) as archive:
        entry = archive.getinfo(f"mod_info/{ident}/info.json")
        if entry.file_size > MAX_CATALOG:
            raise ValueError("Métadonnées ZIP trop volumineuses.")
        return json.loads(archive.read(entry).decode("utf-8-sig"))


def installed(mods_dir, mod):
    if not mods_dir:
        return []
    root = Path(mods_dir)
    found = []
    for folder in (root, root / "repo"):
        if not folder.is_dir():
            continue
        for path in folder.glob("*.zip"):
            try:
                info = archive_info(path, mod["id"])
                found.append((path, info.get("version", "?")))
            except (OSError, ValueError, KeyError, zipfile.BadZipFile):
                continue
    return found


def status(mods_dir, mod):
    copies = installed(mods_dir, mod)
    if not copies:
        return "Non installé", "—"
    versions = ", ".join(v for _, v in copies)
    try:
        if any(version(v) > version(mod["version"]) for _, v in copies):
            return "Version locale plus récente", versions
    except ValueError:
        pass
    if len(copies) == 1 and sha256(copies[0][0]) == mod["sha256"]:
        return "À jour", versions
    return ("Doublons à remplacer" if len(copies) > 1 else "Mise à jour disponible"), versions


def game_running():
    if os.name != "nt":
        return False
    output = subprocess.check_output(["tasklist", "/FO", "CSV", "/NH"],
                                     creationflags=subprocess.CREATE_NO_WINDOW,
                                     timeout=10).decode("utf-8", errors="replace")
    return any(row and row[0].lower().startswith("beamng") and row[0].lower().endswith(".exe")
               for row in csv.reader(io.StringIO(output)))


@contextlib.contextmanager
def install_lock(root):
    # Keep the file: deleting a lock file can allow concurrent locks on different inodes.
    with open(root / ".mr14kara-update.lock", "a+b") as stream:
        stream.seek(0, os.SEEK_END)
        if stream.tell() == 0:
            stream.write(b"0")
            stream.flush()
        stream.seek(0)
        try:
            if os.name == "nt":
                import msvcrt
                msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            raise RuntimeError("Une autre installation est déjà en cours.") from exc
        try:
            yield
        finally:
            stream.seek(0)
            if os.name == "nt":
                msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(stream.fileno(), fcntl.LOCK_UN)


def install(mods_dir, mod, progress=lambda done, total: None, local=False):
    if Path(mods_dir).is_symlink():
        raise ValueError("Le dossier mods ne doit pas être un lien symbolique.")
    root = Path(mods_dir).resolve()
    if not root.is_dir() or root.name.lower() != "mods":
        raise ValueError("Choisissez le dossier « mods » de votre dossier utilisateur BeamNG.")
    if root.is_symlink():
        raise ValueError("Le dossier mods ne doit pas être un lien symbolique.")
    if game_running():
        raise RuntimeError("Fermez BeamNG.drive avant de modifier les mods.")
    with install_lock(root):
        return _install(root, mod, progress, local)


def _install(root, mod, progress, local):
    destination = root / safe_filename(mod["filename"])
    copies = installed(root, mod)
    if destination.exists() and destination not in [p for p, _ in copies]:
        raise ValueError("Un fichier portant ce nom appartient à un autre mod ou est illisible.")
    for _, existing_version in copies:
        try:
            newer = version(existing_version) > version(mod["version"])
        except ValueError:
            newer = False
        if newer:
            raise ValueError("La version installée est plus récente ; remplacement refusé.")
    fd, temporary_name = tempfile.mkstemp(prefix=".mr14kara-", suffix=".download", dir=root)
    temporary = Path(temporary_name)
    backup = None
    originals = []
    try:
        with os.fdopen(fd, "wb") as target, open_source(mod["url"], local) as source:
            total = 0
            while block := source.read(256 * 1024):
                total += len(block)
                if total > mod["size"] or total > MAX_DOWNLOAD:
                    raise ValueError("Le fichier dépasse la taille annoncée.")
                target.write(block)
                progress(total, mod["size"])
            target.flush()
            os.fsync(target.fileno())
        if total != mod["size"] or sha256(temporary) != mod["sha256"]:
            raise ValueError("Téléchargement incomplet ou empreinte SHA-256 incorrecte.")
        with zipfile.ZipFile(temporary) as archive:
            if sum(e.file_size for e in archive.infolist()) > 2 * MAX_DOWNLOAD:
                raise ValueError("Archive décompressée trop volumineuse.")
            if archive.testzip() is not None:
                raise ValueError("Archive ZIP endommagée.")
        info = archive_info(temporary, mod["id"])
        if info.get("version") != mod["version"]:
            raise ValueError("La version du ZIP ne correspond pas au catalogue.")
        if game_running():
            raise RuntimeError("BeamNG a été lancé. Fermez le jeu, puis réessayez.")
        backup_root = root.parent / "Mr14KaraFR-backups"
        backup_root.mkdir(exist_ok=True)
        backup = Path(tempfile.mkdtemp(prefix=datetime.now().strftime("%Y%m%d-%H%M%S-") + mod["id"] + "-",
                                      dir=backup_root))
        for i, (path, _) in enumerate(copies):
            saved = backup / f"{i}-{path.name}"
            shutil.copy2(path, saved)
            originals.append((path, saved))
        (backup / "restore.json").write_text(json.dumps({"files": [
            {"original": str(p), "backup": s.name} for p, s in originals]}, indent=2), encoding="utf-8")
        removed = []
        replaced = False
        try:
            os.replace(temporary, destination)
            replaced = True
            for path, saved in originals:
                if path != destination:
                    path.unlink()
                    removed.append((path, saved))
        except Exception:
            if replaced:
                for path, saved in originals:
                    if path == destination or (path, saved) in removed:
                        shutil.copy2(saved, path)
                if destination not in [p for p, _ in originals]:
                    destination.unlink(missing_ok=True)
            raise
        return backup
    finally:
        temporary.unlink(missing_ok=True)
