# Shared shapes: the workspace, the store file and every file the skills read or write

Written 2026-10-21 as the contract between the skills in this set. Every skill reads and writes the same files in the same shapes, so what one skill saves is what the next one reads. Section numbers are fixed; skills and briefs cite them.

## 1. The workspace

The store keeps one folder, the workspace. Every skill takes its path as the first input (default: the current directory) and never writes outside it. Nothing in it is sent anywhere by a skill.

```
<workspace>/
  store/store.md                        the store file, read first by every skill (template: skills/store-setup/assets/store-template.md)
  store/observed-YYYY-MM-DD.md          store-setup's proposal of [observed] values from the saved public pages (section 9)
  store/connection-YYYY-MM-DD.json      what the model read through the host's Shopify connection, saved as a file before any script runs
                                        (shape: skills/store-setup/assets/connection-read-template.json; read-only; never written by a script)
  pages/YYYY-MM-DD/                     the store's public pages as saved on a date (section 2)
  exports/products-YYYY-MM-DD.csv       the admin's products export, dropped in by the person (columns: references/shopify-exports.md)
  exports/products-connection-YYYY-MM-DD.csv  the products the model read through the connection, written in the export's own column
                                        names, one row per variant or image; read by product_gaps.py --export, refused by product_import.py
  exports/<other>-YYYY-MM-DD.csv        later exports (orders, customers, inventory), same naming
  visibility/audit-YYYY-MM-DD.md        ai-visibility-audit's findings, readable (section 5)
  visibility/audit-YYYY-MM-DD.json      the same findings, machine-readable (section 5)
  visibility/answers/YYYY-MM-DD.md      a filled answer-check sheet (section 6)
  agent-guide/agents.md.liquid          the drafted agent guide, for the person to paste into the theme (section 7)
  agent-guide/llms-full.txt.liquid      optional, the longer companion (section 7)
  agent-guide/product-index-YYYY-MM-DD.md  the drafted product index the companion carries, for the person's review (section 7)
  agent-guide/connection-YYYY-MM-DD.json  the product list read through the connection by agent-guide, in the store/connection shape with tags
  agent-guide/check-YYYY-MM-DD.md       the guide check's report (section 7)
  agent-guide/superseded/               earlier drafts and reports set aside under a dated name (check-YYYY-MM-DD-<n>.md), never deleted
  products/gaps-YYYY-MM-DD.csv          product-facts' per-product gap table (section 8)
  products/gaps-YYYY-MM-DD.md           the readable summary of the gap table (section 8)
  products/facts-YYYY-MM-DD.md          the review file: proposed facts, alt text, FAQ entries and body additions (section 8)
  products/product-import-YYYY-MM-DD.csv  the import file built from approved entries (section 8)
```

Dates in file names and in cells are ISO, `YYYY-MM-DD`. Times, when needed, are UTC `YYYY-MM-DDTHH:MMZ`.

## 2. Saved public pages, `pages/YYYY-MM-DD/`

One folder per day the pages were read, written by `ai-visibility-audit`'s `fetch_pages.py` or by the person saving pages by hand. Files are saved as fetched, bytes unchanged.

```
pages/YYYY-MM-DD/
  fetch-log.csv              url, path, status, bytes, fetched_at, note      (one row per request, including failures)
  robots.txt                 /robots.txt
  agents.md                  /agents.md
  llms.txt                   /llms.txt
  llms-full.txt              /llms-full.txt
  ucp.json                   /.well-known/ucp
  sitemap.xml                /sitemap.xml
  sitemap_<name>.xml         each child sitemap the index names (query string dropped from the file name)
  home.html                  /
  products.json              /products.json?limit=250 (first page; a second page is products-2.json)
  products/<handle>.html     /products/<handle>
  products/<handle>.json     /products/<handle>.json
  collections/<handle>.html  /collections/<handle> (always collections/all.html)
  policies/<name>.html       /policies/shipping-policy, refund-policy, privacy-policy, terms-of-service
  pages/<handle>.html        /pages/<handle> for pages the sitemap lists whose handle contains faq, guide, about or contact
```

A missing file means the path was not fetched or not saved; a `fetch-log.csv` row with a non-200 status says what happened. A folder saved by hand may lack `fetch-log.csv`: it is valid, its files count as fetched with status 200, and a script that reads it says in its coverage line that the log was absent. The fetcher takes the product handles to sample from the store file (section 9, products sampled per audit) in the order the products sitemap lists them, unless the person names handles.

## 3. The store file, `store/store.md`

