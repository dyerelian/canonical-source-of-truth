---
name: source-of-truth
description: Create, update, or close a project's canonical Confluence "source of truth" page for any project — GTD-tracked or ad-hoc. Use when the user asks to create/spin up a source of truth, a canonical page, a project page, or a single source of truth for a project or initiative; to update/refresh a project's Confluence page with a decision, milestone, status change, risk, or new update; or to close out a project's page when it's done. Actively gathers context from Granola, email/.msg files, Slack, Atlassian, SharePoint/local files, and the GTD workbook to draft or refresh the page.
---

# Source of Truth (Canonical Project Page)

Confluence is the **publicly-facing single source of truth** for every project. This skill
creates, updates, and closes those canonical pages for **any** project — whether or not it is
tracked in Dan's Getting Things Done (GTD) workbook. (Inspired by Naomi's "Canonical
Everything" — one authoritative page per project.)

This skill **owns** the canonical-page process. The GTD skills (`add-gtd-items`, `gtd`) and
`/close-day` reference this skill's `references/canonical-project-page.md` for the create /
update / close mechanics rather than keeping their own copy.

## When to use

- **Create** — a new project or initiative needs its canonical page (e.g. after a kickoff
  meeting). Also use to **reconcile** an existing ad-hoc page onto the convention.
- **Update** — an existing project changes: a status/owner/target change, a decision, a
  milestone, a new risk/open question, or a tied task worth surfacing publicly.
- **Close** — a project is done; move its page from the Active to the Closed index list.

## Workflow

### 1. Identify the project & check for an existing page

- Determine the project name and whether it already has a page:
  - Search space `PROD` by title (`confluence_get_page_by_title` / `confluence_search`).
  - If the project is in the GTD workbook, check its Projects-row `notes` (column **O**) for
    `Canonical page: <url>`.
- If a page exists → this is an **update** (or reconcile). If not → this is a **create**.

### 2. Gather context (active, read-only)

Pull real context before writing, per `references/context-sources.md`:
Granola meetings, email/`.msg` files (via `scripts/read_msg.py`), Slack, Atlassian
(Jira/Confluence), SharePoint/OneDrive/Downloads folders and local files, and the GTD
workbook. Keep searches narrow and recent; capture only page-relevant facts (outcome, owner,
status, target dates, key links, decisions, milestones, risks, updates). Always capture the
**SharePoint folder link** for Key Links.

### 3. Create / Update / Close the page

Follow `references/canonical-project-page.md`:
- **Create** — build the page from the storage-format body template, create it under
  `Active Projects` (space `PROD`, parent `5728960520`), then append its link to the Active
  Projects index list.
- **Update** — `confluence_get_page`, **merge** the change into Overview / Milestones /
  Decisions / Open Questions-Risks / Updates (never blank a section), `confluence_update_page`.
- **Close** — flip the page Status to Closed, move its link from the Active index list
  (`5728960520`) to the Closed index list (`5728763908`).

Apply the **page content rules** every time: spell out every acronym on first use with the
acronym in parentheses; attribute to the meeting/discussion, **never** name a capture/notes
tool; keep it public-facing and self-contained.

### 4. Link to the GTD workbook (only if tracked there)

If the project is tracked in the GTD workbook, link the two per
`references/canonical-project-page.md` → "Linking to the GTD workbook (optional)": store
`Canonical page: <url>` in the project's `notes` (column **O**) via the **`add-gtd-items`**
writer, and put the GTD Project ID in the page's Overview table. If the project is **not** in
the workbook, skip this — offer to add a project row only if Dan wants it. Never require the
workbook.

### 5. Report

Report the page title, URL, its index-list membership (Active/Closed), whether it was
created / updated / closed and what changed, and any GTD linkage made.

## References & scripts

- `references/canonical-project-page.md` — the authoritative create / update / close mechanics,
  Confluence coordinates, body template, and page content rules. **This is the file the GTD
  skills and `/close-day` point at.**
- `references/context-sources.md` — how to gather context from each source, read-only.
- `scripts/read_msg.py` — parse a saved Outlook `.msg` file (subject/from/to/date/attachments/
  body). Run via the full interpreter path `C:\Program Files\Python312\python.exe`.

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
