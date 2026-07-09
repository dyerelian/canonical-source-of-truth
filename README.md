# Canonical Source of Truth (`source-of-truth` skill)

A [Claude Code](https://claude.ai/code) **skill** that creates, updates, and closes a
project's **canonical Confluence "source of truth" page** — for **any** project, whether or
not it is tracked in Dan's Getting Things Done (GTD) workbook.

Confluence is the publicly-facing single source of truth per project (inspired by Naomi's
"Canonical Everything" — one authoritative page each). This skill owns that process; the GTD
skills (`add-gtd-items`, `gtd`) and the `close-day` skill reference this repo's
`references/canonical-project-page.md` for the create / update / close mechanics rather than
keeping their own copy.

## What it does

- **Create** a canonical page for a new project/initiative (or reconcile an ad-hoc page onto
  the convention), placed under `Active Projects` in the `PROD` Confluence space and linked
  into the Active Projects index list.
- **Update** an existing page on any material change — merge into Overview / Milestones /
  Decisions / Open Questions-Risks / Updates (never overwrite).
- **Close** a project's page — flip Status to Closed and move its link from the Active to the
  Closed index list.
- **Gather context** first from Granola, email/`.msg` files, Slack, Atlassian, SharePoint /
  local files, and the GTD workbook (all read-only).

## Repository contents

| Path | Purpose |
|------|---------|
| `SKILL.md` | The skill definition and workflow (loaded by Claude Code). |
| `references/canonical-project-page.md` | **Authoritative** create/update/close mechanics, Confluence coordinates, storage-format body template, and page content rules. Referenced by the GTD and close-day skills. |
| `references/context-sources.md` | How to gather context from each source, read-only. |
| `scripts/read_msg.py` | Parse a saved Outlook `.msg` file (subject/from/to/date/attachments/body). Requires `extract_msg`. |
| `install.ps1` | Creates the `~/.claude/skills/source-of-truth` junction into this repo. |

## Confluence coordinates

Space `PROD`; `Active Projects` index page ID `5728960520`; `Closed Projects` index page ID
`5728763908`. Per-project child pages live under Active Projects; a project's active/closed
state is tracked by which index **list** its link sits in (the Confluence MCP tools cannot
re-parent pages).

## Consumers (cross-repo dependency)

Two sibling skills reference this repo by absolute path
(`C:\Users\E724101\.claude\skills\source-of-truth\references\canonical-project-page.md`):

- **`add-gtd-items`** (repo `AAA-claude-skill-GTD`) — creates/updates a project's page when a
  project row is added or changes.
- **`close-day`** (repo `Daily-Close-Skill`) — refreshes/moves canonical pages during the
  end-of-day close, and flags active projects missing or with a stale page.

## Sync model (junction)

On the author's machine this repo is the **single source of truth**, and the live skill under
`~/.claude/skills/source-of-truth` is a **directory junction** pointing at the repo root — so
editing in either place touches the same files, with no copying and no drift.

```
~/.claude/skills/source-of-truth  ──junction──▶  <repo root>
```

Workflow: edit wherever's convenient, then commit/push from the repo:

```powershell
cd ~/repos/Source-of-Truth-Skill
git add -A; git commit -m "..."; git push
```

(Re)create the junction on this machine — or on a fresh clone — by running `install.ps1`, or:

```powershell
$live = Join-Path $env:USERPROFILE '.claude\skills\source-of-truth'
$repo = $PSScriptRoot   # the cloned repo's root
if (Test-Path $live) { Remove-Item $live -Recurse -Force }
New-Item -ItemType Junction -Path $live -Target $repo | Out-Null
```

Directory junctions need **no admin rights or Developer Mode** on Windows and are transparent
to Claude Code. They are local to a machine — on a new machine, clone then run `install.ps1`.

> **Note on paths:** `SKILL.md` and the references contain absolute Windows paths specific to
> the author's machine (skills directory, Python interpreter, workbook location). Adjust these
> for your environment before use.
