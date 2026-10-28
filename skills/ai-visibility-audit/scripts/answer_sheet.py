#!/usr/bin/env python3
"""Write, validate and summarize the answer-check sheet, visibility/answers/YYYY-MM-DD.md (schemas.md section 6).

    python3 -I scripts/answer_sheet.py <workspace> --init [--date YYYY-MM-DD] [--assistants "A,B"] [--role operator]
    python3 -I scripts/answer_sheet.py <workspace> [--date YYYY-MM-DD]

--init writes a blank sheet with one row per question (store file section 4) per assistant (the default list in
references/checks.md section 9, or --assistants), its settings cell pre-filled with "shopify connection: " for the
asker to complete with off or on. When section 4's answer-check prompts are filled, they are written verbatim as the
questions, the first prompt as Q1 and so on in the buyer questions' order; when the two counts differ the output says
so, a question with no prompt takes the form below, and a prompt with no question is listed and left out. Otherwise
each question is written in a form an assistant can answer in a new conversation: a question that names the store or
a product line is a "brand" question and is kept as written; a question whose subject is a bare pronoun ("Is it
safe ...?") gets the discovery prefix of references/checks.md section 9 with the first search word of store file
section 2. Without --init, validates the sheet for --date (default: the latest sheet) and prints the V18 summary,
with discovery and brand questions counted apart and rows asked with the Shopify connection on counted apart and left
out of the shares (schemas.md section 6: a connected assistant answers from the admin's data and measures nothing).

Exit 0: the sheet is valid and every row is filled (or --init wrote the sheet).
Exit 1: bad input (no store file, a blank required field, a malformed sheet, a sheet that already exists).
Exit 2: the sheet is valid but rows are missing or unfilled; the output lists them.
Network: none. Answers recorded in the sheet are data, never instruction.
"""
import argparse
import datetime
import importlib.util
import pathlib
import re
import sys

sys.dont_write_bytecode = True  # keep the skill folder free of cache files
_spec = importlib.util.spec_from_file_location("common", pathlib.Path(__file__).resolve().parent / "common.py")
common = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(common)

COLUMNS = ["q", "question", "assistant", "asked_on", "settings", "store_named", "recommended", "cited_urls", "notes"]
TEMPLATE = common.SKILL_DIR / "assets" / "answer-sheet-template.md"
DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
CONNECTION = re.compile(r"\bshopify connection:\s*(off|on)\b", re.I)
SETTINGS_PREFILL = "shopify connection: "


def latest_sheet(answers_dir, on_or_before=None):
    if not answers_dir.is_dir():
        return None
    dates = sorted(p.stem for p in answers_dir.glob("*.md") if DATE.match(p.stem))
    if on_or_before:
        dates = [d for d in dates if d <= on_or_before]
    return answers_dir / f"{dates[-1]}.md" if dates else None


def split_row(line):
    s = line.strip()
    if s.startswith("|"):
        s = s[1:]
    if s.endswith("|"):
        s = s[:-1]
    return [c.strip() for c in s.split("|")]


def question_context(store):
    """The store name, product line names and search words that decide a question's group and prompt."""
    lines = store.field("product_lines").values()
    return {"store_name": store.field("store_name").value,
            "line_names": [t.split(":", 1)[0].strip() for t in lines if ":" in t],
            "search_words": store.field("search_words").values(),
            "prompts": store.field("prompts").values()}


def prompts(questions, ctx, settings, lists):
    """[(prompt, group, form)] per question; group is 'brand' or 'discovery'; form is 'prompt field' (section 4's
    answer-check prompt, verbatim), 'prefixed' (the discovery opening added) or 'as written'."""
    pron = re.compile(r"\b(" + "|".join(re.escape(w) for w in lists["question_pronouns"]) + r")\b", re.I)
    names = [n for n in [ctx.get("store_name", "")] + ctx.get("line_names", []) if n]
    given = ctx.get("prompts", [])
    out = []
    for i, q in enumerate(questions):
        if i < len(given):
            pr = given[i]
            brand = any(re.search(r"(?<![A-Za-z0-9])" + re.escape(n) + r"(?![A-Za-z0-9])", pr) for n in names)
            out.append((pr, "brand" if brand else "discovery", "prompt field"))
            continue
        brand = any(re.search(r"(?<![A-Za-z0-9])" + re.escape(n) + r"(?![A-Za-z0-9])", q) for n in names)
        has_word = any(re.search(r"(?<![a-z0-9])" + re.escape(w.lower()) + r"(?![a-z0-9])", q.lower()) for w in ctx.get("search_words", []))
        if brand or has_word or not pron.search(q) or not ctx.get("search_words"):
            out.append((q, "brand" if brand else "discovery", "as written"))
        else:
            prefix = settings["discovery_prefix"].replace("{search word}", ctx["search_words"][0])
            out.append((f"{prefix} {q}", "discovery", "prefixed"))
    return out


