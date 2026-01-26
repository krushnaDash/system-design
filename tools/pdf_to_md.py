#!/usr/bin/env python3
"""
Extract text from exported Confluence PDFs and generate per-page Markdown summaries plus a manifest.

- Scans an input directory for .pdf files.
- Extracts raw text with pdfminer.six.
- Writes a corresponding .md file with a simple header and the raw text for downstream processing.
- Emits a manifest.json with basic metadata.

Usage:
  python tools/pdf_to_md.py --in-dir exports/pdf --out-dir exports/parsed

After running, you can review the generated Markdown and we can ingest it to populate
Behavioral, Cross-Functional, and Technical Retrospective sections with metrics and artifacts.
"""
import argparse
import json
from pathlib import Path
from typing import List, Dict

from pdfminer.high_level import extract_text


def pdf_to_text(pdf_path: Path) -> str:
    return extract_text(str(pdf_path))


def derive_title(pdf_path: Path) -> str:
    # Use filename stem as a proxy for title
    return pdf_path.stem.replace("-", " ")


def write_md(md_path: Path, title: str, text: str) -> None:
    md_path.parent.mkdir(parents=True, exist_ok=True)
    content = f"# {title}\n\n" + "```\n" + text.strip() + "\n```\n"
    md_path.write_text(content, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert PDFs to Markdown snapshots")
    parser.add_argument("--in-dir", required=True, help="Directory with PDF files")
    parser.add_argument("--out-dir", required=True, help="Directory to write Markdown and manifest")
    args = parser.parse_args()

    in_dir = Path(args.in_dir)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    manifest: List[Dict] = []

    for pdf in sorted(in_dir.glob("*.pdf")):
        try:
            text = pdf_to_text(pdf)
        except Exception as e:
            print(f"Failed to extract {pdf}: {e}")
            continue
        title = derive_title(pdf)
        md_path = out_dir / f"{pdf.stem}.md"
        write_md(md_path, title, text)
        manifest.append({
            "pdf": str(pdf),
            "markdown": str(md_path),
            "title": title,
            "chars": len(text),
        })

    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Wrote {len(manifest)} items to {out_dir} and manifest.json")


if __name__ == "__main__":
    main()
