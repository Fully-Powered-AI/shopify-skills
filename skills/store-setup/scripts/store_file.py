#!/usr/bin/env python3
"""Create or validate the store file, <workspace>/store/store.md.

    python3 -I store_file.py <workspace> [--init] [--template PATH]

--init copies the template to store/store.md and refuses to overwrite one that
exists. Without --init the file is validated against the template, which is
read at run time (default: ../assets/store-template.md beside this script), so
a template change reaches the check without editing this file.

Exit codes (contract section 5): 0 valid; 1 malformed or a required field
blank (the first line is one plain sentence naming the section and the rule);
2 valid with [open] items, blank optional fields or a check to confirm
(listed, the last prefixed "check:"). argparse usage
errors also exit 2, before anything is read.

Product-line items (section 2) are read through the shared module
fact_slots.py beside this file (schemas.md sections 3 and 12): an item with no
name before a colon is malformed (exit 1); an item with no category part, or a
'same category' with no category above it, is an open item with a check: line
(exit 2).

Other skills import the reader by path:

    import importlib.util, pathlib
    spec = importlib.util.spec_from_file_location("store_file", PATH_TO_THIS_FILE)
    store_file = importlib.util.module_from_spec(spec); spec.loader.exec_module(store_file)
    data = store_file.read_store_file("<workspace>/store/store.md")
    store_file.field(data, 2, "The facts every product page states")["items"]

Writing rules read here (schemas.md section 3; the template's first section):
a field is a bullet whose template text ends with a colon; its value follows
on the same line with the source mark last; an indented line under a field is
template guidance when it carries no mark and the person's detail when it
carries one; a field's line is never stated twice. Standard library only.
"""
import argparse
import importlib.util
import re
import shutil
import sys
from pathlib import Path

VERSION = "0.1.0"
HERE = Path(__file__).resolve().parent
DEFAULT_TEMPLATE = HERE.parent / "assets" / "store-template.md"


def _load_fact_slots():
    """The set's shared reader of section 2 (schemas.md section 12), loaded by path from beside this file, so it
    works under python3 -I and when another skill imports this module by path."""
    spec = importlib.util.spec_from_file_location("fact_slots", HERE / "fact_slots.py")
    module = importlib.util.module_from_spec(spec)
    sys.dont_write_bytecode = True
    spec.loader.exec_module(module)
    return module


fact_slots = _load_fact_slots()

# The four source marks (template, second paragraph).
MARKS = ("owner", "observed", "default", "open")
MARK_ANY = re.compile(r"\[(owner|observed|default|open)\]")
TRAILING_BRACKET = re.compile(r"\[([^\[\]]{1,40})\]\s*$")
HEADING = re.compile(r"^## (\d+)\. (.+?)\s*$")
LEVEL2 = re.compile(r"^## ")
LOG_ENTRY = re.compile(r"^\d{4}-\d{2}-\d{2}, [^,]+, .+")

# Required fields for a usable store file: (section, opening words of the
# label, minimum count of settled values or items, rule kind). Source: the
# store-setup script specification of 2026-10-21.
REQUIRED = [
    (1, "Store name", 1, "value"),
    (1, "Public domain", 1, "url"),
    (2, "The business in one line", 1, "value"),
    (2, "Product lines", 1, "items"),
    (2, "The facts every product page states", 3, "items"),
    (4, "The questions buyers ask before buying", 3, "items"),
    (6, "Policy pages published", 4, "items-or-none"),
    (7, "Who approves a change to product data", 1, "role"),
    (7, "Who pastes theme files", 1, "role"),
    (8, "How the skills reach the store", 1, "entrance"),
]
# The three entrances (contract section 8; template section 8).
ENTRANCES = ("connection", "exports", "public")
# Roles used when the store file's section 7 table cannot be read (template section 7).
DEFAULT_ROLES = ("owner", "operator", "support", "finance")


def norm(text):
    return " ".join(text.split())


class Problem(Exception):
    """A malformed store file: the message is the one plain sentence the person reads."""


