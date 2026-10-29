"""Direct Discord OAuth2/PKCE for the GitHub trial distribution.

No bot token/client secret. User tokens stay in memory and are sent only to Discord.
"""
import base64
import hashlib
import hmac
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import re
import secrets
import threading
import time
from urllib.error import HTTPError
from urllib.parse import urlencode, urlsplit, parse_qs
from urllib.request import Request, build_opener, HTTPRedirectHandler, HTTPSHandler
from tls_support import tls_context
import webbrowser

from core import load_catalog, APP_VERSION

DISCORD_API = "https://discord.com/api/v10"
TOKEN_URL = "https://discord.com/api/oauth2/token"
REVOKE_URL = "https://discord.com/api/oauth2/token/revoke"
ISSUER = "https://discord.com"
GITHUB_PREFIX = "https://github.com/Mr14KaraFR/Mr14KaraFR-Mod-Center/releases/"
SCOPES = {"identify", "guilds.members.read"}
CALLBACK_PORT = 47619
REDIRECT_URI = f"http://127.0.0.1:{CALLBACK_PORT}/callback"


def pkce_pair():
    verifier = secrets.token_urlsafe(32)
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode("ascii")).digest()).rstrip(b"=").decode("ascii")
    return verifier, challenge


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ValueError("Discord ne doit pas rediriger les requêtes authentifiées.")


def discord_json(url, token=None, form=None):
    parsed = urlsplit(url)
    if parsed.scheme != "https" or parsed.netloc != "discord.com" or not parsed.path.startswith("/api/"):
        raise ValueError("Adresse Discord non autorisée.")
    headers = {"User-Agent": f"Mr14KaraFR-ModCenter/{APP_VERSION}"}
    if token:
        headers["Authorization"] = "Bearer " + token
    data = None
    if form is not None:
        headers["Content-Type"] = "application/x-www-form-urlencoded"
        data = urlencode(form).encode("ascii")
    try:
        with build_opener(HTTPSHandler(context=tls_context()), NoRedirect()).open(Request(url, data=data, headers=headers), timeout=20) as response:
            raw = response.read(1024 * 1024 + 1)
            if len(raw) > 1024 * 1024:
                raise ValueError("Réponse Discord trop volumineuse.")
            # Revocation may return an empty body.
            return json.loads(raw) if raw else {}
    except HTTPError as exc:
        messages = {401: "Connexion Discord expirée. Reconnecte-toi.",
                    403: "Discord refuse cet accès. Vérifie les autorisations de connexion.",
                    404: "Rejoins le serveur Discord Mr14KaraFR pour accéder aux mods.",
                    429: "Discord reçoit trop de demandes. Patiente puis réessaie."}
        raise ValueError(messages.get(exc.code, "Connexion Discord indisponible. Réessaie plus tard.")) from None


def validate_callback(path, host, state):
    parsed = urlsplit(path)
    if host != f"127.0.0.1:{CALLBACK_PORT}" or parsed.path != "/callback" or len(path) > 8192:
        raise ValueError("Adresse de retour invalide.")
    values = parse_qs(parsed.query, keep_blank_values=True)
    if len(values.get("state", [])) != 1 or not hmac.compare_digest(values["state"][0], state):
        raise ValueError("État de connexion invalide.")
    if values.get("iss") != [ISSUER]:
        raise ValueError("Émetteur de connexion invalide.")
    if "error" in values:
        raise PermissionError("Connexion Discord refusée.")
    codes = values.get("code", [])
    if len(codes) != 1 or not 1 <= len(codes[0]) <= 2048:
        raise ValueError("Code de connexion absent.")
    return codes[0]


class CallbackServer(HTTPServer):
    allow_reuse_address = False

    def get_request(self):
        connection, address = super().get_request()
        connection.settimeout(2)
        return connection, address


def receive_authorization(client_id, cancel, notify, timeout=600):
    verifier, challenge = pkce_pair()
    state = secrets.token_urlsafe(32)
    result = {}

    class Callback(BaseHTTPRequestHandler):
        def log_message(self, *_args):
            pass  # The request URL contains an authorization code: never log it.

        def do_GET(self):
            try:
                result["code"] = validate_callback(self.path, self.headers.get("Host"), state)
                message = "Connexion reçue. Tu peux revenir au Mod Center."
                status = 200
            except PermissionError:
                result["denied"] = True
                message, status = "Connexion annulée. Reviens au Mod Center.", 200
            except ValueError:
                message, status = "Retour invalide. Recommence depuis le Mod Center.", 400
            raw = ("<!doctype html><html lang=fr><meta charset=utf-8><title>Mod Center</title>"
                   "<style>body{font:20px system-ui;background:#0b101b;color:#edf3ff;padding:8vw}</style>"
                   "<h1>Mr14KaraFR Mod Center</h1><p>" + message + "</p></html>").encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(raw)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("Referrer-Policy", "no-referrer")
            self.send_header("Content-Security-Policy", "default-src 'none'; style-src 'unsafe-inline'; frame-ancestors 'none'")
            self.end_headers()
            try:
                self.wfile.write(raw)
            except OSError:
                pass

    try:
        server = CallbackServer(("127.0.0.1", CALLBACK_PORT), Callback)
    except OSError:
        raise ValueError("Le port de connexion Discord est occupé. Ferme l’autre Mod Center puis réessaie.") from None
    with server:
        server.timeout = 0.5
        url = ISSUER + "/oauth2/authorize?" + urlencode({
            "client_id": client_id, "response_type": "code", "redirect_uri": REDIRECT_URI,
            "scope": " ".join(sorted(SCOPES)), "state": state,
            "code_challenge": challenge, "code_challenge_method": "S256", "prompt": "consent"})
        if not webbrowser.open(url):
            raise ValueError("Impossible d’ouvrir le navigateur pour la connexion Discord.")
        notify("Autorise la connexion dans ton navigateur, puis reviens au Mod Center.")
        deadline = time.monotonic() + timeout
        while "code" not in result and not result.get("denied"):
            if cancel.is_set():
                raise ValueError("Connexion annulée.")
            if time.monotonic() >= deadline:
                raise ValueError("Connexion expirée. Clique à nouveau sur Se connecter avec Discord.")
            server.handle_request()
    if result.get("denied"):
        raise ValueError("Connexion Discord refusée.")
    return result["code"], verifier


