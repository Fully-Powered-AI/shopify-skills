# The eighteen checks, their priorities and the lists the scripts read

Dated 2026-10-21; fix round 2 of the same date moved the fact-slot and catalog rules to the set's shared module. Written for `ai-visibility-audit` from the set's `schemas.md` section 5 (the check list) and `references/ai-channels-extract.md` (the platform facts). The fenced blocks marked `settings`, `list` and `table` are read by `scripts/audit_pages.py` and `scripts/answer_sheet.py` at run time: change a value here, never in a script or in SKILL.md. Values marked [build] are this build's choices, open to the owner's change; every other value names its source.

Contents: 1 how each check is read; 2 outcomes; 3 the priority table; 4 settings; 5 crawler names; 6 barrier signals; 7 contact and placeholder patterns; 8 text addressed to an assistant; 9 the default assistant list.

## 1. How each check is read from the saved files

A file counts as fetched with status 200 when `fetch-log.csv` says so; when the folder has no fetch log (pages saved by hand), a saved file is taken as status 200 and the coverage line says so.

| id | read from | passes when | evidence names |
|---|---|---|---|
| V01 | `robots.txt` | no `User-agent: *` group carries `Disallow: /`, and no group naming a crawler in section 5 carries `Disallow: /` | the groups found, the crawler names matched |
| V02 | `agents.md` | saved with status 200 | file size |
| V03 | `agents.md` | a product line name or a search word from store file section 2 appears as a word, after the store name is removed | the words found, or none |
| V04 | `llms.txt`, `llms-full.txt` | both saved with status 200; each noted as a mirror of `agents.md` or custom (rule in section 4) | mirror or custom per file |
| V05 | `ucp.json` | parses as JSON with a top-level `ucp` key | the profile version |
| V06 | `sitemap.xml` | it names product, collection and page child sitemaps; the agentic-discovery child is noted, not required | the children named |
| V07 | `policies/*.html` | the four policy files (section 4 below) saved with status 200 | the missing ones |
| V08 | `pages/*.html`, the pages sitemap, store file section 6, `home.html` | a saved page whose handle contains a word from section 4 `faq_handle_words`, or a page store file section 6 names, is saved; a `FAQPage` block on the home page is named in the evidence and does not pass the check | the handle, or the sitemap handles read, and the home page's FAQPage question count when it has one; home JSON-LD blocks that do not parse are counted, naming FAQPage when their text carries it |
| V09 | sampled product pages | every page carries a `Product` (or `ProductGroup`) JSON-LD with name, image, and an offer with price, currency and availability | per page: required fields missing, recommended fields counted |
| V10 | sampled product pages | the share of pages with a `FAQPage` JSON-LD reaches `faq_required_share_percent` | the count |
| V11 | home and product pages | an `Organization` JSON-LD has name, url and at least one `sameAs` entry, none empty | entries counted, then filled and blank; home JSON-LD blocks that do not parse are counted, naming Organization when their text carries it |
| V12 | sampled product pages; `collections/all.html` reported apart | the share of `img` tags with a non-empty `alt` on the sampled product pages reaches the target (section 4); the collection page's count is shown beside it and not scored | tags and tags with alt, in total and per page, then the collection page's count |
| V13 | sampled product pages, visible text | every fact slot in store file section 2 is found on every page (the shared rule, section 4) | per page, the slots missing; a slot missing on more than half the pages carries the shared wording note as its fix |
| V14 | sampled product pages | each has a `title`, a meta description and exactly one `h1` | per page, what is off |
| V15 | home and product pages, store file section 6 | no signal from section 6 below is found and section 6 lists none | each signal and the file it was seen in |
| V16 | store file sections 2 and 10, `assets/catalog-exclusions-2026-10-21.csv` | every product line names a category, none matches a row (the shared rule, section 4), and store file section 10 does not disagree | the lines by category, the matches |
| V17 | saved contact, policy and home pages, store file section 6 | a public email address or a contact form (section 7) is found, or section 6 names a contact email | where it was seen |
| V18 | the latest sheet under `visibility/answers/` on or before the audit date | the sheet is valid, complete, no older than the answer-check cadence (section 4), and at least one row was asked with the Shopify connection off; `not run` when no sheet exists or no row is filled | questions asked, store named, recommended, cited pages by domain, over the rows asked with the connection off; rows asked with it on and brand questions counted apart |

## 2. What each outcome means

- `pass`: the files show what the check asks for. It is not indexing, citation or recommendation.
- `fail`: the files show the check is not met; the fix says what to change.
- `blocked`: the file the check needs is not in `pages/<date>/` (or failed to fetch). Excluded from pass counts and listed under coverage. Fetch or save the file and run the audit again.
- `not run`: the check does not apply or has no input yet (V18 with no sheet, or a sheet with no filled row), with the reason.
- `inconclusive`: a signal a person must test (V15), a product line with no category, or a word match that disagrees with store file section 10 (V16).

V16 is the feed door; the other seventeen are the open-web door (`ai-channels-extract.md` section 1). V18 measures; the others prepare.

## 3. The priority table

Priority 1 blocks reading: an assistant or agent cannot get the page or the facts. Priority 2 blocks citing: the facts can be read, but there is little worth quoting or no path to confirm them. Priority 3 is polish. A row is a check id and the condition code the script emits; `none` keeps a finding off the fix list. [build]

