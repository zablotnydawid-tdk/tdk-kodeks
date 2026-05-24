$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$VenvPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"

if (Test-Path $VenvPython) {
    & $VenvPython (Join-Path $ProjectRoot "scripts\local_operator_audit.py") @args
    exit $LASTEXITCODE
}

$Python = Get-Command python -ErrorAction SilentlyContinue
if ($Python) {
    & $Python.Source (Join-Path $ProjectRoot "scripts\local_operator_audit.py") @args
    exit $LASTEXITCODE
}

if (Get-Command py -ErrorAction SilentlyContinue) {
    & py -3 (Join-Path $ProjectRoot "scripts\local_operator_audit.py") @args
    exit $LASTEXITCODE
}

if (Get-Command wsl.exe -ErrorAction SilentlyContinue) {
    $ArgString = ($args | ForEach-Object { "'$_'" }) -join " "
    wsl.exe bash -lc "cd /mnt/c/KODEKS && .venv/bin/python scripts/local_operator_audit.py $ArgString"
    exit $LASTEXITCODE
}

throw "Python not found. Install Python or create .venv first."
