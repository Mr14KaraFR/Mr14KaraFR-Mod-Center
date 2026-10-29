"""ECU Studio desktop window. The interface is served by the installed ECU mod."""
import argparse
import html
import json
import os
from pathlib import Path
import ssl
import sys
import threading
from urllib.request import build_opener, ProxyHandler

import applications

from app_version import VERSION
URL = "http://127.0.0.1:8724/"
WAITING = """<!doctype html><html lang="fr"><meta charset="utf-8">
<style>body{margin:0;background:#0b101b;color:#edf3ff;font:18px 'Segoe UI',sans-serif;
display:grid;place-items:center;height:100vh}.card{max-width:650px;padding:48px;background:#141d2d;
border:1px solid #243149;border-radius:18px}h1{color:#489bff}p{line-height:1.6}small{color:#97a9c4}</style>
<div class="card"><h1>ECU Studio</h1><p id="status">Connexion à BeamNG…</p>
<p>Lance BeamNG.drive, active le mod ECU Studio, puis ouvre le tuner ECU dans le jeu.
La connexion se fera automatiquement.</p><small>Tu peux garder cette fenêtre sur ton deuxième écran.</small></div></html>"""


def diagnose():
    context = ssl.create_default_context()
    if not context.check_hostname or context.verify_mode != ssl.CERT_REQUIRED:
        return 1
    import webview
    # Import the actual Windows renderer: catches missing .NET / bundled DLLs.
    from webview.platforms import winforms
    return 0


def run(no_update=False):
    import webview
    window = webview.create_window("ECU Studio · Mr14KaraFR", html=WAITING,
                                   width=1280, height=900, min_size=(900, 650),
                                   background_color="#0b101b")
    stopped = threading.Event()
    window.events.closed += stopped.set
    def worker():
        if not no_update and getattr(sys, "frozen", False):
            try:
                apps = applications.load_apps(applications.CATALOG_URL)
                entry = next((a for a in apps if a["id"] == "ecustudio"), None)
                if entry and applications.version(entry["version"]) > applications.version(VERSION):
                    window.evaluate_js("document.getElementById('status').textContent='Mise à jour d’ECU Studio…';")
                    exe = applications.install(entry)
                    applications.launch(exe)
                    window.destroy()
                    return
            except Exception:
                # A network outage must never block access to the tuner.
                pass
        opener = build_opener(ProxyHandler({}))
        connected = False
        while not stopped.is_set():
            try:
                with opener.open(URL, timeout=2) as response:
                    page = response.read(16000).decode("utf-8")
                ready = "ECU Studio By Mr14KaraFR" in page and "window.ECU_SESSION=" in page
            except Exception:
                ready = False
            if ready and not connected:
                window.load_url(URL)
                connected = True
            elif not ready and connected:
                window.load_html(WAITING)
                connected = False
            stopped.wait(2)
    webview.settings["ALLOW_DOWNLOADS"] = True
    cache = Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "Mr14KaraFR/ECUStudio/WebView"
    webview.start(worker, gui="edgechromium", storage_path=str(cache), private_mode=False)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--diagnose-tls")
    parser.add_argument("--no-update", action="store_true", help="Test local sans mise à jour.")
    args = parser.parse_args()
    if args.diagnose_tls:
        raise SystemExit(diagnose())
    if not args.no_update and applications.handoff("ecustudio", VERSION):
        raise SystemExit(0)
    try:
        run(args.no_update)
    except Exception as exc:
        import tkinter as tk
        from tkinter import messagebox
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("ECU Studio", "Impossible d’ouvrir ECU Studio. Vérifie que Microsoft Edge WebView2 Runtime est installé.\n\n" + str(exc))
        root.destroy()
