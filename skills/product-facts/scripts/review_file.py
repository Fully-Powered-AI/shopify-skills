#!/usr/bin/env python3
"""Write the skeleton of the review file, products/facts-<date>.md.

Usage:
  python3 -I scripts/review_file.py <workspace> --date YYYY-MM-DD [--handles h1,h2] [--export exports/products-YYYY-MM-DD.csv]
  python3 -I scripts/review_file.py <workspace> --date YYYY-MM-DD --check

Reads products/gaps-<date>.csv (written by product_gaps.py), the store file
(sections 1, 2, 3, 4, 7) and, for image sources, pages/<date>/products/<handle>.json
or the export. Writes one block per product in the shape of schemas.md
section 8, from assets/facts-template.md: the missing slots with their
sources, the images without alt text by src, the buyer questions, the
structured-data gaps with where each is fixed (references/facts-and-alt-text.md
section 5), and empty [proposed] lines for the model to fill.

Default handles: every product in the gap table with at least one gap that
is in a product line of store file section 2 (the gap table notes the
others "not in a product line"; name one with --handles to include it).
The output and the file's coverage text account for every product in the
gap table with counts: in the file; fine (in a product line, every slot in
the description and no known gap; named, no block); left out (not in a
product line). Alt status unknown is named under inputs missing for every
product it applies to, in the file or fine.
Refuses to overwrite a review file that already has [approved] lines.

With --check it reads the drafted file instead and flags fact and FAQ lines
whose source names no known kind (label, spec, page, owner or cleared,
anywhere in the source, or the slot's own source), empty values, alt text
over Shopify's recommended length, and the store's redline words (exit 0
clean, 2 flagged).

Exit codes: 0 written; 1 bad input (one sentence says what to fix); 2 written
but partial (alt text unknown for some products, store file section 4 has no
buyer questions, or section 7 names no approver). Reads workspace files only;
never calls the network.
"""

import argparse
import csv
import datetime
import json
import re
import sys
from pathlib import Path

sys.dont_write_bytecode = True  # keep the skill folder free of cache files
sys.path.insert(0, str(Path(__file__).resolve().parent))
import fact_slots  # noqa: E402
import shared  # noqa: E402

HERE = Path(__file__).resolve().parent
TEMPLATE = HERE.parent / "assets" / "facts-template.md"
GAP_TABLE = HERE.parent / "references" / "facts-and-alt-text.md"


def fail(msg):
    print("RESULT: BAD INPUT")
    print(msg)
    sys.exit(1)


def gap_lines():
    """Rows of the section 5 table, keyed by gap id."""
    rows = {}
    in_table = False
    for line in GAP_TABLE.read_text(encoding="utf-8").splitlines():
        if line.startswith("## 5."):
            in_table = True
            continue
        if in_table and line.startswith("## "):
            break
        if in_table and line.startswith("| ") and not line.startswith("| gap ") and not line.startswith("|---"):
            cells = [c.strip() for c in line.strip("|").split("|")]
            if len(cells) >= 5:
                rows[cells[0]] = {"where": cells[2], "who": cells[3], "import": cells[4]}
    return rows


SOURCE = re.compile(r"\(source:\s*([^)]*)\)\s*$", re.I)
# The source kinds references/facts-and-alt-text.md section 1 allows; a slot's
# own source as store file section 2 words it is accepted too.
# A kind word may stand anywhere in the source ("the product title on the page, 2026-10-21").
SOURCE_KINDS = re.compile(r"\b(label|spec\w*|page|owner|cleared)\b", re.I)
ALT_RECOMMENDED, ALT_MAX = shared.ALT_RECOMMENDED, shared.ALT_MAX


