"""CSRF token manager for GLPI."""

from bs4 import BeautifulSoup

class CsrfManager:
    def __init__(self, page):
        self.page = page
        self._token = None

    def refresh(self):
        soup = BeautifulSoup(self.page.content(), "html.parser")
        node = soup.find("input", {"name": "_glpi_csrf_token"})
        self._token = node.get("value") if node else None
        return self._token

    def get_token(self):
        return self._token or self.refresh()

    def inject_headers(self, headers: dict):
        headers["X-Glpi-Csrf-Token"] = self.get_token()
        return headers
