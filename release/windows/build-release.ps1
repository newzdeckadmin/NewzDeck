[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [string]$PayloadDirectory,

    [Parameter(Mandatory)]
    [string]$PortableArchive,

    [Parameter(Mandatory)]
    [string]$OutputDirectory,

    [Parameter(Mandatory)]
    [string]$Version,

    [Parameter(Mandatory)]
    [string]$IsccPath
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$PayloadDirectory = (Resolve-Path -LiteralPath $PayloadDirectory).Path
$PortableArchive = (Resolve-Path -LiteralPath $PortableArchive).Path
$IsccPath = (Resolve-Path -LiteralPath $IsccPath).Path
$scriptPath = Join-Path $PSScriptRoot 'NewzDeck.iss'

if ($Version -notmatch '^\d+\.\d+\.\d+$') {
    throw "Version '$Version' is invalid. Expected X.Y.Z."
}

$requiredFiles = @(
    'version.txt',
    'NewzDeck.exe',
    'NewzDeck.ico',
    'NewzDeckBootstrap.exe',
    'NewzDeckCore.exe',
    'NewzDeckService.exe',
    'NewzDeckTray.exe',
    'NewzDeckPicker.exe',
    'NewzDeckThumb.exe',
    'NewzDeckYenc.exe',
    'server.py',
    'sab_engine.py',
    'automation_engine.py',
    'static/index.html',
    'static/app.js',
    'static/styles.css'
)
foreach ($requiredFile in $requiredFiles) {
    if (-not (Test-Path -LiteralPath (Join-Path $PayloadDirectory $requiredFile) -PathType Leaf)) {
        throw "Release payload is missing required file '$requiredFile'."
    }
}

$payloadVersion = (Get-Content -LiteralPath (Join-Path $PayloadDirectory 'version.txt') -Raw).Trim()
if ($payloadVersion -cne $Version) {
    throw "Payload version '$payloadVersion' does not match requested version '$Version'."
}

$iconBytes = [System.IO.File]::ReadAllBytes((Join-Path $PayloadDirectory 'NewzDeck.ico'))
if ($iconBytes.Length -lt 6 -or $iconBytes[0] -ne 0 -or $iconBytes[1] -ne 0 -or $iconBytes[2] -ne 1 -or $iconBytes[3] -ne 0) {
    throw 'NewzDeck.ico is not a valid Windows icon file.'
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
    "/DAppVersion=$Version",
    "/DPayloadDir=$PayloadDirectory",
    "/DOutputDir=$OutputDirectory",
    $scriptPath
)

& $IsccPath @compilerArguments
if ($LASTEXITCODE -ne 0) {
    throw "Inno Setup compilation failed with exit code $LASTEXITCODE."
}

$installerName = "NewzDeck_v${Version}_Setup.exe"
$portableName = "NewzDeck_v${Version}_Portable.zip"
$checksumName = "NewzDeck_v${Version}_SHA256.txt"
$installerPath = Join-Path $OutputDirectory $installerName
$portablePath = Join-Path $OutputDirectory $portableName
$checksumPath = Join-Path $OutputDirectory $checksumName

if (-not (Test-Path -LiteralPath $installerPath -PathType Leaf)) {
    throw "Inno Setup did not produce expected installer '$installerName'."
}

Copy-Item -LiteralPath $PortableArchive -Destination $portablePath -Force

$checksumLines = foreach ($artifact in @($installerPath, $portablePath)) {
    $hash = (Get-FileHash -LiteralPath $artifact -Algorithm SHA256).Hash.ToLowerInvariant()
    '{0}  {1}' -f $hash, (Split-Path -Leaf $artifact)
}
[System.IO.File]::WriteAllLines(
    $checksumPath,
    $checksumLines,
    [System.Text.UTF8Encoding]::new($false)
)

Write-Host "Built NewzDeck Windows release assets for v${Version}:"
Get-ChildItem -LiteralPath $OutputDirectory -File | ForEach-Object {
    Write-Host " - $($_.Name)"
}
