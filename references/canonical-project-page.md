# Canonical Project Page (Confluence source of truth)

Confluence is the **publicly-facing source of truth** for every project. When a
**new project** kicks off, create a canonical Confluence page for it; whenever that
project later **changes**, mirror the change back onto its page so the page always
reflects current reality.
(Inspired by Naomi's "Canonical Everything" — one authoritative page per project.)

- **Create a page** → new projects / initiatives (see "Creating a page for a new project").
- **Update a page** → whenever a project with a canonical page changes: a status /
  owner / target / scope change, a decision, a milestone, a new risk or open question,
  or a tied task / waiting-for item worth surfacing publicly (see "Updating an existing page").
- **Move a page** (Active ↔ Closed) → on project completion (see "Completing a project").

All text written to a page follows the writing rules in "Page content rules" below.

> **GTD linkage is optional.** This process works for **any** project, whether or not it
> is tracked in a Getting Things Done (GTD) workbook. If the project *is* in the workbook, also link the two
> (see "Linking to the GTD workbook (optional)"). If it is not, skip every workbook step —
> the Confluence page stands on its own.

## Runtime and instance configuration

Before any Confluence write, read `config/source-of-truth.local.json`. If it is missing, read
`config/source-of-truth.example.json` for the expected shape and ask the user to run
`install.ps1` with their Confluence values.

- Use the configured site, cloud ID, space key, Active Projects index page ID, and Closed
  Projects index page ID for the current user's Confluence instance.
- If the Active/Closed IDs are marked unresolved, search by exact title in the configured
  space. If still missing, ask the user where to place the indexes or create those index pages only
  after an explicit user request or when `behavior.allowCreateMissingIndexes` is `true`.
- In Codex, prefer the `mcp__my_atlassian` tools when they exist. In Claude Code, use the
  equivalent `my-atlassian`/Confluence MCP tools. With the generic Atlassian connector, pass the
  configured `cloudId` value and request `contentFormat: "html"` for page bodies.

## Where pages go

- **Space key:** read from local config.
- **Active index page:** `Active Projects`, using the configured content ID.
- **Closed index page:** `Closed Projects`, using the configured content ID.

Each project gets its own child page under `Active Projects`. The two index pages
(`Active Projects` / `Closed Projects`) are **link lists** that are the canonical
navigation — a project's active/closed state is reflected by which list its link
lives in. (The Confluence MCP tools cannot re-parent a page in the tree, so the
list membership — not the page's tree parent — is the source of truth for state.)

## Creating a page for a new project

Use a connected Confluence create-page tool:

- `space_key` / `spaceId`: the configured space key from local config
- `parent_id` / `parentId`: the configured Active Projects page ID
- `title`: the project name (must be unique in the space — if a page with that
  title already exists, reuse/link it instead of creating a duplicate)
- `body_html`: the storage-format template below (fill in known values; leave
  placeholders for what isn't known yet)

**Standing rule: every new project gets a canonical
Confluence page — create it automatically as part of adding the project. Do not
ask first.** Always include the project's **SharePoint folder** (and any other
working hub: Jira board, Slack channel, key docs) under **Key Links** — link the
SharePoint location explicitly in the page body.

Then **add the new page to the Active Projects index list**:
1. `confluence_get_page` on the configured Active Projects page ID to read its current
   `body_storage_html`.
2. Append a list item linking to the new page.
3. `confluence_update_page` on the configured Active Projects page ID with the updated body
   (version
   auto-bumps).

### Body template (Confluence storage format)

```html
<h2>Overview</h2>
<p><em>One-paragraph statement of the outcome / definition of done.</em></p>
<table>
  <tbody>
    <tr><th>Status</th><td>In Progress</td></tr>
    <tr><th>Owner</th><td></td></tr>
    <tr><th>Area</th><td></td></tr>
    <tr><th>Target date</th><td></td></tr>
    <tr><th>GTD Project ID</th><td></td></tr>
  </tbody>
</table>
<h2>Key Links</h2>
<ul>
  <li>SharePoint folder: </li>
  <li>Jira epic / board: </li>
  <li>Slack channel: </li>
  <li>Related docs: </li>
</ul>
<h2>Milestones</h2>
<ul>
  <li></li>
</ul>
<h2>Decisions</h2>
<p><em>Log key decisions here with dates so the page stays canonical.</em></p>
<ul>
  <li></li>
</ul>
<h2>Open Questions / Risks</h2>
<ul>
  <li></li>
</ul>
<h2>Updates</h2>
<p><em>Reverse-chronological log of notable updates.</em></p>
<ul>
  <li></li>
</ul>
```

Leave the `GTD Project ID` cell blank when the project is not tracked in the workbook.

### After creating

1. Capture the returned page URL.
2. **If the project is in the GTD workbook**, link the two (see "Linking to the GTD
   workbook (optional)"). If it is not, skip this.
3. Report the page title, URL, and (if applicable) the GTD project ID/row back to the user.

## Updating an existing page

Because the page is the public source of truth, an existing project's page must not
drift from reality. Whenever the project changes — via an `add-gtd-items` run, a
`/close-day` sweep, or an ad-hoc update — mirror the change onto the page in the
**same run**; do not wait to be asked.

**When to update** — any of:

- A status / owner / target-date / scope change.
- A decision, a milestone reached, or a new risk / open question.
- A new task / waiting-for / commitment tied to the project that reflects a real change
  in state worth surfacing publicly.

Skip pure capture noise (e.g. an unprocessed inbox thought that isn't yet a decision or action).

**How to find the page:**

- If the project is in the GTD workbook, read the canonical URL from its `notes`
  (column **O**, stored as `Canonical page: <url>`) and take the numeric page ID from the URL.
- Otherwise, locate it by title with `confluence_search` /
  `confluence_get_page_by_title` in the configured space.
- If the project has no page yet, create one via "Creating a page for a new project" first.

**How to update — merge, never overwrite:**

1. `confluence_get_page` on that ID to read the current `body_storage_html` and version.
2. **Merge into the existing body, preserving everything already there:**
   - **Overview table** — update only the cells that changed (Status, Owner, Target
     date, Next milestone).
   - **Milestones** — mark items done / add new ones.
   - **Decisions** — append a dated bullet per decision (never remove past decisions).
   - **Open Questions / Risks** — add new ones; mark resolved ones resolved.
   - **Updates** — **prepend** a dated bullet (reverse-chronological) summarizing what
     changed this run.
3. `confluence_update_page` with the merged body (the version auto-bumps).
4. Report the page URL and a one-line note of what changed on it.

Never blank or replace a section — append/merge only. Date every Decisions and Updates
entry (ISO, from `currentDate`). Keep all text public-facing per "Page content rules."

## Page content rules

Everything written to a canonical page is publicly facing, so:

- **Spell out every acronym on first use, with the acronym in parentheses immediately
  after the written-out term** — e.g. "Auto Club Enterprises (ACE)", "Revenue Cloud
  (RC)", "Automobile Club of Southern California (ACSC)". After that first write-out on
  a page the bare acronym is fine. Apply this to market codes and internal shorthand too.
- **Attribute to the meeting or discussion itself, never to any capture / notes tool.**
  Cite the event — e.g. "per the 2026-07-07 Scott 1:1" — not the tool the notes came
  from. Do not name unapproved or internal-only tooling anywhere on the page.
- Keep the tone professional and self-contained: no private asides, no raw transcript
  dumps, and no links to tools that are not approved for the page's audience.

## Completing a project

When a project's status is set to a done/complete value (e.g. via an
`add-gtd-items` project update, during `/close-day`, or an ad-hoc close), move its
canonical page to the closed list:

1. **Flip the page Status** to `Closed` (or `Complete`): `confluence_get_page` on
   the project page, edit the Status cell in the Overview table, `confluence_update_page`.
2. **Remove the link from Active Projects**: get body, drop the
   project's list item, update.
3. **Add the link to Closed Projects**: get body, append the
   project's list item, update.

Note: the page's tree parent stays under Active Projects (the tools can't
re-parent); the index-list membership is what marks it closed. The user can drag it in
the Confluence tree manually if they want the hierarchy to match.

## Linking to the GTD workbook (optional)

Only when the project is tracked in a Getting Things Done (GTD) workbook — otherwise skip this section entirely.

- **Store the page URL in the project row.** Put the URL into the project's `notes`
  field (workbook column **O**), prefixed `Canonical page: <url>`, so it sits alongside
  any other project notes. Recommended order: create the page first, then write the
  project row with the URL already in `notes` (one write, no follow-up update). If the
  project row was already written, re-run the writer with the project's `id` to update
  its `notes`.
- **Writing is delegated to `add-gtd-items`.** Use that skill's
  `scripts/Add-GtdItems.ps1` writer and `references/workbook-schema.md` — do not
  hand-write the `.xlsx`. If there is no matching project row yet, offer to add one via
  `add-gtd-items`.
- **Put the GTD Project ID in the page's Overview table** (`GTD Project ID` cell) so the
  link is visible from the page too.
