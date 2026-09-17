"""Authentication manager for GLPI."""

from ..browser.manager import BrowserManager


class LoginManager:
    """Handles authentication against GLPI instances."""

    def __init__(self, browser: BrowserManager):
        self.browser = browser

    def login(self, url: str, username: str, password: str):
        session = self.browser.start()
        session.goto(f"{url}/")
        page = session.page
        page.locator("input[name='login_name']").fill(username)
        page.locator("input[name='login_password']").fill(password)
        page.locator("form").locator("button, input[type='submit']").first.click()
        return session

    def logout(self):
        if self.browser.page:
            self.browser.page.goto("front/logout.php")

    def is_logged_in(self) -> bool:
        return self.browser.page is not None
