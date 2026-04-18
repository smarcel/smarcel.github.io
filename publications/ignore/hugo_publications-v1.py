#!/usr/bin/env python3
"""
Hugo Publication Manager
========================
Sync BibTeX entries (from local files or URLs) into Hugo publication folders.

Each publication gets:
  content/publication/<bibtex-key>/
      index.md   – Hugo front matter + abstract
      cite.bib   – single-entry BibTeX file
      featured.jpg – placeholder (or downloaded cover)

Usage
-----
  python hugo_publications.py --help
  python hugo_publications.py --bib refs.bib --out content/publication
  python hugo_publications.py --bib refs.bib --bib extra.bib --url https://example.com/pubs.bib
  python hugo_publications.py --bib refs.bib --dry-run

Dependencies
------------
  pip install bibtexparser requests Pillow

"""

import argparse
import os
import re
import sys
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional

# ---------------------------------------------------------------------------
# Optional imports – warn gracefully if missing
# ---------------------------------------------------------------------------
try:
    import bibtexparser
    from bibtexparser.bwriter import BibTexWriter
    from bibtexparser.bibdatabase import BibDatabase
except ImportError:
    sys.exit("Missing dependency: pip install bibtexparser")

try:
    import requests
except ImportError:
    requests = None  # URL fetching will be disabled

try:
    from PIL import Image, ImageDraw, ImageFont
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# BibTeX helpers
# ---------------------------------------------------------------------------

PUBLICATION_TYPES = {
    "article":       "article-journal",
    "inproceedings": "paper-conference",
    "proceedings":   "paper-conference",
    "conference":    "paper-conference",
    "book":          "book",
    "incollection":  "chapter",
    "phdthesis":     "thesis",
    "mastersthesis": "thesis",
    "techreport":    "report",
    "misc":          "manuscript",
    "preprint":      "article",  # common custom type
    "unpublished":   "manuscript",
}

def load_bib_file(path: str) -> list[dict]:
    """Parse a local .bib file and return list of entry dicts."""
    with open(path, encoding="utf-8") as f:
        db = bibtexparser.load(f)
    log.info(f"Loaded {len(db.entries)} entries from {path}")
    return db.entries


def load_bib_url(url: str) -> list[dict]:
    """Download a .bib file from a URL and parse it."""
    if requests is None:
        log.warning("requests not installed – skipping URL: %s", url)
        return []
    log.info(f"Fetching {url} …")
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    db = bibtexparser.loads(r.text)
    log.info(f"Loaded {len(db.entries)} entries from {url}")
    return db.entries


def merge_entries(entry_lists: list[list[dict]]) -> dict[str, dict]:
    """Merge multiple entry lists, keyed by BibTeX ID. Later lists win."""
    merged = {}
    for entries in entry_lists:
        for e in entries:
            key = e.get("ID", "").strip()
            if key:
                merged[key] = e
    return merged


# ---------------------------------------------------------------------------
# Field extraction helpers
# ---------------------------------------------------------------------------

def clean(text: str) -> str:
    """Remove LaTeX braces and normalize whitespace."""
    text = re.sub(r"[{}]", "", text)
    return re.sub(r"\s+", " ", text).strip()


def extract_year(entry: dict) -> str:
    year = clean(entry.get("year", ""))
    if not year:
        # Try to find a 4-digit year in the date field
        date = entry.get("date", "")
        m = re.search(r"\b(19|20)\d{2}\b", date)
        year = m.group(0) if m else ""
    return year


def extract_authors(entry: dict) -> list[str]:
    """Return list of 'Firstname Lastname' strings."""
    raw = clean(entry.get("author", ""))
    if not raw:
        return []
    parts = re.split(r"\s+and\s+", raw, flags=re.IGNORECASE)
    authors = []
    for p in parts:
        p = p.strip()
        if "," in p:
            last, first = p.split(",", 1)
            p = f"{first.strip()} {last.strip()}"
        authors.append(p)
    return authors


