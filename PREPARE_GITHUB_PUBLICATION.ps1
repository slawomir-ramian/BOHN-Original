$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()
$env:PYTHONUTF8 = "1"

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

try {
    & git rev-parse --is-inside-work-tree *> $null
    if ($LASTEXITCODE -ne 0) {
        throw "ERROR: this directory is not a Git repository."
    }

    $Python = Join-Path $Root ".venv\Scripts\python.exe"
    if (-not (Test-Path $Python)) {
        $PythonCommand = Get-Command python -ErrorAction SilentlyContinue
        if ($null -eq $PythonCommand) {
            throw "ERROR: Python and the .venv environment were not found."
        }
        $Python = $PythonCommand.Source
    }

    & $Python -m unittest tests.test_github_publication -v
    if ($LASTEXITCODE -ne 0) {
        throw "ERROR: publication preparation tests failed."
    }

    & $Python tools\validate_stage_15_closeout.py
    if ($LASTEXITCODE -ne 0) {
        throw "ERROR: Stage 15 closeout validation failed."
    }

    & $Python tools\audit_github_publication.py
    if ($LASTEXITCODE -ne 0) {
        throw "ERROR: publication audit found a blocking problem."
    }

    Write-Host "GITHUB PUBLICATION PREPARATION: PASS" -ForegroundColor Green
    Write-Host "Report: docs\GITHUB_PUBLICATION_AUDIT.md"
    Write-Host "No git add, git commit, git remote or git push was executed."
}
catch {
    Write-Host ("ERROR: " + $_.Exception.Message) -ForegroundColor Red
    exit 1
}
