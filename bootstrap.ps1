[CmdletBinding()] param([ValidateSet('Preflight','System','Tools','WSL','Docker','AI','Hermes','Keystone')][string]$Phase='Preflight')
$root='C:\Einrichtung\scripts'
switch($Phase){
 'Preflight' { & (Join-Path $root '00-preflight.ps1') }
 'System' { & (Join-Path $root '01-system.ps1') }
 'Tools' { & (Join-Path $root '02-tools.ps1') }
 default { Write-Output "Phase $Phase is intentionally not enabled by default. Prepare/document only; explicit implementation is required." }
}
