# Confluence Configuration

Use this reference when a task needs to understand or repair the skill's Confluence setup.

## Config files

- `config/source-of-truth.local.json` is the machine-specific runtime config. It is generated
  by `install.ps1` and ignored by Git.
- `config/source-of-truth.example.json` is the tracked schema/example. Use it only to understand
  the expected shape when local config is missing.
- Local config always wins over example values.

## Required fields

- `confluence.siteUrl`: the Confluence wiki URL, such as
  `https://your-site.atlassian.net/wiki`.
- `confluence.cloudId`: required for generic Atlassian connector tools.
- `confluence.spaceKey`: the Confluence space where project pages live.
- `confluence.activeIndex.title`: title used to search for the active project index.
- `confluence.activeIndex.pageId`: required before creating project pages.
- `confluence.closedIndex.title`: title used to search for the closed project index.
- `confluence.closedIndex.pageId`: required before closing or moving project pages.
- `behavior.allowCreateMissingIndexes`: when `false`, ask before creating missing index pages.

## Fresh install setup

Run `install.ps1` from the repo root. For a complete non-interactive setup:

```powershell
.\install.ps1 -SiteUrl "https://your-site.atlassian.net/wiki" -CloudId "<cloud-id>" -SpaceKey "<SPACE>" -ActiveIndexPageId "<active-page-id>" -ClosedIndexPageId "<closed-page-id>"
```

If page IDs are unknown, run the installer with the known site/space values. On first use, search
for the configured Active/Closed titles in the configured space. Create missing index pages only
after explicit user approval or when local config sets `allowCreateMissingIndexes` to `true`.
For automation, pass `-NoPrompt` so the installer writes unresolved values without prompting.
