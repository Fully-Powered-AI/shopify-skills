"""Reads the store file, store/store.md, by section number and field label.

Shared by guide_check.py and product_index.py, which load it by path (python3 -I
does not put the script folder on the import path). Product-line items are parsed by
the set's shared module fact_slots.py (references/schemas.md section 12), loaded the
same way; this reader never parses an item by a rule of its own. The parsing follows the rules in
the set's schemas.md section 3: a field is a bullet whose template text ends with a
colon, the value follows on the same line, the source mark is last; marked indented
lines under a field are the person's detail, unmarked ones are template guidance.

Field labels are taken at run time from the store-setup skill's template when that
skill sits beside this one; otherwise from the copy in LABELS below, which is the
template version 0.1.1 of 2026-10-21. A template change therefore reaches this reader
when the set is installed together.
"""
import importlib.util
import pathlib
import re
import sys

sys.dont_write_bytecode = True  # leave no cache files in the skill folder
_HERE = pathlib.Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("fact_slots", _HERE / "fact_slots.py")
fact_slots = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(fact_slots)

MARK = re.compile(r"\s*\[(owner|observed|default|open)\]\s*$")
SECTION = re.compile(r"^## (\d+)\.\s")

# Opening words -> full template text of the field line (template 0.1.1, 2026-10-21).
LABELS = {
    "Store name": "Store name:",
    "Public domain": "Public domain, as `https://...`:",
    "Countries sold to": "Countries sold to and shipped to:",
    "The business in one line": "The business in one line, in the person's own words:",
    "Product lines": "Product lines, one per indented line: the line's name, what it is, who it is for, and the Shopify product category it sits in:",
    "The words buyers use": "The words buyers use for the category and the products (the search words), one per indented line:",
    "The facts every product page states": "The facts every product page states (the fact slots), one per indented line: the slot's name, and where the fact comes from (label, specification sheet, the person):",
    "Statements the store makes": "Statements the store makes about its products and has cleared, verbatim, one per indented line with the product or line it applies to; a statement not here is \"ask\":",
    "Statements the store never makes": "Statements the store never makes, one per indented line, with the reason:",
    "Words, topics and comparisons": "Words, topics and comparisons the brand does not use (the redlines), one per indented line:",
    "Comparisons to named competitors allowed": "Comparisons to named competitors allowed [default no]:",
    "Who buys": "Who buys, in plain words:",
    "The questions buyers ask": "The questions buyers ask before buying, five to ten, in the buyer's own words, one per indented line (this is the answer-check list):",
    "Answer-check prompts": "Answer-check prompts (optional), the questions above as a buyer would type them into an assistant that knows nothing about the store, naming the kind of product and the need but no brand, one per indented line; when blank, the answer check uses the questions above with a short opening:",
    "Policy pages published": "Policy pages published, one per indented line with the URL (shipping, refund, privacy, terms):",
    "FAQ or buying-guide pages": "FAQ or buying-guide pages, one per indented line with the URL, or `none`:",
    "Public contact email": "Public contact email for buyers and agents, the role that reads it, and the reply-time target:",
    "Who pastes theme files": "Who pastes theme files such as the agent guide (role):",
}


class StoreFileError(Exception):
    pass


def _labels_from_template():
    here = pathlib.Path(__file__).resolve()
    tpl = here.parents[2] / "store-setup" / "assets" / "store-template.md"
    labels = dict(LABELS)
    if not tpl.exists():
        return labels, "embedded copy (template 0.1.1)"
    lines = [l[2:].rstrip() for l in tpl.read_text(encoding="utf-8").splitlines() if l.startswith("- ")]
    for key in LABELS:
        for l in lines:
            if l.startswith(key):
                labels[key] = l
                break
    return labels, "the store-setup template beside this skill"


class Field:
    def __init__(self, value, mark, details):
        self.value = value          # text after the label, mark removed ("" when blank)
        self.mark = mark            # owner, observed, default, open, or None
        self.details = details      # [(text, mark)] from marked indented lines

    @property
    def is_open(self):
        return self.mark == "open" and not self.value and not self.details

    @property
    def is_blank(self):
        return not self.value and not self.details and self.mark is None

    def items(self):
        """The list the field carries: marked indented lines, else the field's own value."""
        if self.details:
            return [t for t, _ in self.details]
        if self.value and self.value.lower() != "none":
            return [self.value]
        return []


class StoreFile:
    def __init__(self, path):
        self.path = pathlib.Path(path)
        if not self.path.exists():
            raise StoreFileError(f"There is no store file at {self.path}; run store-setup first.")
        self.labels, self.label_source = _labels_from_template()
        self.sections = {}
        current = None
        for line in self.path.read_text(encoding="utf-8").splitlines():
            m = SECTION.match(line)
            if m:
                current = int(m.group(1))
                self.sections[current] = []
                continue
            if current is not None:
                self.sections[current].append(line)

    def field(self, section, key):
        if section not in self.sections:
            raise StoreFileError(f"The store file has no section {section}; it was not made from the template.")
        label = self.labels[key]
        lines = self.sections[section]
        for i, line in enumerate(lines):
            if line.startswith("- ") and line[2:].startswith(label):
                rest = line[2 + len(label):]
                mark = None
                mm = MARK.search(rest)
                if mm:
                    mark = mm.group(1)
                    rest = rest[:mm.start()]
                details = []
                for nxt in lines[i + 1:]:
                    if not nxt.strip():
                        continue
                    if not nxt[0].isspace():
                        break
                    dm = MARK.search(nxt)
                    if dm:
                        text = nxt[:dm.start()].strip()
                        if text.startswith("- "):
                            text = text[2:].strip()
                        details.append((text, dm.group(1)))
                return Field(rest.strip(), mark, details)
        raise StoreFileError(f"Section {section} of the store file lacks the field \"{label}\"; the template text was edited.")


def product_lines(store):
    """Section 2's product-line items, parsed by fact_slots.parse_lines ('same category' resolved).

    Each item is {"name", "what", "category", "category_from", "problem"}; "problem" is set when the
    item is not in the template's shape (no colon after the name, no category part)."""
    return fact_slots.parse_lines(store.field(2, "Product lines").items())


def line_names(store):
    """Product line names from section 2: the name before the colon, as fact_slots reads it."""
    return [l["name"] for l in product_lines(store) if l["name"]]


def line_problems(store):
    """Items not in the template's shape, as (name, problem) pairs; store-setup is the skill that fixes them."""
    return [(l["name"] or l["entry"], l["problem"]) for l in product_lines(store) if l["problem"]]
