"""Build the standalone ECU Studio Windows application."""
import json
import os
from pathlib import Path
import ssl
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
CENTER = ROOT.parent / "mod-center"
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(CENTER))
from app_version import VERSION
env = os.environ.copy()
env["PYTHONPATH"] = os.pathsep.join([str(ROOT / ".build-deps"), str(CENTER / ".build-deps"), str(CENTER)])
env["PYINSTALLER_CONFIG_DIR"] = str(ROOT / "build/cache")
arguments = [
    sys.executable, "-m", "PyInstaller", "--noconfirm", "--onedir", "--windowed", "--noupx",
    "--name", "ECU-Studio", "--paths", str(CENTER), "--paths", str(ROOT / ".build-deps"),
    "--distpath", str(ROOT / "dist" / VERSION), "--workpath", str(ROOT / "build"),
    "--specpath", str(ROOT / "build"), "--collect-all", "webview", "--collect-all", "pythonnet",
    "--collect-all", "clr_loader",
]
certificate = Path(ssl.__file__).with_name("codex-rejected-cas.pem")
if certificate.is_file():
    arguments += ["--add-data", str(certificate) + os.pathsep + "."]
arguments += [str(ROOT / "app.py")]
subprocess.run(arguments, env=env, check=True, cwd=ROOT)
folder = ROOT / "dist" / VERSION / "ECU-Studio"
(folder / "application.json").write_text(json.dumps({
    "id": "ecustudio", "version": VERSION, "executable": "ECU-Studio.exe"}), encoding="utf-8")
subprocess.run([str(folder / "ECU-Studio.exe"), "--diagnose-tls", "-"], check=True, timeout=45)
print(folder)
