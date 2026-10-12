# Interactive Qwen/Ollama Test

## Start

```powershell
Set-ExecutionPolicy -Scope Process Bypass
C:\Einrichtung\05_AI\qwen-tests\interactive-qwen-test.ps1
```

Syntax-/Menü-Dry-Run ohne Ollama-Anfrage:

```powershell
C:\Einrichtung\05_AI\qwen-tests\interactive-qwen-test.ps1 -DryRun
```

## Menü

1. Read-only Preflight anzeigen
2. Qwen-Ollama-8K-Test
3. 16K-Test — separate Sicherheitsbestätigung
4. 32K-Test — separate Sicherheitsbestätigung
5. Hermes — im Skript deaktiviert
6. Cleanup-Check — nur diagnostisch
7. letzten Report öffnen
8. Beenden

Nach jedem Test wird kein weiterer Test automatisch gestartet. Es gibt keine automatischen Retries.

## Sicherheitsregeln

- Endpoint: `http://127.0.0.1:11434`
- Modell: `qwen3.8:latest`
- Tests laufen seriell mit einer Anfrage.
- Vor jedem Test werden Prozesse, `nvidia-smi`, RAM, VRAM, `ollama ps`, Modelle und API-Erreichbarkeit geprüft.
- `llama-server.exe` wird angezeigt, aber standardmäßig niemals beendet.
- Codex-, Windows-, NVIDIA-, DWM-, Explorer-, Docker-, WSL- und fremde Modellprozesse werden nicht beendet.
- Unklare Prozesszuordnung verhindert den Test.
- Unter 16 GiB freiem RAM oder 20.000 MiB freiem VRAM wird nur gewarnt; es erfolgt keine automatische Bereinigung.
- Hermes, MCP, Tools, Vision, llama.cpp, LM Studio, vLLM, Docker-GPU, WSL-GPU und Gate 7 werden nicht gestartet.

## Reportpfade

Jeder Lauf erhält ein eigenes Verzeichnis:

```text
C:\Einrichtung\05_AI\qwen-tests\interactive-runs\<timestamp>\
```

Darin werden inkrementell geschrieben:

```text
preflight.json / preflight.md
runtime-samples.jsonl
response-stream.jsonl
errors.jsonl
request.json
response.json (nur bei gültigem JSON)
postflight.json / postflight.md
runtime.json
report.md
```

## Statuswerte

- `QUALIFIED_8K_GPU`: Request, JSON, Schema, GPU-Nachweis, Preflight und Postflight bestanden.
- `CONDITIONAL_8K`: Request erfolgreich, aber CPU-Offload oder knappe Ressourcen.
- `INVALID_MODEL_RESPONSE`: Antwort fehlt, ist ungültig oder nicht schema-konform.
- `OLLAMA_UNAVAILABLE`: lokale API nicht erreichbar.
- `MODEL_NOT_FOUND`: Modell nicht verfügbar.
- `OUT_OF_MEMORY`: Speicher- oder GPU-Speicherfehler.
- `CLIENT_ERROR`: Client-/Transportfehler.
- `DIRTY_STATE`: unerwarteter oder unklarer Prozesszustand.

## Manuelle Cleanup-Anleitung

Das Skript beendet standardmäßig keine Prozesse. Prüfe zuerst den letzten `postflight.json`- und `report.md`-Status. Bei einem verbleibenden `llama-server.exe` oder geladenen Modell:

1. PID, Parent-PID, ExecutablePath und CommandLine dokumentieren.
2. Zugehörigkeit zum konkreten Test eindeutig bestätigen.
3. Nur nach ausdrücklicher Benutzerfreigabe einen PID-spezifischen Cleanup durchführen.
4. Niemals globale Kill-Befehle oder Prozessnamen-Wildcards verwenden.

## Weitere Grenzen

Das Skript ändert keine Keystone-, Hermes-, Ollama-Modell-, WSL-, Docker-, Treiber-, BIOS-, Registry- oder Firewall-Konfiguration. Es lädt kein Modell automatisch herunter und führt keine automatische Wiederholung aus.
