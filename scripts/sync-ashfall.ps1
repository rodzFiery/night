# NEXORA ASHFALL — one-command visual branch sync (Windows PowerShell 5.1).
# Run from anywhere. Keeps a timestamped backup of the current app directory.
$ErrorActionPreference = 'Stop'
$project = Join-Path $env:USERPROFILE 'Downloads\night-main\night-main'
if (-not (Test-Path (Join-Path $project 'app\main.py'))) {
  throw "NEXORA project not found at $project. Change the project path in this script."
}
$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$backup = Join-Path $project ("app-backup-" + $stamp)
$zip = Join-Path $env:TEMP ("nexora-ashfall-" + $stamp + ".zip")
$extract = Join-Path $env:TEMP ("nexora-ashfall-" + $stamp)
Write-Host "Backing up existing app to $backup"
Copy-Item (Join-Path $project 'app') $backup -Recurse -Force
try {
  $url = 'https://github.com/rodzFiery/night/archive/refs/heads/ashfall-settlement-terrain-rework.zip'
  Write-Host 'Downloading the latest ASHFALL development branch...'
  Invoke-WebRequest -Uri $url -OutFile $zip -UseBasicParsing
  Expand-Archive -LiteralPath $zip -DestinationPath $extract -Force
  $source = Get-ChildItem -Path $extract -Directory | Select-Object -First 1
  if (-not $source) { throw 'Archive has no project folder.' }
  $app = Join-Path $source.FullName 'app'
  if (-not (Test-Path (Join-Path $app 'main.py'))) { throw 'Archive missing app/main.py.' }
  Copy-Item (Join-Path $app '*') (Join-Path $project 'app') -Recurse -Force
  Write-Host 'ASHFALL branch synchronized successfully.' -ForegroundColor Green
  Write-Host "Backup: $backup"
  Write-Host 'Restart Uvicorn and press Ctrl+F5 in your browser.'
} catch {
  Write-Host 'Update failed. Original app backup remains intact.' -ForegroundColor Red
  throw
} finally {
  if (Test-Path $zip) { Remove-Item $zip -Force }
  if (Test-Path $extract) { Remove-Item $extract -Recurse -Force }
}