def extract_doi(entry: dict) -> str:
    doi = clean(entry.get("doi", ""))
    # Strip URL prefix if present
    doi = re.sub(r"^https?://(dx\.)?doi\.org/", "", doi)
    return doi


def extract_url(entry: dict) -> str:
    return clean(entry.get("url", entry.get("link", "")))


def extract_abstract(entry: dict) -> str:
    return clean(entry.get("abstract", ""))


def pub_type(entry: dict) -> str:
    btype = entry.get("ENTRYTYPE", "misc").lower()
    return PUBLICATION_TYPES.get(btype, "manuscript")


def slug(key: str) -> str:
    """Turn a BibTeX key into a safe folder name."""
    return re.sub(r"[^\w\-]", "-", key).lower().strip("-")


# ---------------------------------------------------------------------------
# Hugo front-matter builder
# ---------------------------------------------------------------------------

def build_front_matter(entry: dict, existing: Optional[dict] = None) -> dict:
    """
    Build the Hugo/Wowchemy front-matter dict.
    If `existing` is provided, only AUTO fields are overwritten;
    manual fields (tags, featured, image caption, etc.) are preserved.
    """
    ex = existing or {}

    authors = extract_authors(entry)
    year = extract_year(entry)
    title = clean(entry.get("title", "Untitled"))
    abstract = extract_abstract(entry)
    doi = extract_doi(entry)
    url = extract_url(entry)
    venue = clean(entry.get("journal",
                  entry.get("booktitle",
                  entry.get("school",
                  entry.get("publisher", "")))))

    # Build publication_types list (Wowchemy v5+ uses string list)
    pub_type_str = pub_type(entry)

    # Date
    month = clean(entry.get("month", "01"))
    # Normalize month name → number
    month_map = {
        "jan": "01", "feb": "02", "mar": "03", "apr": "04",
        "may": "05", "jun": "06", "jul": "07", "aug": "08",
        "sep": "09", "oct": "10", "nov": "11", "dec": "12",
    }
    month = month_map.get(month[:3].lower(), month.zfill(2) if month.isdigit() else "01")
    date_str = f"{year}-{month}-01" if year else ""

    fm = {
        # AUTO-managed fields (always overwritten)
        "title":            title,
        "authors":          authors,
        "date":             date_str,
        "publishDate":      datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "publication_types": [pub_type_str],
        "publication":      venue,
        "abstract":         abstract,
        # Links
        "doi":              doi,
    }

    # Build url_* links
    links = ex.get("links", [])
    if doi and not any(l.get("name") == "DOI" for l in links):
        links.append({"name": "DOI", "url": f"https://doi.org/{doi}"})
    if url and not any(l.get("url") == url for l in links):
        links.append({"name": "URL", "url": url})
    fm["links"] = links

    # MANUAL fields – preserve if already set
    fm["featured"]    = ex.get("featured", False)
    fm["tags"]        = ex.get("tags", [])
    fm["categories"]  = ex.get("categories", [])
    fm["projects"]    = ex.get("projects", [])
    fm["image"]       = ex.get("image", {
        "caption": "",
        "focal_point": "Smart",
        "preview_only": False,
    })
    fm["summary"]     = ex.get("summary", "")

    return fm


def fm_to_toml(fm: dict) -> str:
    """Serialize front-matter dict to Hugo TOML format."""
    lines = ["+++"]

    def val(v):
        if isinstance(v, bool):
            return "true" if v else "false"
        if isinstance(v, str):
            escaped = v.replace('"', '\\"')
            return f'"{escaped}"'
        if isinstance(v, list):
            if not v:
                return "[]"
            if all(isinstance(i, str) for i in v):
                items = ", ".join(f'"{i}"' for i in v)
                return f"[{items}]"
        return repr(v)

    for k, v in fm.items():
        if isinstance(v, dict):
            lines.append(f"\n[{k}]")
            for dk, dv in v.items():
                lines.append(f'  {dk} = {val(dv)}')
        elif isinstance(v, list) and v and isinstance(v[0], dict):
            for item in v:
                lines.append(f"\n[[{k}]]")
                for ik, iv in item.items():
                    lines.append(f"  {ik} = {val(iv)}")
        else:
            lines.append(f"{k} = {val(v)}")

    lines.append("+++")
    return "\n".join(lines)


