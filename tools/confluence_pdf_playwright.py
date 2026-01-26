#!/usr/bin/env python3
"""
Confluence PDF exporter via Playwright (SSO-friendly).

How it works:
- Uses a persistent Chromium profile so you can log in once via your normal SSO flow.
- Loads a list of Confluence page URLs and saves each as a PDF (print-to-PDF).
- Attempts to fully render pages (wait for network idle and scroll) before printing.

Usage:
  # First time: open an interactive browser to log in via SSO, then export
  python tools/confluence_pdf_playwright.py --urls-file urls.txt --out-dir exports/pdf --profile-dir ~/.confluence-exporter --interactive-login

  # Subsequent runs (session cookies retained in profile):
  python tools/confluence_pdf_playwright.py --urls-file urls.txt --out-dir exports/pdf --profile-dir ~/.confluence-exporter

Notes:
- Provide full page URLs (e.g., https://wiki.company.com/x/AbCdE or /spaces/SPACEKEY/pages/<id>). One per line.
- For large pages with lazy loading, printing after a full scroll improves completeness.
- Page headers/footers are disabled by default; adjust as needed.
"""
import argparse
import asyncio
from pathlib import Path
from urllib.parse import urljoin, urlparse, parse_qs, urlunparse

from playwright.async_api import async_playwright


async def ensure_logged_in(context, first_url: str, interactive: bool):
    page = await context.new_page()
    await page.goto(first_url, wait_until="load")
    if interactive:
        print("A browser window opened. Complete SSO login if prompted, then press Enter here to continue...")
        # Run blocking input() without blocking the event loop
        import asyncio as _asyncio
        await _asyncio.to_thread(input)
    # Wait a bit in case of redirects after login
    await page.wait_for_load_state("networkidle")
    await page.close()


async def fully_render(page):
    # Wait for network to be idle, then progressively scroll to bottom to trigger lazy loads.
    await page.wait_for_load_state("networkidle")

    # Progressive scroll
    last_height = 0
    for _ in range(30):
        height = await page.evaluate("document.body.scrollHeight")
        if height <= last_height:
            break
        last_height = height
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await page.wait_for_timeout(400)
        await page.wait_for_load_state("networkidle")


async def export_pdf(context, url: str, out_dir: Path):
    page = await context.new_page()
    try:
        await page.goto(url, wait_until="load")
        await fully_render(page)
        # Remove sticky elements that can overlay content in print
        try:
            await page.add_style_tag(content="""
                * { print-color-adjust: exact; -webkit-print-color-adjust: exact; }
                header, nav, .aui-header, .css-1hnx2m8, .css-1o72pil, .css-1l2qy5m, .ak-navigation, .ak-editor-toolbar { display: none !important; }
            """)
        except Exception:
            pass
        # Derive filename from title
        title = await page.title()
        safe = "".join(c if c.isalnum() or c in ("-", "_") else "-" for c in title).strip("-") or "page"
        out_path = out_dir / f"{safe}.pdf"
        i = 2
        while out_path.exists():
            out_path = out_dir / f"{safe}-{i}.pdf"
            i += 1
        await page.pdf(path=str(out_path), format="A4", print_background=True, margin={"top": "10mm", "right": "10mm", "bottom": "10mm", "left": "10mm"})
        print(f"Saved {url} -> {out_path}")
    finally:
        await page.close()


def _is_confluence_page(url: str, origin: str, allow_viewpage: bool = False) -> bool:
    # Keep same-origin pages that look like Confluence content
    try:
        u = urlparse(url)
    except Exception:
        return False
    if not u.scheme or not u.netloc:
        return False
    if f"{u.scheme}://{u.netloc}" != origin:
        return False
    # Exclude non-content and admin/actions
    excluded_paths = (
        "/pages/createpage.action",
        "/pages/editpage.action",
        "/pages/removepage.action",
        "/pages/viewinfo.action",
        "/pages/viewpreviousversions.action",
        "/pages/viewpageattachments.action",
        "/pages/worddav/uploadimport.action",
        "/spaces/viewspacesummary.action",
        "/spaces/spacepermissions.action",
        "/spaces/choosetheme.action",
        "/spaces/listentitylinks.action",
        "/spaces/viewtrackerreport.action",
        "/pages/reorderpages.action",
        "/pages/copypage.action",
        "/spaces/flyingpdf/pdfpageexport.action",
        "/pages/viewrecentblogposts.action",
        "/display/",  # we allow display pages, but will filter via allowlist below
    )
    if any(u.path.startswith(p) for p in excluded_paths if p != "/display/"):
        return False
    # Allow content-like paths
    if allow_viewpage and u.path.startswith("/pages/viewpage.action"):
        return True
    return u.path.startswith("/display/")


