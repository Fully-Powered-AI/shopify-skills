# How a Shopify store is found by AI assistants and shopping agents

Written 2026-10-21 from the platform pages listed in section 9. The reference covers store categories generally; a category restriction is applied to the store's recorded products, not inferred from a particular brand. Secondary sources (trade press, agency blogs, an aggregator) are marked. These are the facts the found-by-AI skills cite; a skill never adds a platform fact from memory. Re-check before relying on a detail. Section numbers are fixed.

## 1. Two doors

A store reaches an assistant's answer through two doors. The **feed door**: Shopify Catalog hands product data to AI channels that show product cards and, on some channels, check out in the chat; the merchant does nothing beyond eligibility and the admin's switches. The **open-web door**: an assistant or agent searches the web, reads the store's pages and other people's pages about it, and decides what to say; the merchant controls what the pages say, how they read to a machine, and what third parties have to cite. Being in a feed does not guarantee placement, and being well written does not guarantee citation; the skills measure both and claim neither.

## 2. Shopify Catalog and its exclusions

Shopify Catalog is a structured source of product information gathered from eligible products on Shopify stores, used by Shop, AI platforms, shopping sites and agents. Eligible products are included automatically; a merchant cannot opt out of Catalog itself but can stop individual agentic storefronts from reading it. Requirements (`help.shopify.com/en/manual/shopify-catalog/requirements`): the store on the Starter plan or higher and not in private mode; a price above zero; no sensitive content in images or description; not in an excluded category, and excluding a category excludes its subcategories. Shopify can change the list. Excluded as read on 2026-10-21:

| category | examples Shopify gives |
|---|---|
| Alcohol | alcoholic beverages, homebrewing and winemaking supplies |
| Tobacco and vaping | all tobacco products, vaporizers, e-cigarettes, e-liquid |
| Drugs and smoking accessories | CBD supplements, smoking accessories, rolling papers |
| Prescription and medical products | hearing aids, respiratory care equipment |
| Weapons, ammunition and accessories | firearms, ammunition, combat knives, stun guns, pepper spray |
| Recreational and imitation weapons | hunting and shooting products, archery, airsoft, paintball |
| Explosives | fireworks, firecrackers, sparklers |
| Science, laboratory and hazardous materials | laboratory equipment, specimens, chemicals, dissection kits |
| Adult and mature content | all products in the Mature category: pornography, erotic videos, magazines and literature, sex toys, erotic clothing |
| Sexual health and wellness products | condoms, spermicides, personal lubricants |
| Money-related products | bullion, collectible coins and banknotes, virtual currency |
| Prop money | play money, replica currency |
| Services and product add-ons | professional, personal, home and automotive services |
| Event tickets | concerts, sports, other events |
| Live animals | live animals, animal husbandry products |
| Uncategorized | products Shopify classifies as Uncategorized |

The admin shows ineligibility reasons under Sales channels > Agentic > Sources > Shopify Catalog. The audit's `assets/catalog-exclusions-<date>.csv` carries this table for the V16 check; update the file and its date when the page changes.

## 3. Agentic storefronts: the channels and what they get

