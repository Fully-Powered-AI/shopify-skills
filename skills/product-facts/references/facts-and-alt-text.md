# Facts, alt text, FAQ entries, body additions and structured-data gaps

Written 2026-10-21 for `product-facts`. Frameworks, shapes and worked examples only; the order of work is in `SKILL.md`. Platform facts come from the set's `references/shopify-exports.md`, `references/ai-channels.md` and `references/shopify-access.md` as read that day, and from this folder's `shopify-exports-extract.md`. The examples use three invented stores. `review_file.py` reads the table in section 5, so its columns stay as written.

Contents: 1 the fact-slot method; 2 alt text; 3 FAQ entries; 4 body additions; 5 structured-data gaps and where each is fixed; 6 the ways to apply approved entries.

## 1. The fact-slot method

A fact slot is a fact every product page should state, named by the owner in store file section 2 with where it comes from. The skill has no list of its own; a candle store and a bicycle store have nothing in common here.

| term | meaning |
|---|---|
| slot | the line in store file section 2: its name, optional page wording in parentheses (the words the pages use, comma separated), and `from <source>` |
| source | the kinds the set's `references/schemas.md` section 8 names: `label` (the product's own label or packaging, as the person supplies it), `spec` (a specification sheet the person supplies), `page` (the product's own saved page text), `owner` (the person said it in the conversation) and `cleared` (a cleared statement in store file section 3); the slot's own source as section 2 words it is accepted too |
| found | by the set's one rule, `references/schemas.md` section 12, in `scripts/fact_slots.py`: every content word of the slot name appears (by stem, so "compatibility" meets "compatible", a qualifier such as "safe" meeting "compatibility"), or one phrase in its parentheses appears whole, or, when the name holds a unit word, the text states a quantity in that unit ("9 oz" for "size in ounces") |
| missing | not found in the description; it may still be on the page outside the description, which the gap table's notes name |
| open | a slot whose value has no source yet; it stays a question for the owner |

Word matching is a screen, not a reading. A slot the page states in other words is missed; the owner writes the page's words in the parentheses in section 2 through `store-setup`, for example `dishwasher compatibility (dishwasher safe, top rack)`, never by editing the module. A slot missing from more than half the descriptions carries the module's fixed note, "check the slot's wording first". A slot found by word can still be stated wrongly; the model reads the description before proposing anything.

Slots apply to the products of the store's product lines (store file section 2, each item written `<name>: <what it is>, <who it is for>; category <path>` or ending `same category`), by the line rule of `references/schemas.md` section 12: the line's name matched whole in the handle, then the title, then the product type; a product type alone, a tag or the category's last segment only suggests a line, and two strong signals naming different lines give several. A suggested or several-line product is checked and its notes say "confirm"; merchandise, gift cards and products of a line the store file does not list are noted "not in a product line" and left out of the slot counts.

Source precedence for a proposed value: the label or spec sheet the person supplied, then the page's own text, then the person. A value seen only on a third party's page is not a source.

## 2. Alt text

Alt text tells a person who cannot see the image what it shows. Shape, in this order, as one line: what the object is, which product (the product's name as the store writes it), which size, color or variant when the image shows one, and the view or setting when it matters (the back label, in use, the contents laid out). Shopify allows 512 characters and recommends 125 or fewer (`shopify-exports-extract.md` section 1).

| store (invented) | image | weak | good |
|---|---|---|---|
| a ceramics studio | a mug from the side | mug coffee mug handmade ceramic mug gift | Tidewater mug in sea-glass glaze, 12-ounce size, side view showing the thumb rest |
| a running-shoe shop | the sole | image of shoe | Ridgeback trail shoe in slate gray, sole showing the 5-millimeter lugs |
| a plant-care brand | the bottle's back | Grow Plus | Back label of the 8-ounce Grow Plus bottle listing the feeding schedule |

Anti-patterns: a list of search words; "image of" or "picture of"; the file name; the title alone repeated on every image; a claim the store has not cleared (store file section 3); promotional words; describing what is not in the image. An image that only decorates (a background texture) is reported to the person rather than given invented alt text.

## 3. FAQ entries

An FAQ entry answers one buyer question from store file section 4 that this product's facts can answer. The answer is one to three sentences built only from the store's cleared statements (section 3) and the product's sourced facts (section 2), and it names that source. It respects the redlines and the statements the store never makes (section 3). A question the store file cannot answer for this product is listed as `[open]` with what is needed, never answered from general knowledge.

Example (invented plant-care store): Q: Can I use it on succulents? A: Yes, at half strength once a month in spring and summer, as the back label's feeding schedule says. (source: label)

Where an approved FAQ entry lands: the products CSV has no standard FAQ column (`shopify-exports-extract.md` section 1), so the import appends it to the description as a question in bold and its answer. FAQPage structured data is the theme's or an app's work (section 5).

## 4. Body additions

A body addition is a plain paragraph of facts appended after the owner's description. It never rewrites, reorders or removes the owner's copy, and it carries no styling. Each approved addition becomes one HTML paragraph, its text escaped, added at the end of the exported description; an addition already present word for word is skipped. Shopify's pages do not say whether the current `Description` column accepts HTML; the older column is named `Body (HTML)` (`shopify-exports-extract.md` section 4).

Example (invented ceramics studio): "The Tidewater mug holds 12 ounces, is dishwasher safe on the top rack, and is not for use in the microwave, as its care card states."

## 5. Structured-data and catalog gaps, where each is fixed

`review_file.py` prints the line for each gap a product has. "Import" says whether this skill's import file changes it; the skill reports the rest and fixes none of it.

| gap | what the gap table shows | where it is fixed | who acts | import |
|---|---|---|---|---|
| sku | variants_with_sku below variants | each variant's SKU in the admin, or the export's SKU column | operator, after the approver in store file section 7 | no |
| barcode | variants_with_barcode below variants | each variant's barcode in the admin, or the export's barcode column (GTIN, UPC, EAN or ISBN) | operator, after the approver | no |
| category | product_category empty | the product's category in the admin (Shopify's standard taxonomy), or the export's category column | operator, after the approver | no |
| rating | jsonld_rating no | a reviews app that adds ratings to the product structured data (store file section 5) | owner chooses the app | no |
| product-jsonld | jsonld_product no | the theme's product template, which on Shopify's own themes outputs the product's structured data | the person who edits the theme | no |
| faq-markup | jsonld_faq no | the theme or an app that marks up a visible FAQ | the person who edits the theme | no |
| meta-description | meta_description no | the product's search engine listing in the admin, or the export's SEO description column | operator, after the approver | no |
| shipping-returns | not measured by the gap table; checked by ai-visibility-audit (V09) | the theme or an app for page markup, or the store's shipping and return settings | owner | no |

Google's merchant listing page names name, image and offers as required on Product, and brand, sku, gtin or mpn, description, category and aggregateRating among the recommended fields; it recommends shipping and return policies at organization level (the set's `references/shopify-exports.md` section 4). Shopify Catalog shares title, description, options, images, price and availability with AI channels (`references/ai-channels.md` section 3), which is why the description carries the facts.

## 6. The ways to apply approved entries

| way | when | what the person does | what is unverified |
|---|---|---|---|
| import file | a products export is in `exports/` | backup export first; import `products/product-import-<date>.csv` with "Overwrite products with matching handles"; check one product before the rest | `shopify-exports-extract.md` section 2 marks alt-text rows and image rows on overwrite `not found` and a description-only change `inferred` |
| by hand | no export, or a few products | paste each approved line into the product in the admin (description; media item > Add alt text) | nothing beyond the admin's own behavior |
| the host's connection | the connection is installed with write access and the person says yes to the printed plan | nothing; the model applies one product at a time and reports | whether the connection can set an image's alt text is not in the references; the model checks the capability the host lists before offering it |
