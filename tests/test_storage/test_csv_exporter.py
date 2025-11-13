"""Unit tests for CSVExporter.

This module tests the CSVExporter class following requirements 3 and 4
from .spec-workflow/specs/seller-data-collection-analysis/requirements.md.

Requirements:
- Requirement 3 (中間CSVエクスポート)
- Requirement 4 (アニメタイトル判定による二次創作セラー特定)
"""

import re
from pathlib import Path
from unittest.mock import patch

import pandas as pd
import pytest

from modules.storage.csv_exporter import CSVExporter


class TestCSVExporterInit:
    """Test CSVExporter initialization."""

    def test_init_default_output_dir(self):
        """Test initialization with default output directory.

        Given: No output_dir parameter
        When: CSVExporter is initialized
        Then: output_dir should be "output/"
        """
        # When
        exporter = CSVExporter()

        # Then
        assert exporter.output_dir == "output/"

    def test_init_custom_output_dir(self):
        """Test initialization with custom output directory.

        Given: Custom output_dir parameter
        When: CSVExporter is initialized
        Then: output_dir should be the custom value
        """
        # Given
        custom_dir = "custom_output/"

        # When
        exporter = CSVExporter(output_dir=custom_dir)

        # Then
        assert exporter.output_dir == custom_dir


class TestExportIntermediateCSV:
    """Test export_intermediate_csv method."""

    def test_export_intermediate_csv_success(self, tmp_path):
        """Test successful intermediate CSV export with "未判定".

        Given: Valid seller data without is_anime_seller
        When: export_intermediate_csv is called
        Then: CSV file is created with "未判定" in 二次創作 column
        """
        # Given
        exporter = CSVExporter(output_dir=str(tmp_path) + "/")
        sellers = [
            {
                "seller_name": "テストセラー1",
                "seller_url": "https://auctions.yahoo.co.jp/seller1",
                "product_titles": ["商品A", "商品B"],
            },
            {
                "seller_name": "テストセラー2",
                "seller_url": "https://auctions.yahoo.co.jp/seller2",
                "product_titles": ["商品C"],
            },
        ]

        # When
        filepath = exporter.export_intermediate_csv(sellers)

        # Then
        assert Path(filepath).exists()
        df = pd.read_csv(filepath, encoding="utf-8-sig")
        assert list(df.columns) == ["セラー名", "セラーページURL", "二次創作"]
        assert len(df) == 2
        assert df["セラー名"].tolist() == ["テストセラー1", "テストセラー2"]
        assert df["セラーページURL"].tolist() == [
            "https://auctions.yahoo.co.jp/seller1",
            "https://auctions.yahoo.co.jp/seller2",
        ]
        assert df["二次創作"].tolist() == ["未判定", "未判定"]

    def test_export_intermediate_csv_filename_format(self, tmp_path):
        """Test intermediate CSV filename format.

        Given: Valid seller data
        When: export_intermediate_csv is called
        Then: Filename should match sellers_{YYYYMMDD_HHMMSS}.csv
        """
        # Given
        exporter = CSVExporter(output_dir=str(tmp_path) + "/")
        sellers = [
            {
                "seller_name": "テストセラー",
                "seller_url": "https://auctions.yahoo.co.jp/seller",
                "product_titles": ["商品A"],
            }
        ]

        # When
        filepath = exporter.export_intermediate_csv(sellers)

        # Then
        filename = Path(filepath).name
        pattern = r"^sellers_\d{8}_\d{6}\.csv$"
        assert re.match(pattern, filename), f"Filename {filename} does not match pattern"

    def test_export_intermediate_csv_empty_list(self, tmp_path):
        """Test intermediate CSV export with empty seller list.

        Given: Empty seller list
        When: export_intermediate_csv is called
        Then: CSV file is created with only headers
        """
        # Given
        exporter = CSVExporter(output_dir=str(tmp_path) + "/")
        sellers = []

        # When
        filepath = exporter.export_intermediate_csv(sellers)

        # Then
        assert Path(filepath).exists()
        df = pd.read_csv(filepath, encoding="utf-8-sig")
        assert list(df.columns) == ["セラー名", "セラーページURL", "二次創作"]
        assert len(df) == 0

    def test_export_intermediate_csv_auto_create_directory(self, tmp_path):
        """Test automatic directory creation.

        Given: Non-existent output directory
        When: export_intermediate_csv is called
        Then: Directory should be automatically created
        """
        # Given
        output_dir = tmp_path / "new_output"
        exporter = CSVExporter(output_dir=str(output_dir) + "/")
        sellers = [
            {
                "seller_name": "テストセラー",
                "seller_url": "https://auctions.yahoo.co.jp/seller",
                "product_titles": ["商品A"],
            }
        ]

        # When
        filepath = exporter.export_intermediate_csv(sellers)

        # Then
        assert output_dir.exists()
        assert Path(filepath).exists()

    def test_export_intermediate_csv_utf8_with_bom(self, tmp_path):
        """Test UTF-8 with BOM encoding for Excel compatibility.

        Given: Seller data with Japanese characters
        When: export_intermediate_csv is called
        Then: File should be encoded as UTF-8 with BOM
        """
        # Given
        exporter = CSVExporter(output_dir=str(tmp_path) + "/")
        sellers = [
            {
                "seller_name": "日本語セラー名",
                "seller_url": "https://auctions.yahoo.co.jp/seller",
                "product_titles": ["商品"],
            }
        ]

        # When
        filepath = exporter.export_intermediate_csv(sellers)

        # Then
        with open(filepath, "rb") as f:
            content = f.read()
            # UTF-8 BOM is \xef\xbb\xbf
            assert content.startswith(b"\xef\xbb\xbf")


