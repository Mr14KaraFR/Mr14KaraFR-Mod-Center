import io
import json
from pathlib import Path
import tempfile
import unittest
from contextlib import contextmanager
from unittest.mock import patch
import zipfile
import core


class AuthenticatedInstallation(unittest.TestCase):
    def test_private_zip_is_verified_and_auth_is_only_sent_on_download(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            folder=root/"mods";folder.mkdir()
            source=root/"source.zip"
            with zipfile.ZipFile(source,"w") as z:
                z.writestr("mod_info/example/info.json",json.dumps({"version":"1.0.0"}))
            entry=dict(id="example",name="Example",filename="example.zip",version="1.0.0",
                size=source.stat().st_size,sha256=core.sha256(source),
                url="https://private.example/download/stable/example/"+core.sha256(source),
                access="subscriber",locked=False)
            calls=[]
            @contextmanager
            def download(url,local=False,headers=None,data=None):
                calls.append((url,headers))
                with source.open("rb") as stream: yield stream
            with patch("core.open_source",download),patch("core.game_running",return_value=False):
                core.install(folder,entry,download_headers={"Authorization":"Bearer test-session"})
            self.assertEqual(calls,[(entry["url"],{"Authorization":"Bearer test-session"})])
            self.assertEqual(core.sha256(folder/"example.zip"),entry["sha256"])

    def test_denied_private_download_preserves_installed_mod(self):
        with tempfile.TemporaryDirectory() as directory:
            folder=Path(directory)/"mods";folder.mkdir()
            target=folder/"example.zip"
            with zipfile.ZipFile(target,"w") as z:
                z.writestr("mod_info/example/info.json",json.dumps({"version":"1.0.0"}))
            before=target.read_bytes()
            entry=dict(id="example",name="Example",filename="example.zip",version="2.0.0",
                size=1,sha256="a"*64,url="https://private.example/download")
            with patch("core.open_source",side_effect=PermissionError("Forbidden")),patch("core.game_running",return_value=False):
                with self.assertRaises(PermissionError):
                    core.install(folder,entry,download_headers={"Authorization":"Bearer test"})
            self.assertEqual(target.read_bytes(),before)
            self.assertFalse(list(folder.glob("*.download")))

if __name__=="__main__": unittest.main()
