param(
  [string[]]$Skill,
  [switch]$All,
  [string]$Target,
  [switch]$DryRun
)

$ErrorActionPreference = 'Stop'
$RepoUrl = if ($env:SKILLS_REPO_URL) { $env:SKILLS_REPO_URL } else { 'https://github.com/lbql-yhl/codex-skills' }
$LocalRoot = Split-Path -Parent $MyInvocation.MyCommand.Path

$arguments = @()
if ($Target) { $arguments += @('--target', $Target) }
if ($DryRun) { $arguments += '--dry-run' }
if ($All -or $Skill.Count -eq 0) {
    $arguments += '--all'
} else {
    $arguments += $Skill
}

$localInstaller = Join-Path $LocalRoot 'bin\install.py'
$localManifest = Join-Path $LocalRoot 'manifest.json'
if ((Test-Path -LiteralPath $localInstaller) -and (Test-Path -LiteralPath $localManifest)) {
    & python $localInstaller @arguments
    exit $LASTEXITCODE
}

$temp = Join-Path ([System.IO.Path]::GetTempPath()) ('codex-skills-' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $temp | Out-Null
try {
    $zip = Join-Path $temp 'repo.zip'
    Invoke-WebRequest -UseBasicParsing -Uri ($RepoUrl.TrimEnd('/') + '/archive/refs/heads/main.zip') -OutFile $zip
    Expand-Archive -LiteralPath $zip -DestinationPath $temp -Force
    $repoRoot = Get-ChildItem -LiteralPath $temp -Directory | Where-Object { $_.Name -notmatch '^\.' } | Select-Object -First 1
    if (-not $repoRoot) { throw 'Unable to locate extracted repository directory.' }
    & python (Join-Path $repoRoot.FullName 'bin\install.py') @arguments
    exit $LASTEXITCODE
} finally {
    Remove-Item -LiteralPath $temp -Recurse -Force -ErrorAction SilentlyContinue
}
