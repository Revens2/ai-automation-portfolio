"""Browser/viewport QA with screenshots preserved as workflow artifacts."""
from __future__ import annotations

import functools
import json
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urljoin

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "qa-screenshots"
OUT.mkdir(exist_ok=True)
PAGES = [
    "index.html", "fr/index.html", "projects.html", "fr/projets.html",
    "architecture.html", "fr/architecture.html",
    *[f"projects/{slug}.html" for slug in ("orchestration", "sandbox", "rag", "watchy", "audits")],
    *[f"fr/projets/{slug}.html" for slug in ("orchestration", "sandbox", "rag", "watchy", "audits")],
]
FAILED = []
SIZES = [(360, 800), (390, 844), (1440, 900)]
SCREENSHOTS = {"index.html", "fr/index.html", "projects.html", "fr/projets.html", "fr/projets/rag.html", "fr/projets/watchy.html", "fr/architecture.html", "architecture.html"}


def handler(*args, **kwargs):
    return SimpleHTTPRequestHandler(*args, directory=str(ROOT), **kwargs)


httpd = ThreadingHTTPServer(("127.0.0.1", 0), handler)
base = f"http://127.0.0.1:{httpd.server_address[1]}/"
threading.Thread(target=httpd.serve_forever, daemon=True).start()

with sync_playwright() as p:
    # Hosted runners ship Chrome; avoid unreliable CDN downloads when available.
    import shutil
    if shutil.which("google-chrome") or shutil.which("google-chrome-stable"):
        browser = p.chromium.launch(channel="chrome", headless=True, args=["--no-sandbox"])
    else:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
    try:
        for width, height in SIZES:
            context = browser.new_context(viewport={"width": width, "height": height}, device_scale_factor=1)
            for rel in PAGES:
                page = context.new_page()
                page_errors = []
                page.on("pageerror", lambda err: page_errors.append(str(err)))
                response = page.goto(urljoin(base, rel), wait_until="load", timeout=20000)
                if not response or response.status != 200:
                    FAILED.append(f"{rel} @{width}: missing HTTP 200")
                    page.close()
                    continue
                values = page.evaluate("""() => ({
                  bg: getComputedStyle(document.body).backgroundColor,
                  overflow: document.documentElement.scrollWidth - innerWidth,
                  h1: document.querySelectorAll('h1').length,
                  lang: document.documentElement.lang
                })""")
                if values["bg"] != "rgb(14, 15, 17)":
                    FAILED.append(f"{rel} @{width}: dark theme not applied ({values['bg']})")
                if values["overflow"] > 2:
                    FAILED.append(f"{rel} @{width}: horizontal overflow {values['overflow']}px")
                if values["h1"] != 1:
                    FAILED.append(f"{rel} @{width}: H1 count {values['h1']}")
                if values["lang"] != ("fr" if rel.startswith("fr/") else "en"):
                    FAILED.append(f"{rel} @{width}: unexpected language")
                # Force lazy images to fetch before asserting integrity.
                images = page.evaluate("""async () => {
                  return await Promise.all([...document.images].map(async img => {
                    img.loading = 'eager';
                    try {await img.decode();return {src:img.getAttribute('src'),ok:img.naturalWidth>0};}
                    catch (e) {return {src:img.getAttribute('src'),ok:false};}
                  }));
                }""")
                for img in images:
                    if not img["ok"]:
                        FAILED.append(f"{rel} @{width}: broken image {img['src']}")
                if page_errors:
                    FAILED.append(f"{rel} @{width}: JS error {page_errors[0]}")
                if "projets.html" in rel or rel == "projects.html":
                    buttons = page.locator(".filter-btn[data-filter='rag']")
                    if buttons.count() == 1:
                        total = page.locator("[data-domain]:visible").count()
                        buttons.click()
                        filtered = page.locator("[data-domain]:visible").count()
                        if filtered <= 0 or filtered >= total:
                            FAILED.append(f"{rel} @{width}: project filter did not narrow results ({filtered}/{total})")
                        page.locator(".filter-btn[data-filter='all']").click()
                    else:
                        FAILED.append(f"{rel} @{width}: project filter missing")
                if rel in SCREENSHOTS and width in (360, 1440):
                    page.evaluate("window.scrollTo(0, 0)")
                    page.wait_for_timeout(80)
                    page.screenshot(path=str(OUT / (rel.replace("/", "_").replace(".html", "") + f"_{width}.png")), full_page=True)
                print(json.dumps({"page": rel, "viewport": width, "theme": values["bg"], "overflow_px": values["overflow"], "images": len(images)}, ensure_ascii=False))
                page.close()
            context.close()
    finally:
        browser.close()
        httpd.shutdown()

if FAILED:
    print("FAIL:")
    print("\n".join(" - " + v for v in FAILED))
    raise SystemExit(1)
print(f"PASS: {len(PAGES)} pages x {len(SIZES)} viewports, dark CSS, images, overflow, JS, filters.")