# SPDX-License-Identifier: AGPL-3.0-only
from __future__ import annotations

import re
from typing import Any
from urllib.parse import urlparse

JsonDict = dict[str, Any]

INTERACTIVE_ROLES = {
    "button",
    "checkbox",
    "combobox",
    "link",
    "menuitem",
    "menuitemcheckbox",
    "menuitemradio",
    "option",
    "radio",
    "searchbox",
    "slider",
    "spinbutton",
    "switch",
    "tab",
    "textbox",
}
ROOT_ROLES = {"banner", "contentinfo", "main", "navigation", "region", "search"}
CONTAINER_ROLES = {
    "article",
    "definition",
    "dialog",
    "figure",
    "form",
    "generic",
    "group",
    "list",
    "listitem",
    "paragraph",
    "row",
    "section",
    "table",
    "tabpanel",
    "term",
}
TEXT_ROLES = {
    "blockquote",
    "code",
    "definition",
    "heading",
    "img",
    "image",
    "note",
    "paragraph",
    "status",
    "strong",
    "term",
    "text",
    "time",
}
IGNORED_ROLES = {"none", "presentation"}
TAG_ROLE_MAP = {
    "a": "link",
    "article": "article",
    "aside": "complementary",
    "button": "button",
    "footer": "contentinfo",
    "form": "form",
    "h1": "heading",
    "h2": "heading",
    "h3": "heading",
    "h4": "heading",
    "h5": "heading",
    "h6": "heading",
    "header": "banner",
    "img": "img",
    "input": "textbox",
    "li": "listitem",
    "main": "main",
    "nav": "navigation",
    "ol": "list",
    "p": "paragraph",
    "section": "region",
    "select": "combobox",
    "textarea": "textbox",
    "time": "time",
    "ul": "list",
}


class WebDomCollectionError(RuntimeError):
    """Raised when the Playwright web collector cannot produce a payload."""


def derive_app_id_from_url(url: str) -> str:
    parsed = _normalize_url(url)
    hostname = (parsed.hostname or "unknown-host").lower()
    safe_host = re.sub(r"[^a-z0-9.]+", "-", hostname).strip(".-")
    return f"web.{safe_host or 'unknown-host'}"


def collect_from_web_dom(
    url: str, *, timeout_ms: int = 10_000, browser_name: str = "chromium"
) -> JsonDict:
    sync_playwright, playwright_error, playwright_timeout = _load_playwright()
    parsed = _normalize_url(url)

    try:
        with sync_playwright() as playwright:
            browser_type = getattr(playwright, browser_name, None)
            if browser_type is None:
                raise WebDomCollectionError(
                    f"Unsupported browser '{browser_name}'. Expected chromium, firefox, or webkit."
                )

            browser = browser_type.launch()
            context = browser.new_context()
            page = context.new_page()
            try:
                page.goto(
                    parsed.geturl(), wait_until="domcontentloaded", timeout=timeout_ms
                )
                try:
                    page.wait_for_load_state(
                        "networkidle", timeout=min(timeout_ms, 3_000)
                    )
                except playwright_timeout:
                    # Network idle is best-effort only. Dynamic public pages often keep
                    # analytics connections open after the meaningful tree is ready.
                    pass

                title = _safe_page_title(page, parsed.hostname or "Untitled page")
                snapshot = page.locator("body").aria_snapshot(timeout=timeout_ms)
                if snapshot and str(snapshot).strip():
                    return _build_payload_from_aria_snapshot(
                        str(snapshot), parsed.geturl(), title
                    )
                return _build_payload_from_dom_snapshot(page, parsed.geturl(), title)
            finally:
                context.close()
                browser.close()
    except ImportError as exc:  # pragma: no cover - defensive import edge.
        raise WebDomCollectionError(str(exc)) from exc
    except playwright_error as exc:
        raise WebDomCollectionError(
            f"Playwright collection failed for {parsed.geturl()}: {exc}"
        ) from exc


def _load_playwright():
    try:
        from playwright.sync_api import Error, TimeoutError, sync_playwright
    except ImportError as exc:  # pragma: no cover - covered via raised message.
        raise WebDomCollectionError(
            "Playwright is required for --url analysis. Run `uv sync --dev` "
            "and then `.venv/bin/playwright install chromium`."
        ) from exc
    return sync_playwright, Error, TimeoutError


