<#
.SYNOPSIS
    Install the source-of-truth Claude skill into ~/.claude/skills via a directory junction.
.DESCRIPTION
    Creates (or recreates) a directory junction ~/.claude/skills/source-of-truth pointing at
    this repo's root, so editing in either place touches the same files (no copying, no drift).
    Directory junctions need no admin rights or Developer Mode on Windows.
    Restart Claude Code afterwards so the new skill is picked up.
#>
[CmdletBinding()]
param(
    [string]$SkillsRoot = (Join-Path $env:USERPROFILE '.claude\skills')
)

$ErrorActionPreference = 'Stop'
$repo = $PSScriptRoot
$live = Join-Path $SkillsRoot 'source-of-truth'

New-Item -ItemType Directory -Force -Path $SkillsRoot | Out-Null
if (Test-Path $live) { Remove-Item $live -Recurse -Force }
New-Item -ItemType Junction -Path $live -Target $repo | Out-Null
Write-Host "Junctioned: $live -> $repo"

Write-Host ""
Write-Host "Done. Restart Claude Code (or start a new session) to load the skill."
