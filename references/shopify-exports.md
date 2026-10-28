# Shopify exports, product import behavior, public product JSON, structured data, theme files and admin screens

Written 2026-10-21 by the research pass from Shopify's help and developer pages and Google's Search Central page, all read 2026-10-21 Pacific time, 2026-10-22 03:53 to 03:59 UTC (the log has times). Facts only, no procedure. Points not from Shopify or Google are marked **secondary**; points seen in a saved storefront response rather than read in documentation are marked **observed**. Section numbers are fixed. Re-check before relying on a detail; these pages change.

Short source keys used in the tables:

| key | URL |
|---|---|
| CSV | https://help.shopify.com/en/manual/products/import-export/using-csv |
| TPL | https://help.shopify.com/cdn/shopifycloud/product-knowledge/production/csv/product_template.csv (Shopify's sample file, linked from CSV) |
| IMP | https://help.shopify.com/en/manual/products/import-export/import-products |
| EXP | https://help.shopify.com/en/manual/products/import-export/export-products |
| ISS | https://help.shopify.com/en/manual/products/import-export/common-import-issues |
| AJAX | https://shopify.dev/docs/api/ajax/reference/product |
| GML | https://developers.google.com/search/docs/appearance/structured-data/merchant-listing (page says "Last updated 2026-09-08 UTC") |
| SD | https://shopify.dev/docs/api/liquid/filters/structured_data |
| TMPL | https://shopify.dev/docs/storefronts/themes/architecture/templates |
| AGT | https://shopify.dev/docs/storefronts/themes/architecture/templates/agents-md-liquid |
| LIM | https://shopify.dev/docs/storefronts/themes/architecture/limits |
| CODE | https://help.shopify.com/en/manual/online-store/themes/theme-structure/extend/edit-theme-code |
| AS | https://help.shopify.com/en/manual/online-sales-channels/agentic-storefronts |
| AH | https://help.shopify.com/en/manual/online-sales-channels/agentic-storefronts/agentic-home |
| ALT | https://help.shopify.com/en/manual/products/product-media/add-alt-text |

## 1. The products CSV (read 2026-10-21)

### 1.1 Two generations of column names

Shopify's current help page and sample file use new, plain-language headers (`URL handle`, `Description`, `Product image URL`, `SKU`). The headers the skills' brief names (`Handle`, `Body (HTML)`, `Image Src`, `Variant SKU`, `Variant Barcode`, `Image Alt Text`, `SEO Title`) are the older generation. Shopify says it "maintains backward compatibility with older column names" and that a file with the old singular `Barcode` column "is updated to Barcodes on the next occasion that you export" (CSV). Neither page states which generation a given store's export carries today, so a script must accept both and map them (section 1.4).

### 1.2 Current headers, in the order of Shopify's sample file (TPL)