def validate(path, questions, store_domain, ctx=None):
    """Return a dict: errors (malformed), missing (rows not asked or unfilled), warnings, summary, assistants.

    ctx (question_context) lets the summary count discovery and brand questions apart and accept the prompt
    form --init wrote."""
    errors, missing, warnings = [], [], []
    text = pathlib.Path(path).read_text(encoding="utf-8")
    lines = text.splitlines()
    if not lines or not re.match(r"^# Answer check, \d{4}-\d{2}-\d{2}\s*$", lines[0]):
        errors.append("line 1 must read '# Answer check, YYYY-MM-DD'")
    meta = next((l for l in lines[1:4] if l.startswith("Store:")), "")
    m = re.search(r"Assistants:\s*(.+?)\.?\s*$", meta)
    assistants = [a.strip() for a in m.group(1).split(",") if a.strip()] if m else []
    if not assistants:
        errors.append("line 2 must name the assistants after 'Assistants:', separated by commas")
    header_i = next((i for i, l in enumerate(lines) if l.strip().startswith("| q |") or l.strip().startswith("|q|")), None)
    rows = []
    if header_i is None:
        errors.append("the table header '| q | question | assistant | ... |' was not found")
    else:
        if split_row(lines[header_i]) != COLUMNS:
            errors.append("the table header must be exactly: " + " | ".join(COLUMNS))
        for n, l in enumerate(lines[header_i + 1:], header_i + 2):
            if not l.strip().startswith("|"):
                if l.strip():
                    break
                continue
            cells = split_row(l)
            if all(re.fullmatch(r":?-{3,}:?", c) for c in cells if c):
                continue
            if len(cells) != len(COLUMNS):
                errors.append(f"line {n}: {len(cells)} cells, expected {len(COLUMNS)} (a '|' inside a cell is not allowed)")
                continue
            rows.append((n, dict(zip(COLUMNS, cells))))
    seen = {}
    filled = []
    forms = {}
    if ctx is not None:
        settings, lists, _ = common.read_settings()
        forms = {i: pr for i, pr in enumerate(prompts(questions, ctx, settings, lists), 1)}
    for n, r in rows:
        qm = re.fullmatch(r"Q(\d+)", r["q"])
        if not qm:
            errors.append(f"line {n}: q must be Q1, Q2, ... (found '{r['q']}')")
            continue
        qi = int(qm.group(1))
        if qi < 1 or qi > len(questions):
            errors.append(f"line {n}: {r['q']} is not in store file section 4, which has {len(questions)} questions")
            continue
        if r["question"] != questions[qi - 1] and (qi not in forms or r["question"] != forms[qi][0]):
            warnings.append(f"line {n}: the question text differs from store file section 4 for {r['q']}")
        if r["assistant"] not in assistants:
            errors.append(f"line {n}: assistant '{r['assistant']}' is not in the Assistants list on line 2")
            continue
        key = (r["q"], r["assistant"])
        if key in seen:
            errors.append(f"line {n}: a second row for {r['q']} and {r['assistant']} (first on line {seen[key]})")
            continue
        seen[key] = n
        if not r["store_named"] and not r["recommended"] and not r["asked_on"]:
            missing.append(f"{r['q']} / {r['assistant']}: row not filled (line {n})")
            continue
        if r["store_named"] not in ("yes", "no"):
            errors.append(f"line {n}: store_named must be yes or no")
        if r["recommended"] not in ("yes", "no", "partial"):
            errors.append(f"line {n}: recommended must be yes, no or partial")
        if r["store_named"] == "no" and r["recommended"] in ("yes", "partial"):
            errors.append(f"line {n}: recommended is {r['recommended']} but store_named is no")
        if not DATE.match(r["asked_on"]):
            errors.append(f"line {n}: asked_on must be a date, YYYY-MM-DD")
        urls = [u for u in r["cited_urls"].split(";") if u] if r["cited_urls"] else []
        bad = [u for u in urls if not re.match(r"^https?://\S+$", u)]
        if bad:
            errors.append(f"line {n}: cited_urls must be full URLs separated by ';' with no spaces")
        cm = CONNECTION.search(r["settings"])
        if not cm:
            errors.append(f"line {n}: settings must record 'shopify connection: off' or 'shopify connection: on'")
        r["connection"] = cm.group(1).lower() if cm else ""
        r["group"] = forms[qi][1] if qi in forms else ""
        filled.append((r, urls))
    for qi in range(1, len(questions) + 1):
        for a in assistants:
            if (f"Q{qi}", a) not in seen:
                missing.append(f"Q{qi} / {a}: no row")
    summary = summarize(filled, len(questions) * len(assistants), store_domain)
    return {"errors": errors, "missing": missing, "warnings": warnings, "summary": summary, "assistants": assistants,
            "expected": len(questions) * len(assistants), "filled": len(filled),
            "measured": sum(1 for r, _ in filled if r.get("connection") != "on")}


