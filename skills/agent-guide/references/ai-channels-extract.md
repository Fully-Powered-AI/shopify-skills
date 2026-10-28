# Extract: the agent files and what the open-web door rewards

Extracted 2026-10-21 from the set's `references/ai-channels.md` sections 4, 5 and 8 (written 2026-10-21 from the platforms' own pages read that day), with the theme-file rows of `references/shopify-exports.md` section 5 and its section 7 item 13 and the connection limits of `references/shopify-access.md` section 2 that this skill relies on. Refreshed 2026-10-21 in fix round 2 with the managed guide's points from section 5 and the two not-found points. This copy lets the skill folder run alone; when the set's files change, this extract is refreshed from them, never from memory. Re-check before relying on a detail.

## 1. The agent files and their templates (from `ai-channels.md` section 4)

- Every store serves `/agents.md`, a managed file Shopify writes: UCP discovery and the MCP endpoint, read-only browsing URLs for products, collections and search, the store's published policies, and guidance for personal shopping agents (the Shop skill). It deliberately omits contact details. `/llms.txt` and `/llms-full.txt` mirror it by default.
- Shopify's developer page says the managed file is all most stores need and that a custom template is for advanced requirements.
- Templates (Shopify changelog of 2026-05-28): `templates/agents.md.liquid` controls `/agents.md` and is the default for the other two; `templates/llms.txt.liquid` controls only `/llms.txt`; `templates/llms-full.txt.liquid` controls only `/llms-full.txt`. With no template, a path falls back to the agents template, then to Shopify's default.
- The template cannot be a JSON template. Its context is only `request` and `agents` (`store_name`, `store_url`, `ucp_discovery_url`, `mcp_endpoint_url`, `ucp_versions`, `currency`, `sitemap_url`); `shop`, `collections` and `pages` render blank. Product facts in a custom guide are therefore written text, and endpoints come from `agents`.
- Shopify advises against private merchant data such as contact email addresses or phone numbers in this file, and to keep the endpoints discoverable through `agents` rather than hardcoded.
- Theme files are edited under Online Store > Themes > Edit code. Shopify's rules for connected AI tools bar them from editing the live theme, so a person pastes the file, ideally into a duplicated theme first.
- Size limits for the template are not documented on the pages read; a community report (secondary) names a 256 KB theme-file limit.

From `ai-channels.md` section 5, as the lead recorded Shopify's generated guide on 2026-10-21 (read at `/agents.md` on a store with no `agents.md.liquid`; the generated text is Shopify's, so a custom guide carries these points in its own words and cites this section, never a saved page). The managed guide asks agents to:

- place orders and submit payment only with the buyer's authorization, following the required review and approval steps: the buyer reviews and approves the order on the checkout page, and the agent waits for that approval before submitting;
- identify requests as agent-initiated, using Web Bot Auth for server-to-server requests and for hosted or remote browsers;
- in a browser, use the store's WebMCP tools for every shopping action, and when they are unavailable or cannot do what is needed, hand back to the buyer rather than script checkout forms or page controls;
- back off on 429 responses and respect `Retry-After`;
- use the buyer's country and currency where the tool schemas support them;
- for read-only browsing, prefer the shopping tools' structured data, and otherwise discover URLs through `/sitemap.xml`, read products at `/products/{handle}` and collections at `/collections/all` or `/collections/{handle}`, with the same identification.

The generated guide names no storefront search path, so the skill's template links none. It also names the store's policy pages and calls itself the store's canonical agent-facing description.

From `shopify-exports.md` section 5: the file is created in the theme's templates folder (right-click the folder > New file...; no spaces in names; the extension is required); the code editor's help page advises duplicating the theme first, the agents template page does not; Timeline restores one file at a time and its history is finite; the file "is broadly cached"; the nearest theme-limit row is 256 KB for other Liquid files.

Not found, from `shopify-exports.md` section 5 (last row) and section 7 (item 13), recorded by the lead on 2026-10-21: which theme's `agents.md.liquid` the store serves (the agents template page names no theme), and whether an unpublished, duplicated theme's template can be previewed, through the theme preview or otherwise, before that theme is published. A skill promises no preview.

From `shopify-access.md` section 2: the connected AI tools for Claude, ChatGPT and the others cannot edit, publish or delete the live theme even with write access.

## 2. What the open-web door rewards (from `ai-channels.md` section 8)

The set's reading of Google's guidance on generative AI search, the Chrome team's guidance for agent-friendly sites and the project's own AI-search audit; a reading, not a ranking formula. The points this skill relies on:

- The facts are on the page as text: what the product is, for whom, its measurable facts, price, availability, shipping and returns.
- A page exists that answers the buyer's actual questions directly, with the conditions that change the answer.
- Policies are published and readable; a contact path exists.
- No hidden text for bots, no claims the store does not make to people, no fabricated reviews.

Being well written does not guarantee citation, and a custom guide is one source among many (`ai-channels.md` section 1). Measurement is the answer check that `ai-visibility-audit` keeps.
