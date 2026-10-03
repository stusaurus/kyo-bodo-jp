import json
from pathlib import Path
from scripts import build_site as b
from scripts.fetch_rakuten import valid_url, match_item

def test_scene_hard_constraints():
    for scene in b.SCENES:
        for g in b.GAMES:
            if b.scene_score(g,scene)<50: continue
            sid=scene['scene_id']
            if sid=='couple': assert g['players_min']<=2<=g['players_max']
            if sid=='large-group': assert g['players_max']>=5
            if sid=='short': assert g['play_time_max']<=20
            if sid=='cooperative': assert g['cooperation']>=4
            if sid=='children': assert g['age']<=12

def test_rakuten_host_boundary():
    for url in ('https://evilrakuten.co.jp/x','https://rakuten.co.jp.evil.com/x','https://rakuten.evil.com/x'):
        assert not valid_url(url)

def test_every_retained_product_is_revalidated():
    for gid,hit in b.RAKUTEN.items():
        assert valid_url(hit['url']) and valid_url(hit['item_url'])
        assert match_item(b.BY_ID[gid],{'itemName':hit['item_name']})[0]

def test_404_is_noindex():
    b.main()
    assert '<meta name="robots" content="noindex">' in (b.SITE/'404.html').read_text()


def test_cooperation_is_a_shared_goal_mode_not_a_conversation_rating():
    expected={"ito","ito-rainbow","codenames-duet","just-one","the-mind","hanabi","pandemic","the-crew-deep-sea","dorfromantik"}
    assert {g["game_id"] for g in b.GAMES if g["cooperation"]>=4}==expected
    assert {g["game_id"] for g in b.GAMES if g["cooperative"]}==expected


def test_current_dixit_edition_supports_eight_players():
    assert b.BY_ID["dixit"]["players_max"]==8


def test_silent_cooperative_game_does_not_claim_discussion():
    game=b.BY_ID["the-mind"]
    assert "相談" not in b.fit_copy(game)
    assert "同じ目標" in b.fit_copy(game)
