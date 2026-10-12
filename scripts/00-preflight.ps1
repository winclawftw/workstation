[CmdletBinding()] param()
. "$PSScriptRoot\common.ps1"
Ensure-SetupDirectories
$phase='Gate0-Preflight'; $started=Get-Date
$protected=Assert-ProtectedDiskReadOnly
$os=Get-ComputerInfo | Select-Object WindowsProductName,WindowsVersion,OsBuildNumber,OsArchitecture,WindowsInstallDateFromRegistry
$disks=Get-ProtectedDiskInventory
$volumes=Get-Volume | Select-Object DriveLetter,FileSystemLabel,FileSystem,@{N='size_gb';E={[math]::Round($_.Size/1GB,2)}},@{N='free_gb';E={[math]::Round($_.SizeRemaining/1GB,2)}}
$hardware=@{ cpu=(Get-CimInstance Win32_Processor | Select-Object -First 1 Name,NumberOfCores,NumberOfLogicalProcessors); board=(Get-CimInstance Win32_BaseBoard | Select-Object -First 1 Manufacturer,Product,SerialNumber); bios=(Get-CimInstance Win32_BIOS | Select-Object -First 1 SMBIOSBIOSVersion,ReleaseDate); ram_gb=[math]::Round((Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory/1GB,2); gpu=(Get-CimInstance Win32_VideoController | Select-Object Name,AdapterRAM,DriverVersion,DriverDate) }
$commands=@{}
foreach($n in 'winget','pwsh','git','python','py','node','npm','code','docker','wsl','ffmpeg','ffprobe','7z'){ $commands[$n]=Get-SafeCommandVersion $n }
$hyperv=$null; try { $hyperv=Get-WindowsOptionalFeature -Online -FeatureName Microsoft-Hyper-V-All -ErrorAction Stop | Select-Object FeatureName,State } catch { $hyperv=[pscustomobject]@{FeatureName='Microsoft-Hyper-V-All';State='UNAVAILABLE_NON_ADMIN'} }
$virtualization=@{ wsl_status=(wsl --status 2>&1 | Out-String).Trim(); wsl_version=(wsl --version 2>&1 | Out-String).Trim(); wsl_list=(wsl --list --verbose 2>&1 | Out-String).Trim(); hyperv=$hyperv; virtualization_firmware=(Get-CimInstance Win32_ComputerSystem).HypervisorPresent }
$network=@{ adapters=(Get-NetAdapter | Where-Object Status -eq 'Up' | Select-Object Name,InterfaceDescription,LinkSpeed,MacAddress); internet=(Test-NetConnection -ComputerName 'www.microsoft.com' -Port 443 -InformationLevel Quiet) }
$secureBoot=$null; try { $secureBoot=Confirm-SecureBootUEFI } catch { $secureBoot=$null }
$security=@{ secure_boot=$secureBoot; defender=(Get-MpComputerStatus -ErrorAction SilentlyContinue | Select-Object AMRunningMode,AntivirusEnabled,RealTimeProtectionEnabled); firewall=(Get-NetFirewallProfile | Select-Object Name,Enabled,DefaultInboundAction,DefaultOutboundAction) }
$adobe=@{}
foreach($name in 'Creative Cloud','Photoshop','Illustrator','Premiere Pro','After Effects','Media Encoder'){ $adobe[$name]=@(Get-ItemProperty 'HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall\*','HKLM:\Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\*','HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\*' -ErrorAction SilentlyContinue | Where-Object { $_.PSObject.Properties['DisplayName'] -and $_.DisplayName -like "*$name*" } | Select-Object -ExpandProperty DisplayName) }
$report=[ordered]@{ timestamp=(Get-Date).ToString('o'); phase=$phase; admin=Test-Admin; os=$os; hardware=$hardware; disks=$disks; volumes=$volumes; commands=$commands; virtualization=$virtualization; network=$network; security=$security; adobe=$adobe; protected_disk=$protected }
$jsonPath='C:\Einrichtung\00_Preflight\preflight-report.json'; $txtPath='C:\Einrichtung\00_Preflight\preflight-report.txt'; $report | ConvertTo-Json -Depth 15 | Set-Content $jsonPath -Encoding UTF8; $report | Out-String -Width 240 | Set-Content $txtPath -Encoding UTF8
$report | ConvertTo-Json -Depth 15 | Set-Content 'C:\Einrichtung\state\machine-manifest.json' -Encoding UTF8
Update-State @{ current_phase=$phase; completed_phases=@($phase); skipped_phases=@(); failed_phases=@(); blocked_phases=@(); detected_tools=$commands; installed_tools=@(); system_state=$report; protected_disks=@($protected); next_recommended_phase='Gate1-Windows-Foundation' }
Write-SetupLog $phase 'Read-only system preflight' 'PowerShell' 'Preflight report written' 0 'PASS' ((Get-Date)-$started).TotalSeconds
Write-Output "PASS $phase`nReport: $jsonPath`nProtected disk: Disk $($protected.Number) $($protected.FriendlyName)"