def split_sections(text):
    """Return ([{num, title, line, body: [(lineno, text)]}], stray_level2_lines)."""
    sections, stray = [], []
    current = None
    for n, line in enumerate(text.splitlines(), start=1):
        m = HEADING.match(line)
        if m:
            current = {"num": int(m.group(1)), "title": m.group(2), "line": n, "body": []}
            sections.append(current)
        elif LEVEL2.match(line):
            stray.append((n, line.strip()))
        elif current is not None:
            current["body"].append((n, line))
    return sections, stray


def is_indented(line):
    return line[:1] in (" ", "\t") and line.strip() != ""


def bullet_blocks(body):
    """Top-level bullets with their indented lines: [(lineno, text, [(lineno, text)])]."""
    blocks, current = [], None
    for n, line in body:
        if line.startswith("- "):
            current = (n, line[2:].rstrip(), [])
            blocks.append(current)
        elif current is not None and is_indented(line):
            current[2].append((n, line.strip()))
        elif line.strip() == "" and current is not None:
            continue
        else:
            current = None
    return blocks


def read_template(path):
    """Headings, field labels and guidance lines, section by section."""
    text = Path(path).read_text(encoding="utf-8")
    sections, _ = split_sections(text)
    out = {}
    for s in sections:
        labels, guidance = [], {}
        if s["num"] != 11:
            for _, t, cont in bullet_blocks(s["body"]):
                if t.rstrip().endswith(":"):
                    label = norm(t)
                    labels.append(label)
                    guidance[label] = {norm(c) for _, c in cont}
        out[s["num"]] = {"title": s["title"], "labels": labels, "guidance": guidance,
                         "roles": table_roles(s["body"])}
    return out


def table_roles(body):
    rows, seen_header = [], False
    for _, line in body:
        if line.startswith("|"):
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if not seen_header:
                seen_header = True
                continue
            if all(re.fullmatch(r":?-{3,}:?", c) for c in cells if c):
                continue
            if cells and cells[0]:
                rows.append(cells[0].lower())
        else:
            seen_header = False
    return rows


def split_mark(text):
    """Return (value, mark, problem) for the text after a label or an indented line."""
    text = text.strip()
    m = TRAILING_BRACKET.search(text)
    mark = None
    if m:
        word = m.group(1).strip()
        if word in MARKS:
            mark = word
            text = text[: m.start()].rstrip()
        elif re.fullmatch(r"[a-z][a-z -]*", word):
            return text, None, f"'[{word}]' is not a mark; use [owner], [observed], [default] or [open]"
    if MARK_ANY.search(text):
        return text, mark, "a source mark sits inside the line; the mark goes last"
    return text, mark, None


