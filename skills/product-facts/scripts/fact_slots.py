#!/usr/bin/env python3
"""One reading of store file section 2 for every skill in the set: fact slots, product lines, catalog eligibility.

Why one module: on 2026-10-21 the audit (V13) and the gap table (product-facts) read the same product page and
disagreed about which facts it states, because each carried its own matcher. This module is the single rule, written
down in references/schemas.md section 12. The source of truth is skills/store-setup/scripts/fact_slots.py; every
other skill carries a byte-identical copy in its scripts/ folder so that a skill folder still runs on its own, and
Keep every copy byte-identical to the store-setup original.

Python 3 standard library only. No network. Import by path or run the built-in cases:
    python3 -I fact_slots.py --self-test

What it reads and returns:
  parse_slot(entry)      -> {"name", "options", "source"}       a fact-slot line, section 2
  slot_found(slot, page_tokens) -> bool                         the match rule, section 12 of schemas.md
  slot_wording_note(missing, total) -> str                      "check the slot's wording first" when it is missing on most
  parse_lines(entries)   -> [{"name", "what", "category", "category_from", "problem", "entry"}]   product-line items, section 2
                            ("entry" is the item's text as written, for a message about an item with no name)
  line_of(lines, title, handle, product_type, tags, category) -> {"kind", "lines", "where"}
  read_exclusions(path)  -> rows of the dated exclusions list (assets/catalog-exclusions-YYYY-MM-DD.csv)
  catalog_status(category_path, rows) -> {"status", "matches"}  eligible, excluded or unknown, a word match only
Errors: read_exclusions raises ExclusionsError (a ValueError) for a header other than the five columns, and lets a
missing file raise FileNotFoundError; callers print one plain sentence and exit 1.
Every list below is a build choice of 2026-10-21, marked [build]; the owner changes a match by writing the page's
wording as an option on the slot line, never by editing this file. The self-test's stores and products are invented.
"""
import argparse
import csv
import os
import re
import sys
import tempfile

VERSION = "0.1.1"  # 2026-10-21; 0.1.0 the same day

# Words in a slot or line name that carry no fact [build].
STOP = {
    "a", "an", "and", "or", "the", "of", "in", "on", "for", "to", "with", "by",
    "from", "is", "it", "its", "as", "per", "what", "how", "each", "every",
}
# Suffixes stripped, longest first, so "compatibility" meets "compatible" and "ounces" meets "ounce" [build].
SUFFIXES = ("ibility", "ability", "ility", "ities", "ing", "ies", "es", "ed", "ty", "s")
# Words that state the same kind of fact: a page saying "dishwasher safe" states dishwasher compatibility [build].
QUALIFIER_GROUPS = (
    {"compatibility", "compatible", "safe", "safety", "friendly"},
)
# Units and their abbreviations; a slot whose name holds a unit word is found by a stated quantity, a number followed
# by the unit or its abbreviation ("8 oz", "8oz", "8 fl oz") [build]. "inch" is left out: "in" is a stop word.
UNITS = {
    "ounce": ("oz",), "milliliter": ("ml",), "liter": ("l", "ltr"), "gram": ("g",), "kilogram": ("kg",),
    "milligram": ("mg",), "pound": ("lb", "lbs"), "gallon": ("gal",), "centimeter": ("cm",), "millimeter": ("mm",),
    "minute": ("min", "mins"), "hour": ("hr", "hrs"), "count": ("ct", "pcs", "pieces", "pack"),
}
# Tokens that may sit between a number and its unit ("8 fl oz") [build].
UNIT_BRIDGE = {"fl", "fluid", "net", "wt"}


class ExclusionsError(ValueError):
    """The exclusions file does not have the five columns category, examples, terms, source, date."""


def tokens(text):
    """Lowercase word and number tokens, in order."""
    return re.findall(r"[a-z0-9]+", (text or "").lower())


def stem(word):
    for suf in SUFFIXES:
        if word.endswith(suf) and len(word) - len(suf) >= 3:
            return word[: -len(suf)]
    return word


# ---------------------------------------------------------------- fact slots

