<#
.SYNOPSIS
    Install the source-of-truth skill into Claude Code and/or Codex via directory junctions.
.DESCRIPTION
    Creates live skill directory junctions pointing at this repo's root, so editing in either
    place touches the same files (no copying, no drift). Directory junctions need no admin
    rights or Developer Mode on Windows. Also creates a local, ignored Confluence configuration
    file unless -SkipConfigure is used. Restart Claude Code and start a new Codex session
    afterwards so the new skill is picked up.
#>
[CmdletBinding()]
param(
    [ValidateSet('Both', 'Claude', 'Codex')]
    [string]$Target = 'Both',

    [string]$ClaudeSkillsRoot = (Join-Path $env:USERPROFILE '.claude\skills'),
    [string]$CodexSkillsRoot = (Join-Path $env:USERPROFILE '.codex\skills'),

    [string]$SiteUrl,
    [string]$CloudId,
    [string]$SpaceKey,
    [string]$ActiveIndexPageId,
    [string]$ClosedIndexPageId,
    [string]$ActiveIndexTitle,
    [string]$ClosedIndexTitle,

    [switch]$AllowCreateMissingIndexes,
    [switch]$NoPrompt,
    [switch]$SkipConfigure,
    [switch]$Force
)

$ErrorActionPreference = 'Stop'
$repo = $PSScriptRoot
$configDir = Join-Path $repo 'config'
$exampleConfigPath = Join-Path $configDir 'source-of-truth.example.json'
$localConfigPath = Join-Path $configDir 'source-of-truth.local.json'
$activeIndexTitleWasProvided = $PSBoundParameters.ContainsKey('ActiveIndexTitle')
$closedIndexTitleWasProvided = $PSBoundParameters.ContainsKey('ClosedIndexTitle')

function Test-HasValue {
    param([AllowNull()][string]$Value)
    return -not [string]::IsNullOrWhiteSpace($Value)
}

function Get-NestedValue {
    param(
        [AllowNull()]$Object,
        [Parameter(Mandatory = $true)][string[]]$Path,
        [AllowNull()]$Default
    )

    $current = $Object
    foreach ($segment in $Path) {
        if ($null -eq $current) {
            return $Default
        }
        if ($current.PSObject.Properties.Name -notcontains $segment) {
            return $Default
        }
        $current = $current.$segment
    }
    if ($null -eq $current) {
        return $Default
    }
    return $current
}

function Get-ConfigString {
    param(
        [AllowNull()][string]$Provided,
        [AllowNull()][string]$Existing,
        [AllowNull()][string]$Default,
        [Parameter(Mandatory = $true)][string]$PromptLabel,
        [Parameter(Mandatory = $true)][bool]$CanPrompt
    )

    if (Test-HasValue $Provided) {
        return $Provided
    }
    if (Test-HasValue $Existing) {
        return $Existing
    }

    $value = $Default
    if ($CanPrompt) {
        $suffix = ''
        if (Test-HasValue $Default) {
            $suffix = " [$Default]"
        }
        $answer = Read-Host "$PromptLabel$suffix"
        if (Test-HasValue $answer) {
            $value = $answer
        }
    }

    if ($null -eq $value) {
        return ''
    }
    return [string]$value
}