class TestExportFinalCSV:
    """Test export_final_csv method."""

    def test_export_final_csv_boolean_mapping(self, tmp_path):
        """Test final CSV export with boolean to Japanese text mapping.

        Given: Seller data with is_anime_seller boolean values
        When: export_final_csv is called
        Then: CSV should map True→"はい", False→"いいえ", None→"未判定"
        """
        # Given
        exporter = CSVExporter(output_dir=str(tmp_path) + "/")
        sellers = [
            {
                "seller_name": "アニメセラー",
                "seller_url": "https://auctions.yahoo.co.jp/anime",
                "is_anime_seller": True,
            },
            {
                "seller_name": "非アニメセラー",
                "seller_url": "https://auctions.yahoo.co.jp/not_anime",
                "is_anime_seller": False,
            },
            {
                "seller_name": "未判定セラー",
                "seller_url": "https://auctions.yahoo.co.jp/unknown",
                "is_anime_seller": None,
            },
        ]

        # When
        filepath = exporter.export_final_csv(sellers)

        # Then
        assert Path(filepath).exists()
        df = pd.read_csv(filepath, encoding="utf-8-sig")
        assert list(df.columns) == ["セラー名", "セラーページURL", "二次創作"]
        assert df["二次創作"].tolist() == ["はい", "いいえ", "未判定"]

    def test_export_final_csv_filename_format(self, tmp_path):
        """Test final CSV filename format.

        Given: Valid seller data
        When: export_final_csv is called
        Then: Filename should match sellers_{YYYYMMDD_HHMMSS}_final.csv
        """
        # Given
        exporter = CSVExporter(output_dir=str(tmp_path) + "/")
        sellers = [
            {
                "seller_name": "テストセラー",
                "seller_url": "https://auctions.yahoo.co.jp/seller",
                "is_anime_seller": True,
            }
        ]

        # When
        filepath = exporter.export_final_csv(sellers)

        # Then
        filename = Path(filepath).name
        pattern = r"^sellers_\d{8}_\d{6}_final\.csv$"
        assert re.match(pattern, filename), f"Filename {filename} does not match pattern"

    def test_export_final_csv_empty_list(self, tmp_path):
        """Test final CSV export with empty seller list.

        Given: Empty seller list
        When: export_final_csv is called
        Then: CSV file is created with only headers
        """
        # Given
        exporter = CSVExporter(output_dir=str(tmp_path) + "/")
        sellers = []

        # When
        filepath = exporter.export_final_csv(sellers)

        # Then
        assert Path(filepath).exists()
        df = pd.read_csv(filepath, encoding="utf-8-sig")
        assert list(df.columns) == ["セラー名", "セラーページURL", "二次創作"]
        assert len(df) == 0


