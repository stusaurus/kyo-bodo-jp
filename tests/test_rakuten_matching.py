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
    assert m.match_item(g,item("Gamewright Sushi Go Party 寿司パーティー！ カードゲーム"))[0]
    assert m.match_item(g,item("寿司パーティー！ カードゲーム"))[0]
    assert m.match_item(g,item("スシゴーパーティ！ 日本語版 ボードゲーム"))[0]
    assert not m.match_item(g,item("スシゴー！ 日本語版 カードゲーム"))[0]
    assert not m.match_item(g,item("中古 ボードゲーム スシゴーパーティ！ 日本語版"))[0]
    assert not m.match_item(g,item("寿司パーティー！ バランスゲーム"))[0]

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
        if g["game_id"]=="patchwork":
            name="ホビージャパン パッチワーク 日本語版 ボードゲーム"
        if g["game_id"]=="the-game":
            name="ザ・ゲーム 第2版 完全日本語版 アークライト ボードゲーム"
        if g["game_id"]=="terraforming-mars":
            name="テラフォーミング・マーズ 完全日本語版 アークライト ボードゲーム"
        if g["game_id"]=="mandala":
            name="マンダラ MANDALA 日本語版 ボードゲーム"
        if g["game_id"]=="sagrada":
            name="サグラダ 日本語版 Engames ボードゲーム"
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

def test_second_audit_false_positives_are_rejected():
    cases=[
        ("patchwork","ホビー 模型車 バイク レーシングカー パッチワークボードゲーム reflection game"),
        ("nine-tiles","ナインタイル ミッキーアンドフレンズ オインクゲームズ ボードゲーム"),
    ]
    for game_id,name in cases:
        ok,reason,_=m.match_item(game(game_id),item(name))
        assert not ok,(game_id,name,reason)

def test_patchwork_branded_base_edition_is_allowed():
    ok,reason,_=m.match_item(
        game("patchwork"),
        item("ホビージャパン パッチワーク：10周年記念バージョン 日本語版 ボードゲーム")
    )
    assert ok,reason


def test_take_it_easy_exact_japanese_listing_without_generic_context():
    g=game("take-it-easy")
    assert m.match_item(g,item("テイクイットイージー 日本語版"))[0]
    assert not m.match_item(g,item("Take It Easy ステッカー"))[0]
    assert not m.match_item(g,item("木村拓哉 Checkpoint Take It Easy CD"))[0]

def test_sushi_go_party_requires_gamewright_for_generic_japanese_alias():
    g=game("sushi-go-party")
    assert m.match_item(g,item("Gamewright Sushi Go Party 寿司パーティー カードゲーム"))[0]
    assert not m.match_item(g,item("回転寿司 寿司パーティー おもちゃ"))[0]


def test_patchwork_2025_exact_japanese_title_without_publisher_is_allowed():
    ok,reason,_=m.match_item(
        game("patchwork"),
        item("パッチワーク 2025年新版 日本語版")
    )
    assert ok,reason

def test_exact_jan_queries_are_present_for_hard_to_find_games():
    assert "4573591300034" in m.query_variants(game("take-it-easy"))
    assert "3558380134831" in m.query_variants(game("patchwork"))


def test_more_standalone_sibling_games_are_rejected():
    for gid,name in [("the-mind","ザ・マインド エクストリーム 日本語版"),("splendor","宝石の煌き デュエル 日本語版"),("pandemic","パンデミック レガシー 日本語版 ホビージャパン"),("azul","アズール ミニ 日本語版 ボードゲーム")]:
        assert not m.match_item(game(gid),item(name))[0]


def test_observed_80_game_false_positives_are_rejected():
    cases=[
        ("heat","ヒート：ヘヴィレイン 日本語版 ボードゲーム"),
        ("mandala","ぬりえブック MANDALA1 マンダラお絵かき"),
        ("the-game","EXIT 脱出：ザ・ゲーム ファラオの玄室 日本語版"),
        ("forbidden-island","パラサイト 禁断の島 クリスティン・フロセス"),
        ("ice-cool","アイスクールリング ネッククーラー 冷感グッズ"),
        ("qwirkle","MindWare クワークル ラミー Qwirkle Rummy 戦略型カードゲーム"),
        ("quiz-iisen","クイズいいセン行きまSHOW! 恋愛編 アークライト ボードゲーム"),
        ("cascadia","カスカディア・ジュニア 日本語版 ボードゲーム"),
        ("terraforming-mars","テラフォーミング・マーズ ダイスゲーム 日本語版 ボードゲーム"),
        ("sagrada","サグラダ ライフ 日本語版 ボードゲーム"),
    ]
    for game_id,name in cases:
        ok,reason,_=m.match_item(game(game_id),item(name))
        assert not ok,(game_id,name,reason)


def test_new_base_game_examples_are_accepted():
    cases=[
        ("heat","ヒート 日本語版 ボードゲーム ホビージャパン"),
        ("mandala","マンダラ MANDALA 日本語版 ボードゲーム"),
        ("the-game","ザ・ゲーム 第2版 完全日本語版 アークライト ボードゲーム"),
        ("forbidden-island","禁断の島 完全日本語版 アークライト ボードゲーム"),
        ("ice-cool","アイスクール 日本語版 ホビージャパン ボードゲーム"),
        ("qwirkle","クワークル 日本語版 タイル ボードゲーム"),
        ("quiz-iisen","クイズいいセン行きまSHOW! アークライト ボードゲーム"),
        ("cascadia","カスカディア 日本語版 ケンビル ボードゲーム"),
        ("terraforming-mars","テラフォーミング・マーズ 完全日本語版 アークライト ボードゲーム"),
        ("sagrada","サグラダ 日本語版 Engames ボードゲーム"),
    ]
    for game_id,name in cases:
        ok,reason,_=m.match_item(game(game_id),item(name))
        assert ok,(game_id,name,reason)


def test_third_audit_variant_false_positives_are_rejected():
    cases=[
        ("mandala","タロットクロス カードゲーム ボードゲーム用シート 抽象的なマンダラ"),
        ("qwirkle","マインドウェア クワークル デラックス版 Qwirkle Deluxe Edition"),
        ("cascadia","カスカディア・ローリング：波立つ川 日本語版 ボードゲーム"),
        ("sagrada","Floodgate Games サグラダ ボードゲーム ファミリーゲーム"),
    ]
    for game_id,name in cases:
        ok,reason,_=m.match_item(game(game_id),item(name))
        assert not ok,(game_id,name,reason)
