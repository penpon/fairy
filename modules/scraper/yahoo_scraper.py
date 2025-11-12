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
        yahoo_login_url: str = "https://login.yahoo.co.jp/config/login",
        yahoo_auctions_url: str = "https://auctions.yahoo.co.jp/",
        headless: bool = True,
    ) -> None:
        """初期化：SessionManagerとプロキシ設定を依存注入

        Args:
            session_manager: Cookie管理用のSessionManager
            proxy_config: {"url": "...", "username": "...", "password": "..."}（urlはプロキシサーバーのURL）
            yahoo_login_url: Yahoo ログインページのURL（デフォルト: https://login.yahoo.co.jp/config/login）
            yahoo_auctions_url: Yahoo AuctionsのURL（デフォルト: https://auctions.yahoo.co.jp/）
            headless: ブラウザをヘッドレスモードで起動するか（デフォルト: True）

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
        self.yahoo_login_url = yahoo_login_url
        self.yahoo_auctions_url = yahoo_auctions_url
        self.headless = headless
        self.playwright: Playwright | None = None
        self.browser: Browser | None = None
        self.context: BrowserContext | None = None
        self.page: Page | None = None
        self._max_retries = 3
        self._retry_delays = [2, 4, 8]  # 指数バックオフ（秒）
        self._timeout = 30000  # 30秒（ミリ秒）
        self._sms_timeout = 180  # 3分（秒）  # 3分（秒）

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
                await self.page.goto(self.yahoo_login_url, timeout=self._timeout)
                logger.info(f"Navigated to {self.yahoo_login_url}")

                # 電話番号を入力
                await self._fill_phone_number(phone_number)

                # SMS送信ボタンをクリック
                await self._click_send_sms_button()

                # ユーザーにSMS認証コード入力を促す
                sms_code = await self._prompt_for_sms_code()

                # SMS認証コードを入力
                await self._fill_sms_code(sms_code)

                # Yahoo Auctionsページに遷移してログイン確認
                logger.info("Navigating to Yahoo Auctions to verify login")
                try:
                    await self.page.goto(
                        self.yahoo_auctions_url,
                        timeout=self._timeout,
                        wait_until="domcontentloaded",
                    )
                    logger.info(f"Navigated to Yahoo Auctions: {self.yahoo_auctions_url}")
                except Exception as e:
                    logger.warning(
                        f"Failed to navigate to Yahoo Auctions: {e}, trying with current page"
                    )

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

        # forループを抜けた = 3回すべて失敗した
        raise LoginError(
            f"Login failed after {self._max_retries} attempts: Invalid credentials or login process failed"
        )

    async def _verify_proxy_connection(self) -> None:
        """プロキシ接続を検証し、IPアドレスが期待値と一致するか確認

        Raises:
            ProxyAuthenticationError: プロキシ認証失敗またはIPアドレス不一致
        """
        temp_playwright = None
        temp_browser = None
        temp_context = None
        temp_page = None

        try:
            # 一時的にブラウザを起動してプロキシ接続を確認
            temp_playwright = await async_playwright().start()
            temp_browser = await temp_playwright.chromium.launch(headless=self.headless)

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

            # IPアドレスの確認（/ip エンドポイントを使用してプレーンテキストのIPのみを取得）
            try:
                logger.info("Checking IP address via proxy...")
                await temp_page.goto("https://inet-ip.info/ip", timeout=10000)

                # ページのテキストコンテンツを取得（プレーンテキストのIPアドレスのみ）
                ip_text = await temp_page.text_content("body")

                # IPアドレスを抽出（前後の空白や改行を削除）
                current_ip = ip_text.strip() if ip_text else ""

                logger.info(f"Current IP address: {current_ip}")

                # 期待されるIPアドレス
                expected_ip = "164.70.96.2"

                if current_ip != expected_ip:
                    error_msg = f"IP address mismatch! Expected: {expected_ip}, Got: {current_ip}"
                    logger.error(error_msg)
                    raise ProxyAuthenticationError(f"Proxy IP verification failed. {error_msg}")

                logger.info(f"✅ IP address verified: {current_ip}")

            except ProxyAuthenticationError:
                raise
            except Exception as e:
                logger.warning(f"IP address verification failed: {e}")
                # IP確認に失敗してもプロキシ接続自体は成功しているので続行
                # より厳格にしたい場合はここでraiseする
                logger.warning("Continuing despite IP verification failure...")

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
            self.browser = await self.playwright.chromium.launch(headless=self.headless)

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
            await self.page.goto(self.yahoo_auctions_url, timeout=self._timeout)
            return True

        except Exception as e:
            logger.warning(f"Session restoration failed: {e}")
            return False

    async def _fill_phone_number(self, phone_number: str) -> None:
        """電話番号を入力フォームに入力

        Args:
            phone_number: 電話番号
        """
        # Yahoo JAPANログインページの携帯電話番号入力フィールド
        await self.page.get_by_role("textbox", name="携帯電話番号/メールアドレス/ID").fill(
            phone_number, timeout=self._timeout
        )
        logger.info("Phone number filled (value not logged for security)")

    async def _click_send_sms_button(self) -> None:
        """「次へ」ボタンをクリックしてSMS送信画面へ、そして「認証コードを送信」ボタンをクリック"""
        # 「次へ」ボタンをクリック
        await self.page.get_by_role("button", name="次へ").click(timeout=self._timeout)
        await self.page.wait_for_load_state("networkidle", timeout=self._timeout)
        logger.info("'Next' button clicked")

        # パスキー認証画面が表示される場合があるので「他の方法でログイン」をクリック
        try:
            other_method_button = await self.page.get_by_role(
                "button", name="他の方法でログイン"
            ).wait_for(timeout=5000)
            if other_method_button:
                await other_method_button.click()
                logger.info("Clicked 'Other login methods' button")
                await self.page.wait_for_load_state("networkidle", timeout=self._timeout)
        except Exception:
            # ボタンが見つからない場合はスキップ（すでにSMS入力画面の場合）
            logger.info("No 'Other login methods' button found, proceeding")

        # 「認証コードを送信」ボタンをクリック
        try:
            send_code_button = await self.page.get_by_role(
                "button", name="認証コードを送信"
            ).wait_for(timeout=5000)
            if send_code_button:
                await send_code_button.click()
                logger.info("Clicked 'Send verification code' button")
                await self.page.wait_for_load_state("networkidle", timeout=self._timeout)
        except Exception as e:
            # ボタンが見つからない場合はログに記録して続行
            logger.warning(f"'Send verification code' button not found: {e}")

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
        """SMS認証コードを入力フォームに入力し、ログインボタンをクリック

        Args:
            sms_code: SMS認証コード
        """
        # SMS認証コード入力フィールドを探す（複数のセレクタを試す）
        code_input = None
        selectors = [
            'input[name="code"]',
            'input[type="text"]',
            'input[placeholder*="認証"]',
            'input[placeholder*="コード"]',
        ]

        for selector in selectors:
            try:
                code_input = await self.page.wait_for_selector(selector, timeout=5000)
                if code_input:
                    logger.info(f"Found SMS code input with selector: {selector}")
                    break
            except Exception:
                continue

        if not code_input:
            raise ValueError("SMS code input field not found")

        # SMSコードを入力
        await self.page.fill(selector, sms_code, timeout=self._timeout)
        logger.info("SMS code filled")

        # ログインボタンをクリック（複数の方法を試す）
        login_clicked = False

        # 方法1: ボタンのテキストで探す
        try:
            login_button = await self.page.get_by_role("button", name="ログイン").wait_for(
                timeout=3000
            )
            if login_button:
                await login_button.click()
                logger.info("Clicked 'Login' button (by role)")
                login_clicked = True
        except Exception:
            pass

        # 方法2: submitボタンで探す
        if not login_clicked:
            try:
                await self.page.click('button[type="submit"]', timeout=3000)
                logger.info("Clicked submit button")
                login_clicked = True
            except Exception:
                pass

        # 方法3: Enterキーを押す
        if not login_clicked:
            try:
                await self.page.keyboard.press("Enter")
                logger.info("Pressed Enter key to submit")
                login_clicked = True
            except Exception:
                pass

        if not login_clicked:
            raise ValueError("Failed to click login button")

        # ページ遷移を待つ
        await self.page.wait_for_load_state("networkidle", timeout=self._timeout)
        logger.info("SMS code submitted and login attempted")

        # Yahoo側のリダイレクトが完全に完了するまで少し待機
        import asyncio

        await asyncio.sleep(2)
        logger.info(f"Current URL after SMS auth: {self.page.url}")

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

            # 現在のURLを取得
            current_url = self.page.url
            logger.debug(f"Checking login status at URL: {current_url}")

            # ログインページにいる場合は未ログイン
            if "login.yahoo.co.jp" in current_url:
                logger.debug("Currently on login page - not logged in")
                return False

            # Yahoo系のドメインにいる場合、複数の条件でログイン状態を確認
            # 1. ログアウトリンクの存在を確認
            logout_button = await self.page.query_selector('a[href*="logout"]')
            if logout_button:
                logger.debug("Found logout link - logged in")
                return True

            # 2. ユーザーメニューやアカウント情報の存在を確認
            user_menu_selectors = [
                'a[href*="myauctions"]',  # マイオークションリンク
                'div[class*="user"]',  # ユーザー関連のdiv
                'a[href*="account"]',  # アカウントリンク
            ]
            for selector in user_menu_selectors:
                element = await self.page.query_selector(selector)
                if element:
                    logger.debug(f"Found user element ({selector}) - logged in")
                    return True

            # 3. yahoo.co.jpまたはauctions.yahoo.co.jpにいて、ログインフォームがない場合はログイン済みと判定
            if "yahoo.co.jp" in current_url:
                login_form = await self.page.query_selector('input[name="login"]')
                if not login_form:
                    logger.debug("On Yahoo domain without login form - likely logged in")
                    return True

            logger.debug("No login indicators found - not logged in")
            return False

        except Exception as e:
            logger.warning(f"Failed to check login status: {e}")
            return False

    async def fetch_seller_products(
        self, seller_url: str, max_products: int = 12
    ) -> dict[str, str | list[str]]:
        """Yahoo Auctionsセラーページから商品名を取得

        Args:
            seller_url: Yahoo AuctionsセラーページURL
            max_products: 取得する最大商品数（デフォルト12）

        Returns:
            dict: {
                "seller_name": str,
                "seller_url": str,
                "product_titles": list[str]
            }

        Raises:
            ConnectionError: プロキシ接続失敗（最大3回リトライ後）
        """
        last_exception = None

        for attempt in range(self._max_retries):
            try:
                logger.info(
                    f"Fetching seller products (attempt {attempt + 1}/{self._max_retries}): {seller_url}"
                )

                # ブラウザ起動（プロキシ設定を含む）
                if not self.page:
                    await self._launch_browser_with_proxy()

                # セラーページにアクセス
                await self.page.goto(seller_url, timeout=self._timeout)
                logger.info(f"Navigated to seller page: {seller_url}")

                # セラー名と商品タイトルを取得
                seller_name = await self._extract_seller_name()
                product_titles = await self._extract_product_titles(max_products)

                logger.info(f"Fetched {len(product_titles)} product titles from {seller_name}")

                # 商品数が指定数未満の場合は警告ログ
                if len(product_titles) < max_products:
                    logger.warning(
                        f"商品数が{max_products}件未満です（{len(product_titles)}件）: {seller_name}"
                    )

                return {
                    "seller_name": seller_name,
                    "seller_url": seller_url,
                    "product_titles": product_titles,
                }

            except (TimeoutError, Exception) as e:
                last_exception = e
                error_type = "Timeout" if isinstance(e, TimeoutError) else "Unexpected error"
                logger.warning(f"{error_type} occurred: {e}")

                if attempt < self._max_retries - 1:
                    await self._retry_with_backoff(attempt)

        # すべてのリトライが失敗した
        error_msg = (
            f"Yahoo Auctionsへの接続が{self._max_retries}回のリトライ後も失敗しました: {seller_url}"
        )
        raise ConnectionError(error_msg) from last_exception

    async def _extract_seller_name(self) -> str:
        """ページからセラー名を抽出

        Returns:
            セラー名（取得できない場合は"不明なセラー"）
        """
        # セラー名セレクタ候補
        seller_name_selectors = ['h1[class*="seller"]', "h1"]

        for selector in seller_name_selectors:
            seller_name_element = await self.page.query_selector(selector)
            if seller_name_element:
                seller_name_text = await seller_name_element.text_content()
                if seller_name_text:
                    return seller_name_text.strip()

        return "不明なセラー"

    async def _extract_product_titles(self, max_products: int) -> list[str]:
        """ページから商品タイトルを抽出

        Args:
            max_products: 取得する最大商品数

        Returns:
            商品タイトルのリスト
        """
        # 商品タイトルセレクタ候補
        product_title_selectors = ['a[class*="product-title"]', 'div[class*="title"]']

        product_elements = []
        for selector in product_title_selectors:
            product_elements = await self.page.query_selector_all(selector)
            if product_elements:
                break

        product_titles: list[str] = []
        for element in product_elements[:max_products]:
            title_text = await element.text_content()
            if title_text:
                product_titles.append(title_text.strip())

        return product_titles

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
