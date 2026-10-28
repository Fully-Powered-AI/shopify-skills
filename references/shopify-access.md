# How a skill reaches a Shopify store: the three entrances, the hosts, and what each can do

Written 2026-10-21 from Shopify's, Anthropic's and OpenAI's own pages read that day; secondary sources are marked. Re-check before relying on a detail; these products change monthly. Section numbers are fixed.

## 1. The three entrances

| entrance | what it gives | needs | used by |
|---|---|---|---|
| the host's Shopify connection | live reads of products, collections, orders, customers, inventory, analytics; writes to products, collections, inventory and discounts when write access was approved | the person's AI tool connected through Shopify's official connector for that tool, approved in the admin | the model, never a script; what it reads is saved into the workspace as files |
| exports | CSV files from the admin: products, orders, customers, inventory; a receipt that can be kept | the person exports and drops the file into `exports/` | every skill, as its first-class data |
| public pages | what any visitor or agent can read: robots, agent files, the UCP profile, sitemaps, product pages and their public JSON, collections, policies | nothing; `fetch_pages.py` or the person saves them | the found-by-AI skills |

A skill states which entrances it accepts and what it does with only the weakest. No skill requires an API token of its own in slice 1.

## 2. The host's Shopify connection

Shopify publishes official integrations for the hosted assistants and keeps a help section on them (`help.shopify.com/en/manual/ai-powered-tools/connecting-ai-tools`). As of 2026-10-21 it lists: a plugin for ChatGPT, a connector for Claude, connectors for Gemini, Grok, Muse and Perplexity, a plugin for Microsoft Copilot, the Shopify CLI connector for local developer tools, and `shopify.com/SKILL.md`, a pointer file that tells an AI tool which official integration to use and reads or changes nothing itself.

