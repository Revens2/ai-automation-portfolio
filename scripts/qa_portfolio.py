"""Check bilingual static portfolio paths, semantics, source privacy and links."""
from __future__ import annotations

import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlsplit, unquote

ROOT = Path(__file__).resolve().parents[1]
CASES = ("orchestration", "sandbox", "rag", "watchy", "audits")
PAGES = (
    ("index.html", "en", "fr/index.html"),
    ("fr/index.html", "fr", "index.html"),
    ("projects.html", "en", "fr/projets.html"),
    ("fr/projets.html", "fr", "projects.html"),
    *tuple((f"projects/{name}.html", "en", f"fr/projets/{name}.html") for name in CASES),
    *tuple((f"fr/projets/{name}.html", "fr", f"projects/{name}.html") for name in CASES),
)
PRIVATE_REPOS = {
    "sandbox-mcp", "agent-memory-private", "rag-v2", "Watchy",
    "brave-devtools-mcp", "wisperfiou", "activitywatch-stack", "ARION"
}
ROOT_URL = "https://revens2.github.io/ai-automation-portfolio/"
ERRORS: list[str] = []


class PageParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.attrs: list[tuple[str, dict[str, str]]] = []
        self.ids: list[str] = []
        self.lang = ""
        self.h1 = 0

    def handle_starttag(self, tag, attrs):
        vals = dict(attrs)
        self.attrs.append((tag, vals))
        if tag == "html":
            self.lang = vals.get("lang", "")
        if tag == "h1":
            self.h1 += 1
        if vals.get("id"):
            self.ids.append(vals["id"])


def fail(path, message):
    ERRORS.append(f"{path}: {message}")


for rel, language, parallel in PAGES:
    path = ROOT / rel
    if not path.is_file():
        fail(rel, "missing page")
        continue
    html = path.read_text(encoding="utf-8")
    parsed = PageParser()
    parsed.feed(html)
    if parsed.lang != language:
        fail(rel, f"expected html lang {language}, got {parsed.lang}")
    if parsed.h1 != 1:
        fail(rel, f"expected one H1, got {parsed.h1}")
    if len(set(parsed.ids)) != len(parsed.ids):
        fail(rel, "duplicate id attributes")
    if re.search(r"(ghp_[0-9A-Za-z]{15}|sk-[A-Za-z0-9]{25}|BEGIN PRIVATE KEY|10\.200\.\d+\.\d+)", html):
        fail(rel, "sensitive-looking string")
    link_elements = [attrs for tag, attrs in parsed.attrs if tag == "link"]
    canonicals = [x.get("href") for x in link_elements if x.get("rel") == "canonical"]
    expected_url = (ROOT_URL if rel == "index.html" else
                    ROOT_URL + "fr/" if rel == "fr/index.html" else
                    urljoin(ROOT_URL, rel))
    if canonicals != [expected_url]:
        fail(rel, f"canonical mismatch: {canonicals!r} expected {expected_url}")
    alt_langs = {x.get("hreflang"): x.get("href") for x in link_elements if x.get("rel") == "alternate"}
    parallel_url = (ROOT_URL if parallel == "index.html" else
                    ROOT_URL + "fr/" if parallel == "fr/index.html" else
                    urljoin(ROOT_URL, parallel))
    if alt_langs.get(language) != expected_url:
        fail(rel, "self hreflang missing or incorrect")
    if alt_langs.get("fr" if language == "en" else "en") != parallel_url:
        fail(rel, "reciprocal-language hreflang missing or incorrect")

    for tag, attrs in parsed.attrs:
        if tag == "img":
            if not attrs.get("alt"):
                fail(rel, f"image lacks nonempty alt: {attrs.get('src')}")
            if not attrs.get("loading") == "lazy":
                fail(rel, f"image not lazy loaded: {attrs.get('src')}")
        for property_ in ("href", "src"):
            value = attrs.get(property_)
            if not value:
                continue
            if property_ == "href" and value.startswith("#"):
                if value[1:] not in parsed.ids:
                    fail(rel, f"missing anchor {value}")
                continue
            absolute = urljoin(expected_url, value)
            destination = urlsplit(absolute)
            if destination.netloc == "github.com" and destination.path.startswith("/Revens2/"):
                repo_name = destination.path.split("/")[2]
                if repo_name in PRIVATE_REPOS:
                    fail(rel, f"private repository publicly linked: {repo_name}")
            if destination.netloc != "revens2.github.io":
                continue
            prefix = "/ai-automation-portfolio/"
            if not destination.path.startswith(prefix):
                fail(rel, f"outside portfolio link: {value}")
                continue
            localpath = unquote(destination.path[len(prefix):])
            if not localpath or localpath.endswith("/"):
                localpath += "index.html"
            if not (ROOT / localpath).is_file():
                fail(rel, f"broken local resource: {value} -> {localpath}")
    css_links = [attrs["href"] for tag, attrs in parsed.attrs if tag == "link" and attrs.get("rel") == "stylesheet"]
    if len(css_links) != 1 or "?v=20261021dark" not in css_links[0]:
        fail(rel, f"unexpected versioned stylesheet: {css_links}")

if ERRORS:
    print(f"FAIL: {len(ERRORS)} issues")
    for err in ERRORS:
        print(" -", err)
    sys.exit(1)
print(f"PASS: {len(PAGES)} pages, headings, canonical/hreflang, anchors, links, assets, privacy and CSS versioning.")