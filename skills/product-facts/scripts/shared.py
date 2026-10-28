"""Shared readers for the product-facts scripts: the store file, saved pages,
the products export and the review file. Standard library only; reads files,
never the network.

Imported by product_gaps.py, review_file.py and product_import.py, which put
this folder on sys.path themselves because `python3 -I` does not. Fact slots
and product lines are not read here: every caller imports the shared module
fact_slots.py from the same folder (references/schemas.md section 12).
"""

import csv
import html
import json
import re
from html.parser import HTMLParser
from pathlib import Path

# ---------------------------------------------------------------- store file
# Field openings from the store template, version 0.1.1 of 2026-10-21
# (skills/store-setup/assets/store-template.md). Scripts find a field by its
# opening words and take the value from after the field's full template text.
FIELD_SLOTS = (2, "The facts every product page states")
FIELD_LINES = (2, "Product lines")
FIELD_QUESTIONS = (4, "The questions buyers ask before buying")
FIELD_PROMPTS = (4, "Answer-check prompts (optional)")
FIELD_CLEARED = (3, "Statements the store makes about its products and has cleared")
FIELD_NEVER = (3, "Statements the store never makes")
FIELD_REDLINES = (3, "Words, topics and comparisons the brand does not use")
FIELD_REVIEWS_APP = (5, "Reviews app")
FIELD_ALT_RULE = (9, "Every product image carries alt text")
FIELD_DOMAIN = (1, "Public domain")
FIELD_APPROVER = (7, "Who approves a change to product data")

# Full template text of each field line, template 0.1.1 of 2026-10-21. Used
# only when the store-setup template is not beside this skill; otherwise the
# labels are read from that template at run time (schemas.md section 3), so a
# template change reaches these scripts when the set is installed together.
LABELS = {
    "The facts every product page states": "The facts every product page states (the fact slots), one per indented line: the slot's name, and where the fact comes from (label, specification sheet, the person):",
    "Product lines": "Product lines, one per indented line: the line's name, what it is, who it is for, and the Shopify product category it sits in:",
    "The questions buyers ask before buying": "The questions buyers ask before buying, five to ten, in the buyer's own words, one per indented line (this is the answer-check list):",
    "Answer-check prompts (optional)": "Answer-check prompts (optional), the questions above as a buyer would type them into an assistant that knows nothing about the store, naming the kind of product and the need but no brand, one per indented line; when blank, the answer check uses the questions above with a short opening:",
    "Statements the store makes about its products and has cleared": "Statements the store makes about its products and has cleared, verbatim, one per indented line with the product or line it applies to; a statement not here is \"ask\":",
    "Statements the store never makes": "Statements the store never makes, one per indented line, with the reason:",
    "Words, topics and comparisons the brand does not use": "Words, topics and comparisons the brand does not use (the redlines), one per indented line:",
    "Reviews app": "Reviews app, and whether it adds ratings to the product structured data:",
    "Every product image carries alt text": "Every product image carries alt text [default yes]:",
    "Public domain": "Public domain, as `https://...`:",
    "Who approves a change to product data": "Who approves a change to product data before it is imported or applied (role):",
}
TEMPLATE = Path(__file__).resolve().parents[2] / "store-setup" / "assets" / "store-template.md"

MARK = re.compile(r"\s*\[(owner|observed|default|open)\]\s*$")


TEMPLATE_VERSION = "0.1.1"


def _labels():
    """Full field labels: from the store-setup template beside this skill
    when present, else the embedded copy above (template 0.1.1)."""
    labels = dict(LABELS)
    if TEMPLATE.is_file():
        lines = [l[2:].rstrip() for l in TEMPLATE.read_text(encoding="utf-8").splitlines() if l.startswith("- ")]
        for key in LABELS:
            for l in lines:
                if l.startswith(key) and l.endswith(":"):
                    labels[key] = l
                    break
    return labels


FULL_LABELS = _labels()
# Said in the coverage line when the labels came from the embedded copy
# (schemas.md section 3); empty when the template was read at run time.
LABELS_NOTE = ("" if TEMPLATE.is_file() else
               f"store file labels: the embedded copy of template {TEMPLATE_VERSION} (the store-setup template is not beside this skill)")


