"""Rapras authentication scraper module."""

import asyncio

from playwright.async_api import Browser, BrowserContext, Page, Playwright, async_playwright

from modules.scraper.session_manager import SessionManager
from modules.utils.logger import get_logger

logger = get_logger(__name__)


class LoginError(Exception):
    """ログイン処理に失敗した場合の例外"""

    pass


class RaprasScraper:
    """Raprasサイトへのユーザー名・パスワード認証を自動化するクラス"""

    def __init__(
        self,
        session_manager: SessionManager,
        rapras_url: str = "https://www.rapras.jp/",
        headless: bool = True,
    ) -> None:
        """初期化：SessionManagerを依存注入

        Args:
            session_manager: Cookie管理用のSessionManager
            rapras_url: RaprasのURL（デフォルト: https://www.rapras.jp/）
            headless: ブラウザをヘッドレスモードで起動するか（デフォルト: True）
        """
        self.session_manager = session_manager
        self.rapras_url = rapras_url
        self.headless = headless
        self.playwright: Playwright | None = None
        self.browser: Browser | None = None
        self.context: BrowserContext | None = None
        self.page: Page | None = None

        self._max_retries = 3
        # 指数バックオフ：2^1=2, 2^2=4, 2^3=8秒
        self._retry_delays = [2**i for i in range(1, self._max_retries + 1)]
        self._timeout = (
            30000  # 30秒（ミリ秒）  # 30秒（ミリ秒）  # 30秒（ミリ秒）  # 30秒（ミリ秒）
        )

    async def login(self, username: str, password: str) -> bool:
        """Raprasにログイン

        Args:
            username: Raprasユーザー名
            password: Raprasパスワード

        Returns:
            ログイン成功時True

        Raises:
            LoginError: ログイン処理に失敗した場合
            TimeoutError: タイムアウト（30秒）が発生した場合
        """
        for attempt in range(self._max_retries):
            try:
                logger.info(f"Login attempt {attempt + 1}/{self._max_retries}")

                # セッションが存在する場合は復元を試みる
                if self.session_manager.session_exists("rapras"):
                    logger.info("Existing session found, attempting to restore")
                    if await self._restore_session():
                        if await self.is_logged_in():
                            logger.info("Session restored successfully")
                            return True
                        else:
                            logger.warning("Session restoration failed, proceeding with login")
                            # 復元されたブラウザをクリーンアップ
                            await self._close_browser()

                # ブラウザを起動
                await self._launch_browser()

                # ログインページにアクセス
                await self.page.goto(self.rapras_url, timeout=self._timeout)
                logger.info(f"Navigated to {self.rapras_url}")

                # ユーザー名とパスワードを入力
                await self._fill_credentials(username, password)

                # ログインボタンをクリック
                await self._click_login_button()

                # ログイン成功を確認
                if await self.is_logged_in():
                    # セッションCookieを保存
                    cookies = await self.context.cookies()
                    self.session_manager.save_session("rapras", cookies)
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

        # forループを抜けた = 3回すべて失敗した
        raise LoginError(
            f"Login failed after {self._max_retries} attempts: Invalid credentials or login process failed"
        )

    async def _launch_browser(self) -> None:
        """ブラウザを起動"""
        if not self.playwright:
            self.playwright = await async_playwright().start()

        if not self.browser:
            self.browser = await self.playwright.chromium.launch(headless=self.headless)

        if not self.context:
            self.context = await self.browser.new_context()

        if not self.page:
            self.page = await self.context.new_page()

    async def _restore_session(self) -> bool:
        """セッションを復元

        Returns:
            復元成功時True、失敗時False
        """
        try:
            cookies = self.session_manager.load_session("rapras")
            if not cookies:
                return False

            await self._launch_browser()
            await self.context.add_cookies(cookies)
            await self.page.goto(self.rapras_url, timeout=self._timeout)
            return True

        except Exception as e:
            logger.warning(f"Session restoration failed: {e}")
            return False

    async def _fill_credentials(self, username: str, password: str) -> None:
        """ユーザー名とパスワードを入力フォームに入力

        Args:
            username: ユーザー名
            password: パスワード
        """
        # 実際のRaprasサイトのセレクタに合わせて調整が必要
        # ここでは一般的なセレクタを使用
        await self.page.fill('input[name="username"]', username, timeout=self._timeout)
        await self.page.fill('input[name="password"]', password, timeout=self._timeout)
        logger.info("Credentials filled")

    async def _click_login_button(self) -> None:
        """ログインボタンをクリック"""
        # テキストが「ログイン」のボタンをクリック
        await self.page.get_by_role("button", name="ログイン").click(timeout=self._timeout)
        await self.page.wait_for_load_state("networkidle", timeout=self._timeout)
        logger.info("Login button clicked")

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

            # 実際のRaprasサイトのログイン判定ロジックに合わせて調整が必要
            # ここではログアウトボタンまたはユーザーメニューの存在で判定
            # 例: ログイン後に表示される要素をチェック
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

    async def _close_browser(self) -> None:
        """ブラウザセッションをクリーンアップ（内部用）"""
        await self.close()

    async def fetch_seller_links(
        self, start_date: str, end_date: str, min_price: int = 100000
    ) -> list[dict]:
        """集計ページからセラーリンクを取得

        Args:
            start_date: 開始日（YYYY-MM-DD）
            end_date: 終了日（YYYY-MM-DD）
            min_price: 最低落札価格合計（デフォルト10万円）

        Returns:
            list[dict]: [{"seller_name": str, "total_price": int, "link": str}]

        Raises:
            RuntimeError: ブラウザが初期化されていない場合
        """
        if not self.page:
            raise RuntimeError("Browser not initialized. Call login() first.")

        try:
            # 集計ページURL
            url = (
                f"{self.rapras_url}sum_analyse"
                f"?target=epsum&updown=down&genre=all"
                f"&sdate={start_date}&edate={end_date}"
            )

            logger.info(f"Fetching seller links from {url}")
            await self.page.goto(url, timeout=self._timeout)

            # セラーテーブルの行を取得
            rows = await self.page.query_selector_all("table tbody tr")
            logger.info(f"Found {len(rows)} seller rows")

            sellers = []
            for row in rows:
                try:
                    # セラー名を取得（2列目）
                    seller_name_elem = await row.query_selector("td:nth-child(2)")
                    if not seller_name_elem:
                        continue
                    seller_name = await seller_name_elem.inner_text()

                    # 落札価格合計を取得（5列目）
                    price_elem = await row.query_selector("td:nth-child(5)")
                    if not price_elem:
                        continue
                    price_text = await price_elem.inner_text()

                    # 価格文字列から数値を抽出（例: "150,000円" → 150000）
                    price_value = int(price_text.replace(",", "").replace("円", ""))

                    # min_price未満はスキップ
                    if price_value < min_price:
                        logger.debug(
                            f"Skipping seller {seller_name} (price: {price_value} < {min_price})"
                        )
                        continue

                    # セラーリンクを取得
                    link_elem = await row.query_selector("td:nth-child(2) a")
                    if not link_elem:
                        continue
                    link = await link_elem.get_attribute("href")

                    sellers.append(
                        {"seller_name": seller_name, "total_price": price_value, "link": link}
                    )

                except (ValueError, AttributeError) as e:
                    logger.warning(f"Failed to parse seller row: {e}")
                    continue

            logger.info(f"Collected {len(sellers)} sellers with price >= {min_price}")
            return sellers

        except TimeoutError as e:
            logger.error(f"Timeout while fetching seller links: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to fetch seller links: {e}")
            raise
