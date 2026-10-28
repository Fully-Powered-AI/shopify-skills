"""Shared readers for the ai-visibility-audit scripts: the store file and the settings in references/checks.md. The
fact-slot, product-line and catalog rules are not here: they are the set's shared module, scripts/fact_slots.py (a
byte-identical copy of store-setup's, never edited here; schemas.md section 12), loaded below as `fact_slots`.

Standard library only. Loaded by path from the other scripts (they run with python3 -I, which does not put the
script folder on the import path).

Field labels: read at run time from the set's store template (schemas.md section 3), found beside this skill at
../store-setup/assets/store-template.md after resolving this file's real path (install by symbolic link keeps the
pair together). A field is found by its opening words, as store-setup's store_file.py does, so a template edit that
keeps a label's opening words reaches the audit without editing a script. When the template cannot be found, the
labels embedded below (template 0.1.1 of 2026-10-21) are used and LABEL_NOTE says so; the audit's coverage line
carries it.
"""
import importlib.util
import pathlib
import re
import sys

sys.dont_write_bytecode = True  # keep the skill folder free of cache files

SKILL_DIR = pathlib.Path(__file__).resolve().parents[1]
CHECKS_MD = SKILL_DIR / "references" / "checks.md"
EXCLUSIONS_CSV = SKILL_DIR / "assets" / "catalog-exclusions-2026-10-21.csv"
STORE_TEMPLATE = SKILL_DIR.parent / "store-setup" / "assets" / "store-template.md"

_fs_spec = importlib.util.spec_from_file_location("fact_slots", pathlib.Path(__file__).resolve().parent / "fact_slots.py")
fact_slots = importlib.util.module_from_spec(_fs_spec)
_fs_spec.loader.exec_module(fact_slots)

# Each field the scripts read: (section, the label's opening words). The opening words are matched against the
# template's labels at run time.
FIELDS = {
    "store_name": (1, "Store name"),
    "domain": (1, "Public domain"),
    "product_lines": (2, "Product lines"),
    "search_words": (2, "The words buyers use"),
    "fact_slots": (2, "The facts every product page states"),
    "questions": (4, "The questions buyers ask before buying"),
    "prompts": (4, "Answer-check prompts"),
    "faq_pages": (6, "FAQ or buying-guide pages"),
    "contact_email": (6, "Public contact email"),
    "barriers": (6, "Popups, age gates or password pages"),
    "ai_tool": (5, "The AI tool the person uses"),
    "answer_cadence": (9, "Answer-check cadence"),
    "alt_required": (9, "Every product image carries alt text"),
    "sample_size": (9, "Product pages sampled per audit"),
    "category_status": (10, "The product category checked against the Catalog exclusion list"),
}
# Fields a store file written to an earlier template may lack; a missing line reads as blank, never as an error.
OPTIONAL = {"prompts"}
# Fallback labels, verbatim from store template 0.1.1, used only when the template file is not found.
EMBEDDED_LABELS = {
    1: ["Store name:", "Public domain, as `https://...`:"],
    2: ["Product lines, one per indented line: the line's name, what it is, who it is for, and the Shopify product category it sits in:",
        "The words buyers use for the category and the products (the search words), one per indented line:",
        "The facts every product page states (the fact slots), one per indented line: the slot's name, and where the fact comes from (label, specification sheet, the person):"],
    4: ["The questions buyers ask before buying, five to ten, in the buyer's own words, one per indented line (this is the answer-check list):",
        "Answer-check prompts (optional), the questions above as a buyer would type them into an assistant that knows nothing about the store, naming the kind of product and the need but no brand, one per indented line; when blank, the answer check uses the questions above with a short opening:"],
    5: ["The AI tool the person uses (for example Claude, ChatGPT), and whether it is connected to the store through Shopify's connector for that tool:"],
    6: ["FAQ or buying-guide pages, one per indented line with the URL, or `none`:",
        "Public contact email for buyers and agents, the role that reads it, and the reply-time target:",
        "Popups, age gates or password pages on the storefront, one per indented line (what it is and where it shows), or `none`:"],
    9: ["Answer-check cadence [default monthly]:", "Every product image carries alt text [default yes]:",
        "Product pages sampled per audit [default 5]:"],
    10: ["The product category checked against the Catalog exclusion list (`references/ai-channels.md` section 2): `eligible`, `excluded` or `unknown`, with the date:"],
}
MARK = re.compile(r"\s*\[(owner|observed|default|open)\]\s*$")


