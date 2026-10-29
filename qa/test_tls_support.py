"""TLS remains strict even when no Windows/system CA roots are available."""
import hashlib
import io
import json
from pathlib import Path
import ssl
import tempfile
import unittest
from unittest.mock import patch

import core
import tls_support


class PortableTLS(unittest.TestCase):
    def test_bundled_roots_work_with_an_empty_system_store(self):
        empty = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        # The bundled development runtime may preload one bootstrap CA.
        # No Windows/system trust store has been loaded into this context.
        self.assertLessEqual(empty.cert_store_stats()["x509_ca"], 1)
        with patch("tls_support.ssl.create_default_context", return_value=empty):
            context = tls_support.tls_context()
        self.assertGreaterEqual(context.cert_store_stats()["x509_ca"], 100)
        self.assertTrue(context.check_hostname)
        self.assertEqual(context.verify_mode, ssl.CERT_REQUIRED)

    def test_ca_bundle_matches_verified_upstream_checksum(self):
        bundle = tls_support.ca_bundle_path()
        provenance = json.loads(bundle.with_name("certifi-bundle.json").read_text(encoding="utf-8"))
        self.assertEqual(hashlib.sha256(bundle.read_bytes()).hexdigest(), provenance["cacert_sha256"])
        self.assertFalse(provenance["modified"])
        self.assertTrue(provenance["source"].startswith("https://files.pythonhosted.org/"))

    def test_missing_bundle_is_an_error_not_an_unverified_fallback(self):
        with tempfile.TemporaryDirectory() as directory:
            missing = Path(directory) / "missing.pem"
            with patch("tls_support.ca_bundle_path", return_value=missing):
                with self.assertRaises(OSError):
                    tls_support.tls_context()

    def test_disabled_verification_is_refused(self):
        unsafe = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        unsafe.check_hostname = False
        unsafe.verify_mode = ssl.CERT_NONE
        with patch("tls_support.ssl.create_default_context", return_value=unsafe):
            with self.assertRaisesRegex(RuntimeError, "vérification HTTPS"):
                tls_support.tls_context()

    def test_public_catalog_requests_use_portable_verified_context(self):
        class Response(io.BytesIO):
            def geturl(self):
                return "https://example.test/catalog.json"
        with patch("core.urlopen", return_value=Response(b"{}")) as opener:
            with core.open_source("https://example.test/catalog.json") as response:
                self.assertEqual(response.read(), b"{}")
        context = opener.call_args.kwargs["context"]
        self.assertTrue(context.check_hostname)
        self.assertEqual(context.verify_mode, ssl.CERT_REQUIRED)
        self.assertGreaterEqual(context.cert_store_stats()["x509_ca"], 100)


if __name__ == "__main__":
    unittest.main()