def _load_yaml():
    try:
        import yaml
    except ImportError as exc:  # pragma: no cover - covered via raised message.
        raise WebDomCollectionError(
            "PyYAML is required for --url analysis. Run `uv sync --dev` to install project dependencies."
        ) from exc
    return yaml


def _normalize_url(url: str):
    parsed = urlparse(url.strip())
    if parsed.scheme not in {"http", "https"}:
        raise WebDomCollectionError(
            "Web DOM collection only supports http and https URLs."
        )
    if not parsed.netloc:
        raise WebDomCollectionError("Web DOM collection requires an absolute URL.")
    return parsed


def _safe_page_title(page: Any, fallback: str) -> str:
    try:
        title = str(page.title() or "").strip()
    except Exception:
        title = ""
    return title or fallback


def _build_payload_from_accessibility_tree(
    snapshot: JsonDict, url: str, title: str
) -> JsonDict:
    children = _normalize_accessibility_children(snapshot.get("children", []))
    return _build_payload_from_normalized_tree(children, url=url, title=title)


def _build_payload_from_aria_snapshot(snapshot: str, url: str, title: str) -> JsonDict:
    yaml = _load_yaml()
    parsed = yaml.safe_load(snapshot) or []
    children = _normalize_aria_children(parsed)
    return _build_payload_from_normalized_tree(children, url=url, title=title)


def _normalize_accessibility_children(children: list[JsonDict]) -> list[JsonDict]:
    normalized: list[JsonDict] = []
    for child in children:
        normalized.extend(_normalize_accessibility_node(child))
    return normalized


def _normalize_aria_children(children: list[Any]) -> list[JsonDict]:
    normalized: list[JsonDict] = []
    for child in children:
        normalized.extend(_normalize_aria_node(child))
    return normalized


def _normalize_aria_node(node: Any) -> list[JsonDict]:
    if isinstance(node, str):
        text = str(node).strip()
        if not text:
            return []
        role, label = _parse_aria_key(text)
        if role in IGNORED_ROLES:
            return []
        return [
            {
                "role": role,
                "label": label or text,
                "children": [],
                "accessibility_identifier": None,
            }
        ]

    if not isinstance(node, dict):
        return []

    normalized: list[JsonDict] = []
    for raw_key, raw_value in node.items():
        role, label = _parse_aria_key(str(raw_key))
        children = []

        if isinstance(raw_value, list):
            children = _normalize_aria_children(raw_value)
        elif raw_value is not None:
            if role in {"paragraph", "text"} and not label:
                label = str(raw_value).strip()
            elif not label and isinstance(raw_value, str):
                label = str(raw_value).strip()

        if role in IGNORED_ROLES:
            normalized.extend(children)
            continue

        if not _should_include_node(role, label, children):
            normalized.extend(children)
            continue

        normalized.append(
            {
                "role": role,
                "label": label,
                "children": children,
                "accessibility_identifier": None,
            }
        )

    return normalized


def _normalize_accessibility_node(node: JsonDict) -> list[JsonDict]:
    role = _normalize_role(node.get("role"))
    label = _best_label(node)
    children = _normalize_accessibility_children(node.get("children", []))

    if role in IGNORED_ROLES:
        return children

    if not _should_include_node(role, label, children):
        return children

    return [
        {
            "role": role,
            "label": label,
            "children": children,
            "accessibility_identifier": None,
        }
    ]


