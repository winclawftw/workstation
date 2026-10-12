[CmdletBinding()]
param()
$ErrorActionPreference='Continue'
$LogRoot='C:\Einrichtung\03_WSL'
New-Item -ItemType Directory -Force -Path $LogRoot | Out-Null
$LogFile=Join-Path $LogRoot 'wsl-precheck.txt'
"=== WSL PRECHECK $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') ===" | Set-Content -LiteralPath $LogFile -Encoding UTF8
function Add-Section { param([string]$Title,[scriptblock]$Action)
    "`n--- $Title ---" | Add-Content -LiteralPath $LogFile -Encoding UTF8
    try { (& $Action 2>&1 | Out-String).Trim() | Add-Content -LiteralPath $LogFile -Encoding UTF8 } catch { "ERROR: $($_.Exception.Message)" | Add-Content -LiteralPath $LogFile -Encoding UTF8 }
}
Add-Section 'CURRENT WINDOWS' { Get-CimInstance Win32_OperatingSystem | Select-Object Caption,Version,BuildNumber,OSArchitecture,SystemDrive,WindowsDirectory,InstallDate | Format-List }
Add-Section 'WINDOWS REGISTRY IDENTITY' { Get-ItemProperty 'HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion' | Select-Object ProductName,DisplayVersion,EditionID,CurrentBuild,CurrentBuildNumber,UBR | Format-List }
Add-Section 'ACTIVE SYSTEM DISK' { Get-Partition -DriveLetter $env:SystemDrive.TrimEnd(':') | Select-Object DiskNumber,PartitionNumber,DriveLetter,Type,Size | Format-List; Get-Disk | Select-Object Number,FriendlyName,SerialNumber,Size,IsBoot,IsSystem,OperationalStatus | Format-Table -AutoSize }
Add-Section 'WSL VERSION' { wsl --version }
Add-Section 'WSL STATUS' { wsl --status }
Add-Section 'INSTALLED DISTRIBUTIONS' { wsl --list --verbose }
Add-Section 'AVAILABLE DISTRIBUTIONS' { wsl --list --online }
Add-Section 'WINDOWS OPTIONAL FEATURE: WSL' { try { Get-WindowsOptionalFeature -Online -FeatureName 'Microsoft-Windows-Subsystem-Linux' -ErrorAction Stop | Select-Object FeatureName,State | Format-List } catch { "UNAVAILABLE: $($_.Exception.Message)" } }
Add-Section 'WINDOWS OPTIONAL FEATURE: VIRTUALMACHINEPLATFORM' { try { Get-WindowsOptionalFeature -Online -FeatureName 'VirtualMachinePlatform' -ErrorAction Stop | Select-Object FeatureName,State | Format-List } catch { "UNAVAILABLE: $($_.Exception.Message)" } }
Add-Section '7-ZIP LOCAL CHECK' { if(Test-Path 'C:\Program Files\7-Zip\7z.exe'){Get-Item 'C:\Program Files\7-Zip\7z.exe' | Select-Object FullName,Length,LastWriteTime}else{'MISSING'} }
Add-Content -LiteralPath $LogFile -Value "`nLog: $LogFile" -Encoding UTF8
Write-Output "Precheck written: $LogFile"
