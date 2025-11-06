"""Session management module for cookie persistence and restoration."""

import json
from pathlib import Path
from typing import Any

from modules.utils.logger import get_logger

logger = get_logger(__name__)


class SessionManager:
    """Cookie永続化・復元によるセッション管理クラス"""

    def __init__(self, session_dir: str = "sessions") -> None:
        """初期化：セッションファイル保存ディレクトリを指定

        Args:
            session_dir: セッションファイル保存ディレクトリパス（デフォルト: "sessions"）
        """
        self.session_dir = Path(session_dir)

    def save_session(self, service_name: str, cookies: list[dict[str, Any]]) -> None:
        """セッションCookieをファイルに保存

        Args:
            service_name: サービス名（"rapras" or "yahoo"）
            cookies: Playwrightから取得したCookieリスト

        Raises:
            IOError: ファイル書き込み失敗時（警告ログ出力）
        """
        try:
            # ディレクトリが存在しない場合は作成
            self.session_dir.mkdir(parents=True, exist_ok=True)

            session_file = self.session_dir / f"{service_name}_session.json"

            # Cookieをファイルに保存
            with session_file.open("w", encoding="utf-8") as f:
                json.dump(cookies, f, ensure_ascii=False, indent=2)

            logger.info(f"Session saved successfully: {session_file}")

        except OSError as e:
            logger.warning(f"Failed to save session for {service_name}: {e}")

    def load_session(self, service_name: str) -> list[dict[str, Any]] | None:
        """セッションCookieをファイルから読み込み

        Args:
            service_name: サービス名（"rapras" or "yahoo"）

        Returns:
            Cookieリスト、ファイルが存在しない場合はNone

        Raises:
            JSONDecodeError: ファイル破損時（警告ログ出力、Noneを返す）
        """
        session_file = self.session_dir / f"{service_name}_session.json"

        # ファイルが存在しない場合はNone
        if not session_file.exists():
            logger.info(f"No session file found for {service_name}")
            return None

        try:
            # Cookieをファイルから読み込み
            with session_file.open("r", encoding="utf-8") as f:
                cookies = json.load(f)

            logger.info(f"Session loaded successfully: {session_file}")
            return cookies

        except json.JSONDecodeError as e:
            logger.warning(f"Session file corrupted for {service_name}: {e}")
            return None

        except OSError as e:
            logger.warning(f"Failed to load session for {service_name}: {e}")
            return None

    def session_exists(self, service_name: str) -> bool:
        """セッションファイルの存在確認

        Args:
            service_name: サービス名（"rapras" or "yahoo"）

        Returns:
            セッションファイルが存在する場合True、存在しない場合False
        """
        session_file = self.session_dir / f"{service_name}_session.json"
        return session_file.exists()

    def delete_session(self, service_name: str) -> None:
        """セッションファイルを削除

        Args:
            service_name: サービス名（"rapras" or "yahoo"）
        """
        session_file = self.session_dir / f"{service_name}_session.json"

        if session_file.exists():
            try:
                session_file.unlink()
                logger.info(f"Session deleted successfully: {session_file}")
            except OSError as e:
                logger.warning(f"Failed to delete session for {service_name}: {e}")
        else:
            logger.info(f"No session file to delete for {service_name}")
