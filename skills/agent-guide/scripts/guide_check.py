#!/usr/bin/env python3
"""Check the drafted agent guide before a person pastes it into the theme.

Reads <workspace>/agent-guide/agents.md.liquid (and llms-full.txt.liquid when present),
the store file <workspace>/store/store.md (sections 1, 2, 3 and 6), the word lists and
size limit in ../references/guide-shape.md, and, with --pages, the saved sitemaps and
policy pages under <workspace>/pages/<date>/. Writes <workspace>/agent-guide/check-<date>.md
(dated by --date, else by --pages, else today in UTC), setting aside an earlier report
of that date under agent-guide/superseded/.

Exit 0: every check passed. Exit 2: warnings only, or a check was skipped (partial).
Exit 1: a check failed, or an input is missing or unreadable (the first line says which).
No network.
"""
import argparse
import csv
import datetime
import importlib.util
import pathlib
import re
import sys
import urllib.parse

HERE = pathlib.Path(__file__).resolve().parent
REFERENCE = HERE.parent / "references" / "guide-shape.md"

sys.dont_write_bytecode = True  # leave no cache files in the skill folder
_spec = importlib.util.spec_from_file_location("storefile", HERE / "storefile.py")
storefile = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(storefile)  # it loads the shared fact_slots.py beside it

REQUIRED = [
    "## What this store is",
    "## Who it is for",
    "## The product lines and how to choose",
    "## Facts an agent may state",
    "## Policies",
    "## Shopping here as an agent",
    "## What not to assume",
]
OPTIONAL_LAST = {"llms-full.txt.liquid": ["## Product index"]}
H1 = re.compile(r"^# .+: a guide for agents\s*$")
OUTPUT = re.compile(r"\{\{\s*(.*?)\s*\}\}", re.S)
TAG = re.compile(r"\{%-?\s*(\w+)")
URL = re.compile(r"https?://[^\s)<>\]\"'`]+")
STORE_LINK = re.compile(r"\{\{\s*agents\.store_url\s*\}\}(/[^\s)<>\]\"'`]*)?")
EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PHONE = re.compile(r"(?<![\w/.-])\+?\(?\d[\d\s().-]{7,}\d(?![\w/-])")
# An unbroken run of 12 to 14 digits is a product code (UPC, EAN, GTIN), not a phone number.
PRODUCT_CODE = re.compile(r"\d{12,14}")
DOLLAR = re.compile(r"\$\s?\d")
# A placeholder is an angle-bracketed phrase with a space in it; it may carry a nested
# one-word placeholder such as <name> or <handle>.
_PH_PART = r"(?:[^<>=\n]|<[\w-]+>)"
PLACEHOLDER = re.compile(r"<(?!!--)(?=[a-z])" + _PH_PART + r"*\s" + _PH_PART + r"*>")
SKELETON = "Skeleton for templates/agents.md.liquid"
# British forms that the house's American spelling replaces; written with a bracket
# class so the set's own spelling check does not read the list as prose.
SPELLING = [
    r"colo[u]rs?", r"behavio[u]rs?", r"flavo[u]rs?", r"favo[u]rite", r"cent[r]es?",
    r"met[r]es?", r"lit[r]es?", r"catalog[u]es?", r"organi[s](e|ed|es|ing|ation)",
    r"recogni[s](e|ed|es|ing)", r"customi[s](e|ed|es|ing)", r"personali[s](e|ed|es)",
    r"optimi[s](e|ed|es|ing)", r"analy[s](e|ed|es|ing)", r"licen[c]e", r"program[m]es?",
    r"label[l](ed|ing)", r"travel[l](ed|ing)", r"cancel[l](ed|ing)", r"jewel[l]ery",
    r"gr[e]y", r"alumin[i]um", r"moul[d]s?", r"defen[c]e", r"fulfi[l]ment",
]
SPELLING_RE = re.compile(r"\b(" + "|".join(SPELLING) + r")\b", re.I)


def fail_input(msg):
    print(f"Input error: {msg}")
    sys.exit(1)


