# Qwen VRAM Cleanup Report

**Zeitpunkt:** 2026-09-16 08:39 CEST  
**Aktion:** Ausschließlich die acht autorisierten `llama-server.exe`-PIDs beendet  
**Status:** COMPLETE — WAITING FOR FURTHER APPROVAL

## Scope and safety

- Keine globalen Kill-Befehle verwendet.
- Keine Ollama-, Codex-, Windows-, Docker-, WSL- oder NVIDIA-Prozesse beendet.
- Keine Dienste automatisch gestartet.
- Kein Qwen-Benchmark gestartet.

## Pre-termination verification

Alle acht im `qwen-vram-ownership-report.md` dokumentierten PIDs existierten noch und wurden einzeln verifiziert. Jede PID hatte exakt den Prozessnamen `llama-server.exe` und den ExecutablePath:

```text
C:\Einrichtung\05_AI\ollama\lib\ollama\llama-server.exe
```

| PID | ParentProcessId | Port | Verifikation |
|---:|---:|---:|---|
| 6136 | 20332 | 57896 | PASS |
| 9560 | 23168 | 58742 | PASS |
| 9680 | 15528 | 58360 | PASS |
| 11612 | 11012 | 50558 | PASS |
| 17136 | 8876 | 63581 | PASS |
| 22836 | 22260 | 64641 | PASS |
| 24068 | 23868 | 59200 | PASS |
| 27332 | 15528 | 60449 | PASS |

### Verified command lines

```text
PID 6136: C:\Einrichtung\05_AI\ollama\lib\ollama\llama-server.exe --model C:\Einrichtung\05_AI\models\blobs\sha256-dde5aa3fc5ffc17176b5e8bdc82f587b24b2678c6c66101bf7da77af9f7ccdff --port 57896 --host 127.0.0.1 --no-webui --offline -c 32768 -np 1 --log-verbosity 4 --no-log-prefix --no-log-timestamps --no-jinja --chat-template chatml --load-mode none --flash-attn auto -b 512 -ub 512 --context-shift --keep 4
PID 9560: C:\Einrichtung\05_AI\ollama\lib\ollama\llama-server.exe --model C:\Einrichtung\05_AI\models\blobs\sha256-dde5aa3fc5ffc17176b5e8bdc82f587b24b2678c6c66101bf7da77af9f7ccdff --port 58742 --host 127.0.0.1 --no-webui --offline -c 32768 -np 1 --log-verbosity 4 --no-log-prefix --no-log-timestamps --no-jinja --chat-template chatml --load-mode none --flash-attn auto -b 1024 -ub 1024 --context-shift --keep 4
PID 9680: C:\Einrichtung\05_AI\ollama\lib\ollama\llama-server.exe --model C:\Einrichtung\05_AI\models\blobs\sha256-2af3b81862c6be03c769683af18efdadb2c33f60ff32ab6f83e42c043d6c7816 --port 58360 --host 127.0.0.1 --no-webui --offline -c 2048 -np 1 --log-verbosity 4 --no-log-prefix --no-log-timestamps --no-jinja --chat-template chatml --load-mode none --flash-attn auto -b 512 -ub 512 --context-shift --keep 4
PID 11612: C:\Einrichtung\05_AI\ollama\lib\ollama\llama-server.exe --model C:\Einrichtung\05_AI\models\blobs\sha256-dde5aa3fc5ffc17176b5e8bdc82f587b24b2678c6c66101bf7da77af9f7ccdff --port 50558 --host 127.0.0.1 --no-webui --offline -c 32768 -np 1 --log-verbosity 4 --no-log-prefix --no-log-timestamps --no-jinja --chat-template chatml --load-mode none --flash-attn auto -b 1024 -ub 1024 --context-shift --keep 4
PID 17136: C:\Einrichtung\05_AI\ollama\lib\ollama\llama-server.exe --model C:\Einrichtung\05_AI\models\blobs\sha256-dde5aa3fc5ffc17176b5e8bdc82f587b24b2678c6c66101bf7da77af9f7ccdff --port 63581 --host 127.0.0.1 --no-webui --offline -c 32768 -np 1 --log-verbosity 4 --no-log-prefix --no-log-timestamps --no-jinja --chat-template chatml --load-mode none --flash-attn auto -b 512 -ub 512 --context-shift --keep 4
PID 22836: C:\Einrichtung\05_AI\ollama\lib\ollama\llama-server.exe --model C:\Einrichtung\05_AI\models\blobs\sha256-dde5aa3fc5ffc17176b5e8bdc82f587b24b2678c6c66101bf7da77af9f7ccdff --port 64641 --host 127.0.0.1 --no-webui --offline -c 32768 -np 1 --log-verbosity 4 --no-log-prefix --no-log-timestamps --no-jinja --chat-template chatml --load-mode none --flash-attn auto -b 1024 -ub 1024 --context-shift --keep 4
PID 24068: C:\Einrichtung\05_AI\ollama\lib\ollama\llama-server.exe --model C:\Einrichtung\05_AI\models\blobs\sha256-f5f1dd8920d417aac2718b0bda3403da274301efdd6760b4f0f4b864ff2ad57d --port 59200 --host 127.0.0.1 --no-webui --offline -c 65536 -np 1 --log-verbosity 4 --no-log-prefix --no-log-timestamps --no-jinja --chat-template chatml --mmproj C:\Einrichtung\05_AI\models\blobs\sha256-ac3714bfdddeca31351f2752bf1a63f266f4df87c0b68c895e44945ca704448e --spec-type draft-mtp --spec-draft-n-max 4 --spec-draft-backend-sampling --load-mode none --flash-attn auto -b 512 -ub 512 --context-shift --keep 4
PID 27332: C:\Einrichtung\05_AI\ollama\lib\ollama\llama-server.exe --model C:\Einrichtung\05_AI\models\blobs\sha256-dde5aa3fc5ffc17176b5e8bdc82f587b24b2678c6c66101bf7da77af9f7ccdff --port 60449 --host 127.0.0.1 --no-webui --offline -c 32768 -np 1 --log-verbosity 4 --no-log-prefix --no-log-timestamps --no-jinja --chat-template chatml --load-mode none --flash-attn auto -b 1024 -ub 1024 --context-shift --keep 4
```

No additional `llama-server.exe` process outside this authorized set was present before the action.

## Controlled termination

Each authorized PID was passed individually to a PID-specific `Stop-Process` operation. No process-name wildcard or global process termination was used.

## Post-termination verification

```text
Remaining llama-server.exe processes: 0
Automatic new llama-server.exe processes: none observed
```

## NVIDIA state after cleanup

```text
GPU:              NVIDIA GeForce RTX 3090 Ti
VRAM total:       24,564 MiB
VRAM used:        1,006 MiB
VRAM free:        23,304 MiB
GPU utilization:  13 %
```

`nvidia-smi` showed only ordinary Windows graphics processes after cleanup, including ChatGPT/Codex desktop GPU, shell components, Explorer, Edge/WebView, Snipping Tool and related desktop processes. No `llama-server.exe` remained in the NVIDIA process list.

## System RAM after cleanup

```text
Free RAM:   24,293.1 MiB / approximately 23.72 GiB
Total RAM:  31,622.0 MiB / approximately 30.88 GiB
```

**STATUS: WAITING FOR FURTHER USER APPROVAL**
