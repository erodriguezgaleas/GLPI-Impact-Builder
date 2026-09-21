"""Runtime inspection helpers for reverse engineering GLPI Impact safely."""

from __future__ import annotations
from typing import Any
from playwright.sync_api import Page


class ImpactInspector:
    """Inspect the live GLPIImpact object without mutating the workspace."""

    EDGE_TERMS = ("edge", "edition", "history", "action", "save", "delta")

    def __init__(self, page: Page):
        self.page = page

    def describe(self) -> dict[str, Any]:
        self.page.wait_for_function("() => Boolean(window.GLPIImpact && GLPIImpact.cy)")
        return self.page.evaluate("""() => {
            const methods = [];
            const properties = {};
            const seen = new Set();
            let object = GLPIImpact;
            while (object && object !== Object.prototype) {
                for (const name of Object.getOwnPropertyNames(object)) {
                    if (seen.has(name) || name === 'constructor') continue;
                    seen.add(name);
                    let value;
                    try { value = GLPIImpact[name]; } catch (_) { continue; }
                    if (typeof value === 'function') methods.push({name, arity: value.length});
                    else if (value === null || ['string', 'number', 'boolean'].includes(typeof value))
                        properties[name] = value;
                }
                object = Object.getPrototypeOf(object);
            }
            return {
                methods: methods.sort((a, b) => a.name.localeCompare(b.name)),
                properties,
                node_count: GLPIImpact.cy.nodes().length,
                edge_count: GLPIImpact.cy.edges().length
            };
        }""")

    def method_source(self, name: str) -> str:
        self.page.wait_for_function("() => Boolean(window.GLPIImpact)")
        source = self.page.evaluate("""name => {
            const fn = GLPIImpact[name];
            return typeof fn === 'function' ? Function.prototype.toString.call(fn) : null;
        }""", name)
        if source is None:
            raise AttributeError(f"GLPIImpact method not found: {name}")
        return source

    def method_sources(self, names: list[str]) -> dict[str, str]:
        result: dict[str, str] = {}
        for name in names:
            try:
                result[name] = self.method_source(name)
            except AttributeError:
                continue
        return result

    def related_methods(self, terms: tuple[str, ...] | None = None) -> list[dict[str, Any]]:
        """Find runtime methods whose name or source references edge workflow terms."""
        terms = terms or self.EDGE_TERMS
        report = self.describe()
        result: list[dict[str, Any]] = []
        for method in report["methods"]:
            name = method["name"]
            source = self.method_source(name)
            haystack = f"{name}\n{source}".lower()
            matches = sorted({term for term in terms if term.lower() in haystack})
            if matches:
                result.append({
                    "name": name,
                    "arity": method["arity"],
                    "matches": matches,
                    "source": source,
                })
        return result

    def edge_runtime_report(self) -> dict[str, Any]:
        names = [
            "computeDelta", "computeEdgeDelta", "computeItemsDelta", "computeContext",
            "getCurrentState", "addNode", "setEditionMode", "enterEditionMode",
        ]
        return {
            "runtime": self.describe(),
            "method_sources": self.method_sources(names),
            "related_methods": self.related_methods(),
            "save_candidates": self.save_candidates(),
        }

    def save_candidates(self) -> list[dict[str, Any]]:
        return self.page.evaluate("""() => [...document.querySelectorAll('button, a, input[type=submit]')]
            .map((element, index) => ({
                index, tag: element.tagName.toLowerCase(), id: element.id || null,
                name: element.getAttribute('name'),
                text: (element.innerText || element.value || '').trim(),
                title: element.getAttribute('title'),
                aria_label: element.getAttribute('aria-label'),
                class_name: element.className || null
            }))
            .filter(item => /save|apply|update|guardar|aplicar|actualizar/i.test(
                [item.text, item.title, item.aria_label, item.name, item.id]
                    .filter(Boolean).join(' ')
            ))""")
