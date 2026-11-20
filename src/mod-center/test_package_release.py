import unittest
from package_release import repair_text


class CatalogueTextTests(unittest.TestCase):
    def test_repairs_accents_without_changing_download_identity(self):
        data = {"name": "FumÃ©e diesel volumÃ©trique", "notes": "3â€“9 cm, 1150 Â°C",
                "url": "https://github.com/example/releases/download/v1/mod.zip", "sha256": "a" * 64,
                "size": 1234, "version": "0.44.2"}
        repaired = repair_text(data)
        self.assertEqual(repaired["name"], "Fumée diesel volumétrique")
        self.assertEqual(repaired["notes"], "3–9 cm, 1150 °C")
        for key in ("url", "sha256", "size", "version"):
            self.assertEqual(repaired[key], data[key])

    def test_correct_french_and_nested_entries_stay_intact(self):
        data = {"mods": [{"description": "Flammes d’échappement et détonations."}]}
        self.assertEqual(repair_text(data), data)