def read_store_file(path, template_path=None):
    """Parse the store file. Returns {section number: section dict}.

    A section dict has title, line, fields {label: field}, roles (section 7
    table) and entries (section 11). A field is {line, value, mark, items:
    [{line, text, mark}]}. Raises Problem with one plain sentence when the
    file breaks a writing rule.
    """
    template = read_template(template_path or DEFAULT_TEMPLATE)
    text = Path(path).read_text(encoding="utf-8")
    sections, stray = split_sections(text)
    if stray:
        n, line = stray[0]
        raise Problem(f"line {n}: '{line}' is not a numbered section heading; headings are fixed as in the template")
    nums = [s["num"] for s in sections]
    for num in sorted(template):
        if num not in nums:
            raise Problem(f"section {num} ('## {num}. {template[num]['title']}') is missing; copy it from the template")
    for s in sections:
        if s["num"] not in template:
            raise Problem(f"line {s['line']}: section {s['num']} is not in the template")
        if nums.count(s["num"]) > 1:
            raise Problem(f"section {s['num']} appears more than once")
        if s["title"] != template[s["num"]]["title"]:
            raise Problem(f"section {s['num']}: the heading reads '{s['title']}'; the template has '{template[s['num']]['title']}'")
    if nums != sorted(nums):
        raise Problem("sections are out of order: " + ", ".join(str(n) for n in nums) + "; they run 1 to 11")
    out = {}
    for s in sections:
        num, tpl = s["num"], template[s["num"]]
        sec = {"title": s["title"], "line": s["line"], "fields": {}, "entries": [],
               "roles": table_roles(s["body"]) or tpl["roles"]}
        out[num] = sec
        for n, t, cont in bullet_blocks(s["body"]):
            if num == 11:
                if not LOG_ENTRY.match(t.strip()):
                    raise Problem(f"section 11, line {n}: a log entry reads 'YYYY-MM-DD, role, what was decided, which section changed'")
                sec["entries"].append({"line": n, "text": t.strip()})
                continue
            nt = norm(t)
            label = None
            for cand in tpl["labels"]:
                if nt.startswith(cand) and (label is None or len(cand) > len(label)):
                    label = cand
            if label is None:
                raise Problem(f"section {num}, line {n}: '{short(nt)}' is not a field of the template; extra detail goes on an indented line under a field")
            if label in sec["fields"]:
                raise Problem(f"section {num}, line {n}: the field '{short(label)}' is stated twice; scripts read one line per field")
            value, mark, problem = split_mark(nt[len(label):])
            if problem:
                raise Problem(f"section {num}, line {n}: {problem}")
            if value and mark is None:
                raise Problem(f"section {num}, line {n}: the value '{short(value)}' has no source mark; end the line with [owner], [observed], [default] or [open]")
            items = []
            for cn, ct in cont:
                if norm(ct) in tpl["guidance"].get(label, set()):
                    continue
                itext = ct[2:] if ct.startswith("- ") else ct
                ivalue, imark, iproblem = split_mark(itext)
                if iproblem:
                    raise Problem(f"section {num}, line {cn}: {iproblem}")
                if imark is None:
                    raise Problem(f"section {num}, line {cn}: the indented line '{short(ivalue)}' has no source mark; detail lines carry their own mark")
                items.append({"line": cn, "text": ivalue, "mark": imark})
            sec["fields"][label] = {"line": n, "value": value, "mark": mark, "items": items}
    return out


def field(data, section, opening):
    """The field of a section whose label starts with the given opening words, or None."""
    for label, f in data.get(section, {}).get("fields", {}).items():
        if label.startswith(opening):
            return f
    return None


def short(text, width=70):
    text = norm(text)
    return text if len(text) <= width else text[: width - 3] + "..."


def settled(f):
    """Values and items that carry a mark other than [open]."""
    vals = []
    if f["value"] and f["mark"] != "open":
        vals.append(f["value"])
    vals += [i["text"] for i in f["items"] if i["mark"] != "open"]
    return vals


def has_open(f):
    return f["mark"] == "open" or any(i["mark"] == "open" for i in f["items"])