class TestExportErrorHandling:
    """Test error handling scenarios."""

    @patch("modules.storage.csv_exporter.pd.DataFrame.to_csv")
    def test_export_intermediate_csv_io_error(self, mock_to_csv, tmp_path):
        """Test IOError handling on write failure.

        Given: DataFrame.to_csv raises IOError
        When: export_intermediate_csv is called
        Then: IOError should be raised
        """
        # Given
        exporter = CSVExporter(output_dir=str(tmp_path) + "/")
        sellers = [
            {
                "seller_name": "テストセラー",
                "seller_url": "https://auctions.yahoo.co.jp/seller",
                "product_titles": ["商品A"],
            }
        ]
        mock_to_csv.side_effect = OSError("Write permission denied")

        # When/Then
        with pytest.raises(IOError, match="CSV書き込み失敗:"):
            exporter.export_intermediate_csv(sellers)

    @patch("modules.storage.csv_exporter.pd.DataFrame.to_csv")
    def test_export_final_csv_io_error(self, mock_to_csv, tmp_path):
        """Test IOError handling on write failure for final CSV.

        Given: DataFrame.to_csv raises IOError
        When: export_final_csv is called
        Then: IOError should be raised
        """
        # Given
        exporter = CSVExporter(output_dir=str(tmp_path) + "/")
        sellers = [
            {
                "seller_name": "テストセラー",
                "seller_url": "https://auctions.yahoo.co.jp/seller",
                "is_anime_seller": True,
            }
        ]
        mock_to_csv.side_effect = OSError("Disk full")

        # When/Then
        with pytest.raises(IOError, match="CSV書き込み失敗:"):
            exporter.export_final_csv(sellers)

    def test_export_intermediate_csv_none_input(self, tmp_path):
        """Test ValueError when sellers is None.

        Given: sellers parameter is None
        When: export_intermediate_csv is called
        Then: ValueError should be raised
        """
        # Given
        exporter = CSVExporter(output_dir=str(tmp_path) + "/")

        # When/Then
        with pytest.raises(ValueError, match="sellers cannot be None"):
            exporter.export_intermediate_csv(None)

    def test_export_final_csv_none_input(self, tmp_path):
        """Test ValueError when sellers is None for final CSV.

        Given: sellers parameter is None
        When: export_final_csv is called
        Then: ValueError should be raised
        """
        # Given
        exporter = CSVExporter(output_dir=str(tmp_path) + "/")

        # When/Then
        with pytest.raises(ValueError, match="sellers cannot be None"):
            exporter.export_final_csv(None)

    def test_export_intermediate_csv_missing_seller_name(self, tmp_path):
        """Test ValueError when seller_name is missing.

        Given: Seller dict without seller_name key
        When: export_intermediate_csv is called
        Then: ValueError should be raised with key information
        """
        # Given
        exporter = CSVExporter(output_dir=str(tmp_path) + "/")
        sellers = [
            {
                "seller_url": "https://auctions.yahoo.co.jp/seller",
                "product_titles": ["商品A"],
            }
        ]

        # When/Then
        with pytest.raises(ValueError, match="missing required key 'seller_name'"):
            exporter.export_intermediate_csv(sellers)

    def test_export_intermediate_csv_missing_seller_url(self, tmp_path):
        """Test ValueError when seller_url is missing.

        Given: Seller dict without seller_url key
        When: export_intermediate_csv is called
        Then: ValueError should be raised with key information
        """
        # Given
        exporter = CSVExporter(output_dir=str(tmp_path) + "/")
        sellers = [
            {
                "seller_name": "テストセラー",
                "product_titles": ["商品A"],
            }
        ]

        # When/Then
        with pytest.raises(ValueError, match="missing required key 'seller_url'"):
            exporter.export_intermediate_csv(sellers)

    def test_export_final_csv_missing_seller_name(self, tmp_path):
        """Test ValueError when seller_name is missing in final CSV.

        Given: Seller dict without seller_name key
        When: export_final_csv is called
        Then: ValueError should be raised with key information
        """
        # Given
        exporter = CSVExporter(output_dir=str(tmp_path) + "/")
        sellers = [
            {
                "seller_url": "https://auctions.yahoo.co.jp/seller",
                "is_anime_seller": True,
            }
        ]

        # When/Then
        with pytest.raises(ValueError, match="missing required key 'seller_name'"):
            exporter.export_final_csv(sellers)

    def test_export_final_csv_missing_seller_url(self, tmp_path):
        """Test ValueError when seller_url is missing in final CSV.

        Given: Seller dict without seller_url key
        When: export_final_csv is called
        Then: ValueError should be raised with key information
        """
        # Given
        exporter = CSVExporter(output_dir=str(tmp_path) + "/")
        sellers = [
            {
                "seller_name": "テストセラー",
                "is_anime_seller": True,
            }
        ]

        # When/Then
        with pytest.raises(ValueError, match="missing required key 'seller_url'"):
            exporter.export_final_csv(sellers)

    def test_export_intermediate_csv_non_dict_item(self, tmp_path):
        """Test ValueError when seller item is not a dict.

        Given: sellers list contains non-dict item
        When: export_intermediate_csv is called
        Then: ValueError should be raised
        """
        # Given
        exporter = CSVExporter(output_dir=str(tmp_path) + "/")
        sellers = [
            "not a dict",
        ]

        # When/Then
        with pytest.raises(ValueError, match="must be a dict"):
            exporter.export_intermediate_csv(sellers)

    def test_export_final_csv_non_dict_item(self, tmp_path):
        """Test ValueError when seller item is not a dict in final CSV.

        Given: sellers list contains non-dict item
        When: export_final_csv is called
        Then: ValueError should be raised
        """
        # Given
        exporter = CSVExporter(output_dir=str(tmp_path) + "/")
        sellers = [
            "not a dict",
        ]

        # When/Then
        with pytest.raises(ValueError, match="must be a dict"):
            exporter.export_final_csv(sellers)
