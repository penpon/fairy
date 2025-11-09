# Requirements Document

## Introduction

Rapras（https://www.rapras.jp/）とYahoo Auctions（https://auctions.yahoo.co.jp/）から、二次創作を扱うセラー（出品者）を特定する機能です。Rapras集計ページからセラーリンクを取得し、Yahoo Auctionsのセラーページで商品タイトルをアニメ判定することで、二次創作セラーを識別します。結果はCSV形式でエクスポートされます。

## Alignment with Product Vision

本機能は、product.mdで定義されている以下の機能を実現します：

- **セラーデータ収集・分析・CSVエクスポート**
- **アニメタイトルフィルタリング**

これにより、以下の価値を提供します：

- **セラー特定**: 二次創作を扱うセラーの自動識別
- **効率化**: アニメ判定による早期スキップでスクレイピング時間を短縮
- **データ活用**: CSV形式でのエクスポートによる外部ツールでの活用

## Requirements

### Requirement 1: Rapras集計ページからのセラーリンク取得

**User Story:** ヤフーオークション出品者として、Rapras集計ページから落札価格合計10万円以上のセラーリンクを取得したいので、対象期間を指定してセラー一覧を自動収集できるようにしたい

#### Acceptance Criteria

1. WHEN システムがRaprasにログイン THEN システムは集計ページ（https://www.rapras.jp/sum_analyse?target=epsum&updown=down&genre=all&sdate=2025-08-01&edate=2025-10-31）にアクセスする
2. WHEN 集計ページを取得 THEN システムはセラー一覧テーブルから以下の情報をスクレイピングする：
   - セラー名
   - 落札価格合計
   - セラーリンク（Yahoo Auctionsへのリンク）
3. WHEN セラーリンクを取得 THEN システムは落札価格合計が10万円以上のセラーのみを対象とし、上から順番にセラーリンクを収集する
4. IF 落札価格合計が10万円未満 THEN システムは該当セラーをスキップする
5. WHEN データ収集が完了 THEN システムは収集したセラー数をログに記録する
6. IF スクレイピング中にエラーが発生 THEN システムはエラーログを記録し、部分的に収集したデータを保持する

### Requirement 2: Yahoo Auctionsセラーページからの商品名取得

**User Story:** ヤフーオークション出品者として、Raprasから取得したセラーリンク先（Yahoo Auctions）から商品名を取得したいので、セラーページにアクセスして商品一覧を自動収集できるようにしたい

#### Acceptance Criteria

1. WHEN システムがRaprasからセラーリンクを取得 THEN システムはYahoo Auctions（プロキシ経由）のセラーページにアクセスする
2. WHEN セラーページを取得 THEN システムは上から最大12件の商品をスクレイピング対象とする
3. WHEN 商品データを収集 THEN システムは以下の情報を取得する：
   - セラー名（例: "アート工房 クリスプ"）
   - セラーページURL（例: "https://auctions.yahoo.co.jp/sellinglist/56qo7eumP8EYVhY6kWg5poNgj3Wef?user_type=c&auc_seller_id=56qo7eumP8EYVhY6kWg5poNgj3Wef"）
   - 商品名（例: "らんまちゃん らんま A4 ポスター 同人 アニメ イラスト 美女 E017621"）
4. IF 商品が12件未満 THEN システムは取得可能な全商品を収集し、警告ログを記録する
5. IF Yahoo Auctionsへのアクセスが失敗 THEN システムは最大3回リトライし、全失敗時は例外を発生させる

### Requirement 3: 中間CSVエクスポート

**User Story:** ヤフーオークション出品者として、Gemini CLI制限に備えて収集途中のデータを保存したいので、商品名取得完了時点でCSV形式でエクスポートできるようにしたい

#### Acceptance Criteria

1. WHEN 全セラーの商品名取得が完了 THEN システムは中間CSVファイルをエクスポートする
2. WHEN CSV変換を実行 THEN システムは以下のカラムを含むCSVファイルを生成する：
   - セラー名
   - セラーページURL
   - 二次創作（初期値: "未判定"）
3. WHEN ファイル名を生成 THEN システムは`sellers_{YYYYMMDD_HHMMSS}.csv`形式で命名する
4. WHEN CSV出力先を指定 THEN システムはデフォルトで`output/`ディレクトリに保存する
5. WHEN CSVエクスポートが完了 THEN システムはファイルパスをログに出力し、次のアニメ判定処理に進む

### Requirement 4: アニメタイトル判定による二次創作セラー特定

