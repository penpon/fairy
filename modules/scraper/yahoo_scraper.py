"""Yahoo Auctions authentication scraper module with proxy support."""

import asyncio

from playwright.async_api import Browser, BrowserContext, Page, Playwright, async_playwright

from modules.scraper.session_manager import SessionManager
from modules.utils.logger import get_logger

logger = get_logger(__name__)


class ProxyAuthenticationError(Exception):
    """プロキシ認証に失敗した場合の例外"""

    pass


class LoginError(Exception):
    """ログイン処理に失敗した場合の例外"""

    pass


class YahooAuctionScraper:
    """Yahoo Auctionsへの電話番号・SMS認証を自動化するクラス（プロキシBASIC認証経由）"""

    def __init__(
        self,
        session_manager: SessionManager,
        proxy_config: dict[str, str],
        yahoo_url: str = "https://auctions.yahoo.co.jp/",
    ) -> None:
        """初期化：SessionManagerとプロキシ設定を依存注入

        Args:
            session_manager: Cookie管理用のSessionManager
            proxy_config: {"url": "...", "username": "...", "password": "..."}（urlはプロキシサーバーのURL）
            yahoo_url: Yahoo AuctionsのURL（デフォルト: https://auctions.yahoo.co.jp/）

        Raises:
            ValueError: proxy_configに必須キーが不足している場合
        """
        # プロキシ設定の検証
        required_keys = {"url", "username", "password"}
        if not all(key in proxy_config for key in required_keys):
            missing_keys = required_keys - set(proxy_config.keys())
            raise ValueError(f"proxy_config is missing required keys: {missing_keys}")

        self.session_manager = session_manager
        self.proxy_config = proxy_config
        self.yahoo_url = yahoo_url
        self.playwright: Playwright | None = None
        self.browser: Browser | None = None
        self.context: BrowserContext | None = None
        self.page: Page | None = None
        self._max_retries = 3
        self._retry_delays = [2, 4, 8]  # 指数バックオフ（秒）
        self._timeout = 30000  # 30秒（ミリ秒）
        self._sms_timeout = 180  # 3分（秒）

    async def login(self, phone_number: str) -> bool:
        """Yahoo Auctionsにログイン（SMS認証）

        Args:
            phone_number: ログイン用電話番号

        Returns:
            ログイン成功時True

        Raises:
            ProxyAuthenticationError: プロキシ認証失敗
            LoginError: ログイン処理に失敗した場合
            TimeoutError: タイムアウト（30秒）が発生した場合
        """
        # プロキシ認証エラーは1回のみ試行（リトライなし）
        try:
            await self._verify_proxy_connection()
        except ProxyAuthenticationError:
            logger.error("Proxy authentication failed")
            raise

        # ログイン処理はリトライ可能
        for attempt in range(self._max_retries):
            try:
                logger.info(f"Login attempt {attempt + 1}/{self._max_retries}")

                # セッションが存在する場合は復元を試みる
                if self.session_manager.session_exists("yahoo"):
                    logger.info("Existing session found, attempting to restore")
                    if await self._restore_session():
                        if await self.is_logged_in():
                            logger.info("Session restored successfully")
                            return True
                        else:
                            logger.warning("Session restoration failed, proceeding with login")

                # ブラウザを起動（プロキシ設定を含む）
                await self._launch_browser_with_proxy()

                # ログインページにアクセス
                await self.page.goto(self.yahoo_url, timeout=self._timeout)
                logger.info(f"Navigated to {self.yahoo_url}")

                # 電話番号を入力
                await self._fill_phone_number(phone_number)

                # SMS送信ボタンをクリック
                await self._click_send_sms_button()

                # ユーザーにSMS認証コード入力を促す
                sms_code = await self._prompt_for_sms_code()

                # SMS認証コードを入力
                await self._fill_sms_code(sms_code)

                # ログイン成功を確認
                if await self.is_logged_in():
                    # セッションCookieを保存
                    cookies = await self.context.cookies()
                    self.session_manager.save_session("yahoo", cookies)
                    logger.info("Login successful")
                    return True
                else:
                    logger.warning("Login validation failed")
                    if attempt < self._max_retries - 1:
                        await self._retry_with_backoff(attempt)
                    continue

            except TimeoutError as e:
                logger.warning(f"Timeout occurred: {e}")
                if attempt < self._max_retries - 1:
                    await self._retry_with_backoff(attempt)
                else:
                    raise TimeoutError(f"Login timed out after {self._max_retries} attempts") from e

            except Exception as e:
                logger.error(f"Unexpected error during login: {e}")
                if attempt < self._max_retries - 1:
                    await self._retry_with_backoff(attempt)
                else:
                    raise LoginError(f"Login failed after {self._max_retries} attempts: {e}") from e

    async def _verify_proxy_connection(self) -> None:
        """プロキシ接続を検証

        Raises:
            ProxyAuthenticationError: プロキシ認証失敗
        """
        temp_playwright = None
        temp_browser = None
        temp_context = None
        temp_page = None

        try:
            # 一時的にブラウザを起動してプロキシ接続を確認
            temp_playwright = await async_playwright().start()
            temp_browser = await temp_playwright.chromium.launch(headless=True)

            # プロキシ設定でコンテキストを作成
            temp_context = await temp_browser.new_context(
                proxy={
                    "server": self.proxy_config["url"],
                    "username": self.proxy_config["username"],
                    "password": self.proxy_config["password"],
                }
            )

            temp_page = await temp_context.new_page()

            # 簡単な接続テスト
            try:
                await temp_page.goto("https://www.google.com", timeout=10000)
                logger.info("Proxy connection verified successfully")
            except Exception as e:
                # プロキシ認証エラーと判定
                logger.error(f"Proxy connection test failed: {e}")
                raise ProxyAuthenticationError(
                    "Proxy authentication failed. Please check PROXY_USERNAME and PROXY_PASSWORD in .env"
                ) from e

        except ProxyAuthenticationError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error during proxy verification: {e}")
            raise ProxyAuthenticationError(f"Proxy verification failed: {e}") from e
        finally:
            # リソースをクリーンアップ
            if temp_page:
                try:
                    await temp_page.close()
                except Exception as e:
                    logger.warning(f"Error closing temp page: {e}")

            if temp_context:
                try:
                    await temp_context.close()
                except Exception as e:
                    logger.warning(f"Error closing temp context: {e}")

            if temp_browser:
                try:
                    await temp_browser.close()
                except Exception as e:
                    logger.warning(f"Error closing temp browser: {e}")

            if temp_playwright:
                try:
                    await temp_playwright.stop()
                except Exception as e:
                    logger.warning(f"Error stopping temp playwright: {e}")

    async def _launch_browser_with_proxy(self) -> None:
        """プロキシ設定でブラウザを起動"""
        if not self.playwright:
            self.playwright = await async_playwright().start()

        if not self.browser:
            self.browser = await self.playwright.chromium.launch(headless=True)

        if not self.context:
            # プロキシ設定を含むコンテキストを作成
            # ログに認証情報を出力しない
            proxy_server = self.proxy_config["url"]
            logger.info(f"Launching browser with proxy: {proxy_server}")

            self.context = await self.browser.new_context(
                proxy={
                    "server": self.proxy_config["url"],
                    "username": self.proxy_config["username"],
                    "password": self.proxy_config["password"],
                }
            )

        if not self.page:
            self.page = await self.context.new_page()

    async def _restore_session(self) -> bool:
        """セッションを復元

        Returns:
            復元成功時True、失敗時False
        """
        try:
            cookies = self.session_manager.load_session("yahoo")
            if not cookies:
                return False

            await self._launch_browser_with_proxy()
            await self.context.add_cookies(cookies)
            await self.page.goto(self.yahoo_url, timeout=self._timeout)
            return True

        except Exception as e:
            logger.warning(f"Session restoration failed: {e}")
            return False

    async def _fill_phone_number(self, phone_number: str) -> None:
        """電話番号を入力フォームに入力

        Args:
            phone_number: 電話番号
        """
        # 実際のYahoo Auctionsサイトのセレクタに合わせて調整が必要
        await self.page.fill('input[name="phone"]', phone_number, timeout=self._timeout)
        logger.info("Phone number filled (value not logged for security)")

    async def _click_send_sms_button(self) -> None:
        """SMS送信ボタンをクリック"""
        # 実際のYahoo Auctionsサイトのセレクタに合わせて調整が必要
        await self.page.click('button[type="submit"]', timeout=self._timeout)
        await self.page.wait_for_load_state("networkidle", timeout=self._timeout)
        logger.info("SMS send button clicked")

    async def _prompt_for_sms_code(self) -> str:
        """ユーザーにSMS認証コード入力を促す

        Returns:
            ユーザーが入力したSMS認証コード

        Raises:
            TimeoutError: SMS入力タイムアウト（3分）
        """
        logger.info("Waiting for SMS code input (timeout: 3 minutes)")
        print("\n" + "=" * 50)
        print("SMS認証コードを入力してください")
        print("タイムアウト: 3分")
        print("=" * 50)

        try:
            # asyncio.wait_forで3分のタイムアウトを設定
            sms_code = await asyncio.wait_for(
                asyncio.to_thread(input, "SMS認証コード: "), timeout=self._sms_timeout
            )

            if not sms_code.strip():
                raise ValueError("SMS code cannot be empty")

            logger.info("SMS code received")
            return sms_code.strip()

        except TimeoutError as e:
            logger.error("SMS code input timeout")
            raise TimeoutError("SMS code input timeout. Please try again.") from e

    async def _fill_sms_code(self, sms_code: str) -> None:
        """SMS認証コードを入力フォームに入力

        Args:
            sms_code: SMS認証コード
        """
        # 実際のYahoo Auctionsサイトのセレクタに合わせて調整が必要
        await self.page.fill('input[name="code"]', sms_code, timeout=self._timeout)
        await self.page.click('button[type="submit"]', timeout=self._timeout)
        await self.page.wait_for_load_state("networkidle", timeout=self._timeout)
        logger.info("SMS code submitted")

    async def _retry_with_backoff(self, attempt: int) -> None:
        """指数バックオフでリトライ待機

        Args:
            attempt: 現在の試行回数（0始まり）
        """
        delay = self._retry_delays[attempt]
        logger.info(f"Retrying in {delay} seconds...")
        await asyncio.sleep(delay)

    async def is_logged_in(self) -> bool:
        """ログイン状態を確認

        Returns:
            ログイン済みの場合True、未ログインの場合False
        """
        try:
            if not self.page:
                return False

            # 実際のYahoo Auctionsサイトのログイン判定ロジックに合わせて調整が必要
            # ここではログアウトボタンまたはユーザーメニューの存在で判定
            logout_button = await self.page.query_selector('a[href*="logout"]')
            return logout_button is not None

        except Exception as e:
            logger.warning(f"Failed to check login status: {e}")
            return False

    async def close(self) -> None:
        """ブラウザセッションを閉じる"""
        try:
            if self.page:
                await self.page.close()
                self.page = None

            if self.context:
                await self.context.close()
                self.context = None

            if self.browser:
                await self.browser.close()
                self.browser = None

            if self.playwright:
                await self.playwright.stop()
                self.playwright = None

            logger.info("Browser session closed")

        except Exception as e:
            logger.warning(f"Error while closing browser: {e}")
