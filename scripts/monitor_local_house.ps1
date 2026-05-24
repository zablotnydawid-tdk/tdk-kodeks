$ErrorActionPreference = "Stop"

$ProjectRoot = "C:\KODEKS"
$Python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"

if (-not (Test-Path $Python)) {
    if (Get-Command py -ErrorAction SilentlyContinue) {
        & py -3 (Join-Path $ProjectRoot "scripts\local_house_status.py") @args
        exit $LASTEXITCODE
    }

    $PythonCommand = Get-Command python -ErrorAction SilentlyContinue
    if ($PythonCommand) {
        $Python = $PythonCommand.Source
    } elseif (Get-Command wsl.exe -ErrorAction SilentlyContinue) {
        $ArgString = ($args | ForEach-Object { "'$_'" }) -join " "
        wsl.exe bash -lc "cd /mnt/c/KODEKS && .venv/bin/python scripts/local_house_status.py $ArgString"
        exit $LASTEXITCODE
    } else {
        throw "Python not found. Install Python, create Windows .venv, or run from WSL with .venv/bin/python."
    }
}

& $Python (Join-Path $ProjectRoot "scripts\local_house_status.py") @args
exit $LASTEXITCODE
