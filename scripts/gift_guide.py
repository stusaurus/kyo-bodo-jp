"""Fact-first gift buying guide rendered from the existing verified catalog.

No popularity ranking, price forecast, personal play-test claim or offer cloning.
The guide links to the existing purchase-safe game detail pages.
"""
import json

GIFT_GROUPS = (
    {
        "age": 6,
        "title": "6歳からのプレゼント候補",
        "intro": "絵や形を見て遊ぶ短時間の作品と、全員で出口をふさぐ協力ゲーム。読める文字の量や大人のサポートも考えて選びます。",
        "ids": ("dobble", "nine-tiles", "bandido"),
    },
    {
        "age": 8,
        "title": "8歳からのプレゼント候補",
        "intro": "みんなで協力する作品と、地形タイルを考えて置く作品。最初は一緒にルールを確認できる人がいると選びやすくなります。",
        "ids": ("zombie-kidz", "kingdomino", "the-game"),
    },
    {
        "age": 10,
        "title": "10歳からのプレゼント候補",
        "intro": "配置をじっくり考える作品、2人専用の対戦作品、役割を分ける協力作品。遊ぶ人数が固定かどうかを特に確かめます。",
        "ids": ("harmonies", "splendor-duel", "the-crew-deep-sea"),
    },
)


def gift_groups(by_id, supports_players):
    """Fail before publication if a cited title's published facts change."""
    ids_seen = set()
    result = []
    for group in GIFT_GROUPS:
        games = []
        for gid in group["ids"]:
            if gid in ids_seen:
                raise ValueError("Repeated gift choice " + gid)
            ids_seen.add(gid)
            game = by_id[gid]
            if game["age"] > group["age"] or not supports_players(game, 2):
                raise ValueError("Ineligible gift choice " + gid)
            if game["play_time_min"] > game["play_time_max"]:
                raise ValueError("Invalid game duration for " + gid)
            games.append(game)
        result.append((group, tuple(games)))
    if len(ids_seen) != 9:
        raise ValueError("Gift guide must have nine distinct published games")
    return tuple(result)


