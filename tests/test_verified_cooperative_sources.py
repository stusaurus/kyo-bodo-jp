"""Verified primary-source facts for high-intent cooperative game buying decisions."""
from html import unescape
from scripts import build_site as m

# Sources independently inspected on 2026-11-18. Original publisher or
# recognized official Japanese distributor; these do not claim live inventory.
FACTS = {
    "sky-team": (2, 2, 20, 20, 12, "https://suppe.sugorokuya.jp/items/220360"),
    "codenames-duet": (2, None, 15, 15, 11, "https://hobbyjapan.games/codename_duet/"),
    "bandido": (1, 4, 15, 15, 6, "https://suppe.sugorokuya.jp/items/190126"),
    "the-game": (1, 5, 15, 20, 8,
                 "https://arclightgames.jp/product/%E3%82%B6%E3%82%B2%E3%83%BC%E3%83%A0%E7%AC%AC2%E7%89%88/"),
    "ito-rainbow": (2, 14, 5, 15, 8, "https://arclightgames.jp/product/705rainbow/"),
    "ito": (2, 10, 30, 30, 8, "https://arclightgames.jp/product/ito/"),
    "zombie-kidz": (2, 4, 15, 15, 7, "https://suppe.sugorokuya.jp/items/190088"),
    "the-mind": (2, 4, 20, 20, 8, "https://suppe.sugorokuya.jp/items/180261"),
}


def test_individual_facts_are_backed_by_the_exact_edition_source():
    assert len(m.GAMES) == 83
    for gid, (pmin, pmax, tmin, tmax, age, url) in FACTS.items():
        g = m.BY_ID[gid]
        assert (g["players_min"], g["players_max"],
                g["play_time_min"], g["play_time_max"], g["age"]) == (
                    pmin, pmax, tmin, tmax, age), gid
        assert g["specs_source"] == url
        assert g["cooperative"]
        assert m.supports_players(g, 2)
    assert m.BY_ID["codenames-duet"]["players_open_ended"] is True


def test_each_new_source_is_visible_in_game_detail_with_safe_outgoing_link():
    for gid, (_, _, _, _, _, source) in FACTS.items():
        html = m.game_page(m.BY_ID[gid])
        assert "人数・所要時間・対象年齢の確認元" in html
        assert f'href="{source}"' in html
        assert 'target="_blank" rel="noopener noreferrer"' in html
        assert "PR：購入前に販売ページで" in html
    # Existing three certified sources remain intact.
    for gid in ("nana-card-game", "lama", "ark-nova"):
        assert m.BY_ID[gid].get("specs_source", "").startswith("https://")
    assert sum(bool(g.get("specs_source")) for g in m.GAMES) >= 11


def test_two_person_cooperative_comparison_shows_sources_without_inventing_others():
    html = m.two_player_cooperative_guide()
    eligible = [g for g in m.GAMES if m.supports_players(g, 2) and g["cooperative"]]
    assert len(eligible) == 15
    assert "情報の確認元" in html
    assert "未確認の作品について根拠を推測で補っていません" in html
    for g in eligible:
        if g.get("specs_source"):
            source = g["specs_source"]
            assert f'href="{source}"' in html
            assert f'aria-label="{g["title"]}の人数・時間・年齢の確認元"' in html
        else:
            assert f'<tr data-cooperative-game="{g["game_id"]}">' in html
    assert html.count("取扱元・メーカー</a>") == sum(
        bool(g.get("specs_source")) for g in eligible)
    assert html.count("詳細ページで版をご確認ください</span>") == sum(
        not bool(g.get("specs_source")) for g in eligible)


def test_no_recategorization_or_time_bucket_change_for_two_player_coops():
    eligible = [g for g in m.GAMES if m.supports_players(g, 2) and g["cooperative"]]
    assert [sum(predicate(g) for g in eligible) for predicate in [
        lambda g:g["play_time_max"]<=20,
        lambda g:20<g["play_time_max"]<=30,
        lambda g:g["play_time_max"]>30
    ]] == [7, 6, 2]
