#!/usr/bin/env python3
"""Build the products import file from the approved lines of a review file.

Usage:
  python3 -I scripts/product_import.py <workspace> products/facts-YYYY-MM-DD.md --export exports/products-YYYY-MM-DD.csv [--handles h] [--reference PATH]

Reads [approved] lines only. Starts from the export's own rows for the
handles with approved entries, keeps every other cell of the columns the file
carries as exported, and changes only: the image alt text cell on the row
whose image URL the entry names; the description cell on the product's first
row, with each approved body addition and FAQ entry appended as an HTML
paragraph. Approved facts are the record behind those lines and are not
written on their own. Writes products/product-import-<date>.csv and prints
the plan.

Which columns the file carries (schemas.md section 8, the lead's rule of
2026-10-21): when the run has no approved alt text, every image column is
left out (and a row left with nothing but its handle is dropped), so the
import rests on Shopify's stated rule that an omitted column leaves the
stored value unchanged; the first line says so and still asks for a
one-product test; exit 0. When alt text is approved, the image rows travel
as exported.

The import behaviors the file depends on are read from the status table in
references/shopify-exports-extract.md section 2 (or --reference). When any
needed behavior is not `stated`, the first line says UNVERIFIED and to
import one product first, and the exit is 2 with the file written. Without
an export it refuses and prints the approved lines grouped by handle, for
the person to apply by hand.

Exit codes: 0 written, behaviors stated; 1 refused (no export given or found,
no approved line, an unknown handle or image, a column the export lacks, an
empty approved line; one sentence each, with the by-hand fallback when the
export is missing); 2 written, behavior unverified. Reads workspace files
only; never calls the network and never imports anything.
"""

import argparse
import csv
import re
import sys
from collections import Counter
from pathlib import Path
from urllib.parse import urlsplit

sys.dont_write_bytecode = True  # keep the skill folder free of cache files
sys.path.insert(0, str(Path(__file__).resolve().parent))
import shared  # noqa: E402

DEFAULT_REFERENCE = Path(__file__).resolve().parent.parent / "references" / "shopify-exports-extract.md"
ALT_MAX, ALT_RECOMMENDED = shared.ALT_MAX, shared.ALT_RECOMMENDED
FALLBACK = ("export the products from the admin (Products > Export, plain CSV) into exports/ and pass it with "
            "--export, or apply the approved lines by hand in the admin or through the host's connection one "
            "product at a time after a printed plan and the person's yes (SKILL.md step 10).")
SOURCE_TAIL = re.compile(r"\s*\(source:[^)]*\)\s*$", re.I)


def refuse(lines, after=()):
    print("RESULT: REFUSED, nothing written")
    for l in list(lines) + list(after):
        print(l)
    sys.exit(1)


SECTION_NAMES = {"facts": "fact", "alt text": "alt text", "faq": "FAQ", "body additions": "body addition"}


def grouped(approved):
    """The approved lines by handle, for the person to paste in the admin."""
    if not approved:
        return ["Approved lines by product: none yet; the approver marks lines [approved] first."]
    out = ["Approved lines by product, to apply by hand (description additions go after the owner's text):"]
    order = []
    for e in approved:
        if e["handle"] not in order:
            order.append(e["handle"])
    for h in order:
        mine = [e for e in approved if e["handle"] == h]
        out.append(f"  {h}: {len(mine)} approved line(s)")
        for e in mine:
            out.append(f"    {SECTION_NAMES.get(e['section'] or '', e['section'] or 'no section')}: {e['text']}")
    return out


def behaviors(path):
    status = {}
    in_table = False
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if line.startswith("## 2."):
            in_table = True
            continue
        if in_table and line.startswith("## "):
            break
        if in_table and line.startswith("| ") and not line.startswith("| id ") and not line.startswith("|---"):
            cells = [c.strip() for c in line.strip("|").split("|")]
            if len(cells) >= 3:
                status[cells[0]] = cells[2]
    return status


def bare(url):
    p = urlsplit(url.strip())
    return f"{p.netloc}{p.path}".lower()


