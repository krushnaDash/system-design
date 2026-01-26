#!/usr/bin/env python3
"""
Confluence page exporter for private spaces.
- Supports Confluence Cloud and Server/DC using the REST API.
- Exports pages as HTML (storage format) or Markdown (via html2text conversion).
- Auth via environment variables for safety.

Environment variables:
  CONFLUENCE_URL        Base URL, e.g. https://your-domain.atlassian.net/wiki
  CONFLUENCE_EMAIL      (Cloud) Account email (or username for Server/DC)
  CONFLUENCE_API_TOKEN  (Cloud) API token (or PAT for Server/DC)

Usage examples:
  python tools/confluence_export.py --space-key ENG --out-dir exports/eng --format html
  python tools/confluence_export.py --root-page-id 123456 --out-dir exports/thread --format md

Notes:
- For large spaces, prefer a root page export to keep scope focused.
- PDF export is best done by converting the saved HTML using your preferred toolchain (e.g., wkhtmltopdf or pandoc). This script focuses on structured content export for downstream processing.
"""
import argparse
import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import requests
from requests.auth import HTTPBasicAuth

try:
    import html2text  # type: ignore
except Exception:
    html2text = None

DEFAULT_PAGE_LIMIT = 50


def getenv_or_exit(name: str) -> str:
    val = os.getenv(name)
    if not val:
        print(f"Missing environment variable: {name}", file=sys.stderr)
        sys.exit(2)
    return val


def build_client() -> Tuple[str, HTTPBasicAuth]:
    base_url = getenv_or_exit("CONFLUENCE_URL").rstrip("/")
    email = getenv_or_exit("CONFLUENCE_EMAIL")
    token = getenv_or_exit("CONFLUENCE_API_TOKEN")
    return base_url, HTTPBasicAuth(email, token)


def confluence_get(base_url: str, auth: HTTPBasicAuth, path: str, params: Optional[Dict] = None) -> Dict:
    url = f"{base_url}/rest/api{path}"
    resp = requests.get(url, auth=auth, params=params, timeout=30)
    if not resp.ok:
        raise RuntimeError(f"GET {url} failed: {resp.status_code} {resp.text[:200]}")
    return resp.json()


def fetch_page(base_url: str, auth: HTTPBasicAuth, page_id: str) -> Dict:
    return confluence_get(base_url, auth, f"/content/{page_id}", params={"expand": "body.storage,version,ancestors"})


def fetch_children(base_url: str, auth: HTTPBasicAuth, page_id: str, limit: int = DEFAULT_PAGE_LIMIT) -> List[Dict]:
    results: List[Dict] = []
    start = 0
    while True:
        data = confluence_get(base_url, auth, f"/content/{page_id}/child/page", params={"limit": limit, "start": start, "expand": "version"})
        results.extend(data.get("results", []))
        if data.get("_links", {}).get("next"):
            start += limit
        else:
            break
    return results


def fetch_space_pages(base_url: str, auth: HTTPBasicAuth, space_key: str, limit: int = DEFAULT_PAGE_LIMIT) -> List[Dict]:
    # Use CQL to paginate through pages in a space.
    results: List[Dict] = []
    start = 0
    cql = f"space={space_key} and type=page order by created asc"
    while True:
        data = confluence_get(base_url, auth, "/content/search", params={"cql": cql, "limit": limit, "start": start, "expand": "version"})
        batch = data.get("results", [])
        if not batch:
            break
        results.extend(batch)
        if len(batch) < limit:
            break
        start += limit
    return results


def slugify(name: str) -> str:
    safe = "".join(c if c.isalnum() or c in ("-", "_") else "-" for c in name.strip())
    safe = "-".join(filter(None, safe.split("-")))
    return safe[:120] if safe else "page"


def ensure_unique(path: Path) -> Path:
    if not path.exists():
        return path
    stem = path.stem
    suffix = path.suffix
    parent = path.parent
    i = 2
    while True:
        candidate = parent / f"{stem}-{i}{suffix}"
        if not candidate.exists():
            return candidate
        i += 1


def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(content, encoding="utf-8")
    tmp.replace(path)


def convert_html_to_md(html: str) -> str:
    if html2text is None:
        raise RuntimeError("html2text is not installed. Install dependencies from requirements.txt or use --format html.")
    h = html2text.HTML2Text()
    h.body_width = 0
    h.ignore_images = False
    h.ignore_links = False
    return h.handle(html)


def export_page(base_url: str, auth: HTTPBasicAuth, page: Dict, out_dir: Path, fmt: str) -> None:
    page_id = page.get("id")
    detail = fetch_page(base_url, auth, page_id)
    title = detail.get("title", f"page-{page_id}")
    storage = detail.get("body", {}).get("storage", {}).get("value", "")
    version = detail.get("version", {}).get("number")

    slug = slugify(title)
    ext = ".html" if fmt == "html" else ".md"
    filename = f"{slug}-{page_id}-v{version}{ext}" if version else f"{slug}-{page_id}{ext}"
    out_path = ensure_unique(out_dir / filename)

    if fmt == "html":
        content = storage
    elif fmt == "md":
        content = convert_html_to_md(storage)
    else:
        raise ValueError("Unsupported format. Use 'html' or 'md'.")

    write_file(out_path, content)
    print(f"Saved {title} -> {out_path}")


def walk_pages_under_root(base_url: str, auth: HTTPBasicAuth, root_id: str) -> List[Dict]:
    # BFS traversal to collect root + all descendants
    queue = [root_id]
    seen = set()
    out: List[Dict] = []
    while queue:
        pid = queue.pop(0)
        if pid in seen:
            continue
        seen.add(pid)
        page = fetch_page(base_url, auth, pid)
        out.append(page)
        children = fetch_children(base_url, auth, pid)
        queue.extend(child.get("id") for child in children)
        # be nice to API
        time.sleep(0.1)
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description="Export Confluence pages to HTML/Markdown via REST API.")
    src = parser.add_mutually_exclusive_group(required=True)
    src.add_argument("--space-key", help="Confluence space key (export all pages in space)")
    src.add_argument("--root-page-id", help="Root page ID to export (recursively includes children)")
    parser.add_argument("--out-dir", required=True, help="Output directory")
    parser.add_argument("--format", choices=["html", "md"], default="html", help="Export format: html or md")
    parser.add_argument("--max-pages", type=int, default=0, help="Optional cap on pages exported (0 = no cap)")

    args = parser.parse_args()

    base_url, auth = build_client()
    out_dir = Path(args.out_dir)

    pages: List[Dict]
    if args.root_page_id:
        pages = walk_pages_under_root(base_url, auth, args.root_page_id)
    else:
        pages = fetch_space_pages(base_url, auth, args.space_key)

    if args.max_pages and len(pages) > args.max_pages:
        pages = pages[: args.max_pages]

    for p in pages:
        export_page(base_url, auth, p, out_dir, args.format)


if __name__ == "__main__":
    main()
