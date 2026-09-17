"""Guarded persistence for GLPI Impact workspaces through the GLPI UI."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from playwright.sync_api import Page

from .builder import ImpactBuilder


class PersistenceError(RuntimeError):
    """Raised when a safe GLPI Impact persistence operation cannot proceed."""


@dataclass(frozen=True)
class SaveResult:
    attempted: bool
    persisted: bool
    dry_run: bool
    delta_before: dict[str, Any]
    delta_after: dict[str, Any] | None = None


class ImpactPersistence:
    """Persist a prepared workspace only through an observed GLPI UI control.

    Direct calls to ``ajax/impact.php`` are intentionally not implemented.
    A real write requires ``confirm=True`` and an unambiguous visible save
    control. The default behavior is therefore a non-mutating dry run.
    """

    SAVE_PATTERN = r"save|apply|update|guardar|aplicar|actualizar"

    def __init__(self, page: Page, builder: ImpactBuilder | None = None):
        self.page = page
        self.builder = builder or ImpactBuilder(page)

    def pending_delta(self) -> dict[str, Any]:
        return self.builder.compute_delta()

    def has_pending_changes(self) -> bool:
        delta = self.pending_delta()
        return self._contains_change(delta)

    def save_controls(self) -> list[dict[str, Any]]:
        """Return visible controls whose metadata indicates a save action."""
        return self.page.evaluate(
            """pattern => [...document.querySelectorAll('button, a, input[type=submit]')]
                .filter(el => {
                    const style = window.getComputedStyle(el);
                    const visible = style.display !== 'none' && style.visibility !== 'hidden';
                    const text = [
                        el.innerText,
                        el.value,
                        el.title,
                        el.getAttribute('aria-label'),
                        el.name,
                        el.id
                    ].filter(Boolean).join(' ');
                    return visible && new RegExp(pattern, 'i').test(text);
                })
                .map((el, index) => ({
                    index,
                    tag: el.tagName.toLowerCase(),
                    id: el.id || null,
                    name: el.getAttribute('name'),
                    text: (el.innerText || el.value || '').trim(),
                    title: el.title || null,
                    aria_label: el.getAttribute('aria-label')
                }))""",
            self.SAVE_PATTERN,
        )

    def save(self, *, confirm: bool = False, timeout: int = 30_000) -> SaveResult:
        delta_before = self.pending_delta()
        if not self._contains_change(delta_before):
            return SaveResult(False, False, not confirm, delta_before, delta_before)

        if not confirm:
            return SaveResult(False, False, True, delta_before, None)

        controls = self.save_controls()
        if len(controls) != 1:
            raise PersistenceError(
                f"Expected exactly one visible GLPI save control, found {len(controls)}"
            )

        control = controls[0]
        selector = self._selector(control)
        locator = self.page.locator(selector).first
        locator.click()

        self.page.wait_for_timeout(500)
        try:
            self.page.wait_for_function(
                """() => {
                    if (!window.GLPIImpact || !GLPIImpact.computeDelta) return false;
                    const delta = GLPIImpact.computeDelta();
                    const changed = value => {
                        if (Array.isArray(value)) return value.length > 0;
                        if (value && typeof value === 'object') {
                            return Object.values(value).some(changed);
                        }
                        return value !== null && value !== undefined && value !== false && value !== '';
                    };
                    return !changed(delta);
                }""",
                timeout=timeout,
            )
        except Exception:
            pass

        delta_after = self.pending_delta()
        persisted = not self._contains_change(delta_after)
        return SaveResult(True, persisted, False, delta_before, delta_after)

    @classmethod
    def _contains_change(cls, value: Any) -> bool:
        if isinstance(value, dict):
            return any(cls._contains_change(item) for item in value.values())
        if isinstance(value, (list, tuple, set)):
            return any(cls._contains_change(item) for item in value)
        return value not in (None, False, "", 0)

    @staticmethod
    def _selector(control: dict[str, Any]) -> str:
        if control.get("id"):
            escaped = str(control["id"]).replace('"', '\\"')
            return f'[id="{escaped}"]'
        if control.get("name"):
            escaped = str(control["name"]).replace('"', '\\"')
            return f'{control["tag"]}[name="{escaped}"]'
        raise PersistenceError("Save control has no stable id or name selector")
