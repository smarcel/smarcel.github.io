#!/usr/bin/env python3
"""
hugo_publications.py  –  BibTeX → Hugo/HugoBlox publication bundles
=====================================================================

Reads one or more BibTeX files and generates Hugo publication folders
that exactly match the HugoBlox Academic CV theme format, based on
the two reference examples (facerecbench_icassp-2025 and
foundation-models-biometrics-survey_tifs-2025).

Output structure
----------------
  <out_dir>/
    conferences/   →  paper-conference  (inproceedings, conference, …)
    journals/      →  article-journal   (article)
    misc/          →  books, chapters, reports, theses, workshops, etc.

Each folder:
  <bib-key-slug>/
    index.md       YAML front-matter (HugoBlox format)
    cite.bib       single BibTeX entry
    featured.png   placeholder image (only when Pillow available and
                   no image already exists)

Online cross-check (requires 'requests' + 'beautifulsoup4'):
  1. publications.idiap.ch  – enriches abstract, DOI, PDF URL, keywords,
     projects, and paper-page URL from the canonical Idiap BibTeX export.
  2. www.idiap.ch/paper/<slug>/  – detects paper pages and adds a
     'source' link.
  3. GitHub URLs are recognised in url/pdf fields and added as 'code' links.

Author alias
------------
  --me "Marcel, Sébastien"
  Replaces that author with the Hugo alias 'me' in every index.md.

Featured logic
--------------
  conferences / journals published >= 2024  →  featured: true
  all misc entries                          →  featured: false

Usage
-----
  pip install bibtexparser requests beautifulsoup4 Pillow

  python hugo_publications.py --bib refs.bib --me "Marcel, Sébastien"
  python hugo_publications.py --bib refs.bib --out content/publication --dry-run
  python hugo_publications.py --bib refs.bib --keys OtroshiShahreza_ICASSP_2026
  python hugo_publications.py --bib refs.bib --offline       # skip internet lookups
  python hugo_publications.py --bib refs.bib --list          # list all entries
"""

import argparse
import logging
import re
import sys
import time
from pathlib import Path
from typing import Optional

# ── mandatory ────────────────────────────────────────────────────────────────
try:
    import bibtexparser
    from bibtexparser.bwriter import BibTexWriter
    from bibtexparser.bibdatabase import BibDatabase
except ImportError:
    sys.exit("Missing dependency: pip install bibtexparser")

# ── optional ─────────────────────────────────────────────────────────────────
try:
    import requests
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry
    REQUESTS_OK = True
except ImportError:
    REQUESTS_OK = False

try:
    from bs4 import BeautifulSoup
    BS4_OK = True
except ImportError:
    BS4_OK = False

try:
    from PIL import Image, ImageDraw, ImageFont
    PIL_OK = True
except ImportError:
    PIL_OK = False

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
log = logging.getLogger(__name__)

FEATURED_SINCE = 2024   # year threshold for featured: true

# ── BibTeX ENTRYTYPE → (Hugo publication_type, output sub-folder) ────────────
TYPE_MAP = {
    "inproceedings":  ("paper-conference", "conferences"),
    "conference":     ("paper-conference", "conferences"),
    "article":        ("article-journal",  "journals"),
    "book":           ("book",             "misc"),
    "incollection":   ("chapter",          "misc"),
    "inbook":         ("chapter",          "misc"),
    "phdthesis":      ("thesis",           "misc"),
    "mastersthesis":  ("thesis",           "misc"),
    "techreport":     ("report",           "misc"),
    "report":         ("report",           "misc"),
    "misc":           ("manuscript",       "misc"),
    "unpublished":    ("manuscript",       "misc"),
    "preprint":       ("article",          "misc"),
    "workshop":       ("paper-conference", "misc"),
}
DEFAULT_TYPE = ("manuscript", "misc")


# ════════════════════════════════════════════════════════════════════════════
# BibTeX I/O
# ════════════════════════════════════════════════════════════════════════════

def load_bib(path: str) -> list:
    with open(path, encoding="utf-8") as f:
        db = bibtexparser.load(f)
    log.info(f"Loaded {len(db.entries)} entries from {path}")
    return db.entries