def render_gift_guide(by_id, supports_players, card, shell, e, u, canon, player_label, format_play_time):
    selections = gift_groups(by_id, supports_players)
    sections = []
    for group, games in selections:
        age = group["age"]
        game_cards = "".join(card(g, "gift_guide") for g in games)
        # All nine entries are ordinary internal game-detail/purchase paths.
        # Include a compact factual table so gifts can be compared before clicking.
        table_rows = "".join(
            "<tr><th scope=\"row\"><a data-gift-detail=\"" + e(g["game_id"]) +
            "\" href=\"" + u("games/" + g["game_id"] + "/") + "\" data-track=\"game_detail_click\" data-game-id=\"" + e(g["game_id"]) + "\" data-source=\"gift_guide\">" + e(g["title"]) +
            "</a></th><td>" + e(player_label(g)) +
            "</td><td>" + format_play_time(g) +
            "</td><td>" + str(g["age"]) + "歳〜</td><td>" +
            e(g["how_to_play"][1]) + "</td></tr>"
            for g in games
        )
        sections.append(
            f'<section class="section gift-age" id="age-{age}" aria-labelledby="gift-age-{age}">'
            f'<div class="eyebrow">FROM AGE {age}</div>'
            f'<h2 id="gift-age-{age}">{e(group["title"])}</h2>'
            f'<p>{e(group["intro"])}</p>'
            f'<p class="small">{age}歳の人に贈る場合、以下はすべて掲載版の対象年齢下限が{age}歳以下の作品です。'
            '年齢だけでは遊びやすさを保証できません。</p>'
            '<div class="grid popular-grid gift-cards">' + game_cards + '</div>'
            '<p class="small gift-table-help">表は横にスクロールして、対象年齢・遊び方の一手まで確認できます。</p>'
            '<div class="scene-table-scroll gift-table-scroll" role="region" tabindex="0" '
            f'aria-label="{age}歳以上で検討する3作品の比較表。横にスクロールできます">'
            '<table class="scene-data-table gift-table"><caption>掲載データに基づく3作品の比較。人気順・価格順ではありません。</caption>'
            '<thead><tr><th scope="col">作品</th><th scope="col">人数</th><th scope="col">時間</th>'
            '<th scope="col">対象年齢</th><th scope="col">遊び方の一手</th></tr></thead><tbody>'
            + table_rows + '</tbody></table></div></section>'
        )
    navigation = "".join(
        f'<a href="#age-{group["age"]}">{group["age"]}歳からの候補を見る →</a>'
        for group, _ in selections
    )
    content = (
        '<section class="page-hero gift-hero">'
        f'<div class="breadcrumb"><a href="{u()}">ホーム</a> / '
        f'<a href="{u("scenes/children/")}">小学生と遊ぶ</a> / プレゼント選び</div>'
        '<div class="eyebrow">A GIFT TO PLAY TOGETHER</div>'
        '<h1>ボードゲームのプレゼントを年齢・人数で選ぶ</h1>'
        '<p>小学生へのクリスマスや誕生日の贈り物を探している方へ。'
        '「誰と遊ぶ？」「何分遊べる？」を先に確認し、贈ったあと実際に使える1本を探しましょう。</p>'
        '<p class="small">きょうボドの掲載作品から、対象年齢が6・8・10歳以下で、'
        '2人以上の遊び方が登録されている例を各3本紹介します。'
        '人気ランキング・実際に遊んだ体験談・売れ筋順位ではありません。</p>'
        '<nav class="gift-jumps" aria-label="対象年齢から贈り物を探す">'
        + navigation + '</nav></section>'
        '<section class="section gift-checklist" aria-labelledby="gift-checklist-title">'
        '<div class="eyebrow">BEFORE YOU GIFT</div>'
        '<h2 id="gift-checklist-title">プレゼントを買う前に、3つだけ確認</h2>'
        '<ol class="gift-checklist-grid">'
        '<li><strong>対象年齢</strong><span>箱に書かれた対象年齢と贈る子の年齢を確認。'
        '小学生でも低学年・高学年で適した内容は変わります。</span></li>'
        '<li><strong>遊ぶ人数</strong><span>2人専用、2〜4人、1人でも遊べる作品は違います。'
        '家族や友達など、遊ぶ機会がある人数を確認してください。</span></li>'
        '<li><strong>遊ぶ時間と販売版</strong><span>説明・準備も含めた時間の余裕を確認。'
        '購入先では商品名、版、対象年齢、価格、送料、到着日と在庫を確かめてください。</span></li>'
        '</ol></section>'
        + "".join(sections) +
        '<section class="section gift-after" aria-labelledby="gift-after-title">'
        '<div class="eyebrow">ONE MORE CHECK</div>'
        '<h2 id="gift-after-title">7歳・9歳・11歳なら、条件を細かく指定</h2>'
        '<p>上の9作品は比較例です。年齢が7歳・9歳・11歳などの場合や、'
        '一緒に遊ぶ人数が決まっている場合は、既存の小学生向け絞り込みで'
        '<strong>1歳刻みの年齢・2〜6人・時間</strong>から全掲載候補を見直せます。</p>'
        f'<p><a class="btn primary" href="{u("scenes/children/")}">小学生向けの年齢・人数で探す →</a></p>'
        '<h3>1人で遊ぶ機会が多い場合</h3>'
        '<p>1人用ルールのある作品を選び、実際に買う版でソロプレイの仕様を確認してください。</p>'
        f'<p><a class="text-link" href="{u("scenes/solo/")}">1人対応の作品を比較する →</a></p>'
        '<p class="small">掲載の人数・時間・対象年齢は登録している版の参考情報です。'
        '年齢・人数だけで好みや遊びやすさを保証しません。'
        '価格・送料・在庫・到着予定日や版は変動するため、販売店で最終確認してください。'
        '作品詳細からの購入先リンクにはアフィリエイト広告が含まれる場合があります。</p>'
        '</section>'
    )
    schema = json.dumps({
        "@context": "https://schema.org",
        "@type": "ItemList",
        "name": "年齢・人数で比べるボードゲームのプレゼント候補",
        "itemListElement": [
            {"@type": "ListItem", "position": i+1,
             "url": canon("games/" + g["game_id"] + "/"), "name": g["title"]}
            for i, g in enumerate(g for _, games in selections for g in games)
        ],
    }, ensure_ascii=False)
    return shell(
        "ボードゲームのプレゼント｜小学生・家族向けに年齢と人数で選ぶ",
        "クリスマス・誕生日のボードゲームプレゼントを6歳・8歳・10歳から比較。掲載作品の人数・遊び方・時間・対象年齢を見比べ、購入版・送料・在庫の確認点も紹介。",
        content, "guides/gift-board-games/",
        '<script type="application/ld+json">' + schema + '</script>'
    )