def read_template_labels(path=STORE_TEMPLATE):
    """Labels by section number from the store template: top-level bullets whose text ends with a colon."""
    labels, cur = {}, None
    for line in pathlib.Path(path).read_text(encoding="utf-8").splitlines():
        m = re.match(r"^## (\d+)\. ", line)
        if m:
            cur = int(m.group(1))
            labels[cur] = []
        elif cur is not None and line.startswith("- ") and line.rstrip().endswith(":"):
            labels[cur].append(" ".join(line[2:].split()))
    return labels


try:
    LABELS = read_template_labels()
    LABEL_NOTE = ""
except OSError:
    LABELS = EMBEDDED_LABELS
    LABEL_NOTE = (f"store template not found at {STORE_TEMPLATE}; the store file was read with the labels of "
                  "template 0.1.1 (2026-10-21) carried in scripts/common.py")


class StoreFileError(Exception):
    """A store file problem the person must fix; the message is one plain sentence."""


class Field:
    def __init__(self, value, mark, items):
        self.value = value          # text on the field's own line, mark removed ('' when blank)
        self.mark = mark            # owner, observed, default, open, or None
        self.items = items          # [(text, mark)] from marked indented lines

    def is_open(self):
        return self.mark == "open" and not self.value and not self.items

    def is_blank(self):
        return not self.value and not self.items and self.mark != "open"

    def values(self):
        """List values: marked detail lines that are not [open]; else the field's own value when it is not 'none'."""
        out = [t for t, m in self.items if m != "open" and t]
        if not out and self.value and self.value.lower() != "none" and self.mark != "open":
            out = [self.value]
        return out

    def is_none(self):
        return self.value.strip().lower().startswith("none") and not self.items


class StoreFile:
    def __init__(self, path):
        self.path = pathlib.Path(path)
        if not self.path.is_file():
            raise StoreFileError(f"There is no store file at {self.path}; run store-setup with the store owner first.")
        self.lines = self.path.read_text(encoding="utf-8").splitlines()
        self.sections = {}
        cur = None
        for line in self.lines:
            m = re.match(r"^## (\d+)\. ", line)
            if m:
                cur = int(m.group(1))
                self.sections[cur] = []
                continue
            if cur is not None:
                self.sections[cur].append(line)

    def field(self, key):
        sec, opening = FIELDS[key]
        if sec not in self.sections:
            raise StoreFileError(f"The store file has no section {sec}; restore its headings from the template.")
        labels = LABELS.get(sec, [])
        lines = self.sections[sec]
        for i, line in enumerate(lines):
            if not line.startswith("- "):
                continue
            text = " ".join(line[2:].split())
            label = max((l for l in labels if text.startswith(l)), key=len, default=None)
            if label is None or not label.startswith(opening):
                continue
            rest = text[len(label):]
            mark = None
            m = MARK.search(rest)
            if m:
                mark = m.group(1)
                rest = rest[:m.start()]
            items = []
            for nxt in lines[i + 1:]:
                if not nxt.startswith("  "):
                    break
                s = nxt.strip()
                if s.startswith("- "):
                    s = s[2:]
                mm = MARK.search(s)
                if mm:  # unmarked indented lines are template guidance
                    items.append((s[:mm.start()].strip(), mm.group(1)))
            return Field(rest.strip(), mark, items)
        if key in OPTIONAL:
            return Field("", None, [])
        raise StoreFileError(f"Store file section {sec} lacks the line starting \"{opening}\"; restore it from the template.")

    def require(self, key):
        f = self.field(key)
        if f.is_blank():
            sec, opening = FIELDS[key]
            raise StoreFileError(f"Store file section {sec}, \"{opening}\", is blank; fill it with store-setup and run again.")
        return f


def read_settings(path=CHECKS_MD):
    """Return (settings dict, lists dict, tables dict) from the fenced blocks in references/checks.md."""
    text = pathlib.Path(path).read_text(encoding="utf-8")
    settings, lists, tables = {}, {}, {}
    for kind, name, body in re.findall(r"```(settings|list|table) ?(\S*)\n(.*?)\n```", text, re.S):
        rows = [l.strip() for l in body.splitlines() if l.strip()]
        if kind == "settings":
            for r in rows:
                k, v = r.split(":", 1)
                v = v.strip()
                settings[k.strip()] = int(v) if re.fullmatch(r"-?\d+", v) else v
        elif kind == "list":
            lists[name] = rows
        else:
            tables[name] = [r.split() for r in rows]
    return settings, lists, tables


def host_of(url):
    m = re.match(r"^(?:https?://)?([^/?#]+)", url.strip(), re.I)
    return m.group(1).lower() if m else ""


def same_domain(a, b):
    """Hosts that differ only by a leading www. are one domain."""
    strip = lambda h: h[4:] if h.startswith("www.") else h
    return strip(a.lower()) == strip(b.lower())
