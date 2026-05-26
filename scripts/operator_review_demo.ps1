param(
    [string]$Root = "C:\KODEKS",
    [string]$InputPath = "",
    [string]$OutputPath = "",
    [string]$MarkdownPath = ""
)

$ErrorActionPreference = "Stop"

function Convert-ToWslPath {
    param([string]$Path)

    $fullPath = [System.IO.Path]::GetFullPath($Path)
    if ($fullPath -match "^([A-Za-z]):\\(.*)$") {
        $drive = $Matches[1].ToLowerInvariant()
        $rest = $Matches[2] -replace "\\", "/"
        return "/mnt/$drive/$rest"
    }
    return $Path
}

function Resolve-Python {
    param([string]$Root)

    $candidates = @(
        (Join-Path $Root ".venv\Scripts\python.exe"),
        "python",
        "py"
    )
    foreach ($candidate in $candidates) {
        if (Test-Path $candidate) {
            if ([System.IO.Path]::GetExtension($candidate).ToLowerInvariant() -eq ".exe") {
                return [pscustomobject]@{ Kind = "windows"; Path = $candidate }
            }
            continue
        }
        $command = Get-Command $candidate -ErrorAction SilentlyContinue
        if ($command) {
            return [pscustomobject]@{ Kind = "windows"; Path = $command.Source }
        }
    }

    $wslPython = Join-Path $Root ".venv\bin\python"
    if ((Test-Path $wslPython) -and (Get-Command "wsl.exe" -ErrorAction SilentlyContinue)) {
        return [pscustomobject]@{ Kind = "wsl"; Path = (Convert-ToWslPath $wslPython) }
    }
    if (Get-Command "wsl.exe" -ErrorAction SilentlyContinue) {
        return [pscustomobject]@{ Kind = "wsl"; Path = "python3" }
    }
    return $null
}

try {
    $pythonCommand = Resolve-Python -Root $Root
    if (-not $pythonCommand) {
        Write-Error "Missing Python runtime"
        exit 2
    }

    if (-not $InputPath) {
        $InputPath = Join-Path $Root "sample_data\operator_review_input.json"
    }
    if (-not $OutputPath) {
        $OutputPath = Join-Path $Root "data\live_ops\operator_review_result.json"
    }
    if (-not $MarkdownPath) {
        $MarkdownPath = Join-Path $Root "data\live_ops\operator_review_report.md"
    }

    if (-not (Test-Path $InputPath)) {
        Write-Error "Missing operator review input: $InputPath"
        exit 2
    }
    $runtimePath = Join-Path $Root "app\live_ops\operator_review.py"
    if (-not (Test-Path $runtimePath)) {
        Write-Error "Missing operator review runtime: $runtimePath"
        exit 2
    }

    Write-Host ""
    Write-Host "EXIM OPERATOR REVIEW :: CLOSED-CASE DEMO" -ForegroundColor Cyan
    Write-Host ("input:    {0}" -f $InputPath)
    Write-Host ("json:     {0}" -f $OutputPath)
    Write-Host ("markdown: {0}" -f $MarkdownPath)
    Write-Host ""

    if ($pythonCommand.Kind -eq "wsl") {
        $output = & wsl.exe $pythonCommand.Path (Convert-ToWslPath $runtimePath) --input (Convert-ToWslPath $InputPath) --output (Convert-ToWslPath $OutputPath) --markdown (Convert-ToWslPath $MarkdownPath) 2>&1
    }
    else {
        $output = & $pythonCommand.Path $runtimePath --input $InputPath --output $OutputPath --markdown $MarkdownPath 2>&1
    }
    $code = $LASTEXITCODE
    if ($null -eq $code) {
        if ((Test-Path $OutputPath) -and (Test-Path $MarkdownPath)) {
            $code = 0
        }
        else {
            $code = 1
        }
    }
    if ($code -ne 0) {
        $output | ForEach-Object { Write-Host $_ }
        Write-Error "OPERATOR REVIEW demo failed with exit code $code"
        exit 1
    }
    $output | ForEach-Object { Write-Host $_ }

    Write-Host ""
    Write-Host "operator-review-demo-ok" -ForegroundColor Green
    exit 0
} catch {
    Write-Error ("OPERATOR REVIEW controlled failure: {0}" -f $_.Exception.Message)
    exit 1
}