class StoreFileError(Exception):
    """Raised with the one sentence the person reads."""


def read_store(workspace):
    path = Path(workspace) / "store" / "store.md"
    if not path.is_file():
        raise StoreFileError(
            f"There is no store file at {path}; run store-setup with the person who runs the store first."
        )
    sections = {}
    current = None
    for line in path.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^##\s+(\d+)\.", line)
        if m:
            current = int(m.group(1))
            sections[current] = []
            continue
        if current is not None:
            sections[current].append(line)
    return sections


def _after_colon(rest):
    """Fallback when the line does not carry the full template text: the
    value starts after the first colon outside backticks."""
    ticks = False
    for k, ch in enumerate(rest):
        if ch == "`":
            ticks = not ticks
        elif ch == ":" and not ticks and (k + 1 == len(rest) or rest[k + 1] in " \t"):
            return rest[k + 1:]
    return ""


def field(sections, spec):
    """Return (value, mark, details) for a field; details are the marked
    indented lines as (text, mark). An unmarked indented line is template
    guidance and is skipped."""
    number, opening = spec
    label = FULL_LABELS.get(opening)
    lines = sections.get(number, [])
    for i, line in enumerate(lines):
        if line.startswith("- ") and line[2:].startswith(opening):
            rest = line[2:]
            value = rest[len(label):] if label and rest.startswith(label) else _after_colon(rest)
            mark = None
            mm = MARK.search(value)
            if mm:
                mark = mm.group(1)
                value = value[: mm.start()]
            details = []
            for sub in lines[i + 1:]:
                if sub.startswith("- ") or sub.startswith("#"):
                    break
                if not sub.startswith((" ", "\t")) or not sub.strip():
                    continue
                sm = MARK.search(sub)
                if not sm:
                    continue
                text = sub.strip()
                text = text[2:] if text.startswith("- ") else text
                text = MARK.sub("", text).strip()
                details.append((text, sm.group(1)))
            return value.strip(), mark, details
    return None, None, []


def list_field(sections, spec):
    """Marked list entries for a list field, [open] entries left out; also
    returns how many entries were [open]."""
    value, mark, details = field(sections, spec)
    items = [t for t, m in details if m != "open" and t]
    opened = sum(1 for _, m in details if m == "open")
    if not items and value and mark not in (None, "open"):
        items = [value]
    return items, opened, mark


# ---------------------------------------------------------------- product lines
# Fact slots and product lines are read and matched by the shared module
# fact_slots.py beside this file (references/schemas.md section 12), never by
# a rule of this skill's own. Said in a gap-table note for a product that
# matches no product line in store file section 2; review_file.py reads it
# back from the notes.
NOT_IN_LINE = "not in a product line in store file section 2: fact slots not checked"


