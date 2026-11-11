<#
.SYNOPSIS
  Build a standalone Windows app (dist\CaptionAssist\CaptionAssist.exe) and a zip for releases.

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File scripts\build.ps1
#>
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

$version = (Select-String -Path "src\caption_assist\__init__.py" -Pattern '__version__ = "(.+)"').Matches[0].Groups[1].Value
Write-Host "Building Caption Assist $version" -ForegroundColor Cyan

python -m pip install --upgrade -e ".[dev]" | Out-Null
python scripts\make_icon.py
python -m pytest -q

if (Test-Path build) { Remove-Item build -Recurse -Force }
if (Test-Path dist)  { Remove-Item dist  -Recurse -Force }

python -m PyInstaller `
  --noconfirm --clean --windowed `
  --name CaptionAssist `
  --icon assets\icon.ico `
  --paths src `
  --collect-submodules caption_assist `
  --exclude-module tkinter `
  run.pyw

$zip = "dist\CaptionAssist-$version-win64.zip"
Compress-Archive -Path dist\CaptionAssist\* -DestinationPath $zip -Force
Write-Host "Done: dist\CaptionAssist\CaptionAssist.exe" -ForegroundColor Green
Write-Host "Release zip: $zip" -ForegroundColor Green