Shopify's Agentic Storefronts channel covers ChatGPT, Microsoft Copilot, Google AI Mode and the Gemini app, managed from the admin; Meta's Muse reads Shopify Catalog as well (Shopify's news page of 2026-03-24 and the help pages). Requirements: sell to US customers, Catalog-eligible products, the Agentic Storefronts Supplemental Terms accepted, published terms of service, privacy, and return and refund policies. Status as the help pages said on 2026-10-21: ChatGPT live for merchants selling to US buyers wherever the store is based; Copilot and Google in early access, Google requiring a US-based store and the Google & YouTube channel with product sync. Data shared by default: title, description, options, images, price and availability, kept current; compare-at prices optional. Checkout on ChatGPT happens on the merchant's own store; Copilot and Google can take direct checkout, switchable per channel. Shopify Catalog Mapping lets a store source titles, descriptions, categories and attributes from metafields or title conventions, and group variant-like products into one listing. Each AI channel decides what it shows for a request; eligibility is not placement.

Non-Shopify brands can join through the Agentic plan, which adds products to Catalog without an online store.

## 4. The agent files and their templates

Every store serves `/agents.md`, a managed file Shopify writes: UCP discovery and the MCP endpoint, read-only browsing URLs for products, collections and search, the store's published policies, and guidance for personal shopping agents (the Shop skill). It deliberately omits contact details. `/llms.txt` and `/llms-full.txt` mirror it by default. Shopify's developer page says the managed file is all most stores need and that a custom template is for advanced requirements.

Templates (changelog 2026-05-28, `shopify.dev/changelog/posts/customize-llmstxt-llms-fulltxt-and-agentsmd`): `templates/agents.md.liquid` controls `/agents.md` and is the default for the other two; `templates/llms.txt.liquid` controls only `/llms.txt`; `templates/llms-full.txt.liquid` controls only `/llms-full.txt`; with no template a path falls back to the agents template, then to Shopify's default. The template cannot be a JSON template; its context is only `request` and `agents` (`store_name`, `store_url`, `ucp_discovery_url`, `mcp_endpoint_url`, `ucp_versions`, `currency`, `sitemap_url`); `shop`, `collections` and `pages` render blank, so product facts in a custom guide are written text and endpoints come from `agents`. Shopify advises against private merchant data such as contact email addresses or phone numbers in this file, and to keep the endpoints discoverable through `agents` rather than hardcoded. Theme files are edited under Online Store > Themes > Edit code; Shopify's rules for connected AI tools bar them from editing the live theme, so a person pastes the file, ideally into a duplicated theme first. Size limits for the template are not documented on the pages read; a community report (secondary) names a 256 KB theme-file limit.

## 5. Open-web crawlers and robots

Shopify's default `robots.txt` allows all user agents and has no per-bot AI rules; a theme may override it with `robots.txt.liquid`. Shopify's agentic-storefronts page calls robots rules "directional and advisory" for open-web discoverability and separate from Catalog feeds. The managed agent guide asks agents to identify agent traffic (Web Bot Auth for server-to-server and hosted browsers), to use the store's WebMCP tools for shopping actions in a browser, and to back off on 429. A crawl allowance is not indexing, citation or recommendation; the audit records access and says nothing about ranking.

What Shopify's generated agent guide asks of agents (read 2026-10-21 at `/agents.md` on a store with no `agents.md.liquid`; the generated text is Shopify's and the points are recorded here so a custom guide can carry them in its own words and cite this section rather than a saved page): place orders and submit payment only with the buyer's authorization and follow the required review and approval steps, which means asking the buyer to review and approve the order on the checkout page and waiting for that before submitting; identify requests as agent-initiated, with Web Bot Auth for server-to-server requests and hosted or remote browsers; in a browser, use the store's WebMCP tools for every shopping action and, when they are unavailable or cannot do what is needed, hand back to the buyer rather than scripting checkout forms or page controls; back off on 429 responses and respect `Retry-After`; use the buyer's country and currency where the tool schemas support them; for read-only browsing, prefer the shopping tools' structured data, and otherwise discover URLs through `/sitemap.xml`, read products at `/products/{handle}` and collections at `/collections/all` or `/collections/{handle}`, following the same identification guidance. The generated guide names no storefront search path, so the set's guide template links none. The guide also names the store's policy pages and says the document is the store's canonical agent-facing description.

Crawler names worth knowing when reading a robots file (the source research records vendor-page verification on 2026-10-19): OpenAI's GPTBot, OAI-SearchBot and ChatGPT-User; Anthropic's ClaudeBot and Claude-User; Perplexity's PerplexityBot and Perplexity-User; Google's Googlebot and Google-Extended; Meta's Meta-WebIndexer, Meta-ExternalAgent and Meta-ExternalFetcher. Training crawlers, search indexers and user-requested fetchers have different purposes and may be allowed separately.

## 6. Platform policies on what may be surfaced

Stated here so a skill can tell a store where to look, never as a legal statement.

- **OpenAI**: product feeds into ChatGPT are open to approved partners through chatgpt.com/merchants; products must be "legal, safe, and appropriate for a general audience"; excluded categories include adult content, age-restricted goods such as alcohol, nicotine and gambling, harmful or dangerous materials, weapons, prescription-only medications, unlicensed financial products and legally restricted goods (`developers.openai.com/commerce/guides/get-started`). The commerce-policies page itself refused our fetch; secondary snippets say it prohibits "adult sexual products such as sex toys".
- **Meta**: commerce policies prohibit adult products and listings that "position products in a sexually suggestive manner", and medical and healthcare products including medical devices and ingestible supplements; the page read names no sexual-health exception (`facebook.com/policies_center/commerce/`). Muse's in-chat checkout draws on Meta's catalog, so these rules reach Muse.
- **Google Merchant Center**: sexual merchandise is restricted to adults and shown "in limited scenarios based on user search queries, user age and local laws"; nudity and adult content are disallowed in about thirty listed countries (`support.google.com/merchants/answer/6150138`). Google AI Mode and Gemini take Shopify products through the Google & YouTube channel.

