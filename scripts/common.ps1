Set-StrictMode -Version Latest
$script:SetupRoot = 'C:\Einrichtung'
$script:LogRoot = Join-Path $script:SetupRoot '08_Logs'
$script:DebugRoot = Join-Path $script:SetupRoot '09_Debug'
$script:StatePath = Join-Path $script:SetupRoot 'state\CODEX_STATE.json'
$script:CodexStatePath = Join-Path $script:SetupRoot '10_Codex\CODEX_STATE.json'

function Ensure-SetupDirectories {
    foreach ($path in @($script:SetupRoot, $script:LogRoot, $script:DebugRoot, (Join-Path $script:SetupRoot 'state'), (Join-Path $script:SetupRoot '10_Codex'), (Join-Path $script:SetupRoot '02_Tools\python'))) {
        New-Item -ItemType Directory -Force -Path $path | Out-Null
    }
}

function Write-SetupLog {
    param([string]$Phase,[string]$Action,[string]$CommandType,[string]$Result,[int]$ExitCode=0,[string]$Status='PASS',[double]$DurationSeconds=0)
    Ensure-SetupDirectories
    $entry = [ordered]@{ timestamp=(Get-Date).ToString('o'); phase=$Phase; action=$Action; command_type=$CommandType; result=$Result; exit_code=$ExitCode; duration_seconds=[math]::Round($DurationSeconds,3); status=$Status }
    $file = Join-Path $script:LogRoot ("setup-{0}.jsonl" -f (Get-Date -Format 'yyyyMMdd'))
    ($entry | ConvertTo-Json -Compress) | Add-Content -LiteralPath $file -Encoding UTF8
}

function Test-Command { param([string]$Name) return [bool](Get-Command $Name -ErrorAction SilentlyContinue) }
function Get-SafeCommandVersion { param([string]$Name,[string[]]$Arguments=@('--version'))
    if(-not (Test-Command $Name)){ return $null }
    $cmd=Get-Command $Name -ErrorAction SilentlyContinue
    if($cmd.Source -match '\\.cache\\codex-runtimes' -or ($Name -eq 'python' -and $cmd.Source -match 'WindowsApps')){ return $null }
    try { $out = & $Name @Arguments 2>&1 | Out-String; if($out -match 'was not found|not recognized|Microsoft Store'){ return $null }; return $out.Trim() } catch { return $null }
}
function Test-Admin { return ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator) }

function Get-ProtectedDiskInventory {
    Get-Disk | ForEach-Object {
        [pscustomobject]@{ number=$_.Number; model=$_.FriendlyName; serial=$_.SerialNumber; bus_type=[string]$_.BusType; partition_style=[string]$_.PartitionStyle; size_gb=[math]::Round($_.Size/1GB,2); is_boot=$_.IsBoot; is_system=$_.IsSystem; operational_status=[string]$_.OperationalStatus }
    }
}

function Update-State {
    param([hashtable]$Changes)
    Ensure-SetupDirectories
    $state = if(Test-Path $script:StatePath){ Get-Content -Raw $script:StatePath | ConvertFrom-Json -AsHashtable } else { @{} }
    foreach($key in $Changes.Keys){ $state[$key] = $Changes[$key] }
    $state['timestamps'] = @{ updated=(Get-Date).ToString('o'); last_update=(Get-Date).ToString('o') }
    $json=$state | ConvertTo-Json -Depth 15
    $json | Set-Content -LiteralPath $script:StatePath -Encoding UTF8
    $json | Set-Content -LiteralPath $script:CodexStatePath -Encoding UTF8
}

function Write-DebugReport {
    param([string]$Phase,[string]$ErrorMessage,[string]$SuggestedNextAction,[string]$CommandOutput='')
    Ensure-SetupDirectories
    $stamp=Get-Date -Format 'yyyyMMdd-HHmmss'
    $path=Join-Path $script:DebugRoot ("{0}-{1}.json" -f $Phase,$stamp)
    [ordered]@{ timestamp=(Get-Date).ToString('o'); failing_phase=$Phase; error=$ErrorMessage; suggested_next_action=$SuggestedNextAction; command_output=$CommandOutput; environment_summary=@{ computer=$env:COMPUTERNAME; user=$env:USERNAME; admin=Test-Admin; powershell=$PSVersionTable.PSVersion.ToString(); cwd=(Get-Location).Path }; versions=@{ git=Get-SafeCommandVersion git; python=Get-SafeCommandVersion python; node=Get-SafeCommandVersion node; wsl=Get-SafeCommandVersion wsl @('--version') } } | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $path -Encoding UTF8
    return $path
}

function Assert-ProtectedDiskReadOnly {
    $disks=Get-Disk
    $oneTb=$disks | Where-Object { $_.Size -ge 900GB -and $_.Size -le 1100GB -and -not $_.IsBoot }
    if(@($oneTb).Count -ne 1){ throw 'Protected 1-TB disk could not be identified uniquely; no storage action permitted.' }
    return $oneTb
}