def _build_payload_from_dom_snapshot(page: Any, url: str, title: str) -> JsonDict:
    raw_nodes = page.evaluate("""
        () => {
          const interactiveTags = new Set(["a", "button", "input", "select", "textarea"]);
          const semanticTags = new Set([
            "article", "aside", "button", "figure", "footer", "form", "h1", "h2",
            "h3", "h4", "h5", "h6", "header", "img", "input", "li", "main", "nav",
            "ol", "p", "section", "select", "textarea", "time", "ul"
          ]);

          const isVisible = (element) => {
            const style = window.getComputedStyle(element);
            const rect = element.getBoundingClientRect();
            return style.display !== "none" && style.visibility !== "hidden" && rect.width >= 0 && rect.height >= 0;
          };

          const roleFor = (element) => {
            const explicitRole = element.getAttribute("role");
            if (explicitRole) return explicitRole.trim().toLowerCase();
            const tag = element.tagName.toLowerCase();
            if (/^h[1-6]$/.test(tag)) return "heading";
            if (tag === "a") return "link";
            if (tag === "button") return "button";
            if (tag === "input") {
              const type = (element.getAttribute("type") || "text").toLowerCase();
              if (type === "checkbox") return "checkbox";
              if (type === "radio") return "radio";
              if (type === "search") return "searchbox";
              return "textbox";
            }
            if (tag === "select") return "combobox";
            if (tag === "textarea") return "textbox";
            if (tag === "nav") return "navigation";
            if (tag === "main") return "main";
            if (tag === "header") return "banner";
            if (tag === "footer") return "contentinfo";
            if (tag === "section") return "region";
            if (tag === "article") return "article";
            if (tag === "ul" || tag === "ol") return "list";
            if (tag === "li") return "listitem";
            if (tag === "img") return "img";
            if (tag === "form") return "form";
            if (tag === "p") return "paragraph";
            if (tag === "time") return "time";
            if (tag === "figure") return "figure";
            return "generic";
          };

          const labelFor = (element) => {
            return (
              element.getAttribute("aria-label") ||
              element.getAttribute("title") ||
              element.innerText ||
              element.textContent ||
              ""
            ).replace(/\\s+/g, " ").trim();
          };

          const nodeFor = (element) => {
            if (!isVisible(element)) return null;
            const tag = element.tagName.toLowerCase();
            const role = roleFor(element);
            const label = labelFor(element);
            const children = [];
            for (const child of element.children) {
              const childNode = nodeFor(child);
              if (childNode) {
                children.push(childNode);
              }
            }

            const keep = semanticTags.has(tag) || interactiveTags.has(tag) || label || children.length;
            if (!keep) return null;

            return {
              role,
              label,
              accessibility_identifier:
                element.getAttribute("data-testid") ||
                element.getAttribute("id") ||
                element.getAttribute("name") ||
                null,
              children,
            };
          };

          const roots = [];
          for (const child of document.body.children) {
            const node = nodeFor(child);
            if (node) roots.push(node);
          }
          return roots;
        }
        """)
    return _build_payload_from_normalized_tree(raw_nodes or [], url=url, title=title)


def _build_payload_from_normalized_tree(
    children: list[JsonDict], *, url: str, title: str
) -> JsonDict:
    parsed = urlparse(url)
    screen_slug = _slugify(f"{parsed.hostname or 'page'}-{parsed.path or 'root'}")
    screen_id = screen_slug or "web-screen"
    screen_name = title.strip() or (parsed.hostname or "Web page")
    root_id = "screen-root"
    root_children = []
    for index, child in enumerate(children, start=1):
        root_children.extend(
            _materialize_elements(
                node=child,
                parent_id=root_id,
                depth=1,
                path=(index,),
            )
        )

    elements = [
        {
            "element_id": root_id,
            "parent_id": None,
            "element_type": "container",
            "role": "screen",
            "slab_layer": "01. OS Site (The Land)",
            "label": "",
            "accessibility_identifier": None,
            "interactive": False,
            "visible": True,
            "bounds": None,
            "hierarchy_depth": 0,
            "child_count": sum(
                1 for node in root_children if node["parent_id"] == root_id
            ),
            "text_present": False,
            "traits": ["collector-root"],
            "source": f"collector:playwright:web:{urlparse(url).hostname or 'unknown'}",
        }
    ]
    elements.extend(root_children)

    return {
        "project_name": screen_name,
        "platform": "web",
        "screens": [
            {
                "screen_id": screen_id,
                "screen_name": screen_name,
                "elements": elements,
            }
        ],
    }