**User Story:** ヤフーオークション出品者として、収集した商品名がアニメ作品かどうかを判定したいので、Gemini CLIを使用して自動判定し、二次創作セラーを特定できるようにしたい

#### Acceptance Criteria

1. WHEN 商品名が取得完了 THEN システムは商品名からスペース区切りで先頭2つの文字列を抽出してタイトルとする（例: "らんまちゃん らんま A4 ポスター 同人 アニメ イラスト 美女 E017621" → "らんまちゃん らんま"）
2. WHEN タイトルをアニメ判定 THEN システムは`gemini -m "gemini-2.5-flash" -p "このタイトルはアニメ作品ですか？（タイトル: {title}）"`コマンドを実行し、結果を取得する
3. IF Geminiが「はい」または「アニメ」を含む応答 THEN システムは該当セラーを「二次創作セラー」としてマークし、残りの商品判定をスキップする
4. IF Geminiが「いいえ」を含む応答 THEN システムは次の商品タイトルの判定を継続する
5. WHEN 12件全ての商品が「いいえ」判定 THEN システムは該当セラーを「非二次創作セラー」としてマークする
6. IF Gemini CLIがエラー THEN システムは該当商品を「判定不能」としてマークし、次の商品判定を継続する
7. WHEN 全セラーの判定が完了 THEN システムは中間CSVファイルの「二次創作」カラムを更新（"未判定" → "はい" or "いいえ"）し、最終CSVファイルとして保存する

### Requirement 5: 複数セラー並行処理

**User Story:** ヤフーオークション出品者として、複数セラーのデータを一度に収集したいので、セラーリストを並行処理できるようにしたい

#### Acceptance Criteria

1. WHEN 複数セラーを処理 THEN システムは各セラーを並行処理する（最大3並列）
2. WHEN 並行処理を実行 THEN システムは各セラーのデータ収集を独立したタスクとして実行する
3. IF 1つのセラー処理が失敗 THEN システムは他のセラー処理を継続し、失敗セラーをエラーログに記録する
4. WHEN 全セラー処理が完了 THEN システムは成功・失敗の集計結果をログに出力する
5. WHEN 処理時間が全体で5分を超過 THEN システムはタイムアウト警告をログに出力する

## Non-Functional Requirements

### Code Architecture and Modularity
- **Single Responsibility Principle**: データ収集（Scraper）、分析（Analyzer）、エクスポート（Exporter）を独立したモジュールとして分離
- **Modular Design**:
  - `modules/scraper/`: Rapras/Yahoo Auctionsスクレイピング機能
  - `modules/analyzer/`: アニメタイトル判定機能
  - `modules/storage/`: CSVエクスポート機能
- **Dependency Management**: Scraperは認証機能（rapras-yahoo-authentication）に依存
- **Clear Interfaces**: 各モジュールの公開メソッドを明確に定義

### Performance
- **Processing Speed**: 1セラーあたり30秒以下（product.md準拠）
- **Parallel Processing**: 複数セラー最大3並列
- **Early Termination**: アニメ判定成功時に残り商品をスキップすることで処理時間を短縮
- **Data Extraction Accuracy**: 100%（product.md Critical Success Criteria準拠）

### Reliability
- **Error Handling**: 全てのスクレイピング処理にtry-except処理を実装
- **Retry Strategy**: Yahoo Auctionsアクセス失敗時に最大3回リトライ
- **Partial Success**: 一部セラー失敗時も他のセラー処理を継続
- **Gemini API Error Handling**: API エラー時も処理を継続し、次の商品判定を実行

### Usability
- **Progress Feedback**: セラー処理進捗をログに出力
- **Error Messages**: ユーザーフレンドリーなエラーメッセージ（日本語）
- **Logging**: INFO/WARNING/ERRORレベルでのログ出力（modules/utils/logger.py使用）
- **CSV Compatibility**: Excel、Google Sheetsで開ける標準CSV形式

### Testability
- **Test Coverage**: 95%以上（tech.md準拠）
- **Unit Tests**: 各モジュールの正常系・異常系・境界値テスト
- **Integration Tests**: Rapras/Yahoo Auctions実環境テスト
- **Mock Support**: スクレイピング操作とGemini API呼び出しをモック可能な設計

### Scalability
- **Multiple Sellers**: 複数セラー並行処理（最大3並列）
- **Large Datasets**: 100セラー以上に対応
- **Memory Efficiency**: ストリーミング処理によるメモリ効率化
