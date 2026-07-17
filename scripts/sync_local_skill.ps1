[CmdletBinding(SupportsShouldProcess)]
param(
    [string]$InstallDir = (Join-Path $env:USERPROFILE '.codex\skills\mathematical-modeling-competition-copilot')
)

$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
$expectedLeaf = 'mathematical-modeling-competition-copilot'
$resolvedTarget = [System.IO.Path]::GetFullPath($InstallDir)

if ((Split-Path -Leaf $resolvedTarget) -ne $expectedLeaf) {
    throw "InstallDir must end with '$expectedLeaf': $resolvedTarget"
}
if ($resolvedTarget -eq $repoRoot) {
    throw 'InstallDir must differ from the repository root.'
}

$files = git -C $repoRoot ls-files
if ($LASTEXITCODE -ne 0 -or -not $files) {
    throw 'Unable to enumerate tracked repository files.'
}

$copied = 0
foreach ($relative in $files) {
    if ($relative -eq '.gitignore' -or $relative.StartsWith('.github/') -or $relative.StartsWith('docs/')) {
        continue
    }
    $source = Join-Path $repoRoot $relative
    $destination = Join-Path $resolvedTarget $relative
    if ($PSCmdlet.ShouldProcess($destination, "Copy from $source")) {
        New-Item -ItemType Directory -Force -Path (Split-Path -Parent $destination) | Out-Null
        Copy-Item -LiteralPath $source -Destination $destination -Force
        $sourceHash = (Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash
        $destinationHash = (Get-FileHash -LiteralPath $destination -Algorithm SHA256).Hash
        if ($sourceHash -ne $destinationHash) {
            throw "Hash mismatch after copying: $relative"
        }
        $copied += 1
    }
}

Write-Output "Synchronized $copied tracked skill files to $resolvedTarget"