def read_lists():
    if not REFERENCE.exists():
        fail_input(f"the reference {REFERENCE} is missing; reinstall the skill folder.")
    text = REFERENCE.read_text(encoding="utf-8")
    lists = {}
    for m in re.finditer(r"<!-- list: ([\w-]+) -->\s*```\n(.*?)```", text, re.S):
        lists[m.group(1)] = [l.strip() for l in m.group(2).splitlines() if l.strip()]
    size = re.search(r"^size-limit-bytes:\s*(\d+)\s*$", text, re.M)
    for need in ("agents-outputs", "standard-paths", "claim-words", "comparison-words"):
        if need not in lists:
            fail_input(f"the reference {REFERENCE.name} lacks the list '{need}'.")
    if not size:
        fail_input(f"the reference {REFERENCE.name} lacks the size-limit-bytes line.")
    return lists, int(size.group(1))


def word_re(words):
    parts = []
    for w in words:
        e = re.escape(w)
        left = r"(?<![\w-])" if w[0].isalnum() else ""
        right = r"(?![\w-])" if w[-1].isalnum() else ""
        parts.append(left + e + right)
    return re.compile("|".join(parts), re.I)


def norm(s):
    return re.sub(r"\s+", " ", s.strip().strip('"').strip()).lower()


class Report:
    def __init__(self):
        self.rows = []  # (file, check, outcome, detail)

    def add(self, file, check, outcome, detail=""):
        self.rows.append((file, check, outcome, detail))

    def count(self, outcome):
        return sum(1 for r in self.rows if r[2] == outcome)


def sitemap_index(pages):
    """Paths present in the saved sitemaps, and the path families whose sitemap was not saved."""
    present, unsaved, read = set(), set(), []
    families = {"products": "/products/", "pages": "/pages/", "collections": "/collections/",
                "blogs": "/blogs/", "articles": "/blogs/"}
    index = pages / "sitemap.xml"
    named = []
    if index.exists():
        for loc in re.findall(r"<loc>\s*([^<\s]+)\s*</loc>", index.read_text(encoding="utf-8", errors="replace")):
            name = urllib.parse.urlsplit(loc.replace("&amp;", "&")).path.rsplit("/", 1)[-1]
            named.append(name)
    for f in sorted(pages.glob("sitemap*.xml")):
        if f.name == "sitemap.xml":
            continue
        read.append(f.name)
        for loc in re.findall(r"<loc>\s*([^<\s]+)\s*</loc>", f.read_text(encoding="utf-8", errors="replace")):
            present.add(urllib.parse.urlsplit(loc).path.rstrip("/") or "/")
    saved_names = {f.name for f in pages.glob("sitemap*.xml")}
    for name in named:
        m = re.match(r"sitemap_([a-z]+)_", name)
        if m and m.group(1) in families and name not in saved_names:
            unsaved.add(families[m.group(1)])
    for fam in ("/collections/",):
        for f in (pages / "collections").glob("*.html") if (pages / "collections").exists() else []:
            present.add(fam + f.stem)
    return present, unsaved, read, index.exists()


def fetch_status(pages):
    status = {}
    log = pages / "fetch-log.csv"
    if log.exists():
        with log.open(encoding="utf-8", newline="") as fh:
            for row in csv.DictReader(fh):
                path = urllib.parse.urlsplit(row.get("url", "")).path or row.get("path", "")
                status[path.rstrip("/") or "/"] = (row.get("status") or "").strip()
    return status


