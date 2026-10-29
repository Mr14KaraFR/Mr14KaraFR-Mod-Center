import io
import json
import unittest
from contextlib import contextmanager
from unittest.mock import patch
from urllib.error import HTTPError
import core
from private_access import PrivateAccess


class PrivateDownloads(unittest.TestCase):
    def test_authentication_never_follows_redirects(self):
        handler = core.NoPrivateRedirect()
        from urllib.request import Request
        with self.assertRaisesRegex(ValueError, "redirigé"):
            handler.redirect_request(Request("https://service.test/download", headers={"Authorization":"Bearer secret"}),
                                     None, 302, "", {}, "https://elsewhere.test/leak")

    def test_credentials_cannot_go_to_foreign_downloads(self):
        client = PrivateAccess("https://service.test")
        client.session = "a" * 64
        with self.assertRaisesRegex(ValueError, "service configuré"):
            client.download_headers({"url":"https://evil.test/download/a", "locked":False})
        with self.assertRaisesRegex(ValueError, "rôle"):
            client.download_headers({"url":"https://service.test/download/a", "locked":True})
        self.assertEqual(client.download_headers({"url":"https://service.test/download/a", "locked":False}),
                         {"Authorization":"Bearer "+"a"*64})

    def test_catalog_does_not_fallback_to_public_when_denied(self):
        client = PrivateAccess("https://service.test")
        client.session = "b"*64
        with patch("private_access.load_catalog", side_effect=HTTPError("https://service.test/catalog",403,"Forbidden",{},None)) as load:
            with self.assertRaises(HTTPError):
                client.catalog("beta")
            self.assertEqual(load.call_count,1)
            self.assertEqual(load.call_args.kwargs["headers"],client.headers())

    def test_logout_erases_local_session_even_if_network_fails(self):
        client=PrivateAccess("https://service.test")
        client.session="c"*64
        with patch.object(client,"request",side_effect=OSError("offline")):
            with self.assertRaises(OSError): client.logout()
        self.assertIsNone(client.session)

    def test_service_origin_validation(self):
        for value in ["http://service.test","https://service.test/other","https://service.test?x=y"]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                PrivateAccess(value)

    def test_http_error_hides_provider_and_secret_details(self):
        client=PrivateAccess("https://service.test")
        with patch("private_access.open_source",side_effect=HTTPError("https://service.test/me",401,"sensitive",{},None)):
            with self.assertRaisesRegex(ValueError,"nouveau"):
                client.request("/me")

if __name__=="__main__": unittest.main()
