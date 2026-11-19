# Get your online store ready for AI shopping assistants

FullyPowered Workflow Templates for online store teams turn the AI your store already pays for into a team that knows how the work is done: an online store owner with product details checked and gaps listed for approval, a store operator with the shop's public pages audited for AI assistants, an e-commerce lead with a guide for shopping assistants drafted and checked. Workflow templates, made to be customized and deployed. All plain Markdown, all free, MIT license.

We are FullyPowered AI. We build AI workflows for companies, and these are the templates we start from. We publish them because a good starting point should be open to everyone. Copy one. Change it. Make it yours.

> [!TIP]
> **Missing a template that is not listed here, or want these customized for your organization? Reach out to us.** These are templates, made to be customized and deployed. FullyPowered AI customizes and builds AI workflows, connects them to your business systems, installs them in your agents and puts them in the hands of the people who own the work. [See more examples for online store teams](https://fullypowered.ai/industries/ecommerce-and-retail/?utm_source=github&utm_medium=referral&utm_campaign=workflow-collections&utm_content=shopify-skills-readme&from=gh-shopify-skills-readme) · [Have one built for your team](https://fullypowered.ai/pricing/?utm_source=github&utm_medium=referral&utm_campaign=workflow-collections&utm_content=shopify-skills-readme&from=gh-shopify-skills-readme). Not sure where to start? Email hello@fullypowered.ai and a person will answer.

**Who this is for**

- Online store owners who want AI assistants and shopping agents to describe their products accurately.
- Store and e-commerce leads who want a repeatable check of public pages their team can run.
- The person who runs the store, who gets prepared drafts and still approves every change.

**What these are for**

- **Your best way of doing it, for the whole team.** One piece of work, written down precisely enough that an assistant prepares it the same way every time.
- **Work you can check.** Every template says what it needs, what it produces, what it checked and what it could not.
- **A person decides.** Anything that sends, posts, pays or changes a record waits for someone to approve it.
- **Tied into your business systems.** A workflow can be designed to pull from the systems your company already runs, and even push data back into them, with guardrails and a person approving. [Browse the Connectors Directory](https://fullypowered.ai/connectors/?utm_source=github&utm_medium=referral&utm_campaign=workflow-collections&utm_content=shopify-skills-readme&from=gh-shopify-skills-readme).
- **Free, open and portable.** MIT-licensed plain instructions that run in the assistant or agent your team already uses: ChatGPT, Claude, Claude Code, Claude Cowork, Codex, Copilot, Gemini, Grok, Perplexity.

**Quick start**

1. **Try it now with one product.** Pick one product. Copy the instruction below into the AI assistant you already use. Fill in the four lines at the end with that product's details, then send it. Nothing on your store changes.

   ```text
   Help me fill the gaps on one product page of my online store. I will
   paste the product description, the text from its label or spec sheet, a
   one-line note on what the main photo shows, and a few questions buyers
   ask.

   1. List each fact the label states that the description leaves out. Put
   the source in brackets after each one.
   2. Write one line of alt text for the main photo: what the item is, the
   product name, the size or variant, and the view.
   3. Answer each buyer question using only the label and the description,
   and name the source. If neither one says, mark the line Open and write
   the question I should ask the owner.

   Mark every line Proposed. Do not invent facts. Do not change my existing
   description.

   Description: [paste here]
   Label or spec sheet: [paste here]
   Main photo shows: [one line]
   Buyer questions: [two or three]
   ```

2. Read what comes back. It marks what it checked and what is left for you. What a result looks like, for a candle shop:

   ```text
   Juniper Hollow soy candle, 9 oz

   Facts the description leaves out
   - Proposed: Burn time is about 50 hours. [label]
   - Proposed: Wax is a soy and coconut blend. [label]
   - Proposed: Wick is cotton. [label]

   Alt text
   - Proposed: Juniper Hollow soy candle in an amber glass jar, 9-ounce size, front view with the lid off.

   Buyer questions
   - Can I reuse the jar? Proposed: Yes. The label says to remove leftover wax with warm water before reuse. [label]
   - Is it safe for a room with pets? Open: neither the label nor the description says. Ask the owner what the store can state.
   ```

3. Stop there. You will know if this is for you. When you want it fitted to your company, or built into your agents, [that is what we do](https://fullypowered.ai/pricing/?utm_source=github&utm_medium=referral&utm_campaign=workflow-collections&utm_content=shopify-skills-readme&from=gh-shopify-skills-readme).

You start each run, supply the pages, labels and questions, and approve every line. The templates prepare and check. Nothing is published, imported or changed on the store unless you do it or say yes to it.

These are templates and samples, made to be changed and put to work. Copy one, adjust it to how your store runs, and use it in the AI assistant you already pay for. They are a starting point, not a complete list. A workflow can be one step or many, and FullyPowered AI builds workflows of any kind for a company, including ones that run several steps.

Four skills for preparing and reviewing a Shopify store's public information for AI assistants and shopping agents. They use a shared store file, saved pages and exports; an existing Shopify connection is optional.

## Included

| Skill | Work it does |
|---|---|
| [store-setup](skills/store-setup/SKILL.md) | Creates and checks the store file with the operator; records observed values for confirmation. |
| [ai-visibility-audit](skills/ai-visibility-audit/SKILL.md) | Runs 18 checks on saved public pages and maintains an answer-check sheet. |
| [agent-guide](skills/agent-guide/SKILL.md) | Drafts and checks an agent-guide Liquid template, with an optional product index. |
| [product-facts](skills/product-facts/SKILL.md) | Identifies product-information gaps and prepares approved additions for import. |

Each folder includes its instructions, templates, reference extracts, scripts and offline fixtures. Shared file schemas and dated platform references are in `references/`. This package contains these four skills only. See [SOURCES.md](SOURCES.md) for upstream acknowledgments.

## Install and run locally

Clone the public package:

```sh
git clone https://github.com/Fully-Powered-AI/shopify-skills.git
cd shopify-skills
```

Keep the whole package together: some instructions read `../../references/` from their skill folder. Register the skill folders in place with your host's loader, or ask a file-aware agent to read the relevant `skills/<name>/SKILL.md` directly. Copying a skill folder alone can lose shared reference context.

Use a host with file access and Python 3.10 or newer for the scripts. The scripts use the standard library. Host connection capabilities must be checked in the host; this extraction does not establish that every advertised host has been tested.

From the package root, create a private workspace:

```sh
mkdir -p workspace
python3 -I skills/store-setup/scripts/store_file.py workspace --init
```

Then run `store-setup` with the person who runs the store to fill the open fields. Run the audit on saved public pages, then use its findings to choose `agent-guide` or `product-facts`. Scripts take the workspace path; instructions and assets stay in their package folders. The root `.gitignore` excludes this workspace, exports and other local output; keep credentials out of the store file.

Only `ai-visibility-audit/scripts/fetch_pages.py` makes network requests, after its printed plan and confirmation. The other scripts work on local files. Publishing a guide, importing a CSV or changing a connected store requires the person's action or the skill's explicit approval step. Platform facts retain their source dates and need checking before live use; the offline tests do not verify current platform policy or live imports.

## Offline tests

From the package root, with Bash and Python available:

```sh
bash skills/store-setup/scripts/fixtures/run_fixtures.sh
bash skills/ai-visibility-audit/scripts/fixtures/run_fixtures.sh
bash skills/agent-guide/scripts/fixtures/run_fixtures.sh
bash skills/product-facts/scripts/fixtures/run_fixtures.sh
```

These suites use sample store data and temporary workspace copies. Fetch cases use dry-run, plan-only or rejected inputs and make no network requests. They check deterministic behavior, not recommendation ranking, model quality or live connector compatibility.

## Releases and license

This is the public release edition of a private authoring project. Updates are prepared in that project and released here explicitly; the two editions are not automatically merged. Keep local store or company work in a separate workspace.

[MIT](LICENSE), copyright 2026 FullyPowered AI. Third-party source acknowledgments and recorded upstream license terms remain in [SOURCES.md](SOURCES.md); this license does not relicense the cited source materials.