What the connector for Claude exposes (Anthropic's listing at `claude.com/connectors/shopify`, developer Shopify, added April 2026, connector URL `setup.shopify.com/mcp`), 25 tools in all, 24 shown: products (`search_products`, `get-product`, `create-product`, `update-product`, `bulk-update-product-status`, `upload-image`), collections (`search_collections`, `get-collection`, `create-collection`, `update-collection`, `add-to-collection`), orders and customers (`list-orders`, `get-order`, `list-customers`), inventory (`get-inventory-levels`, `set-inventory`), discounts and analytics (`create-discount`, `run-analytics-query`), store (`get-shop-info`, `switch-shop`), and GraphQL (`graphql_schema`, `graphql_query`, `graphql_mutation`, `validate_graphql_codeblocks`). Shopify's help page says the ChatGPT plugin has the same capabilities. A skill names the capability, not the tool; these names are examples of what the model will find.

Rules Shopify states for these integrations:

- Installed from the AI tool's directory, not the Shopify App Store; installing redirects to the admin to approve the data access requested. Use a desktop browser for setup.
- Access is read-only unless write access is approved at install; to reduce access afterward, uninstall. Access is further capped by the permissions of the staff account the tool acts through. Claude adds its own controls, and a workspace owner can restrict the connector.
- Blocked even with write access: issuing refunds, canceling or capturing orders, marking orders paid, processing returns, creating or adjusting gift cards; editing, publishing or deleting the live theme; changing settings such as plan, payments, taxes or domains.
- Changes are made one item at a time, so a large batch can stop partway; finish an incomplete batch in the admin.
- One store is connected at a time; a conversation that started before a switch may keep using the earlier store, so start a new conversation after switching.
- "AI outputs can contain errors, so review any information or action" the tool proposes; the merchant is responsible for changes the tool makes, and data shared through the tool is subject to that company's terms.
- No extra Shopify fee; the person pays the AI tool's subscription.

What this means for a skill: read through the connection freely at the approved level; save what was read into the workspace in the shapes `schemas.md` gives; propose any change as a printed plan; change only after the person's yes, one bounded batch, then report; prefer the admin's CSV import for product data because the file is a receipt; never promise an action from the blocked list.

## 3. Exports

The admin exports CSV files for products, orders, customers and inventory. The column layouts, the import rules for products (matching by handle, the overwrite option, how image rows and alt text are written, which cells an import can change) and what is unverified are recorded in `references/shopify-exports.md`, written by the research pass from Shopify's help pages. Scripts read export columns by name and name any they could not find.

## 4. Public pages

Every Shopify storefront serves, without login: `/robots.txt` (Shopify's default allows all user agents and points agents to the agent guide and the UCP endpoints; a theme may override it with `robots.txt.liquid`); `/agents.md` with `/llms.txt` and `/llms-full.txt` mirroring it unless path templates exist (`references/ai-channels.md` section 4); `/.well-known/ucp`, the Universal Commerce Protocol profile naming an MCP shopping endpoint whose catalog tools require an agent token (Shopify's agent authentication), so a skill reads the profile and does not call the tools; `/sitemap.xml` with child sitemaps for products, pages, collections, blogs and articles and an agentic-discovery sitemap listing the agent guide; `/products.json?limit=250`, the public product list (title, body HTML, vendor, product type, tags, variants with price and sku, images with src; no barcode and no alt text, as observed 2026-10-21), and `/products/<handle>.json`, the single product, which adds the variants' barcode and the images' alt text (`references/shopify-exports.md` section 3; Shopify documents neither endpoint, so they are served without a support commitment); product, collection, page and policy HTML, which on most themes carries JSON-LD for Product, Organization and sometimes FAQPage.

`fetch_pages.py` reads these with plain GET requests, a named user agent, a pause between requests, no cookies, and refuses admin, account, cart and checkout paths. Reading public pages is what any visitor does; the skill still identifies itself and backs off on a 429.

## 5. Developer paths (not used in slice 1)

- **Shopify AI Toolkit** (`github.com/Shopify/shopify-ai-toolkit`, MIT, open-sourced April 2026): a plugin for coding agents (Claude Code, Codex, Cursor, VS Code and others) with documentation and schema search, GraphQL and Liquid validation, and store execution through the Shopify CLI; telemetry is on by default with an opt-out; Shopify does not accept pull requests. A developer's tool, not a merchant's.
- **Shopify CLI connector**: connects a local AI tool to a store the developer authorizes through the CLI.
- **A custom app of one's own**: legacy custom apps created in the admin ended on 2026-01-01; a store's own app is now created in the Dev Dashboard, installed on the store, and obtains an Admin API token by the client credentials grant (`POST https://{shop}.myshopify.com/admin/oauth/access_token`, `grant_type=client_credentials`, id and secret), valid 24 hours, scopes as released on the app's version, and only when the app and the store sit in the same Shopify organization. A client's store in another organization needs the authorization code grant instead. This is the path for a later slice's `--live` scripts, if ever needed.

## 6. The hosts and how each runs a skill

- **Claude.** Claude Code reads a skill folder from its skills location; claude.ai runs custom skills (upload the folder or a zip of it) with code execution for the scripts. The Shopify connector is added under Customize > Connectors.
- **ChatGPT.** OpenAI's help article "Skills in ChatGPT" (read 2026-10-21): skills are available to eligible Business, Enterprise, Healthcare and Edu users subject to workspace settings; a skill is a folder with `SKILL.md` (name and description in the front matter) plus optional `scripts/`, `references/` and `assets/`; a person uploads it from Create > Upload from your computer and ChatGPT scans it before it is available. Secondary reports say skills were off by default in Enterprise workspaces until a 2026-07-23 default-on date and that standalone skills also run in the ChatGPT desktop app, Codex CLI and the IDE extension. The Shopify plugin for ChatGPT is installed as an app from ChatGPT's app directory. Python scripts run in ChatGPT's code execution.
- **Both** follow the Agent Skills open standard, so one folder serves both. A skill writes its instructions host-neutrally: capabilities, not tool names; "the host's Shopify connection", not a product name; and says in Limits what differs (a workspace without skills enabled or without code execution runs the skill's prose by hand and skips the scripts).

## 7. Sources

- https://help.shopify.com/en/manual/ai-powered-tools/connecting-ai-tools (the list of integrations)
- https://help.shopify.com/en/manual/ai-powered-tools/connecting-ai-tools/shopify-connector-for-claude
- https://help.shopify.com/en/manual/ai-powered-tools/connecting-ai-tools/considerations
- https://help.shopify.com/en/manual/ai-powered-tools/connecting-ai-tools/authorizing-access
- https://help.shopify.com/en/manual/ai-powered-tools/connecting-ai-tools/shopify-skill-md
- https://claude.com/connectors/shopify (the tool list)
- https://help.openai.com/en/articles/20001066-skills-in-chatgpt and https://developers.openai.com/codex/skills
- https://github.com/Shopify/shopify-ai-toolkit
- https://shopify.dev/docs/apps/build/authentication-authorization/access-tokens/client-credentials-grant
- Secondary: https://www.usecarly.com/blog/shopify-mcp/, https://flatlineagency.com/blog/shopify-ai-connector-chatgpt-claude, https://community.shopify.dev/t/is-it-still-possible-to-create-a-custom-app-for-a-single-store-admin-storefront-access-without-partner-dashboard-cli/28387