def check(ws, date, sections):
    """Check drafted lines: sources named, alt length, redline words, empty
    values. Exit 0 clean, 2 flagged, 1 when the file is missing."""
    path = ws / "products" / f"facts-{date}.md"
    if not path.is_file():
        fail(f"There is no review file at products/facts-{date}.md; write the skeleton first.")
    redlines, _, _ = shared.list_field(sections, shared.FIELD_REDLINES)
    red_words = [r for r in redlines if len(r) <= 40]
    slot_sources = {fact_slots.parse_slot(x)["source"].lower()
                    for x in shared.list_field(sections, shared.FIELD_SLOTS)[0]} - {""}
    flags = []
    entries = [e for e in shared.read_review(path) if e["mark"] in ("proposed", "approved")]
    for e in entries:
        sec, text, ln = e["section"] or "", e["text"], e["line"]
        where = f"line {ln} ({e['handle']}, {sec or 'no section'})"
        if sec in ("facts", "faq"):
            m = SOURCE.search(text)
            kind = (m.group(1).strip().lower() if m else "")
            if not kind or not (SOURCE_KINDS.search(kind) or any(ss in kind for ss in slot_sources)):
                flags.append(f"{where}: no source of a known kind; name label, spec, page, owner or cleared in "
                             "the source, or the slot's own source from store file section 2")
            body = SOURCE.sub("", text)
            if sec == "facts" and (":" not in body or not body.split(":", 1)[1].strip()):
                flags.append(f"{where}: empty value; fill it from a source or mark the line [open]")
            if sec == "faq" and not re.search(r"A:\s*\S", body):
                flags.append(f"{where}: empty answer; answer it from the store file or mark the line [open]")
        elif sec == "alt text":
            alt = text.split(": ", 1)[1].strip() if ": " in text else ""
            if not alt:
                flags.append(f"{where}: empty alt text")
            elif len(alt) > ALT_MAX:
                flags.append(f"{where}: {len(alt)} characters, over Shopify's maximum of {ALT_MAX}")
            elif len(alt) > ALT_RECOMMENDED:
                flags.append(f"{where}: {len(alt)} characters, over the {ALT_RECOMMENDED} Shopify recommends")
        elif sec == "body additions" and not text:
            flags.append(f"{where}: empty body addition; write it or delete the line")
        low = text.lower()
        for r in red_words:
            if r.lower() in low:
                flags.append(f"{where}: carries the redline '{r}' (store file section 3)")
        if shared.INJECTION.search(text):
            flags.append(f"{where}: carries text addressed to an assistant")
    print("Flagged: fix or mark [open] before the approver reads it" if flags else "Clean")
    print(f"lines checked: {len(entries)}; flags: {len(flags)}")
    for f in flags:
        print(f)
    print(f"Coverage. Inputs used: products/facts-{date}.md, store file section 3 redlines ({len(red_words)}). "
          "Could not judge: whether a value matches its source, whether alt text matches its image, whether an answer "
          "stays inside the cleared statements; the approver reads those.")
    print("RESULT: FLAGGED" if flags else "RESULT: CLEAN")
    sys.exit(2 if flags else 0)


def num(v):
    try:
        return int(v)
    except (TypeError, ValueError):
        return None


