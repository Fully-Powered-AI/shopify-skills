#!/usr/bin/env python3
"""Save a store's public pages into pages/<date>/ (schemas.md section 2). The one network script in the set.

    python3 -I scripts/fetch_pages.py <workspace> <domain> [--date YYYY-MM-DD] [--handles h1,h2] [--yes] [--dry-run]

Without --yes it prints the plan (every fixed path, and the rule for the sitemap-driven part) and fetches nothing.
With --yes it fetches: the fixed paths, the sitemap index and each child it names, then the product handles in
products-sitemap order up to the store file's sample size (section 9) or the --handles given, and the pages whose
handle contains a word from references/checks.md (fetch_page_handle_words) or that store file section 6 names.
--dry-run builds the full list from sitemaps already saved in pages/<date>/, prints it with any refusals, and writes
nothing; it makes no request.

Rules (contract section 5): plain GET only; a user agent naming the set; a pause between requests; no cookies, no
credentials; redirects followed only on the same domain; /admin, /account, /cart, /checkout(s), /orders and any other host
refused; one retry after a 429, honoring Retry-After up to a cap. Saved bytes are unchanged; fetch-log.csv has one
row per request, failures included.

Exit 0: every request returned 200 (or the dry run built its list). Exit 1: bad input, named in one sentence.
Exit 2: the plan was printed and needs the person's yes, or one or more requests failed (listed).
"""
import argparse
import csv
import datetime
import html
import importlib.util
import pathlib
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

sys.dont_write_bytecode = True  # keep the skill folder free of cache files
_spec = importlib.util.spec_from_file_location("common", pathlib.Path(__file__).resolve().parent / "common.py")
common = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(common)

USER_AGENT = "shopify-skills-ai-visibility-audit/0.1 (public page check by the store's operator; one request per second)"
PAUSE_SECONDS = 1          # contract section 5: a pause between requests
TIMEOUT_SECONDS = 20       # build choice: a slow page is logged as failed rather than waited on
RETRY_AFTER_CAP = 30       # build choice: the longest wait honored after a 429 before the one retry
REFUSED_SEGMENTS = {"admin", "account", "cart", "checkout", "checkouts", "orders"}   # contract section 5, and the private /orders path the default robots file disallows
LOCALE = re.compile(r"^[a-z]{2}(-[a-z]{2})?$")
HANDLE = re.compile(r"^[a-z0-9][a-z0-9._-]*$")

FIXED = [
    ("/robots.txt", "robots.txt"), ("/agents.md", "agents.md"), ("/llms.txt", "llms.txt"),
    ("/llms-full.txt", "llms-full.txt"), ("/.well-known/ucp", "ucp.json"), ("/sitemap.xml", "sitemap.xml"),
    ("/", "home.html"), ("/products.json?limit=250", "products.json"), ("/collections/all", "collections/all.html"),
]


def refusal(url, host):
    """Return the reason a URL is refused, or None."""
    u = urllib.parse.urlsplit(url)
    if u.scheme not in ("http", "https"):
        return "not an http address"
    if not common.same_domain(u.hostname or "", host):
        return f"off the domain ({u.hostname})"
    if u.username or u.password:
        return "carries credentials"
    segs = [s for s in urllib.parse.unquote(u.path).lower().split("/") if s]
    if ".." in segs:
        return "climbs out of the path"
    look = segs[:2] if segs and LOCALE.match(segs[0]) else segs[:1]
    for s in look:
        if s in REFUSED_SEGMENTS:
            return f"refused path /{s}"
    return None


def child_name(loc):
    base = urllib.parse.urlsplit(loc).path.rsplit("/", 1)[-1]
    return base if base.endswith(".xml") else base + ".xml"


def locs(text):
    return [html.unescape(x.strip()) for x in re.findall(r"<loc>\s*(.*?)\s*</loc>", text, re.S)]


def dynamic_plan(base, host, index_text, child_texts, n_sample, handles, page_words, named_pages):
    """From the sitemap index and its children, the list of (url, saved path) and the refusals."""
    plan, refused = [], []
    for loc in locs(index_text):
        why = refusal(loc, host)
        if why:
            refused.append((loc, why))
            continue
        plan.append((loc, child_name(loc)))
    prods, pgs = [], []
    for name, text in child_texts.items():
        for loc in locs(text):
            m = re.search(r"/products/([^/?#]+)$", urllib.parse.urlsplit(loc).path)
            p = re.search(r"/pages/([^/?#]+)$", urllib.parse.urlsplit(loc).path)
            if not (m or p):
                continue
            why = refusal(loc, host)
            if why:
                refused.append((loc, why))
                continue
            if m and name.startswith("sitemap_products") and m.group(1) not in prods:
                prods.append(m.group(1))
            if p and name.startswith("sitemap_pages") and any(w in p.group(1).lower() for w in page_words):
                pgs.append(p.group(1))
    chosen = handles if handles else prods[:n_sample]
    for h in chosen:
        plan.append((f"{base}/products/{h}", f"products/{h}.html"))
        plan.append((f"{base}/products/{h}.json", f"products/{h}.json"))
    for h in pgs + [x for x in named_pages if x not in pgs]:
        plan.append((f"{base}/pages/{h}", f"pages/{h}.html"))
    return plan, refused, chosen