def parse_slot(entry):
    """'base (ceramic, glass, steel), from the label' -> name 'base', options ['ceramic', 'glass', 'steel'], source 'the label'.

    Options are the text in parentheses, split at ',' and ';' only, so 'hand wash only' stays one phrase. The source is
    the text after a final ', from '."""
    source = ""
    m = re.search(r",\s*from\s+(.+)$", entry, re.I)
    body = entry[: m.start()] if m else entry
    if m:
        source = m.group(1).strip()
    options = []
    pm = re.search(r"\(([^)]*)\)", body)
    if pm:
        options = [o.strip() for o in re.split(r"[,;]", pm.group(1)) if o.strip()]
        body = body[: pm.start()] + body[pm.end():]
    name = re.sub(r"\s+", " ", body).strip(" ,:")
    return {"name": name, "options": options, "source": source}


def _unit_forms(word):
    """The forms a stated quantity may use for a unit word in a slot name, or an empty set."""
    base = word[:-2] if word.endswith("es") and word[:-2] in UNITS else word[:-1] if word.endswith("s") and word[:-1] in UNITS else word
    if base not in UNITS:
        return set()
    return {base, base + "s", base + "es"} | set(UNITS[base])


def _quantity_stated(page_tokens, forms):
    n = len(page_tokens)
    for i, t in enumerate(page_tokens):
        if t.isdigit():
            j = i + 1
            if j < n and page_tokens[j] in UNIT_BRIDGE:
                j += 1
            if j < n and page_tokens[j] in forms:
                return True
        m = re.fullmatch(r"\d+([a-z]+)", t)
        if m and m.group(1) in forms:
            return True
    return False


def slot_found(slot, page_tokens):
    """The rule of schemas.md section 12. page_tokens is the page's token list in order (tokens(text)).

    Found when (a) every content word of the slot name appears, a word matching by stem prefix and a qualifier word
    by any word of its group; or (b) one option appears whole, every word of it; or (c) the name holds a unit word
    and the page states a quantity in that unit."""
    text_tokens = set(page_tokens)
    words = [w for w in tokens(slot["name"]) if w not in STOP]

    def has(word):
        group = next((g for g in QUALIFIER_GROUPS if word in g), {word})
        stems = {stem(g) for g in group}
        return any(t.startswith(s) for s in stems for t in text_tokens)

    if words and all(has(w) for w in words):
        return True
    for opt in slot["options"]:
        ot = tokens(opt)
        if ot and all(o in text_tokens for o in ot):
            return True
    forms = set()
    for w in words:
        forms |= _unit_forms(w)
    if forms and _quantity_stated(page_tokens, forms):
        return True
    return False


def slot_wording_note(missing, total):
    """A fixed sentence when a slot is missing on more than half of the pages or descriptions read; else ''."""
    if total and missing * 2 > total:
        return "check the slot's wording first: missing on most pages read; a page may state it in other words, which go in parentheses on the slot line"
    return ""


# ---------------------------------------------------------------- product lines

CATEGORY = re.compile(r"(?:^|[;,]\s*)(?:shopify\s+)?(?:product\s+)?category\s*:?\s+(.+)$", re.I)
SAME_CATEGORY = re.compile(r"\bsame category\b", re.I)


def parse_line(entry, previous_category=""):
    """'Breakfast: a plain black tea, for everyday drinking; category Food, Beverages & Tobacco > Beverages > Tea' ->
    name 'Breakfast', what 'a plain black tea, for everyday drinking', category 'Food, Beverages & Tobacco > Beverages > Tea'.

    'same category' takes the line above's. An item with no colon has an empty name and a problem, so no skill matches
    a sentence as a line name; each caller reports the problem the same way."""
    problem = ""
    if ":" in entry:
        name, rest = entry.split(":", 1)
    else:
        name, rest = "", entry
        problem = "no colon after the line's name"
    cm = CATEGORY.search(rest)
    if cm:
        category, category_from = cm.group(1).strip().rstrip(". "), "stated"
        rest = rest[: cm.start()]
    elif SAME_CATEGORY.search(rest):
        category, category_from = previous_category, "same"
        rest = SAME_CATEGORY.sub("", rest)
        if not previous_category:
            problem = problem or "'same category' on a line with no category above it"
    else:
        category, category_from = "", ""
        problem = problem or "no 'category <path>' or 'same category' part"
    what = re.sub(r"\s+", " ", rest).strip(" ;,")
    return {"name": name.strip(), "what": what, "category": category, "category_from": category_from, "problem": problem,
            "entry": entry.strip()}