def merge_entries(lists):
    merged = {}
    for entries in lists:
        for e in entries:
            key = e.get("ID", "").strip()
            if key:
                merged[key] = e
    return merged


# ════════════════════════════════════════════════════════════════════════════
# Field helpers
# ════════════════════════════════════════════════════════════════════════════

LATEX_ACCENTS = {
    r"\'e": "é", r"\'E": "É", r"\`e": "è", r"\`E": "È",
    r"\^e": "ê", r"\^E": "Ê", r'\"e': "ë", r'\"E': "Ë",
    r"\'a": "á", r"\'A": "Á", r"\`a": "à", r"\`A": "À",
    r"\^a": "â", r"\^A": "Â", r'\"a': "ä", r'\"A': "Ä",
    r"\'o": "ó", r"\'O": "Ó", r"\`o": "ò", r"\`O": "Ò",
    r"\^o": "ô", r"\^O": "Ô", r'\"o': "ö", r'\"O': "Ö",
    r"\'u": "ú", r"\'U": "Ú", r"\`u": "ù", r"\`U": "Ù",
    r"\^u": "û", r"\^U": "Û", r'\"u': "ü", r'\"U': "Ü",
    r"\'i": "í", r"\'I": "Í", r"\`i": "ì", r"\`I": "Ì",
    r"\^i": "î", r"\^I": "Î", r'\"i': "ï", r'\"I': "Ï",
    r"\c{c}": "ç", r"\c{C}": "Ç",
    r"\~n": "ñ",  r"\~N": "Ñ",
    r"\ss": "ß",
    r"{\'{e}}": "é", r"{\'{E}}": "É",  # Idiap style {\'e} → é
    r"{\`{e}}": "è",
}


def clean(text: str) -> str:
    if not text:
        return ""
    for latex, uni in LATEX_ACCENTS.items():
        text = text.replace(latex, uni)
    text = re.sub(r"[{}]", "", text)
    return re.sub(r"\s+", " ", text).strip()


def year_int(entry: dict) -> int:
    raw = clean(entry.get("year", entry.get("date", "")))
    m = re.search(r"\b(19|20)\d{2}\b", raw)
    return int(m.group(0)) if m else 0


def year_str(entry: dict) -> str:
    y = year_int(entry)
    return str(y) if y else ""


def month_str(entry: dict) -> str:
    month_map = {
        "jan": "01", "feb": "02", "mar": "03", "apr": "04",
        "may": "05", "jun": "06", "jul": "07", "aug": "08",
        "sep": "09", "oct": "10", "nov": "11", "dec": "12",
    }
    raw = clean(entry.get("month", "")).strip()
    if not raw:
        return "01"
    if raw.isdigit():
        return raw.zfill(2)
    return month_map.get(raw[:3].lower(), "01")


def date_str(entry: dict) -> str:
    y = year_str(entry)
    return f"{y}-{month_str(entry)}-01" if y else ""


def extract_authors(entry: dict) -> list:
    raw = clean(entry.get("author", ""))
    if not raw:
        return []
    parts = re.split(r"\s+and\s+", raw, flags=re.IGNORECASE)
    result = []
    for p in parts:
        p = p.strip()
        if "," in p:
            last, first = p.split(",", 1)
            p = f"{first.strip()} {last.strip()}"
        result.append(p)
    return result


def _last_name(name: str) -> str:
    name = name.strip()
    if "," in name:
        return name.split(",")[0].strip().lower()
    parts = name.split()
    return parts[-1].lower() if parts else ""


def apply_me_alias(authors: list, me_canonical: Optional[str]) -> list:
    if not me_canonical:
        return authors
    return ["me" if _last_name(a) == _last_name(me_canonical) else a
            for a in authors]


def extract_doi(entry: dict) -> str:
    doi = clean(entry.get("doi", ""))
    doi = re.sub(r"^https?://(dx\.)?doi\.org/", "", doi)
    return doi.strip()


def extract_pdf(entry: dict) -> str:
    return clean(entry.get("pdf", ""))


def extract_url(entry: dict) -> str:
    return clean(entry.get("url", entry.get("link", "")))


