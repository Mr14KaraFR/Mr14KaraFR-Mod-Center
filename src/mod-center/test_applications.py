"""Application update tests: temporary fake EXEs, never touches the game or user apps."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile

import applications as apps
from core import sha256


class ApplicationUpdates(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.install_root = self.root / "installed"
        self.entry = self.package("1.0.0")

    def package(self, version, files=None, manifest=None):
        path = self.root / (version + ".zip")
        with zipfile.ZipFile(path, "w") as archive:
            archive.writestr("application.json", json.dumps(manifest or {
                "id": "ecustudio", "version": version, "executable": "ECU-Studio.exe"}))
            for name, value in (files or {"ECU-Studio.exe": "fake program", "_internal/test": "dependency"}).items():
                info = zipfile.ZipInfo()
                info.filename = name
                archive.writestr(info, value)
        return dict(id="ecustudio", name="ECU Studio", version=version,
                    size=path.stat().st_size, sha256=sha256(path), url=path.as_uri())

    def install(self, entry=None, probe=False):
        return apps.install(entry or self.entry, local=True, root=self.install_root, probe=probe)

    def test_install_outside_game_and_status(self):
        self.assertEqual(apps.status(self.entry, self.install_root)[0], "Non installé")
        exe = self.install()
        self.assertTrue(exe.is_file())
        self.assertEqual(apps.status(self.entry, self.install_root), ("À jour", "1.0.0"))

    def test_update_keeps_old_executable_and_switches_pointer(self):
        old = self.install()
        new = self.install(self.package("2.0.0"))
        self.assertNotEqual(old, new)
        self.assertTrue(old.is_file())
        self.assertEqual(apps.current("ecustudio", self.install_root)["exe"], new)

    def test_corrupt_download_preserves_current(self):
        old = self.install()
        bad = {**self.package("2.0.0"), "sha256": "0" * 64}
        with self.assertRaisesRegex(ValueError, "SHA-256"):
            self.install(bad)
        self.assertEqual(apps.current("ecustudio", self.install_root)["exe"], old)

    def test_probe_failure_preserves_current(self):
        old = self.install()
        with patch("applications.subprocess.run", side_effect=OSError("cannot launch")):
            with self.assertRaises(OSError):
                self.install(self.package("2.0.0"), probe=True)
        self.assertEqual(apps.current("ecustudio", self.install_root)["exe"], old)

    def test_probe_checks_real_staged_executable_before_switch(self):
        with patch("applications.subprocess.run") as run:
            self.install(probe=True)
        self.assertEqual(run.call_args.args[0][1:], ["--diagnose-tls", "-"])

    def test_refuse_downgrade(self):
        self.install(self.package("2.0.0"))
        with self.assertRaisesRegex(ValueError, "plus récente"):
            self.install()

    def test_manifest_mismatch(self):
        entry = self.package("1.0.0", manifest={"id": "modcenter"})
        with self.assertRaisesRegex(ValueError, "Identité"):
            self.install(entry)
        self.assertIsNone(apps.current("ecustudio", self.install_root))

    def test_archive_traversal_and_windows_paths_rejected(self):
        for path in ("../escape.exe", "C:/escape.exe", "dir/CON.txt", "dir/file:stream",
                     "dir/../escape", "dir/back\\..\\..\\escape", "dir/trailing.", "/absolute"):
            with self.subTest(path=path):
                entry = self.package("1.0.0", files={"ECU-Studio.exe": "fake", path: "bad"})
                with self.assertRaisesRegex(ValueError, "Chemin dangereux"):
                    self.install(entry)
        self.assertFalse((self.root / "escape.exe").exists())

    def test_missing_executable_rejected(self):
        with self.assertRaisesRegex(ValueError, "Exécutable absent"):
            self.install(self.package("1.0.0", files={"wrong.exe": "bad"}))

    def test_installs_locked_against_concurrent_processes(self):
        from core import install_lock
        base = self.install_root / "ecustudio"
        base.mkdir(parents=True)
        with install_lock(base):
            with self.assertRaisesRegex(RuntimeError, "autre installation"):
                self.install()

    def test_old_catalogue_remains_compatible(self):
        path = self.root / "catalog.json"
        path.write_text(json.dumps({"schema": 1, "mods": []}))
        self.assertEqual(apps.load_apps(path.as_uri(), local=True), [])

    def test_catalogue_validation_and_relative_urls(self):
        path = self.root / "catalog.json"
        entry = {**self.entry, "url": "1.0.0.zip"}
        path.write_text(json.dumps({"schema": 1, "mods": [], "applications": [entry]}))
        self.assertEqual(apps.load_apps(path.as_uri(), local=True)[0]["url"], self.entry["url"])
        path.write_text(json.dumps({"schema": 1, "mods": [], "applications": [entry, entry]}))
        with self.assertRaisesRegex(ValueError, "deux fois"):
            apps.load_apps(path.as_uri(), local=True)

    def test_malformed_pointer_does_not_launch(self):
        base = self.install_root / "ecustudio"
        base.mkdir(parents=True)
        (base / "current.json").write_text('{"version":"../../escape","sha256":"x"}')
        self.assertIsNone(apps.current("ecustudio", self.install_root))

    def test_old_shortcut_handoff_is_offline_and_uses_latest(self):
        exe = self.install(self.package("2.0.0"))
        with patch("applications.sys.frozen", True, create=True), patch("applications.launch") as launch:
            self.assertTrue(apps.handoff("ecustudio", "1.0.0", root=self.install_root))
            launch.assert_called_once_with(exe, ())
        with patch("applications.sys.frozen", True, create=True), patch("applications.launch") as launch:
            self.assertFalse(apps.handoff("ecustudio", "3.0.0", root=self.install_root))
            launch.assert_not_called()


if __name__ == "__main__":
    unittest.main()

