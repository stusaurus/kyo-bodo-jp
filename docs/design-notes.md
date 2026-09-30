# きょうボド：2026年9月 ビジュアル再設計

## アートディレクション

参考画像「きょうボド 今日なにやる？」と「ボードゲーム選びの楽しいひととき」を基準に、暖かな日差し、木のテーブル、植物、楽しそうな表情を大きく見せる。クリーム色・ネイビー・オレンジを共通の色とし、大人にも家族にも使いやすい、落ち着いたポップさに統一した。

トップはヒーロー → 6つのシーン → 今日のおすすめ → 診断の流れ → 厳選した定番3本。定番の残りと全14シーンは既存の一覧へつなぐ。絵文字、順位の王冠、重複するシーンチップ、小さなバッジ、カードの枠と影を減らした。

診断は1問ずつ、診断結果は第一候補を主役に、残る4本は補助候補として表示する。ゲーム詳細は紹介文・商品画像・1分ルールを先に見せ、評価軸は折りたたむ。楽天のサムネイルは同じ画像の320px表示を使用し、取得できなければ従来の128pxに戻す。それも取得できない場合は落ち着いたプレースホルダーを表示する。商品照合やデータ内のURLは変更しない。

## 画像資産と制作指示

生成には built-in image_gen を使用。参考画像はスタイル・空気感の参照として使用し、UIの文字はHTMLで描画した。画像はWebPに最適化してリポジトリに保存。

- `assets/hero-kyo-bodo.webp`：1536 × 1024、375,054 bytes
- `assets/scene-sprite.webp`：1536 × 1024、453,632 bytes

最終制作指示（プロンプトセット）：

```text
Use case: illustration-story
Asset type: Japanese board-game discovery website hero illustration
Primary request: Create an original, premium, warm editorial illustration inspired by the supplied reference images. Show four smiling family members enjoying a board game around a wooden table in a sunlit, comfortable room with green plants.
Style/medium: Refined Japanese illustration with gentle anime-inspired character drawing, natural expressions, rich but soft detail, and polished lighting. Friendly, slightly cute and playful, suitable for adults and families.
Color palette: Warm cream, natural wood, muted greens, navy and restrained orange accents.
Composition/framing: Large welcoming landscape artwork that makes the pleasure of playing together immediately clear. The artwork is used beside website copy; no lettering is embedded in the illustration.
Constraints: No text, UI, badges, logos, watermark, cheap stock-art appearance, childish caricatures, or excessive decorative symbols.
```

```text
Use case: illustration-story
Asset type: Six-scene navigation sprite for the same website
Primary request: Create six premium illustrations in the same warm, refined visual world as the supplied references and the hero: a couple playing together; a family playing; children with an adult; a group of friends; a short game with an hourglass; and cooperative play.
Composition/framing: Exactly three columns and two rows, six equally sized square tiles, with no labels, gutters, frames or UI. Each scene is readable as a separate square crop.
Style/medium: Polished Japanese editorial illustration, gentle expressions, soft sunlight, warm cream and wood, muted greenery, restrained navy and orange. Friendly and playful without looking childish.
Constraints: No text, logos, watermarks, emojis, badges or cheap clip-art styling. All six scenes must share the same illustration quality and palette.
```

## 維持したもの

- 50ゲームのカタログと全14シーン、診断の質問・選択肢・採点、日替わりおすすめの選定ロジック。
- 楽天の商品取得・照合・品質判定・安全な検索へのフォールバック。ゲームID、商品URL、広告属性。
- GA4のイベント名・パラメーター・`operator_test`。計測スクリプトは変更していない。
- 全68ページのURL、canonical、構造化データ、sitemap.xml、robots.txt、GitHub Pages。Google所有権確認ファイルも公開用ビルドに含めた。

## 確認

- pytest：35件成功。
- PC 1440px / iPhone幅393px：トップ、診断、診断結果、シーン一覧、家族シーン、ゲーム一覧、ito詳細、未解決商品の詳細を確認。横にはみ出さず、JavaScriptエラーなし。
- 診断の第一候補と2〜5位を旧採点ロジックと比較し一致。戻る操作、一覧フィルター、楽天クリックのゲームID・流入元・順位、GA4イベント、operator_testの有効化・解除を確認。
- 公開用ビルドの全68ページのcanonicalと内部リンク、既存のsitemap.xml・robots.txt・計測スクリプトの一致を確認。
- 改修前の最新楽天監査：50ゲーム中49件が安全な商品一致、take-it-easy 1件は検索へのフォールバック。重複商品コードなし。公開時にはActionsが再取得・再監査する。

CIは従来の検証・楽天監査・Pages公開を維持し、画像・CSS・JavaScriptの変更もビルド対象になるよう `assets/**` を追加した。
