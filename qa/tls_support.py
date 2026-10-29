"""Verified HTTPS trust shared by downloads, Discord OAuth and diagnostics."""
from pathlib import Path
import ssl
import sys


def ca_bundle_path():
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    return base / "assets" / "cacert.pem"


def tls_context():
    # Keep Windows/system trust and supplement it with the unmodified Mozilla CA list.
    # This also works on Windows Server machines whose system root store is incomplete.
    context = ssl.create_default_context()
    context.load_verify_locations(cafile=str(ca_bundle_path()))
    if context.verify_mode != ssl.CERT_REQUIRED or not context.check_hostname:
        raise RuntimeError("La vérification HTTPS des certificats et du nom d’hôte doit rester active.")
    return context
