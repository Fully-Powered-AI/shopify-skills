# Platform facts store-setup relies on

Extracted 2026-10-21 from the set's shared references, `../../../references/shopify-access.md` and `../../../references/ai-channels.md` (both read from Shopify's, Anthropic's and OpenAI's pages on 2026-10-21), so this folder runs alone with a filled store file. Re-check before relying on a detail; these products change monthly. Nothing here is a legal statement. Section numbers are fixed.

## 1. The AI tool's Shopify connection

- Shopify publishes official integrations for the hosted assistants, among them a connector for Claude and a plugin for ChatGPT; Shopify's help page says the ChatGPT plugin has the same capabilities as the Claude connector (shopify-access section 2). So a person on either host can connect the store directly; the integration is installed from the AI tool's own directory and the person approves the data access in the Shopify admin.
- Access is read-only unless write access was approved at install, and is further capped by the staff account the tool acts through (shopify-access section 2).
- Even with write access the connection cannot issue refunds, cancel or capture orders, mark orders paid, process returns, create or adjust gift cards, edit, publish or delete the live theme, or change settings such as plan, payments, taxes or domains (shopify-access section 2).
- One store is connected at a time; after switching stores, start a new conversation (shopify-access section 2).
- The connection's tools are grouped as products, collections, orders and customers, inventory, discounts and analytics, store, and GraphQL; the store group gives store information (shopify-access section 2). Which fields a store-information read returns (plan, theme, markets) is not in the references; verify by reading and record what was returned.

## 2. Admin screens the person checks

- Shopify Catalog status: Sales channels > Agentic > Sources > Shopify Catalog, which also shows ineligibility reasons (ai-channels section 2).
- Themes: Online Store > Themes, where the theme's name and version show; theme code under Edit code (ai-channels section 4).
- Products export: Products > Export (`../../../references/shopify-exports.md` section 6).

## 3. Agentic storefronts

Shopify's Agentic Storefronts channel covers ChatGPT, Microsoft Copilot, Google AI Mode and the Gemini app, managed from the admin; requirements include selling to US customers, Catalog-eligible products, accepted supplemental terms and published terms of service, privacy, and return and refund policies (ai-channels section 3).

## 4. Shopify Catalog exclusions

Eligible products enter Shopify Catalog automatically; requirements include the Starter plan or higher, a price above zero, and a category not on the exclusion list, where excluding a category excludes its subcategories (ai-channels section 2). The list as read on 2026-10-21 is carried as `../assets/catalog-exclusions-2026-10-21.csv`, with Shopify's example terms; update the file and its date when the page changes.

## 5. The agent guide and the robots file

- Every store serves `/agents.md`, a managed file Shopify writes (discovery and endpoint details, browsing URLs, policies, guidance for personal shopping agents including the Shop skill); `/llms.txt` and `/llms-full.txt` mirror it by default; a theme template `templates/agents.md.liquid` replaces it (ai-channels section 4).
- Shopify's default `robots.txt` allows all user agents and has no per-bot AI rules; a theme may override it with `robots.txt.liquid` (ai-channels section 5). AI crawler names worth recognizing are listed in ai-channels section 5 and carried in `../assets/observe-signals-2026-10-21.csv`.
