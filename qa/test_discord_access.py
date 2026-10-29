import hashlib
import time
import unittest
from unittest.mock import patch
from urllib.parse import urlencode
from discord_access import (DiscordAccess, SCOPES, REDIRECT_URI, CALLBACK_PORT, pkce_pair,
                            validate_callback, discord_json, GITHUB_PREFIX)

CONFIG = {"client_id":"1565374469550116864","guild_id":"1565343607471341708",
          "subscriber_role_id":"1565346784358699180","beta_role_id":"1565357181140738118"}
USER = {"id":"123456789012345678","username":"test"}
ENTRY = {"id":"example","url":GITHUB_PREFIX+"download/release/example.zip"}


class DiscordTrial(unittest.TestCase):
    def client(self, roles=()):
        client = DiscordAccess(CONFIG, GITHUB_PREFIX+"latest/download/catalog.json")
        client.session = "test-bearer"
        client.expires = time.monotonic()+3600
        return client

    def api(self, roles):
        def call(url, token=None, form=None):
            self.assertEqual(token,"test-bearer")
            return {"user":USER,"roles":list(roles)} if url.endswith("/member") else USER
        return call

    def test_pkce_random_and_sha256_challenge(self):
        import base64
        verifier, challenge = pkce_pair()
        self.assertNotEqual(verifier,pkce_pair()[0])
        self.assertGreaterEqual(len(verifier),43)
        self.assertEqual(challenge,base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b"=").decode())

    def test_callback_rejects_wrong_state_host_issuer_and_duplicate_codes(self):
        state="test-random-state"
        query={"state":state,"code":"one-use-code","iss":"https://discord.com"}
        path="/callback?"+urlencode(query)
        host=f"127.0.0.1:{CALLBACK_PORT}"
        self.assertEqual(validate_callback(path,host,state),"one-use-code")
        for modified,modified_host in ((path,"evil.example"),(path.replace(state,"wrong"),host),
                (path.replace("discord.com","other.example"),host),(path+"&code=second",host)):
            with self.assertRaises(ValueError): validate_callback(modified,modified_host,state)
        with self.assertRaises(PermissionError):
            validate_callback("/callback?"+urlencode({**query,"error":"access_denied"}),host,state)

    def test_no_secret_is_used_in_pkce_token_exchange(self):
        client=self.client()
        with patch("discord_access.receive_authorization",return_value=("code","verifier")),patch(
                "discord_access.discord_json",return_value={"token_type":"Bearer","scope":" ".join(SCOPES),
                "access_token":"test","expires_in":3600}) as token,patch.object(client,"account",return_value={"subscriber":True}):
            client.login()
        form=token.call_args.kwargs["form"]
        self.assertEqual(form["client_id"],CONFIG["client_id"])
        self.assertEqual(form["code_verifier"],"verifier")
        self.assertNotIn("client_secret",form)
        self.assertEqual(form["redirect_uri"],REDIRECT_URI)

    def test_role_checks_are_live_and_do_not_send_tokens_to_github(self):
        client=self.client()
        with patch("discord_access.discord_json",side_effect=self.api([CONFIG["subscriber_role_id"]])),patch(
                "discord_access.load_catalog",return_value=[dict(ENTRY)]) as catalog:
            mods=client.catalog()
            self.assertFalse(mods[0]["locked"])
            self.assertIsNone(client.download_headers(mods[0]))
            self.assertEqual(catalog.call_args.kwargs,{})
        with patch("discord_access.discord_json",side_effect=self.api([])):
            with self.assertRaisesRegex(ValueError,"rôle"):
                client.download_headers(mods[0])

    def test_beta_and_subscriber_are_separate(self):
        client=self.client()
        with patch("discord_access.discord_json",side_effect=self.api([CONFIG["beta_role_id"]])):
            account=client.account()
            self.assertTrue(account["beta"])
            self.assertFalse(account["subscriber"])
            with self.assertRaises(ValueError): client.download_headers({**ENTRY,"access":"subscriber"})
            self.assertIsNone(client.download_headers({**ENTRY,"access":"beta"}))
            self.assertEqual(client.catalog("beta"),[])  # no fake beta release

    def test_logged_out_catalog_is_locked(self):
        client=DiscordAccess(CONFIG,GITHUB_PREFIX+"latest/download/catalog.json")
        with patch("discord_access.load_catalog",return_value=[dict(ENTRY)]) as load:
            self.assertTrue(client.catalog()[0]["locked"])
            self.assertNotIn("headers",load.call_args.kwargs)
        with self.assertRaises(ValueError): client.catalog("beta")

    def test_foreign_url_and_mismatched_identity_are_rejected(self):
        client=self.client()
        for url in ("https://evil.test/mod.zip","https://github.com/other/repo/releases/mod.zip"):
            with self.assertRaises(ValueError): client.validate_github(url)
        with patch("discord_access.discord_json",side_effect=[USER,{"user":{"id":"999"},"roles":[]}]):
            with self.assertRaisesRegex(ValueError,"correspond"):client.account()
        with self.assertRaises(ValueError):discord_json("https://evil.test/api/user",token="must-not-leak")

    def test_logout_always_clears_memory(self):
        client=self.client()
        with patch("discord_access.discord_json",side_effect=OSError("offline")):
            with self.assertRaises(OSError):client.logout()
        self.assertIsNone(client.session)

    def test_refresh_failure_clears_expired_session(self):
        client=self.client();client.expires=0;client.refresh_token="refresh"
        with patch("discord_access.discord_json",side_effect=ValueError("expired")):
            with self.assertRaises(ValueError):client.account()
        self.assertIsNone(client.session)

    def test_owner_has_both_accesses_without_assigning_paid_roles(self):
        client=DiscordAccess({**CONFIG,"owner_user_id":USER["id"]},GITHUB_PREFIX+"latest/download/catalog.json")
        client.session="test-bearer";client.expires=time.monotonic()+3600
        with patch("discord_access.discord_json",side_effect=self.api([])):
            self.assertTrue(client.account()["subscriber"])
            self.assertTrue(client.account()["beta"])

    def test_missing_scope_is_rejected_without_keeping_tokens(self):
        client=DiscordAccess(CONFIG,GITHUB_PREFIX+"latest/download/catalog.json")
        with self.assertRaises(ValueError):
            client.set_tokens({"token_type":"Bearer","scope":"identify","access_token":"test","expires_in":3600})
        self.assertIsNone(client.session)

    def test_real_loopback_callback_and_pkce_correspondence(self):
        import base64
        import threading
        from urllib.parse import urlsplit,parse_qs
        from urllib.request import build_opener, ProxyHandler
        from discord_access import receive_authorization
        opened=[]
        errors=[]
        def open_browser(url):
            opened.append(url)
            params=parse_qs(urlsplit(url).query)
            def return_code():
                try:
                    target=REDIRECT_URI+"?"+urlencode({"code":"test-code","state":params["state"][0],
                                                      "iss":"https://discord.com"})
                    with build_opener(ProxyHandler({})).open(target,timeout=3) as response:
                        self.assertEqual(response.status,200)
                except Exception as error:
                    errors.append(error)
                    print("Loopback test error:", type(error).__name__, str(error))
            threading.Thread(target=return_code,daemon=True).start()
            return True
        with patch("discord_access.webbrowser.open",side_effect=open_browser):
            code,verifier=receive_authorization(CONFIG["client_id"],threading.Event(),lambda text:None,timeout=5)
        self.assertEqual(code,"test-code")
        self.assertFalse(errors)
        params=parse_qs(urlsplit(opened[0]).query)
        self.assertEqual(set(params["scope"][0].split()),SCOPES)
        expected=base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b"=").decode()
        self.assertEqual(params["code_challenge"],[expected])
        self.assertNotIn("client_secret",params)

    def test_cancelled_login_releases_local_listener(self):
        import threading
        from discord_access import receive_authorization,CallbackServer
        cancel=threading.Event();cancel.set()
        with patch("discord_access.webbrowser.open",return_value=True):
            with self.assertRaisesRegex(ValueError,"annulée"):
                receive_authorization(CONFIG["client_id"],cancel,lambda text:None,timeout=5)
        # The next login can bind to the exact registered callback port.
        with CallbackServer(("127.0.0.1",CALLBACK_PORT), __import__("http.server",fromlist=["BaseHTTPRequestHandler"]).BaseHTTPRequestHandler):
            pass

if __name__=="__main__":unittest.main()