def main():
    ap = argparse.ArgumentParser(description="Build the import file from approved review lines.")
    ap.add_argument("workspace")
    ap.add_argument("facts", help="products/facts-YYYY-MM-DD.md, relative to the workspace")
    ap.add_argument("--export", help="exports/products-YYYY-MM-DD.csv, relative to the workspace; without it nothing is written")
    ap.add_argument("--handles", help="comma-separated handles: build the file for these products only (one product first)")
    ap.add_argument("--reference", default=str(DEFAULT_REFERENCE),
                    help="the extract whose section 2 holds the import behaviors (default: this skill's)")
    a = ap.parse_args()
    ws = Path(a.workspace)

    fp = ws / a.facts
    m = re.search(r"facts-(\d{4}-\d{2}-\d{2})\.md$", a.facts)
    if not fp.is_file() or not m:
        refuse([f"The review file {a.facts} is not in the workspace under the name products/facts-YYYY-MM-DD.md."])
    date = m.group(1)
    entries = shared.read_review(fp)
    approved = [e for e in entries if e["mark"] == "approved"]
    if a.handles:
        only = {h.strip() for h in a.handles.split(",") if h.strip()}
        approved = [e for e in approved if e["handle"] in only]
    if not a.export:
        refuse(["No products export was given, and the import file is built only from one; " + FALLBACK], grouped(approved))
    ep = ws / a.export
    if not ep.is_file():
        refuse([f"The export {a.export} is not in the workspace; " + FALLBACK], grouped(approved))
    # The guard is the fixed name SKILL.md step 2 gives the connection's save
    # (exports/products-connection-YYYY-MM-DD.csv); a file saved under another name passes.
    if "connection" in Path(a.export).name:
        refuse([f"{a.export} was saved from the host's connection, not exported by Shopify; the import file is "
                "built only from the admin's own export, so its rows and columns are Shopify's."])
    try:
        header, rows, cmap = shared.read_export(ep)
    except (ValueError, UnicodeDecodeError) as e:
        refuse([f"The export {a.export} could not be read as UTF-8 CSV ({e}); export it again as a plain CSV file."])
    for key in ("handle", "title"):
        if key not in cmap:
            refuse([f"The export has no {shared.COLUMNS[key][0]} column ({' or '.join(shared.COLUMNS[key])}); "
                    "an overwrite needs the handle and the title (shopify-exports-extract.md section 2)."])
    order, groups = shared.export_products(rows, cmap)

    if not approved:
        refuse([f"{a.facts} has no [approved] line" + (" for the handles given" if a.handles else "") + ". Change [proposed] to [approved] on the lines the approver "
                "accepts, then run this again."])

    problems = []
    alt_changes = {}      # (handle, row index) -> alt
    additions = {}        # handle -> [html paragraph]
    facts_approved = 0
    warnings = []
    for e in approved:
        h, sec, text, ln = e["handle"], (e["section"] or ""), e["text"], e["line"]
        if h not in groups:
            problems.append(f"line {ln}: handle '{h}' is not in the export")
            continue
        if sec == "facts":
            value = SOURCE_TAIL.sub("", text.split(":", 1)[1]).strip() if ":" in text else ""
            if not value:
                problems.append(f"line {ln}: approved fact has no value")
            facts_approved += 1
        elif sec == "alt text":
            if ": " not in text:
                problems.append(f"line {ln}: approved alt text is not in the form '<image URL>: <alt text>'")
                continue
            src, alt = text.split(": ", 1)
            alt = alt.strip()
            if not alt:
                problems.append(f"line {ln}: approved alt text is empty")
                continue
            if len(alt) > ALT_MAX:
                problems.append(f"line {ln}: alt text has {len(alt)} characters; Shopify's maximum is {ALT_MAX}")
                continue
            if len(alt) > ALT_RECOMMENDED:
                warnings.append(f"line {ln}: alt text has {len(alt)} characters; Shopify recommends {ALT_RECOMMENDED} or fewer")
            if "image_src" not in cmap:
                problems.append(f"line {ln}: the export has no Image Src or Product image URL column")
                continue
            hits = [i for i, r in enumerate(groups[h]) if (r.get(cmap["image_src"]) or "").strip() == src.strip()]
            if not hits:
                hits = [i for i, r in enumerate(groups[h]) if bare(r.get(cmap["image_src"]) or "") == bare(src)]
            if not hits:
                problems.append(f"line {ln}: image {src} is not among the export's image rows for '{h}'")
                continue
            alt_changes[(h, hits[0])] = alt
        elif sec in ("faq", "body additions"):
            body = SOURCE_TAIL.sub("", text).strip()
            if sec == "faq":
                qm = re.match(r"Q:\s*(.+?)\s+A:\s*(.*)$", body)
                if not qm or not qm.group(2).strip():
                    problems.append(f"line {ln}: approved FAQ entry needs 'Q: <question> A: <answer>' with an answer")
                    continue
                para = f"<p><strong>{shared.escape(qm.group(1).strip())}</strong><br>{shared.escape(qm.group(2).strip())}</p>"
            else:
                if not body:
                    problems.append(f"line {ln}: approved body addition is empty")
                    continue
                para = f"<p>{shared.escape(body)}</p>"
            additions.setdefault(h, []).append((ln, para))
        else:
            problems.append(f"line {ln}: approved line is under '### {e['section']}', not Facts, Alt text, FAQ or Body additions")

    if alt_changes and "image_alt" not in cmap:
        problems.append("the export has no Image Alt Text or Image alt text column, which the approved alt text needs")
    if additions and "description" not in cmap:
        problems.append("the export has no Body (HTML) or Description column, which the approved additions need")
    variant_cols = [k for k in ("sku", "barcode", "price") if k in cmap]
    if variant_cols and not ("option1_name" in cmap and "option1_value" in cmap):
        problems.append("the export carries variant columns without Option1 name and value; importing it would replace "
                        "the variants (shopify-exports-extract.md section 2, options-with-variants)")
    if problems:
        refuse(problems)

    touched = []
    for h in order:
        if h in additions or any(k[0] == h for k in alt_changes):
            touched.append(h)
    # The columns the file carries: without approved alt text, no image column.
    image_cols = []
    if not alt_changes:
        named = {cmap[k] for k in shared.IMAGE_KEYS if k in cmap}
        image_cols = [c for c in header if c in named or shared.IMAGE_HEADER.search(c)]
    out_header = [c for c in header if c not in image_cols]
    hcol = cmap["handle"]
    out_rows = []
    dropped = 0
    cells = Counter()
    per_product = []
    skipped = 0
    for h in touched:
        group = [dict(r) for r in groups[h]]
        notes = []
        if h in additions:
            col = cmap["description"]
            first = next((i for i, r in enumerate(group) if (r.get(cmap["title"]) or "").strip()), 0)
            current = group[first].get(col) or ""
            added = 0
            for ln, para in additions[h]:
                if para in current:
                    skipped += 1
                    continue
                current = current + para
                added += 1
            if added:
                group[first][col] = current
                cells[col] += 1
                notes.append(f"description +{added} paragraph(s)")
        n_alt = 0
        for (hh, idx), alt in alt_changes.items():
            if hh == h:
                group[idx][cmap["image_alt"]] = alt
                cells[cmap["image_alt"]] += 1
                n_alt += 1
        if n_alt:
            notes.append(f"alt text on {n_alt} image(s)")
        if image_cols:
            kept = [r for r in group if any((r.get(c) or "").strip() for c in out_header if c != hcol)]
            dropped += len(group) - len(kept)
            group = kept
        out_rows.extend(group)
        per_product.append(f"  {h}: {', '.join(notes) if notes else 'nothing new (already present)'}; rows {len(group)}")

    needed = ["overwrite-option", "required-on-update"]
    if image_cols:
        # The images stay as stored because their columns are omitted (stated);
        # the variant cells travel as exported with their option columns.
        needed.append("omitted-column")
    else:
        if alt_changes:
            needed.append("image-alt-update")
        if "image_src" in cmap and any((r.get(cmap["image_src"]) or "").strip() for r in out_rows):
            needed.append("image-rows-on-overwrite")
        if additions:
            needed.append("description-update")
    status = behaviors(a.reference)
    unverified = [f"{b} ({status.get(b, 'not in the reference')})" for b in needed if status.get(b) != "stated"]

    out = ws / "products" / f"product-import-{date}.csv"
    out.parent.mkdir(exist_ok=True)
    with open(out, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=out_header, extrasaction="ignore")
        w.writeheader()
        w.writerows(out_rows)

    if unverified:
        print("UNVERIFIED: import one product first and check it in the admin before importing the rest; "
              "Shopify's pages do not confirm: " + "; ".join(unverified))
    elif image_cols:
        print("Written: no alt text is approved, so the image columns are left out and the import rests on Shopify's "
              "stated rule that a column left out of the file leaves the stored value unchanged (omitted-column, "
              f"{Path(a.reference).name} section 2); still import one product first and check it in the admin")
    else:
        print("Written: every import behavior this file depends on is stated in the reference")
    print(f"plan: products {len(touched)}; rows {len(out_rows)} (every row of those products, as exported"
          + (f", less {dropped} image-only row(s)" if dropped else "") + f"); "
          f"cells changed {sum(cells.values())}; columns changed: "
          + (", ".join(f"{c} {n}" for c, n in cells.items()) or "none"))
    print(f"columns kept as exported: {len(out_header)}; import option: Overwrite products with matching handles")
    if image_cols:
        print(f"image columns left out (no approved alt text): {', '.join(image_cols)}")
    for p in per_product:
        print(p)
    print(f"approved lines read: {len(approved)}; facts approved (records, not written): {facts_approved}; "
          f"additions already in the description, skipped: {skipped}")
    for wline in warnings:
        print(wline)
    print(f"written: products/product-import-{date}.csv")
    print(f"Coverage. Inputs used: {a.facts}, {a.export}, {Path(a.reference).name} section 2. Inputs missing: none. "
          "Could not judge: whether Shopify applies the file as the reference infers"
          + (" (see UNVERIFIED)" if unverified else "") + "; whether each approved line is true, which is the approver's call. "
          f"Fine: every approved line matched a product and, for alt text, an image row.")
    sys.exit(2 if unverified else 0)


if __name__ == "__main__":
    main()