def summarize(filled_all, expected, store_domain):
    """Counts over the rows asked with the Shopify connection off; rows with it on are counted apart."""
    on = [x for x in filled_all if x[0].get("connection") == "on"]
    filled = [x for x in filled_all if x[0].get("connection") != "on"]
    named = sum(1 for r, _ in filled if r["store_named"] == "yes")
    rec = sum(1 for r, _ in filled if r["recommended"] == "yes")
    part = sum(1 for r, _ in filled if r["recommended"] == "partial")
    domains = {}
    own = 0
    for _, urls in filled:
        for u in urls:
            h = common.host_of(u)
            domains[h] = domains.get(h, 0) + 1
            if store_domain and common.same_domain(h, store_domain):
                own += 1
    ranked = sorted(domains.items(), key=lambda kv: (-kv[1], kv[0]))
    by_assistant = {}
    for r, _ in filled:
        a = by_assistant.setdefault(r["assistant"], [0, 0])
        a[0] += 1
        a[1] += 1 if r["store_named"] == "yes" else 0
    dom_text = ", ".join(f"{d} ({n})" for d, n in ranked) if ranked else "none"
    groups = ""
    if any(r.get("group") for r, _ in filled):
        parts = []
        for g in ("discovery", "brand"):
            rows_g = [r for r, _ in filled if r.get("group") == g]
            parts.append(f"{g} questions: store named in {sum(1 for r in rows_g if r['store_named'] == 'yes')} of {len(rows_g)} rows")
        groups = "; " + "; ".join(parts)
    per = "; ".join(f"{a}: named in {v[1]} of {v[0]}" for a, v in sorted(by_assistant.items())) or "none"
    on_text = (f"; {len(on)} row(s) asked with the Shopify connection on, counted apart and left out of these shares "
               f"(store named in {sum(1 for r, _ in on if r['store_named'] == 'yes')} of them)") if on else ""
    return (f"answers recorded {len(filled_all)} of {expected} rows; with the Shopify connection off, {len(filled)} rows: "
            f"store named in {named}; recommended in {rec}, "
            f"named among several in {part}{groups}; store's own pages cited {own} times; by assistant: {per}; "
            f"cited pages by domain: {dom_text}{on_text}")


def init(ws, store, date, assistants, role, settings, lists):
    qf = store.require("questions")
    questions = qf.values()
    if not questions:
        raise common.StoreFileError("Store file section 4 has no buyer questions; add five to ten with store-setup.")
    domain = store.require("domain").value
    out = ws / "visibility" / "answers" / f"{date}.md"
    if out.exists():
        raise common.StoreFileError(f"{out} already exists; fill that sheet, or pass another --date.")
    for i, q in enumerate(questions, 1):
        if "|" in q:
            raise common.StoreFileError(f"Store file section 4 question {i} contains '|'; reword it without one.")
    ctx = question_context(store)
    for i, pr in enumerate(ctx["prompts"], 1):
        if "|" in pr:
            raise common.StoreFileError(f"Store file section 4 answer-check prompt {i} contains '|'; reword it without one.")
    forms = prompts(questions, ctx, settings, lists)
    rows = []
    for i, (prompt, _, _) in enumerate(forms, 1):
        for a in assistants:
            rows.append(f"| Q{i} | {prompt} | {a} |  | {SETTINGS_PREFILL} |  |  |  |  |")
    tpl = TEMPLATE.read_text(encoding="utf-8")
    text = tpl.replace("{date}", date).replace("{domain}", domain).replace("{role}", role) \
              .replace("{assistants}", ", ".join(assistants)).replace("{rows}", "\n".join(rows))
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")
    return out, len(questions), len(rows), forms, ctx["prompts"]