def extract_abstract(entry: dict) -> str:
    return clean(entry.get("abstract", ""))


def extract_keywords(entry: dict) -> list:
    raw = clean(entry.get("keywords", ""))
    if not raw:
        return []
    return [k.strip() for k in re.split(r"[;,]", raw) if k.strip()]


def extract_projects(entry: dict) -> list:
    """Read Idiap-style 'projects' field (e.g. projects = {SAFER, CARMEN})."""
    raw = clean(entry.get("projects", ""))
    if not raw:
        return []
    return [p.strip() for p in re.split(r"[;,]", raw) if p.strip()]


def pub_type_folder(entry: dict) -> tuple:
    btype = entry.get("ENTRYTYPE", "misc").lower()
    return TYPE_MAP.get(btype, DEFAULT_TYPE)


def make_slug(key: str) -> str:
    return re.sub(r"[^\w\-]", "-", key).lower().strip("-")


# ════════════════════════════════════════════════════════════════════════════
# Online enrichment
# ════════════════════════════════════════════════════════════════════════════

_session_obj = None


def _session():
    global _session_obj
    if _session_obj is None and REQUESTS_OK:
        s = requests.Session()
        retry = Retry(total=3, backoff_factor=0.5,
                      status_forcelist=[429, 500, 502, 503, 504])
        s.mount("https://", HTTPAdapter(max_retries=retry))
        s.headers["User-Agent"] = "hugo-publications-script/2.0"
        _session_obj = s
    return _session_obj


def _get(url: str, timeout: int = 10) -> Optional[str]:
    try:
        r = _session().get(url, timeout=timeout)
        if r.status_code == 200:
            return r.text
    except Exception as ex:
        log.debug(f"GET failed {url}: {ex}")
    return None


def _title_similarity(a: str, b: str) -> float:
    wa = set(re.sub(r"[^\w\s]", "", a.lower()).split())
    wb = set(re.sub(r"[^\w\s]", "", b.lower()).split())
    if not wa or not wb:
        return 0.0
    return len(wa & wb) / len(wa | wb)


def enrich_from_idiap(bib_key: str, title: str) -> dict:
    """
    Query publications.idiap.ch to enrich one entry.
    Returns a dict (possibly empty) with any of:
      abstract, doi, pdf, keywords, projects, url, paper_page
    """
    enrichment: dict = {}
    if not REQUESTS_OK or not BS4_OK:
        return enrichment

    # Search by the first 6 words of the title
    short = " ".join(title.split()[:6])
    html = _get(f"https://publications.idiap.ch/search?query={requests.utils.quote(short)}")
    pub_id = None
    if html:
        soup = BeautifulSoup(html, "html.parser")
        for a_tag in soup.find_all("a", href=True):
            m = re.search(r"/publications/show/(\d+)", a_tag["href"])
            if m and _title_similarity(a_tag.get_text(strip=True), title) > 0.55:
                pub_id = m.group(1)
                break

    if not pub_id:
        return enrichment

    log.info(f"  → Idiap pub id={pub_id} matched; fetching BibTeX …")

    # Fetch the canonical BibTeX
    bib_html = _get(f"https://publications.idiap.ch/export/publication/{pub_id}/bibtex")
    if bib_html:
        bib_text = re.sub(r"```[a-z]*\n?", "", bib_html).strip()
        try:
            db = bibtexparser.loads(bib_text)
            if db.entries:
                e = db.entries[0]
                for field, key in [("abstract", "abstract"), ("doi", "doi"),
                                    ("pdf", "pdf"), ("url", "url")]:
                    val = clean(e.get(field, ""))
                    if val:
                        enrichment[key] = val
                kw = extract_keywords(e)
                if kw:
                    enrichment["keywords"] = kw
                pr = extract_projects(e)
                if pr:
                    enrichment["projects"] = pr
        except Exception as ex:
            log.debug(f"BibTeX parse error: {ex}")

    # Check the show page for a paper-page URL
    show = _get(f"https://publications.idiap.ch/publications/show/{pub_id}")
    if show:
        soup2 = BeautifulSoup(show, "html.parser")
        for a_tag in soup2.find_all("a", href=True):
            href = a_tag["href"]
            if "idiap.ch/paper/" in href:
                enrichment["paper_page"] = href
                break

    time.sleep(0.3)
    return enrichment