Filled from the template at `skills/store-setup/assets/store-template.md`; the template's first section states the writing rules and they are repeated here because every script relies on them:

- Headings are fixed and numbered 1 to 11; scripts find a section by its number.
- A field is a bullet whose template text ends with a colon; the value follows the colon on the same line; the source mark (`[owner]`, `[observed]`, `[default]`, `[open]`) is the last thing on the line.
- An indented line under a field is template guidance when it carries no mark and the person's detail when it carries one. Lists ("one per indented line") are read from the marked indented lines.
- A blank value is "not yet decided"; a script that needs it exits 1 naming the section. `[open]` is a decided "undecided" and is reported, not fatal, unless the field is required for the run.
- Scripts take the headings and field labels from the template file at run time, so a template change reaches every check without editing a script (`store-setup`'s `store_file.py` is the shared reader; other skills copy its parsing or call it by path). A script that carries embedded labels as a fallback carries the current template version's and says in its coverage line when it fell back.
- A product-line item (section 2) is written `<name>: <what it is>, <who it is for>; category <the full Shopify product category path>`, or ends in `same category` to take the line above's. `store_file.py` reports an item with no name before a colon as a problem (exit 1) and an item with no category part as an open item (exit 2). Every skill parses these items and matches products to lines through the shared module `fact_slots.py` (section 12).
- A fact-slot item (section 2) is written `<slot name> (<the words the pages use, comma separated>), from <where the fact comes from>`; the parentheses are optional. Every skill matches a slot against a page or a description through `fact_slots.py` (section 12), never through a rule of its own.
- Section 4's answer-check prompts are optional; when filled, `answer_sheet.py --init` writes them as the questions; when blank, it writes the buyer questions with a short opening (section 6).

Sections: 1 The store; 2 What it sells; 3 Claims and words; 4 Buyers and their questions; 5 Apps and systems; 6 Pages, policies and contact; 7 People and roles; 8 Access; 9 Thresholds and cadences; 10 AI channels; 11 Decisions log.

## 4. CSV rules every script follows

- UTF-8, comma separated, header row exactly as listed, in this order. A script refuses a file whose header differs and says which column is missing or extra. The exception is a Shopify export, whose header is Shopify's; a script reads it by column name and names what it could not find.
- Empty cell means unknown. Never `N/A`, `null` or a dash.
- Lists inside a cell are separated by `;` with no spaces.
- Money is a plain decimal in the store currency with no symbol. Percentages are plain decimals of percent.
- Every write is preceded by a read of the whole file and followed by the script printing how many rows it read, added and changed.

## 5. The audit, `visibility/audit-YYYY-MM-DD.json` and `.md`

The JSON is the record; the Markdown is the same findings for a person, with the fix list first. The check list is fixed so that audits on different dates compare:

| id | check | what passes |
|---|---|---|
| V01 | robots file | `/robots.txt` saved; no blanket disallow; no disallow aimed at AI crawlers (names in the audit's reference) |
| V02 | agent guide present | `/agents.md` saved with status 200 |
| V03 | agent guide is the store's own | the guide names the store's product lines or search words from store file section 2; else it is Shopify's default (reported as `fail` with the fix "write the guide") |
| V04 | llms files | `/llms.txt` and `/llms-full.txt` saved with status 200 (mirror or custom, noted; a file is a mirror of `agents.md` when no more than `mirror_max_differing_lines` lines differ, a changed line counted once, since Shopify rewrites the line that names the file) |
| V05 | UCP profile | `/.well-known/ucp` saved and parses as JSON with a `ucp` key |
| V06 | sitemaps | `/sitemap.xml` saved and names product, collection and page sitemaps; agentic discovery sitemap present (noted) |
| V07 | policies | shipping, refund, privacy and terms pages saved with status 200 |
| V08 | FAQ or guide page | a saved page whose handle contains `faq` or `guide`, or a page the store file section 6 names, exists |
| V09 | product structured data | every sampled product page carries a `Product` JSON-LD with name, image, and an offer with price, currency and availability; the recommended fields (brand, sku, gtin or mpn, description, aggregateRating, shipping and return details) are counted and listed |
| V10 | product FAQ structured data | sampled product pages carry a `FAQPage` JSON-LD (count) |
| V11 | organization structured data | an `Organization` JSON-LD with name, url and `sameAs` entries, none of them empty |
| V12 | image alt text | share of `img` tags with non-empty `alt` on the sampled product pages and the main collection page, against the threshold in the audit's reference |
| V13 | facts in the page text | for each fact slot in store file section 2, whether the slot is found in each sampled product page's visible text (scripts and styles removed) by the shared rule in section 12; a slot missing on more than half the sampled pages carries the fixed note "check the slot's wording first" instead of a fix that adds the fact |
| V14 | title, description, heading | each sampled product page has a title, a meta description and exactly one H1 |
| V15 | storefront barriers | signals of a password page, an age gate or a popup script (listed in the audit's reference); any signal is `inconclusive` with the fix "test in a plain browser" |
| V16 | catalog eligibility | every product line's category in store file section 2 against the dated exclusion list in the audit's `assets/`, by the match rule in section 12: `eligible` is `pass`; `excluded` is `fail` with priority `none` (the fix is not on the open web; the admin's own screen decides); `unknown` (no category stated) is `inconclusive`; a value in store file section 10 that disagrees with the computed one is `inconclusive` |
| V17 | public contact path | a contact email or contact form on the saved contact, policy or home pages, or the one store file section 6 names |
| V18 | answer check | the latest sheet under `visibility/answers/`: `pass` when it is valid, complete (a row per question per assistant) and within the answer-check cadence of store file section 9; `fail` when it is partly filled, malformed or older than the cadence; `not run` when no sheet exists or no row is filled yet (a measurement not taken is not a failed one). The evidence gives the share of rows where the store was named and where it was recommended, the cited domains, brand questions counted apart, and rows whose settings record the Shopify connection on counted apart and excluded from the shares |

Outcomes: `pass`, `fail`, `blocked` (the needed file is not in `pages/<date>/`), `not run` (not applicable, with the reason), `inconclusive` (a signal that needs a person). A check that is `blocked` or `not run` is excluded from pass counts and listed under coverage.

JSON shape:

```
{"store": "<domain>", "date": "YYYY-MM-DD", "pages_dir": "pages/YYYY-MM-DD", "sampled_products": ["<handle>", ...],
 "checks": [{"id": "V01", "name": "...", "outcome": "pass|fail|blocked|not run|inconclusive", "evidence": "...", "fix": "...", "priority": "1|2|3|none"}],
 "coverage": {"inputs_used": [...], "inputs_missing": [...], "not_judged": [...]}}
```

`priority` comes from the table in the audit's reference (what blocks reading, what blocks citing, what is polish); never from prose.

## 6. The answer-check sheet, `visibility/answers/YYYY-MM-DD.md`

A person asks each assistant the buyer questions from store file section 4 and records what happened. The sheet is Markdown with a fixed table; `ai-visibility-audit`'s `answer_sheet.py` validates and summarizes it.

```
# Answer check, YYYY-MM-DD
Store: <domain>. Asked by: <role>. Assistants: <list>.

| q | question | assistant | asked_on | settings | store_named | recommended | cited_urls | notes |
```

`q` is `Q1`, `Q2`, ... in the order of section 4. The `question` cell carries what was typed: section 4's answer-check prompt when that field is filled, else the buyer question with a short opening that names the kind of product (`answer_sheet.py --init` writes it); a question that names the store or a product line is a brand question and is counted apart from the discovery questions. `store_named` is `yes`, `no`; `recommended` is `yes`, `no`, `partial` (named among several); `cited_urls` is a `;` list or empty; `settings` records `shopify connection: off` or `on`, then search or browsing on or off and the plan where known. The asker uses an assistant account with no Shopify connection to this store, or turns the connection off for the conversation, because a connected assistant answers from the store's own admin data and measures nothing; rows marked `on` are counted apart and left out of the shares. A row per question per assistant. A question not asked of an assistant has no row and is reported as missing.

## 7. The agent guide, `agent-guide/`

`agents.md.liquid` is the file the person pastes into the theme as `templates/agents.md.liquid`; Shopify then serves it at `/agents.md` and, unless a path-specific template exists, at `/llms.txt` and `/llms-full.txt` (`references/ai-channels.md` section 4). The template sees only the `request` and `agents` objects, so every store fact is written text and every endpoint is a Liquid output from `agents` (`{{ agents.store_url }}`, `{{ agents.ucp_discovery_url }}`, `{{ agents.mcp_endpoint_url }}`, `{{ agents.sitemap_url }}`).

Required sections, in this order, headings as written: `# <store name>: a guide for agents`, `## What this store is`, `## Who it is for`, `## The product lines and how to choose`, `## Facts an agent may state`, `## Policies`, `## Shopping here as an agent` (the endpoints through `agents`, and the Shopify-managed instructions a custom guide keeps), `## What not to assume`. No email address or phone number (Shopify's guidance for this file). Every statement about the products comes from store file sections 2 and 3; a line that is not there is not written.

`check-YYYY-MM-DD.md` is the report of `guide_check.py`: size, sections, links, Liquid outputs, redline words, contact details, flagged claim words, each with pass or fail, the store's never-made statements and section 3 redlines listed for a person, then the coverage line. Its date is the `--pages` date when one is given. A second check on the same date moves the earlier report to `superseded/check-YYYY-MM-DD-<n>.md` and says so. `product-index-YYYY-MM-DD.md` is the index `product_index.py` drafts for `llms-full.txt.liquid`, read first from `store/connection-YYYY-MM-DD.json` or `agent-guide/connection-YYYY-MM-DD.json` (the host's connection, read-only, draft and archived products left out), then from the saved products JSON, then from the export; it matches products to lines by the rule in section 12 and reports each product as one, suggested, several or none.

## 8. Product facts, `products/`

`gaps-YYYY-MM-DD.csv`, one row per product, columns in this order:

`handle, title, status, product_category, variants, variants_with_sku, variants_with_barcode, images, images_with_alt, description_chars, fact_slots_found, fact_slots_missing, jsonld_product, jsonld_rating, jsonld_faq, meta_description, source, notes`

`fact_slots_found` and `fact_slots_missing` are `;` lists of slot names from store file section 2, matched in the product description (the export's, else the product JSON's) by the shared rule in section 12; slots found only elsewhere on the saved page are named in `notes`, so this table and the audit's V13 (whole visible page) are not the same measure. Both cells are empty for a product the table notes as not in a product line of section 2 (by the rule in section 12): empty means not checked, never "nothing missing", and such products take no part in the slot totals. A slot missing from more than half the in-line descriptions carries the fixed note "check the slot's wording first" in the summary. `jsonld_*` and `meta_description` are `yes`, `no` or empty (no saved page for that handle). `source` is `json` (the public products JSON), `export` (the products export) or `page`; when more than one was read, the order of precedence for a cell is export, then json, then page, and `notes` says which fields came from where.

`facts-YYYY-MM-DD.md`, the review file, one block per product with fixed headings:

```
# Product facts review, YYYY-MM-DD
Store: <domain>. Sources: <files read>.

## <handle>
### Facts
- [proposed] <slot>: <value> (source: label | spec | page | owner | cleared, named anywhere in the source text, with a date where one applies)
### Alt text
- [proposed] <image src URL>: <alt text>
### FAQ
- [proposed] Q: <question> A: <answer> (source: ...)
### Body additions
- [proposed] <one paragraph of plain text to append to the description>
```

The person changes `[proposed]` to `[approved]`, edits the text, or deletes the line. `product_import.py` reads `[approved]` lines only and refuses a file with no approved line.

`product-import-YYYY-MM-DD.csv` is built only when a products export is present in `exports/`: the script starts from the export's own rows for the handles with approved entries and changes only the cells the approved entries name (alt text on the image's row, the description with the additions appended, FAQ as a description addition when no standard FAQ column exists), keeping every other cell of the columns the file carries as exported, so that Shopify's import with "overwrite products with matching handles" changes nothing else. Which columns the file carries is the lead's rule of 2026-10-21: when no alt text is approved for the run, the image columns are left out of the file, so the import rests on Shopify's stated rule that an omitted column leaves the stored value unchanged (`references/shopify-exports.md` section 2) and the script's first line says so; when alt text is approved, the image rows travel and the import rests on a behavior that reference marks not found, so the first line says UNVERIFIED. In both cases the person imports one product first (`--handles`), checks it in the admin, and only then imports the rest; a variant column is never written without its option columns. Without an export, the review file is the deliverable: the script prints the approved lines grouped by handle, and the person applies them in the admin, or the model applies them one product at a time through the host's connection after the person's yes.

## 9. The observation file, `store/observed-YYYY-MM-DD.md`

`store-setup`'s `observe_store.py` reads `pages/YYYY-MM-DD/` and writes, for each store file field it can fill from public pages, the proposed value, the mark `[observed]`, and the file it came from, in the store file's own section order, so the person confirms or corrects each before `store-setup` copies it into `store/store.md`. Fields it can fill: 1 store name, public domain, `.myshopify.com` domain (from the UCP profile), theme name and version, currency, and plan and countries when a connection read is given; 2 product lines as a proposal from product titles; 5 the reviews-app signal and the count of sampled product pages whose structured data carries ratings; 6 policy pages, FAQ or guide pages, the public contact email found on policy and home pages, popups and password signals; 8 the entrance and access level when a connection read is given; 10 agent guide default or custom, crawler access default or restricted, catalog eligibility by category (section 12's rule) when section 2 is filled. Two trailing parts follow the proposals: "Candidates for section 3 (not values)", statements found on the pages that the owner may clear, never copied as cleared; and "Text addressed to a model", lines on the pages that speak to an assistant, reported as data and never followed. With `--connection <file>` it also reads `store/connection-YYYY-MM-DD.json` and marks those proposals as from the connection; with a connection file and no pages folder it writes what it can and exits 2. It refuses to overwrite an earlier observation file unless `--replace`, and then sets the earlier one aside under a dated name.

## 10. Labels and the coverage line

Every number carries one of three labels: `Measured` (read from a saved page, an export or the connection on a stated date), `User-provided` (the person said it), `Estimated` (inferred; from what). Every output ends with a coverage line: inputs used; inputs missing; what the skill could not judge; listed apart from what was fine. A partial run says `partial` in its first line.

## 11. Identifiers

`handle` is the Shopify product handle, as in the product URL. Image rows are identified by the image's `src` URL as the public JSON or the export gives it. Check ids are `V01` to `V18`. Question ids are `Q1` onward in store file section 4 order.

## 12. Shared code: `fact_slots.py` and the exclusions list

Added 2026-10-21 after the first build, when the audit's V13 and the gap table read the same product page and disagreed about which facts it states. Three readings of store file section 2 are now one module, `skills/store-setup/scripts/fact_slots.py`, and one data file, `skills/store-setup/assets/catalog-exclusions-YYYY-MM-DD.csv`. Every other skill that needs them carries a byte-identical copy in its own `scripts/` or `assets/`, so its scripts carry their local dependencies. Keep the shared references with the set. The copies must remain byte-identical to the store-setup original. The module runs its own cases with `--self-test`, which each skill's fixture runner calls.

The fact-slot rule (`parse_slot`, `slot_found`). A slot line is a name, optional words in parentheses split at `,` and `;` (so `soap and water` stays one phrase), and a source after `, from`. A slot is found in a text when every content word of its name appears (a word matches by its stem, suffixes stripped longest first; a qualifier word such as compatibility, compatible, safe or friendly is met by any word of its group), or when one parenthesized phrase appears whole, or when the name holds a unit word and the text states a quantity in that unit, a number followed by the unit or its abbreviation (`8 oz`, `8oz`, `8 fl oz`). The stop words, suffixes, qualifier groups and units are build choices of 2026-10-21 listed in the module; an owner changes a match by writing the page's words in the parentheses, never by editing the module. A slot missing from more than half the pages or descriptions read carries the fixed wording note (`slot_wording_note`), because the likelier cause is the slot's words, not the page.

The product-line rule (`parse_lines`, `line_of`). An item is `<name>: <what it is>, <who it is for>; category <path>` or ends in `same category`. An item with no colon parses to an empty name and a `problem`, so no skill matches a sentence as a line name; `store-setup` reports it as a problem (exit 1) and every other skill as a warning that names `store-setup`. A product belongs to a line by its handle first, then its title, then its product type, a line name matched whole between word boundaries (so `Oil` is not found in `oil-based`) and the longer of two nested names winning; two strong signals that name different lines give `several`; a product type alone, a tag, or the category's last segment gives `suggested` for the owner to confirm; nothing gives `none`, and a product with `none` is not in a line and is left out of per-line counts and slot totals.

The catalog rule (`read_exclusions`, `catalog_status`). The exclusions file has the columns `category, examples, terms, source, date`: Shopify's category names and examples as its requirements page lists them on the date, and `terms`, the lead's extra match words. A product category path is split at `>` and each segment compared on its own: a segment matches a row when it equals the row's category, a term or an example (singular or plural), when a term or example of two or more words appears whole inside it, or when the segment, of two or more words, appears whole inside the row's category or an example. A one-word term matches only a segment equal to it, so `Food, Beverages and Tobacco` does not match `tobacco` while `Tobacco Products` does. One matching segment excludes the path. The result is a word match, never Shopify's ruling: the admin's own Shopify Catalog screen decides, and every output says so. `read_exclusions` raises `ExclusionsError` (a `ValueError`) for a header other than the five columns and lets a missing file raise `FileNotFoundError`; a script catches both, prints one plain sentence naming the file, and exits 1.
