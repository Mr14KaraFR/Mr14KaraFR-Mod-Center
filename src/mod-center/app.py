"""Mr14KaraFR Mod Center — Windows desktop interface."""
import argparse
import json
import os
from pathlib import Path
import queue
import sys
import threading
import traceback
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import webbrowser
import applications

from core import APP_VERSION, install, load_catalog, status, check_url
from diagnostics import diagnose

HERE = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
BG, PANEL, EDGE = "#0b101b", "#141d2d", "#243149"
TEXT, MUTED, BLUE, GREEN = "#edf3ff", "#97a9c4", "#489bff", "#5cddb0"
FONT = "Segoe UI"
PREVIEW = [
    ("ECU Studio", "Cartographies moteur, réglages et profils de conduite.", "ECU"),
    ("Suspension pneumatique", "Hauteur, pression et commandes de suspension.", "AIR"),
    ("Fumée diesel volumétrique", "Fumée volumétrique et effets d’échappement.", "DSL"),
    ("Flammes & détonations HQ", "Flammes volumétriques et effets sonores.", "HQ"),
]


def json_file(path, fallback):
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        return fallback


class App(tk.Tk):
    def __init__(self, config_path=None, catalog=None):
        super().__init__()
        self.title(f"Mr14KaraFR Mod Center • {APP_VERSION}")
        self.geometry("1080x900")
        self.minsize(1020, 870)
        self.configure(bg=BG)
        self.protocol("WM_DELETE_WINDOW", self.close)
        data = Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "Mr14KaraFR/ModCenter"
        self.config_path = Path(config_path) if config_path else data / "settings.json"
        defaults = json_file(HERE / "channel.json", {})
        self.config_data = {**defaults, **json_file(self.config_path, {})}
        if not self.config_data.get("catalog_url"):
            self.config_data["catalog_url"] = defaults.get("catalog_url", "")
        self.mods_dir = tk.StringVar(value=self.config_data.get("mods_dir", ""))
        self.catalog_url = self.config_data.get("catalog_url", "")
        self.local = False
        if catalog:
            self.catalog_url = Path(catalog).resolve().as_uri()
            self.local = True
        self.mods = []
        self.applications = []
        self.section = "mods"
        self.cached_rows = []
        self.events = queue.Queue()
        self.busy = False
        self.cards = []
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("Blue.Horizontal.TProgressbar", background=BLUE, troughcolor=PANEL,
                        bordercolor=BG, lightcolor=BLUE, darkcolor=BLUE)
        self.build()
        self.preview()
        self.after(80, self.poll)
        if self.catalog_url:
            self.after(200, self.refresh)

    def label(self, parent, text, size=10, color=TEXT, bold=False, **kw):
        return tk.Label(parent, text=text, font=(FONT, size, "bold" if bold else "normal"),
                        fg=color, bg=parent.cget("bg"), **kw)

    def button(self, parent, text, command, primary=False):
        return tk.Button(parent, text=text, command=command, font=(FONT, 10, "bold"),
                         bg=BLUE if primary else EDGE, fg="#081321" if primary else TEXT,
                         activebackground="#75b5ff", activeforeground="#081321",
                         disabledforeground="#72839d", relief="flat", bd=0,
                         padx=18, pady=10, cursor="hand2")

    def build(self):
        header = tk.Frame(self, bg=BG)
        header.pack(fill="x", padx=30, pady=(24, 18))
        self.label(header, "M14", 21, BLUE, True).pack(side="left", padx=(0, 18))
        titles = tk.Frame(header, bg=BG)
        titles.pack(side="left")
        self.label(titles, "Mr14KaraFR", 11, MUTED).pack(anchor="w")
        self.label(titles, "MOD CENTER", 23, TEXT, True).pack(anchor="w")
        self.button(header, "Paramètres", self.settings).pack(side="right")
        self.discord_button = self.button(header, "Discord ↗", self.discord)
        self.discord_button.pack(side="right", padx=10)
        self.discord_button.config(state="normal" if self.config_data.get("discord_url") else "disabled")

        hero = tk.Frame(self, bg=PANEL, highlightbackground=EDGE, highlightthickness=1)
        hero.pack(fill="x", padx=30)
        self.label(hero, "Tes mods et tes applications.", 21, TEXT, True).pack(anchor="w", padx=22, pady=(17, 5))
        self.label(hero, "Installe tes créations et ouvre tes outils pour BeamNG.drive.",
                   11, MUTED).pack(anchor="w", padx=22, pady=(0, 17))

        setup = self.setup_frame = tk.Frame(self, bg=BG)
        setup.pack(fill="x", padx=30, pady=(18, 4))
        self.label(setup, "DOSSIER DES MODS BEAMNG", 9, MUTED, True).pack(anchor="w", pady=(0, 6))
        row = tk.Frame(setup, bg=BG)
        row.pack(fill="x")
        self.folder_entry = tk.Entry(row, textvariable=self.mods_dir, font=(FONT, 10), bg=PANEL,
                                     fg=TEXT, insertbackground=TEXT, relief="flat", bd=8)
        self.folder_entry.pack(side="left", fill="x", expand=True, ipady=3)
        self.folder_button = self.button(row, "Parcourir…", self.choose_folder)
        self.folder_button.pack(side="left", padx=(10, 0))

        toolbar = self.toolbar_frame = tk.Frame(self, bg=BG)
        toolbar.pack(fill="x", padx=30, pady=(19, 12))
        self.mods_tab = self.button(toolbar, "Mods", lambda: self.select_section("mods"), True)
        self.mods_tab.pack(side="left")
        self.apps_tab = self.button(toolbar, "Applications", lambda: self.select_section("applications"))
        self.apps_tab.pack(side="left", padx=8)
        self.refresh_button = self.button(toolbar, "Vérifier les mises à jour", self.refresh)
        self.refresh_button.pack(side="right", padx=(10, 0))
        self.update_button = self.button(toolbar, "Tout mettre à jour", self.update_existing, True)
        self.update_button.pack(side="right")
        self.update_button.config(state="disabled")

        self.grid_frame = tk.Frame(self, bg=BG)
        self.grid_frame.configure(height=340)
        self.grid_frame.grid_propagate(False)
        self.grid_frame.pack(fill="both", expand=True, padx=30)
        for col in range(2):
            self.grid_frame.columnconfigure(col, weight=1, uniform="cards")
        for row in range(2):
            self.grid_frame.rowconfigure(row, weight=1, uniform="cards")

        footer = tk.Frame(self, bg=BG)
        footer.pack(fill="x", padx=30, pady=(10, 16))
        self.progress = ttk.Progressbar(footer, style="Blue.Horizontal.TProgressbar", maximum=100)
        self.progress.pack(fill="x", pady=(0, 8))
        self.message = self.label(footer, "Hébergement à configurer · ouvre Paramètres pour connecter le catalogue.", 10, MUTED)
        self.message.pack(anchor="w")
        self.label(footer, f"v{APP_VERSION} · Mise à jour du Mod Center au lancement · Ferme BeamNG pour modifier les mods",
                   9, MUTED).pack(anchor="w", pady=(5, 0))

    def clear_cards(self):
        for child in self.grid_frame.winfo_children():
            child.destroy()
        self.cards = []

    def card(self, index, name, description, code, latest="—", current="—", state="Catalogue à connecter", mod=None):
        frame = tk.Frame(self.grid_frame, bg=PANEL, highlightbackground=EDGE, highlightthickness=1)
        frame.grid(row=index // 2, column=index % 2, sticky="nsew",
                   padx=(0, 7) if index % 2 == 0 else (7, 0), pady=(0, 12))
        top = tk.Frame(frame, bg=PANEL)
        top.pack(fill="x", padx=17, pady=(13, 5))
        self.label(top, code, 10, BLUE, True).pack(side="left")
        self.label(top, state, 9, GREEN if state == "À jour" else MUTED).pack(side="right")
        self.label(frame, name, 15, TEXT, True).pack(anchor="w", padx=17)
        self.label(frame, description, 10, MUTED, wraplength=410, justify="left").pack(anchor="w", padx=17, pady=(5, 10))
        lower = tk.Frame(frame, bg=PANEL)
        lower.pack(side="bottom", fill="x", padx=17, pady=(0, 14))
        versions = tk.Frame(lower, bg=PANEL)
        versions.pack(side="left")
        self.label(versions, f"Installée : {current}", 9, MUTED).pack(anchor="w")
        self.label(versions, f"Disponible : {latest}", 9, TEXT).pack(anchor="w")
        text = "Installer" if state == "Non installé" else "Mettre à jour"
        if state == "À jour":
            text = "À jour ✓"
        button = self.button(lower, text, lambda: self.start_install([mod]), True)
        button.pack(side="right")
        if not mod or self.busy or state in ("À jour", "Version locale plus récente") or not self.mods_dir.get():
            button.config(state="disabled")
        if mod and mod.get("notes"):
            self.button(lower, "Nouveautés", lambda: messagebox.showinfo(name, mod["notes"])).pack(side="right", padx=8)
        self.cards.append(button)

    def select_section(self, section):
        self.section = section
        if section == "applications":
            self.setup_frame.pack_forget()
        elif not self.setup_frame.winfo_manager():
            self.setup_frame.pack(fill="x", padx=30, pady=(18, 4), before=self.toolbar_frame)
        self.set_busy(self.busy)
        self.mods_tab.config(bg=BLUE if section == "mods" else EDGE, fg="#081321" if section == "mods" else TEXT)
        self.apps_tab.config(bg=BLUE if section == "applications" else EDGE, fg="#081321" if section == "applications" else TEXT)
        if self.mods:
            self.render(self.cached_rows)
        else:
            self.preview()

    def render_applications(self):
        self.clear_cards()
        if not self.applications:
            self.label(self.grid_frame, "Aucune application publiée dans ce catalogue.", 13, MUTED).grid(
                row=0, column=0, columnspan=2, sticky="w")
            return
        for i, app in enumerate(self.applications):
            state, installed = applications.status(app)
            if app["id"] == "modcenter":
                installed = APP_VERSION
                state = "À jour" if applications.version(APP_VERSION) >= applications.version(app["version"]) else "Mise à jour disponible"
            self.card(i, app["name"], app.get("description", ""), "APP", app["version"], installed, state)
            button = self.cards[-1]
            info = applications.current(app["id"])
            if app["id"] == "modcenter":
                button.config(text="Mod Center ouvert", state="disabled")
            elif state in ("À jour", "Version locale plus récente") and info:
                button.config(text="Ouvrir", command=lambda path=info["exe"]: applications.launch(path),
                              state="disabled" if self.busy else "normal")
            else:
                button.config(text="Installer" if state == "Non installé" else "Mettre à jour",
                              command=lambda entry=app: self.install_application(entry),
                              state="disabled" if self.busy else "normal")

    def install_application(self, app):
        def work():
            exe = applications.install(app, lambda n, total: self.events.put(("progress", n * 100 / total)), self.local)
            if app["id"] == "ecustudio" and not self.local:
                try:
                    applications.create_shortcut(exe)
                except Exception as exc:
                    return (self.mods, self.cached_rows, app["name"] + " installé. Raccourci indisponible : " + str(exc)[:80], self.applications)
            return (self.mods, self.cached_rows, app["name"] + " installé.", self.applications)
        self.run_worker(work)

    def preview(self):
        if self.section == "applications":
            self.render_applications()
            return
        self.clear_cards()
        entries = json_file(HERE / "preview.json", {}).get("mods", [])
        versions = {entry["name"]: entry["version"] for entry in entries}
        for i, (name, desc, code) in enumerate(PREVIEW):
            self.card(i, name, desc, code, latest=versions.get(name, "—"))

    def render(self, rows):
        self.cached_rows = rows
        if self.section == "applications":
            self.render_applications()
            return
        self.clear_cards()
        for i, (mod, state, current) in enumerate(rows):
            self.card(i, mod["name"], mod.get("description", ""),
                      ["ECU", "AIR", "DSL", "HQ"][i % 4], mod["version"], current, state, mod)

    def save(self):
        self.config_data["mods_dir"] = self.mods_dir.get().strip()
        # Local test catalogues are deliberately not persisted as the public channel.
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        temp = self.config_path.with_suffix(".tmp")
        temp.write_text(json.dumps(self.config_data, ensure_ascii=False, indent=2), encoding="utf-8")
        temp.replace(self.config_path)

    def choose_folder(self):
        chosen = filedialog.askdirectory(title="Sélectionne le dossier mods du dossier utilisateur BeamNG")
        if chosen:
            path = Path(chosen)
            if path.name.lower() != "mods":
                messagebox.showinfo("Dossier BeamNG", "Sélectionne précisément le dossier nommé « mods ».")
                return
            self.mods_dir.set(chosen)
            self.save()
            if self.catalog_url:
                self.refresh()

    def set_busy(self, busy):
        self.busy = busy
        for widget in (self.refresh_button, self.folder_button, self.folder_entry):
            widget.config(state="disabled" if busy else "normal")
        can_update = bool(self.applications) if self.section == "applications" else bool(self.mods and self.mods_dir.get())
        self.update_button.config(state="disabled" if busy or not can_update else "normal")
        if busy:
            for button in self.cards:
                button.config(state="disabled")

    def run_worker(self, function):
        if self.busy:
            return
        self.set_busy(True)
        def run():
            try:
                self.events.put(("done", function()))
            except Exception as exc:
                self.events.put(("error", (str(exc), traceback.format_exc())))
        threading.Thread(target=run, daemon=True).start()

    def rows(self, mods, folder):
        return [(m, *status(folder, m)) for m in mods]

    def refresh(self):
        if self.busy:
            return
        if not self.catalog_url:
            self.settings()
            return
        folder, url, local = self.mods_dir.get(), self.catalog_url, self.local
        self.message.config(text="Vérification du catalogue et des versions installées…")
        def work():
            mods = load_catalog(url, local)
            if len(mods) > 4:
                raise ValueError("Ce catalogue contient plus de quatre mods.")
            apps = applications.load_apps(url, local)
            # Development/local catalogues never replace the running application.
            if getattr(sys, "frozen", False) and not local:
                for app in apps:
                    if app["id"] == "modcenter" and applications.version(app["version"]) > applications.version(APP_VERSION):
                        self.events.put(("message", "Mise à jour du Mod Center… redémarrage automatique à la fin."))
                        try:
                            exe = applications.install(app, lambda n, total: self.events.put(("progress", n * 100 / total)))
                        except Exception as exc:
                            return (mods, self.rows(mods, folder), "Mise à jour du Mod Center différée : " + str(exc)[:100], apps)
                        self.events.put(("restart", exe))
                        return None
            return (mods, self.rows(mods, folder), "Mode test local" if local else "Catalogue en ligne vérifié", apps)
        self.run_worker(work)

    def update_existing(self):
        if self.section == "applications":
            def work():
                count = 0
                for app in self.applications:
                    state, _ = applications.status(app)
                    if app["id"] != "modcenter" and state == "Mise à jour disponible":
                        applications.install(app, lambda n, total: self.events.put(("progress", n * 100 / total)), self.local)
                        count += 1
                return (self.mods, self.cached_rows,
                        f"{count} application(s) mise(s) à jour. Rouvre-les pour utiliser la nouvelle version." if count else "Les applications installées sont à jour.",
                        self.applications)
            self.run_worker(work)
            return
        # The install worker rechecks status, so newly added mods are never installed by this button.
        self.start_install(self.mods, existing_only=True)

    def start_install(self, mods, existing_only=False):
        if self.busy:
            return
        folder, local = self.mods_dir.get(), self.local
        if not folder:
            self.choose_folder()
            return
        self.save()
        all_mods = list(self.mods)
        def work():
            count = 0
            for mod in mods:
                state, _ = status(folder, mod)
                if state in ("À jour", "Version locale plus récente") or (existing_only and state == "Non installé"):
                    continue
                self.events.put(("message", f"Téléchargement et vérification : {mod['name']}…"))
                install(folder, mod, lambda n, total: self.events.put(("progress", n * 100 / total)), local)
                count += 1
            return (all_mods, self.rows(all_mods, folder),
                    f"{count} mod(s) installé(s). Tu peux lancer BeamNG." if count else "Les mods installés sont à jour.", self.applications)
        self.run_worker(work)

    def poll(self):
        while True:
            try:
                kind, value = self.events.get_nowait()
            except queue.Empty:
                break
            if kind == "restart":
                try:
                    applications.launch(value)
                    self.destroy()
                    return
                except OSError as exc:
                    self.set_busy(False)
                    self.message.config(text="Redémarrage impossible : " + str(exc)[:100])
            elif kind == "done":
                if value is None:
                    continue
                self.mods, rows, message, self.applications = value
                self.set_busy(False)
                self.render(rows)
                self.message.config(text=message)
                self.progress["value"] = 0
            elif kind == "error":
                value, details = value
                try:
                    self.config_path.parent.mkdir(parents=True, exist_ok=True)
                    with self.config_path.with_name("errors.log").open("a", encoding="utf-8") as log:
                        log.write(details + "\n")
                except OSError:
                    pass
                self.set_busy(False)
                self.message.config(text="Opération interrompue : " + value[:120])
                self.progress["value"] = 0
                messagebox.showerror("Mod Center", value)
                self.mods = []
                self.preview()
                self.update_button.config(state="disabled")
            elif kind == "message":
                self.message.config(text=value)
            elif kind == "progress":
                self.progress["value"] = value
        self.after(80, self.poll)

    def discord(self):
        url = self.config_data.get("discord_url", "")
        if url.startswith(("https://discord.gg/", "https://discord.com/invite/")):
            webbrowser.open(url)

    def settings(self):
        if self.busy:
            return
        dialog = tk.Toplevel(self)
        dialog.title("Paramètres du Mod Center")
        dialog.configure(bg=BG)
        dialog.geometry("660x360")
        dialog.transient(self)
        dialog.grab_set()
        self.label(dialog, "Connecter tes mises à jour", 17, TEXT, True).pack(anchor="w", padx=24, pady=(20, 10))
        self.label(dialog, "Adresse HTTPS du catalogue public (catalog.json)", 10, MUTED).pack(anchor="w", padx=24)
        url = tk.StringVar(value=self.config_data.get("catalog_url", ""))
        entry = tk.Entry(dialog, textvariable=url, bg=PANEL, fg=TEXT, insertbackground=TEXT, font=(FONT, 10), bd=8, relief="flat")
        entry.pack(fill="x", padx=24, pady=(6, 14))
        self.label(dialog, "Invitation de ton serveur Discord (facultatif)", 10, MUTED).pack(anchor="w", padx=24)
        discord = tk.StringVar(value=self.config_data.get("discord_url", ""))
        tk.Entry(dialog, textvariable=discord, bg=PANEL, fg=TEXT, insertbackground=TEXT,
                 font=(FONT, 10), bd=8, relief="flat").pack(fill="x", padx=24, pady=(6, 16))
        buttons = tk.Frame(dialog, bg=BG)
        buttons.pack(fill="x", padx=24)
        def save():
            try:
                address = url.get().strip()
                invite = discord.get().strip()
                if address:
                    check_url(address)
                if invite and not invite.startswith(("https://discord.gg/", "https://discord.com/invite/")):
                    raise ValueError("Utilise une invitation discord.gg ou discord.com/invite.")
                self.config_data.update(catalog_url=address, discord_url=invite)
                self.catalog_url, self.local = address, False
                self.save()
                self.mods = []
                self.preview()
                self.update_button.config(state="disabled")
                self.discord_button.config(state="normal" if invite else "disabled")
                dialog.destroy()
                if address:
                    self.refresh()
            except (OSError, ValueError) as exc:
                messagebox.showerror("Configuration", str(exc), parent=dialog)
        def local_catalog():
            path = filedialog.askopenfilename(parent=dialog, title="Catalogue local de test",
                                             filetypes=[("Catalogue JSON", "*.json")])
            if path:
                self.catalog_url, self.local = Path(path).resolve().as_uri(), True
                dialog.destroy()
                self.refresh()
        self.button(buttons, "Catalogue local (test)", local_catalog).pack(side="left")
        self.button(buttons, "Enregistrer", save, True).pack(side="right")

    def close(self):
        if self.busy:
            messagebox.showinfo("Opération en cours", "Attends la fin de l’opération avant de fermer le Mod Center.")
            return
        self.destroy()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--catalog", type=Path, help="Catalogue local pour les tests, jamais mémorisé.")
    parser.add_argument("--config", type=Path, help="Fichier de paramètres alternatif pour les tests.")
    parser.add_argument("--diagnose", type=Path, help="Écrit un diagnostic local du catalogue sans modifier les mods.")
    parser.add_argument("--diagnose-tls", type=Path, help="Vérifie HTTPS sans réseau et sans fenêtre.")
    args = parser.parse_args()
    if args.diagnose:
        raise SystemExit(diagnose(args.diagnose, args.config))
    if args.diagnose_tls:
        raise SystemExit(diagnose(args.diagnose_tls, tls_only=True))
    if not args.catalog and not args.config and applications.handoff("modcenter", APP_VERSION):
        raise SystemExit(0)
    App(args.config, args.catalog).mainloop()
