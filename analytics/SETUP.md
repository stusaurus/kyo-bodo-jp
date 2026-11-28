# きょうボド｜有料コネクタを使わない公式GA4・GSC計測

対象：**stusaurus/kyo-bodo-jp のみ**。他サイトのGA4 IDやSearch Consoleの実績を混ぜない。

## 現在の状態

- 公式GA4 property **556462193**（Measurement IDではなくプロパティID）
- Search Console URL-prefix property **https://stusaurus.github.io/kyo-bodo-jp/**
- note第2記事 https://note.com/kyo_bodo_jp/n/n168b6eda559b
- 許可済みキャンペーン **gift_guide_20261119**、UTM source / medium **note / referral**
- このPRは **APIの読み取り処理を安全に用意するだけ**。接続・認証、取得成功、noteからの訪問件数、楽天確定成果は証明していない。
- Wix・Windsor.ai・Supermetrics等の有料サービスは不要。既存の無料APIとGitHub Actionsの利用枠内で実行する（利用枠・Google Cloudの請求設定は管理者が事前に確認）。

## 1回だけ必要な認証設定（鍵ファイル禁止）

この操作はGoogle Cloud／GA4／Search Consoleの管理者権限が必要。このリポジトリに認証できる設定が存在するかを外部からは判定できないため、**設定済みと断定しない**。

1. 既存のGoogle Cloud環境を使い、**Google Analytics Data API** と **Google Search Console API** の読み取りを許可する。新たな有料プランを契約しない。
2. GitHub Actionsから短命トークンを得る **Workload Identity Federation（OIDC）** を許可する。GitHub subject / attribute.repositoryを **stusaurus/kyo-bodo-jp** に限定する。日用品など別リポジトリへの信頼設定があっても、きょうボドの権限とみなさない。長期サービスアカウント鍵のJSONを発行・共有しない。
3. 対象のGoogleサービスアカウントに、きょうボドGA4 property **556462193** の **閲覧者**（read-only）権限を付ける。**GA4画面で権限を確認**し、他サイトのプロパティ権限を流用しない。
4. 同じサービスアカウントをSearch Consoleの上記 **正確なURL-prefixプロパティ** のユーザーとして追加する（読み取りが可能な権限）。親の github.io プロパティだけでは、本レポートは権限不足として停止する。
5. **きょうボドのGitHubリポジトリだけ**で Settings → Secrets and variables → Actions → Variables を開き、次の２つを追加する。
   - \`KYO_GCP_WIF_PROVIDER\`: \`projects/＜Google Cloud project number＞/locations/global/workloadIdentityPools/＜pool＞/providers/＜provider＞\`
   - \`KYO_GCP_SERVICE_ACCOUNT\`: \`＜read-only-account＞@＜project＞.iam.gserviceaccount.com\`
   どちらも公開設定用の識別子であり、個人のパスワードやサービスアカウント鍵ではない。
6. Actions → **Kyo Bodo official GA4 and GSC read-only report (no paid connector)** → Run workflow → main から実行し、SummaryとArtifactを確認する。2026-11-24の公式API実行成功（Actions run 45384517625）を受け、毎日10:37 JST（01:37 UTC）に既存の読み取り専用レポートを定期実行する。実行時刻はGitHub Actionsの混雑等で遅れる場合がある。手動実行は引き続きmainから可能。PR・main以外では認証付きAPIジョブを実行しない。定期実行の初回成功はActionsの実績で別途確認する。

**認証変数が未設定の場合**も手動起動できるが、\`NOT_CONFIGURED\` を出力するだけでAPIには接続しない。変数があってもGoogle側の権限・OIDC許可がない場合は認証エラーになるため、実測成功と誤認しない。

## レポートの判定

- GA4：\`2026-11-20\`に公開したnote第2記事について、**2日以上前の完了済み日**から、\`note_campaign_landing\`, \`game_detail_click\`, \`affiliate_click\`, \`rakuten_search_click\` を集計。Googleの標準sessionManualCampaignName・sessionManualSourceMediumを使い、可能なら \`customEvent:operator_test\` で運営者テストを分離する。
- \`customEvent:operator_test\` が未登録なら **運営者以外の件数は不明**。運営者以外と仮分類できても「真の顧客」「購入確定」ではない。GA4イベント数とセッション数・ユーザー数・楽天確定報酬を混同しない。
- GSC：米国太平洋時間基準の確定遅延を見込み、3日前までの28日を読む。サイト全体とトップ・2人用・カップル・小学生・ギフトページのGoogle自然検索クリック/表示を区別する。**note経由クリックは含まれない**。行がないページは\`null\`、0とみなさない。
- Google APIのメタデータでしきい値処理・結果の切り捨てが示されると\`QUALITY_RESTRICTED\`。権限がなければ\`NOT_AUTHORIZED\`などの状態だけを出す。
- 出力は\`audit-results/free-google/report.json\` と\`report.md\`の**集計結果だけ**。GitHub artifactは14日保存。個人ID、メールアドレス、検索文字列、認証情報、サービスアカウント鍵は保存しない。
- **どちらのAPIも読み取り専用**。サイト更新、商品変更、Google Search ConsoleへのURL登録申請、GA4送信、楽天API発注、GitHub issue自動書込みを実行しない。

### 本番データが取得できないときの無料代替

Google管理画面からGA4レポートとGSC「検索パフォーマンス」の必要な期間を**CSVで書き出してこのチャットに添付**すれば、追加の有料サービスやAPI認証設定なしで分析できる。選択するGA4プロパティは556462193で、GSCプロパティは上記きょうボドのURL-prefixのみ。他サイトを選ばない。

### 根拠

- Google Analytics Data API の標準ディメンション： https://developers.google.com/analytics/devguides/reporting/data/v1/api-schema
- Search Console Search Analytics API： https://developers.google.com/webmaster-tools/v1/searchanalytics/query
- GitHub → Google Cloudの鍵不要OIDC認証： https://github.com/google-github-actions/auth
