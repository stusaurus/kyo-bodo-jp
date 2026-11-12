"""Two-player quick filter uses actual catalog fields and leaves other scenes alone."""
import re
import unittest
from scripts.build_site import GAMES, SCENES, scene_page, supports_players, player_label, u, asset
from scripts.two_player_quick_filter import render_two_player_quick_filter


class TwoPlayerQuickFilterTests(unittest.TestCase):
    def setUp(self):
        self.scene = next(s for s in SCENES if s["scene_id"] == "two-player")
        self.games = [g for g in GAMES if supports_players(g, 2)]

    def test_only_two_player_catalog_candidates_enter_quick_filter(self):
        html = render_two_player_quick_filter(self.games, u, asset, player_label, supports_players)
        self.assertEqual(html.count(' data-two-game '), len(self.games))
        self.assertEqual(html.count('data-source="two_player_quick"'), len(self.games))
        self.assertEqual(html.count('data-time-max='), len(self.games))
        self.assertEqual(html.count('data-min-age='), len(self.games))
        self.assertEqual(html.count('data-cooperative='), len(self.games))
        self.assertIn('data-two-quick-count role="status" aria-live="polite"', html)
        self.assertIn('two-player-quick-filter.js', html)
        self.assertNotIn('人気順におすすめ', html)
        self.assertNotIn('楽天で購入', html)

    def test_default_three_include_one_genuine_two_only_example(self):
        page = render_two_player_quick_filter(self.games, u, asset, player_label, supports_players)
        first_three = re.findall(r'<li data-two-game[^>]*>.*?data-game-id="([^"]+)"', page, re.S)[:3]
        self.assertEqual(len(first_three), 3)
        self.assertEqual(first_three[0], 'quarto')
        self.assertTrue(any(g['game_id'] == first_three[0] and
                            g['players_min'] == g['players_max'] == 2 for g in self.games))
        self.assertIn('掲載人数が2人だけ', page)
        self.assertEqual(page.count(' data-two-game '), len(self.games))
        self.assertEqual(len(set(re.findall(r'data-game-id="([^"]+)"', page))), len(self.games))
        self.assertIn('人気・優劣・購入可能性の順位ではありません', page)

    def test_non_matching_game_never_enters_shortlist(self):
        game = dict(self.games[0], players_min=3, players_max=5)
        html = render_two_player_quick_filter([game], u, asset, player_label, supports_players)
        self.assertEqual(html, '')

    def test_visible_default_is_at_most_three_without_javascript(self):
        html = render_two_player_quick_filter(self.games[:8], u, asset, player_label, supports_players)
        self.assertEqual(len(re.findall(r'<li data-two-game[^>]*>', html)), min(8, len(self.games)))
        self.assertEqual(len(re.findall(r'<li data-two-game[^>]* hidden>', html)), max(0, min(8,len(self.games))-3))
        self.assertIn('遊べる時間', html)
        self.assertIn('協力するゲーム', html)
        self.assertIn('一番小さい人の年齢', html)
        # The catalog includes two-person games for children under 8.
        # Never force a six-year-old to select an older child or skip age validation.
        self.assertTrue(any(g["age"] <= 4 for g in self.games))
        self.assertTrue(any(g["age"] == 6 for g in self.games))
        for age in ("4", "6", "8", "10", "12"):
            self.assertIn(f'name="age" value="{age}"', html)
        self.assertLess(html.index('name="age" value="4"'), html.index('name="age" value="6"'))

    def test_real_two_player_page_only(self):
        html = scene_page(self.scene)
        self.assertIn('data-two-player-quick-filter', html)
        self.assertIn('two-player-quick-filter.js', html)
        self.assertIn('id="two-player-choices"', html)
        for scene in SCENES:
            if scene["scene_id"] == "two-player":
                continue
            self.assertNotIn('data-two-player-quick-filter', scene_page(scene))

    def test_two_player_page_quick_selector_uses_full_verified_catalog(self):
        page = scene_page(self.scene)
        section = re.search(r'<section class="two-player-quick".*?</section>', page, re.S)
        self.assertIsNotNone(section)
        quick = section.group(0)
        self.assertEqual(quick.count(' data-two-game '), len(self.games))
        self.assertIn('掲載カタログの2人対応' + str(len(self.games)) + '本', quick)
        self.assertIn('href="#two-player-format-title"', quick)
        self.assertIn('2人専用の候補を先に見る', quick)
        self.assertNotIn('全12本', quick)
        only_two = [g for g in self.games if g["players_min"] == g["players_max"] == 2]
        self.assertTrue(only_two)
        for game in only_two:
            self.assertIn('data-game-id="' + game["game_id"] + '"', quick)
        for game in GAMES:
            if not supports_players(game, 2):
                self.assertNotIn('data-game-id="' + game["game_id"] + '"', quick)
        self.assertLess(page.index('data-two-player-quick-filter'), page.index('data-two-player-format'))
        self.assertEqual(page.count('<h1>'), 1)

    def test_schema_and_eligibility_not_derived_from_rank(self):
        html = render_two_player_quick_filter(self.games[:3], u, asset, player_label, supports_players)
        for g in self.games[:3]:
            self.assertIn('data-time-max="' + str(int(g["play_time_max"])) + '"', html)
            self.assertIn('data-min-age="' + str(int(g["age"])) + '"', html)
            self.assertIn('data-game-id="' + g["game_id"] + '"', html)


if __name__ == "__main__":
    unittest.main()