def check_idiap_paper_page(slug: str) -> Optional[str]:
    """HEAD-check https://www.idiap.ch/paper/<slug>/"""
    if not REQUESTS_OK:
        return None
    url = f"https://www.idiap.ch/paper/{slug}/"
    try:
        r = _session().head(url, timeout=8, allow_redirects=True)
        if r.status_code == 200:
            return url
    except Exception:
        pass
    return None


# ════════════════════════════════════════════════════════════════════════════
# Preserve manual edits from existing index.md
# ════════════════════════════════════════════════════════════════════════════

def read_existing(path: Path) -> dict:
    """
    Read an existing index.md and return a dict of manually-set fields
    that should survive re-generation (unless --force).
    """
    if not path.exists():
        return {}
    text = path.read_text(encoding="utf-8")
    out: dict = {}

    m = re.search(r"^publishDate:\s*['\"]?([^'\"\n]+)['\"]?", text, re.M)
    if m:
        out["publishDate"] = m.group(1).strip()

    m = re.search(r"^featured:\s*(true|false)", text, re.M)
    if m:
        out["featured_manual"] = (m.group(1) == "true")

    m = re.search(r"^tags:\s*\n((?:\s+- .+\n?)+)", text, re.M)
    if m:
        out["tags"] = [re.sub(r"^\s*-\s*", "", l).strip()
                       for l in m.group(1).splitlines() if l.strip()]

    m = re.search(r"^summary:\s*'(.*?)'", text, re.M | re.S)
    if not m:
        m = re.search(r'^summary:\s*"(.*?)"', text, re.M | re.S)
    if m:
        out["summary"] = m.group(1).strip()

    m = re.search(r"^projects:\s*\[([^\]]*)\]", text, re.M)
    if m:
        out["projects"] = [p.strip().strip("'\"")
                           for p in m.group(1).split(",") if p.strip()]

    links = re.findall(r"  - type:\s*(\S+)\s*\n\s+url:\s*(\S+)", text)
    if links:
        out["links"] = [{"type": t, "url": u} for t, u in links]

    return out


# ════════════════════════════════════════════════════════════════════════════
# link list builder
# ════════════════════════════════════════════════════════════════════════════

def build_links(pdf_url, url, doi, paper_page, existing_links) -> list:
    result = list(existing_links)          # preserve manual links
    seen = {l["url"] for l in result}

    def add(ltype, lurl):
        lurl = lurl.strip()
        if lurl and lurl not in seen:
            result.append({"type": ltype, "url": lurl})
            seen.add(lurl)

    if pdf_url:
        add("pdf", pdf_url)

    if paper_page:
        if "github.com" in paper_page:
            add("code", paper_page)
        else:
            add("source", paper_page)
    elif url:
        if "github.com" in url:
            add("code", url)
        elif "idiap.ch/paper/" in url:
            add("source", url)
        else:
            add("source", url)

    return result


# ════════════════════════════════════════════════════════════════════════════
# YAML helpers
# ════════════════════════════════════════════════════════════════════════════

def qs(value: str) -> str:
    """Wrap string in YAML single-quotes; fall back to double if needed."""
    if "'" in value:
        value = value.replace('"', '\\"')
        return f'"{value}"'
    return f"'{value}'"


# ════════════════════════════════════════════════════════════════════════════
# index.md builder – matches your exact template format
# ════════════════════════════════════════════════════════════════════════════

