"""Exercise real Tk geometry without displaying or controlling a window."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app import App


class CatalogLayoutTests(unittest.TestCase):
    def test_cards_keep_actions_visible_and_scroll_at_both_widths(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(App, "after"):
            app = App(config_path=Path(folder) / "settings.json")
            app.withdraw()
            try:
                view = app.catalog_view
                view.pack_forget()
                view.place(x=0, y=0, width=1000, height=300)
                app.clear_cards()
                for index in range(5):
                    app.card(index, "Suspension pneumatique", "Description détaillée du mod et de ses réglages. " * 4,
                             "AIR", "0.44.2", "0.44.1", "Mise à jour disponible",
                             {"notes": "Les nouveautés du mod."})
                for width, columns in ((1000, 2), (700, 1), (1000, 2)):
                    view.place_configure(width=width)
                    app.update()
                    self.assertEqual(view.columns, columns)
                    for frame, button in zip(view.frames, app.cards):
                        self.assertGreaterEqual(frame.winfo_height(), 200)
                        bottom = button.winfo_rooty() + button.winfo_height()
                        self.assertLessEqual(bottom, frame.winfo_rooty() + frame.winfo_height())
                        self.assertGreaterEqual(button.winfo_width(), button.winfo_reqwidth())
                    view.scroll_to(1)
                    app.update()
                    self.assertAlmostEqual(view.canvas.yview()[1], 1, places=3)
                    last = view.frames[-1]
                    self.assertLessEqual(last.winfo_y() + last.winfo_height(),
                                         view.canvas.canvasy(view.canvas.winfo_height()))
                app.clear_cards()
                app.update()
                self.assertEqual(view.frames, [])
                self.assertEqual(view.content.winfo_children(), [])
            finally:
                app.destroy()


if __name__ == "__main__":
    unittest.main()