# ---------------------------------------------------------------- HTML
class _Text(HTMLParser):
    SKIP = {"script", "style", "noscript", "template", "svg"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.depth = 0
        self.parts = []
        self.ld = []
        self._in_ld = False
        self._ld_buf = []
        self.meta_description = None
        self.title_seen = False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "script" and (a.get("type") or "").lower() == "application/ld+json":
            self._in_ld = True
            self._ld_buf = []
        if tag == "meta" and (a.get("name") or "").lower() == "description":
            self.meta_description = (a.get("content") or "").strip()
        if tag in self.SKIP:
            self.depth += 1

    def handle_endtag(self, tag):
        if tag == "script" and self._in_ld:
            self.ld.append("".join(self._ld_buf))
            self._in_ld = False
        if tag in self.SKIP and self.depth:
            self.depth -= 1

    def handle_data(self, data):
        if self._in_ld:
            self._ld_buf.append(data)
        elif not self.depth:
            self.parts.append(data)


def html_text(markup):
    p = _Text()
    p.feed(markup or "")
    return re.sub(r"\s+", " ", " ".join(p.parts)).strip()


def read_page(path):
    """Visible text, JSON-LD objects and meta description of a saved page."""
    p = _Text()
    p.feed(Path(path).read_text(encoding="utf-8", errors="replace"))
    objects = []
    for raw in p.ld:
        try:
            data = json.loads(raw)
        except ValueError:
            continue
        stack = [data]
        while stack:
            item = stack.pop()
            if isinstance(item, list):
                stack.extend(item)
            elif isinstance(item, dict):
                objects.append(item)
                for key in ("@graph", "hasVariant", "mainEntity", "offers"):
                    if key in item:
                        stack.append(item[key])
    text = re.sub(r"\s+", " ", " ".join(p.parts)).strip()
    return {"text": text, "ld": objects, "meta_description": p.meta_description}


def ld_types(obj):
    t = obj.get("@type")
    return set(t) if isinstance(t, list) else {t} if t else set()


# ---------------------------------------------------------------- the export
# Column names in both generations, from references/shopify-exports-extract.md
# section 1 (Shopify's help pages read 2026-10-21). Matched case-insensitively.
COLUMNS = {
    "handle": ("Handle", "URL handle"),
    "title": ("Title",),
    "description": ("Body (HTML)", "Description"),
    "category": ("Product Category", "Product category"),
    "status": ("Status",),
    "sku": ("Variant SKU", "SKU"),
    "barcode": ("Variant Barcode", "Barcodes", "Variant Barcodes", "Barcode"),
    "image_src": ("Image Src", "Product image URL"),
    "image_alt": ("Image Alt Text", "Image alt text"),
    "option1_name": ("Option1 Name", "Option1 name"),
    "option1_value": ("Option1 Value", "Option1 value"),
    "image_position": ("Image Position", "Image position"),
    "variant_image": ("Variant Image", "Variant image URL"),
    "price": ("Variant Price", "Price"),
    "product_type": ("Type",),
    "tags": ("Tags",),
}

# The image columns, left out of an import file that carries no approved alt
# text (schemas.md section 8; references/shopify-exports-extract.md section 2,
# omitted-column). A header that names an image in any other way is caught by
# IMAGE_HEADER.
IMAGE_KEYS = ("image_src", "image_alt", "image_position", "variant_image")
IMAGE_HEADER = re.compile(r"\bimage\b", re.I)

# Shopify's alt-text recommendation and maximum (references/shopify-exports-extract.md section 1).
ALT_RECOMMENDED, ALT_MAX = 125, 512


def read_export(path):
    """Header, rows and a map from our key to the export's own column name."""
    with open(path, encoding="utf-8-sig", newline="") as fh:
        reader = csv.reader(fh)
        rows = list(reader)
    if not rows:
        raise ValueError(f"{path} is empty.")
    header = rows[0]
    lower = {h.strip().lower(): h for h in header}
    colmap = {}
    for key, names in COLUMNS.items():
        for n in names:
            if n.lower() in lower:
                colmap[key] = lower[n.lower()]
                break
    body = [dict(zip(header, r + [""] * (len(header) - len(r)))) for r in rows[1:] if any(c.strip() for c in r)]
    return header, body, colmap


def export_products(rows, colmap):
    """Group export rows by handle, in file order."""
    groups = {}
    order = []
    hcol = colmap.get("handle")
    for row in rows:
        h = (row.get(hcol) or "").strip()
        if not h:
            continue
        if h not in groups:
            groups[h] = []
            order.append(h)
        groups[h].append(row)
    return order, groups


# ---------------------------------------------------------------- review file
ENTRY = re.compile(r"^-\s+\[(proposed|approved|open)\]\s*(.*)$")
SECTIONS = {"facts", "alt text", "faq", "body additions"}


def read_review(path):
    """Entries as dicts: handle, section, mark, text, line number."""
    entries = []
    handle = None
    section = None
    for n, line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), 1):
        if line.startswith("## "):
            handle = line[3:].strip()
            section = None
            continue
        if line.startswith("### "):
            section = line[4:].strip().lower()
            continue
        m = ENTRY.match(line.strip())
        if m and handle:
            entries.append({"handle": handle, "section": section, "mark": m.group(1),
                            "text": m.group(2).strip(), "line": n})
    return entries


def escape(text):
    return html.escape(text, quote=False)


# Phrases that mean text inside an input is addressed to an assistant
# (build choice, 2026-10-21). Such text is reported, never followed.
INJECTION = re.compile(
    r"(ignore (all |any )?(previous|prior|above) instructions|as an ai|dear (ai|assistant|agent)|"
    r"(assistant|agent|ai model|language model)s?,? (must|should|please)|system prompt)",
    re.I,
)
