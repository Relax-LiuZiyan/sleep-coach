Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$specPath = Join-Path $repoRoot "SleepCoach.spec"
$installerScript = Join-Path $repoRoot "installer\SleepCoach.iss"
$distExe = Join-Path $repoRoot "dist\SleepCoach\SleepCoach.exe"
$releaseExe = Join-Path $repoRoot "release\SleepCoach-Setup.exe"
$portableZip = Join-Path $repoRoot "release\SleepCoach-portable.zip"

function Assert-LastExitCode {
    param(
        [string]$StepName
    )

    if ($LASTEXITCODE -ne 0) {
        throw "$StepName failed with exit code $LASTEXITCODE."
    }
}

function Resolve-ReleaseVersion {
    $version = python -m sleep_coach.release_version
    Assert-LastExitCode "Release version resolution"
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to resolve release version."
    }

    $resolved = $version.Trim()
    if (-not $resolved) {
        throw "Release version resolved to an empty string."
    }

    return $resolved
}

function Resolve-IsccPath {
    $command = Get-Command iscc -ErrorAction SilentlyContinue
    if ($command) {
        return $command.Source
    }

    $candidates = @(
        (Join-Path $env:LOCALAPPDATA "Programs\Inno Setup 6\ISCC.exe"),
        "C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
        "C:\Program Files\Inno Setup 6\ISCC.exe"
    )

    foreach ($candidate in $candidates) {
        if (Test-Path $candidate) {
            return $candidate
        }
    }

    throw "Inno Setup Compiler (ISCC.exe) was not found."
}

Write-Host "Running packaging tests..."
pytest tests -q
Assert-LastExitCode "Packaging tests"

Write-Host "Cleaning previous build artifacts..."
foreach ($path in @("build", "dist", "release")) {
    $target = Join-Path $repoRoot $path
    if (Test-Path $target) {
        Remove-Item -LiteralPath $target -Recurse -Force
    }
}

Write-Host "Building PyInstaller bundle..."
python -m PyInstaller --noconfirm --clean $specPath
Assert-LastExitCode "PyInstaller build"

if (-not (Test-Path $distExe)) {
    throw "PyInstaller build completed but $distExe was not found."
}

New-Item -ItemType Directory -Path (Join-Path $repoRoot "release") -Force | Out-Null

Write-Host "Creating portable ZIP..."
Compress-Archive -Path (Join-Path $repoRoot "dist\SleepCoach\*") -DestinationPath $portableZip -Force

if (-not (Test-Path $portableZip)) {
    throw "Portable ZIP build completed but $portableZip was not found."
}

$iscc = Resolve-IsccPath
$appVersion = Resolve-ReleaseVersion

Write-Host "Resolved release version: $appVersion"
Write-Host "Building installer..."
& $iscc "/DAppVersion=$appVersion" $installerScript
Assert-LastExitCode "Installer build"

if (-not (Test-Path $releaseExe)) {
    throw "Installer build completed but $releaseExe was not found."
}

Write-Host "Build complete:"
Write-Host "  Bundle  : $distExe"
Write-Host "  Portable : $portableZip"
Write-Host "  Installer: $releaseExe"
