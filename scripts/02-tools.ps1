[CmdletBinding()] param()
. "$PSScriptRoot\common.ps1"
$phase='Gate2-Developer-Tools'; $started=Get-Date; Assert-ProtectedDiskReadOnly | Out-Null
$env:Path=[Environment]::GetEnvironmentVariable('Path','Machine')+';'+[Environment]::GetEnvironmentVariable('Path','User')
$packages=@(
 @{name='PowerShell 7'; id='Microsoft.PowerShell'; command='pwsh'},
 @{name='Git'; id='Git.Git'; command='git'},
 @{name='Git LFS'; id='GitHub.GitLFS'; command='git-lfs'},
 @{name='Python'; id='Python.Python.3.12'; command='python'},
 @{name='Node.js LTS'; id='OpenJS.NodeJS.LTS'; command='node'},
 @{name='Visual Studio Code'; id='Microsoft.VisualStudioCode'; command='code'},
 @{name='7-Zip'; id='7zip.7zip'; command='7z'},
 @{name='FFmpeg'; id='Gyan.FFmpeg.Shared'; command='ffmpeg'}
)
$results=@(); $failed=@(); $skipped=@(); $installed=@()
foreach($p in $packages){
  $before=Get-SafeCommandVersion $p.command
  if($p.command -eq 'git-lfs'){ try{$before=(git lfs version 2>&1 | Out-String).Trim()}catch{$before=$null} }
  if($before){ $skipped += $p.name; $results += [pscustomobject]@{name=$p.name;status='SKIPPED';before=$before;after=$before}; continue }
  $search=winget search --id $p.id --exact --accept-source-agreements 2>&1 | Out-String
  if($LASTEXITCODE -ne 0 -or $search -notmatch [regex]::Escape($p.id)){ $failed += $p.name; $results += [pscustomobject]@{name=$p.name;status='BLOCKED';reason='winget package identity not found or could not be verified';search=$search.Trim()}; continue }
  $out=winget install --id $p.id --exact --silent --accept-package-agreements --accept-source-agreements 2>&1 | Out-String; $code=$LASTEXITCODE; $env:Path=[Environment]::GetEnvironmentVariable('Path','Machine')+';'+[Environment]::GetEnvironmentVariable('Path','User'); $after=Get-SafeCommandVersion $p.command
  if($p.command -eq 'git-lfs'){ try{$after=(git lfs version 2>&1 | Out-String).Trim()}catch{$after=$null} }
  if($code -eq 0 -and $after){$st='PASS';$installed+=$p.name}else{$st='FAILED';$failed+=$p.name; Write-DebugReport $phase "Installation failed: $($p.name)" 'Review package output and rerun this phase after resolving the installer issue.' $out | Out-Null}
  $results += [pscustomobject]@{name=$p.name;status=$st;exit_code=$code;before=$before;after=$after;output=$out.Trim()}
  Write-SetupLog $phase "Install/check $($p.name)" 'winget' ($out.Trim()) $code $st 0
}
$gitUser=git config --global user.name 2>$null; $gitEmail=git config --global user.email 2>$null
$confirmed=@($results | Where-Object { $_.status -in @('PASS','SKIPPED') } | Select-Object -ExpandProperty name)
$summary=[ordered]@{timestamp=(Get-Date).ToString('o');phase=$phase;results=$results;skipped=$skipped;installed=$installed;confirmed=$confirmed;failed=$failed;git_user_configuration_required=([string]::IsNullOrWhiteSpace($gitUser) -or [string]::IsNullOrWhiteSpace($gitEmail))}
$summary | ConvertTo-Json -Depth 8 | Set-Content 'C:\Einrichtung\02_Tools\tools-report.json' -Encoding UTF8
Update-State @{ current_phase=$phase; completed_phases=@('Gate0-Preflight','Gate1-Windows-Foundation',$phase); installed_tools=$confirmed; detected_tools=@{ git=(Get-SafeCommandVersion git); python=(Get-SafeCommandVersion python); node=(Get-SafeCommandVersion node); pwsh=(Get-SafeCommandVersion pwsh); code=(Get-SafeCommandVersion code); ffmpeg=(Get-SafeCommandVersion ffmpeg); sevenzip=(Get-SafeCommandVersion 7z) }; failed_phases=if($failed.Count -gt 0){@($phase)}else{@()}; next_recommended_phase='Gate3-WSL2 (explicit activation required)' }
Write-Output "KEYSTONE WORKSTATION SETUP`nCurrent Gate: $phase`nPASS: $($installed -join ', ')`nSKIPPED: $($skipped -join ', ')`nBLOCKED/FAILED: $($failed -join ', ')`nProtected Disk: PASS`nNext Gate: Gate3-WSL2 (not automatically executed)"