def _canonicalize(url: str) -> str:
    # Drop fragments and unnecessary query params; keep pageId for viewpage.action
    u = urlparse(url)
    query = parse_qs(u.query)
    kept = {}
    if u.path.startswith("/pages/viewpage.action") and "pageId" in query:
        kept["pageId"] = query["pageId"]
    new_query = "&".join(f"{k}={v[0]}" for k, v in kept.items()) if kept else ""
    return urlunparse((u.scheme, u.netloc, u.path, "", new_query, ""))


async def _get_page_id(page) -> str | None:
    # Try to extract pageId from meta tag used by Confluence
    pid = await page.eval_on_selector("meta[name='ajs-page-id']", "el => el && el.getAttribute('content')")
    return pid


async def _collect_links_rest(page, origin: str, page_id: str, depth: int, max_pages: int) -> list[str]:
    # Traverse children via Confluence REST using current authenticated session (SSO cookies apply)
    collected: list[str] = []

    async def _walk(pid: str, d: int):
        nonlocal collected
        if max_pages > 0 and len(collected) >= max_pages:
            return
        # Construct REST URL
        url = f"{origin}/rest/api/content/{pid}/child/page?limit=50"
        data = await page.evaluate("async (url) => { const r = await fetch(url, { credentials: 'same-origin' }); if (!r.ok) throw new Error('REST ' + r.status); return r.json(); }", url)
        results = data.get("results", []) if isinstance(data, dict) else []
        for itm in results:
            child_id = itm.get("id")
            if not child_id:
                continue
            link = f"{origin}/pages/viewpage.action?pageId={child_id}"
            if link not in collected:
                collected.append(link)
            if d + 1 <= depth:
                await _walk(child_id, d + 1)

    await _walk(page_id, 0)
    # Ensure the parent is included first
    parent_link = f"{origin}/pages/viewpage.action?pageId={page_id}"
    collected = [parent_link] + [u for u in collected if u != parent_link]
    return collected


async def _collect_links_rest_ancestor(page, origin: str, page_id: str, max_pages: int) -> list[str]:
    # Use CQL search to list all descendants (ancestor=pageId)
    collected: list[str] = []
    start = 0
    limit = 50
    while True:
        if max_pages > 0 and len(collected) >= max_pages:
            break
        url = f"{origin}/rest/api/content/search?cql=ancestor={page_id}+and+type=page&limit={limit}&start={start}"
        data = await page.evaluate("async (url) => { const r = await fetch(url, { credentials: 'same-origin' }); if (!r.ok) throw new Error('REST ' + r.status); return r.json(); }", url)
        results = data.get("results", []) if isinstance(data, dict) else []
        if not results:
            break
        for itm in results:
            cid = itm.get("id")
            if not cid:
                continue
            link = f"{origin}/pages/viewpage.action?pageId={cid}"
            if link not in collected:
                collected.append(link)
                if max_pages > 0 and len(collected) >= max_pages:
                    break
        if len(results) < limit:
            break
        start += limit
    # Ensure parent first
    parent_link = f"{origin}/pages/viewpage.action?pageId={page_id}"
    collected = [parent_link] + [u for u in collected if u != parent_link]
    return collected