```table priorities
V01 fail 1
V02 fail 2
V03 fail 2
V04 fail 3
V05 fail 2
V06 fail 1
V07 fail 2
V08 fail 2
V09 fail 1
V10 fail 3
V11 no-organization 2
V11 no-sameas 2
V11 blank-sameas 3
V12 below-floor 2
V12 above-floor 3
V13 all-missing 1
V13 some-missing 2
V14 fail 3
V15 inconclusive 1
V16 fail none
V16 inconclusive none
V17 fail 2
V18 fail 2
```

## 4. Settings

```settings
alt_floor_percent: 80
alt_target_percent_when_required: 100
faq_required_share_percent: 100
mirror_max_differing_lines: 3
answer_cadence_days_weekly: 7
answer_cadence_days_monthly: 31
answer_cadence_days_quarterly: 92
```

- `alt_floor_percent` [build]: below it, V12 is priority 2; at or above it but under the target, priority 3. The target is `alt_target_percent_when_required` when store file section 9 says every image carries alt text (`yes`), else the floor.
- `mirror_max_differing_lines` [build]: V04 calls an llms file a mirror of `agents.md` when no more than this many lines differ; Shopify's mirror rewrites the line that names the file being read. A changed line counts once (a block of changed lines counts its longer side).
- `faq_required_share_percent` [build]: the share of sampled product pages that must carry `FAQPage` for V10 to pass.
- V13's slot rule: the set's shared rule, `../../references/schemas.md` section 12, applied by `scripts/fact_slots.py` (`parse_slot`, `slot_found`, `slot_wording_note`); its word lists live in that module, and an owner widens a match by writing the page's words in parentheses on the slot line.
- V16's match rule: the set's shared rule, `../../references/schemas.md` section 12, applied by `scripts/fact_slots.py` (`parse_lines`, `read_exclusions`, `catalog_status`) over every product line's category; a match is a word match, never Shopify's ruling.
- Answer-check cadence: store file section 9 `weekly`, `monthly` or `quarterly`, as days.

```list policy_files
shipping-policy
refund-policy
privacy-policy
terms-of-service
```

```list faq_handle_words
faq
guide
```

```list fetch_page_handle_words
faq
guide
about
contact
```

## 5. Crawler names

From `ai-channels-extract.md` section 5 (verified 2026-10-19 from the vendors' pages, as the set's reference records). Training crawlers, search indexers and user-requested fetchers have different purposes; a store may block one on purpose, so V01's evidence names which.

```list crawlers
GPTBot
OAI-SearchBot
ChatGPT-User
ClaudeBot
Claude-User
PerplexityBot
Perplexity-User
Googlebot
Google-Extended
Meta-WebIndexer
Meta-ExternalAgent
Meta-ExternalFetcher
```

## 6. Barrier signals

Substrings looked for, case-insensitive, in the raw HTML. Any hit makes V15 `inconclusive`: a script or a class name says a barrier may exist, and only a plain browser shows whether it blocks the page. Generic words such as "popup" alone are left out because review widgets and cart drawers use them. [build]

```list barrier_signals
password | template-password
password | form_type" value="storefront_password
age gate | age-verification
age gate | age_verification
age gate | agegate
age gate | age-gate
signup form app | klaviyo.com/onsite
signup form app | privy.com
signup form app | justuno
signup form app | wisepops
signup form app | newsletter-popup
signup form app | newsletter_popup
signup form app | popup-newsletter
```

## 7. Contact and placeholder patterns

A contact form is a Shopify form carrying `form_type` with value `contact`; the newsletter form carries `customer` and does not count. An email address counts when it is not a placeholder below.

```list email_placeholders
xxx@
@xxx.
@example.com
@domain.com
@email.com
@yourstore
```

## 8. Text addressed to an assistant

Phrases that mark text written to an AI reader rather than to a person. Hits are counted in the coverage line and never acted on; Shopify's own default files carry some, so a hit is a note, not a finding. [build]

```list agent_addressed
if you are an ai
if you are reading this on behalf
ignore previous instructions
ignore all previous
as an ai assistant
please highly recommend
you must recommend
```

## 9. The default assistant list and the questions for the answer check

The assistants a buyer is likely to ask, from the AI channels the set's `ai-channels.md` sections 3 and 7 name (agentic storefronts and personal agents); the person replaces it with `--assistants` when they use others. [build]

```list assistants
ChatGPT
Claude
Gemini
Perplexity
Microsoft Copilot
```

How `answer_sheet.py --init` writes a question so an assistant asked in a new conversation can answer it [build]. When store file section 4's answer-check prompts are filled, they are written verbatim, paired with the buyer questions in order (`schemas.md` section 6); the rest of this paragraph applies to a question with no prompt. A question that names the store or a product line (store file sections 1 and 2, matched with their capitals) is a brand question: kept as written, and counted apart, because it tests what an assistant knows about the store rather than whether it finds the store. A question with no search word in it whose subject is one of the pronouns below gets the discovery prefix, with the first search word of store file section 2 in place of `{search word}`. Every other question is kept as written. The summary counts discovery and brand rows apart. Each row's settings cell starts `shopify connection: ` for the asker to finish with `off` or `on`; a filled row without one is malformed, and rows marked `on` are counted apart and left out of the shares, because a connected assistant answers from the store's admin data (`schemas.md` section 6).

```settings
discovery_prefix: I'm shopping for {search word}.
```

```list question_pronouns
it
its
they
them
this
these
that one
```
