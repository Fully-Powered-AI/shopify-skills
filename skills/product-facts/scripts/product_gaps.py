#!/usr/bin/env python3
"""Per-product gap table for product-facts.

Usage:
  python3 -I scripts/product_gaps.py <workspace> --date YYYY-MM-DD [--export exports/products-YYYY-MM-DD.csv]

Reads the store file (section 2 fact slots, section 9 alt-text rule),
pages/<date>/products.json (and products-2.json onward), pages/<date>/products/<handle>.json
and .html when present, and the products export when given. Writes
products/gaps-<date>.csv (schemas.md section 8, columns in order) and
products/gaps-<date>.md, then prints the summary and the coverage line.

Fact slots are matched in the product description (export first, then the
product JSON) by the shared rule of fact_slots.py (references/schemas.md
section 12): the slot name's words, a phrase in its parentheses whole, or for
a unit word a stated quantity such as "9 oz". The description is what the
import changes and what Shopify Catalog passes on. Slots that appear only
elsewhere on the saved page are named in notes. A word match is a signal for
the person, not proof that the fact is stated correctly.

Slots are checked only on products in one of the product lines of store file
section 2, by fact_slots.line_of (handle, title, product type, then tags and
the category's last segment). A product the rule only suggests, or that
several lines match, is checked and its notes say "confirm". Other products
(merch, gift cards, products of a line the store file does not list) get the
note "not in a product line" and empty slot cells, and are left out of the
slot counts. When section 2 lists no lines, or no product matches one, every
product is checked against every slot and the summary says so.

Exit codes: 0 every product had a saved page or product JSON; 1 bad input
(one sentence says what to fix); 2 partial: some products had neither, so
their alt text, barcodes or structured data are unknown (empty cells).
Reads workspace files only; never calls the network.
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

# schemas.md section 8, 2026-10-21.
HEADER = [
    "handle", "title", "status", "product_category", "variants", "variants_with_sku",
    "variants_with_barcode", "images", "images_with_alt", "description_chars",
    "fact_slots_found", "fact_slots_missing", "jsonld_product", "jsonld_rating",
    "jsonld_faq", "meta_description", "source", "notes",
]
# A description is reported thin when it carries fewer than this share of the
# store's own fact slots (build choice, 2026-10-21; change it here).
THIN_SHARE = 0.5
# Recommended Product fields checked in the saved JSON-LD; Google's merchant
# listing page as references/facts-and-alt-text.md section 5 records it.
LD_RECOMMENDED = [
    ("brand", ("brand",)),
    ("sku", ("sku",)),
    ("gtin or mpn", ("gtin", "gtin8", "gtin12", "gtin13", "gtin14", "isbn", "mpn")),
    ("description", ("description",)),
    ("category", ("category",)),
    ("aggregateRating", ("aggregateRating",)),
]


def fail(msg):
    print("RESULT: BAD INPUT")
    print(msg)
    sys.exit(1)


def yn(flag):
    return "yes" if flag else "no"


def load_json(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def main():
    ap = argparse.ArgumentParser(description="Write the per-product gap table.")
    ap.add_argument("workspace")
    ap.add_argument("--date", required=True, help="the pages/<date>/ folder to read, YYYY-MM-DD")
    ap.add_argument("--export", help="exports/products-YYYY-MM-DD.csv, relative to the workspace")
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
    slot_entries, slots_open, _ = shared.list_field(sections, shared.FIELD_SLOTS)
    if not slot_entries:
        fail("Store file section 2 lists no fact slots ('The facts every product page states'); "
             "decide them with the owner in store-setup, then run this again.")
    slots = [fact_slots.parse_slot(s) for s in slot_entries]
    product_lines = fact_slots.parse_lines(shared.list_field(sections, shared.FIELD_LINES)[0])
    line_problems = [f"{pl['name'] or pl['entry']}: {pl['problem']}" for pl in product_lines if pl["problem"]]
    alt_rule, _, _ = shared.field(sections, shared.FIELD_ALT_RULE)
    domain, _, _ = shared.field(sections, shared.FIELD_DOMAIN)

    pages = ws / "pages" / a.date
    used, missing = [], []

    listed = {}
    order = []
    list_files = sorted(pages.glob("products.json")) + sorted(
        pages.glob("products-*.json"), key=lambda p: int(re.sub(r"\D", "", p.stem) or 0))
    for lf in list_files:
        data = load_json(lf)
        if not isinstance(data, dict) or not isinstance(data.get("products"), list):
            missing.append(f"{lf.relative_to(ws)} (not product JSON)")
            continue
        used.append(str(lf.relative_to(ws)))
        for p in data["products"]:
            h = p.get("handle")
            if h and h not in listed:
                listed[h] = p
                order.append(h)
    if not list_files:
        missing.append(f"pages/{a.date}/products.json")

    exp_groups, exp_map, exp_order = {}, {}, []
    if a.export:
        ep = ws / a.export
        if not ep.is_file():
            fail(f"The export {a.export} is not in the workspace; drop the admin's products export into exports/ "
                 "or run without --export.")
        try:
            _, rows, exp_map = shared.read_export(ep)
        except (ValueError, UnicodeDecodeError) as e:
            fail(f"The export {a.export} could not be read as UTF-8 CSV ({e}); export it again as a plain CSV file.")
        if "handle" not in exp_map:
            fail(f"The export {a.export} has no Handle or URL handle column, so its rows cannot be matched to products.")
        exp_order, exp_groups = shared.export_products(rows, exp_map)
        used.append(a.export)
    else:
        missing.append("products export (alt text, barcodes, category and status come from it when present)")

    prod_dir = pages / "products"
    extra = sorted(p.stem for p in prod_dir.glob("*.json")) + sorted(p.stem for p in prod_dir.glob("*.html"))
    handles = []
    for h in exp_order + order + extra:
        if h not in handles:
            handles.append(h)
    if not handles:
        fail(f"No product data: pages/{a.date}/ has no products.json or saved product pages, and no export was given. "
             "Save the pages (ai-visibility-audit's fetch_pages.py) or drop a products export into exports/.")

    out_rows = []
    pending = []
    no_saved = []
    alt_unknown = []
    injected = []
    slot_counts = {s["name"]: 0 for s in slots}
    totals = {"images": 0, "alt": 0, "alt_known": 0, "variants": 0, "sku": 0, "barcode": 0, "barcode_known": 0}
    for h in handles:
        notes = []
        from_where = {}
        hj = None
        hp = prod_dir / f"{h}.json"
        if hp.is_file():
            d = load_json(hp)
            hj = d.get("product") if isinstance(d, dict) else None
            if hj is None:
                notes.append(f"products/{h}.json is not product JSON")
        page = None
        hh = prod_dir / f"{h}.html"
        if hh.is_file():
            page = shared.read_page(hh)
        lj = listed.get(h)
        er = exp_groups.get(h)
        if hj is None and page is None:
            no_saved.append(h)

        def exp_first(key):
            col = exp_map.get(key)
            if not er or not col:
                return ""
            for r in er:
                v = (r.get(col) or "").strip()
                if v:
                    return v
            return ""

        # title
        title = exp_first("title") or (hj or {}).get("title") or (lj or {}).get("title") or ""
        status = exp_first("status")
        ptype = exp_first("product_type") or (hj or {}).get("product_type") or (lj or {}).get("product_type") or ""
        raw_tags = exp_first("tags") or (hj or {}).get("tags") or (lj or {}).get("tags") or ""
        tags = [t.strip() for t in (raw_tags.split(",") if isinstance(raw_tags, str) else raw_tags) if str(t).strip()]
        category = exp_first("category")
        if category:
            from_where["category"] = "export"
        elif page:
            for obj in page["ld"]:
                if shared.ld_types(obj) & {"Product", "ProductGroup"} and obj.get("category"):
                    c = obj["category"]
                    category = c.get("name", "") if isinstance(c, dict) else str(c)
                    from_where["category"] = "page"
                    break

        # variants and images
        variants = sku = barcode = images = alt = ""
        if er:
            vcols = [exp_map.get(k) for k in ("option1_value", "sku", "price") if exp_map.get(k)]
            vrows = [r for r in er if any((r.get(c) or "").strip() for c in vcols)]
            variants = len(vrows)
            sku = sum(1 for r in vrows if (r.get(exp_map.get("sku", ""), "") or "").strip()) if "sku" in exp_map else ""
            barcode = (sum(1 for r in vrows if (r.get(exp_map["barcode"]) or "").strip())
                       if "barcode" in exp_map else "")
            if "image_src" in exp_map:
                irows = [r for r in er if (r.get(exp_map["image_src"]) or "").strip()]
                images = len(irows)
                alt = (sum(1 for r in irows if (r.get(exp_map["image_alt"]) or "").strip())
                       if "image_alt" in exp_map else "")
            from_where["variants and images"] = "export"
        elif hj or lj:
            src = hj or lj
            vs = src.get("variants") or []
            ims = src.get("images") or []
            variants = len(vs)
            sku = sum(1 for v in vs if (v.get("sku") or "").strip())
            images = len(ims)
            if hj:
                barcode = sum(1 for v in vs if (v.get("barcode") or "").strip())
                alt = sum(1 for i in ims if (i.get("alt") or "").strip())
                from_where["variants and images"] = "product json"
            else:
                from_where["variants and images"] = "list json"
                notes.append("alt text and barcodes unknown: the list JSON carries neither")
        if alt == "" and images != "" and from_where.get("variants and images") == "export":
            notes.append("the export has no image alt text column")

        for key, val in (("variants", variants), ("images", images)):
            if val != "":
                totals[key] += val
        if sku != "":
            totals["sku"] += sku
        if barcode != "":
            totals["barcode"] += barcode
            totals["barcode_known"] += variants if variants != "" else 0
        if alt != "":
            totals["alt"] += alt
            totals["alt_known"] += images if images != "" else 0
        elif images != 0:
            alt_unknown.append(h)

        # description and fact slots
        desc = exp_first("description")
        if desc:
            from_where["description"] = "export"
        else:
            desc = (hj or {}).get("body_html") or (lj or {}).get("body_html") or ""
            if desc:
                from_where["description"] = "product json" if hj and hj.get("body_html") else "list json"
        dtext = shared.html_text(desc)
        dtokens = fact_slots.tokens(dtext)
        found = [s["name"] for s in slots if fact_slots.slot_found(s, dtokens)]
        missing_slots = [s["name"] for s in slots if s["name"] not in found]
        slot_notes = []
        if page and missing_slots:
            ptokens = fact_slots.tokens(page["text"])
            elsewhere = [s["name"] for s in slots if s["name"] in missing_slots and fact_slots.slot_found(s, ptokens)]
            if elsewhere:
                slot_notes.append("on the page but not in the description: " + ";".join(elsewhere))
        if desc and len(found) < THIN_SHARE * len(slots):
            slot_notes.append(f"thin: {len(found)} of {len(slots)} fact slots in the description")
        slot_at = len(notes)  # slot notes go here once the product line is settled
        if not desc:
            notes.append("no description")
        for label, text in (("description", dtext), ("page", page["text"] if page else "")):
            if text and shared.INJECTION.search(text):
                notes.append(f"text addressed to an assistant in the {label}; not acted on")
                injected.append(h)
                break

        # structured data
        jp = jr = jf = md = ""
        if page:
            prods = [o for o in page["ld"] if shared.ld_types(o) & {"Product", "ProductGroup"}]
            jp = yn(prods)
            jr = yn(any(o.get("aggregateRating") for o in prods))
            jf = yn(any("FAQPage" in shared.ld_types(o) for o in page["ld"]))
            md = yn(bool(page["meta_description"]))
            if prods:
                variants_ld = [v for o in prods for v in (o.get("hasVariant") or []) if isinstance(v, dict)]
                pool = prods + variants_ld
                lacks = [label for label, keys in LD_RECOMMENDED if not any(any(o.get(k) for k in keys) for o in pool)]
                if lacks:
                    notes.append("structured data lacks: " + ";".join(lacks))
        else:
            notes.append("no saved product page: structured data and meta description not read")

        if er:
            source = "export"
        elif hj or lj:
            source = "json"
        else:
            source = "page"
        if from_where:
            notes.append("from: " + ";".join(f"{k} {v}" for k, v in from_where.items()))

        line = fact_slots.line_of(product_lines, title=title, handle=h, product_type=ptype, tags=tags, category=category)
        pending.append((len(out_rows), line, found, missing_slots, slot_notes, slot_at, notes))
        out_rows.append({
            "handle": h, "title": title, "status": status, "product_category": category,
            "variants": variants, "variants_with_sku": sku, "variants_with_barcode": barcode,
            "images": images, "images_with_alt": alt, "description_chars": len(dtext) if desc else "",
            "fact_slots_found": ";".join(found), "fact_slots_missing": ";".join(missing_slots),
            "jsonld_product": jp, "jsonld_rating": jr, "jsonld_faq": jf, "meta_description": md,
            "source": source, "notes": "",
        })

    # Settle the product lines, then the slot cells and counts.
    filtering = bool(product_lines) and any(p[1]["kind"] != "none" for p in pending)
    out_of_line = []
    to_confirm = 0
    for idx, line, found, missing_slots, slot_notes, slot_at, notes in pending:
        r = out_rows[idx]
        if filtering and line["kind"] == "suggested":
            slot_notes = [f"product line {line['lines'][0]} suggested by the {line['where']}; confirm"] + slot_notes
            to_confirm += 1
        elif filtering and line["kind"] == "several":
            slot_notes = [f"several lines match: {', '.join(line['lines'])}; confirm"] + slot_notes
            to_confirm += 1
        if filtering and line["kind"] == "none":
            out_of_line.append(r["handle"])
            r["fact_slots_found"] = r["fact_slots_missing"] = ""
            notes[slot_at:slot_at] = [shared.NOT_IN_LINE]
        else:
            for name in found:
                slot_counts[name] += 1
            notes[slot_at:slot_at] = slot_notes
        r["notes"] = "; ".join(notes)

    out_dir = ws / "products"
    out_dir.mkdir(exist_ok=True)
    csv_path = out_dir / f"gaps-{a.date}.csv"
    prior = 0
    if csv_path.is_file():
        with open(csv_path, encoding="utf-8", newline="") as fh:
            prior = max(0, sum(1 for _ in fh) - 1)
    with open(csv_path, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=HEADER)
        w.writeheader()
        w.writerows(out_rows)

    n = len(out_rows)
    partial = bool(no_saved)
    first = (f"Partial: {len(no_saved)} of {n} products have no saved product page or product JSON"
             if partial else "Complete: every product had a saved page or product JSON")
    label = f"Measured, from the files read on {a.date}"
    lines = [first, f"rows read: {n}; rows written: {n} (replacing {prior})" if prior else f"rows read: {n}; rows written: {n}"]
    n_in = n - len(out_of_line)
    if filtering:
        lines.append(f"products not in a product line in store file section 2, left out of the slot counts: "
                     f"{len(out_of_line)} of {n}" + (" (" + ";".join(out_of_line[:20]) + (" and more" if len(out_of_line) > 20 else "") + ")" if out_of_line else ""))
    elif product_lines:
        lines.append("no product matched a product line of store file section 2 by name or category; "
                     "every product was checked against every slot")
    else:
        lines.append("store file section 2 lists no product lines; every product was checked against every slot")
    if to_confirm:
        lines.append(f"products whose product line needs the owner's confirmation (suggested, or several lines match): {to_confirm}")
    if line_problems:
        lines.append("check: product-line items store-setup should fix in section 2: " + "; ".join(line_problems))
    lines.append(f"fact slots ({label}): " + "; ".join(f"{k} in {v} of {n_in} descriptions" for k, v in slot_counts.items()))
    for k, v in slot_counts.items():
        note = fact_slots.slot_wording_note(n_in - v, n_in)
        if note:
            lines.append(f"{k}: {note}")
    if totals["alt_known"]:
        lines.append(f"images with alt text ({label}): {totals['alt']} of {totals['alt_known']} images where alt is known"
                     + (f"; alt status unknown for {len(alt_unknown)} of {n} products" if alt_unknown else ""))
    else:
        lines.append("images with alt text: unknown for every product (no export and no product JSON with alt)")
    lines.append(f"variants with sku ({label}): {totals['sku']} of {totals['variants']}")
    if totals["barcode_known"]:
        lines.append(f"variants with barcode ({label}): {totals['barcode']} of {totals['barcode_known']} where known")
    with_page = [r for r in out_rows if r["jsonld_product"]]
    if with_page:
        lines.append(f"saved pages read: {len(with_page)}; Product JSON-LD on {sum(r['jsonld_product'] == 'yes' for r in with_page)}, "
                     f"ratings on {sum(r['jsonld_rating'] == 'yes' for r in with_page)}, "
                     f"FAQPage on {sum(r['jsonld_faq'] == 'yes' for r in with_page)}, "
                     f"meta description on {sum(r['meta_description'] == 'yes' for r in with_page)}")
    if alt_rule:
        lines.append(f"store file section 9, every image carries alt text: {alt_rule}")
    if slots_open:
        lines.append(f"fact slots marked [open] in store file section 2, not checked: {slots_open}")
    # A "Fine" item is listed only when its count is above zero and complete.
    fine = []

    def fine_if(what, have, of):
        if have and have == of:
            fine.append(f"{what} ({have} of {of})")

    for k, v in slot_counts.items():
        fine_if(f"{k} in every in-line description", v, n_in)
    fine_if("every variant has a sku", totals["sku"], totals["variants"])
    fine_if("every image with known alt status has alt text", totals["alt"], totals["alt_known"])
    fine_if("Product JSON-LD on every saved product page",
            sum(r["jsonld_product"] == "yes" for r in with_page), len(with_page))
    coverage = [
        "Coverage.",
        "Inputs used: store file sections 2 and 9; " + "; ".join(used) + f"; saved product pages: {len(with_page)}" +
        (f"; products in a product line: {n_in} of {n}, {len(out_of_line)} left out of the slot counts" if filtering else "") +
        (f"; {shared.LABELS_NOTE}" if shared.LABELS_NOTE else "") + ".",
        "Inputs missing: " + ("; ".join(missing) if missing else "none") +
        (f"; no saved page or product JSON for {len(no_saved)} products: " + ";".join(no_saved[:20]) +
         (" and more" if len(no_saved) > 20 else "") if no_saved else "") +
        (f"; alt status for {len(alt_unknown)} products: " + ";".join(alt_unknown[:20]) +
         (" and more" if len(alt_unknown) > 20 else "") if alt_unknown else "") + ".",
        "Could not judge: whether a matched slot states the fact correctly (word match only); whether alt text "
        "describes its image; structured data on products without a saved page" +
        (f"; {len(set(injected))} products carry text addressed to an assistant, not acted on" if injected else "") + ".",
        "Fine: " + ("; ".join(fine) if fine else "nothing was complete across every product read") + ".",
    ]

    md_lines = [first, "", f"# Product gaps, {a.date}", "",
                f"Store: {domain or 'domain not in store file section 1'}. Sources: {', '.join(used)}.", ""]
    md_lines += [f"- {l}" for l in lines[1:]]
    md_lines += ["", "| handle | slots missing | images with alt | sku | barcode | Product JSON-LD | rating | FAQ | notes |",
                 "|---|---|---|---|---|---|---|---|---|"]
    for r in sorted(out_rows, key=lambda r: (-len([x for x in r["fact_slots_missing"].split(";") if x]), r["handle"])):
        md_lines.append(
            f"| {r['handle']} | {r['fact_slots_missing'].replace(';', ', ') or 'none'} | "
            f"{r['images_with_alt'] if r['images_with_alt'] != '' else 'unknown'} of {r['images'] if r['images'] != '' else '?'} | "
            f"{r['variants_with_sku']} of {r['variants']} | "
            f"{r['variants_with_barcode'] if r['variants_with_barcode'] != '' else 'unknown'} | "
            f"{r['jsonld_product'] or 'not read'} | {r['jsonld_rating'] or 'not read'} | {r['jsonld_faq'] or 'not read'} | "
            f"{r['notes'].replace('|', '/')} |")
    md_lines += ["", *coverage, ""]
    (out_dir / f"gaps-{a.date}.md").write_text("\n".join(md_lines), encoding="utf-8")

    for l in lines:
        print(l)
    print(f"written: products/gaps-{a.date}.csv, products/gaps-{a.date}.md")
    for c in coverage:
        print(c)
    print("RESULT: PARTIAL" if partial else "RESULT: COMPLETE")
    sys.exit(2 if partial else 0)


if __name__ == "__main__":
    main()
