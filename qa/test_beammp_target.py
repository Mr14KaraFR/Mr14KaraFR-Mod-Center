"""BeamMP installations use temporary fake servers, never the real VPS or game."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile
import core


class BeamMPDestination(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.client = self.root / "BeamMP VANILLA BRAND/Resources/Client"
        self.client.mkdir(parents=True)
        self.archive = self.root / "download.zip"
        self.write_mod(self.archive, "2.0.0")
        self.mod = dict(id="example", name="Test", filename="example.zip", version="2.0.0",
                        url=self.archive.as_uri(), size=self.archive.stat().st_size,
                        sha256=core.sha256(self.archive))
        self.processes = patch("core.beammp_server_running", return_value=False)
        self.processes.start()
        self.addCleanup(self.processes.stop)

    def write_mod(self, path, version):
        with zipfile.ZipFile(path, "w") as archive:
            archive.writestr("mod_info/example/info.json", json.dumps({"version": version}))

    def install(self):
        return core.install(self.client, self.mod, local=True)

    def test_installs_in_client_without_renaming_or_extracting(self):
        self.install()
        self.assertTrue(self.client.is_dir())
        self.assertEqual(core.status(self.client, self.mod)[0], "À jour")
        self.assertEqual(core.sha256(self.client / "example.zip"), self.mod["sha256"])
        self.assertFalse((self.client / "mods").exists())
        self.assertFalse((self.client / "mod_info").exists())

    def test_update_backup_is_outside_distributed_client_and_server_plugins_untouched(self):
        old = self.client / "legacy.zip"
        self.write_mod(old, "1.0.0")
        original = old.read_bytes()
        plugin = self.client.parent / "Server/plugin/main.lua"
        plugin.parent.mkdir(parents=True)
        plugin.write_text("return {}", encoding="utf-8")
        backup = self.install()
        self.assertEqual(backup.parent, self.client.parent / "Mr14KaraFR-backups")
        self.assertNotIn(self.client, backup.parents)
        self.assertEqual((backup / "0-legacy.zip").read_bytes(), original)
        self.assertFalse(old.exists())
        self.assertEqual(plugin.read_text(encoding="utf-8"), "return {}")

    def test_only_real_resources_client_or_mods_are_accepted(self):
        for relative in ("Client", "Other/Client", "Resources/Server", "Resources", "Downloads"):
            folder = self.root / relative
            folder.mkdir(parents=True, exist_ok=True)
            with self.subTest(path=relative), self.assertRaisesRegex(ValueError, "Resources/Client"):
                core.install(folder, self.mod, local=True)
            self.assertFalse((folder / "example.zip").exists())
        self.assertEqual(core.target_kind(self.client), "beammp")
        game = self.root / "game/mods"
        game.mkdir(parents=True)
        self.assertEqual(core.validate_target(game), game.resolve())

    def test_client_repo_is_not_scanned_or_cleaned_as_server_content(self):
        hidden = self.client / "repo"
        hidden.mkdir()
        old = hidden / "legacy.zip"
        self.write_mod(old, "1.0.0")
        before = old.read_bytes()
        self.assertEqual(core.installed(self.client, self.mod), [])
        self.install()
        self.assertEqual(old.read_bytes(), before)

    def test_running_server_blocks_before_download(self):
        with patch("core.beammp_server_running", return_value=True), patch("core.open_source") as download:
            with self.assertRaisesRegex(RuntimeError, "Arrête le serveur BeamMP"):
                self.install()
            download.assert_not_called()
        self.assertFalse((self.client / "example.zip").exists())

    def test_server_start_during_download_preserves_old_zip(self):
        old = self.client / "example.zip"
        self.write_mod(old, "1.0.0")
        before = old.read_bytes()
        with patch("core.beammp_server_running", side_effect=[False, True]):
            with self.assertRaisesRegex(RuntimeError, "Arrête le serveur BeamMP"):
                self.install()
        self.assertEqual(old.read_bytes(), before)
        self.assertFalse(list(self.client.glob("*.download")))

    def test_running_local_game_does_not_block_a_stopped_server_target(self):
        with patch("core.game_running", return_value=True):
            self.install()
        self.assertTrue((self.client / "example.zip").is_file())

    def test_server_detector_does_not_mistake_launcher_for_server(self):
        self.processes.stop()
        with patch("core.windows_processes", return_value=["beammp-launcher.exe", "beamng.drive.x64.exe"]):
            self.assertFalse(core.beammp_server_running())
        with patch("core.windows_processes", return_value=["beammp-server-windows.exe"]):
            self.assertTrue(core.beammp_server_running())


if __name__ == "__main__":
    unittest.main()
