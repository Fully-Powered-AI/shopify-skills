# Store file: Harbor Leaf Tea

Template version 0.1.1, 2026-10-21 (0.1.0 earlier the same day; 0.1.1 adds guidance lines under three fields, one optional field in section 4 and a `none` rule in section 6, and changes no field label). The `store-setup` skill fills this in with the person who runs the store and saves it as `<workspace>/store/store.md`. Every other skill in the set reads it first and takes the store's facts and rules from here, never from its own knowledge. Headings are fixed: skills find sections by their numbers. A blank line under a heading means "not yet decided"; a skill that needs it stops and asks, once.

Mark every line with its source in square brackets: `[owner]` for what the person who runs the store said, `[observed]` for what was read from a public page or the admin on a date, `[default]` for a set default the person accepted, `[open]` for an undecided item.

How a value is written, so every script reads it the same way: the value follows the template's text on the field's own line, with its mark last. An indented line under a field is template guidance when it carries no mark, and the person's detail when it carries one; detail never replaces a value that the field's own line already has, and stands in for it only when that line is blank. Scripts find fields by the template's opening words and never read a line stated twice. Never edit the template's text, because scripts find each line by it. Extra detail goes on indented lines under the field, each with its own mark.

## 1. The store

- Store name: Harbor Leaf Tea [owner]
- Public domain, as `https://...`: https://www.harborleaf.example [owner]
- The `.myshopify.com` domain:
- Shopify plan:
- Theme name and version, as the admin shows them under Online Store > Themes:
- Store currency: USD [owner]
- Countries sold to and shipped to:
- Other places the products are sold (marketplaces, retailers, the brand's own apps), one per indented line with the URL:

## 2. What it sells

- The business in one line, in the person's own words: Loose-leaf teas blended in small batches [owner]
- Product lines, one per indented line: the line's name, what it is, who it is for, and the Shopify product category it sits in:
  - House Roast: a medium-roast whole-bean coffee, for people who brew at home; category Food, Beverages & Tobacco > Beverages > Coffee [owner]
- The words buyers use for the category and the products (the search words), one per indented line:
  - loose leaf tea [owner]
  - black tea [owner]
- The facts every product page states (the fact slots), one per indented line: the slot's name, and where the fact comes from (label, specification sheet, the person):
  - origin (country, region), from the label [owner]
  - caffeine level (low, medium, high), from the label [owner]
  - steeping time (minutes), from the label [owner]
  - net weight (grams, ounces), from the label [owner]
  Examples of slots: size or volume, material, ingredients, origin, compatibility with something, care or use instructions, what is in the box.

## 3. Claims and words

- Statements the store makes about its products and has cleared, verbatim, one per indented line with the product or line it applies to; a statement not here is "ask":
- Statements the store never makes, one per indented line, with the reason:
- Words, topics and comparisons the brand does not use (the redlines), one per indented line:
- Comparisons to named competitors allowed [default no]:
- Who clears a new statement (role):

## 4. Buyers and their questions

- Who buys, in plain words:
- The questions buyers ask before buying, five to ten, in the buyer's own words, one per indented line (this is the answer-check list):
  - Which loose leaf black tea is best for mornings? [owner]
  - How long should I steep sencha? [owner]
- Where buyers hear about the store today (search, social, marketplaces, press, word of mouth), one per indented line:

## 5. Apps and systems

- Reviews app, and whether it adds ratings to the product structured data:
- Email and SMS app:
- Other apps that change the storefront or product data (subscriptions, bundles, affiliate, translations), one per indented line:
- Analytics in use:
- The AI tool the person uses (for example Claude, ChatGPT), and whether it is connected to the store through Shopify's connector for that tool:

## 6. Pages, policies and contact

- Policy pages published, one per indented line with the URL (shipping, refund, privacy, terms):
- FAQ or buying-guide pages, one per indented line with the URL, or `none`: https://www.harborleaf.example/pages/faq [owner]
- Public contact email for buyers and agents, the role that reads it, and the reply-time target:
- Popups, age gates or password pages on the storefront, one per indented line (what it is and where it shows), or `none`: none [owner]

## 7. People and roles

Roles, never names. A skill addresses its hand-off to a role.

| role | does | approves |
|---|---|---|
| owner | decides the rules, clears statements, signs | the store file, cleared statements, changes to live product data |
| operator | runs the skills, prepares exports, pastes theme files | drafts before they go to the owner |
| support | answers buyer and agent email | nothing |
| finance | reads the money reports | nothing in slice 1 |

- Who approves a change to product data before it is imported or applied (role):
- Who pastes theme files such as the agent guide (role):

## 8. Access

- How the skills reach the store, one or more of `connection` (the person's AI tool connected through Shopify's connector; name the tool), `exports` (CSV exports dropped into `exports/`), `public` (public pages only):
- Connection access level approved at install (`read`, or `read and write`), and the staff account role it acts through:
- Exports the person can produce and how often (products, orders, customers, inventory):
- Admin API app, only if one exists: its name, the environment variable that holds its token, its scopes [default none]:

## 9. Thresholds and cadences

- Audit cadence for `ai-visibility-audit` [default quarterly]:
- Answer-check cadence [default monthly]: monthly [default]
- Every product image carries alt text [default yes]: yes [default]
- Product pages sampled per audit [default 5]: 2 [owner]
- Low-stock units per variant, for later skills [default 5]:
- Late-order days, for later skills [default 3]:

## 10. AI channels

- Shopify Catalog status as the admin shows it under Sales channels > Agentic > Sources > Shopify Catalog, with the date:
- The product category checked against the Catalog exclusion list (`references/ai-channels.md` section 2): `eligible`, `excluded` or `unknown`, with the date: [open]
- Agentic storefronts switched on, as the admin shows them, one per indented line with the date:
- Agent guide: `shopify default` or `custom`, with the date of the last change:
- Open-web crawler access: `default` (Shopify's robots file) or `restricted` (a `robots.txt.liquid` exists), with the date:

## 11. Decisions log

Dated entries, newest last: `YYYY-MM-DD, role, what was decided, which section changed`.
