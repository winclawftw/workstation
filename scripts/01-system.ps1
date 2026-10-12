[CmdletBinding()] param()
. "$PSScriptRoot\common.ps1"
$phase='Gate1-Windows-Foundation'; $started=Get-Date; Assert-ProtectedDiskReadOnly | Out-Null
$checks=[ordered]@{ admin=Test-Admin; winget=(Test-Command winget); powershell_51=$PSVersionTable.PSVersion.ToString(); firewall_enabled=@(Get-NetFirewallProfile | Where-Object Enabled -eq $true).Count -gt 0; defender_enabled=([bool](Get-MpComputerStatus -ErrorAction SilentlyContinue).AntivirusEnabled) }
$status=if($checks.winget){'PASS'}else{'BLOCKED'}; $msg=($checks | ConvertTo-Json -Compress); Write-SetupLog $phase 'Validate Windows foundation prerequisites' 'PowerShell' $msg 0 $status ((Get-Date)-$started).TotalSeconds
Update-State @{ current_phase=$phase; completed_phases=@('Gate0-Preflight',$phase); blocked_phases=if($status -eq 'BLOCKED'){@('Gate1-Windows-Foundation')}else{@()}; next_recommended_phase='Gate2-Developer-Tools' }
Write-Output "$status $phase`n$($checks | Out-String)"
