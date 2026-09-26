$ErrorActionPreference = "Stop"
$OutputEncoding = [Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()

if (-not (Test-Path ".\experiments\05_permutation_and_representation")) {
    throw "Najpierw zainstaluj Etap 07."
}
if (-not (Test-Path ".\.venv\Scripts\python.exe")) {
    throw "Brak .venv. Najpierw uruchom .\SETUP_STAGE_07.ps1"
}

& .\.venv\Scripts\python.exe -m pip install -r requirements-stage07r.txt
if ($LASTEXITCODE -ne 0) { throw "Instalacja zaleznosci Etapu 07R nie powiodla sie." }

& .\.venv\Scripts\python.exe tools\materialize_stage_07r.py
if ($LASTEXITCODE -ne 0) { throw "Materializacja Etapu 07R nie powiodla sie." }

& .\.venv\Scripts\python.exe tools\run_stage_07r.py --validate-lock
if ($LASTEXITCODE -ne 0) { throw "Kontrola blokady protokolu nie powiodla sie." }

Write-Host "SETUP STAGE 07R: PASS" -ForegroundColor Green
