# Canonical Source of Truth (`source-of-truth` skill)

A Claude Code and Codex **skill** that creates, updates, and closes a
project's **canonical Confluence "source of truth" page** — for **any** project, whether or
not it is tracked in a Getting Things Done (GTD) workbook.

Confluence is the publicly-facing single source of truth per project (inspired by Naomi's
"Canonical Everything" — one authoritative page each). This skill owns that process; the GTD
skills (`add-gtd-items`, `gtd`) and the `close-day` skill reference this repo's
`references/canonical-project-page.md` for the create / update / close mechanics rather than
keeping their own copy.

## What it does

- **Create** a canonical page for a new project/initiative (or reconcile an ad-hoc page onto
  the convention), placed under the configured `Active Projects` Confluence page and linked
  into the Active Projects index list.
- **Update** an existing page on any material change — merge into Overview / Key Links /
  Skills / Milestones / Decisions / Open Questions-Risks / Updates (never overwrite).
- **Close** a project's page — flip Status to Closed and move its link from the Active to the
  Closed index list.
- **Gather context** first from Granola, email/`.msg` files, Slack, Atlassian, SharePoint /
  local files, and the GTD workbook (all read-only).
- **Document project-specific skills** when useful, using a compact optional Skills section
  after Key Links and before Milestones.

## Repository contents

| Path | Purpose |
|------|---------|
| `SKILL.md` | The skill definition and workflow (loaded by Claude Code and Codex). |
| `agents/openai.yaml` | Codex UI metadata. |
| `config/source-of-truth.example.json` | Tracked example schema for local Confluence setup. |
| `references/canonical-project-page.md` | **Authoritative** create/update/close mechanics, Confluence page workflow, optional project-specific Skills section, storage-format body template, and page content rules. Referenced by the GTD and close-day skills. |
| `references/confluence-instance.md` | Configuration resolution and fresh-install setup rules. |
| `references/context-sources.md` | How to gather context from each source, read-only. |
| `scripts/read_msg.py` | Parse a saved Outlook `.msg` file (subject/from/to/date/attachments/body). Requires `extract_msg`. |
| `install.ps1` | Creates live skill junctions into this repo for Claude, Codex, or both. |

## Fresh install

Clone the repo, then run the installer from the repo root:

```powershell
.\install.ps1 -SiteUrl "https://your-site.atlassian.net/wiki" -CloudId "<cloud-id>" -SpaceKey "<SPACE>" -ActiveIndexPageId "<active-page-id>" -ClosedIndexPageId "<closed-page-id>"
```

The installer creates Claude/Codex skill junctions and writes
`config/source-of-truth.local.json`, which is ignored by Git. If Active/Closed page IDs are not
known yet, omit them; the skill will search by the configured titles and ask before creating
missing index pages. For automation, add `-NoPrompt` to write unresolved values without
interactive prompts.

Per-project child pages live under Active Projects; a project's active/closed state is tracked
by which index **list** its link sits in (the Confluence MCP tools may not be able to re-parent
pages).

## Consumers (cross-repo dependency)

Sibling GTD/close-day skills can reference this repo's
`references/canonical-project-page.md` instead of keeping their own copy:

- **`add-gtd-items`** (repo `AAA-claude-skill-GTD`) — creates/updates a project's page when a
  project row is added or changes.
- **`close-day`** (repo `Daily-Close-Skill`) — refreshes/moves canonical pages during the
  end-of-day close, and flags active projects missing or with a stale page.

## Sync model (junction)

This repo is the **single source of truth**, and the live skill under
`~/.claude/skills/source-of-truth` and/or `~/.codex/skills/source-of-truth` is a **directory
junction** pointing at the repo root — so editing in either place touches the same files, with
no copying and no drift.

```
~/.claude/skills/source-of-truth  ──junction──▶  <repo root>
~/.codex/skills/source-of-truth   ──junction──▶  <repo root>
```

Workflow: edit wherever's convenient, then commit/push from the repo:

```powershell
cd ~/repos/Source-of-Truth-Skill
git add -A; git commit -m "..."; git push
```

(Re)create the junctions on this machine — or on a fresh clone — by running:

```powershell
.\install.ps1
```

Directory junctions need **no admin rights or Developer Mode** on Windows and are transparent
to Claude Code and Codex. They are local to a machine — on a new machine, clone then run
`install.ps1`.

> **Note on paths:** runtime Confluence values belong in `config/source-of-truth.local.json`,
> not tracked Markdown files.