def read_existing_fm(index_md: Path) -> dict:
    """
    Very simple TOML front-matter reader for existing index.md files.
    Returns dict of manually-edited fields we want to preserve.
    """
    if not index_md.exists():
        return {}
    text = index_md.read_text(encoding="utf-8")
    # Extract featured, tags, categories, projects, image, summary
    preserved = {}
    # featured
    m = re.search(r'^featured\s*=\s*(true|false)', text, re.M)
    if m:
        preserved["featured"] = m.group(1) == "true"
    # tags
    m = re.search(r'^tags\s*=\s*\[([^\]]*)\]', text, re.M)
    if m:
        preserved["tags"] = [t.strip().strip('"') for t in m.group(1).split(",") if t.strip()]
    # categories
    m = re.search(r'^categories\s*=\s*\[([^\]]*)\]', text, re.M)
    if m:
        preserved["categories"] = [t.strip().strip('"') for t in m.group(1).split(",") if t.strip()]
    # projects
    m = re.search(r'^projects\s*=\s*\[([^\]]*)\]', text, re.M)
    if m:
        preserved["projects"] = [t.strip().strip('"') for t in m.group(1).split(",") if t.strip()]
    # summary
    m = re.search(r'^summary\s*=\s*"(.*?)"', text, re.M)
    if m:
        preserved["summary"] = m.group(1)
    return preserved


# ---------------------------------------------------------------------------
# BibTeX single-entry writer
# ---------------------------------------------------------------------------

def entry_to_bib(entry: dict) -> str:
    db = BibDatabase()
    db.entries = [entry]
    writer = BibTexWriter()
    writer.indent = "  "
    return writer.write(db)


# ---------------------------------------------------------------------------
# Placeholder image generator
# ---------------------------------------------------------------------------

def make_placeholder_image(path: Path, title: str, year: str):
    """Create a simple colored placeholder image with title text."""
    if not PIL_AVAILABLE:
        log.debug("Pillow not available – skipping placeholder image")
        return
    w, h = 800, 450
    # Color based on hash of title for variety
    hue = abs(hash(title)) % 360
    # Simple HSV → RGB (fixed S=0.4, V=0.85)
    import colorsys
    r, g, b = colorsys.hsv_to_rgb(hue / 360, 0.35, 0.82)
    bg = (int(r * 255), int(g * 255), int(b * 255))
    img = Image.new("RGB", (w, h), bg)
    draw = ImageDraw.Draw(img)

    # Try to load a font, fall back to default
    font_title = font_year = None
    for size, attr in [(32, "font_title"), (20, "font_year")]:
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", size)
        except Exception:
            font = ImageFont.load_default()
        locals()[attr] if False else None
        if attr == "font_title":
            font_title = font
        else:
            font_year = font

    # Wrap title
    words = title.split()
    lines, line = [], []
    for w_word in words:
        line.append(w_word)
        if len(" ".join(line)) > 40:
            lines.append(" ".join(line[:-1]))
            line = [w_word]
    lines.append(" ".join(line))

    text_color = (40, 40, 40)
    y = h // 2 - len(lines) * 20
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font_title)
        tw = bbox[2] - bbox[0]
        draw.text(((800 - tw) / 2, y), line, fill=text_color, font=font_title)
        y += 44

    if year:
        bbox = draw.textbbox((0, 0), year, font=font_year)
        tw = bbox[2] - bbox[0]
        draw.text(((800 - tw) / 2, y + 10), year, fill=text_color, font=font_year)

    img.save(path, "JPEG", quality=85)


# ---------------------------------------------------------------------------
# Main folder creator / updater
# ---------------------------------------------------------------------------