def build_index_md(entry, pub_type, sub_folder, me_canonical,
                   enrichment, existing, slug) -> str:
    e = enrichment or {}
    ex = existing or {}

    title    = clean(entry.get("title", "Untitled"))
    abstract = e.get("abstract") or extract_abstract(entry)
    doi      = e.get("doi") or extract_doi(entry)
    pdf_url  = e.get("pdf") or extract_pdf(entry)
    url      = e.get("url") or extract_url(entry)
    keywords = e.get("keywords") or extract_keywords(entry)
    projects = e.get("projects") or extract_projects(entry) or ex.get("projects", [])
    projects_lower = [p.lower().replace(" ", "-") for p in projects]

    authors  = apply_me_alias(extract_authors(entry), me_canonical)
    year     = year_int(entry)
    d_str    = date_str(entry)

    # Publication venue fields
    btype = entry.get("ENTRYTYPE", "misc").lower()
    if pub_type == "paper-conference":
        venue = clean(entry.get("booktitle", ""))
        # Try to extract a short acronym from the booktitle
        acro_matches = re.findall(r"\b([A-Z]{2,})\b", venue)
        short_venue = acro_matches[-1] if acro_matches else venue[:20]
        pub_full  = f"In *{venue}*" if venue else ""
        pub_short = f"In *{short_venue}*" if short_venue else ""
    elif pub_type == "article-journal":
        venue = clean(entry.get("journal", ""))
        pub_full  = f"*{venue}*" if venue else ""
        pub_short = venue   # use full journal name as short (matches your examples)
    else:
        venue = clean(entry.get("booktitle",
                      entry.get("journal",
                      entry.get("school",
                      entry.get("publisher", "")))))
        pub_full  = venue
        pub_short = ""

    # featured
    if "featured_manual" in ex:
        featured = ex["featured_manual"]
    elif sub_folder == "misc":
        featured = False
    else:
        featured = year >= FEATURED_SINCE

    # publishDate: preserve existing or default to date
    pub_date = ex.get("publishDate", d_str)

    # tags: preserve manual, seed from keywords
    tags = ex.get("tags") or keywords

    # links
    links = build_links(
        pdf_url, url, doi,
        e.get("paper_page"),
        ex.get("links", []),
    )

    # summary
    summary = ex.get("summary", "")
    if not summary and abstract:
        summary = abstract[:300] + ("…" if len(abstract) > 300 else "")

    # hugoblox DOI (only for journal papers that have a DOI)
    use_hb_doi = bool(doi) and pub_type == "article-journal"

    # ── assemble ─────────────────────────────────────────────────────────────
    L = ["---",
         f"title: {qs(title)}",
         "",
         "# Authors",
         "# If you created a profile for a user (e.g. the default `me` user), write the username (folder name) here",
         "# and it will be replaced with their full name and linked to their profile.",
         "authors:"]
    for a in authors:
        L.append(f"  - {a}")
    L += ["",
          "# Author notes (optional)",
          "#author_notes:",
          "#  - 'Equal contribution'",
          "#  - 'Equal contribution'",
          ""]
    if d_str:
        L.append(f"date: '{d_str}'")
    L += ["",
          "# Schedule page publish date (NOT publication's date)."]
    if pub_date:
        L.append(f"publishDate: '{pub_date}'")
    L += ["",
          "# Publication type.",
          "# Accepts a single type but formatted as a YAML list (for Hugo requirements).",
          "# Enter a publication type from the CSL standard.",
          f"publication_types: ['{pub_type}']",
          "",
          "# Publication name and optional abbreviated publication name."]
    if pub_full:
        L.append(f"publication: {qs(pub_full)}")
    if pub_short:
        L.append(f"publication_short: {qs(pub_short)}")
    L.append("")
    if abstract:
        L.append(f"abstract: {qs(abstract)}")
    else:
        L.append("abstract: ''")
    L += ["",
          "# Summary. An optional shortened abstract.",
          f"summary: {qs(summary)}",
          "",
          "tags:"]
    for t in tags:
        L.append(f"  - {t}")
    L += ["",
          "# Display this page in the Featured widget?",
          f"featured: {'true' if featured else 'false'}"]

    if use_hb_doi:
        L += ["",
              "hugoblox:",
              "  ids:",
              f"    doi: {doi}"]

    # Custom links
    L += ["",
          "# Custom links"]
    if links:
        L.append("links:")
        for lk in links:
            L.append(f"  - type: {lk['type']}")
            L.append(f"    url: {lk['url']}")
    else:
        L += ["#links:",
              "#  - type: pdf",
              "#    url: ''"]

    L += ["",
          "# Featured image",
          "# To use, add an image named `featured.jpg/png` to your page's folder.",
          "#image:",
          "#  caption: ''",
          "#  focal_point: ''",
          "#  preview_only: false",
          "",
          "# Associated Projects (optional).",
          "#   Associate this publication with one or more of your projects.",
          "#   Simply enter your project's folder or file name without extension.",
          "#   E.g. `internal-project` references `content/project/internal-project/index.md`.",
          "#   Otherwise, set `projects: []`."]
    if projects_lower:
        proj_items = ", ".join(f"'{p}'" for p in projects_lower)
        L.append(f"projects: [{proj_items}]")
    else:
        L.append("projects: []")

    L += ["",
          "# Slides (optional).",
          "#   Associate this publication with Markdown slides.",
          "#   Simply enter your slide deck's filename without extension.",
          "#   E.g. `slides: \"example\"` references `content/slides/example/index.md`.",
          "#   Otherwise, set `slides: \"\"`.",
          '#slides: ""',
          "---",
          ""]
    return "\n".join(L)