def check_file(path, rel, store, lists, size_limit, pages_dir, report):
    raw = path.read_bytes()
    text = raw.decode("utf-8", errors="replace")
    lines = text.splitlines()
    name = path.name

    # size
    if len(raw) > size_limit:
        report.add(rel, "size", "fail", f"Measured {len(raw)} bytes against the limit of {size_limit} (guide-shape.md section 6)")
    else:
        report.add(rel, "size", "pass", f"Measured {len(raw)} bytes; limit {size_limit}")

    # leftovers from the skeleton
    left = [i for i, l in enumerate(lines, 1) if SKELETON in l or PLACEHOLDER.search(l)]
    if left:
        report.add(rel, "template placeholders", "fail", "unfilled placeholder or skeleton comment on line(s) " + ", ".join(map(str, left[:10])))
    else:
        report.add(rel, "template placeholders", "pass")

    # sections
    h1 = next((l for l in lines if l.startswith("# ")), None)
    problems = []
    if not h1 or not H1.match(h1):
        problems.append("the first heading is not '# <store name>: a guide for agents'")
    h2 = [l.strip() for l in lines if l.startswith("## ")]
    allowed_extra = OPTIONAL_LAST.get(name, [])
    pos = -1
    for h in REQUIRED:
        if h not in h2:
            problems.append(f"missing '{h}'")
            continue
        p = h2.index(h)
        if p < pos:
            problems.append(f"'{h}' out of order")
        pos = max(pos, p)
    extra = [h for h in h2 if h not in REQUIRED and h not in allowed_extra]
    if problems:
        report.add(rel, "sections", "fail", "; ".join(problems))
    else:
        report.add(rel, "sections", "pass", "the heading and seven sections in order")
    if extra:
        report.add(rel, "extra sections", "warning", "sections not in the shape: " + "; ".join(extra))
    # empty sections
    bodies = {}
    cur = None
    for l in lines:
        if l.startswith("## "):
            cur = l.strip()
            bodies[cur] = []
        elif cur and l.strip() and not l.strip().startswith("<!--"):
            bodies[cur].append(l)
    empty = [h for h in REQUIRED if h in bodies and not bodies[h]]
    if empty:
        report.add(rel, "empty sections", "warning", "no text under: " + "; ".join(empty) + " (write the 'not stated' sentence instead)")

    # Liquid outputs
    allowed = set(lists["agents-outputs"])
    bad, unverified, used = [], [], set()
    for m in OUTPUT.finditer(text):
        expr = m.group(1).split("|", 1)[0].strip()
        lm = re.fullmatch(r"agents\.([a-z_]+)", expr)
        if lm and lm.group(1) in allowed:
            used.add(lm.group(1))
        elif expr.startswith("request."):
            unverified.append(expr)
        else:
            bad.append(expr)
    tags = sorted({t for t in TAG.findall(text) if t not in ("comment", "endcomment", "raw", "endraw")})
    if bad:
        report.add(rel, "Liquid outputs", "fail", "outputs outside the documented agents list (they render blank or break): " + "; ".join(sorted(set(bad))))
    else:
        report.add(rel, "Liquid outputs", "pass", "agents outputs used: " + (", ".join(sorted(used)) or "none"))
    if unverified:
        report.add(rel, "request outputs", "warning", "request attributes are not listed in the references; verify: " + "; ".join(sorted(set(unverified))))
    if tags:
        report.add(rel, "Liquid tags", "warning", "Liquid tags present; check them on a duplicated theme: " + ", ".join(tags))
    shop_body = "\n".join(bodies.get("## Shopping here as an agent", []))
    missing_ep = [o for o in ("ucp_discovery_url", "mcp_endpoint_url") if not re.search(r"\{\{\s*agents\." + o, shop_body)]
    if missing_ep:
        report.add(rel, "endpoints", "fail", "'Shopping here as an agent' lacks " + ", ".join("{{ agents.%s }}" % o for o in missing_ep))
    else:
        report.add(rel, "endpoints", "pass")

    # hardcoded store URLs
    domain = store["domain_host"]
    hard, offsite = [], []
    for i, l in enumerate(lines, 1):
        for u in URL.findall(l):
            host = urllib.parse.urlsplit(u).hostname or ""
            if host.endswith("myshopify.com") or (domain and host in (domain, domain.removeprefix("www."), "www." + domain.removeprefix("www."))):
                hard.append(f"line {i}: {u}")
            else:
                offsite.append(f"line {i}: {host}")
        if domain and re.search(re.escape(domain.removeprefix("www.")), URL.sub("", l), re.I):
            report.add(rel, "bare domain", "warning", f"line {i} names the store domain as text; write {{{{ agents.store_url }}}} instead")
        if "myshopify.com" in URL.sub("", l):
            hard.append(f"line {i}: a .myshopify.com address")
    if hard:
        report.add(rel, "hardcoded URLs", "fail", "write these through {{ agents.store_url }} or the agents output for the endpoint: " + "; ".join(hard[:10]))
    else:
        report.add(rel, "hardcoded URLs", "pass")
    if offsite:
        report.add(rel, "off-domain links", "warning", "links off the store's domain, for a person to confirm: " + "; ".join(sorted(set(offsite))[:10]))

    # contact details
    emails = [f"email on line {i}" for i, l in enumerate(lines, 1) if EMAIL.search(l)]
    phones = []
    for i, l in enumerate(lines, 1):
        for m in PHONE.finditer(URL.sub("", OUTPUT.sub("", l))):
            digits = re.sub(r"\D", "", m.group(0))
            if len(digits) >= 10 and not re.fullmatch(r"\d{4}-\d{2}-\d{2}", m.group(0).strip()) \
                    and not PRODUCT_CODE.fullmatch(m.group(0).strip()):
                phones.append(f"phone number on line {i}")
    if emails or phones:
        report.add(rel, "contact details", "fail", "Shopify advises no email or phone in this file: " + "; ".join(sorted(set(emails + phones))))
    else:
        report.add(rel, "contact details", "pass")

    # dollar before a digit
    dollars = [f"line {i}" for i, l in enumerate(lines, 1) if DOLLAR.search(l)]
    if dollars:
        report.add(rel, "dollar before digit", "fail", "write the currency as a word or code: " + ", ".join(dollars))
    else:
        report.add(rel, "dollar before digit", "pass")

    # redlines (literal), comparisons, claim words
    cleared = [norm(s) for s in store["cleared"]]
    def exempt(line):
        n = norm(line)
        return any(c and c in n for c in cleared)
    red_hits = []
    for r in store["redlines"]:
        if len(r) < 2:
            continue
        rr = word_re([r])
        for i, l in enumerate(lines, 1):
            if rr.search(l):
                red_hits.append(f"line {i}: \"{r}\"")
    if red_hits:
        report.add(rel, "redlines", "fail", "store file section 3 redline found: " + "; ".join(red_hits))
    else:
        report.add(rel, "redlines", "pass", f"{len(store['redlines'])} redline(s) checked as literal text")
    comp_re = word_re(lists["comparison-words"])
    comp_hits = [f"line {i}: {m.group(0)}" for i, l in enumerate(lines, 1) if not exempt(l) for m in comp_re.finditer(URL.sub("", OUTPUT.sub("", l)))]
    if comp_hits:
        outcome = "warning" if store["comparisons_allowed"] else "fail"
        report.add(rel, "comparisons", outcome, ("section 3 allows comparisons; each still needs a cleared statement: " if store["comparisons_allowed"] else "section 3 does not allow comparisons: ") + "; ".join(comp_hits[:10]))
    else:
        report.add(rel, "comparisons", "pass")
    claim_re = word_re(lists["claim-words"])
    claim_hits = [f"line {i}: {m.group(0)}" for i, l in enumerate(lines, 1) if not exempt(l) for m in claim_re.finditer(URL.sub("", OUTPUT.sub("", l)))]
    if claim_hits:
        report.add(rel, "claim words", "warning", "for the person to keep, reword or clear: " + "; ".join(claim_hits[:15]))
    else:
        report.add(rel, "claim words", "pass")

    # spelling
    sp = [f"line {i}: {m.group(0)}" for i, l in enumerate(lines, 1) for m in SPELLING_RE.finditer(l)]
    if sp:
        report.add(rel, "American spelling", "warning", "British forms: " + "; ".join(sp[:10]))
    else:
        report.add(rel, "American spelling", "pass")

    # product lines named (what ai-visibility-audit's V03 reads)
    # The names come from fact_slots.parse_lines (the name before the colon). A line counts as named at the start of a bullet, or as a standalone word written with
    # a capital, so "oil-based" in another line's description does not name an "Oil" line.
    names = store["lines"]
    if names:
        def named(n):
            e = re.escape(n)
            bullet = re.compile(r"^\s*[-*]\s+" + e + r"(?![\w-])", re.I | re.M)
            cap = n[0].upper() + n[1:]
            word = re.compile(r"(?<![\w-])" + re.escape(cap) + r"(?![\w-])")
            return bool(bullet.search(text) or word.search(text))
        found = [n for n in names if named(n)]
        missing = [n for n in names if n not in found]
        if not found:
            report.add(rel, "product lines named", "fail", "no product line from store file section 2 appears at the start of a bullet or as a capitalized word; the audit would read this as Shopify's default")
        elif missing:
            report.add(rel, "product lines named", "warning", "named: " + "; ".join(found) + "; not named: " + "; ".join(missing))
        else:
            report.add(rel, "product lines named", "pass", f"all {len(names)} lines named: " + "; ".join(found))

    # links
    paths = []
    for i, l in enumerate(lines, 1):
        for m in STORE_LINK.finditer(l):
            p = (m.group(1) or "/").rstrip(".,;:")
            paths.append((i, p))
    if pages_dir is None:
        report.add(rel, "links", "skipped", f"{len(paths)} store link(s) not checked; run with --pages <date>")
        return
    present, unsaved, read, has_index = sitemap_index(pages_dir)
    status = fetch_status(pages_dir)
    std = set(lists["standard-paths"])
    policies = {urllib.parse.urlsplit(u).path.rstrip("/") for u in store["policy_urls"]}
    bad_links, unknown, ok = [], [], 0
    for i, p in paths:
        clean = urllib.parse.urlsplit(p).path.rstrip("/") or "/"
        if "{" in clean or "<" in clean:
            ok += 1
            continue
        if clean in std:
            ok += 1
            continue
        if clean.startswith("/policies/"):
            saved = (pages_dir / "policies" / (clean.rsplit("/", 1)[-1] + ".html")).exists()
            st = status.get(clean, "")
            if saved and st in ("", "200"):
                ok += 1
            elif saved:
                bad_links.append(f"line {i}: {p} (fetch status {st})")
            elif (pages_dir / "policies").exists():
                bad_links.append(f"line {i}: {p} (no saved policy page of that name)")
            else:
                unknown.append(f"line {i}: {p}")
            continue
        if clean in present:
            ok += 1
            continue
        fam = "/" + clean.strip("/").split("/", 1)[0] + "/"
        if fam in unsaved or not has_index:
            unknown.append(f"line {i}: {p}")
        else:
            bad_links.append(f"line {i}: {p} (not in the saved sitemaps)")
    if bad_links:
        report.add(rel, "links", "fail", "links to pages the saved sitemaps and policy pages do not show: " + "; ".join(bad_links[:10]))
    else:
        report.add(rel, "links", "pass", f"{ok} store link(s) found in the saved pages (sitemaps read: {', '.join(read) or 'none'})")
    if unknown:
        report.add(rel, "links not checkable", "skipped", "the sitemap or policy page for these was not saved: " + "; ".join(unknown[:10]))


