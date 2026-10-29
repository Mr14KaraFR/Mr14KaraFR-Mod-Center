"""Build a portable Windows application using local PyInstaller dependencies."""
import os
from pathlib import Path
import subprocess
import sys
import json
import ssl
from core import APP_VERSION

ROOT = Path(__file__).resolve().parent
dependencies = ROOT / ".build-deps"
environment = os.environ.copy()
environment["PYTHONPATH"] = str(dependencies)
# Keep build and cache files inside this project.
environment["PYINSTALLER_CONFIG_DIR"] = str(ROOT / "build/cache")
catalog = Path(os.environ.get("MR14KARA_PREVIEW_CATALOG", ROOT.parent / "outputs/mod-center-release/catalog.json"))
if catalog.exists():
    entries = json.loads(catalog.read_text(encoding="utf-8"))["mods"]
    (ROOT / "preview.json").write_text(json.dumps({"mods": [
        {"name": m["name"], "version": m["version"]} for m in entries]}, ensure_ascii=False), encoding="utf-8")
arguments = [
    sys.executable, "-m", "PyInstaller", "--noconfirm", "--onedir", "--windowed", "--noupx",
    "--name", "Mr14KaraFR-Mod-Center", "--paths", str(ROOT),
    "--icon", str(ROOT / "assets/modcenter.ico"),
    "--add-data", str(ROOT / "assets") + os.pathsep + "assets",
    "--distpath", str(ROOT / "dist" / APP_VERSION), "--workpath", str(ROOT / "build"),
    "--specpath", str(ROOT / "build"),
    "--add-data", str(ROOT / "channel.json") + os.pathsep + ".",
    "--add-data", str(ROOT / "preview.json") + os.pathsep + ".",
]
# This runtime's ssl.py loads a supplemental certificate file beside ssl.py.
# Preserve that check and ship its dependency at the same relative location.
certificate = Path(ssl.__file__).with_name("codex-rejected-cas.pem")
if certificate.is_file():
    arguments += ["--add-data", str(certificate) + os.pathsep + "."]
elif "codex-rejected-cas.pem" in Path(ssl.__file__).read_text(encoding="utf-8"):
    raise FileNotFoundError("Le fichier de certificat requis par ce Python est absent : " + str(certificate))
arguments += [str(ROOT / "app.py")]
subprocess.run(arguments, env=environment, cwd=ROOT, check=True)
executable = ROOT / "dist" / APP_VERSION / "Mr14KaraFR-Mod-Center/Mr14KaraFR-Mod-Center.exe"
subprocess.run([str(executable), "--diagnose-tls", "-"], cwd=ROOT.parent, check=True, timeout=30)
print("HTTPS du programme Windows vérifié, sans réseau et sans fenêtre.")
print(executable)

folder = executable.parent
(folder / "application.json").write_text(json.dumps({
    "id": "modcenter", "version": APP_VERSION, "executable": executable.name}), encoding="utf-8")
