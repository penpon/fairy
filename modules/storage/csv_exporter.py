"""CSV export functionality for seller data.

This module provides CSV export functionality following requirements 3 and 4
from .spec-workflow/specs/seller-data-collection-analysis/requirements.md.

Requirements:
- Requirement 3 (中間CSVエクスポート)
- Requirement 4 (アニメタイトル判定による二次創作セラー特定)
"""

import os
from datetime import datetime

import pandas as pd

from modules.utils.logger import get_logger

logger = get_logger(__name__)


class CSVExporter:
    """Export seller data to CSV format.

    This class handles both intermediate and final CSV exports with proper
    Japanese character encoding and timestamped filenames.

    Attributes:
        output_dir: CSV出力先ディレクトリ (デフォルト: "output/")
    """

    def __init__(self, output_dir: str = "output/") -> None:
        """Initialize CSVExporter.

        Args:
            output_dir: CSV出力先ディレクトリ (デフォルト: "output/")
        """
        self.output_dir = output_dir

    def _generate_filepath(self, suffix: str = "") -> str:
        """Generate timestamped filepath.

        Args:
            suffix: ファイル名のサフィックス（例: "_final"）

        Returns:
            str: タイムスタンプ付きファイルパス
        """
        os.makedirs(self.output_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"sellers_{timestamp}{suffix}.csv"
        return os.path.join(self.output_dir, filename)

    @staticmethod
    def _map_is_anime_seller(value: bool | None) -> str:
        """Map is_anime_seller boolean to Japanese text.

        Args:
            value: is_anime_seller boolean value

        Returns:
            str: "はい" (True), "いいえ" (False), "未判定" (None)
        """
        if value is True:
            return "はい"
        elif value is False:
            return "いいえ"
        else:
            return "未判定"

    def _save_csv(self, df: pd.DataFrame, filepath: str, log_message: str) -> str:
        """Save DataFrame to CSV file.

        Args:
            df: 保存するDataFrame
            filepath: 出力ファイルパス
            log_message: 成功時のログメッセージ

        Returns:
            str: 出力ファイルパス

        Raises:
            IOError: CSV書き込み失敗時
        """
        try:
            df.to_csv(filepath, index=False, encoding="utf-8-sig")
            logger.info(f"{log_message}: {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"CSV書き込み失敗: {filepath}, エラー: {e}")
            raise IOError(f"CSV書き込み失敗: {filepath}") from e

    def export_intermediate_csv(self, sellers: list[dict]) -> str:
        """Export intermediate CSV with "未判定" for is_anime_seller.

        商品名取得完了時点で中間CSVファイルをエクスポートします。
        二次創作カラムは全て"未判定"として出力されます。

        Args:
            sellers: セラー情報リスト
                例: [{"seller_name": str, "seller_url": str, "product_titles": list[str]}]

        Returns:
            str: 出力ファイルパス
                例: "output/sellers_20250101_120000.csv"

        Raises:
            IOError: CSV書き込み失敗時
        """
        filepath = self._generate_filepath()
        df = pd.DataFrame(
            {
                "セラー名": [s["seller_name"] for s in sellers],
                "セラーページURL": [s["seller_url"] for s in sellers],
                "二次創作": ["未判定" for _ in sellers],
            }
        )
        return self._save_csv(df, filepath, "中間CSVエクスポート完了")

    def export_final_csv(self, sellers: list[dict]) -> str:
        """Export final CSV with boolean to Japanese text mapping.

        アニメ判定完了後に最終CSVファイルをエクスポートします。
        is_anime_sellerをTrue→"はい", False→"いいえ", None→"未判定"に変換します。

        Args:
            sellers: 判定済みセラー情報リスト
                例: [{"seller_name": str, "seller_url": str, "is_anime_seller": bool | None}]

        Returns:
            str: 出力ファイルパス
                例: "output/sellers_20250101_120000_final.csv"

        Raises:
            IOError: CSV書き込み失敗時
        """
        filepath = self._generate_filepath(suffix="_final")
        df = pd.DataFrame(
            {
                "セラー名": [s["seller_name"] for s in sellers],
                "セラーページURL": [s["seller_url"] for s in sellers],
                "二次創作": [self._map_is_anime_seller(s.get("is_anime_seller")) for s in sellers],
            }
        )
        return self._save_csv(df, filepath, "最終CSVエクスポート完了")