A store whose category sits on one of these lists has the feed door closed or narrowed on that channel; the open-web door stays open, and the audit says which is which.

## 7. How the personal agents find merchants

Secondary sources throughout; neither company has documented this.

- **Muse (Meta)**: a study of 50 prompts by Profound, reported by ppc.land (2026), found two parallel searches: a browser search of merchant sites and a query of Meta's product catalog; the catalog supplied most candidates and about a third of final picks. Reporting on an instruction file says the agent ranks well-known merchants first, checks no more than three stores on the open web per request, and favors brands that sell direct over resellers. Meta has not commented. Shopify stores reach Muse's catalog side through Shopify Catalog.
- **Instinct**: a text-message agent. Reported Shopify partnership (September 2026) to search Shopify's merchant network and use Shop Pay; browses store sites like a visitor; has its own email address and emails businesses to ask about availability; pushes unsolicited "Selections" (TechCrunch, 2026-09-30). The browsing and email paths do not depend on Catalog.

What this rewards: a site that works in a plain browser (no barrier before the product page), clear availability on the page, and a public contact address someone answers quickly.

## 8. What the open-web door rewards

The set's reading of Google's guidance on generative AI search (`developers.google.com/search/docs/fundamentals/ai-optimization-guide`), the Chrome team's guidance for agent-friendly sites (`web.dev/articles/ai-agent-site-ux`), and the source research's SEO audit method; a reading, not a ranking formula:

- The facts are in the server-rendered HTML as text, not only in scripts or structured data: what the product is, for whom, its measurable facts, price, availability, shipping and returns.
- Structured data matches the visible text: `Product` with offers, identifiers (sku, gtin or mpn), brand and, where a reviews app supplies them, ratings; `Organization` with consistent `sameAs` links; `FAQPage` where real questions are answered.
- Images carry descriptive alt text; controls have names; one H1; a specific title and description per page.
- A page exists that answers the buyer's actual questions directly, with the conditions that change the answer; a buying guide or FAQ is the natural home.
- Third parties say the same things: reviews, press, forums, marketplace listings and creator posts are what assistants cite most; the store's own pages are one source among them.
- Policies are published and readable; a contact path exists.
- No hidden text for bots, no claims the store does not make to people, no fabricated reviews.

Measurement is the answer check (`schemas.md` section 6): the buyer questions asked of the assistants on a date, with what they recommended and cited. A snippet is an anecdote; a monthly sheet is a trend.

## 9. Sources

Platform pages, read 2026-10-21: https://help.shopify.com/en/manual/shopify-catalog; https://help.shopify.com/en/manual/shopify-catalog/requirements; https://help.shopify.com/en/manual/online-sales-channels/agentic-storefronts/requirements; https://help.shopify.com/en/manual/online-sales-channels/agentic-storefronts/products; https://www.shopify.com/news/agentic-commerce-momentum; https://shopify.dev/changelog/posts/customize-llmstxt-llms-fulltxt-and-agentsmd; https://shopify.dev/docs/storefronts/themes/architecture/templates/agents-md-liquid; https://developers.openai.com/commerce/guides/get-started; https://www.facebook.com/policies_center/commerce/; https://support.google.com/merchants/answer/6150138; https://developers.google.com/search/docs/fundamentals/ai-optimization-guide; https://web.dev/articles/ai-agent-site-ux.

Secondary: https://ppc.land/metas-muse-agent-puts-well-known-merchants-first-as-it-gains-ad-accounts/; https://ppc.land/metas-muse-draws-4-of-6-shopping-picks-from-2-websites-profound-finds/; https://www.tryprofound.com/blog/the-era-of-personal-agents-muse-and-instinct; https://techcrunch.com/2026/09/30/instincts-new-product-recommendations-are-giving-some-users-the-ick/; https://www.eesel.ai/blog/instinct-ai-review; https://community.shopify.com/t/shopify-now-serves-llms-txt-natively-custom-redirect-no-longer-works/622018.