class SameDomainRedirects(urllib.request.HTTPRedirectHandler):
    def __init__(self, host):
        self.host = host

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        why = refusal(newurl, self.host)
        if why:
            raise urllib.error.URLError(f"redirect to {newurl} refused: {why}")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def fetch(opener, url):
    """Return (status, body bytes or None, note)."""
    for attempt in (1, 2):
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT}, method="GET")
        try:
            with opener.open(req, timeout=TIMEOUT_SECONDS) as r:
                return r.status, r.read(), ""
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt == 1:
                wait = e.headers.get("Retry-After", "")
                wait = min(int(wait), RETRY_AFTER_CAP) if wait.isdigit() else RETRY_AFTER_CAP
                time.sleep(wait)
                continue
            return e.code, None, f"HTTP {e.code}"
        except (urllib.error.URLError, OSError) as e:
            return 0, None, str(getattr(e, "reason", e))[:200]
    return 429, None, "HTTP 429 after one retry"


def main():
    ap = argparse.ArgumentParser(description="Save a store's public pages into pages/<date>/ (schemas.md section 2).")
    ap.add_argument("workspace")
    ap.add_argument("domain", help="the store's public domain, for example https://www.example-store.com")
    ap.add_argument("--date", help="YYYY-MM-DD; default today (UTC)")
    ap.add_argument("--handles", help="comma-separated product handles to sample instead of the sitemap order")
    ap.add_argument("--yes", action="store_true", help="fetch; without it only the plan is printed")
    ap.add_argument("--dry-run", action="store_true", help="build the full list from sitemaps already saved in pages/<date>/; no request")
    a = ap.parse_args()
    ws = pathlib.Path(a.workspace)
    date = a.date or datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", date):
        print("error: --date must be YYYY-MM-DD.")
        return 1
    d = a.domain.strip()
    if not re.match(r"^https?://", d):
        d = "https://" + d
    u = urllib.parse.urlsplit(d)
    if u.path not in ("", "/") or u.query or u.username or not u.hostname or not re.fullmatch(r"[a-z0-9.-]+\.[a-z]{2,}", u.hostname.lower()):
        print("error: name the domain alone, for example https://www.example-store.com, with no path, query or login.")
        return 1
    host = u.hostname.lower()
    base = f"https://{host}"
    try:
        store = common.StoreFile(ws / "store" / "store.md")
        sd = common.host_of(store.require("domain").value)
        if not common.same_domain(sd, host):
            print(f"error: {host} is not the public domain in store file section 1 ({sd}); fetch only the store's own domain.")
            return 1
        sf = store.require("sample_size")
        m = re.match(r"\d+", sf.value)
        if not m:
            raise common.StoreFileError("Store file section 9, \"Product pages sampled per audit\", must be a whole number.")
        n_sample = int(m.group(0))
        named = [re.search(r"/pages/([^/?#]+)", x).group(1) for x in store.field("faq_pages").values()
                 if re.search(r"/pages/([^/?#]+)", x) and common.same_domain(common.host_of(x), host)]
        _, lists, _ = common.read_settings()
    except common.StoreFileError as e:
        print(f"error: {e}")
        return 1
    handles = []
    if a.handles:
        handles = [h.strip() for h in a.handles.split(",") if h.strip()]
        bad = [h for h in handles if not HANDLE.match(h)]
        if bad:
            print(f"error: not a product handle: {', '.join(bad)}; a handle is lowercase letters, digits and hyphens, as in the product URL.")
            return 1
    fixed = FIXED + [(f"/policies/{p}", f"policies/{p}.html") for p in lists["policy_files"]]
    folder = ws / "pages" / date

    if a.dry_run:
        idx = folder / "sitemap.xml"
        if not idx.exists():
            print(f"error: --dry-run needs a saved {idx}; without it, run without --dry-run to see the plan.")
            return 1
        children = {f.name: f.read_text(encoding="utf-8", errors="replace") for f in folder.glob("sitemap_*.xml")}
        plan, refused, chosen = dynamic_plan(base, host, idx.read_text(encoding="utf-8", errors="replace"), children,
                                             n_sample, handles, lists["fetch_page_handle_words"], named)
        full = [(base + p, f) for p, f in fixed] + plan
        print(f"dry run: {len(full)} requests planned for {host}, {len(refused)} refused; nothing fetched or written.")
        for url, f in full:
            print(f"  GET {url} -> {f}")
        for url, why in refused:
            print(f"  REFUSED {url}: {why}")
        print(f"products sampled: {', '.join(chosen) or 'none'} (store file section 9 sample size {n_sample})")
        return 0

    if not a.yes:
        print(f"plan only: nothing fetched. Run again with --yes to fetch these from {host}, one request per {PAUSE_SECONDS} second(s):")
        for p, f in fixed:
            print(f"  GET {base}{p} -> {f}")
        print("  then each child sitemap the index names -> sitemap_<name>.xml")
        if handles:
            for h in handles:
                print(f"  GET {base}/products/{h} and {base}/products/{h}.json -> products/{h}.html, .json")
        else:
            print(f"  then the first {n_sample} product handles in products-sitemap order -> products/<handle>.html and .json")
        print(f"  then pages whose handle contains {', '.join(lists['fetch_page_handle_words'])}" + (f", and {', '.join(named)}" if named else "") + " -> pages/<handle>.html")
        print("  and /products.json?page=2&limit=250 -> products-2.json if the first page holds 250 products")
        n_prod = len(handles) if handles else n_sample
        print(f"Request bound: {len(fixed)} fixed paths, plus one per child sitemap the index names, plus {2 * n_prod} product requests "
              f"({n_prod} product(s), page and JSON), plus one per matching page" + (f" ({len(named)} named in store file section 6 among them)" if named else "")
              + ", plus at most one second products page. Every request is to " + host + ".")
        if not handles:
            print("The product handles and matching pages are read from the sitemaps after the yes, in sitemap order; the fetch report names them, "
                  "and nothing else is requested. To choose the products now, pass --handles.")
        print(f"Refused always: {', '.join('/' + s for s in sorted(REFUSED_SEGMENTS))} and any other host. User agent: {USER_AGENT}")
        return 2

    if folder.exists() and any(folder.iterdir()):
        print(f"error: {folder} already holds files; pass another --date so earlier pages stay as they were.")
        return 1
    folder.mkdir(parents=True, exist_ok=True)
    opener = urllib.request.build_opener(SameDomainRedirects(host))
    log, failed = [], []

    def get(url, rel):
        why = refusal(url, host)
        stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%MZ")
        if why:
            log.append([url, rel, "", "0", stamp, f"refused: {why}"])
            return None
        status, body, note = fetch(opener, url)
        if status == 200 and body is not None:
            out = folder / rel
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_bytes(body)
        else:
            failed.append(f"{url} ({note or status})")
        log.append([url, rel, str(status), str(len(body) if body else 0), stamp, note])
        time.sleep(PAUSE_SECONDS)
        return body

    bodies = {}
    for p, f in fixed:
        bodies[f] = get(base + p, f)
    idx = (bodies.get("sitemap.xml") or b"").decode("utf-8", "replace")
    children = {}
    for loc in locs(idx):
        name = child_name(loc)
        if refusal(loc, host) is None and (name.startswith("sitemap_products") or name.startswith("sitemap_pages")):
            children[name] = (get(loc, name) or b"").decode("utf-8", "replace")
    plan, refused, chosen = dynamic_plan(base, host, idx, children, n_sample, handles, lists["fetch_page_handle_words"], named)
    for loc, why in refused:
        log.append([loc, "", "", "0", datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%MZ"), f"refused: {why}"])
    for url, rel in plan:
        if rel.startswith("sitemap_") and rel in children:
            continue
        get(url, rel)
    pj = bodies.get("products.json")
    if pj and pj.count(b'"handle"') >= 250:
        get(f"{base}/products.json?page=2&limit=250", "products-2.json")
    with open(folder / "fetch-log.csv", "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["url", "path", "status", "bytes", "fetched_at", "note"])
        w.writerows(log)
    saved = sum(1 for r in log if r[2] == "200")
    print(("partial: " if failed else "complete: ") + f"{saved} of {len(log)} requests saved to {folder}; products sampled: {', '.join(chosen) or 'none'}.")
    for f in failed:
        print(f"  failed: {f}")
    for loc, why in refused:
        print(f"  refused: {loc}: {why}")
    print(f"Next: python3 -I scripts/audit_pages.py {ws} --date {date}")
    return 2 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