# ════════════════════════════════════════════════════════════════════════════
# cite.bib writer
# ════════════════════════════════════════════════════════════════════════════

# Non-standard Idiap-only fields to strip from the exported cite.bib
_IDIAP_FIELDS = {"mainresearchprogram", "additionalresearchprograms", "projects"}


def entry_to_bib(entry: dict) -> str:
    clean_entry = {k: v for k, v in entry.items()
                   if k.lower() not in _IDIAP_FIELDS
                   and k not in ("ENTRYTYPE", "ID")}
    clean_entry["ENTRYTYPE"] = entry.get("ENTRYTYPE", "misc")
    clean_entry["ID"] = entry.get("ID", "unknown")
    db = BibDatabase()
    db.entries = [clean_entry]
    writer = BibTexWriter()
    writer.indent = "  " * 6
    writer.order_entries_by = None
    return bibtexparser.dumps(db, writer)


# ════════════════════════════════════════════════════════════════════════════
# Placeholder image
# ════════════════════════════════════════════════════════════════════════════

def make_placeholder(path: Path, title: str, year: str):
    if not PIL_OK:
        return
    import colorsys
    w, h = 800, 450
    hue = abs(hash(title)) % 360
    r, g, b = colorsys.hsv_to_rgb(hue / 360, 0.28, 0.86)
    img = Image.new("RGB", (w, h), (int(r * 255), int(g * 255), int(b * 255)))
    draw = ImageDraw.Draw(img)
    font = ImageFont.load_default()
    words, lines, line = title.split(), [], []
    for word in words:
        line.append(word)
        if len(" ".join(line)) > 45:
            lines.append(" ".join(line[:-1]))
            line = [word]
    lines.append(" ".join(line))
    y0 = h // 2 - len(lines) * 18
    for ln in lines:
        draw.text((w // 2 - len(ln) * 3, y0), ln, fill=(40, 40, 40), font=font)
        y0 += 34
    if year:
        draw.text((w // 2 - 18, y0 + 6), year, fill=(80, 80, 80), font=font)
    img.save(path, "PNG")


# ════════════════════════════════════════════════════════════════════════════
# Per-entry processor
# ════════════════════════════════════════════════════════════════════════════

def process_entry(entry, out_dir, me_canonical,
                  dry_run=False, force=False, offline=False, no_image=False):
    bib_key  = entry.get("ID", "").strip()
    title    = clean(entry.get("title", ""))
    pub_type, sub_folder = pub_type_folder(entry)
    slug     = make_slug(bib_key)
    folder   = out_dir / sub_folder / slug

    is_new = not folder.exists()
    log.info(f"[{'CREATE' if is_new else 'UPDATE'}] {sub_folder}/{slug}  ({pub_type})")

    if dry_run:
        return

    folder.mkdir(parents=True, exist_ok=True)
    index_md = folder / "index.md"
    cite_bib = folder / "cite.bib"

    # online enrichment
    enrichment: dict = {}
    if not offline and REQUESTS_OK:
        paper_page = check_idiap_paper_page(slug)
        if paper_page:
            log.info(f"  ✓ Paper page: {paper_page}")
            enrichment["paper_page"] = paper_page
        idiap_data = enrich_from_idiap(bib_key, title)
        enrichment.update(idiap_data)

    # preserve manual edits
    existing = {} if force else read_existing(index_md)

    # write index.md
    content = build_index_md(
        entry, pub_type, sub_folder, me_canonical,
        enrichment, existing, slug,
    )
    index_md.write_text(content, encoding="utf-8")

    # write cite.bib
    cite_bib.write_text(entry_to_bib(entry), encoding="utf-8")

    # placeholder image (new entries only, skip if image already present)
    if is_new and not no_image:
        for ext in ("featured.png", "featured.jpg"):
            if (folder / ext).exists():
                break
        else:
            make_placeholder(folder / "featured.png", title, year_str(entry))

    log.info(f"  ✓  {folder.relative_to(out_dir)}")


# ════════════════════════════════════════════════════════════════════════════
# CLI
# ════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="BibTeX → Hugo/HugoBlox publication bundles",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--bib", metavar="FILE", action="append", default=[],
                        help="BibTeX file (repeat for multiple files)")
    parser.add_argument("--out", metavar="DIR", default="publications",
                        help="Root output directory (default: publications/)")
    parser.add_argument("--me", metavar='"Last, First"',
                        help='Author name to replace with "me" alias')
    parser.add_argument("--dry-run", action="store_true",
                        help="Show actions without writing any files")
    parser.add_argument("--force", action="store_true",
                        help="Overwrite all fields, including manual edits")
    parser.add_argument("--offline", action="store_true",
                        help="Skip all internet lookups")
    parser.add_argument("--no-image", action="store_true",
                        help="Do not generate placeholder images")
    parser.add_argument("--keys", metavar="KEY", nargs="+",
                        help="Process only these BibTeX keys")
    parser.add_argument("--list", action="store_true",
                        help="List all entries and exit")
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    if not args.bib:
        parser.error("Provide at least one --bib FILE.")

    if not REQUESTS_OK and not args.offline:
        log.warning("'requests' not installed – running offline. "
                    "Install: pip install requests beautifulsoup4")
        args.offline = True

    # load
    all_lists = [load_bib(f) for f in args.bib]
    merged = merge_entries(all_lists)
    log.info(f"Total unique entries: {len(merged)}")

    # list mode
    if args.list:
        print(f"\n{'Key':<42} {'Year':<6} {'Folder':<14} {'Title'}")
        print("-" * 110)
        for k in sorted(merged, key=lambda k: -year_int(merged[k])):
            e = merged[k]
            _, sf = pub_type_folder(e)
            print(f"{k:<42} {year_str(e):<6} {sf:<14} "
                  f"{clean(e.get('title',''))[:50]}")
        print()
        return

    # filter by keys
    targets = merged
    if args.keys:
        targets = {k: v for k, v in merged.items() if k in args.keys}
        missing = set(args.keys) - set(targets)
        if missing:
            log.warning("Keys not found: %s", ", ".join(missing))

    out_dir = Path(args.out)
    conf_n = sum(1 for e in targets.values() if pub_type_folder(e)[1] == "conferences")
    jour_n = sum(1 for e in targets.values() if pub_type_folder(e)[1] == "journals")
    misc_n = sum(1 for e in targets.values() if pub_type_folder(e)[1] == "misc")
    log.info(f"Conferences: {conf_n}  |  Journals: {jour_n}  |  Misc: {misc_n}")

    for key, entry in sorted(targets.items(), key=lambda kv: -year_int(kv[1])):
        process_entry(
            entry, out_dir,
            me_canonical=args.me,
            dry_run=args.dry_run,
            force=args.force,
            offline=args.offline,
            no_image=args.no_image,
        )

    if args.dry_run:
        log.info("[DRY RUN] No files written.")
    else:
        log.info(f"\nDone → {out_dir}/")
        log.info(f"  conferences/  {conf_n} entries")
        log.info(f"  journals/     {jour_n} entries")
        log.info(f"  misc/         {misc_n} entries")


if __name__ == "__main__":
    main()
