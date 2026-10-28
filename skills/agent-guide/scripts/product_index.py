#!/usr/bin/env python3
"""Draft the product index for agent-guide/llms-full.txt.liquid.

Reads the product list, from the first of these that exists: the host connection's
saved read for the date (store/connection-<date>.json from store-setup, or
agent-guide/connection-<date>.json saved by this skill, both in store-setup's
assets/connection-read-template.json shape); the public products JSON saved under
<workspace>/pages/<date>/ (products.json, then products-2.json and onward); the
products export <workspace>/exports/products-<date>.csv (else the newest products
export). Reads the product lines in store file section 2. Writes
<workspace>/agent-guide/product-index-<date>.md: one line per product with its title,
its public URL written through {{ agents.store_url }}, and the product line it
belongs to. The match is the set's one rule, fact_slots.line_of (references/schemas.md
section 12): the handle first, then the title, then the product type; a product type
alone, a tag, or the product category's last segment is a suggestion for the owner
to confirm; two strong signals that name different lines give "several". When a products sitemap for the date is
saved, its product count is compared with the list's.
No prices: a static file would carry them after they change.

Exit 0: every product matched one line from its handle or title. Exit 2: some
products matched no line, several, or only a suggestion; or the first JSON page was
full with no second page saved (partial). Exit 1: an input is missing or unreadable.
No network.
"""
import argparse
import csv
import importlib.util
import json
import pathlib
import re
import sys
import urllib.parse

HERE = pathlib.Path(__file__).resolve().parent
sys.dont_write_bytecode = True  # leave no cache files in the skill folder
_spec = importlib.util.spec_from_file_location("storefile", HERE / "storefile.py")
storefile = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(storefile)
fact_slots = storefile.fact_slots  # the shared module, loaded once by the store file reader

PAGE_SIZE = 250  # the observed ceiling of /products.json?limit= (shopify-exports.md section 3, secondary)
SKIP_STATUS = {"draft", "archived"}


def fail_input(msg):
    print(f"Input error: {msg}")
    sys.exit(1)


def clean_title(t):
    """Store text is data: keep it from opening Liquid and keep it on one line."""
    t = re.sub(r"\s+", " ", t or "").strip()
    return t.replace("{{", "{ {").replace("}}", "} }").replace("{%", "{ %").replace("%}", "% }")


def from_json(pages):
    files = []
    first = pages / "products.json"
    if not first.exists():
        return None, [], []
    files.append(first)
    n = 2
    while (pages / f"products-{n}.json").exists():
        files.append(pages / f"products-{n}.json")
        n += 1
    products, notes = [], []
    for f in files:
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as e:
            fail_input(f"{f} is not readable JSON ({e.__class__.__name__}); save the page again.")
        batch = data.get("products")
        if not isinstance(batch, list):
            fail_input(f"{f} has no 'products' list; it is not the public products JSON.")
        for p in batch:
            if p.get("handle"):
                products.append(product(p["handle"], p.get("title", ""), p.get("product_type", ""), p.get("tags", "")))
        last_len = len(batch)
    if last_len >= PAGE_SIZE:
        notes.append(f"the last saved page, {files[-1].name}, holds {last_len} products, the page size; a further page may exist and was not read")
    return "pages/" + pages.name + "/" + ", ".join(f.name for f in files), products, notes