| # | header | holds (CSV) |
|---|---|---|
| 1 | Title | product name; the only required column for new products |
| 2 | URL handle | unique product identifier, used in the product URL |
| 3 | Description | "details about what the product is"; CSV does not say whether HTML is accepted |
| 4 | Vendor | origin or source of the product |
| 5 | Product category | Standard Product Taxonomy label, as the full breadcrumb with `>` separators or the category ID (example form `hg-15-1-2`); used for US tax rates |
| 6 | Type | merchant's own label |
| 7 | Tags | keywords for search and filtering |
| 8 | Published on online store | defaults to true |
| 9 | Status | active, draft or archived; defaults to active |
| 10 | SKU | variant SKU |
| 11 | Variant Barcodes | sample file's spelling; CSV's table says `Barcodes`: up to 20 barcodes, `;`-separated |
| 12-20 | Option1 name, Option1 value, Option1 Linked To, Option2 name, Option2 value, Option2 Linked To, Option3 name, Option3 value, Option3 Linked To | option names and values; Linked To connects an option to a category metafield (CSV spells it `Option1 LinkedTo`) |
| 21 | Price | defaults to 0.00 |
| 22 | Compare-at price | original price for showing a discount |
| 23 | Cost per item | merchant's cost |
| 24 | Charge tax | defaults to true |
| 25 | Tax code | (sample file only; not described in CSV's table) |
| 26-29 | Unit price total measure, Unit price total measure unit, Unit price base measure, Unit price base measure unit | (sample file only) |
| 30 | Inventory tracker | `shopify` when tracking is on, blank otherwise (EXP) |
| 31 | Inventory quantity | single-location stores only; defaults to 0 |
| 32 | Continue selling when out of stock | deny or continue; defaults to deny |
| 33 | Weight value (grams) | defaults to 0 |
| 34 | Weight unit for display | g, kg, lb or oz; defaults to kg |
| 35 | Requires shipping | defaults to true |
| 36 | Fulfillment service | manual or a custom service handle; `gift_card` for gift cards (EXP) |
| 37 | Product image URL | public image URL; "Shopify downloads the images during the import and re-uploads them in your store" |
| 38 | Image position | display order, ascending from 1 |
| 39 | Image alt text | maximum 512 characters, 125 or fewer recommended |
| 40 | Variant image URL | variant image |
| 41 | Gift card | defaults to false |
| 42 | SEO title | blank means the product Title is used |
| 43 | SEO description | up to 320 characters |
| 44 | Color (product.metafields.shopify.color-pattern) | a category metafield column; metafield headers follow `<name> (product.metafields.<namespace>.<key>)` |
| 45-57 | Google Shopping / Google product category, / Gender, / Age group, / Manufacturer part number (MPN), / Ad group name, / Ads labels, / Condition, / Custom product, / Custom label 0 to 4 | values used by sync apps |
| 58-61 | Packed product length, width, height, dimension unit | go together; unit cm or in |

CSV's table also lists `Price / International`, `Compare-at price / International`, `Included / [Primary]` and `Included / International` (market columns; "International" is replaced by the market's name) and an optional `Collection` column that "isn't included in exports". The sample file (TPL) does not carry those. Column order in a real export: **not found** stated; read columns by name.

### 1.3 Rows: variants and extra images (CSV)

| point | what CSV says |
|---|---|
| variants | first row carries the product; "In the following rows, enter the URL handle. Then skip the Title, Description, Vendor, and Tags columns." |
| extra images, simple product | "In the following rows, only enter the handle and the URL for each additional image." |
| one image per row | "You must use only one row per image"; up to 250 images per product |
| image order | Image position, ascending from 1 |
| export carries images? | "the images associated with each product aren't included in the CSV file" (EXP); the file carries image URLs, not image files |
| sorting | importing a file "sorted by a spreadsheet editor such as Microsoft Excel or Apple Numbers" can lose the product's images (IMP) |
| encoding | "your CSV file must be UTF-8 encoded" (ISS) |

### 1.4 Older headers and their current equivalents

ISS's "Invalid CSV header: missing headers" entry gives the first line a file "should be", in the old naming: `Handle, Title, Body (HTML), Vendor, Type, Tags, Published, Option1 Name, Option1 Value, Option2 Name, Option2 Value, Option3 Name, Option3 Value, Variant SKU, Variant Grams, Variant Inventory Tracker, Variant Inventory Qty, Variant Inventory Policy, Variant Fulfillment Service, Variant Price, Variant Compare-at Price, Variant Requires Shipping, Variant Taxable, Variant Barcode, Image Src, Image Alt Text` (26 columns, ISS).

| old (ISS, and the brief) | current (CSV/TPL) | basis of the pairing |
|---|---|---|
| Handle | URL handle | same definition; pairing is this pass's reading |
| Body (HTML) | Description | same |
| Variant SKU | SKU | same |
| Variant Barcode | Barcodes / Variant Barcodes | CSV names the singular-to-plural update |
| Image Src | Product image URL | same |
| Image Position | Image position | case only |
| Image Alt Text | Image alt text | case only |
| Product Category | Product category | case only |
| SEO Title / SEO Description | SEO title / SEO description | case only |
| Published | Published on online store | same |
| Variant Price | Price | same |

