# The agent guide's shape, its Liquid outputs, its word lists and an example

Written 2026-10-21 for the `agent-guide` skill from the set's `references/schemas.md` section 7, `references/ai-channels.md` sections 4, 5 and 8 (extract in `ai-channels-extract.md` beside this file) and `references/shopify-exports.md` section 5. `scripts/guide_check.py` reads the four fenced lists and the size line below at run time; change a list here and the check follows. Re-check the platform rows before relying on them.

Contents: 1 the sections; 2 the `agents` outputs; 3 standard paths; 4 claim words; 5 comparison words; 6 size limit; 7 paste facts; 8 example guide.

## 1. The sections, in order

| heading, as written | holds | from the store file | why an agent needs it |
|---|---|---|---|
| `# <store name>: a guide for agents` | the store's name, written as `{{ agents.store_name }}` or as text | section 1, store name | names whose guide this is |
| `## What this store is` | the business in one line; the currency through `{{ agents.currency }}`; where it sells and ships | sections 1 and 2 | the first question an agent answers for a buyer: is this the right kind of shop |
| `## Who it is for` | who buys, in plain words | section 4 | lets an agent match a buyer to the store without guessing at a market |
| `## The product lines and how to choose` | each product line: its name, what it is, who it is for; how to choose between lines only as the lines themselves say | section 2, and section 3 cleared statements | the "which one should I get" question, the commonest before a purchase |
| `## Facts an agent may state` | the fact slots every product page states, and the cleared statements verbatim | section 2 fact slots, section 3 cleared statements | separates what may be repeated from what must be read on the page |
| `## Policies` | a link to each published policy page | section 6 | shipping and returns decide many purchases |
| `## Shopping here as an agent` | the endpoints through `agents` outputs, and Shopify's managed guidance in this set's own words: buyer authorization and review before an order, agent identification with Web Bot Auth, WebMCP tools in a browser and handing back when they cannot help, 429 and `Retry-After`, the buyer's country and currency, the read-only browsing paths | none; `agents` outputs and `ai-channels-extract.md` section 1 (dated 2026-10-21) | Shopify's default answers this part; a custom file has to keep it |
| `## What not to assume` | the statements the store never makes; that prices and availability change; that the file carries no contact details, and the contact page when section 6 names one | sections 3 and 6 | stops an agent filling a gap with a plausible claim |

A section whose store fields are blank keeps its heading and one plain sentence saying the store has not stated it, so the shape holds and the gap is visible. A `## Product index` section may follow the last one in `llms-full.txt.liquid` only.

## 2. The `agents` outputs

The template's context is only `request` and `agents`; `shop`, `collections` and `pages` render blank (`ai-channels-extract.md` section 1). The attribute names below are the ones the references list; what each renders is read from its name, and the references give no sample values, so confirm on the live file after publishing.

| output | what it stands for |
|---|---|
| `{{ agents.store_name }}` | the store's name |
| `{{ agents.store_url }}` | the store's public address; build store links on it, as `{{ agents.store_url }}/policies/refund-policy` |
| `{{ agents.ucp_discovery_url }}` | the UCP profile's address |
| `{{ agents.mcp_endpoint_url }}` | the MCP shopping endpoint |
| `{{ agents.ucp_versions }}` | the UCP versions the store supports |
| `{{ agents.currency }}` | the store currency |
| `{{ agents.sitemap_url }}` | the sitemap's address |

<!-- list: agents-outputs -->
```
store_name
store_url
ucp_discovery_url
mcp_endpoint_url
ucp_versions
currency
sitemap_url
```

## 3. Standard paths

Paths every Shopify storefront serves, from `references/shopify-access.md` section 4, `references/ai-channels.md` section 4 and `references/schemas.md` section 2. A link to one of these passes the link check without a sitemap entry. The storefront search path is left out: `ai-channels.md` section 4 names search among the managed file's browsing URLs, but no reference records its path, so the guide does not link it (not in the references; verify).

<!-- list: standard-paths -->
```
/
/collections/all
/sitemap.xml
/robots.txt
/agents.md
/llms.txt
/llms-full.txt
/.well-known/ucp
```

## 4. Claim words

Words that make a claim a store must stand behind. The check flags each as a warning for the person, never a failure, and skips a line that carries a cleared statement from store file section 3 verbatim. The list is this build's choice, drawn from what the open-web reading in `ai-channels-extract.md` section 2 rewards (facts, no claims the store does not make to people); add to it as runs show new ones.

<!-- list: claim-words -->
```
best
finest
leading
top-rated
top rated
number one
#1
premium
ultimate
perfect
guaranteed
guarantee
revolutionary
world-class
unbeatable
unmatched
cheapest
lowest price
superior
clinically proven
doctor recommended
dermatologist recommended
award-winning
safest
healthiest
cure
cures
miracle
amazing
incredible
must-have
life-changing
all-natural
non-toxic
hypoallergenic
eco-friendly
```

## 5. Comparison words