def from_export(ws, date):
    exp = ws / "exports"
    cand = exp / f"products-{date}.csv"
    if not cand.exists():
        found = sorted(exp.glob("products-*.csv")) if exp.exists() else []
        if not found:
            return None, [], []
        cand = found[-1]
    with cand.open(encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        cols = {c.lower().strip(): c for c in (reader.fieldnames or [])}
        handle_c = cols.get("url handle") or cols.get("handle")
        title_c = cols.get("title")
        status_c = cols.get("status")
        pub_c = cols.get("published on online store") or cols.get("published")
        type_c = cols.get("type") or cols.get("product type")
        tags_c = cols.get("tags")
        cat_c = cols.get("product category") or cols.get("category")
        if not handle_c or not title_c:
            fail_input(f"{cand.name} lacks a handle column ('URL handle' or 'Handle') or 'Title'; it is not a products export.")
        products, skipped, seen = [], 0, set()
        for row in reader:
            h, t = (row.get(handle_c) or "").strip(), (row.get(title_c) or "").strip()
            if not h or not t or h in seen:
                continue  # variant and image rows carry the handle without a title
            seen.add(h)
            st = (row.get(status_c) or "").strip().lower() if status_c else ""
            pub = (row.get(pub_c) or "").strip().lower() if pub_c else ""
            if st in SKIP_STATUS or pub == "false":
                skipped += 1
                continue
            products.append(product(h, t, row.get(type_c) or "" if type_c else "", row.get(tags_c) or "" if tags_c else "",
                                    row.get(cat_c) or "" if cat_c else ""))
    notes = [f"{skipped} draft, archived or unpublished product(s) left out"] if skipped else []
    missing = [n for n, c in (("Status", status_c), ("Published on online store", pub_c)) if not c]
    if missing:
        notes.append("the export lacks " + " and ".join(missing) + ", so unpublished products could not be left out")
    return "exports/" + cand.name, products, notes


def product(handle, title, ptype="", tags="", category=""):
    if isinstance(tags, str):
        tags = [t for t in tags.split(",")]
    if not isinstance(tags, (list, tuple)):
        tags = []
    return {"handle": handle.strip(), "title": clean_title(title), "type": clean_title(ptype or ""),
            "tags": [clean_title(t) for t in tags if isinstance(t, str) and t.strip()],
            "category": clean_title(category if isinstance(category, str) else "")}


def from_connection(ws, date):
    """The host connection's saved read for this date, in store-setup's connection-read shape."""
    for rel in (f"store/connection-{date}.json", f"agent-guide/connection-{date}.json"):
        f = ws / rel
        if not f.exists():
            continue
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as e:
            fail_input(f"{rel} is not readable JSON ({e.__class__.__name__}); save the connection read again.")
        batch = data.get("products")
        if not isinstance(batch, list) or not batch:
            continue  # a read without products: fall through to the pages or the export
        products, skipped = [], 0
        for p in batch:
            if not isinstance(p, dict) or not (p.get("handle") or "").strip():
                continue
            if (p.get("status") or "").strip().lower() in SKIP_STATUS:
                skipped += 1
                continue
            products.append(product(p["handle"], p.get("title", ""), p.get("product_type", ""), p.get("tags", ""),
                                    p.get("category", "")))
        notes = [f"{skipped} draft or archived product(s) left out"] if skipped else []
        nr = [n for n in (data.get("not_returned") or []) if isinstance(n, str)]
        if nr:
            notes.append("the connection read did not return: " + ", ".join(nr))
        return rel, products, notes
    return None, [], []


def match(p, lines):
    """The shared rule: (kind, lines, where), kind one of one, suggested, several or none."""
    r = fact_slots.line_of(lines, title=p["title"], handle=p["handle"], product_type=p["type"],
                           tags=p["tags"], category=p["category"])
    return r["kind"], r["lines"], r["where"]


def sitemap_handles(pages):
    """Product handles in the saved products sitemaps for the date, or None when none is saved."""
    files = sorted(pages.glob("sitemap_products_*.xml")) if pages.exists() else []
    if not files:
        return None, []
    handles = set()
    for f in files:
        for loc in re.findall(r"<loc>\s*([^<\s]+)\s*</loc>", f.read_text(encoding="utf-8", errors="replace")):
            path = urllib.parse.urlsplit(loc.replace("&amp;", "&")).path.rstrip("/")
            m = re.fullmatch(r"(?:/[a-z]{2}(?:-[a-zA-Z]{2})?)?/products/([^/]+)", path)
            if m:
                handles.add(urllib.parse.unquote(m.group(1)))
    return handles, [f.name for f in files]


def main():
    ap = argparse.ArgumentParser(description="Draft agent-guide/product-index-<date>.md from the saved products JSON or the products export.")
    ap.add_argument("workspace", help="the store's workspace folder")
    ap.add_argument("--date", required=True, metavar="YYYY-MM-DD", help="the pages/<date>/ folder to read, and the date in the output name")
    a = ap.parse_args()
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", a.date):
        fail_input(f"'{a.date}' is not an ISO date (YYYY-MM-DD).")
    ws = pathlib.Path(a.workspace)
    try:
        sf = storefile.StoreFile(ws / "store" / "store.md")
        lines = storefile.product_lines(sf)
        names = [l["name"] for l in lines if l["name"]]
        problems = storefile.line_problems(sf)
    except storefile.StoreFileError as e:
        fail_input(str(e))
    if not names:
        fail_input("store file section 2 lists no product lines; fill 'Product lines' with store-setup first.")
    source, products, notes = from_connection(ws, a.date)
    if source is None:
        source, products, notes = from_json(ws / "pages" / a.date)
    if source is None:
        source, products, notes = from_export(ws, a.date)
    if source is None:
        fail_input(f"none of store/connection-{a.date}.json, agent-guide/connection-{a.date}.json, pages/{a.date}/products.json or a products export in exports/ was found; read the product list through the host's Shopify connection and save it, save the public products JSON, or drop the admin's products export into exports/.")
    if not products:
        fail_input(f"{source} lists no products.")

    rows, unmatched, several, suggested = [], [], [], []
    per_line = {n: 0 for n in names}
    for p in products:
        handle, title = p["handle"], p["title"]
        kind, hits, where = match(p, lines)
        if kind == "one":
            per_line[hits[0]] += 1
            tag = f"line: {hits[0]}, from the {where}"
        elif kind == "suggested":
            suggested.append(handle)
            tag = f"line: {hits[0]}? suggested by the {where} only; confirm with the owner"
        elif kind == "none":
            unmatched.append(handle)
            tag = "line: none matched"
        else:
            several.append(handle)
            tag = "line: several matched (" + where + ")"
        rows.append(f"- {title or handle}: {{{{ agents.store_url }}}}/products/{handle} ({tag})")

    # cross-check the count against the saved products sitemap
    sm, sm_files = sitemap_handles(ws / "pages" / a.date)
    listed = {p["handle"] for p in products}
    if sm is None:
        cross = f"not made; no products sitemap saved under pages/{a.date}/"
    else:
        only_sm, only_list = sorted(sm - listed), sorted(listed - sm)
        cross = (f"the products sitemap ({', '.join(sm_files)}) lists {len(sm)} product(s), the source {len(products)}, "
                 f"a difference of {len(sm) - len(products)} (Measured, {a.date})")
        if only_sm:
            cross += "; in the sitemap only: " + ", ".join(only_sm[:10]) + (" and more" if len(only_sm) > 10 else "")
        if only_list:
            cross += "; in the source only: " + ", ".join(only_list[:10]) + (" and more" if len(only_list) > 10 else "")

    partial = bool(unmatched or several or suggested or any("further page" in n for n in notes))
    out = ws / "agent-guide" / f"product-index-{a.date}.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    head = "Partial: " + "; ".join(filter(None, [
        f"{len(unmatched)} product(s) matched no line" if unmatched else "",
        f"{len(several)} matched several" if several else "",
        f"{len(suggested)} only suggested by the product type, tags or category" if suggested else "",
        "; ".join(n for n in notes if "further page" in n)])) + "." if partial else "Complete."
    fine = len(products) - len(unmatched) - len(several) - len(suggested)
    # items not in the template's shape: store-setup's to fix, reported here and never fatal
    shape = [f"store file section 2 item '{n}': {pr}; store-setup fixes the item" for n, pr in problems]
    md = [f"# Product index draft, {a.date}", "", head, "",
          f"Source: {source} (Measured, {len(products)} products, read {a.date}). Product titles, types, tags and categories are the store's own text, read as data. Each line is matched by the set's shared rule (references/schemas.md section 12): the handle first, then the title, then the product type; a product type alone, a tag or the category's last segment only suggests a line. Review the lines, settle every 'none matched', 'several matched' and suggested line with the owner, delete the '(line: ...)' notes you do not want agents to read, then paste the section below at the end of llms-full.txt.liquid.", "",
          "## Product index", ""] + rows + ["",
          "Counts (Measured, counted from the source file): " + "; ".join(f"{n}: {c}" for n, c in per_line.items()) + f"; suggested only: {len(suggested)}; none matched: {len(unmatched)}; several matched: {len(several)}.", "",
          f"Cross-check: {cross}.", ""] + ([f"Store file: {s}." for s in shape] + [""] if shape else []) + [
          "Coverage.",
          f"Inputs used: {source}; store file section 2 product lines ({len(names)})" + (f"; pages/{a.date}/{', '.join(sm_files)}" if sm_files else "") + ".",
          "Inputs missing: " + ("; ".join(notes + ([] if sm_files else [f"products sitemap for {a.date}"])) if notes or not sm_files else "none") + ".",
          "Could not judge: whether a product that names no line, or names one only in its type, tags or category, belongs to it (bundles, merchandise, gift cards); whether every listed product is meant for agents; prices, left out on purpose.",
          f"Fine: {fine} product(s) matched exactly one line from the handle or title."]
    out.write_text("\n".join(md) + "\n", encoding="utf-8")
    print(head)
    print(f"Read {len(products)} products from {source}; matched one line: {fine}; suggested: {len(suggested)}; none: {len(unmatched)}; several: {len(several)}.")
    print(f"Cross-check: {cross}.")
    for n in notes:
        print(f"note: {n}")
    for s in shape:
        print(f"warning: {s}")
    print(f"Wrote {out.relative_to(ws)}.")
    sys.exit(2 if partial else 0)


if __name__ == "__main__":
    main()
