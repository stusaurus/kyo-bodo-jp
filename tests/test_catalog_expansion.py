"""Regression tests for source-backed additions to the board-game catalog."""
import unittest

from data.catalog import GAMES, supports_players
from scripts.fetch_rakuten import match_item


class CatalogExpansionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.by_id = {game["game_id"]: game for game in GAMES}

    def test_new_games_are_unique_and_sourced(self):
        self.assertEqual(len(GAMES), 88)
        self.assertEqual(len(self.by_id), len(GAMES))
        specs = {
            "nana-card-game": (2, 5, 15, 15, 6),
            "lama": (2, 6, 20, 20, 8),
            "ark-nova": (1, 4, 90, 150, 14),
        }
        for gid, values in specs.items():
            with self.subTest(game=gid):
                game = self.by_id[gid]
                actual = tuple(game[k] for k in (
                    "players_min", "players_max",
                    "play_time_min", "play_time_max", "age"))
                self.assertEqual(actual, values)
                self.assertTrue(game["specs_source"].startswith("https://"))
                self.assertEqual(len(game["how_to_play"]), 3)
                self.assertTrue(game["rakuten_query"])
                self.assertFalse(game["cooperative"])

    def test_new_games_obey_player_constraints(self):
        self.assertTrue(supports_players(self.by_id["ark-nova"], 1))
        self.assertFalse(supports_players(self.by_id["ark-nova"], 5))
        self.assertFalse(supports_players(self.by_id["nana-card-game"], 1))
        self.assertTrue(supports_players(self.by_id["nana-card-game"], 5))
        self.assertFalse(supports_players(self.by_id["lama"], 7))

    def test_verified_products_not_confused_with_sibling_editions(self):
        cases = [
            ("nana-card-game", "ナナカードゲーム Mob+ 日本語版", True),
            ("lama", "ラマ メビウスゲームズ カードゲーム", True),
            ("lama", "ラマダイス メビウスゲームズ カードゲーム", False),
            ("lama", "ラマパーティ AMIGO カードゲーム", False),
            ("lama", "ラマ・カダブラ カードゲーム", False),
            ("ark-nova", "アーク・ノヴァ 新たなる方舟 日本語版", True),
            ("ark-nova", "アーク・ノヴァ 新たなる方舟 追加マップパック2 日本語版", False),
            ("ark-nova", "アーク・ノヴァ マリンワールド 日本語版", False),
            ("ark-nova", "アーク・ノヴァ サンクチュアリ 日本語版", False),
        ]
        for gid, title, expected in cases:
            with self.subTest(game=gid, listing=title):
                matched, reason, score = match_item(self.by_id[gid], {"itemName": title})
                self.assertEqual(matched, expected, msg=(gid, title, reason, score))


if __name__ == "__main__":
    unittest.main()
