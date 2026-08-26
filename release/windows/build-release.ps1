[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [string]$PayloadDirectory,

    [Parameter(Mandatory)]
    [string]$OutputDirectory,

    [Parameter(Mandatory)]
    [string]$GitTag,

    [Parameter(Mandatory)]
    [string]$IsccPath
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$PayloadDirectory = (Resolve-Path -LiteralPath $PayloadDirectory).Path
$IsccPath = (Resolve-Path -LiteralPath $IsccPath).Path
$scriptPath = Join-Path $PSScriptRoot 'NewzDeck.iss'
$versionPath = Join-Path $PayloadDirectory 'VERSION.txt'

foreach ($requiredFile in @('VERSION.txt', 'NewzDeck.exe', 'NewzDeck.ico')) {
    $requiredPath = Join-Path $PayloadDirectory $requiredFile
    if (-not (Test-Path -LiteralPath $requiredPath -PathType Leaf)) {
        throw "Release payload is missing required root file '$requiredFile'."
    }
}

$version = (Get-Content -LiteralPath $versionPath -Raw).Trim()
if ($version -notmatch '^\d+\.\d+\.\d+$') {
    throw "Payload version '$version' is invalid. VERSION.txt must contain X.Y.Z."
}

$expectedTag = "v$version"
if ($GitTag -cne $expectedTag) {
    throw "Release tag '$GitTag' does not match payload version '$version'. Expected '$expectedTag'."
}

$iconBytes = [System.IO.File]::ReadAllBytes((Join-Path $PayloadDirectory 'NewzDeck.ico'))
if ($iconBytes.Length -lt 6 -or $iconBytes[0] -ne 0 -or $iconBytes[1] -ne 0 -or $iconBytes[2] -ne 1 -or $iconBytes[3] -ne 0) {
    throw 'NewzDeck.ico is not a valid Windows icon file. Use the real NewzDeck application icon.'
}

if (Test-Path -LiteralPath $OutputDirectory) {
    if (@(Get-ChildItem -LiteralPath $OutputDirectory -Force).Count -ne 0) {
        throw "Output directory '$OutputDirectory' must be empty."
    }
}
else {
    New-Item -ItemType Directory -Path $OutputDirectory | Out-Null
}
$OutputDirectory = (Resolve-Path -LiteralPath $OutputDirectory).Path

$compilerArguments = @(
    "/DAppVersion=$version",
    "/DPayloadDir=$PayloadDirectory",
    "/DOutputDir=$OutputDirectory",
    $scriptPath
)

& $IsccPath @compilerArguments
if ($LASTEXITCODE -ne 0) {
    throw "Inno Setup compilation failed with exit code $LASTEXITCODE."
}

$installerName = "NewzDeck_v${version}_Setup.exe"
$portableName = "NewzDeck_v${version}_Portable.zip"
$checksumName = "NewzDeck_v${version}_SHA256.txt"
$installerPath = Join-Path $OutputDirectory $installerName
$portablePath = Join-Path $OutputDirectory $portableName
$checksumPath = Join-Path $OutputDirectory $checksumName

if (-not (Test-Path -LiteralPath $installerPath -PathType Leaf)) {
    throw "Inno Setup did not produce expected installer '$installerName'."
}

Add-Type -AssemblyName System.IO.Compression.FileSystem
[System.IO.Compression.ZipFile]::CreateFromDirectory(
    $PayloadDirectory,
    $portablePath,
    [System.IO.Compression.CompressionLevel]::Optimal,
    $false
)

$checksumLines = foreach ($artifact in @($installerPath, $portablePath)) {
    $hash = (Get-FileHash -LiteralPath $artifact -Algorithm SHA256).Hash.ToLowerInvariant()
    '{0}  {1}' -f $hash, (Split-Path -Leaf $artifact)
}
[System.IO.File]::WriteAllLines(
    $checksumPath,
    $checksumLines,
    [System.Text.UTF8Encoding]::new($false)
)

Write-Host "Built NewzDeck Windows release assets for ${expectedTag}:"
Get-ChildItem -LiteralPath $OutputDirectory -File | ForEach-Object {
    Write-Host " - $($_.Name)"
}
