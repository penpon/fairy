# Product Overview

ヤフーオークション出品者のための市場分析プラットフォーム。Phase 1-2では、ラプラス・ヤフーオークションからセラー出品データを自動収集・分析し、売れ筋傾向把握と競合分析を支援します。Phase 3以降では、収集したデータを元にAI Agentを用いてチャット形式で任意のデータ出力を実施します（例：本日売り上げが一番高いセラー）。また、CRMシステムの構築を実施します。

## Key Capabilities（Phase 1-2）

- **ラプラス・ヤフーオークション認証自動化（SMS半自動対応）**
  - プログラムから電話番号ログインを実行
  - ユーザーが手元の携帯で受信したSMSコードを確認
  - PC上でコードを入力して認証完了
- **セラーデータ収集・分析・CSV エクスポート**
- **アニメタイトルフィルタリング**
  - `gemini -p "$ARGUMENTS"` コマンドでタイトルがアニメ作品かどうか判定
  - 判定結果に基づいてデータをフィルタリング

## Critical Success Criteria（Phase 1-2）

- **Data Extraction Accuracy**: 100%
- **Connection Success Rate**: 100%
- **Processing Speed**: 1セラーあたり 30秒以下

## Future Roadmap（Phase 3+）

AI Agentを用いた実装、CRM連携を計画中。詳細は実装時に決定。
