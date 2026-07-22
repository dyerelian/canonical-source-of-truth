---
name: source-of-truth
description: Create, update, or close a project's canonical Confluence "source of truth" page for any project, GTD-tracked or ad-hoc, in Codex or Claude Code. Use when the user asks to create/spin up a source of truth, canonical page, project page, or single source of truth for a project or initiative; to update/refresh a project's Confluence page with a decision, milestone, status change, risk, or new update; or to close out a project's page when it's done. Uses connected Confluence/Atlassian tools plus read-only context from Granola, email/.msg files, Slack, Jira, SharePoint/local files, and the GTD workbook.
---

# Source of Truth (Canonical Project Page)

Confluence is the **publicly-facing single source of truth** for every project. This skill
creates, updates, and closes those canonical pages for **any** project — whether or not it is
tracked in a Getting Things Done (GTD) workbook. (Inspired by Naomi's "Canonical
Everything" — one authoritative page per project.)

This skill **owns** the canonical-page process. The GTD skills (`add-gtd-items`, `gtd`) and
`/close-day` reference this skill's `references/canonical-project-page.md` for the create /
update / close mechanics rather than keeping their own copy.

## Runtime compatibility

- **Configuration:** Read `config/source-of-truth.local.json` first. If it is missing, read
  `config/source-of-truth.example.json` for the expected shape and ask the user to run
  `install.ps1` with their Confluence values. `references/confluence-instance.md` explains the
  config fields and setup rules.
- **Codex:** Prefer the connected `mcp__my_atlassian` Confluence tools when present
  (`confluence_get_page`, `confluence_get_page_by_title`, `confluence_search`,
  `confluence_create_page`, `confluence_update_page`). If only the generic Atlassian
  connector is available, use `mcp__atlassian` tools and the cloud/site values in local config.
- **Claude Code:** Use the equivalent Confluence MCP tools exposed in that environment. The
  same workflow applies even if the namespace renders with hyphens instead of underscores.
- Before creating or updating project pages, verify the configured Confluence space and
  Active/Closed index page IDs. Do not create project pages until the Active index page ID is
  configured or explicitly discovered.

> **Local fallback mode (Atlassian access blocked, since 2026-07-21).** While Confluence is
> unreachable, this skill writes an interim local **`SOURCE_OF_TRUTH.docx`** in each project's
> folder instead of a Confluence page. Confluence stays the canonical home — the local doc is a
> bridge to migrate up once access is restored. See "Local fallback mode" below and
> `references/canonical-project-page.md` → "Local fallback mode". Detect the block when any
> `confluence_*` call returns 401/403 or the Confluence/Atlassian MCP server is disabled or
> unreachable, or when the user asks for the local doc explicitly.

## When to use

- **Create** — a new project or initiative needs its canonical page (e.g. after a kickoff
  meeting). Also use to **reconcile** an existing ad-hoc page onto the convention.
- **Update** — an existing project changes: a status/owner/target change, a decision, a
  milestone, a new risk/open question, or a tied task worth surfacing publicly.
- **Close** — a project is done; move its page from the Active to the Closed index list.

## Workflow

### 1. Identify the project & check for an existing page

- Determine the project name and whether it already has a page:
  - Search the configured Confluence space by title (`confluence_get_page_by_title` /
    `confluence_search`, or the generic Atlassian search/page tools).
  - If the project is in the GTD workbook, check its Projects-row `notes` (column **O**) for
    `Canonical page: <url>`.
- If a page exists → this is an **update** (or reconcile). If not → this is a **create**.

### 2. Gather context (active, read-only)

Pull real context before writing, per `references/context-sources.md`:
Granola meetings, email/`.msg` files (via `scripts/read_msg.py`), Slack, Atlassian
(Jira/Confluence), SharePoint/OneDrive/Downloads folders and local files, and the GTD
workbook. Also check for project-specific skills when the project maintains local skill
documentation. Keep searches narrow and recent; capture only page-relevant facts (outcome,
owner, status, target dates, key links, relevant skills, decisions, milestones, risks,
updates). Always capture the **SharePoint folder link** for Key Links.

### 3. Create / Update / Close the page

Follow `references/canonical-project-page.md`:
- **Create** — build the page from the storage-format body template, create it under
  the configured `Active Projects` parent/index page, then append its link to the Active
  Projects index list.
- **Update** — `confluence_get_page`, **merge** the change into Overview / Key Links /
  Skills / Milestones / Decisions / Open Questions-Risks / Updates (never blank a section),
  `confluence_update_page`.
- **Close** — flip the page Status to Closed, move its link from the Active index list
  to the configured Closed index list.

Apply the **page content rules** every time: spell out every acronym on first use with the
acronym in parentheses; attribute to the meeting/discussion, **never** name or link a
capture/notes tool (no Granola links anywhere on the page); **never** put GTD item keys
(`P-###`/`A-###`/`W-###`) or "GTD"/"next action" tracking language on the page; keep it
public-facing and self-contained.

### 4. Link to the GTD workbook (only if tracked there)

If the project is tracked in the GTD workbook, link the two per
`references/canonical-project-page.md` → "Linking to the GTD workbook (optional)": store
`Canonical page: <url>` in the project's `notes` (column **O**) via the **`add-gtd-items`**
writer. The link is one-directional — workbook → page only; do **not** put the GTD Project ID
or any GTD key on the page. If the project is **not** in the workbook, skip this — offer to add
a project row only if Dan wants it. Never require the workbook.

### 5. Report

Report the page title, URL, its index-list membership (Active/Closed), whether it was
created / updated / closed and what changed, and any GTD linkage made.

## Local fallback mode (Atlassian unavailable)

When Confluence can't be reached (see the callout at the top), do everything the same —
identify the project, gather context (§2), apply the **page content rules** — but read/write a
local `SOURCE_OF_TRUTH.docx` instead of a Confluence page, per
`references/canonical-project-page.md` → "Local fallback mode". In short:

1. **Locate the project folder.** For a GTD project, use its SharePoint/working folder (the same
   one that would go under Key Links); read column **O** notes for a folder hint. For an ad-hoc
   project, ask Dan for the folder path. The file is `<project folder>\SOURCE_OF_TRUTH.docx`.
2. **Create** — build the content model (see the renderer's JSON shape) and render:
   `& "C:\Program Files\Python312\python.exe" scripts/source_of_truth_docx.py render --input model.json --output "<folder>\SOURCE_OF_TRUTH.docx"`.
3. **Update — read, merge, re-render (never edit in place; Word COM is broken here).** First
   `... source_of_truth_docx.py read --input "<folder>\SOURCE_OF_TRUTH.docx"` to get the current
   model, apply the **same merge rules** as a page (update Overview cells, append Decisions,
   prepend dated Updates, add Milestones/Risks — never blank a section), then `render` the full
   model back to the same path.
4. **Close** — set the model's `status` to `Closed`/`Complete` and prepend a dated Updates entry;
   re-render. (There are no Active/Closed index lists locally.)
5. **When Atlassian access returns**, offer to migrate each `SOURCE_OF_TRUTH.docx` up to a proper
   Confluence page (the model maps 1:1 to the storage-format body template) and then treat
   Confluence as canonical again.

The renderer embeds the content model as `word/sotdata.json` inside the `.docx`, so `read` round-
trips losslessly; if that part is ever missing it falls back to parsing the document headings.
Never hand-edit the `.docx`.

## References & scripts

- `references/canonical-project-page.md` — the authoritative create / update / close mechanics,
  body template, page content rules, **and the local-fallback mechanics**. **This is the file
  the GTD skills and `/close-day` point at.**
- `references/confluence-instance.md` — configuration resolution rules and fresh-install setup.
- `references/context-sources.md` — how to gather context from each source, read-only.
- `scripts/source_of_truth_docx.py` — render/read the interim local `SOURCE_OF_TRUTH.docx`
  (fallback mode). Run via `C:\Program Files\Python312\python.exe`.
- `scripts/read_msg.py` — parse a saved Outlook `.msg` file (subject/from/to/date/attachments/
  body). Run with `py`, `python`, or a known full Python interpreter path.

## Guardrails

- **Confluence is the only external write**, and only when creating/updating/closing a page —
  all context gathering is strictly read-only (never post to Slack/Teams, send mail, or modify
  Jira/Granola).
- **Merge, never overwrite** on updates — preserve every existing section; append Decisions /
  prepend Updates with ISO dates from `currentDate`.
- **One page per project** — search before creating to avoid duplicates; reuse/link an existing
  page instead.
- **GTD writes go through `add-gtd-items`** — never hand-write the `.xlsx` (Excel COM is broken
  on this machine).
