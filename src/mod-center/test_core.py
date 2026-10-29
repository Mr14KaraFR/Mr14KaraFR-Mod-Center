"""Integration tests use only temporary fake mods; the real game is never modified."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile

import core


class Updates(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.mods = self.root / "game/mods"
        self.mods.mkdir(parents=True)
        self.release = self.root / "release"
        self.release.mkdir()
        self.archive = self.release / "example.zip"
        self.write_zip(self.archive, "2.0.0")
        self.entry = dict(id="testmod", name="Test mod", version="2.0.0", filename="example.zip",
                          url=self.archive.as_uri(), size=self.archive.stat().st_size,
                          sha256=core.sha256(self.archive))
        self.catalog = self.release / "catalog.json"
        self.catalog.write_text(json.dumps({"schema": 1, "mods": [self.entry]}), encoding="utf-8")
        self.process = patch("core.game_running", return_value=False)
        self.process.start()
        self.addCleanup(self.process.stop)

    def write_zip(self, path, version, ident="testmod"):
        with zipfile.ZipFile(path, "w") as archive:
            archive.writestr(f"mod_info/{ident}/info.json", json.dumps({"version": version}))
            archive.writestr("lua/ge/extensions/test.lua", "return {}")

    def install(self, entry=None):
        return core.install(self.mods, entry or self.entry, local=True)

    def test_fresh_install_and_status(self):
        self.assertEqual(core.status(self.mods, self.entry)[0], "Non installé")
        self.install()
        self.assertEqual(core.status(self.mods, self.entry)[0], "À jour")
        self.assertEqual(core.sha256(self.mods / "example.zip"), self.entry["sha256"])

    def test_update_backs_up_and_removes_legacy_duplicates(self):
        legacy = self.mods / "old-name.zip"
        self.write_zip(legacy, "1.0.0")
        repo = self.mods / "repo"
        repo.mkdir()
        duplicate = repo / "older.zip"
        self.write_zip(duplicate, "0.5.0")
        backup = self.install()
        self.assertFalse(legacy.exists())
        self.assertFalse(duplicate.exists())
        self.assertEqual(len(list(backup.glob("*.zip"))), 2)
        self.assertTrue((backup / "restore.json").exists())

    def test_corrupt_download_preserves_original(self):
        original = self.mods / "example.zip"
        self.write_zip(original, "1.0.0")
        before = original.read_bytes()
        entry = {**self.entry, "sha256": "0" * 64}
        with self.assertRaisesRegex(ValueError, "SHA-256"):
            self.install(entry)
        self.assertEqual(original.read_bytes(), before)
        self.assertFalse(list(self.mods.glob("*.download")))

    def test_wrong_archive_version_preserves_original(self):
        with self.assertRaisesRegex(ValueError, "version du ZIP"):
            self.install({**self.entry, "version": "3.0.0"})
        self.assertFalse((self.mods / "example.zip").exists())

    def test_wrong_archive_identity_is_rejected(self):
        with self.assertRaises(KeyError):
            self.install({**self.entry, "id": "othermod"})
        self.assertFalse((self.mods / "example.zip").exists())

    def test_refuse_downgrade_and_unrelated_file(self):
        target = self.mods / "example.zip"
        self.write_zip(target, "3.0.0")
        with self.assertRaisesRegex(ValueError, "plus récente"):
            self.install()
        self.write_zip(target, "1.0.0", "unrelated")
        with self.assertRaisesRegex(ValueError, "autre mod"):
            self.install()

    def test_rollback_after_duplicate_cleanup_failure(self):
        old = self.mods / "old.zip"
        self.write_zip(old, "1.0.0")
        before = old.read_bytes()
        original_unlink = Path.unlink
        def fail(path, *args, **kwargs):
            if path == old:
                raise PermissionError("locked duplicate")
            return original_unlink(path, *args, **kwargs)
        with patch.object(Path, "unlink", fail):
            with self.assertRaises(PermissionError):
                self.install()
        self.assertEqual(old.read_bytes(), before)
        self.assertFalse((self.mods / "example.zip").exists())

    def test_game_running_stops_install(self):
        with patch("core.game_running", return_value=True):
            with self.assertRaisesRegex(RuntimeError, "Fermez BeamNG"):
                self.install()
        self.assertFalse((self.mods / "example.zip").exists())

    def test_http_and_remote_file_catalogues_rejected(self):
        for url in ("http://example.com/catalog.json", self.catalog.as_uri(), "file://server/share/catalog.json"):
            with self.assertRaises(ValueError):
                core.load_catalog(url)

    def test_local_catalogue_and_relative_download(self):
        entry = {**self.entry, "url": "example.zip"}
        self.catalog.write_text(json.dumps({"schema": 1, "mods": [entry]}))
        mods = core.load_catalog(self.catalog.as_uri(), local=True)
        self.assertEqual(mods[0]["url"], self.archive.as_uri())

    def test_filename_traversal_and_duplicate_ids_rejected(self):
        for filename in ("../escape.zip", "C:/escape.zip", "CON.zip", "bad.exe", "a\\b.zip"):
            self.catalog.write_text(json.dumps({"schema": 1, "mods": [{**self.entry, "filename": filename}]}))
            with self.assertRaises(ValueError):
                core.load_catalog(self.catalog.as_uri(), local=True)
        self.catalog.write_text(json.dumps({"schema": 1, "mods": [self.entry, self.entry]}))
        with self.assertRaises(ValueError):
            core.load_catalog(self.catalog.as_uri(), local=True)

    def test_overlong_download_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "taille annoncée"):
            self.install({**self.entry, "size": 1})
        self.assertFalse((self.mods / "example.zip").exists())

    def test_install_lock_excludes_another_writer(self):
        with core.install_lock(self.mods):
            with self.assertRaisesRegex(RuntimeError, "autre installation"):
                self.install()

    def test_hq_version_and_empty_folder(self):
        self.assertGreater(core.version("6.69.0-HQ"), core.version("6.68.0-HQ"))
        self.assertEqual(core.installed("", self.entry), [])


if __name__ == "__main__":
    unittest.main()
