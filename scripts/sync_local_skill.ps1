[CmdletBinding(SupportsShouldProcess)]
param(
    [string]$InstallDir = (Join-Path $env:USERPROFILE '.codex\skills\mathematical-modeling-competition-copilot'),
    [switch]$Verify
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

$files = git -c "safe.directory=$repoRoot" -C $repoRoot ls-files
if ($LASTEXITCODE -ne 0 -or -not $files) {
    throw 'Unable to enumerate tracked repository files.'
}

$payloadFiles = @(
    $files | Where-Object {
        $_ -ne '.gitignore' -and
        -not $_.StartsWith('.github/') -and
        -not $_.StartsWith('docs/')
    }
)

if ($Verify) {
    $missing = @()
    $mismatched = @()
    foreach ($relative in $payloadFiles) {
        $source = Join-Path $repoRoot $relative
        $destination = Join-Path $resolvedTarget $relative
        if (-not (Test-Path -LiteralPath $destination -PathType Leaf)) {
            $missing += $relative
            continue
        }
        $sourceHash = (Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash
        $destinationHash = (Get-FileHash -LiteralPath $destination -Algorithm SHA256).Hash
        if ($sourceHash -ne $destinationHash) {
            $mismatched += $relative
        }
    }

    $expected = @{}
    foreach ($relative in $payloadFiles) {
        $expected[$relative.Replace('\', '/')] = $true
    }
    $installed = @()
    if (Test-Path -LiteralPath $resolvedTarget -PathType Container) {
        $installed = @(
            Get-ChildItem -LiteralPath $resolvedTarget -File -Recurse |
                ForEach-Object {
                    $_.FullName.Substring($resolvedTarget.Length + 1) -replace '\\', '/'
                }
        )
    }
    $extras = @($installed | Where-Object { -not $expected.ContainsKey($_) })

    Write-Output "Verified payload=$($payloadFiles.Count) missing=$($missing.Count) mismatched=$($mismatched.Count) extra=$($extras.Count)"
    if ($missing.Count -gt 0) {
        Write-Output 'Missing payload files:'
        $missing | ForEach-Object { Write-Output "- $_" }
    }
    if ($mismatched.Count -gt 0) {
        Write-Output 'Hash-mismatched payload files:'
        $mismatched | ForEach-Object { Write-Output "- $_" }
    }
    if ($extras.Count -gt 0) {
        Write-Output 'Extra installed files (left untouched):'
        $extras | ForEach-Object { Write-Output "- $_" }
    }
    if ($missing.Count -gt 0 -or $mismatched.Count -gt 0) {
        exit 1
    }
    return
}

$copied = 0
foreach ($relative in $payloadFiles) {
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
