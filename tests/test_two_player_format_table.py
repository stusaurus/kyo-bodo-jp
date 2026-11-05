"""Regression: two-player table distinguishes player-count formats without inferred quality."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.build_site import SCENES, GAMES, scene_comparison_table, supports_players


class TwoPlayerFormatTableTests(unittest.TestCase):
    def test_two_player_column_and_factual_labels(self):
        scene = next(s for s in SCENES if s["scene_id"] == "two-player")
        eligible = [g for g in GAMES if supports_players(g, 2)]
        result = scene_comparison_table(scene, eligible[:12])
        self.assertIn("2人専用／複数人数対応", result)
        for game in eligible[:12]:
            label = ("2人専用の人数表記" if game["players_min"] == game["players_max"] == 2
                     else "2人を含む複数人数対応")
            self.assertIn(label, result)
        self.assertNotIn("2人で最も面白い", result)

    def test_short_scene_keeps_original_columns(self):
        scene = next(s for s in SCENES if s["scene_id"] == "short")
        result = scene_comparison_table(scene, [])
        self.assertNotIn("2人専用／複数人数対応", result)
        self.assertNotIn("2人専用の人数表記", result)


if __name__ == "__main__":
    unittest.main()
