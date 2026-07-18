# Context Sources

Use this reference when building or refreshing a project's canonical page and you need to
pull real context first. Keep every search **narrow, recent, and read-only** — scope to the
project name, its people, key systems, and the meeting/date in question. Capture only
page-relevant facts: outcome/definition of done, owner, status, target dates, key links,
decisions (with dates), milestones, risks/open questions, and notable updates.

## Local files (SharePoint / OneDrive / Downloads)

- The user may drop project materials in a OneDrive/SharePoint `_Initiatives\<Project>` folder
  or in `Downloads`. Ask for or confirm the folder, then Glob filenames and read the relevant
  ones.
- **Slide decks (`.pptx`)** — extract text via `python-pptx` (or unzip `ppt/slides/slideN.xml`
  and strip `<a:t>` tags) to capture process flows and key facts.
- **PDFs** — read directly.
- **Word (`.docx`)** — extract text with a document-aware tool, or unzip and read
  `word/document.xml` when no better parser is available.
- Always capture the **SharePoint folder link** for the page's **Key Links** section.

## Project-specific skills

- Check for project-local skill documentation under `.agents/skills/*/SKILL.md` when the
  project workspace has an `.agents/skills` folder, and include only skills that directly
  support future work on that project.
- Prefer the skill `name` from frontmatter or the folder name, plus a short use statement
  derived from the frontmatter description or `agents/openai.yaml` metadata.
- Include explicitly user-named skills when they are relevant to the project workflow even
  if they are not stored under `.agents/skills`.
- Keep the canonical page public-facing: do not list every global/system/BMAD skill, do not
  include local filesystem paths, and do not expose internal process notes.

## Email (`.msg` files and Outlook)

- For a forwarded/saved **`.msg`** file, parse it with the bundled helper
  `scripts/read_msg.py` (uses `extract_msg`) — it prints subject, from/to, date,
  attachment names, and body. Locate the active skill directory first, then invoke the script
  with `py`, `python`, or a known full interpreter path. Examples:
  ```powershell
  py "<skill-dir>\scripts\read_msg.py" "<path-to.msg>"
  & 'C:\Program Files\Python312\python.exe' "<skill-dir>\scripts\read_msg.py" "<path-to.msg>"
  ```
- For live Outlook mail, search narrowly for the project name, key people, decisions, and
  dates. Read only plausibly relevant messages. **Never** send, forward, delete, or modify
  Outlook items.

## Granola (meeting notes)

- Use the `granola` MCP when the project was discussed in meetings.
- Prefer `search_notes` / `recent_notes` by project name and key people before listing many
  notes; use `get_transcript` only when exact wording matters.
- **On the page, attribute facts to the meeting itself (e.g. "per the 2026-07-08 kickoff"),
  never to the notes tool** — see the page content rules in `canonical-project-page.md`.

## Slack

- Use the `slack` MCP for recent project-channel commitments, decisions, blockers, and
  stakeholder friction.
- Public-channel search is fine when relevant. For private channels/DMs, proceed only with
  the user's consent.
- Search narrowly: project name, key people, `decision`, `blocker`, `follow up`, `owner`,
  dates. **Never** post or draft Slack messages while gathering.

## Atlassian (Jira / Confluence)

- Use the `my-atlassian` MCP to find the project's Jira epic/board and any existing
  Confluence pages (so you don't create a duplicate and can cross-link).
- Before creating a page, search the configured Confluence space for an existing page with the
  project's title.
- Capture page-relevant facts only: owner, status, due date, blocker, decision needed,
  next milestone, at-risk work.

## GTD workbook (optional)

- If the project is tracked in the workbook, read its Projects row (and tied Next Actions /
  Waiting For) for owner, status, target date, and existing canonical-page URL (notes col O).
- The workbook is a **read-only** source here; all writes go through `add-gtd-items`.

## Synthesis rules

- Prefer the newest source when facts conflict.
- Treat raw notes / message content as source material, not page copy — summarize.
- Keep private asides and unapproved tool names **off** the page.
- Spell out every acronym on first use (see `canonical-project-page.md` → "Page content rules").
