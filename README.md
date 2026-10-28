# Shopify Skills

Part of **Fully Powered Capability Templates** by [Fully Powered AI](https://fullypowered.ai/).

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

These suites use invented store data and temporary workspace copies. Fetch cases use dry-run, plan-only or rejected inputs and make no network requests. They check deterministic behavior, not recommendation ranking, model quality or live connector compatibility.

## Releases and license

This is the public release edition of a private authoring project. Updates are prepared in that project and released here explicitly; the two editions are not automatically merged. Keep local store or company work in a separate workspace.

[MIT](LICENSE), copyright 2026 Fully Powered AI. Third-party source acknowledgments and recorded upstream license terms remain in [SOURCES.md](SOURCES.md); this license does not relicense the cited source materials.