Shopify publishes no old-to-new mapping table: **not found**. Header matching should be case-insensitive.

### 1.5 Required columns (CSV, IMP, ISS)

| case | required |
|---|---|
| new product | Title only |
| adding variants | URL handle as well |
| update (overwrite) | "the only required columns are URL handle and Title" |
| update touching variant fields (SKU, weight and the like) | "you must also include the Option1 name and Option1 value columns" |
| a handle with no title | ISS lists "there is at least one product with a handle, but no product title" as an import error |

## 2. Import behavior (read 2026-10-21)

| question | finding | source |
|---|---|---|
| the overwrite option | labeled **"Overwrite products with matching handles"** (not "Overwrite any current products that have the same handle"). Selected: "the values in the CSV file overwrite the values in the matching columns in the existing product list." Not selected: "the products that match an existing handle are ignored" | IMP, CSV |
| a column present but blank | "the matching value in the product list is overwritten as blank" | CSV, IMP |
| a column omitted from the file | "the value in the product list remains the same" | CSV, IMP |
| a column whose data depends on a missing column | "existing data is deleted or removed"; also "If your data depends on a column that's missing, then you receive an error" | IMP, CSV |
| option columns omitted | "If you don't include the Option1 name and Option1 value columns, then a new default variant is created and existing variants are deleted"; example given: the SKU column included without the Option1 columns | CSV |
| changing option values | "deletes existing variant IDs' values and creates new variant IDs"; can "break third-party dependencies on variant IDs" | CSV |
| Handle + image URL + alt text only, on an existing image | **not found**: no page says whether this updates the existing image's alt text, re-downloads and adds the image again, or replaces the image set. Note also that such a file lacks Title, which CSV calls required on update | CSV, IMP, ISS |
| description changed without touching variants | **not found** as a stated case. What is stated implies it: omitted columns stay the same, and variants are disturbed only by option/variant columns. A file with URL handle, Title and Description only is consistent with the rules but no page confirms the outcome | CSV |
| images on overwrite (kept, replaced, duplicated) | **not found** | CSV, IMP, ISS |
| file size | "Your product CSV can't exceed 15 MB" | IMP |
| row or product limit | **not found**. ISS: "no more than 10,000 new variants can be created by CSV uploads" for stores with 500,000+ variants, not Plus | IMP, ISS |
| image size | up to 5000 x 5000 px or 25 megapixels | ISS |
| runs in the background | **not found** stated | IMP |
| email | "When your CSV file is uploaded, you receive a confirmation email from Shopify to the email address of your user account" (on upload; a completion email is not described) | IMP |
| cancel and history | "Product imports started with a CSV file can't be canceled once they begin, and you can't view a history of past imports" | IMP |
| backup | "Before you start your import, make sure that you have a backup of your product data" (links to export) | IMP |
| flow | Products > Import > Add file > optional "Publish new products to all sales channels" > optional overwrite > Upload and continue > review > Import products | IMP |

Secondary (community.shopify.com threads, not Shopify documentation, read 2026-10-21): users report that importing a file with blank image cells deleted or dissociated existing images, and that repeated image URLs created duplicate files. Threads: https://community.shopify.com/t/urgent-missing-product-images-after-import-possible-rollback/396027, https://community.shopify.com/t/csv-import-creates-multiple-images-in-files/389592.

## 3. Public product JSON (read and observed 2026-10-21)