def process_entry(entry: dict, out_dir: Path, dry_run: bool = False,
                  force: bool = False, no_image: bool = False):
    key = entry.get("ID", "").strip()
    if not key:
        log.warning("Entry without ID – skipping: %s", entry)
        return

    folder = out_dir / slug(key)
    index_md = folder / "index.md"
    cite_bib = folder / "cite.bib"
    image_path = folder / "featured.jpg"

    is_new = not folder.exists()
    action = "CREATE" if is_new else "UPDATE"
    log.info(f"[{action}] {key}  →  {folder}")

    if dry_run:
        return

    folder.mkdir(parents=True, exist_ok=True)

    # Preserve manually edited front-matter fields
    existing_fm = {} if force else read_existing_fm(index_md)

    # Build and write index.md
    fm = build_front_matter(entry, existing_fm)
    content = fm_to_toml(fm)
    abstract = fm.get("abstract", "")
    if abstract:
        content += f"\n\n{abstract}\n"
    index_md.write_text(content, encoding="utf-8")

    # Write cite.bib
    cite_bib.write_text(entry_to_bib(entry), encoding="utf-8")

    # Create placeholder image only for new entries (don't overwrite custom images)
    if is_new and not no_image:
        make_placeholder_image(image_path, fm["title"], extract_year(entry))

    log.info(f"  ✓ {folder.relative_to(out_dir)}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Sync BibTeX entries into Hugo publication folders.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--bib",  metavar="FILE", action="append", default=[],
                        help="Local .bib file (can repeat)")
    parser.add_argument("--url",  metavar="URL",  action="append", default=[],
                        help="URL to a .bib file (can repeat)")
    parser.add_argument("--out",  metavar="DIR",  default="content/publication",
                        help="Hugo publication directory (default: content/publication)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print what would be done without writing files")
    parser.add_argument("--force", action="store_true",
                        help="Overwrite all fields, including manually edited ones")
    parser.add_argument("--no-image", action="store_true",
                        help="Skip placeholder image generation")
    parser.add_argument("--keys", metavar="KEY", nargs="+",
                        help="Process only these BibTeX keys")
    parser.add_argument("--list", action="store_true",
                        help="List all BibTeX keys found in sources and exit")
    parser.add_argument("--report", action="store_true",
                        help="Print a summary table of all found entries")
    args = parser.parse_args()

    if not args.bib and not args.url:
        parser.error("Provide at least one --bib file or --url.")

    # Collect entries
    all_entry_lists = []
    for bib_file in args.bib:
        all_entry_lists.append(load_bib_file(bib_file))
    for url in args.url:
        all_entry_lists.append(load_bib_url(url))

    merged = merge_entries(all_entry_lists)
    log.info(f"Total unique entries: {len(merged)}")

    if args.list:
        for key in sorted(merged):
            e = merged[key]
            print(f"{key:40s}  {extract_year(e)}  {clean(e.get('title',''))[:60]}")
        return

    if args.report:
        print(f"\n{'Key':<35} {'Year':<6} {'Type':<22} {'Title'}")
        print("-" * 100)
        for key in sorted(merged):
            e = merged[key]
            print(f"{key:<35} {extract_year(e):<6} {pub_type(e):<22} {clean(e.get('title',''))[:50]}")
        print()
        return

    out_dir = Path(args.out)

    # Filter by keys if requested
    targets = merged
    if args.keys:
        targets = {k: v for k, v in merged.items() if k in args.keys}
        missing = set(args.keys) - set(targets)
        if missing:
            log.warning("Keys not found: %s", ", ".join(missing))

    if not targets:
        log.warning("No entries to process.")
        return

    for key, entry in targets.items():
        process_entry(entry, out_dir,
                      dry_run=args.dry_run,
                      force=args.force,
                      no_image=args.no_image)

    if args.dry_run:
        log.info("[DRY RUN] No files were written.")
    else:
        log.info(f"Done. Processed {len(targets)} publication(s) in {out_dir}/")


if __name__ == "__main__":
    main()