class DiscordAccess:
    origin = ISSUER

    def __init__(self, config, catalog_url):
        self.config = dict(config)
        for field in ("client_id", "guild_id", "subscriber_role_id", "beta_role_id"):
            if not re.fullmatch(r"\d{17,22}", str(config.get(field, ""))):
                raise ValueError("Connexion Discord à configurer : " + field)
        if config.get("owner_user_id") and not re.fullmatch(r"\d{17,22}", config["owner_user_id"]):
            raise ValueError("Identifiant du propriétaire invalide.")
        self.catalog_url = catalog_url
        self.beta_catalog_url = config.get("beta_catalog_url", "")
        self.session = None
        self.refresh_token = None
        self.expires = 0

    def set_tokens(self, value):
        if (value.get("token_type", "").lower() != "bearer" or
                not SCOPES.issubset(set(value.get("scope", "").split())) or
                not isinstance(value.get("access_token"), str) or not value["access_token"] or
                type(value.get("expires_in")) is not int or value["expires_in"] <= 0):
            raise ValueError("Discord n’a pas accordé les autorisations nécessaires.")
        self.session = value["access_token"]
        self.refresh_token = value.get("refresh_token")
        self.expires = time.monotonic() + value["expires_in"]

    def login(self, cancel=None, notify=lambda text: None):
        cancel = cancel or threading.Event()
        code, verifier = receive_authorization(self.config["client_id"], cancel, notify)
        value = discord_json(TOKEN_URL, form={"client_id": self.config["client_id"],
            "grant_type": "authorization_code", "code": code, "code_verifier": verifier,
            "redirect_uri": REDIRECT_URI})
        self.set_tokens(value)
        try:
            return self.account()
        except Exception:
            self.clear()
            raise

    def ensure_token(self):
        if not self.session:
            raise ValueError("Connecte-toi avec Discord pour accéder à cette version.")
        if self.expires <= time.monotonic() + 60:
            if not self.refresh_token:
                self.clear()
                raise ValueError("Connexion Discord expirée. Reconnecte-toi.")
            try:
                self.set_tokens(discord_json(TOKEN_URL, form={"client_id": self.config["client_id"],
                    "grant_type": "refresh_token", "refresh_token": self.refresh_token}))
            except Exception:
                self.clear()
                raise

    def account(self):
        self.ensure_token()
        user = discord_json(DISCORD_API + "/users/@me", token=self.session)
        member = discord_json(DISCORD_API + "/users/@me/guilds/" + self.config["guild_id"] + "/member", token=self.session)
        if member.get("user", {}).get("id") != user.get("id"):
            raise ValueError("Le compte Discord ne correspond pas au membre du serveur.")
        roles = member.get("roles", [])
        if not isinstance(roles, list):
            raise ValueError("Liste des rôles Discord invalide.")
        owner = bool(self.config.get("owner_user_id")) and user["id"] == self.config["owner_user_id"]
        return {"user": {"id": user["id"], "name": user.get("global_name") or user["username"]},
                "subscriber": owner or self.config["subscriber_role_id"] in roles,
                "beta": owner or self.config["beta_role_id"] in roles}

    def clear(self):
        self.session = self.refresh_token = None
        self.expires = 0

    def logout(self):
        token = self.refresh_token or self.session
        self.clear()
        if token:
            discord_json(REVOKE_URL, form={"client_id": self.config["client_id"], "token": token})

    @staticmethod
    def validate_github(url):
        parsed = urlsplit(url)
        if not url.startswith(GITHUB_PREFIX) or parsed.username or parsed.password or parsed.fragment:
            raise ValueError("Ce fichier ne provient pas des publications officielles GitHub.")

    def catalog(self, channel="stable"):
        if channel not in ("stable", "beta"):
            raise ValueError("Canal de versions inconnu.")
        rights = self.account() if self.session else {"subscriber": False, "beta": False}
        if channel == "beta":
            if not rights["beta"]:
                raise ValueError("Le rôle Bêta-testeur est nécessaire.")
            if not self.beta_catalog_url:
                return []  # No test build is advertised until a real beta catalog exists.
            url = self.beta_catalog_url
        else:
            url = self.catalog_url
        self.validate_github(url)
        entries = load_catalog(url)
        for mod in entries:
            self.validate_github(mod["url"])
            mod.update(access="beta" if channel == "beta" else "subscriber",
                       locked=not rights["beta" if channel == "beta" else "subscriber"])
        return entries

    def download_headers(self, mod):
        # Called immediately before installation, regardless of cached card state.
        rights = self.account()
        access = mod.get("access")
        if access not in ("subscriber", "beta") or not rights["beta" if access == "beta" else "subscriber"]:
            raise ValueError("Ton rôle Discord ne donne pas accès à cette version.")
        self.validate_github(mod["url"])
        return None  # Never send Discord credentials to GitHub or its download CDN.