def _materialize_elements(
    *, node: JsonDict, parent_id: str, depth: int, path: tuple[int, ...]
) -> list[JsonDict]:
    role = _normalize_role(node.get("role"))
    label = str(node.get("label") or "").strip()
    element_id = _element_id(role, path)
    children = node.get("children", [])

    materialized_children = []
    for index, child in enumerate(children, start=1):
        materialized_children.extend(
            _materialize_elements(
                node=child,
                parent_id=element_id,
                depth=depth + 1,
                path=(*path, index),
            )
        )

    current = {
        "element_id": element_id,
        "parent_id": parent_id,
        "element_type": _element_type_for_role(role),
        "role": role or "generic",
        "slab_layer": _slab_layer_for_role(role),
        "label": label,
        "accessibility_identifier": _optional_str(node.get("accessibility_identifier")),
        "interactive": _is_interactive_role(role),
        "visible": True,
        "bounds": None,
        "hierarchy_depth": depth,
        "child_count": sum(
            1 for child in materialized_children if child["parent_id"] == element_id
        ),
        "text_present": bool(label),
        "traits": _traits_for_node(role=role, label=label, has_children=bool(children)),
        "source": "collector:playwright:web-dom",
    }
    return [current, *materialized_children]


def _should_include_node(role: str, label: str, children: list[JsonDict]) -> bool:
    if role in ROOT_ROLES or role in CONTAINER_ROLES or role in TEXT_ROLES:
        return True
    if _is_interactive_role(role):
        return True
    if label:
        return True
    return bool(children)


def _normalize_role(value: Any) -> str:
    role = str(value or "").strip().lower()
    return role or "generic"


def _parse_aria_key(value: str) -> tuple[str, str]:
    stripped = value.strip()
    match = re.match(
        r"^(?P<role>[^\[\"]+?)(?:\s+\"(?P<label>.*?)\")?(?:\s+\[.*\])?$", stripped
    )
    if match is None:
        return _normalize_role(stripped), ""
    role = _normalize_role(match.group("role"))
    label = str(match.group("label") or "").strip()
    return role, label


def _best_label(node: JsonDict) -> str:
    for key in ("name", "value", "valuetext", "description"):
        value = node.get(key)
        if value is None:
            continue
        text = str(value).strip()
        if text:
            return re.sub(r"\s+", " ", text)
    return ""


def _element_id(role: str, path: tuple[int, ...]) -> str:
    role_slug = _slugify(role) or "node"
    return f"{role_slug}-{'-'.join(str(part) for part in path)}"


def _element_type_for_role(role: str) -> str:
    if role in {"banner", "contentinfo", "main", "navigation", "search"}:
        return "navigation"
    if role in {"heading", "paragraph", "note", "status", "term", "time", "text"}:
        return "text"
    if role in {"img", "image", "figure"}:
        return "image"
    if role in {"button", "checkbox", "radio", "switch"}:
        return "button"
    if role in {"textbox", "searchbox", "combobox", "spinbutton"}:
        return "field"
    if role in {"link", "menuitem", "menuitemcheckbox", "menuitemradio", "tab"}:
        return "link"
    if role in {
        "article",
        "definition",
        "dialog",
        "form",
        "group",
        "list",
        "listitem",
        "row",
        "table",
        "tabpanel",
    }:
        return "container"
    return "container"


def _slab_layer_for_role(role: str) -> str:
    if role in {"banner", "contentinfo", "main", "navigation", "region", "search"}:
        return "02. Root (The Slab)"
    if _is_interactive_role(role):
        return "04. Links/Events (Wires & Plumbing)"
    if role in TEXT_ROLES:
        return "05. Assets (The Decor)"
    return "03. Containers (The Frame)"


def _is_interactive_role(role: str) -> bool:
    return role in INTERACTIVE_ROLES


def _traits_for_node(*, role: str, label: str, has_children: bool) -> list[str]:
    traits: list[str] = []
    if _is_interactive_role(role):
        traits.append("interactive")
    if has_children:
        traits.append("group")
    if label:
        traits.append("text")
    if role in ROOT_ROLES:
        traits.append("landmark")
    return traits or ["static"]


def _optional_str(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _slugify(value: str) -> str:
    lowered = value.lower()
    normalized = re.sub(r"[^a-z0-9]+", "-", lowered)
    return normalized.strip("-")