def validate(data, template):
    """Return (problems, open_lines, blank_optional, warnings)."""
    problems, open_lines, blank, warnings = [], [], [], []
    required_labels = set()
    for num, opening, minimum, kind in REQUIRED:
        f = field(data, num, opening)
        label = next((l for l in template[num]["labels"] if l.startswith(opening)), opening)
        required_labels.add((num, label))
        if f is None:
            problems.append(f"section {num}: the required field '{short(label, 50)}' is missing; copy its line from the template")
            continue
        vals = settled(f)
        if not vals and not has_open(f):
            problems.append(f"section {num}: the required field '{short(label, 50)}' is blank; other skills stop here")
            continue
        if not vals:
            continue  # open: reported below as a required open item
        if kind == "url" and not vals[0].startswith(("https://", "http://")):
            problems.append(f"section {num}: the public domain is written as https://..., found '{short(vals[0], 40)}'")
        if kind == "items-or-none":
            if not (len(vals) == 1 and vals[0].strip("`").lower() == "none") and len(vals) < minimum:
                if not has_open(f):
                    problems.append(f"section {num}: list the four policy pages (shipping, refund, privacy, terms) one per indented line, writing 'none' for a page that does not exist, or write none; found {len(vals)}")
        elif kind == "items" and len(vals) < minimum and not has_open(f):
            problems.append(f"section {num}: '{short(label, 50)}' needs at least {minimum} lines; found {len(vals)}")
        if kind == "role":
            roles = data[num]["roles"] or list(DEFAULT_ROLES)
            if not role_only(vals[0], roles):
                problems.append(f"section {num}: '{short(label, 50)}' names a role from the table ({', '.join(roles)}), never a person; found '{short(vals[0], 30)}'")
        if kind == "entrance":
            bad = [p for v in vals for p in entrance_parts(v) if not ENTRANCE_WORD.search(p.lower())]
            if bad:
                problems.append(f"section {num}: each entrance is one of connection, exports, public, separated by commas or 'and'; found '{short(bad[0], 40)}'")
            elif any(re.search(r"\bconnection\b", p.lower()) for v in vals for p in entrance_parts(v)):
                problems.extend(connection_problems(data, vals, warnings))
    line_problems, line_checks = product_line_checks(data)
    problems.extend(line_problems)
    warnings.extend(line_checks)
    for num in sorted(data):
        if num == 11:
            continue
        for label in template[num]["labels"]:
            f = data[num]["fields"].get(label)
            if f is None:
                if (num, label) not in required_labels:
                    blank.append(f"section {num}: '{short(label, 60)}' line missing (optional)")
                continue
            if f["mark"] == "open":
                tag = "required, open" if (num, label) in required_labels else "open"
                open_lines.append(f"section {num}, line {f['line']}: {tag}: {short(label, 60)}")
            for i in f["items"]:
                if i["mark"] == "open":
                    open_lines.append(f"section {num}, line {i['line']}: open item under '{short(label, 40)}': {short(i['text'], 40)}")
            if not f["value"] and not f["items"] and f["mark"] is None and (num, label) not in required_labels:
                blank.append(f"section {num}, line {f['line']}: blank (optional): {short(label, 60)}")
    return problems, open_lines, blank, warnings


ITEM_SHAPE = "`<name>: <what it is>, <who it is for>; category <the full Shopify product category path>`, or end it with `same category`"


def product_line_checks(data):
    """Each settled product-line item through fact_slots.parse_lines (schemas.md section 3).

    Returns (problems, checks): no name before a colon is a problem (exit 1); no category part, or 'same category'
    with nothing above it, is a check (exit 2). Items marked [open] are reported as open items, not here."""
    f = field(data, 2, "Product lines")
    if not f:
        return [], []
    items = [i for i in f["items"] if i["mark"] != "open"]
    parsed = fact_slots.parse_lines([i["text"] for i in items])
    problems, checks = [], []
    for item, line in zip(items, parsed):
        if ":" not in item["text"] or not line["name"]:
            problems.append(f"section 2, line {item['line']}: the product line '{short(item['text'], 40)}' has no name before a colon; "
                            f"write it as {ITEM_SHAPE}")
        elif line["problem"]:
            checks.append(f"section 2, line {item['line']}: the product line '{short(line['name'], 30)}': {line['problem']}; "
                          f"add the category as the admin shows it ({ITEM_SHAPE}), then the catalog check can run")
    return problems, checks


def role_only(value, roles):
    """True when the value names a role from the table and no person.

    A value naming a person is refused even when a role word also appears:
    an '@', or a capitalized word that is neither a role nor the value's first
    word, reads as a name ('Jane Doe (owner)')."""
    low = value.lower()
    if not any(re.search(r"\b" + re.escape(r) + r"\b", low) for r in roles):
        return False
    if "@" in value:
        return False
    words = re.findall(r"[A-Za-z][A-Za-z'-]*", value)
    for i, w in enumerate(words):
        if i > 0 and w[0].isupper() and w.lower() not in roles:
            return False
    return True


ENTRANCE_WORD = re.compile(r"^\W*(" + "|".join(ENTRANCES) + r")\b")
NOT_CONFIRMED = re.compile(r"\b(not (yet )?(confirmed|connected)|unconfirmed|no connection|none)\b")


