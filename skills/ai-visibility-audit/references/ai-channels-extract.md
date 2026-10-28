# What the audit relies on about AI channels: an extract

Dated 2026-10-21. Extracted from the set's `references/ai-channels.md` (written 2026-10-21 from the platforms' own pages read that day), sections 1, 2, 4, 5 and 8, keeping that file's section numbers, so this skill runs alone. Where the two differ, the set's file is the newer word; re-check the platform pages before relying on a detail, because these products change monthly. Text only; no procedure.

## 1. Two doors

A store reaches an assistant's answer through two doors.

- **The feed door.** Shopify Catalog hands product data from eligible products to AI channels that show product cards and, on some channels, check out in the chat. The merchant controls eligibility and the admin's switches, nothing more. Being in the feed does not guarantee placement.
- **The open-web door.** An assistant or agent searches the web, reads the store's pages and other people's pages about it, and decides what to say. The merchant controls what the pages say, how they read to a machine, and what third parties have to cite. Being well written does not guarantee citation.

The audit measures both and claims neither.

## 2. Shopify Catalog and its exclusions

Eligible products enter Shopify Catalog automatically; a merchant cannot opt out of Catalog itself but can stop individual agentic storefronts from reading it. Requirements as Shopify's page `help.shopify.com/en/manual/shopify-catalog/requirements` stated them on 2026-10-21: the store on the Starter plan or higher and not in private mode; a price above zero; no sensitive content in images or description; not in an excluded category, and excluding a category excludes its subcategories. Shopify can change the list. The table as read that day is carried in `assets/catalog-exclusions-2026-10-21.csv`.

The admin shows ineligibility reasons under Sales channels > Agentic > Sources > Shopify Catalog. That screen, not a word match, is the ruling for a store.

## 4. The agent files

Every store serves `/agents.md`, a managed file Shopify writes: UCP discovery and the MCP endpoint, read-only browsing URLs, the published policies and guidance for personal shopping agents. It deliberately omits contact details. `/llms.txt` and `/llms-full.txt` mirror it unless a path-specific template exists. A theme template `templates/agents.md.liquid` replaces the default for all three paths; Shopify's developer page says the managed file is all most stores need and that a custom template is for advanced requirements. A connected AI tool cannot edit the live theme, so a person pastes the template. `/.well-known/ucp` is the Universal Commerce Protocol profile naming an MCP shopping endpoint whose catalog tools require an agent token, so the audit reads the profile and does not call the tools.

## 5. Open-web crawlers and robots

Shopify's default `robots.txt` allows all user agents and has no per-bot AI rules; a theme may override it with `robots.txt.liquid`. Shopify calls robots rules "directional and advisory" for open-web discoverability and separate from Catalog feeds. A crawl allowance is not indexing, citation or recommendation. Crawler names worth knowing (verified 2026-10-19 from the vendors' pages): OpenAI's GPTBot, OAI-SearchBot and ChatGPT-User; Anthropic's ClaudeBot and Claude-User; Perplexity's PerplexityBot and Perplexity-User; Google's Googlebot and Google-Extended; Meta's Meta-WebIndexer, Meta-ExternalAgent and Meta-ExternalFetcher. Training crawlers, search indexers and user-requested fetchers have different purposes and may be allowed separately.

## 8. What the open-web door rewards

A reading of Google's guidance on generative AI search and the Chrome team's guidance for agent-friendly sites, not a ranking formula:

- The facts are in the server-rendered HTML as text: what the product is, for whom, its measurable facts, price, availability, shipping and returns.
- Structured data matches the visible text: `Product` with offers, identifiers, brand and, where a reviews app supplies them, ratings; `Organization` with consistent `sameAs` links; `FAQPage` where real questions are answered.
- Images carry descriptive alt text; one H1; a specific title and description per page.
- A page answers the buyer's actual questions directly, with the conditions that change the answer; a buying guide or FAQ is the natural home.
- Third parties say the same things: reviews, press, forums, marketplace listings and creator posts are what assistants cite most.
- Policies are published and readable; a contact path exists.
- No hidden text for bots, no claims the store does not make to people, no fabricated reviews.

Measurement is the answer check: the buyer questions asked of the assistants on a date, with what they recommended and cited. One answer is an anecdote; a monthly sheet is a trend.
