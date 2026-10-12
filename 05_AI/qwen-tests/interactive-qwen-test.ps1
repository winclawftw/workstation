[CmdletBinding()]
param([switch]$DryRun)
Add-Type -AssemblyName System.Net.Http

$ErrorActionPreference='Stop'
$Base='C:\Einrichtung\05_AI\qwen-tests'
$Ollama='C:\Einrichtung\05_AI\ollama\ollama.exe'
$Endpoint='http://127.0.0.1:11434'
$Model = 'qwen3.8:latest'
$script:LastReport=$null
$script:LastRun=$null
$Schema=@{type='object';properties=@{summary=@{type='string'};steps=@{type='array';items=@{type='string'}}};required=@('summary','steps');additionalProperties=$false}

function Save-Json($Path,$Value){$Value|ConvertTo-Json -Depth 20|Set-Content -LiteralPath $Path -Encoding UTF8}
function Add-Jsonl($Writer,$Value){$Writer.WriteLine(($Value|ConvertTo-Json -Depth 20 -Compress));$Writer.Flush()}
function Get-TargetProcesses{
  $names=@('ollama.exe','llama-server.exe','hermes.exe','python.exe','lmstudio.exe','vllm.exe','docker.exe','wsl.exe','codex.exe','codex-code-mode-host.exe')
  @(Get-CimInstance Win32_Process|Where-Object{$names -contains $_.Name}|ForEach-Object{[pscustomobject]@{Name=$_.Name;PID=$_.ProcessId;ParentPID=$_.ParentProcessId;ExecutablePath=$_.ExecutablePath;CommandLine=$_.CommandLine;RAM_MiB=[math]::Round($_.WorkingSetSize/1MB,1)}})
}
function Get-GpuSnapshot{
  $line=(nvidia-smi --query-gpu=timestamp,name,memory.total,memory.used,memory.free,utilization.gpu,utilization.memory,temperature.gpu --format=csv,noheader,nounits 2>$null|Select-Object -First 1)
  if(-not $line){return [pscustomobject]@{available=$false;error='nvidia-smi failed'}}
  $p=$line-split','|ForEach-Object{$_.Trim()}
  [pscustomobject]@{available=$true;timestamp=$p[0];name=$p[1];vram_total_mib=$p[2];vram_used_mib=$p[3];vram_free_mib=$p[4];gpu_utilization=$p[5];gpu_memory_utilization=$p[6];temperature_c=$p[7]}
}
function Get-SystemSnapshot{
  $os=Get-CimInstance Win32_OperatingSystem
  [pscustomobject]@{free_ram_gib=[math]::Round($os.FreePhysicalMemory/1MB,2);total_ram_gib=[math]::Round($os.TotalVisibleMemorySize/1MB,2);cpu_load_percent=[math]::Round((Get-CimInstance Win32_Processor|Measure-Object LoadPercentage -Average).Average,1)}
}
function Invoke-Ollama {& $Ollama $args 2>&1|Out-String|ForEach-Object{$_.Trim()}}
function Get-Api($Path){Invoke-RestMethod -Uri ($Endpoint+$Path) -Method Get -TimeoutSec 8}
function Confirm-Action($Text){$v=Read-Host "$Text [j/N]";return $v.ToLowerInvariant() -eq 'j'}
function New-Run{
  $dir=Join-Path $Base ('interactive-runs\'+(Get-Date -Format 'yyyyMMdd-HHmmss'))
  New-Item -ItemType Directory -Force -Path $dir|Out-Null
  return $dir
}
function Write-Preflight($Dir,$Context){
  $proc=Get-TargetProcesses;$gpu=Get-GpuSnapshot;$sys=Get-SystemSnapshot
  $ollamaReachable=$false;$apiVersion=$null;$apiError=$null
  try{$apiVersion=Get-Api '/api/version';$ollamaReachable=$true}catch{$apiError=$_.Exception.Message}
  if($ollamaReachable){$ollamaPs=Invoke-Ollama @('ps');$list=Invoke-Ollama @('list');try{$tags=Get-Api '/api/tags'|ConvertTo-Json -Depth 20}catch{$tags='OLLAMA_UNAVAILABLE'};try{$apiPs=Get-Api '/api/ps'|ConvertTo-Json -Depth 20}catch{$apiPs='OLLAMA_UNAVAILABLE'}}else{$ollamaPs='OLLAMA_UNAVAILABLE';$list='OLLAMA_UNAVAILABLE';$tags='OLLAMA_UNAVAILABLE';$apiPs='OLLAMA_UNAVAILABLE'}
  $modelAvailable=($ollamaReachable -and $list -match [regex]::Escape($Model))
  $llama=@($proc|Where-Object Name -eq 'llama-server.exe')
  $status=if(-not $ollamaReachable){'OLLAMA_UNAVAILABLE'}elseif(-not $modelAvailable){'MODEL_NOT_FOUND'}elseif($llama.Count -gt 0){'DIRTY_STATE'}elseif(-not $gpu.available){'CLIENT_ERROR'}else{'PASS'}
  $pre=[pscustomobject]@{timestamp=(Get-Date).ToString('o');model=$Model;context=$Context;parallel=1;endpoint=$Endpoint;processes=$proc;ollama_reachable=$ollamaReachable;api_version=$apiVersion;api_error=$apiError;ollama_ps=$ollamaPs;ollama_list=$list;api_tags=$tags;api_ps=$apiPs;gpu=$gpu;system=$sys;model_available=$modelAvailable;llama_count=$llama.Count;status=$status;message=if($status -eq 'OLLAMA_UNAVAILABLE'){"Ollama API is not reachable at $Endpoint. Start Ollama manually and run preflight again."}else{$null}}
  Save-Json (Join-Path $Dir 'preflight.json') $pre;Set-Content (Join-Path $Dir 'preflight.md') (($pre|ConvertTo-Json -Depth 20)) -Encoding UTF8
  return $pre
}
function Get-Sample($Phase,$Elapsed){[pscustomobject]@{timestamp=(Get-Date).ToString('o');phase=$Phase;elapsed_ms=$Elapsed;gpu=Get-GpuSnapshot;system=Get-SystemSnapshot;ollama_ps=Invoke-Ollama @('ps');processes=Get-TargetProcesses;llama_count=@(Get-TargetProcesses|Where-Object Name -eq 'llama-server.exe').Count}}
function Invoke-Test($Context){
  $dir=New-Run;$script:LastRun=$dir;$script:LastReport=Join-Path $dir 'report.md'
  $sampleW=[IO.StreamWriter]::new((Join-Path $dir 'runtime-samples.jsonl'),$true,[Text.UTF8Encoding]::new($false));$sampleW.AutoFlush=$true
  $responseW=[IO.StreamWriter]::new((Join-Path $dir 'response-stream.jsonl'),$true,[Text.UTF8Encoding]::new($false));$responseW.AutoFlush=$true
  $errorW=[IO.StreamWriter]::new((Join-Path $dir 'errors.jsonl'),$true,[Text.UTF8Encoding]::new($false));$errorW.AutoFlush=$true
  $status='CLIENT_ERROR';$errorText=$null;$requestCount=0;$testPids=@();$responseText='';$json=$null;$httpStatus=$null;$done=$false;$start=(Get-Date)
  try{
    $pre=Write-Preflight $dir $Context
    if($pre.status -ne 'PASS'){throw $pre.status}
    if(-not (Confirm-Action "Start exactly one $Context-token request for $Model?")){throw 'User declined test.'}
    $Schema = @{ type = "object"; properties = @{ summary = @{ type = "string" }; steps = @{ type = "array"; items = @{ type = "string" } } }; required = @("summary", "steps"); additionalProperties = $false }; $request = @{model=$Model;prompt='Erkläre in höchstens fünf kurzen Stichpunkten, was ein kontrollierter Agenten-Workflow mit Plan, Tool-Ausführung, Validierung und Audit bedeutet. Gib ausschließlich die Felder summary und steps gemäß dem JSON-Schema zurück. Erzeuge ausschließlich eine Antwort gemäß dem übergebenen JSON-Schema. Keine Markdown-Codeblöcke. Kein zusätzlicher Text.';stream=$true;format=$Schema;keep_alive='5m';options=@{num_ctx=$Context;temperature=0;num_predict=2048}}|ConvertTo-Json -Depth 20
    Set-Content (Join-Path $dir 'request.json') $request -Encoding UTF8
    Add-Jsonl $sampleW (Get-Sample 'before_request' 0);$requestCount=1;$sw=[Diagnostics.Stopwatch]::StartNew()
    $client=[System.Net.Http.HttpClient]::new();$msg=[Net.Http.HttpRequestMessage]::new([Net.Http.HttpMethod]::Post,($Endpoint+'/api/generate'));$msg.Content=[Net.Http.StringContent]::new($request,[Text.Encoding]::UTF8,'application/json')
    $task=$client.SendAsync($msg,[Net.Http.HttpCompletionOption]::ResponseHeadersRead)
    while(-not $task.IsCompleted){Start-Sleep -Seconds 1;Add-Jsonl $sampleW (Get-Sample 'during_headers' $sw.ElapsedMilliseconds)}
    $resp=$task.GetAwaiter().GetResult();$httpStatus=[int]$resp.StatusCode;Add-Jsonl $responseW ([pscustomobject]@{type='headers';timestamp=(Get-Date).ToString('o');http_status=$httpStatus;headers=($resp.Headers|Out-String)})
    if(-not $resp.IsSuccessStatusCode){$body=$resp.Content.ReadAsStringAsync().GetAwaiter().GetResult();Add-Jsonl $responseW ([pscustomobject]@{type='http_error';body=$body});throw "HTTP $httpStatus"}
    $reader=[IO.StreamReader]::new($resp.Content.ReadAsStreamAsync().Result);$chunks=@()
    while($true){$lt=$reader.ReadLineAsync();while(-not $lt.IsCompleted){Start-Sleep -Seconds 1;Add-Jsonl $sampleW (Get-Sample 'during_generation' $sw.ElapsedMilliseconds)};$line=$lt.GetAwaiter().GetResult();if($null -eq $line){break};if($line){Add-Jsonl $responseW ([pscustomobject]@{type='chunk';timestamp=(Get-Date).ToString('o');raw=$line});$o=$line|ConvertFrom-Json;$chunks+=$o;if($o.response){$responseText+=$o.response};if($o.done){$done=$true;break}}}
    if(-not $done){throw 'INCOMPLETE_STREAM'}
    Add-Jsonl $sampleW (Get-Sample 'after_response' $sw.ElapsedMilliseconds)
    try { $clean = $responseText -replace '```json\s*', '' -replace '```\s*', '' ; $json = $clean | ConvertFrom-Json } catch { throw 'INVALID_MODEL_RESPONSE' }
    if($null -eq $json.summary -or $json.steps -isnot [array]){throw 'INVALID_MODEL_RESPONSE_SCHEMA'}
    Set-Content (Join-Path $dir 'response.json') ($json|ConvertTo-Json -Depth 20) -Encoding UTF8;$status=if($Context -eq 8192 -and (Get-GpuSnapshot).available){'QUALIFIED_8K_GPU'}else{'CONDITIONAL_8K'}
  }catch{ $errorText=$_.Exception.Message;Add-Jsonl $errorW ([pscustomobject]@{timestamp=(Get-Date).ToString('o');message=$errorText;stage='test'});if($errorText -match 'OLLAMA|connect|endpoint'){$status='OLLAMA_UNAVAILABLE'}elseif($errorText -match 'MODEL_NOT_FOUND'){$status='MODEL_NOT_FOUND'}elseif($errorText -match 'OUT_OF_MEMORY|CUDA|GPU'){$status='OUT_OF_MEMORY'}elseif($errorText -match 'INVALID_MODEL_RESPONSE'){$status='INVALID_MODEL_RESPONSE'}}
  finally{
    try{$ps=Invoke-Ollama @('ps');$remaining=@(Get-TargetProcesses|Where-Object Name -eq 'llama-server.exe');$post=[pscustomobject]@{timestamp=(Get-Date).ToString('o');status=if($remaining.Count -eq 0){'PASS'}else{'DIRTY_STATE'};ollama_ps=$ps;processes=Get-TargetProcesses;gpu=Get-GpuSnapshot;system=Get-SystemSnapshot;test_pids=$testPids;remaining_llama=$remaining.Count};Save-Json (Join-Path $dir 'postflight.json') $post;Set-Content (Join-Path $dir 'postflight.md') ($post|ConvertTo-Json -Depth 20) -Encoding UTF8}catch{Add-Jsonl $errorW ([pscustomobject]@{timestamp=(Get-Date).ToString('o');stage='postflight';message=$_.Exception.Message})}
    $runtime=[pscustomobject]@{status=$status;request_count=$requestCount;context=$Context;model=$Model;http_status=$httpStatus;response=$responseText;error=$errorText;request_start=$start.ToString('o');request_end=(Get-Date).ToString('o')};Save-Json (Join-Path $dir 'runtime.json') $runtime
    $report=@"
# Interactive Qwen/Ollama Test

Status: $status
Model: $Model
Context: $Context
Requests: $requestCount
HTTP status: $httpStatus
Error: $errorText
Run directory: $dir

See preflight, runtime samples, response stream, errors and postflight files in this directory.
"@;Set-Content $script:LastReport $report -Encoding UTF8;$sampleW.Dispose();$responseW.Dispose();$errorW.Dispose()
  }
  Write-Host "`nStatus: $status`nReport: $script:LastReport" -ForegroundColor Cyan
}
function Invoke-PreflightOnly{$dir=New-Run;$p=Write-Preflight $dir 8192;if($p.status -eq 'OLLAMA_UNAVAILABLE'){Write-Host "`nOLLAMA_UNAVAILABLE`nEndpoint: $Endpoint`nKeine Modellanfrage gestartet.`nKein Prozess beendet.`nKein Benchmark durchgeführt.`nBitte Ollama manuell starten und anschließend Preflight erneut ausführen.`n" -ForegroundColor Yellow}else{Write-Host ($p|ConvertTo-Json -Depth 10)};$script:LastRun=$dir;$script:LastReport=Join-Path $dir 'preflight.md'}
function Invoke-CleanupCheck{$p=Get-TargetProcesses;Get-GpuSnapshot|Format-List;Get-SystemSnapshot|Format-List;$p|Format-Table -AutoSize;Write-Host 'No process was terminated.'}
function Open-LastReport{if($script:LastReport -and (Test-Path $script:LastReport)){Invoke-Item $script:LastReport}else{Write-Host 'No report recorded in this session.'}}
function Show-Menu{Write-Host "`nInteractive Qwen/Ollama Test`n1. Preflight anzeigen`n2. Qwen-Ollama-8K-Test`n3. Qwen-Ollama-16K-Test`n4. Qwen-Ollama-32K-Test`n5. Hermes-Test (deaktiviert)`n6. Cleanup-Check`n7. letzten Report öffnen`n8. Beenden"}
if($DryRun){Show-Menu;Write-Host 'Dry-run: keine Aktionen ausgeführt.';exit 0}
do{Show-Menu;$choice=Read-Host 'Auswahl';switch($choice){'1'{Invoke-PreflightOnly}'2'{Invoke-Test 8192}'3'{if(Confirm-Action '16K-Test ausdrücklich freigeben?'){Invoke-Test 16384}}'4'{if(Confirm-Action '32K-Test ausdrücklich freigeben?'){Invoke-Test 32768}}'5'{Write-Host 'Hermes-Test ist in diesem Skript deaktiviert.'}'6'{Invoke-CleanupCheck}'7'{Open-LastReport}'8'{return}default{Write-Host 'Ungültige Auswahl.'}}}while($true)

