"""Guarded persistence for GLPI Impact workspaces through the GLPI UI."""

from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Callable
from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError
from .builder import ImpactBuilder
from .graph import ImpactEdge
from .network import ImpactNetworkRecorder


class PersistenceError(RuntimeError):
    """Raised when a safe GLPI Impact persistence operation cannot proceed."""


@dataclass(frozen=True)
class SaveResult:
    attempted: bool
    persisted: bool
    dry_run: bool
    delta_before: dict[str, Any]
    delta_after: dict[str, Any] | None = None
    requests: list[dict[str, Any]] | None = None
    delta_cleared: bool = False
    verification: str = "not_attempted"
    reloaded_edge_present: bool | None = None
    successful_write_responses: int = 0


class ImpactPersistence:
    """Persist through GLPI UI and verify writes by reloading the workspace."""

    SAVE_PATTERN = r"save|apply|update|guardar|aplicar|actualizar"

    def __init__(self, page: Page, builder: ImpactBuilder | None = None):
        self.page = page
        self.builder = builder or ImpactBuilder(page)

    def pending_delta(self) -> dict[str, Any]:
        return self.builder.compute_delta()

    def has_pending_changes(self) -> bool:
        return self._contains_change(self.pending_delta())

    def save_controls(self) -> list[dict[str, Any]]:
        return self.page.evaluate("""pattern => [...document.querySelectorAll('button, a, input[type=submit]')]
            .filter(el => {
                const style = window.getComputedStyle(el);
                const visible = style.display !== 'none' && style.visibility !== 'hidden';
                const text = [el.innerText, el.value, el.title, el.getAttribute('aria-label'), el.name, el.id]
                    .filter(Boolean).join(' ');
                return visible && new RegExp(pattern, 'i').test(text);
            })
            .map(el => ({
                tag: el.tagName.toLowerCase(), id: el.id || null,
                name: el.getAttribute('name'),
                text: (el.innerText || el.value || '').trim(),
                title: el.title || null, aria_label: el.getAttribute('aria-label')
            }))""", self.SAVE_PATTERN)

    def save(
        self,
        *,
        confirm: bool = False,
        timeout: int = 30_000,
        expected_edge: ImpactEdge | None = None,
        reload_workspace: Callable[[], None] | None = None,
    ) -> SaveResult:
        delta_before = self.pending_delta()
        if not self._contains_change(delta_before):
            return SaveResult(False, False, not confirm, delta_before, delta_before, [], False, "no_pending_changes")
        if not confirm:
            return SaveResult(False, False, True, delta_before, None, [], False, "dry_run")

        controls = self.save_controls()
        if len(controls) != 1:
            raise PersistenceError(f"Expected exactly one visible GLPI save control, found {len(controls)}")

        recorder = ImpactNetworkRecorder(self.page, impact_only=False).start()
        try:
            self.page.locator(self._selector(controls[0])).first.click()
            try:
                self.page.wait_for_function("""() => {
                    if (!window.GLPIImpact || !GLPIImpact.computeDelta) return false;
                    const delta = GLPIImpact.computeDelta();
                    const changed = value => {
                        if (Array.isArray(value)) return value.length > 0;
                        if (value && typeof value === 'object') return Object.values(value).some(changed);
                        return value !== null && value !== undefined && value !== false && value !== '' && value !== 0;
                    };
                    return !changed(delta);
                }""", timeout=timeout)
            except PlaywrightTimeoutError:
                pass
            self.page.wait_for_timeout(250)
        finally:
            recorder.stop()

        delta_after = self.pending_delta()
        delta_cleared = not self._contains_change(delta_after)
        requests = recorder.snapshot()
        successful_writes = recorder.successful_write_responses()
        persisted = False
        reloaded_edge_present: bool | None = None
        verification = "client_delta_cleared" if delta_cleared else "pending_delta_remains"

        # Never reload while GLPI still reports unsaved changes: doing so could
        # destroy diagnostic state and turn a failed save into a false positive.
        if delta_cleared and expected_edge is not None and reload_workspace is not None:
            try:
                reload_workspace()
                self.builder.wait_until_ready(timeout=timeout)
                reloaded_edge_present = self.builder.has_edge(expected_edge)
                persisted = reloaded_edge_present
                verification = "verified_after_reload" if persisted else "missing_after_reload"
            except PlaywrightTimeoutError:
                verification = "reload_verification_timeout"

        return SaveResult(
            attempted=True,
            persisted=persisted,
            dry_run=False,
            delta_before=delta_before,
            delta_after=delta_after,
            requests=requests,
            delta_cleared=delta_cleared,
            verification=verification,
            reloaded_edge_present=reloaded_edge_present,
            successful_write_responses=len(successful_writes),
        )

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
