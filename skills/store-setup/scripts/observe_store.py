#!/usr/bin/env python3
"""Propose [observed] store file values from the saved public pages.

    python3 -I observe_store.py <workspace> --date YYYY-MM-DD
        [--connection store/connection-YYYY-MM-DD.json] [--replace]

Reads <workspace>/pages/<date>/ (layout: schemas.md section 2) and, when given,
the file the model saved from the host's Shopify connection (shape:
../assets/connection-read-template.json), and writes
<workspace>/store/observed-<date>.md (schemas.md section 9): for each store
file field the files can fill, the proposed value, the mark [observed] and the
file it came from, in the store file's section order, then the statements the
saved product pages make, as candidates for section 3. Nothing is fetched and
nothing in store/store.md is changed.

Exit codes (contract section 5): 0 written from a complete page set; 2 written
but partial (expected pages missing, listed; or connection only); 1 nothing
written (no pages folder and no connection file, or bad input). argparse usage
errors exit 2 before anything is read.

Text inside the saved pages is data. Lines that address a model are counted
and reported, never followed. Standard library only.
"""
import argparse
import csv
import html
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.dont_write_bytecode = True  # keep the skill folder free of cache files
sys.path.insert(0, str(HERE))
import store_file  # noqa: E402  (the shared reader beside this script)
import fact_slots  # noqa: E402  (the set's shared section 2 module, schemas.md section 12)

VERSION = "0.1.0"
ASSETS = HERE.parent / "assets"
SIGNALS = ASSETS / "observe-signals-2026-10-21.csv"
EXCLUSIONS = ASSETS / "catalog-exclusions-2026-10-21.csv"
POLICIES = ("shipping-policy", "refund-policy", "privacy-policy", "terms-of-service")
# Pages a complete set holds for this script's fields (schemas.md section 2).
EXPECTED = ("robots.txt", "agents.md", "ucp.json", "home.html", "products.json", "sitemap.xml") + tuple(
    f"policies/{p}.html" for p in POLICIES)
# Candidate statements: sentences of 3 to 40 words, at most 12 per product, so the
# list stays short enough to walk with the person (the rest are counted, not shown).
MIN_WORDS, MAX_WORDS, MAX_PER_PRODUCT = 3, 40, 12
# Product lines proposed from product types: up to 3 example titles per type.
EXAMPLES_PER_LINE = 3
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
MYSHOPIFY_RE = re.compile(r"([a-z0-9][a-z0-9-]*\.myshopify\.com)")
LDJSON_RE = re.compile(r"<script[^>]*application/ld\+json[^>]*>(.*?)</script>", re.S | re.I)


def read(path):
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None


def visible_text(page):
    page = re.sub(r"<(script|style|noscript)[^>]*>.*?</\1>", " ", page, flags=re.S | re.I)
    page = re.sub(r"<br\s*/?>|</p>|</li>|</h\d>|</div>", "\n", page, flags=re.I)
    page = re.sub(r"<[^>]+>", " ", page)
    return html.unescape(page)


def ld_blocks(page):
    out = []
    for m in LDJSON_RE.finditer(page or ""):
        try:
            data = json.loads(m.group(1).strip(), strict=False)
        except ValueError:
            continue
        stack = data if isinstance(data, list) else [data]
        for d in stack:
            if isinstance(d, dict):
                out.append(d)
                out.extend(x for x in d.get("@graph", []) if isinstance(x, dict))
    return out


def ld_type(d):
    t = d.get("@type")
    return t if isinstance(t, str) else (t[0] if isinstance(t, list) and t else "")


def load_signals(path):
    sig = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            sig.setdefault(row["kind"], []).append(row["value"])
    return sig


# The item shape for a product line (schemas.md section 3), shown wherever lines are proposed.
LINE_SHAPE_NOTE = ("note: write each line the person keeps as `<name>: <what it is>, <who it is for>; category <the full Shopify "
                   "product category path>`, or end it with `same category` to take the line above's; the groups below are "
                   "product types, not lines, and what each line is, who it is for and its category are the person's")
# The fixed note every catalog proposal carries (schemas.md section 12).
ADMIN_DECIDES = ("note: a word match against the dated list, never Shopify's ruling; the admin's own Shopify Catalog screen "
                 "(Sales channels > Agentic > Sources > Shopify Catalog) decides, and gives the reason when a product is not eligible")
