$ErrorActionPreference = 'Stop'
Set-Location 'C:\Einrichtung\07_Keystone'

New-Item -ItemType Directory -Force -Path '.\keystone_core', '.\tests', '.\data', '.\scripts' | Out-Null

$contracts = @'
class ModelUnavailable(RuntimeError):
    """Raised when a model provider cannot be reached or used."""
'@
Set-Content -LiteralPath '.\keystone_core\contracts.py' -Value $contracts -Encoding utf8

$files = @(
    @{ Url = 'https://raw.githubusercontent.com/winclawftw/workstation/main/07_Keystone/keystone_core/bonsai.py'; Path = '.\keystone_core\bonsai.py' },
    @{ Url = 'https://raw.githubusercontent.com/winclawftw/workstation/main/07_Keystone/tests/test_bonsai_provider.py'; Path = '.\tests\test_bonsai_provider.py' }
)

foreach ($file in $files) {
    Write-Host "Fetching $($file.Path) ..."
    Invoke-WebRequest -Uri $file.Url -OutFile $file.Path
}

if (-not (Test-Path '.\keystone_core\__init__.py')) {
    Set-Content '.\keystone_core\__init__.py' '"""Keystone core package."""' -Encoding utf8
}

Write-Host "`n=== PYTHON ==="
python --version
if ($LASTEXITCODE -ne 0) { throw 'Python is not available as python.' }

Write-Host "`n=== UNIT TESTS ==="
python -m unittest discover -s tests -v
$testExit = $LASTEXITCODE

Write-Host "`n=== PYTHON COMPILE CHECK ==="
python -m compileall -q keystone_core tests
$compileExit = $LASTEXITCODE

Write-Host "`n=== GIT STATUS (READ ONLY) ==="
git status --short -- 07_Keystone

Write-Host "`nRESULT: unittest=$testExit compileall=$compileExit"
if ($testExit -ne 0 -or $compileExit -ne 0) { exit 1 }
exit 0