Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$specPath = Join-Path $repoRoot "SleepCoach.spec"
$installerScript = Join-Path $repoRoot "installer\SleepCoach.iss"
$distExe = Join-Path $repoRoot "dist\SleepCoach\SleepCoach.exe"
$releaseExe = Join-Path $repoRoot "release\SleepCoach-Setup.exe"
$portableZip = Join-Path $repoRoot "release\SleepCoach-portable.zip"

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
pytest tests/test_runtime_paths.py tests/test_startup.py -q

Write-Host "Cleaning previous build artifacts..."
foreach ($path in @("build", "dist", "release")) {
    $target = Join-Path $repoRoot $path
    if (Test-Path $target) {
        Remove-Item -LiteralPath $target -Recurse -Force
    }
}

Write-Host "Building PyInstaller bundle..."
python -m PyInstaller --noconfirm --clean $specPath

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

Write-Host "Building installer..."
& $iscc $installerScript

if (-not (Test-Path $releaseExe)) {
    throw "Installer build completed but $releaseExe was not found."
}

Write-Host "Build complete:"
Write-Host "  Bundle  : $distExe"
Write-Host "  Portable : $portableZip"
Write-Host "  Installer: $releaseExe"