def entrance_parts(value):
    """The parts of an entrance value, split on commas and 'and' outside brackets."""
    parts, depth, buf = [], 0, ""
    for ch in value:
        depth += ch == "("
        depth -= ch == ")"
        if ch == "," and depth == 0:
            parts.append(buf)
            buf = ""
        else:
            buf += ch
    parts.append(buf)
    out = []
    for p in parts:
        out += [q for q in re.split(r"\band\b(?![^()]*\))", p) if q.strip()]
    return [norm(q) for q in out]


def connection_problems(data, vals, warnings):
    """Section 8 lists 'connection': the tool is named there or in section 5,
    and section 5 does not say the connection is unconfirmed (warning, exit 2)."""
    tool_in_8 = any(re.search(r"\bconnection\b\W*\S", p) for v in vals for p in entrance_parts(v)
                    if re.search(r"\bconnection\b", p.lower()))
    f5 = field(data, 5, "The AI tool the person uses")
    v5 = settled(f5) if f5 else []
    tool_in_5 = bool(v5) and not re.match(r"^\W*none\b", v5[0].lower())
    if v5 and NOT_CONFIRMED.search(v5[0].lower()):
        warnings.append(f"section 8 lists connection, but section 5 says the connection is not confirmed ('{short(v5[0], 40)}'); confirm it or drop connection from section 8")
    if not tool_in_8 and not tool_in_5:
        return ["section 8: 'connection' names the AI tool it goes through, as 'connection (Claude)', or section 5 names it"]
    return []


def init(workspace, template):
    target = workspace / "store" / "store.md"
    if target.exists():
        print("NOT CREATED: store/store.md already exists; this script never overwrites it. Run without --init to validate it.")
        return 1
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(template, target)
    print(f"CREATED: store/store.md from the template ({template.name}); nothing else was written.")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description="Create (--init) or validate the store file, store/store.md.")
    ap.add_argument("workspace", help="the workspace folder")
    ap.add_argument("--init", action="store_true", help="copy the template to store/store.md; refuses to overwrite")
    ap.add_argument("--template", default=str(DEFAULT_TEMPLATE), help="the store file template (default: ../assets/store-template.md)")
    a = ap.parse_args(argv)
    workspace = Path(a.workspace)
    template = Path(a.template)
    if not workspace.is_dir():
        print(f"MALFORMED INPUT: the workspace folder {workspace} does not exist; name an existing folder.")
        return 1
    if not template.is_file():
        print(f"MALFORMED INPUT: the template {template} was not found; pass --template with its path.")
        return 1
    if a.init:
        return init(workspace, template)
    path = workspace / "store" / "store.md"
    if not path.is_file():
        print("MALFORMED: store/store.md does not exist; run with --init to create it from the template.")
        return 1
    tpl = read_template(template)
    try:
        data = read_store_file(path, template)
    except Problem as p:
        print(f"MALFORMED: {p}.")
        return 1
    problems, open_lines, blank, warnings = validate(data, tpl)
    counts = (f"read store/store.md: {sum(len(s['fields']) for s in data.values())} fields, "
              f"{sum(len(f['items']) for s in data.values() for f in s['fields'].values())} indented lines, "
              f"{len(data.get(11, {}).get('entries', []))} log entries")
    if problems:
        print(f"MALFORMED: {problems[0]}.")
        for p in problems[1:]:
            print(f"also: {p}")
        print(counts)
        return 1
    if open_lines or blank or warnings:
        checks = f", {len(warnings)} to check" if warnings else ""
        print(f"VALID WITH OPEN ITEMS: {len(open_lines)} open, {len(blank)} blank optional{checks}.")
        for line in open_lines + blank + ["check: " + w for w in warnings]:
            print(f"  {line}")
        print(counts)
        return 2
    print("VALID: every section present and in order, every line marked, every required field filled.")
    print(counts)
    return 0


if __name__ == "__main__":
    sys.exit(main())