| point | finding | source |
|---|---|---|
| documented status of `/products.json` and `/products/<handle>.json` | **not found** in Shopify documentation: served by storefronts but not documented, so merely served, with no support commitment | searches of shopify.dev and help.shopify.com (log) |
| the documented neighbor | the Ajax API documents `GET /{locale}/products/{product-handle}.js`: `id, title, handle, description, published_at, created_at, vendor, type, tags, price, price_min, price_max, available, price_varies, compare_at_price, variants, images, featured_image, options, url`; variants carry `price, sku, barcode, available, compare_at_price, requires_shipping, taxable, weight, option1-3`; `images` is a list of URL strings with no alt; prices in the example are integers (12900), the unit is not stated; no support or versioning statement | AJAX |
| `/products.json` fields | **observed**: `products[]` with `id, title, handle, body_html, vendor, product_type, tags, published_at, created_at, updated_at, options, variants, images`; variants `id, title, price` (string, e.g. "30.00"), `compare_at_price, sku, available, grams, requires_shipping, taxable, position, option1-3, featured_image`; images `id, src, position, width, height, variant_ids`. **No `alt` on images and no `barcode` on variants** in the list response | saved storefront response, one store |
| `/products/<handle>.json` fields | **observed**: `product` with the above plus `image, published_scope, template_suffix`; variants add `barcode, inventory_management, inventory_policy, fulfillment_service, weight, weight_unit, price_currency`, and lack `available`; images add `alt` | saved storefront response, one store |
| `limit` and its maximum | **not found** in Shopify documentation. Secondary: 250 is the observed ceiling, larger values clamped (https://dev.to/rslndev/we-tested-shopifys-productsjson-on-68-stores-the-limits-tutorials-dont-mention-1ofj, https://www.productscraper.online/blog/shopify-products-json-endpoint) | |
| `page` versus `since_id` | **not found** in Shopify documentation. Secondary: `page=N` used in practice, stopping at an empty page; `since_id` support inconsistent on the storefront (same two sources) | |

Consequence for the reference `shopify-access.md` section 4, which says the list JSON carries barcode and alt: per the observation, alt and barcode come from the per-handle JSON, not the list.

## 4. Product structured data (read 2026-10-21)

Google, Product merchant listing (GML):

| on | required | recommended |
|---|---|---|
| Product | name, image, offers | aggregateRating, audience, brand.name, category, color, description, gtin (or gtin8, gtin12, gtin13, gtin14, isbn), hasAdultConsideration, hasCertification, inProductGroupWithID, isVariantOf, material, mpn, pattern, review, size, sku, subjectOf |
| Offer | price (or priceSpecification.price), priceCurrency (or priceSpecification.priceCurrency); price above zero | availability, hasMerchantReturnPolicy, itemCondition, priceValidUntil, shippingDetails, url, validFrom, validThrough |

Shipping and returns (GML): Google recommends a global shipping policy and a global return policy "under Organization markup instead"; offer-level `shippingDetails` and product-level `hasMerchantReturnPolicy` are for overriding the standard policy. Where markup is hard to keep current, Google suggests configuring shipping and returns in Merchant Center. Precedence, strongest first: product-level Merchant Center feeds, Content API settings, settings in Merchant Center or Search Console, product-level markup, organization-level markup.

Shopify (SD): the Liquid `structured_data` filter works on `product` and `article`; a product with no variants is output as schema.org `Product`, one with variants as `ProductGroup`; the documented example carries `brand, category, description, image, name, offers (availability, price, priceCurrency, url), url`. SD does not mention sku, gtin, shipping or return policy, and does not say which themes use the filter. Shopify's own themes on GitHub (read 2026-10-21): Dawn `sections/main-product.liquid` line 749-750 and Horizon `sections/product-information.liquid` line 1-2 wrap `product | structured_data` in `<script type="application/ld+json">` (https://github.com/Shopify/dawn, https://github.com/Shopify/horizon). Organization JSON-LD from Shopify themes: **not found** documented.

## 5. Theme files (read 2026-10-21)

| point | finding | source |
|---|---|---|
| the template | `agents.md.liquid` "Renders the agents.md file, which is hosted at the /agents.md URL"; must be Liquid, not JSON; not in themes by default (Shopify generates a default file) | TMPL, AGT |
| fallback | `/agents.md`: agents.md.liquid, then the generated default. `/llms.txt`: llms.txt.liquid, then agents.md.liquid, then default. `/llms-full.txt`: llms-full.txt.liquid, then agents.md.liquid, then default. "if you add only an agents.md.liquid template, then it's used for all three URLs" | AGT |
| objects available inside it | "Only two objects are available": `request` and `agents`; `shop`, `collections`, `pages` and other globals render blank | AGT |
| caching | the file "is broadly cached" | AGT |
| where it is added | Online Store > Themes > the theme's ... menu > Edit code, then create the file in the theme's templates folder | AGT, CODE |
| adding a file in the code editor | right-click the folder name > New file...; no spaces in names; the extension is required | CODE |
| duplicate first | CODE: "Duplicate your theme" to make a backup copy so changes can be discarded. AGT itself does not say so | CODE |
| file history | Timeline restores one file at a time; "Timeline history is finite"; files in `assets/` have no Timeline | CODE |
| size limit | LIM: "Other Liquid files (sections, snippets, layouts)" 256 KB; JSON templates 512 KB; total code 250 MB; 100,000 files per theme. No row names Liquid templates such as `templates/agents.md.liquid` explicitly; the 256 KB row is the nearest | LIM |
| JSON template count | maximum 1000 JSON templates per theme | TMPL |
| which theme's template is served; preview before publishing | **not found** (lead, 2026-10-21): AGT says the template renders the file hosted at `/agents.md` and names no theme; no page read says whether an unpublished (duplicated) theme's `agents.md.liquid` can be previewed, through the theme preview or otherwise, before that theme is published. A skill promises no preview and says so in Limits | AGT, CODE |

## 6. Admin screens (read 2026-10-21)

| screen | finding | source |
|---|---|---|
| Agentic | Sales channels > Agentic (admin URL `admin.shopify.com/apps/agentic`); needs store owner or the Products > View and App and sales channel > Agentic staff permissions. Lets the merchant choose AI channels (ChatGPT, Google AI Mode and Gemini, Microsoft Copilot, Meta), shows why the store might not be eligible for Shopify Catalog, an Explore section and search preview, a listing quality indicator and per-product "Listing insights" (signals such as description completeness and image coverage), performance in search and sales; AI-channel orders carry channel or referrer attribution. AH does not mention agent files. Sub-tab names: **not found** listed | AS, AH |
| products export | Products > Export; scope: current page, all products, selected products, or products matching search and filters; "CSV file for Excel, Numbers, or another spreadsheet program" or "Plain CSV file". Emailed if any single product has more than 100 variants (for current page and selected), otherwise downloaded; non-owners' exports also go to the owner's email; exports of thousands of variants can time out, so filter and split | EXP |
| products import | Products > Import > Add file (flow in section 2) | IMP |
| alt text by hand | Products > product name > click the media item (Preview media) > Add alt text > enter > Save alt text > X to exit; 512 characters maximum, 125 or less recommended; "You can also upload alt text in a CSV file" | ALT |

## 7. Not found

What the pages read on 2026-10-21 did not say:

1. Which header generation (old `Handle`/`Image Src` or current `URL handle`/`Product image URL`) a store's export carries today, and the column order of a real export.
2. An official old-to-new header mapping.
3. Whether a CSV of only Handle, image URL and alt text updates an existing image's alt text, re-adds the image, or replaces the image set; also whether such a file without Title is accepted at all (Title is stated as required on update).
4. Whether existing images are kept, replaced or duplicated when an overwrite import carries image rows, or when it carries no image columns.
5. A stated case of changing the description without touching variants (inferred from the omitted-column rule only).
6. A row or product count limit for imports (only the 15 MB file limit and the 10,000-new-variant cap for very large stores).
7. That imports run in the background, and a completion email (only a confirmation email on upload is stated).
8. Any documentation of `/products.json` or `/products/<handle>.json`: support status, fields, the `limit` maximum, `page` or `since_id` paging.
9. Whether Description accepts HTML (CSV's table does not say).
10. A file size limit stated specifically for Liquid templates.
11. The Agentic section's tab names.
12. Organization JSON-LD from Shopify themes.
13. Which theme's `agents.md.liquid` the store serves, and whether an unpublished (duplicated) theme's template can be previewed before publishing (lead, 2026-10-21; see section 5's last row).
