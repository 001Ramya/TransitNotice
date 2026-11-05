$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$backendPath = Join-Path $projectRoot "backend"
$frontendPath = Join-Path $projectRoot "frontend"
$venvPython = Join-Path $backendPath ".venv\Scripts\python.exe"
$envFile = Join-Path $projectRoot ".env"
$envExample = Join-Path $projectRoot ".env.example"

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    throw "Python is not available. Install Python 3.12 or newer, then run this task again."
}
if (-not (Get-Command npm -ErrorAction SilentlyContinue)) {
    throw "Node.js is not available. Install Node.js LTS, then run this task again."
}

if (-not (Test-Path $envFile)) {
    Copy-Item -LiteralPath $envExample -Destination $envFile
    Write-Host "Created .env from .env.example."
}

if (-not (Test-Path $venvPython)) {
    Write-Host "Creating the local Python environment..."
    & python -m venv (Join-Path $backendPath ".venv")
}

Write-Host "Installing backend packages..."
& $venvPython -m pip install --upgrade pip
& $venvPython -m pip install -r (Join-Path $backendPath "requirements.txt")

Write-Host "Installing frontend packages..."
Push-Location $frontendPath
try {
    & npm install
}
finally {
    Pop-Location
}

Write-Host ""
Write-Host "Preparation complete."
Write-Host "Next: run sql\setup_local_database.sql once from the VS Code PostgreSQL extension,"
Write-Host "then run the task: TransitNotice: Run website."