Words that compare. They fail the check when store file section 3 does not allow comparisons to named competitors (the default is no), and warn when it does, because a comparison still needs a cleared statement.

<!-- list: comparison-words -->
```
better than
worse than
compared to
compared with
versus
vs
unlike
beats
outperforms
alternative to
```

## 6. Size limit

size-limit-bytes: 262144

Source: no row of Shopify's theme limits page names Liquid templates such as `templates/agents.md.liquid`; the nearest row, "Other Liquid files (sections, snippets, layouts)", is 256 KB (`references/shopify-exports.md` section 5, LIM), and a community report (secondary) names the same 256 KB (`references/ai-channels.md` section 4). The check uses 256 KB, as 262144 bytes, until a page states the template's own limit.

## 7. Paste facts

| point | fact | source |
|---|---|---|
| where the file goes | the theme's `templates` folder, as `agents.md.liquid`; it must be Liquid, not a JSON template | `shopify-exports.md` section 5 |
| the editor | Online Store > Themes > the theme's ... menu > Edit code; right-click the folder name > New file...; no spaces in names, the extension required | `shopify-exports.md` section 5 |
| a copy first | the code editor's help page advises duplicating the theme as a backup before editing; the agents template page does not say so | `shopify-exports.md` section 5 |
| who can paste | a person; Shopify bars connected AI tools from editing, publishing or deleting the live theme | `ai-channels-extract.md` section 1; `shopify-access.md` section 2 |
| which paths it serves | `agents.md.liquid` serves `/agents.md`, and `/llms.txt` and `/llms-full.txt` too unless `llms.txt.liquid` or `llms-full.txt.liquid` exists | `ai-channels-extract.md` section 1 |
| undoing it | with no template, each path falls back to Shopify's default; Timeline restores one file at a time and its history is finite | `ai-channels-extract.md` section 1; `shopify-exports.md` section 5 |
| when it shows | the file "is broadly cached", so a change may not show at once | `shopify-exports.md` section 5 |

## 8. Example guide, for an invented store

An invented cookware shop, written as the skill writes from a filled store file. Its store file named two lines, three fact slots, one cleared statement, one statement it never makes, four policy pages and a contact page.

```
# {{ agents.store_name }}: a guide for agents

## What this store is

Fernwood Kitchen Goods sells cast-iron pans and hand-turned wooden utensils for home cooks. Prices are in {{ agents.currency }}. It sells to and ships within the United States and Canada.

## Who it is for

Home cooks who want cookware that lasts and buyers choosing a gift for one.

## The product lines and how to choose

- Cast iron: pre-seasoned skillets and Dutch ovens, for cooks who sear, roast and bake on the stove or in the oven.
- Wooden utensils: spoons, spatulas and boards turned from maple and cherry, for everyday stirring and serving.

A buyer who wants a pan chooses Cast iron; a buyer who wants tools for an existing set chooses Wooden utensils.

## Facts an agent may state

Every product page states these facts; read the value for a product on its page:

- size or capacity, from the specification sheet
- material, from the label
- care instructions, from the label

Statements the store has cleared, verbatim:

- Cast iron: "Seasoned with flaxseed oil before shipping."

## Policies

- Shipping: {{ agents.store_url }}/policies/shipping-policy
- Refunds and returns: {{ agents.store_url }}/policies/refund-policy
- Privacy: {{ agents.store_url }}/policies/privacy-policy
- Terms of service: {{ agents.store_url }}/policies/terms-of-service

## Shopping here as an agent

- Store: {{ agents.store_url }}
- UCP discovery: {{ agents.ucp_discovery_url }} (UCP versions: {{ agents.ucp_versions }})
- MCP endpoint: {{ agents.mcp_endpoint_url }}
- Sitemap: {{ agents.sitemap_url }}
- Personal shopping agents can use the Shop skill for this store.
- Orders and payment: act only with the buyer's authorization. Ask the buyer to review and approve the order on the checkout page, and submit nothing until the buyer has approved it.
- Identify every agent-initiated request as agent traffic. Server-to-server requests and hosted or remote browsers use Web Bot Auth.
- In a browser, carry out each shopping action through the store's WebMCP tools. If those tools are missing or cannot do what the buyer needs, hand the task back to the buyer; do not script checkout forms or page controls.
- When the store answers 429, slow down and wait as long as its Retry-After header says before trying again.
- Where a tool's schema accepts the buyer's country and currency, pass them.
- Read-only browsing: use the shopping tools' structured data first. Otherwise find pages through the sitemap above, read a product at {{ agents.store_url }}/products/{handle} and a collection at {{ agents.store_url }}/collections/all or {{ agents.store_url }}/collections/{handle}, and identify those requests the same way.

## What not to assume

- This store does not state that its wooden utensils are dishwasher safe.
- Prices and availability change; read them from the shopping tools or the product page at the time of the request, not from this file.
- This file carries no contact email or phone number. Questions go through the contact page: {{ agents.store_url }}/pages/contact
```