async def collect_links_under_parent(context, parent_url: str, depth: int, max_pages: int, allow_viewpage: bool, mode: str = "rest") -> list[str]:
    origin = f"{urlparse(parent_url).scheme}://{urlparse(parent_url).netloc}"
    parent_parsed = urlparse(parent_url)
    # Restrict to same user space path prefix if using /display/~user
    user_space_prefix = None
    parent_prefix = None
    if parent_parsed.path.startswith("/display/"):
        parts = parent_parsed.path.split("/")
        if len(parts) >= 3:
            # e.g., /display/~k0d03gd/...
            user_space_prefix = "/".join(parts[:3]) + "/"
        # e.g., /display/~k0d03gd/ParentPage
        parent_prefix = parent_parsed.path.rstrip("/") + "/"
    # First open the parent page
    parent_page = await context.new_page()
    await parent_page.goto(parent_url, wait_until="load")
    await fully_render(parent_page)
    # If REST mode, use REST traversal which captures true children irrespective of sidebar rendering
    if mode in ("rest", "rest-ancestor"):
        pid = await _get_page_id(parent_page)
        if not pid:
            await parent_page.close()
            return [parent_url]
        if mode == "rest-ancestor":
            urls = await _collect_links_rest_ancestor(parent_page, origin, pid, max_pages=max_pages)
        else:
            urls = await _collect_links_rest(parent_page, origin, pid, depth=depth, max_pages=max_pages)
        await parent_page.close()
        return urls
    # DOM mode fallback (less reliable)
    to_visit = [(parent_url, 0)]
    seen = set()
    collected: list[str] = []

    while to_visit:
        url, d = to_visit.pop(0)
        if url in seen:
            continue
        seen.add(url)

        page = await context.new_page()
        try:
            await page.goto(url, wait_until="load")
            await fully_render(page)
            # Grab anchors
            anchors = await page.eval_on_selector_all("a[href]", "els => els.map(e => e.getAttribute('href'))")
            abs_links = []
            for href in anchors or []:
                if not href:
                    continue
                abs_links.append(urljoin(url, href))

            for link in abs_links:
                if not _is_confluence_page(link, origin, allow_viewpage=allow_viewpage):
                    continue
                canon = _canonicalize(link)
                # Restrict to same user space prefix (for /display) if available
                if user_space_prefix and not urlparse(canon).path.startswith(user_space_prefix):
                    continue
                # Restrict to descendants of the parent page when using /display
                if parent_prefix and not urlparse(canon).path.startswith(parent_prefix):
                    continue
                if canon in seen or canon in collected:
                    continue
                collected.append(canon)
                if max_pages > 0 and len(collected) >= max_pages:
                    break
                if d + 1 <= depth:
                    to_visit.append((canon, d + 1))
        finally:
            await page.close()

        if max_pages > 0 and len(collected) >= max_pages:
            break

    # Ensure parent is first
    parent_canon = _canonicalize(parent_url)
    if parent_canon not in collected:
        collected.insert(0, parent_canon)
    else:
        collected.remove(parent_canon)
        collected.insert(0, parent_canon)
    return collected


async def run(urls_file: Path | None, parent_url: str | None, out_dir: Path, profile_dir: Path, interactive_login: bool, depth: int, max_pages: int, dry_run: bool, allow_viewpage: bool, mode: str):
    if urls_file:
        urls = [line.strip() for line in urls_file.read_text(encoding="utf-8").splitlines() if line.strip() and not line.strip().startswith("#")]
        if not urls:
            raise SystemExit("No URLs found in urls file.")
        first_url = urls[0]
    elif parent_url:
        first_url = parent_url
        urls = None
    else:
        raise SystemExit("Provide either --urls-file or --parent-url")

    out_dir.mkdir(parents=True, exist_ok=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch_persistent_context(
            user_data_dir=str(profile_dir), headless=False if interactive_login else True
        )
        try:
            await ensure_logged_in(browser, first_url, interactive_login)
            if urls is None:
                urls = await collect_links_under_parent(browser, parent_url, depth=depth, max_pages=max_pages, allow_viewpage=allow_viewpage, mode=mode)
            if dry_run:
                print("Discovered URLs (dry run):")
                for u in urls:
                    print(u)
                return
            for url in urls:
                await export_pdf(browser, url, out_dir)
        finally:
            await browser.close()


def main():
    parser = argparse.ArgumentParser(description="Export Confluence pages to PDF using Playwright (SSO-friendly)")
    src = parser.add_mutually_exclusive_group(required=True)
    src.add_argument("--urls-file", help="Path to a text file with Confluence page URLs (one per line)")
    src.add_argument("--parent-url", help="Parent page URL to auto-crawl and export (same-origin)")
    parser.add_argument("--out-dir", required=True, help="Directory to save PDFs")
    parser.add_argument("--profile-dir", required=True, help="Persistent profile dir to store session (e.g., ~/.confluence-exporter)")
    parser.add_argument("--interactive-login", action="store_true", help="Open visible browser and wait for you to complete SSO")
    parser.add_argument("--depth", type=int, default=1, help="Crawl depth from parent (default: 1)")
    parser.add_argument("--max-pages", type=int, default=100, help="Maximum pages to export (0 = unlimited; default: 100)")
    parser.add_argument("--dry-run", action="store_true", help="Only list collected URLs without exporting PDFs")
    parser.add_argument("--allow-viewpage", action="store_true", help="Also include /pages/viewpage.action links (default: false)")
    parser.add_argument("--crawl-mode", choices=["rest", "rest-ancestor", "dom"], default="rest-ancestor", help="Use Confluence REST descendants (default), REST children, or DOM link crawl")
    args = parser.parse_args()

    asyncio.run(
        run(
            Path(args.urls_file) if args.urls_file else None,
            args.parent_url,
            Path(args.out_dir),
            Path(args.profile_dir),
            args.interactive_login,
            depth=args.depth,
            max_pages=args.max_pages,
            dry_run=args.dry_run,
            allow_viewpage=args.allow_viewpage,
            mode=args.crawl_mode,
        )
    )


if __name__ == "__main__":
    main()