def parse_lines(entries):
    out, prev = [], ""
    for e in entries:
        line = parse_line(e, prev)
        prev = line["category"] or prev
        out.append(line)
    return out


def _slug(s):
    return re.sub(r"[^a-z0-9]+", "-", (s or "").lower()).strip("-")


def _reduce(hits):
    """A longer name that contains a shorter one ('Breakfast Blend' over 'Breakfast') wins."""
    if len(hits) > 1:
        longest = max(len(h) for h in hits)
        top = [h for h in hits if len(h) == longest]
        if len(top) == 1 and all(h.lower() in top[0].lower() for h in hits):
            return top
    return hits


def _in_text(text, names):
    return _reduce([n for n in names if text and re.search(r"(?<![\w-])" + re.escape(n) + r"(?![\w-])", text, re.I)])


def _in_handle(handle, names):
    h = "-" + _slug(handle) + "-"
    return _reduce([n for n in names if _slug(n) and "-" + _slug(n) + "-" in h])


def _last_segment(path):
    return (path or "").split(">")[-1].strip().lower()


def line_of(lines, title="", handle="", product_type="", tags=(), category=""):
    """Which product line a product belongs to. Returns {"kind": one|suggested|several|none, "lines": [...], "where": str}.

    Strong signals, in order: the handle, the title, the product type. Two strong signals that name different lines
    give 'several'. A product type alone, a tag, or the category's last segment gives 'suggested' (the owner confirms).
    A line name is matched whole, between word boundaries, so 'Oolong' is not found in 'oolong-style'."""
    names = [l["name"] for l in lines if l.get("name")]
    signals = [("handle", _in_handle(handle, names)), ("title", _in_text(title, names)),
               ("product type", _in_text(product_type, names))]
    strong = [(w, h) for w, h in signals if h]
    if strong:
        for i, (w1, h1) in enumerate(strong):
            for w2, h2 in strong[i + 1:]:
                if not set(h1) & set(h2):
                    return {"kind": "several", "lines": sorted(set(h1) | set(h2)),
                            "where": "; ".join(f"{w}: {', '.join(h)}" for w, h in strong)}
        where, hits = strong[0]
        if len(hits) > 1:
            return {"kind": "several", "lines": hits, "where": where}
        if where == "product type":
            return {"kind": "suggested", "lines": hits, "where": where}
        return {"kind": "one", "lines": hits, "where": where}
    tag_hits = _reduce(sorted({n for t in (tags or ()) for n in _in_text(t, names)}))
    if len(tag_hits) == 1:
        return {"kind": "suggested", "lines": tag_hits, "where": "tags"}
    if tag_hits:
        return {"kind": "several", "lines": tag_hits, "where": "tags"}
    seg = _last_segment(category)
    if seg:
        cat_hits = [l["name"] for l in lines if l.get("name") and l.get("category") and _last_segment(l["category"]) == seg]
        if len(cat_hits) == 1:
            return {"kind": "suggested", "lines": cat_hits, "where": "category"}
        if cat_hits:
            return {"kind": "several", "lines": sorted(cat_hits), "where": "category"}
    return {"kind": "none", "lines": [], "where": ""}


# ---------------------------------------------------------------- catalog eligibility

EXCLUSIONS_COLUMNS = ("category", "examples", "terms", "source", "date")