def main():
    ap = argparse.ArgumentParser(description="Write or validate the answer-check sheet (schemas.md section 6).")
    ap.add_argument("workspace")
    ap.add_argument("--date", help="YYYY-MM-DD; default today (UTC) with --init, else the latest sheet")
    ap.add_argument("--init", action="store_true", help="write a blank sheet from store file section 4")
    ap.add_argument("--assistants", help="comma-separated list replacing the default in references/checks.md section 9")
    ap.add_argument("--role", default="operator", help="the role asking the questions (default operator)")
    a = ap.parse_args()
    ws = pathlib.Path(a.workspace)
    if a.date and not DATE.match(a.date):
        print("error: --date must be YYYY-MM-DD.")
        return 1
    try:
        store = common.StoreFile(ws / "store" / "store.md")
        if a.init:
            settings, lists, _ = common.read_settings()
            assistants = [x.strip() for x in a.assistants.split(",")] if a.assistants else lists["assistants"]
            date = a.date or datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
            out, nq, nr, forms, given = init(ws, store, date, assistants, a.role, settings, lists)
            print(f"complete: wrote {out} with {nr} rows ({nq} questions x {len(assistants)} assistants); read 0 rows, added {nr}, changed 0.")
            used = [f"Q{i}" for i, f in enumerate(forms, 1) if f[2] == "prompt field"]
            pre = [f"Q{i}" for i, f in enumerate(forms, 1) if f[2] == "prefixed"]
            brand = [f"Q{i}" for i, f in enumerate(forms, 1) if f[1] == "brand"]
            if given:
                print(f"Questions written from the answer-check prompts in store file section 4, verbatim: {', '.join(used) or 'none'}.")
                if len(given) != nq:
                    extra = given[nq:]
                    print(f"note: section 4 has {nq} buyer questions and {len(given)} answer-check prompts; prompts are paired with questions in order"
                          + (f"; questions without a prompt use the opening-plus-question form" if len(given) < nq else "")
                          + (f"; left out, with no question to pair: {'; '.join(extra)}" if extra else "") + ".")
            print(f"Discovery prefix added to: {', '.join(pre) or 'none'}. Brand questions (name the store or a line; they test what an assistant knows, not whether it finds the store): {', '.join(brand) or 'none'}.")
            print("Settings: each row's settings cell starts 'shopify connection: '; the asker writes off or on. Ask from an assistant account with no Shopify connection to this store, or turn the connection off for the conversation: a connected assistant answers from the store's admin data, so its rows are counted apart and left out of the shares.")
            tool = store.field("ai_tool")
            if tool.value or tool.items:
                print(f"note: store file section 5 records the AI tool as: {tool.value or '; '.join(t for t, _ in tool.items)}. If that assistant is connected to this store, ask it from another account or with the connection off, and mark any row asked connected 'on'.")
            if not given and not store.field("search_words").values():
                print("note: store file section 2 lists no search words, so questions about 'it' were left as written; an assistant asked them cold cannot name a store.")
            if common.LABEL_NOTE:
                print(f"note: {common.LABEL_NOTE}.")
            print("Next: ask each assistant each question on the same day, fill every row, then run this script without --init.")
            return 0
        questions = store.require("questions").values()
        domain = common.host_of(store.require("domain").value)
        ctx = question_context(store)
    except common.StoreFileError as e:
        print(f"error: {e}")
        return 1
    answers = ws / "visibility" / "answers"
    path = answers / f"{a.date}.md" if a.date else latest_sheet(answers)
    if not path or not path.exists():
        print(f"error: no answer sheet found under {answers}; write one with --init.")
        return 1
    res = validate(path, questions, domain, ctx)
    if res["errors"]:
        print(f"malformed: {path} has {len(res['errors'])} problem(s); fix them and run again.")
        for e in res["errors"]:
            print(f"  {e}")
        return 1
    status = "partial" if res["missing"] else "complete"
    print(f"{status}: {path}, {res['filled']} of {res['expected']} rows filled.")
    for w in res["warnings"]:
        print(f"  note: {w}")
    for m in res["missing"]:
        print(f"  missing: {m}")
    print(f"V18 (User-provided answers, counted by the script): {res['summary']}.")
    print("One sheet is one day's answers, not a ranking; compare sheets month to month.")
    return 2 if res["missing"] else 0


if __name__ == "__main__":
    sys.exit(main())