def load_store(ws):
    try:
        sf = storefile.StoreFile(ws / "store" / "store.md")
        name = sf.field(1, "Store name")
        dom = sf.field(1, "Public domain")
        if not name.value:
            fail_input("store file section 1 has no store name; fill it with store-setup.")
        if not dom.value:
            fail_input("store file section 1 has no public domain; fill it with store-setup.")
        cleared = sf.field(3, "Statements the store makes")
        redl = sf.field(3, "Words, topics and comparisons")
        comp = sf.field(3, "Comparisons to named competitors allowed")
        never = sf.field(3, "Statements the store never makes")
        pol = sf.field(6, "Policy pages published")
        lines = storefile.line_names(sf)
        problems = storefile.line_problems(sf)
        blanks = []
        for sec, key in [(1, "Countries sold to"), (2, "The business in one line"), (2, "Product lines"),
                         (2, "The facts every product page states"), (3, "Statements the store makes"),
                         (3, "Statements the store never makes"), (3, "Words, topics and comparisons"),
                         (4, "Who buys"), (6, "Policy pages published"), (6, "Public contact email")]:
            f = sf.field(sec, key)
            if f.is_blank or f.is_open:
                blanks.append(f"section {sec} '{key}' ({'open' if f.is_open else 'blank'})")
    except storefile.StoreFileError as e:
        fail_input(str(e))
    host = urllib.parse.urlsplit(dom.value.split()[0]).hostname or ""
    return {
        "name": name.value,
        "domain_host": host.lower(),
        "cleared": [q for c in cleared.items() for q in re.findall(r'"([^"]{4,})"', c)] + cleared.items(),
        "redlines": redl.items(),
        "never": never.items(),
        "comparisons_allowed": comp.value.strip().lower().startswith("yes"),
        "policy_urls": [re.search(r"https?://\S+", p).group(0) for p in pol.items() if re.search(r"https?://\S+", p)],
        "lines": lines,
        "line_problems": problems,
        "blanks": blanks,
        "label_source": sf.label_source,
    }


