"""Optional 2-player shortlist based only on published metadata, never rankings."""
from html import escape


def render_two_player_quick_filter(games, url, asset_url, player_label, supports_players):
    eligible = [g for g in games if supports_players(g, 2)]
    if not eligible:
        return ""
    rows = []
    for i, g in enumerate(eligible):
        time = int(g["play_time_max"])
        age = int(g["age"])
        if time <= 0 or age < 0:
            continue
        title = escape(str(g["title"]), quote=True)
        gid = escape(str(g["game_id"]), quote=True)
        label = escape(str(player_label(g)), quote=True)
        rows.append(
            f'<li data-two-game data-time-max="{time}" data-min-age="{age}"'
            f' data-cooperative="{1 if g["cooperative"] else 0}"'
            f'{" hidden" if i >= 3 else ""}>'
            f'<a data-track="game_detail_click" data-source="two_player_quick"'
            f' data-game-id="{gid}" href="{escape(url("games/" + g["game_id"] + "/"), quote=True)}">'
            f'<strong>{title}</strong><span>{label} · '
            f'{int(g["play_time_min"])}〜{time}分 · 対象{age}歳〜 · '
            f'{"協力" if g["cooperative"] else "非協力"}</span></a></li>'
        )
    if not rows:
        return ""
    choices = (
        ("minutes", "遊べる時間", (("0", "指定なし"), ("15", "15分以内"), ("30", "30分以内"))),
        ("style", "遊び方", (("any", "どちらでも"), ("cooperative", "協力するゲーム"))),
        ("age", "一番小さい人の年齢", (("0", "指定なし"), ("4", "4歳"), ("6", "6歳"), ("8", "8歳"), ("10", "10歳"), ("12", "12歳"))),
    )
    filters = []
    for name, legend, options in choices:
        opts = "".join(
            f'<label class="two-quick-option"><input type="radio" name="{name}"'
            f' value="{value}"{" checked" if i == 0 else ""}><span>{escape(label)}</span></label>'
            for i, (value, label) in enumerate(options)
        )
        filters.append(f'<fieldset><legend>{legend}</legend><div class="two-quick-options">{opts}</div></fieldset>')
    return (
        '<section class="two-player-quick" data-two-player-quick-filter'
        ' aria-labelledby="two-player-quick-title">'
        '<div class="eyebrow">CHOOSE IN THREE TAPS</div>'
        '<h2 id="two-player-quick-title">2人で遊ぶ、条件から3本を見つける</h2>'
        '<p>掲載カタログの2人対応' + str(len(rows)) + '本から、時間・遊び方・年齢で絞ります。'
        '確認できた対応人数・所要時間上限・対象年齢だけで判定。'
        '人気・優劣・購入可能性の順位ではありません。</p>'
        '<form aria-label="2人用ゲームの簡単な絞り込み">' + "".join(filters) + '</form>'
        '<p class="two-quick-count" data-two-quick-count role="status" aria-live="polite">'
        '条件を選ぶと候補が絞られます。下の一覧からも全候補を確認できます。</p>'
        '<p class="two-quick-empty" data-two-quick-empty hidden>'
        '条件を広げるか、掲載されている全候補をご覧ください。</p>'
        '<ul class="two-quick-results">' + "".join(rows) + '</ul>'
        '<p><a class="text-link" href="#two-player-format-title">2人専用の候補を先に見る →</a> ' +
        '<a class="text-link" href="#two-player-choices">遊び方の詳しい比較を見る →</a></p>'
        '</section>'
        '<script defer src="' + escape(asset_url("two-player-quick-filter.js"), quote=True) + '"></script>'
    )