function Write-LocalConfig {
    New-Item -ItemType Directory -Force -Path $configDir | Out-Null

    $exampleConfig = $null
    if (Test-Path -LiteralPath $exampleConfigPath) {
        $exampleConfig = Get-Content -LiteralPath $exampleConfigPath -Raw -Encoding UTF8 | ConvertFrom-Json
    }

    $existingConfig = $null
    if (Test-Path -LiteralPath $localConfigPath) {
        $existingConfig = Get-Content -LiteralPath $localConfigPath -Raw -Encoding UTF8 | ConvertFrom-Json
    }

    $canPrompt = (-not $NoPrompt) -and (-not [Console]::IsInputRedirected)
    $providedActiveTitle = if ($activeIndexTitleWasProvided) { $ActiveIndexTitle } else { $null }
    $providedClosedTitle = if ($closedIndexTitleWasProvided) { $ClosedIndexTitle } else { $null }

    $siteUrlValue = Get-ConfigString -Provided $SiteUrl `
        -Existing (Get-NestedValue $existingConfig @('confluence', 'siteUrl') '') `
        -Default (Get-NestedValue $exampleConfig @('confluence', 'siteUrl') '') `
        -PromptLabel 'Confluence site URL' -CanPrompt $canPrompt
    $cloudIdValue = Get-ConfigString -Provided $CloudId `
        -Existing (Get-NestedValue $existingConfig @('confluence', 'cloudId') '') `
        -Default (Get-NestedValue $exampleConfig @('confluence', 'cloudId') '') `
        -PromptLabel 'Confluence cloud ID' -CanPrompt $canPrompt
    $spaceKeyValue = Get-ConfigString -Provided $SpaceKey `
        -Existing (Get-NestedValue $existingConfig @('confluence', 'spaceKey') '') `
        -Default (Get-NestedValue $exampleConfig @('confluence', 'spaceKey') '') `
        -PromptLabel 'Confluence space key' -CanPrompt $canPrompt
    $activeTitleValue = Get-ConfigString -Provided $providedActiveTitle `
        -Existing (Get-NestedValue $existingConfig @('confluence', 'activeIndex', 'title') '') `
        -Default (Get-NestedValue $exampleConfig @('confluence', 'activeIndex', 'title') 'Active Projects') `
        -PromptLabel 'Active projects index title' -CanPrompt $canPrompt
    $closedTitleValue = Get-ConfigString -Provided $providedClosedTitle `
        -Existing (Get-NestedValue $existingConfig @('confluence', 'closedIndex', 'title') '') `
        -Default (Get-NestedValue $exampleConfig @('confluence', 'closedIndex', 'title') 'Closed Projects') `
        -PromptLabel 'Closed projects index title' -CanPrompt $canPrompt
    $activePageIdValue = Get-ConfigString -Provided $ActiveIndexPageId `
        -Existing (Get-NestedValue $existingConfig @('confluence', 'activeIndex', 'pageId') '') `
        -Default (Get-NestedValue $exampleConfig @('confluence', 'activeIndex', 'pageId') '') `
        -PromptLabel 'Active projects index page ID' -CanPrompt $canPrompt
    $closedPageIdValue = Get-ConfigString -Provided $ClosedIndexPageId `
        -Existing (Get-NestedValue $existingConfig @('confluence', 'closedIndex', 'pageId') '') `
        -Default (Get-NestedValue $exampleConfig @('confluence', 'closedIndex', 'pageId') '') `
        -PromptLabel 'Closed projects index page ID' -CanPrompt $canPrompt

    $allowCreate = [bool](Get-NestedValue $existingConfig @('behavior', 'allowCreateMissingIndexes') $false)
    if ($AllowCreateMissingIndexes.IsPresent) {
        $allowCreate = $true
    }

    $config = [ordered]@{
        schemaVersion = 1
        confluence = [ordered]@{
            siteUrl = $siteUrlValue
            cloudId = $cloudIdValue
            spaceKey = $spaceKeyValue
            activeIndex = [ordered]@{
                title = $activeTitleValue
                pageId = $activePageIdValue
            }
            closedIndex = [ordered]@{
                title = $closedTitleValue
                pageId = $closedPageIdValue
            }
        }
        behavior = [ordered]@{
            allowCreateMissingIndexes = $allowCreate
        }
    }

    $config | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $localConfigPath -Encoding UTF8
    Write-Host "Configured local Confluence settings: $localConfigPath"

    $missing = @()
    if (-not (Test-HasValue $siteUrlValue)) { $missing += 'SiteUrl' }
    if (-not (Test-HasValue $cloudIdValue)) { $missing += 'CloudId' }
    if (-not (Test-HasValue $spaceKeyValue)) { $missing += 'SpaceKey' }
    if (-not (Test-HasValue $activePageIdValue)) { $missing += 'ActiveIndexPageId' }
    if (-not (Test-HasValue $closedPageIdValue)) { $missing += 'ClosedIndexPageId' }

    if ($missing.Count -gt 0) {
        Write-Host ""
        Write-Host "Configuration still needs: $($missing -join ', ')"
        Write-Host 'Rerun with:'
        Write-Host '.\install.ps1 -SiteUrl "<https://your-site.atlassian.net/wiki>" -CloudId "<cloud-id>" -SpaceKey "<SPACE>" -ActiveIndexPageId "<active-page-id>" -ClosedIndexPageId "<closed-page-id>"'
    }
}

function Install-SkillJunction {
    param(
        [Parameter(Mandatory = $true)][string]$SkillsRoot,
        [Parameter(Mandatory = $true)][string]$Label
    )

    $live = Join-Path $SkillsRoot 'source-of-truth'
    New-Item -ItemType Directory -Force -Path $SkillsRoot | Out-Null

    if (Test-Path -LiteralPath $live) {
        $item = Get-Item -LiteralPath $live -Force
        $isJunction = $item.Attributes.ToString().Contains('ReparsePoint')
        if (-not $isJunction -and -not $Force) {
            throw "$Label target exists and is not a junction: $live. Re-run with -Force to replace it."
        }
        Remove-Item -LiteralPath $live -Recurse -Force
    }

    New-Item -ItemType Junction -Path $live -Target $repo | Out-Null
    Write-Host "Junctioned ${Label}: $live -> $repo"
}

if ($Target -in @('Both', 'Claude')) {
    Install-SkillJunction -SkillsRoot $ClaudeSkillsRoot -Label 'Claude'
}

if ($Target -in @('Both', 'Codex')) {
    Install-SkillJunction -SkillsRoot $CodexSkillsRoot -Label 'Codex'
}

if (-not $SkipConfigure) {
    Write-LocalConfig
}

Write-Host ""
Write-Host "Done. Restart Claude Code and start a new Codex turn/session to load the skill."
