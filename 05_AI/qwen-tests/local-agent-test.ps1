$ErrorActionPreference = 'Stop'
$Base = 'C:\Einrichtung\05_AI\qwen-tests'
$Endpoint = "http://127.0.0.1:11434"
$ConfigPath = Join-Path $Base "config.json"
$Model = "qwen3.8:latest"
if (Test-Path $ConfigPath) { try { $Model = (ConvertFrom-Json (Get-Content $ConfigPath -Raw)).model } catch {} }

function Show-Menu {
    Clear-Host
    Write-Host "=== LOCAL AGENT TEST (3090 Ti) ===" -ForegroundColor Cyan
    Write-Host "Aktives Modell: $Model" -ForegroundColor Green
    Write-Host "1. Modell wechseln"
    Write-Host "2. GPU Status & VRAM"
    Write-Host "3. Standard-Test starten (8K Kontext)"
    Write-Host "4. Standard-Test starten (16K Kontext)"
    Write-Host "5. Code-Generator-Test starten (JSON + Code)"
    Write-Host "6. VRAM Cleaner (Modell aus VRAM werfen)"
    Write-Host "7. Beenden"
}

while ($true) {
    Show-Menu
    $opt = Read-Host "Wahl"
    switch ($opt) {
        '1' {
            $uri = '{0}/api/tags' -f $Endpoint
            $tags = Invoke-RestMethod -Uri $uri -Method Get -ErrorAction SilentlyContinue
            if ($tags.models) {
                for ($i=0; $i -lt $tags.models.Count; $i++) { Write-Host "[$i] $($tags.models[$i].name)" }
                $idx = Read-Host "Nummer"
                if ($idx -match '^\d+$' -and [int]$idx -lt $tags.models.Count) {
                    $Model = $tags.models[[int]$idx].name
                    $jsonConfig = ConvertTo-Json ([pscustomobject]@{model=$Model})
                    Set-Content -Path $ConfigPath -Value $jsonConfig -Encoding UTF8
                    Write-Host "Modell gewechselt zu: $Model" -ForegroundColor Green
                } else {
                    Write-Host "Ungültige Auswahl." -ForegroundColor Red
                }
            } else { Write-Host "Ollama offline oder keine Modelle gefunden!" -ForegroundColor Red }
            Start-Sleep 1
        }
        '2' { nvidia-smi; Read-Host "Enter" }
        { $_ -eq '3' -or $_ -eq '4' } {
            $ctx = if ($opt -eq '3') { 8192 } else { 16384 }
            $schema = @{ type="object"; properties=@{ summary=@{type="string"}; steps=@{type="array"; items=@{type="string"}}}; required=@("summary","steps"); additionalProperties=$false }
            
            $body = ConvertTo-Json -Depth 10 @{ 
                model = $Model
                prompt = "Schreibe eine kurze Zusammenfassung über Workflows und liefere genau drei kurze Einzelschritte als Array. Verwende keine Sonderzeichen, keine Listen und keine HTML-Tags."
                stream = $false
                format = $schema
                options = @{
                    num_ctx = $ctx
                    temperature = 0.3
                    repeat_penalty = 1.2
                    num_predict = 1024
                }
            }
            try {
                Write-Host "Starte Standard-Test mit $ctx Kontext für $Model..." -ForegroundColor Yellow
                $uri = '{0}/api/generate' -f $Endpoint
                $res = Invoke-RestMethod -Uri $uri -Method Post -Body $body -ContentType 'application/json' -TimeoutSec 120
                $clean = $res.response -replace '<think>[\s\S]*?</think>','' -replace '```json\s*','' -replace '```\s*',''
                $parsed = ConvertFrom-Json $clean.Trim()
                Write-Host "ERFOLG ($ctx Context): $($parsed.summary)" -ForegroundColor Green
                Write-Host "Schritte: $($parsed.steps -join ' | ')" -ForegroundColor Cyan
            } catch { Write-Host "FEHLER: $_" -ForegroundColor Red }
            Read-Host "Enter"
        }
        '5' {
            $schema = @{ 
                type = "object" 
                properties = @{
                    filename = @{ type = "string" }
                    code = @{ type = "string" }
                    explanation = @{ type = "string" }
                }
                required = @("filename", "code", "explanation")
                additionalProperties = $false 
            }
            
            $body = ConvertTo-Json -Depth 10 @{ 
                model = $Model
                prompt = "Schreibe eine kurze Python-Funktion, die einen Dateipfad entgegennimmt und prüft, ob die Datei existiert. Gib das Ergebnis im exakten JSON-Schema zurück (Dateiname, Code, Erklärung)."
                stream = $false
                format = $schema
                options = @{
                    num_ctx = 8192
                    temperature = 0.2
                    repeat_penalty = 1.1
                    num_predict = 2048
                }
            }
            try {
                Write-Host "Starte Code-Generator-Test für $Model..." -ForegroundColor Yellow
                $uri = '{0}/api/generate' -f $Endpoint
                $res = Invoke-RestMethod -Uri $uri -Method Post -Body $body -ContentType 'application/json' -TimeoutSec 120
                $clean = $res.response -replace '<think>[\s\S]*?</think>','' -replace '```json\s*','' -replace '```\s*',''
                $parsed = ConvertFrom-Json $clean.Trim()
                Write-Host "ERFOLG (Code-Test): Datei -> $($parsed.filename)" -ForegroundColor Green
                Write-Host "--- Generierter Code ---" -ForegroundColor Yellow
                Write-Host $parsed.code
                Write-Host "------------------------" -ForegroundColor Yellow
            } catch { Write-Host "FEHLER: $_" -ForegroundColor Red }
            Read-Host "Enter"
        }
        '6' {
            Write-Host "Räume VRAM auf..." -ForegroundColor Yellow
            try {
                $uriPs = '{0}/api/ps' -f $Endpoint
                $psRes = Invoke-RestMethod -Uri $uriPs -Method Get -ErrorAction SilentlyContinue
                if ($psRes.models) {
                    foreach ($m in $psRes.models) {
                        $unloadBody = ConvertTo-Json @{ model = $m.name; keep_alive = 0 }
                        $uriGen = '{0}/api/generate' -f $Endpoint
                        Invoke-RestMethod -Uri $uriGen -Method Post -Body $unloadBody -ContentType 'application/json' -ErrorAction SilentlyContinue | Out-Null
                    }
                }
            } catch {}
            Get-Process -Name "ollama_llama_server", "llama-server" -ErrorAction SilentlyContinue | Stop-Process -Force
            Write-Host "VRAM erfolgreich bereinigt!" -ForegroundColor Green
            Start-Sleep 1
        }
        '7' { exit }
    }
}