def main():
    ap = argparse.ArgumentParser(description="Write the review file skeleton.")
    ap.add_argument("workspace")
    ap.add_argument("--date", required=True)
    ap.add_argument("--handles", help="comma-separated handles; default every product with a gap")
    ap.add_argument("--export", help="exports/products-YYYY-MM-DD.csv, for image sources and alt text")
    ap.add_argument("--check", action="store_true",
                    help="check the drafted lines of products/facts-<date>.md instead of writing the skeleton")
    a = ap.parse_args()
    ws = Path(a.workspace)
    try:
        datetime.date.fromisoformat(a.date)
    except ValueError:
        fail(f"--date {a.date} is not a date in the form YYYY-MM-DD.")
    try:
        sections = shared.read_store(ws)
    except shared.StoreFileError as e:
        fail(str(e))
    if a.check:
        check(ws, a.date, sections)
    gaps_path = ws / "products" / f"gaps-{a.date}.csv"
    if not gaps_path.is_file():
        fail(f"There is no gap table at products/gaps-{a.date}.csv; run product_gaps.py for {a.date} first.")
    with open(gaps_path, encoding="utf-8", newline="") as fh:
        gaps = list(csv.DictReader(fh))
    out_path = ws / "products" / f"facts-{a.date}.md"
    if out_path.is_file() and any(e["mark"] == "approved" for e in shared.read_review(out_path)):
        fail(f"products/facts-{a.date}.md already has [approved] lines; it is the person's record and is not "
             "overwritten. Work in it, or run with another --date.")

    slots = {s["name"]: s for s in (fact_slots.parse_slot(x) for x in shared.list_field(sections, shared.FIELD_SLOTS)[0])}
    questions, q_open, _ = shared.list_field(sections, shared.FIELD_QUESTIONS)
    cleared, cleared_open, cleared_mark = shared.list_field(sections, shared.FIELD_CLEARED)
    never, _, _ = shared.list_field(sections, shared.FIELD_NEVER)
    redlines, _, _ = shared.list_field(sections, shared.FIELD_REDLINES)
    domain, _, _ = shared.field(sections, shared.FIELD_DOMAIN)
    approver, _, _ = shared.field(sections, shared.FIELD_APPROVER)

    by_handle = {r["handle"]: r for r in gaps}

    def has_gap(r):
        return (r["fact_slots_missing"] or r["jsonld_product"] == "no" or r["jsonld_rating"] == "no"
                or r["jsonld_faq"] == "no" or (num(r["images_with_alt"]) is not None and num(r["images"]) is not None
                                                and num(r["images_with_alt"]) < num(r["images"])))

    in_line = [r["handle"] for r in gaps if shared.NOT_IN_LINE not in r["notes"]]
    if a.handles:
        wanted = [h.strip() for h in a.handles.split(",") if h.strip()]
        unknown = [h for h in wanted if h not in by_handle]
        if unknown:
            fail(f"Not in products/gaps-{a.date}.csv: {', '.join(unknown)}. Check the handles against the gap table.")
    else:
        wanted = [h for h in in_line if has_gap(by_handle[h])]
    # Every product in the gap table falls in exactly one group: in the file,
    # fine (in a line, no known gap, no block), not named (with --handles only)
    # or left out (not in a product line).
    left_out = [r["handle"] for r in gaps if shared.NOT_IN_LINE in r["notes"] and r["handle"] not in wanted]
    fine_group = [h for h in in_line if h not in wanted and not has_gap(by_handle[h])]
    not_named = [h for h in in_line if h not in wanted and has_gap(by_handle[h])]

    exp_groups, exp_map = {}, {}
    if a.export:
        ep = ws / a.export
        if not ep.is_file():
            fail(f"The export {a.export} is not in the workspace.")
        _, rows, exp_map = shared.read_export(ep)
        _, exp_groups = shared.export_products(rows, exp_map)

    def alt_status(h):
        """(known, image srcs without alt text) from the export, else the product JSON."""
        if h in exp_groups and "image_src" in exp_map and "image_alt" in exp_map:
            return True, [s for s in ((row.get(exp_map["image_src"]) or "").strip() for row in exp_groups[h]
                                      if not (row.get(exp_map["image_alt"]) or "").strip()) if s]
        pj = ws / "pages" / a.date / "products" / f"{h}.json"
        if pj.is_file():
            try:
                prod = json.loads(pj.read_text(encoding="utf-8")).get("product") or {}
                return True, [i.get("src") for i in prod.get("images") or []
                              if i.get("src") and not (i.get("alt") or "").strip()]
            except (ValueError, AttributeError):
                pass
        return False, []

    table = gap_lines()
    template = TEMPLATE.read_text(encoding="utf-8")
    head_t, product_t = template.split("<!-- product -->")
    head_t = head_t.replace("<!-- head -->", "").strip("\n")

    rules = []
    if cleared:
        rules += [f"- cleared statement: {c}" for c in cleared]
    else:
        rules.append("- cleared statements: none listed in section 3" + (" (marked [open])" if cleared_mark == "open" or cleared_open else "")
                     + "; FAQ answers rest on sourced facts only, and anything else is asked")
    rules += [f"- never stated: {x}" for x in never]
    rules += [f"- redline: {x}" for x in redlines]
    rules.append(f"- approves changes to product data: {approver or 'not set in section 7; ask'}")

    sources = [f"products/gaps-{a.date}.csv", "store/store.md"] + ([a.export] if a.export else [])
    blocks = []
    alt_unknown = []
    counts = {"slots": 0, "images": 0, "questions": 0}
    for h in wanted:
        r = by_handle[h]
        missing = [m for m in r["fact_slots_missing"].split(";") if m]
        facts = []
        for m in missing:
            src = slots.get(m, {}).get("source") or "not named in section 2"
            facts.append(f"- [proposed] {m}:  (source: {src})")
        counts["slots"] += len(missing)
        if shared.NOT_IN_LINE in r["notes"]:
            facts.append("Not in a product line in store file section 2; fact slots not checked.")
        elif not facts:
            facts.append("No fact slot is missing from the description.")

        alt_known, srcs = alt_status(h)
        if alt_known:
            alt = [f"- [proposed] {s}: " for s in srcs] or ["Every image has alt text."]
            counts["images"] += len(srcs)
        else:
            alt = [f"- [open] alt text unknown for {r['images'] or 'its'} images: no product JSON or export with alt text was read"]
            alt_unknown.append(h)

        faq = [f"- [proposed] Q: {q} A:  (source: )" for q in questions] or [
            "- [open] no buyer questions in store file section 4; add them in store-setup"]
        counts["questions"] += len(questions)

        structured = []
        checks = [
            ("sku", num(r["variants_with_sku"]) is not None and num(r["variants"]) is not None and num(r["variants_with_sku"]) < num(r["variants"]),
             f"{r['variants_with_sku']} of {r['variants']} variants have a sku"),
            ("barcode", num(r["variants_with_barcode"]) is not None and num(r["variants"]) is not None and num(r["variants_with_barcode"]) < num(r["variants"]),
             f"{r['variants_with_barcode']} of {r['variants']} variants have a barcode"),
            ("category", r["source"] == "export" and not r["product_category"], "no product category in the export"),
            ("rating", r["jsonld_rating"] == "no", "no rating in the page's structured data"),
            ("product-jsonld", r["jsonld_product"] == "no", "no Product structured data on the page"),
            ("faq-markup", r["jsonld_faq"] == "no", "no FAQPage structured data on the page"),
            ("meta-description", r["meta_description"] == "no", "no meta description"),
        ]
        for gid, hit, what in checks:
            if hit and gid in table:
                t = table[gid]
                structured.append(f"- {gid}: {what}. Fixed: {t['where']}. By: {t['who']}. Import file: {t['import']}.")
        if r["jsonld_product"] == "":
            structured.append("- structured data not read: no saved product page")
        structured = (["Not changed by the import file (Measured, gap table of " + a.date + "):"] + structured) if structured else []

        summary = (f"Title: {r['title']}. Slots missing: {', '.join(missing) or 'none'}. "
                   f"Images with alt text: {r['images_with_alt'] or 'unknown'} of {r['images'] or 'unknown'}. "
                   f"Description: {r['description_chars'] or 0} characters.")
        if r["notes"]:
            summary += f" Notes: {r['notes']}."
        block = (product_t.replace("{handle}", h).replace("{summary}", summary)
                 .replace("{structured}", "\n".join(structured)).replace("{facts}", "\n".join(facts))
                 .replace("{alt}", "\n".join(alt)).replace("{faq}", "\n".join(faq)))
        blocks.append(block.strip("\n"))

    head = (head_t.replace("{date}", a.date).replace("{domain}", domain or "not in store file section 1")
            .replace("{sources}", ", ".join(sources)).replace("{rules}", "\n".join(rules)))
    # Alt status of the products without a block is reported too: "fine" rests
    # on alt text only where it is known.
    fine_alt_unknown = [h for h in fine_group if not alt_status(h)[0]]
    alt_unknown += fine_alt_unknown
    reasons = ([f"alt text unknown for {len(alt_unknown)} products"] if alt_unknown else []) + \
        (["no buyer questions in store file section 4"] if not questions else []) + \
        ([] if approver else ["no approver for product data in store file section 7"])
    partial = bool(reasons)
    first = ("Partial: " + "; ".join(reasons)) if partial else "Complete"

    def named(hs, cap=10):
        return ", ".join(hs[:cap]) + (" and more" if len(hs) > cap else "")

    complete = len(wanted) - len([b for b in wanted if by_handle[b]["fact_slots_missing"]])
    # A "Fine" item is listed only when its count is above zero.
    fine_items = []
    if fine_group:
        fine_items.append(f"every fact slot in the description and no known gap: {len(fine_group)}, not in the file ("
                          + named(fine_group) + ")"
                          + (f"; alt text unknown for {len(fine_alt_unknown)} of them" if fine_alt_unknown else ""))
    if complete:
        fine_items.append(f"products in the file with every fact slot in the description: {complete} of {len(wanted)}")
    fine = ("; ".join(fine_items) if fine_items
            else "nothing was complete across the products in the file" if wanted else "no product needed a block")
    groups = (f"Products: {len(gaps)} in the gap table, {len(in_line)} in a product line; in the file: {len(wanted)}; "
              f"fine, no block: {len(fine_group)}; " +
              (f"in a line with a gap, not named with --handles: {len(not_named)}; " if a.handles else "") +
              f"left out, not in a product line: {len(left_out)}.")
    coverage = ("Coverage. " + groups + " Inputs used: " + ", ".join(sources) +
                (f"; product JSON for image sources" if not a.export else "") +
                (f"; {shared.LABELS_NOTE}" if shared.LABELS_NOTE else "") + ". "
                "Inputs missing: " + (f"alt status for {len(alt_unknown)} products ({named(alt_unknown)}): "
                                      "no product JSON or export with alt text was read" if alt_unknown else "none") + ". "
                "Could not judge: every [proposed] line is empty until the model drafts it from a named source; "
                "which buyer questions each product answers. " +
                (f"Not named: {len(not_named)} products in a product line with a gap ({named(not_named)}). " if not_named else "") +
                (f"Left out: {len(left_out)} products not in a product line in store file section 2 "
                 "(name one with --handles to include it). " if left_out else "") + "Fine: " + fine + ".")
    out_path.parent.mkdir(exist_ok=True)
    out_path.write_text((first + "\n\n" if partial else "") + head + "\n\n" + "\n\n".join(blocks) + "\n\n" + coverage + "\n", encoding="utf-8")
    print(first)
    print(f"products: {len(wanted)} of {len(gaps)} in the gap table"
          + (f"; left out, not in a product line: {len(left_out)}" if left_out else ""))
    print(f"products in a product line: {len(in_line)}; in the file: {len(wanted)}; fine, no block: {len(fine_group)}"
          + (f"; with a gap, not named with --handles: {len(not_named)}" if a.handles else ""))
    print(f"empty lines written: facts {counts['slots']}, alt text {counts['images']}, FAQ {counts['questions']}, body additions {len(wanted)}")
    print(f"written: products/facts-{a.date}.md")
    print(coverage)
    print("RESULT: PARTIAL" if partial else "RESULT: WRITTEN")
    sys.exit(2 if partial else 0)


if __name__ == "__main__":
    main()
