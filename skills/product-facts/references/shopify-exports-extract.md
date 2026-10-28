# Extract: the products CSV and its import, as this skill relies on them

Extracted 2026-10-21 from the set's `references/shopify-exports.md` (written that day by the research pass from Shopify's help pages, read 2026-10-21; source keys below). Facts only. When the set's file changes, this extract is redone from it and redated; `product_import.py` reads the table in section 2 at run time, so a status changed here reaches the script without editing code.

Sources: CSV = help.shopify.com/en/manual/products/import-export/using-csv; IMP = .../import-products; EXP = .../export-products; ISS = .../common-import-issues; ALT = help.shopify.com/en/manual/products/product-media/add-alt-text; TPL = Shopify's sample product CSV, linked from CSV.

## 1. Column names, both generations

Shopify's current sample file uses plain-language headers; older exports and its own error page use the older names. Shopify says it keeps backward compatibility with older names, and no page says which generation a given store's export carries, so the scripts accept both and match case-insensitively (CSV, ISS).

| what | older header | current header |
|---|---|---|
| product identifier | Handle | URL handle |
| title (required on update) | Title | Title |
| description | Body (HTML) | Description |
| category | Product Category | Product category |
| product type (the merchant's own label) | Type | Type |
| tags (keywords for search and filtering) | Tags | Tags |
| status | Status | Status |
| variant sku | Variant SKU | SKU |
| variant barcode | Variant Barcode | Barcodes, or Variant Barcodes in the sample file |
| image URL | Image Src | Product image URL |
| image alt text | Image Alt Text | Image alt text |
| image position (display order) | Image Position | Image position |
| variant image | Variant Image | Variant image URL |
| option columns | Option1 Name, Option1 Value | Option1 name, Option1 value |

Rows: the first row of a product carries the product; following rows carry the handle with a variant or one extra image each; one image per row (CSV). Product category is the taxonomy breadcrumb with `>` separators or the category ID (TPL). Alt text: at most 512 characters, 125 or fewer recommended (CSV, ALT). The file must be UTF-8 and at most 15 MB (ISS, IMP). A file sorted in a spreadsheet program can lose the product's images (IMP).

## 2. Import behaviors and their status

`status` is `stated` (a Shopify page says it), `inferred` (follows from stated rules, no page confirms the case) or `not found` (no page read says it).

| id | behavior | status | source |
|---|---|---|---|
| overwrite-option | with "Overwrite products with matching handles" selected, values in the file's columns overwrite the matching product's values; without it, matching handles are ignored | stated | IMP, CSV |
| blank-cell | a column present but blank overwrites the value as blank | stated | CSV, IMP |
| omitted-column | a column left out of the file leaves the value as it is | stated | CSV, IMP |
| options-with-variants | a file with variant fields but without Option1 name and value creates a new default variant and deletes the existing ones | stated | CSV |
| required-on-update | an overwrite needs URL handle and Title | stated | CSV |
| description-update | an overwrite that changes only the description leaves variants and images as they were | inferred | CSV |
| image-alt-update | an image row with the image's existing URL and new alt text updates that image's alt text rather than adding the image again | not found | CSV, IMP, ISS |
| image-rows-on-overwrite | existing images are kept, not duplicated or replaced, when the overwrite file carries the same image rows | not found | CSV, IMP, ISS |
| cancel | an import cannot be canceled once begun, and there is no import history | stated | IMP |
| backup | Shopify advises a backup export before importing | stated | IMP |

Secondary (community threads, not Shopify documentation): users report blank image cells deleting images and repeated image URLs creating duplicate files.

Which columns the import file carries (the lead's rule of 2026-10-21, the set's `references/schemas.md` section 8, resting on `omitted-column` above, the set's `references/shopify-exports.md` section 2: "the value in the product list remains the same"). When a run has no approved alt text, every image column (the image URL, image alt text, image position and variant image columns of section 1, and any other header naming an image) is left out of the file, and a row that is then left with nothing but its handle is dropped; the images then rest on that stated rule, not on `image-rows-on-overwrite`, and the variant cells travel as exported with their option columns (`options-with-variants`). The file is still imported one product first. When alt text is approved, the image rows travel as exported and the file depends on `image-alt-update` and `image-rows-on-overwrite`, both not found, so it is UNVERIFIED.

## 3. Admin paths

- Export: Products > Export; choose all, current page, selected or filtered products, and "Plain CSV file" or the spreadsheet variant (EXP).
- Import: Products > Import > Add file > optionally "Overwrite products with matching handles" > Upload and continue > review > Import products; a confirmation email is sent on upload (IMP).
- Alt text by hand: Products > the product > click the media item > Add alt text > Save alt text (ALT).

## 4. Not found on the pages read

Which header generation a store's export carries; an official old-to-new mapping; whether an alt-text-only image row updates, re-adds or replaces images; whether images are kept on an overwrite carrying image rows; a stated case of a description-only change; whether the Description column accepts HTML (the older column is named Body (HTML)).
