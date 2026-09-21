"""Authentication manager for GLPI."""

from urllib.parse import urljoin
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from ..browser.manager import BrowserManager


class LoginError(RuntimeError):
    """Raised when the GLPI login flow cannot establish a session."""


class LoginManager:
    """Handle authentication against GLPI instances through the browser UI."""

    def __init__(self, browser: BrowserManager):
        self.browser = browser
        self.base_url: str | None = None

    def login(self, url: str, username: str, password: str, *, timeout: int = 30_000):
        session = self.browser.start()
        self.base_url = url.rstrip("/") + "/"
        session.goto(self.base_url)
        page = session.page

        page.locator("input[name='login_name']").fill(username)
        page.locator("input[name='login_password']").fill(password)
        page.locator("form").locator("button, input[type='submit']").first.click()

        try:
            page.wait_for_function(
                """() => !document.querySelector("input[name='login_password']")""",
                timeout=timeout,
            )
        except PlaywrightTimeoutError as exc:
            raise LoginError(
                "GLPI login was not confirmed; credentials, MFA, SSO or the login page may require manual handling"
            ) from exc

        if page.locator("input[name='login_password']").count():
            raise LoginError("GLPI login form is still visible after submission")
        return session

    def logout(self):
        page = self.browser.page
        if page and not page.is_closed():
            if not self.base_url:
                raise LoginError("Cannot build logout URL before a GLPI base URL is established")
            page.goto(urljoin(self.base_url, "front/logout.php"))

    def is_logged_in(self) -> bool:
        page = self.browser.page
        return bool(
            page is not None
            and not page.is_closed()
            and page.locator("input[name='login_password']").count() == 0
        )
