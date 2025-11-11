"""
Rapras & Yahoo Auctions 認証の使用例

このスクリプトは、Rapras と Yahoo Auctions への自動ログインを実行します。
実行前に .env ファイルに認証情報を設定してください。
"""

import asyncio
import os

from dotenv import load_dotenv

from modules.config.settings import load_proxy_config, load_rapras_config, load_yahoo_config
from modules.scraper.rapras_scraper import RaprasScraper
from modules.scraper.session_manager import SessionManager
from modules.scraper.yahoo_scraper import YahooAuctionScraper
from modules.utils.logger import get_logger

logger = get_logger(__name__)


async def main():
    """メイン処理"""
    # .envファイルから環境変数を読み込み
    load_dotenv()

    # ヘッドレスモード設定を読み込み（デフォルト: True）
    headless = os.getenv("HEADLESS", "true").lower() in ("true", "1", "yes")

    # セッションマネージャーを作成
    session_manager = SessionManager(session_dir="sessions")

    # 1. Rapras認証
    logger.info("=" * 50)
    logger.info("Rapras認証を開始します")
    logger.info("=" * 50)

    try:
        # 設定を読み込み
        rapras_config = load_rapras_config()

        # RaprasScraperを作成
        rapras_scraper = RaprasScraper(session_manager=session_manager, headless=headless)

        # ログイン実行
        success = await rapras_scraper.login(rapras_config.username, rapras_config.password)

        if success:
            logger.info("✅ Raprasログイン成功！")
        else:
            logger.error("❌ Raprasログイン失敗")

        # クリーンアップ
        await rapras_scraper.close()

    except Exception as e:
        logger.error(f"Rapras認証でエラーが発生しました: {e}")

    # 2. Yahoo Auctions認証
    logger.info("\n" + "=" * 50)
    logger.info("Yahoo Auctions認証を開始します")
    logger.info("=" * 50)

    try:
        # 設定を読み込み
        yahoo_config = load_yahoo_config()
        proxy_config = load_proxy_config()

        # プロキシ設定をdict形式に変換
        proxy_dict = {
            "url": proxy_config.url,
            "username": proxy_config.username,
            "password": proxy_config.password,
        }

        # YahooAuctionScraperを作成
        yahoo_scraper = YahooAuctionScraper(
            session_manager=session_manager, proxy_config=proxy_dict, headless=headless
        )

        # ログイン実行（SMS認証コードの入力を促されます）
        success = await yahoo_scraper.login(yahoo_config.phone_number)

        if success:
            logger.info("✅ Yahoo Auctionsログイン成功！")
        else:
            logger.error("❌ Yahoo Auctionsログイン失敗")

        # クリーンアップ
        await yahoo_scraper.close()

    except Exception as e:
        logger.error(f"Yahoo Auctions認証でエラーが発生しました: {e}")

    logger.info("\n" + "=" * 50)
    logger.info("全ての認証処理が完了しました")
    logger.info("=" * 50)


if __name__ == "__main__":
    # 非同期処理を実行
    asyncio.run(main())
