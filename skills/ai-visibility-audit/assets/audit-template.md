# AI visibility audit, {date}{title_suffix}
{status_line}
Store: {domain}. Pages read: `{pages_dir}`. Sampled products: {sampled}. Written by `audit_pages.py`; every count below is Measured from the saved files on {date}.

## Fix list, in priority order

{fix_list}

## The two doors

{doors}

## Every check

| id | check | outcome | priority | evidence | fix |
|---|---|---|---|---|---|
{check_rows}

## What this audit cannot see

- Reading saved files over HTTP is not indexing, crawling history, citation or recommendation; a pass says a page can be read, never that an assistant will name the store.
- A barrier signal (V15) needs a plain-browser test; a script name proves nothing about what a visitor sees.
- The UCP shopping tools need an agent token, so their behavior is unverified; only the profile was read.
- Catalog eligibility (V16) is a word match against a dated list; the admin's Shopify Catalog screen is the ruling.
- The answer check (V18) is the measurement that counts; one answer is an anecdote, a monthly sheet is a trend.

## Coverage

{coverage}
