# Store file: Ember Lane Sauces

Template version 0.1.1, 2026-10-21 (0.1.0 earlier the same day; 0.1.1 adds guidance lines under three fields, one optional field in section 4 and a `none` rule in section 6, and changes no field label). The `store-setup` skill fills this in with the person who runs the store and saves it as `<workspace>/store/store.md`. Every other skill in the set reads it first and takes the store's facts and rules from here, never from its own knowledge. Headings are fixed: skills find sections by their numbers. A blank line under a heading means "not yet decided"; a skill that needs it stops and asks, once.

Mark every line with its source in square brackets: `[owner]` for what the person who runs the store said, `[observed]` for what was read from a public page or the admin on a date, `[default]` for a set default the person accepted, `[open]` for an undecided item.

How a value is written, so every script reads it the same way: the value follows the template's text on the field's own line, with its mark last. An indented line under a field is template guidance when it carries no mark, and the person's detail when it carries one; detail never replaces a value that the field's own line already has, and stands in for it only when that line is blank. Scripts find fields by the template's opening words and never read a line stated twice. Never edit the template's text, because scripts find each line by it. Extra detail goes on indented lines under the field, each with its own mark.

## 1. The store

- Store name: Ember Lane Sauces [owner]
- Public domain, as `https://...`: https://www.emberlane.example [observed]
- The `.myshopify.com` domain: ember-lane-sauces.myshopify.com [observed]
- Shopify plan: Basic, as the admin showed it 2026-10-21 [owner]
- Theme name and version, as the admin shows them under Online Store > Themes: Dawn 15.2.0 [observed]
- Store currency: USD [observed]
- Countries sold to and shipped to: United States and Canada [owner]
- Other places the products are sold (marketplaces, retailers, the brand's own apps), one per indented line with the URL:
  - two independent grocers, no URL [owner]

## 2. What it sells

- The business in one line, in the person's own words: Small-batch hot sauces and chili crisp, made in our own kitchen [owner]
- Product lines, one per indented line: the line's name, what it is, who it is for, and the Shopify product category it sits in:
  Write each line as `<name>: <what it is>, <who it is for>; category <the full Shopify product category path>`, or end it with `same category` to take the line above's. Scripts read the name before the colon and the category after the word `category`; a line name is matched whole against product titles, handles and types.
  - Sauces: fermented hot sauces in 5 oz bottles, for home cooks who want heat with flavor; category Food, Beverages & Tobacco > Food Items > Condiments & Sauces > Hot Sauce [owner]
  - Crisp: chili crisp in 6 oz jars, for the same cooks; same category [owner]
- The words buyers use for the category and the products (the search words), one per indented line:
  - hot sauce [owner]
  - fermented hot sauce [owner]
  - chili crisp [owner]
- The facts every product page states (the fact slots), one per indented line: the slot's name, and where the fact comes from (label, specification sheet, the person):
  - heat level on the store's 1 to 5 scale, from the person [owner]
  - net volume (fl oz, ml), from the label [owner]
  - ingredients, from the label [owner]
  - allergens, from the label [owner]
  - storage after opening, from the label [owner]
  Examples of slots: size or volume, material, ingredients, origin, compatibility with something, care or use instructions, what is in the box.
  Write the words the pages actually use in parentheses after the slot's name, separated by commas, for example `size in ounces (oz, ounce)` or `dishwasher compatibility (dishwasher safe, top rack)`. A script finds the slot by the words of its name, by any one of those phrases whole, or, for a unit, by a stated quantity such as `8 oz`; it never guesses other words.

## 3. Claims and words

- Statements the store makes about its products and has cleared, verbatim, one per indented line with the product or line it applies to; a statement not here is "ask":
  - Sauces: "Fermented for at least 30 days." [owner]
- Statements the store never makes, one per indented line, with the reason:
  - any health benefit; the store makes no health claims [owner]
- Words, topics and comparisons the brand does not use (the redlines), one per indented line:
  - "hottest in the world" [owner]
- Comparisons to named competitors allowed [default no]: no [default]
- Who clears a new statement (role): owner [default]

## 4. Buyers and their questions

- Who buys, in plain words: Home cooks in North America who like fermented flavors [owner]
- The questions buyers ask before buying, five to ten, in the buyer's own words, one per indented line (this is the answer-check list):
  - How hot is it compared with a jalapeno? [owner]
  - Does it need to be refrigerated after opening? [owner]
  - Is it gluten-free? [owner]
  - What makes fermented hot sauce different? [owner]
  - How long does an open bottle last? [owner]
- Answer-check prompts (optional), the questions above as a buyer would type them into an assistant that knows nothing about the store, naming the kind of product and the need but no brand, one per indented line; when blank, the answer check uses the questions above with a short opening:
  - Which fermented hot sauce is milder than sriracha but still has real flavor? [owner]
  - Does an opened bottle of fermented hot sauce need to go in the fridge? [owner]
- Where buyers hear about the store today (search, social, marketplaces, press, word of mouth), one per indented line:
  - farmers markets [owner]
  - search [owner]

## 5. Apps and systems

- Reviews app, and whether it adds ratings to the product structured data: none [owner]
- Email and SMS app: none [owner]
- Other apps that change the storefront or product data (subscriptions, bundles, affiliate, translations), one per indented line: none [owner]
- Analytics in use: Shopify analytics [owner]
- The AI tool the person uses (for example Claude, ChatGPT), and whether it is connected to the store through Shopify's connector for that tool: ChatGPT, connected at read level [owner]

## 6. Pages, policies and contact

- Policy pages published, one per indented line with the URL (shipping, refund, privacy, terms):
  Write `none` on its own indented line, with a mark, for a policy page the store does not publish.
  - https://www.emberlane.example/policies/shipping-policy [observed]
  - https://www.emberlane.example/policies/refund-policy [observed]
  - https://www.emberlane.example/policies/privacy-policy [observed]
  - https://www.emberlane.example/policies/terms-of-service [observed]
- FAQ or buying-guide pages, one per indented line with the URL, or `none`: none [observed]
- Public contact email for buyers and agents, the role that reads it, and the reply-time target: hello@emberlane.example, support, one business day [owner]
- Popups, age gates or password pages on the storefront, one per indented line (what it is and where it shows), or `none`: none [observed]

## 7. People and roles

Roles, never names. A skill addresses its hand-off to a role.

| role | does | approves |
|---|---|---|
| owner | decides the rules, clears statements, signs | the store file, cleared statements, changes to live product data |
| operator | runs the skills, prepares exports, pastes theme files | drafts before they go to the owner |
| support | answers buyer and agent email | nothing |
| finance | reads the money reports | nothing in slice 1 |

- Who approves a change to product data before it is imported or applied (role): owner [default]
- Who pastes theme files such as the agent guide (role): operator [default]

## 8. Access

- How the skills reach the store, one or more of `connection` (the person's AI tool connected through Shopify's connector; name the tool), `exports` (CSV exports dropped into `exports/`), `public` (public pages only): connection (ChatGPT), exports and the API [owner]
- Connection access level approved at install (`read`, or `read and write`), and the staff account role it acts through: read, through the owner's account [owner]
- Exports the person can produce and how often (products, orders, customers, inventory): products, monthly [owner]
- Admin API app, only if one exists: its name, the environment variable that holds its token, its scopes [default none]: none [default]

## 9. Thresholds and cadences

- Audit cadence for `ai-visibility-audit` [default quarterly]: quarterly [default]
- Answer-check cadence [default monthly]: monthly [default]
- Every product image carries alt text [default yes]: yes [default]
- Product pages sampled per audit [default 5]: 5 [default]
- Low-stock units per variant, for later skills [default 5]: 5 [default]
- Late-order days, for later skills [default 3]: 3 [default]

## 10. AI channels

- Shopify Catalog status as the admin shows it under Sales channels > Agentic > Sources > Shopify Catalog, with the date: eligible, 2026-10-21 [owner]
- The product category checked against the Catalog exclusion list (`references/ai-channels.md` section 2): `eligible`, `excluded` or `unknown`, with the date: eligible, 2026-10-21 [observed]
- Agentic storefronts switched on, as the admin shows them, one per indented line with the date:
  - ChatGPT, 2026-10-21 [owner]
- Agent guide: `shopify default` or `custom`, with the date of the last change: shopify default, 2026-10-21 [observed]
- Open-web crawler access: `default` (Shopify's robots file) or `restricted` (a `robots.txt.liquid` exists), with the date: default, 2026-10-21 [observed]

## 11. Decisions log

Dated entries, newest last: `YYYY-MM-DD, role, what was decided, which section changed`.
- 2026-10-21, owner, store file set up with store-setup 0.1.0, all sections
