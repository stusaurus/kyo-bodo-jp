# きょうボド — 今日なにやる？

「人数・気分・時間から、今日遊ぶボードゲームを決める」診断型アフィリエイトサイトのMVPです。

## いま入っているもの

- 50ゲームの構造化データ (`data/catalog.py`)
- 6問・1問ずつのボードゲーム診断
- 診断結果 BEST 5 と「1分で分かる遊び方」
- 14個のシーン別SEOランディングページ
- 50個のゲーム詳細ページ
- 曜日・季節を考慮する「今日のおすすめ3本」
- GA4イベント計測
- `?test=1` / `?test=0` で運営者テストを識別
- 楽天商品検索APIからアフィリエイトURL・商品画像を毎日更新する処理
- sitemap.xml / robots.txt / canonical / ItemList構造化データ
- GitHub Pages自動デプロイ

## 推奨リポジトリ名

`stusaurus/kyo-bodo-jp`

ブランド名とURLが一致し、短く覚えやすいため、`boardgame-finder-jp` より優先します。

## GitHub側で最初に設定するもの

Repository > Settings > Secrets and variables > Actions

Secrets:
- `RAKUTEN_APPLICATION_ID`
- `RAKUTEN_ACCESS_KEY`
- `RAKUTEN_AFFILIATE_ID`

Variables:
- `GA_MEASUREMENT_ID` — ボドゲ版のGA4 WebデータストリームのMeasurement IDを推奨

Pages:
- Settings > Pages > Source を `GitHub Actions`

## ローカルビルド

```bash
python scripts/fetch_rakuten.py   # Secretsがなければ空キャッシュで終了
python scripts/build_site.py
python -m http.server 8000 -d site
```

ローカル確認時はリンクを `/` にするため以下が便利です。

```bash
SITE_BASE_PATH=/ SITE_ORIGIN=http://localhost:8000 python scripts/build_site.py
python -m http.server 8000 -d site
```

## ゲームを追加する

`data/catalog.py` に1件追加するだけです。次回ビルドで以下へ自動反映されます。

- 診断候補
- ゲーム一覧
- ゲーム詳細ページ
- シーン別ページ
- 今日のおすすめ候補
- sitemap

## GA4イベント

- `diagnosis_start`
- `diagnosis_answer`
- `diagnosis_complete`
- `game_result_view`
- `game_detail_click`
- `game_detail_view`
- `daily_recommendation_view`
- `scene_view`
- `affiliate_click`

重要パラメータは `game_id`, `rank`, `conversion_source`, `players`, `who`, `mood`, `desired_time`, `difficulty`, `balance`, `operator_test` です。

## 次の自動改善フェーズ

本MVPでは「編集スコア＋曜日・季節」でおすすめします。データが貯まったら、診断セグメント別に `game_result_view -> affiliate_click` のCTRを集計し、十分な表示数がある組み合わせだけ重みを微調整します。CTRだけで全面的に並び替えると自己強化ループになるため、編集スコアを主、実績CTRを従にしてください。