def main():
    ap = argparse.ArgumentParser(description="Check agent-guide/agents.md.liquid (and llms-full.txt.liquid) and write agent-guide/check-<date>.md.")
    ap.add_argument("workspace", help="the store's workspace folder")
    ap.add_argument("--pages", metavar="YYYY-MM-DD", help="check store links against pages/<date>/ sitemaps and policy pages")
    ap.add_argument("--date", metavar="YYYY-MM-DD", help="date for the report's file name (default: the --pages date, else today, UTC)")
    a = ap.parse_args()
    ws = pathlib.Path(a.workspace)
    date = a.date or a.pages or datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
    for d in (date, a.pages):
        if d and not re.fullmatch(r"\d{4}-\d{2}-\d{2}", d):
            fail_input(f"'{d}' is not an ISO date (YYYY-MM-DD).")
    guide = ws / "agent-guide" / "agents.md.liquid"
    if not guide.exists():
        fail_input(f"there is no draft at {guide}; write it from assets/agents-md-template.liquid first.")
    lists, size_limit = read_lists()
    store = load_store(ws)
    pages_dir = None
    if a.pages:
        pages_dir = ws / "pages" / a.pages
        if not pages_dir.exists():
            fail_input(f"there is no {pages_dir}; save the public pages first or drop --pages.")
    report = Report()
    # product-line items not in the template's shape are store-setup's to fix: a warning, never a failure
    if store["line_problems"]:
        report.add("store/store.md", "product-line items", "warning",
                   "; ".join(f"'{n}': {pr}" for n, pr in store["line_problems"]) + "; fix the item with store-setup")
    else:
        report.add("store/store.md", "product-line items", "pass", f"{len(store['lines'])} item(s) in the template's shape")
    files = [guide]
    full = ws / "agent-guide" / "llms-full.txt.liquid"
    if full.exists():
        files.append(full)
    for f in files:
        check_file(f, "agent-guide/" + f.name, store, lists, size_limit, pages_dir, report)

    fails, warns, skips = report.count("fail"), report.count("warning"), report.count("skipped")
    if fails:
        result, code = f"fail: {fails} failure(s), {warns} warning(s), {skips} skipped", 1
    elif warns or skips:
        result, code = f"{'partial: ' if skips else ''}warnings only: {warns} warning(s), {skips} skipped", 2
    else:
        result, code = "pass: every check passed", 0

    out = ws / "agent-guide" / f"check-{date}.md"
    set_aside = None
    if out.exists():  # nothing is deleted: an earlier report of the same date is set aside
        sup = ws / "agent-guide" / "superseded"
        sup.mkdir(parents=True, exist_ok=True)
        n = 1
        while (sup / f"check-{date}-{n}.md").exists():
            n += 1
        set_aside = sup / f"check-{date}-{n}.md"
        out.rename(set_aside)
    md = [f"# Guide check, {date}", "", f"Result: {result}.", "",
          f"Store: {store['name']}. Files checked: {', '.join('agent-guide/' + f.name for f in files)}. Pages: {('pages/' + a.pages) if a.pages else 'not given'}.", "",
          "| file | check | outcome | detail |", "|---|---|---|---|"]
    for f, c, o, d in report.rows:
        md.append(f"| {f} | {c} | {o} | {d.replace('|', '/')} |")
    md += ["", "For a person to read against the guide (store file section 3; the check matches these only as literal text, so a statement or redline put in other words gets past it):", "",
           "Statements the store never makes:", ""]
    md += [f"- {n}" for n in store["never"]] or ["- none listed"]
    md += ["", "Redlines (words, topics and comparisons the store does not use), including descriptive ones:", ""]
    md += [f"- {r}" for r in store["redlines"]] or ["- none listed"]
    md += ["", "Coverage.",
           f"Inputs used: store file sections 1, 2, 3, 6 (labels from {store['label_source']}); references/guide-shape.md lists; " + (f"pages/{a.pages}/ sitemaps and policy pages." if a.pages else "no saved pages."),
           "Inputs missing: " + ("; ".join(store["blanks"]) if store["blanks"] else "none") + ("" if a.pages else "; saved pages (links not checked)") + ".",
           "Could not judge: whether each sentence is true of the store; whether a descriptive redline or a never-made statement is implied in other words; how Shopify renders the agents outputs; whether the live file matches this draft after caching.",
           f"Fine: {report.count('pass')} check(s) passed."]
    out.write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"Result: {result}.")
    for f, c, o, d in report.rows:
        if o != "pass":
            print(f"{o}: {f}: {c}: {d}")
    if set_aside:
        print(f"Set the earlier report aside as {set_aside.relative_to(ws)}.")
    print(f"Wrote {out.relative_to(ws)}.")
    sys.exit(code)


if __name__ == "__main__":
    main()