# Tags summarized from a connection read: the most used, shown as hints for naming lines.
TAGS_SHOWN = 8


class Obs:
    """Collected proposals: {section: [(label opening, value, source, [details])]}."""

    def __init__(self):
        self.fields = {}
        self.used, self.missing, self.not_judged, self.notes = [], [], [], []

    def add(self, section, opening, value, source, details=None):
        self.fields.setdefault(section, []).append((opening, value, source, details or []))


def observe_pages(pdir, date, sig, obs):
    def page(rel):
        p = pdir / rel
        if p.is_file():
            obs.used.append(f"pages/{date}/{rel}")
            return read(p)
        return None

    home = page("home.html")
    ucp = page("ucp.json")
    robots = page("robots.txt")
    agents = page("agents.md")
    plist = page("products.json")
    statuses = {}
    log = pdir / "fetch-log.csv"
    if log.is_file():
        obs.used.append(f"pages/{date}/fetch-log.csv")
        with open(log, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                statuses[(row.get("path") or "").strip()] = (row.get("status") or "").strip()
    else:
        obs.notes.append("no fetch-log.csv in the pages folder, so HTTP statuses are unknown; a saved file is read as served")

    # Section 1: the store.
    if home:
        m = re.search(r'<meta[^>]+property="og:site_name"[^>]+content="([^"]+)"', home)
        if m:
            obs.add(1, "Store name", html.unescape(m.group(1)), "home.html, og:site_name")
        m = re.search(r'<link[^>]+rel="canonical"[^>]+href="(https?://[^/"]+)', home)
        if m:
            obs.add(1, "Public domain", m.group(1), "home.html, canonical link")
        m = re.search(r"Shopify\.theme\s*=\s*(\{[^}]*\})", home)
        if m:
            try:
                t = json.loads(m.group(1))
                val = f"{t.get('schema_name', '')} {t.get('schema_version', '')}".strip()
                det = [f"the theme copy is named \"{t['name']}\" in the admin"] if t.get("name") and t.get("name") != t.get("schema_name") else []
                if val:
                    obs.add(1, "Theme name and version", val, "home.html, Shopify.theme", det)
            except ValueError:
                pass
        m = re.search(r'Shopify\.currency\s*=\s*\{[^}]*"active"\s*:\s*"([A-Z]{3})"', home)
        if m:
            obs.add(1, "Store currency", m.group(1), "home.html, Shopify.currency")
    mys = None
    if ucp:
        m = MYSHOPIFY_RE.search(ucp.replace("\\/", "/"))
        if m:
            mys = (m.group(1), "ucp.json")
    if not mys and home:
        m = re.search(r'Shopify\.shop\s*=\s*"([^"]+\.myshopify\.com)"', home)
        if m:
            mys = (m.group(1), "home.html, Shopify.shop")
    if mys:
        obs.add(1, "The `.myshopify.com` domain", mys[0], mys[1])

    # Section 2: product lines proposed from product types.
    if plist:
        try:
            products = json.loads(plist).get("products", [])
        except ValueError:
            products = []
            obs.notes.append("products.json did not parse as JSON")
        groups = {}
        for p in products:
            groups.setdefault((p.get("product_type") or "").strip() or "no product type", []).append(p.get("title", ""))
        lines = [f"{k}: {len(v)} product{'s' if len(v) != 1 else ''}, for example {'; '.join(v[:EXAMPLES_PER_LINE])}"
                 for k, v in sorted(groups.items(), key=lambda kv: (-len(kv[1]), kv[0]))]
        if lines:
            obs.add(2, "Product lines", "", f"products.json, {len(products)} products grouped by product type (Measured, first page only)",
                    lines + [LINE_SHAPE_NOTE])
        if len(products) >= 250:
            obs.notes.append("products.json holds 250 products, the first page; a store with more has a second page (products-2.json)")

    # Product pages: categories, ratings, statements.
    product_files = sorted((pdir / "products").glob("*.html")) if (pdir / "products").is_dir() else []
    json_files = sorted((pdir / "products").glob("*.json")) if (pdir / "products").is_dir() else []
    if not product_files and not json_files:
        obs.missing.append(f"pages/{date}/products/<handle>.html and .json (no product page saved)")
    cats, rated = set(), 0
    for pf in product_files:
        obs.used.append(f"pages/{date}/products/{pf.name}")
        for d in ld_blocks(read(pf)):
            if ld_type(d) in ("Product", "ProductGroup"):
                if isinstance(d.get("category"), str) and d["category"].strip():
                    cats.add(d["category"].strip())
                if d.get("aggregateRating"):
                    rated += 1
    if cats:
        obs.add(2, "Product lines", "", "product structured data on the saved product pages",
                [f"category in the structured data: {c}" for c in sorted(cats)]
                + ["note: the structured data may carry only part of the Shopify category; confirm the full one in the admin"])
    if product_files:
        obs.add(5, "Reviews app", f"ratings in the product structured data on {rated} of {len(product_files)} saved product pages (Measured {date}); the app itself is the person's to name",
                "products/*.html, JSON-LD")

    # Section 6: policies, FAQ or guide pages, contact, barriers.
    domain = next((v for o, v, *_ in obs.fields.get(1, []) if o == "Public domain"), None)
    found = []
    for p in POLICIES:
        rel = f"policies/{p}.html"
        if (pdir / rel).is_file():
            st = statuses.get(f"/policies/{p}", "")
            if st and st != "200":
                obs.notes.append(f"/policies/{p} was saved with status {st}; not proposed as published")
                continue
            page(rel)
            found.append(f"{domain or ''}/policies/{p}")
        else:
            obs.missing.append(f"pages/{date}/{rel}")
    if found:
        obs.add(6, "Policy pages published", "", "policies/*.html", found)
    guides = []
    if (pdir / "pages").is_dir():
        for gp in sorted((pdir / "pages").glob("*.html")):
            if re.search(r"faq|guide", gp.stem, re.I):
                guides.append(f"{domain or ''}/pages/{gp.stem}")
                obs.used.append(f"pages/{date}/pages/{gp.name}")
    for sm in sorted(pdir.glob("sitemap_pages*.xml")):
        obs.used.append(f"pages/{date}/{sm.name}")
        for loc in re.findall(r"<loc>([^<]+)</loc>", read(sm) or ""):
            if re.search(r"/pages/[^/]*(faq|guide)", loc, re.I) and loc not in guides:
                guides.append(loc.strip())
    if guides:
        obs.add(6, "FAQ or buying-guide pages", "", "pages/*.html and the pages sitemap", guides)
    elif list(pdir.glob("sitemap_pages*.xml")) or (pdir / "pages").is_dir():
        obs.add(6, "FAQ or buying-guide pages", "none", "no saved page or pages-sitemap entry whose handle contains faq or guide")
    else:
        obs.not_judged.append("FAQ or guide pages (no pages sitemap and no pages/ folder saved)")
    emails, sources = [], []
    for rel in ["home.html"] + [f"policies/{p}.html" for p in POLICIES] + (
            [f"pages/{x.name}" for x in sorted((pdir / "pages").glob("*contact*.html"))] if (pdir / "pages").is_dir() else []):
        text = read(pdir / rel) if (pdir / rel).is_file() else None
        if not text:
            continue
        hits = re.findall(r"mailto:([^\"'?>\s]+)", text) + EMAIL_RE.findall(visible_text(text))
        for e in hits:
            e = html.unescape(e).strip().lower().rstrip(".")
            if EMAIL_RE.fullmatch(e) and e not in emails:
                emails.append(e)
                sources.append(rel)
    if emails:
        obs.add(6, "Public contact email", emails[0], f"{sources[0]}",
                [f"also seen: {e} ({s})" for e, s in zip(emails[1:], sources[1:])] + ["note: the role that reads it and the reply-time target are the person's"])
    barriers = []
    if home:
        low = home.lower()
        for kind, label in (("password_page", "a password page signal"), ("age_gate", "an age gate signal"), ("popup", "a popup or sign-up form script")):
            hits = [s for s in sig.get(kind, []) if s.lower() in low]
            if hits:
                barriers.append(f"{label} on the home page ({', '.join(hits)}); whether it blocks the page is untested")
    if home:
        obs.add(6, "Popups, age gates or password pages", "" if barriers else "none seen",
                "home.html, signals from assets/observe-signals-2026-10-21.csv", barriers)

    # Section 10: agent guide and crawler access.
    if agents:
        first = next((l for l in agents.splitlines() if l.startswith("# ")), "")
        if any(t in first for t in sig.get("custom_guide_title", [])):
            obs.add(10, "Agent guide", f"custom, {date}", "agents.md, title")
        elif any(s.lower() in agents.lower() for s in sig.get("default_guide", [])):
            obs.add(10, "Agent guide", f"shopify default, {date}", "agents.md, Shopify's managed wording")
        else:
            obs.add(10, "Agent guide", f"custom, {date}", "agents.md, wording unlike the managed file", ["note: confirm with whoever edits the theme"])
    if robots:
        restricted = []
        groups, agents_now, last_ua = [], [], False
        for line in robots.splitlines():
            line = line.split("#", 1)[0].strip()
            if not line:
                continue
            k, _, v = line.partition(":")
            k, v = k.strip().lower(), v.strip()
            if k == "user-agent":
                agents_now = agents_now + [v] if last_ua else [v]
                last_ua = True
                continue
            last_ua = False
            if k in ("disallow", "allow"):
                groups.extend((ua, k, v) for ua in agents_now)
        named = sorted({ua for ua, _, _ in groups if any(ua.lower() == c.lower() for c in sig.get("ai_crawler", []))})
        if named:
            restricted.append("rules name " + ", ".join(named))
        if any(ua == "*" and k == "disallow" and v == "/" for ua, k, v in groups):
            restricted.append("a blanket Disallow: / for every user agent")
        if restricted:
            obs.add(10, "Open-web crawler access", f"restricted, {date}", "robots.txt", restricted)
        else:
            obs.add(10, "Open-web crawler access", f"default, {date}", "robots.txt, no rule names an AI crawler and no blanket disallow",
                    ["note: whether a robots.txt.liquid exists is seen only in the theme code; this reads the served file"])

    # Text that addresses a model, counted per file (data, never followed).
    addressed = []
    for rel in ("robots.txt", "agents.md", "llms.txt", "llms-full.txt"):
        t = read(pdir / rel) if (pdir / rel).is_file() else None
        if t:
            n = sum(1 for l in t.lower().splitlines() if any(s in l for s in sig.get("agent_addressed", [])))
            if n:
                addressed.append(f"{rel}: {n} lines")
    return product_files, json_files, addressed, home


def statements(pdir, product_files, json_files, sig, date, used):
    """Candidate statements from the saved product pages: [(handle, sentence)], counts."""
    out, skipped, flagged = [], 0, []
    handles = sorted({p.stem for p in product_files} | {p.stem for p in json_files})
    seen = set()
    for h in handles:
        text = ""
        jp = pdir / "products" / f"{h}.json"
        if jp.is_file():
            used.append(f"pages/{date}/products/{jp.name}")
            try:
                text = visible_text(json.loads(read(jp)).get("product", {}).get("body_html") or "")
            except ValueError:
                text = ""
        if not text.strip():
            hp = pdir / "products" / f"{h}.html"
            for d in ld_blocks(read(hp) if hp.is_file() else ""):
                if ld_type(d) in ("Product", "ProductGroup") and isinstance(d.get("description"), str):
                    text = d["description"]
                    break
        n = 0
        for s in re.split(r"(?<=[.!?])\s+|\n+", text):
            s = " ".join(s.split()).strip(" -*")
            words = s.split()
            if not (MIN_WORDS <= len(words) <= MAX_WORDS):
                continue
            key = s.lower()
            if key in seen:
                continue
            seen.add(key)
            if any(p in key for p in sig.get("agent_addressed", [])):
                flagged.append((h, s))
                continue
            if n >= MAX_PER_PRODUCT:
                skipped += 1
                continue
            out.append((h, s.replace('"', "'")))
            n += 1
    return out, skipped, flagged, len(handles)


def observe_connection(path, obs, workspace):
    data = json.loads(read(path) or "{}")
    rel = str(path.relative_to(workspace)) if path.is_relative_to(workspace) else str(path)
    obs.used.append(rel)
    when = data.get("read_on", "")
    src = f"connection, read {when}" if when else "connection"
    shop = data.get("shop", {}) or {}
    for opening, key in (("Store name", "name"), ("Public domain", "primary_domain"), ("The `.myshopify.com` domain", "myshopify_domain"),
                         ("Shopify plan", "plan"), ("Store currency", "currency"), ("Theme name and version", "theme")):
        v = (shop.get(key) or "").strip()
        if v and v != "https://...":
            obs.add(1, opening, v, src)
    markets = [m for m in shop.get("markets", []) if isinstance(m, str) and m.strip()]
    if markets:
        obs.add(1, "Countries sold to and shipped to", "; ".join(markets), src, ["note: sold to and shipped to can differ; the person confirms both"])
    products = [p for p in data.get("products", []) if isinstance(p, dict)]
    groups = {}
    for p in products:
        key = ((p.get("product_type") or "").strip() or "no product type", (p.get("category") or "").strip())
        groups.setdefault(key, []).append(p.get("title", ""))
    if groups:
        lines = [f"{t}: {len(v)} product{'s' if len(v) != 1 else ''}, for example {'; '.join(v[:EXAMPLES_PER_LINE])}"
                 + (f"; category {c}" if c else "; no category returned")
                 for (t, c), v in sorted(groups.items(), key=lambda kv: (-len(kv[1]), kv[0]))]
        notes = [LINE_SHAPE_NOTE]
        tag_counts = {}
        tagged = 0
        for p in products:
            tags = p.get("tags")
            if isinstance(tags, str):
                tags = [t.strip() for t in tags.split(",")]
            tags = [t.strip() for t in (tags or []) if isinstance(t, str) and t.strip()]
            if tags:
                tagged += 1
            for t in dict.fromkeys(tags):
                tag_counts[t] = tag_counts.get(t, 0) + 1
        if tag_counts:
            top = sorted(tag_counts.items(), key=lambda kv: (-kv[1], kv[0].lower()))[:TAGS_SHOWN]
            notes.append(f"note: tags on {tagged} of {len(products)} products (Measured, the read of {when or 'an undated read'}); most used: "
                         + ", ".join(f"{t} ({n})" for t, n in top) + "; a tag can suggest a line's name, never decide it")
        elif any("tags" in p for p in products):
            notes.append(f"note: the read returned no tags on any of its {len(products)} products")
        obs.add(2, "Product lines", "", f"{src}, {len(products)} products grouped by product type and category", lines + notes)
    host = (data.get("host") or "").strip()
    level = (data.get("access_level") or "").strip()
    obs.add(8, "How the skills reach the store", f"connection{f' ({host})' if host else ''}", src)
    if level:
        obs.add(8, "Connection access level", level, src, ["note: the staff account role it acts through is the person's to say"])
    for nr in data.get("not_returned", []) or []:
        obs.not_judged.append(f"connection did not return: {nr}")
    return [p.get("category", "") for p in products if p.get("category")]


def catalog_check(workspace, categories_from_connection, exclusions, date, obs):
    """Section 10's category check by fact_slots.catalog_status (schemas.md section 12), one result per product line.

    The lines come from store file section 2 through fact_slots.parse_lines ('same category' resolved); with no line
    there, from the distinct categories of the connection read. Any line excluded makes the proposal 'excluded';
    else any line with no category makes it 'unknown'; else 'eligible'."""
    targets, source = [], ""
    sf = workspace / "store" / "store.md"
    if sf.is_file():
        try:
            data = store_file.read_store_file(sf)
            f = store_file.field(data, 2, "Product lines")
            items = [it["text"] for it in (f["items"] if f else []) if it["mark"] != "open"]
            targets = [(ln["name"] or "a line with no name", ln["category"]) for ln in fact_slots.parse_lines(items)]
            source = "store/store.md section 2"
        except store_file.Problem as p:
            obs.notes.append(f"store/store.md could not be read for categories: {p}")
    if not targets and categories_from_connection:
        targets = [(f"category {c}", c) for c in dict.fromkeys(categories_from_connection)]
        source = "the connection read"
    label = "The product category checked against the Catalog exclusion list"
    if not targets:
        obs.add(10, label, f"unknown, {date}",
                "no product line in store file section 2 and no category in the connection read; run again once section 2 names the lines",
                [ADMIN_DECIDES])
        return
    details, statuses = [], []
    for name, cat in targets:
        r = fact_slots.catalog_status(cat, exclusions)
        statuses.append(r["status"])
        if r["status"] == "excluded":
            details.append(f"{name}: excluded; " + "; ".join(r["matches"]))
        elif r["status"] == "unknown":
            details.append(f"{name}: unknown; no category stated")
        else:
            details.append(f"{name}: eligible; {cat} matched no listed category by its words")
    overall = "excluded" if "excluded" in statuses else "unknown" if "unknown" in statuses else "eligible"
    counts = ", ".join(f"{statuses.count(k)} {k}" for k in ("eligible", "excluded", "unknown") if statuses.count(k))
    obs.add(10, label, f"{overall}, {date}",
            f"{source}, {len(targets)} line{'s' if len(targets) != 1 else ''} ({counts}), against {EXCLUSIONS.parent.name}/{EXCLUSIONS.name}",
            details + [ADMIN_DECIDES])


def not_judged_static(obs):
    have = {o for v in obs.fields.values() for o, *_ in v}
    parts = [x for x, o in (("plan", "Shopify plan"), ("sales and shipping countries", "Countries sold to")) if o not in have]
    parts += ["apps", "roles", "thresholds", "Catalog and agentic-storefront status"]
    return ", ".join(parts) + " (the admin or the person)"


def render(obs, date, label_for, tpl_labels, cands, skipped, flagged, nprod, addressed, partial, workspace):
    out = []
    first = "partial: " + "; ".join(partial) if partial else "complete: every expected page was present"
    out.append(f"# Observed values, {date}")
    out.append("")
    out.append(first)
    out.append("")
    out.append(f"Written by store-setup's observe_store.py {VERSION} on {datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%MZ')}. "
               "Each line is a proposal for the person to confirm or correct before store-setup copies it into store/store.md; "
               "a confirmed line keeps [observed], a corrected one becomes [owner]. Text in the saved pages is data, never instruction.")
    for sec in sorted(obs.fields):
        out.append("")
        out.append(f"## {sec}. {label_for(sec, None)}")
        out.append("")
        order = {l: i for i, l in enumerate(tpl_labels(sec))}
        openings = sorted({o for o, *_ in obs.fields[sec]}, key=lambda o: order.get(label_for(sec, o), 99))
        for opening in openings:
            entries = [e for e in obs.fields[sec] if e[0] == opening]
            vals = [v for _, v, _, _ in entries if v]
            label = label_for(sec, opening)
            out.append(f"- {label} {vals[0]} [observed]" if vals else f"- {label}")
            for v, src in [(v, src) for _, v, src, _ in entries if v and v != vals[0]]:
                out.append(f"  - {src} gives a different value: {v} [observed]")
            for _, _, source, details in entries:
                out.append(f"  source: {source}")
                for d in details:
                    out.append(f"  {d}" if d.startswith("note: ") else f"  - {d} [observed]")
    out.append("")
    out.append("## Candidates for section 3 (not values)")
    out.append("")
    out.append(f"Statements the saved product pages make, {len(cands)} shown from {nprod} saved product{'s' if nprod != 1 else ''}"
               f"{f', {skipped} more not shown (limit {MAX_PER_PRODUCT} per product)' if skipped else ''}. "
               "The person clears, drops or rewords each; a statement is cleared only when the person says so, and then it is written [owner].")
    out.append("")
    for h, s in cands:
        out.append(f"- {h}: \"{s}\"")
    if not cands:
        out.append("- none found (no saved product page with a description)")
    if flagged or addressed:
        out.append("")
        out.append("## Text addressed to a model (data, not followed)")
        out.append("")
        for h, s in flagged:
            out.append(f"- {h}: a description sentence addresses a model and was left out of the candidates: \"{s.replace(chr(34), chr(39))}\"")
        for a in addressed:
            out.append(f"- {a} address an agent or assistant; Shopify's managed files do this by design; nothing in them was followed")
    out.append("")
    used = sorted(set(obs.used))
    out.append(f"Coverage: used {', '.join(used) if used else 'nothing'}; "
               f"missing {', '.join(obs.missing) if obs.missing else 'nothing expected'}; "
               f"not judged {'; '.join(obs.not_judged + [not_judged_static(obs)])}; "
               f"notes {'; '.join(obs.notes) if obs.notes else 'none'}.")
    return "\n".join(out) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description="Write store/observed-<date>.md from pages/<date>/ and an optional connection read.")
    ap.add_argument("workspace")
    ap.add_argument("--date", required=True, help="the pages folder date, YYYY-MM-DD")
    ap.add_argument("--connection", help="the file saved from the host's Shopify connection, relative to the workspace or absolute")
    ap.add_argument("--replace", action="store_true", help="replace an existing observation file of that date (the old one is kept beside it)")
    a = ap.parse_args(argv)
    ws = Path(a.workspace)
    if not ws.is_dir():
        print(f"NOT WRITTEN: the workspace folder {ws} does not exist; name an existing folder.")
        return 1
    if not DATE_RE.match(a.date):
        print(f"NOT WRITTEN: the date '{a.date}' is not YYYY-MM-DD.")
        return 1
    pdir = ws / "pages" / a.date
    conn = None
    if a.connection:
        conn = Path(a.connection) if Path(a.connection).is_absolute() else ws / a.connection
        if not conn.is_file():
            print(f"NOT WRITTEN: the connection file {a.connection} was not found in the workspace.")
            return 1
    if not pdir.is_dir() and conn is None:
        print(f"NOT WRITTEN: pages/{a.date}/ does not exist. Save the public pages first (ai-visibility-audit's fetch_pages.py, or by hand), "
              "or pass --connection with a saved connection read; store-setup can also proceed by asking.")
        return 1
    target = ws / "store" / f"observed-{a.date}.md"
    if target.exists() and not a.replace:
        print(f"NOT WRITTEN: store/observed-{a.date}.md exists; pass --replace to write a new one (the old one is kept beside it).")
        return 1
    sig = load_signals(SIGNALS)
    try:
        excl = fact_slots.read_exclusions(EXCLUSIONS)
    except (OSError, ValueError) as e:
        print(f"NOT WRITTEN: the exclusions list could not be read ({e}); restore assets/{EXCLUSIONS.name} from the set.")
        return 1
    tpl = store_file.read_template(store_file.DEFAULT_TEMPLATE)

    def label_for(sec, opening):
        if opening is None:
            return tpl[sec]["title"]
        return next((l for l in tpl[sec]["labels"] if l.startswith(opening)), opening + ":")

    obs = Obs()
    partial = []
    cands, skipped, flagged, nprod, addressed = [], 0, [], 0, []
    conn_cats = []
    if conn is not None:
        try:
            conn_cats = observe_connection(conn, obs, ws)
        except ValueError:
            print(f"NOT WRITTEN: {a.connection} is not JSON in the shape of assets/connection-read-template.json.")
            return 1
    if pdir.is_dir():
        for rel in EXPECTED:
            if not (pdir / rel).is_file() and f"pages/{a.date}/{rel}" not in obs.missing:
                obs.missing.append(f"pages/{a.date}/{rel}")
        product_files, json_files, addressed, _ = observe_pages(pdir, a.date, sig, obs)
        cands, skipped, flagged, nprod = statements(pdir, product_files, json_files, sig, a.date, obs.used)
        obs.missing = list(dict.fromkeys(obs.missing))
        if obs.missing:
            partial.append(f"{len(obs.missing)} expected page(s) missing, listed in the coverage line")
    else:
        obs.missing.append(f"pages/{a.date}/ (the public pages were not saved)")
        partial.append("connection read only; no public pages were saved, so section 6, section 10 and the section 3 candidates are empty")
    catalog_check(ws, conn_cats, excl, a.date, obs)
    text = render(obs, a.date, label_for, lambda sec: tpl[sec]["labels"], cands, skipped, flagged, nprod, addressed, partial, ws)
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        keep = target.with_name(f"observed-{a.date}-before-{datetime.now(timezone.utc).strftime('%H%MZ')}.md")
        target.rename(keep)
        print(f"kept the earlier file as store/{keep.name}")
    target.write_text(text, encoding="utf-8")
    nfields = sum(len({o for o, *_ in v}) for v in obs.fields.values())
    status = "PARTIAL" if partial else "COMPLETE"
    print(f"{status}: wrote store/observed-{a.date}.md with {nfields} proposed fields in {len(obs.fields)} sections and {len(cands)} candidate statements.")
    for m in obs.missing:
        print(f"  missing: {m}")
    if flagged or addressed:
        print(f"  text addressed to a model: {len(flagged)} description sentences, {len(addressed)} files (reported as data)")
    return 2 if partial else 0


if __name__ == "__main__":
    sys.exit(main())
