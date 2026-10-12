[CmdletBinding()]
param()
$ErrorActionPreference='Stop'
$root='C:\Einrichtung\05_AI'
$bin=Join-Path $root 'ollama'
$models=Join-Path $root 'models'
$log=Join-Path $root 'ollama-server.log'
$err=Join-Path $root 'ollama-server.err.log'
New-Item -ItemType Directory -Force -Path $models | Out-Null
$env:OLLAMA_MODELS=$models
$existing=Get-Process -Name ollama -ErrorAction SilentlyContinue
if(-not $existing){
    $p=Start-Process -FilePath (Join-Path $bin 'ollama.exe') -ArgumentList 'serve' -WorkingDirectory $bin -RedirectStandardOutput $log -RedirectStandardError $err -PassThru
    Start-Sleep -Seconds 5
    "PID=$($p.Id)" | Set-Content -LiteralPath (Join-Path $root 'ollama-process.txt') -Encoding UTF8
}
try {
    $version=Invoke-RestMethod -Uri 'http://127.0.0.1:11434/api/version' -TimeoutSec 10
    $version | ConvertTo-Json -Depth 5
} catch {
    "API_ERROR=$($_.Exception.Message)"
    if(Test-Path $log){Get-Content $log -Tail 40}
    if(Test-Path $err){Get-Content $err -Tail 40}
    exit 1
}
