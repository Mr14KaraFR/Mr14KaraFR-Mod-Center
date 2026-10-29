"""Discord login for the private mod service. Only an opaque session stays in RAM."""
import hashlib
import json
import secrets
import threading
import time
import webbrowser
from urllib.error import HTTPError
from urllib.parse import urlparse
from core import check_url, open_source, load_catalog, MAX_CATALOG


class PrivateAccess:
    def __init__(self, origin):
        origin = origin.rstrip("/")
        check_url(origin)
        parsed = urlparse(origin)
        if parsed.path or parsed.query or parsed.fragment:
            raise ValueError("L’adresse du service privé doit être une origine HTTPS.")
        self.origin = origin
        self.session = None

    def request(self, path, data=None, authenticated=False):
        # Fixed service-relative endpoints; credentials never go to catalog-supplied URLs.
        if not path.startswith("/") or path.startswith("//"):
            raise ValueError("Adresse privée invalide.")
        headers = self.headers() if authenticated else {}
        raw = None if data is None else json.dumps(data).encode("utf-8")
        if raw is not None:
            headers["Content-Type"] = "application/json"
        try:
            with open_source(self.origin + path, headers=headers, data=raw) as stream:
                content = stream.read(MAX_CATALOG + 1)
            if len(content) > MAX_CATALOG:
                raise ValueError("Réponse du service trop volumineuse.")
            return json.loads(content)
        except HTTPError as exc:
            messages = {401: "Connecte-toi à nouveau avec Discord.",
                        403: "Ton rôle Discord ne donne pas accès à cette version.",
                        429: "Trop de demandes. Patiente avant de réessayer."}
            raise ValueError(messages.get(exc.code, "Service privé indisponible. Réessaie plus tard.")) from None

    def headers(self):
        if not self.session:
            raise ValueError("Connecte-toi avec Discord pour télécharger cette version.")
        return {"Authorization": "Bearer " + self.session}

    def login(self, cancel=None, notify=lambda message: None):
        cancel = cancel or threading.Event()
        verifier = secrets.token_hex(32)
        start = self.request("/auth/start", {"challenge": hashlib.sha256(verifier.encode()).hexdigest()})
        login_url = start.get("login_url", "")
        if (urlparse(login_url).scheme, urlparse(login_url).netloc) != (
                urlparse(self.origin).scheme, urlparse(self.origin).netloc):
            raise ValueError("Adresse de connexion incorrecte.")
        if urlparse(login_url).path != "/auth/login":
            raise ValueError("Adresse de connexion incorrecte.")
        if not webbrowser.open(login_url):
            raise ValueError("Impossible d’ouvrir le navigateur pour la connexion Discord.")
        notify("Autorise la connexion dans ton navigateur, puis reviens au Mod Center.")
        deadline = time.monotonic() + min(int(start.get("expires_in", 600)), 600)
        interval = max(5, min(int(start.get("interval", 5)), 15))
        while time.monotonic() < deadline:
            if cancel.wait(interval):
                raise ValueError("Connexion annulée.")
            result = self.request("/auth/poll", {"flow": start["flow"], "verifier": verifier})
            if result.get("status") == "denied":
                raise ValueError("Connexion Discord refusée ou interrompue.")
            if result.get("status") == "ready":
                self.session = verifier
                try:
                    return self.account()
                except Exception:
                    self.session = None
                    raise
        raise ValueError("Connexion expirée. Clique à nouveau sur Se connecter avec Discord.")

    def account(self):
        return self.request("/me", authenticated=True)

    def logout(self):
        try:
            if self.session:
                self.request("/logout", {}, authenticated=True)
        finally:
            self.session = None

    def catalog(self, channel="stable"):
        if channel not in ("stable", "beta"):
            raise ValueError("Canal inconnu.")
        return load_catalog(self.origin + "/catalog?channel=" + channel,
                            headers=self.headers() if self.session else None)

    def download_headers(self, mod):
        parsed = urlparse(mod["url"])
        origin = urlparse(self.origin)
        if (parsed.scheme, parsed.netloc) != (origin.scheme, origin.netloc) or not parsed.path.startswith("/download/"):
            raise ValueError("Le téléchargement privé ne provient pas du service configuré.")
        if mod.get("locked", True):
            raise ValueError("Ton rôle Discord ne donne pas accès à cette version.")
        return self.headers()