def read_exclusions(path):
    """Rows of assets/catalog-exclusions-YYYY-MM-DD.csv: category, examples, terms, source, date (lists split at ';').

    Raises ExclusionsError when the header is not exactly the five columns; a missing file raises FileNotFoundError."""
    rows = []
    with open(path, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames or set(reader.fieldnames) != set(EXCLUSIONS_COLUMNS):
            raise ExclusionsError(f"{path}: header must be {','.join(EXCLUSIONS_COLUMNS)}; found {reader.fieldnames}")
        for r in reader:
            rows.append({"category": r["category"].strip(),
                         "examples": [x.strip() for x in r["examples"].split(";") if x.strip()],
                         "terms": [x.strip() for x in r["terms"].split(";") if x.strip()],
                         "source": r["source"].strip(), "date": r["date"].strip()})
    return rows


def _norm(text):
    text = (text or "").lower().replace("&", " and ")
    return " ".join(tokens(text))


def _singular(phrase):
    return " ".join(w[:-1] if len(w) > 3 and w.endswith("s") and not w.endswith("ss") else w for w in phrase.split())


def _same(a, b):
    return a == b or _singular(a) == _singular(b)


def _phrase_in(phrase, text):
    return re.search(r"(?<!\w)" + re.escape(phrase) + r"(?!\w)", text) is not None


def catalog_status(category_path, rows):
    """A word match of a product category path against the dated exclusions list; never Shopify's ruling.

    Each segment of the path (split at '>') is compared on its own. A segment matches a row when it equals the row's
    category, a term or an example (plural or singular); when a term or example of two words or more appears whole
    inside the segment; or when the segment, of two words or more, appears whole inside the row's category or an
    example. A one-word term matches only a segment equal to it, so 'Food, Beverages and Tobacco' does not match
    'tobacco' while 'Tobacco Products' matches the example. One matching segment excludes the path (a subcategory
    of an excluded category is excluded)."""
    if not (category_path or "").strip():
        return {"status": "unknown", "matches": []}
    matches = []
    for raw in category_path.split(">"):
        seg = _norm(raw)
        if not seg:
            continue
        seg_words = len(seg.split())
        for row in rows:
            cat = _norm(row["category"])
            phrases = [cat] + [_norm(x) for x in row["terms"] + row["examples"]]
            hit = None
            for p in phrases:
                if not p:
                    continue
                if _same(seg, p):
                    hit = p
                    break
                if len(p.split()) >= 2 and _phrase_in(p, seg):
                    hit = p
                    break
            if hit is None and seg_words >= 2:
                for p in [cat] + [_norm(x) for x in row["examples"]]:
                    if _phrase_in(seg, p):
                        hit = p
                        break
            if hit is not None:
                matches.append(f"'{raw.strip()}' matches '{hit}' in the excluded category {row['category']}")
                break
    return {"status": "excluded" if matches else "eligible", "matches": matches}


# ---------------------------------------------------------------- self-test

def self_test():
    """Built-in cases on an invented tea and kitchenware store: the shapes the 2026-10-21 reviews found wrong under the
    old matchers. Exit 0 when all hold."""
    fails = []

    def check(name, cond):
        if not cond:
            fails.append(name)

    rinse = tokens("A ceramic mug. Size: small or large. Hot water rinse. Soap sold separately.")
    cleanup = parse_slot("cleanup (dishwasher safe, hand wash only), from the label")
    check("cleanup not found on a page that only mentions water and soap", not slot_found(cleanup, rinse))
    check("cleanup found by its option whole", slot_found(cleanup, tokens("Care: dishwasher safe on the top rack.")))
    size = parse_slot("size in ounces, from the label")
    check("size slot not found by a size selector", not slot_found(size, rinse))
    check("size found by 8 oz", slot_found(size, tokens("Net 8 oz tin")))
    check("size found by 8oz", slot_found(size, tokens("8oz")))
    check("size found by 3.5 fl oz", slot_found(size, tokens("3.5 fl oz")))
    base = parse_slot("base (ceramic, glass, steel), from the label")
    check("base not found when neither name nor option appears", not slot_found(base, tokens("a clear gel in a tube")))
    check("base found by its option glass", slot_found(base, tokens("a glass infuser")))
    check("dishwasher compatibility found via safe", slot_found(parse_slot("dishwasher compatibility, from the label"),
                                                             tokens("Dishwasher Safe (Top Rack Only)")))
    check("compatible meets compatibility", slot_found(parse_slot("microwave compatibility, from the label"),
                                                       tokens("microwave compatible lid")))
    cooktop = parse_slot("induction cooktop compatibility, from the label")
    check("induction cooktop compatibility not found by induction safe alone", not slot_found(cooktop, tokens("oven safe, induction safe")))
    check("induction cooktop compatibility found by its option",
          slot_found(parse_slot("induction cooktop compatibility (induction safe), from the label"), tokens("oven safe, induction safe")))
    check("wording note when missing on most", slot_wording_note(3, 4) != "" and slot_wording_note(1, 4) == "")

    lines = parse_lines([
        "Breakfast: a plain black tea, for everyday drinking; category Food, Beverages & Tobacco > Beverages > Tea & Infusions",
        "Sencha: a steamed green tea, for people who want a light cup; same category",
        "Chai: a spiced black tea, same category",
        "Oolong: a partly oxidized tea, same category",
    ])
    check("line name before the colon", lines[0]["name"] == "Breakfast" and lines[0]["what"].startswith("a plain black tea"))
    check("same category resolves", lines[1]["category"] == lines[0]["category"] and lines[3]["category_from"] == "same")
    no_colon = parse_line("Chai a spiced black tea")
    check("line without a colon has an empty name and a problem", no_colon["name"] == "" and no_colon["problem"] != "")
    check("line without category flagged", parse_line("Rooibos: a red bush infusion")["problem"] != "")
    check("handle beats title", line_of(lines, title="Green Tea with Lemon", handle="harborline-sencha-8-oz")["lines"] == ["Sencha"])
    check("oolong-style does not name Oolong", line_of(lines, title="Harborline Breakfast oolong-style blend", handle="breakfast-9-oz")["lines"] == ["Breakfast"])
    check("handle and title disagree gives several",
          line_of(lines, title="Harborline Chai Spiced", handle="copy-of-harborline-breakfast-25-oz")["kind"] == "several")
    check("type alone is suggested", line_of(lines, title="Travel tin", handle="travel-tin", product_type="Sencha grade")["kind"] == "suggested")
    check("tag alone is suggested", line_of(lines, title="Gift box", handle="gift-box", tags=["Chai", "gift"])["kind"] == "suggested")
    check("no line is none", line_of(lines, title="Logo T-shirt", handle="logo-tee")["kind"] == "none")
    check("an unnamed item is never matched", line_of(parse_lines(["Chai a spiced black tea"]), title="Chai Spiced", handle="chai")["kind"] == "none")

    rows = [
        {"category": "Tobacco and vaping", "examples": ["tobacco products", "vaporizers", "e-cigarettes", "e-liquid"],
         "terms": ["tobacco", "vaping"], "source": "", "date": ""},
        {"category": "Sexual health and wellness products", "examples": ["condoms", "spermicides", "personal lubricants"],
         "terms": ["sexual health", "sexual wellness"], "source": "", "date": ""},
        {"category": "Services and product add-ons", "examples": ["professional services"], "terms": ["services", "product add-ons"],
         "source": "", "date": ""},
    ]
    check("tea under Food, Beverages & Tobacco is eligible",
          catalog_status("Food, Beverages & Tobacco > Beverages > Tea & Infusions", rows)["status"] == "eligible")
    check("tobacco products excluded", catalog_status("Food, Beverages & Tobacco > Tobacco Products > Cigars", rows)["status"] == "excluded")
    check("personal lubricants excluded",
          catalog_status("Health & Beauty > Personal Care > Sexual Wellness > Personal Lubricants", rows)["status"] == "excluded")
    check("a one-word segment equal to a term is excluded", catalog_status("Services", rows)["status"] == "excluded")
    check("professional services excluded by whole-segment phrase", catalog_status("Services > Professional Services", rows)["status"] == "excluded")
    check("empty category is unknown", catalog_status("", rows)["status"] == "unknown")
    check("singular and plural meet", catalog_status("Condom", rows)["status"] == "excluded")

    fd, tmp = tempfile.mkstemp(suffix=".csv")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as f:
            f.write("category,examples,source,date\nAlcohol,beer,x,2026-10-21\n")
        try:
            read_exclusions(tmp)
            check("old four-column header raises ExclusionsError", False)
        except ExclusionsError:
            pass
        with open(tmp, "w", encoding="utf-8", newline="") as f:
            f.write("category,examples,terms,source,date\nAlcohol,alcoholic beverages;homebrewing,alcohol,x,2026-10-21\n")
        got = read_exclusions(tmp)
        check("five-column file reads with split lists", len(got) == 1 and got[0]["examples"] == ["alcoholic beverages", "homebrewing"] and got[0]["terms"] == ["alcohol"])
    finally:
        os.unlink(tmp)
    try:
        read_exclusions(tmp + ".missing")
        check("missing file raises FileNotFoundError", False)
    except FileNotFoundError:
        pass

    for f in fails:
        print("FAIL " + f)
    print(f"fact_slots {VERSION} self-test: {len(fails)} failure(s)")
    return 1 if fails else 0


def main(argv=None):
    ap = argparse.ArgumentParser(description="Shared matcher for store file section 2; run --self-test.")
    ap.add_argument("paths", nargs="*", help="ignored; present so a fixture runner may pass a workspace")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args(argv)
    if a.self_test:
        return self_test()
    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
