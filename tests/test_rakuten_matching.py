import importlib.util
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location("fetch_rakuten",ROOT/"scripts"/"fetch_rakuten.py")
m=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(m)

def game(game_id):
    return next(g for g in m.GAMES if g["game_id"]==game_id)

def item(name,url="https://item.rakuten.co.jp/shop/item/"):
    return {
        "itemName":name,
        "itemUrl":url,
        "affiliateUrl":url,
        "itemCode":"shop:item",
        "mediumImageUrls":[],
    }

def test_sushi_go_party_accepts_only_party_title():
    g=game("sushi-go-party")
    assert m.match_item(g,item("Gamewright Sushi Go Party! ボードゲーム"))[0]
    assert m.match_item(g,item("スシゴーパーティ！ 日本語版 ボードゲーム"))[0]
    assert not m.match_item(g,item("スシゴー！ 日本語版 カードゲーム"))[0]
    assert not m.match_item(g,item("中古 ボードゲーム スシゴーパーティ！ 日本語版"))[0]
    assert not m.match_item(g,item("寿司パーティー！ カードゲーム"))[0]

def test_expansions_and_accessories_are_rejected():
    g=game("catan")
    assert not m.match_item(g,item("カタン 拡張版 航海者"))[0]
    assert not m.match_item(g,item("カタン 専用カードスリーブ"))[0]
    assert not m.match_item(g,item("中古 カタン スタンダード版"))[0]

def test_sibling_games_do_not_cross_match():
    assert not m.match_item(game("ito"),item("ito レインボー アークライト ボードゲーム"))[0]
    assert not m.match_item(game("codenames"),item("コードネーム デュエット 日本語版 ボードゲーム"))[0]
    assert m.match_item(game("codenames-duet"),item("コードネーム デュエット 日本語版 ボードゲーム"))[0]

def test_generic_titles_need_game_context():
    assert not m.match_item(game("heat"),item("HEAT ヒート 保温グッズ"))[0]
    assert m.match_item(game("heat"),item("ヒート ペダル・トゥ・ザ・メタル 日本語版 ボードゲーム"))[0]
    assert not m.match_item(game("scout"),item("SCOUT バッグ"))[0]
    assert m.match_item(game("scout"),item("SCOUT オインクゲームズ カードゲーム"))[0]

def test_every_catalog_title_can_match_a_safe_synthetic_listing():
    for g in m.GAMES:
        name=g["title"]+" ボードゲーム"
        if g["game_id"]=="ito":
            name+=" アークライト"
        if g["game_id"]=="ito-rainbow":
            name+=" アークライト"
        if g["game_id"]=="scout":
            name+=" オインクゲームズ"
        if g["game_id"]=="hanabi":
            name="花火 HANABI ボードゲーム"
        if g["game_id"]=="neu":
            name="ノイ NEU カードゲーム"
        ok,reason,_=m.match_item(g,item(name))
        assert ok,(g["game_id"],name,reason)

def test_rakuten_url_validation():
    assert m.valid_url("https://item.rakuten.co.jp/shop/item/")
    assert m.valid_url("https://hb.afl.rakuten.co.jp/hgc/example")
    assert not m.valid_url("http://item.rakuten.co.jp/shop/item/")
    assert not m.valid_url("https://example.com/item")

def test_observed_wrong_matches_are_rejected():
    cases=[
        ("codenames","コードネーム XXL 日本語版 ボードゲーム"),
        ("quarto","ギガミック クアルト ミニ QUARTO MINI ボードゲーム"),
        ("patchwork","パッチワーク: ドゥードゥル 日本語版 ボードゲーム"),
        ("challengers","チャレンジャーズ！:ビーチカップ 日本語版 ボードゲーム"),
        ("nine-tiles","ナインタイル ポケモンドコダ！ オインクゲームズ ボードゲーム"),
        ("machi-koro","街コロ通 (ツー) ボードゲーム"),
        ("take-it-easy","テイク・イット・イージー【Blu-ray】"),
        ("cat-in-the-box","アドメイト キャットインザボックス じゃらしアタッチメント"),
    ]
    for game_id,name in cases:
        ok,reason,_=m.match_item(game(game_id),item(name))
        assert not ok,(game_id,name,reason)

def test_preferred_base_game_examples_are_accepted():
    cases=[
        ("codenames","コードネーム 2025年新版 日本語版 ボードゲーム"),
        ("quarto","ギガミック QUARTO クアルト ボードゲーム"),
        ("patchwork","パッチワーク 日本語版 ボードゲーム ホビージャパン"),
        ("challengers","チャレンジャーズ！ 日本語版 ボードゲーム"),
        ("nine-tiles","ナインタイル オインクゲームズ ボードゲーム"),
        ("machi-koro","街コロ ボードゲーム"),
        ("take-it-easy","テイク・イット・イージー ボードゲーム"),
        ("cat-in-the-box","キャット・イン・ザ・ボックス 日本語版 ボードゲーム"),
    ]
    for game_id,name in cases:
        ok,reason,_=m.match_item(game(game_id),item(name))
        assert ok,(game_id,name,reason)
