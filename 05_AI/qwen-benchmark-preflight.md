# Qwen Benchmark Preflight

**Erstellt:** 2026-09-16 08:30 CEST  
**Modus:** Read-only diagnostics  
**Status:** COMPLETE — WAITING FOR EXPLICIT USER APPROVAL

## Scope and safety

- Kein neuer Qwen-Benchmark wurde gestartet.
- Kein Prozess wurde beendet oder pausiert.
- Kein Dienst wurde gestartet.
- Keine Modell-, Konfigurations- oder Pfadänderung wurde vorgenommen.
- Die ADATA SX8200PNP / Disk 1 wurde nicht verändert.

## Target processes

Erfasst wurden Prozesse mit den Namen `ollama`, `llama-server`, `hermes`, `codex`, `python`, `lmstudio` und `vllm` (Windows-Prozessabfrage via WMI/CIM). RAM ist der Working Set zum Abfragezeitpunkt. Ports sind die dem PID zugeordneten TCP-Listener bzw. Verbindungen.

| Name | PID | RAM | CommandLine | Parent PID | Port |
|---|---:|---:|---|---:|---|
| codex.exe | 27028 | 116.3 MiB | `C:\Users\mgard\AppData\Local\OpenAI\Codex\bin\12219cbfbcbddde7\codex.exe -c features.code_mode_host=true app-server --analytics-default-enabled -c plugins.codex-app-tools@openai-bundled.mcp_servers.codex_app.enabled=true` | 4016 | TCP 0.0.0.0:55241 (Bound); TCP 0.0.0.0:51202 (Bound); TCP 0.0.0.0:50181 (Bound); outbound HTTPS connections |
| llama-server.exe | 9680 | 3.6 MiB | `C:\Einrichtung\05_AI\ollama\lib\ollama\llama-server.exe --model ...sha256-2af3b81862c6be03c769683af18efdadb2c33f60ff32ab6f83e42c043d6c7816 --port 58360 --host 127.0.0.1 --no-webui --offline -c 2048 -np 1 ...` | 15528 (not present) | TCP 127.0.0.1:58360 LISTEN |
| llama-server.exe | 27332 | 4.0 MiB | `C:\Einrichtung\05_AI\ollama\lib\ollama\llama-server.exe --model ...sha256-dde5aa3fc5ffc17176b5e8bdc82f587b24b2678c6c66101bf7da77af9f7ccdff --port 60449 --host 127.0.0.1 --no-webui --offline -c 32768 -np 1 ...` | 15528 (not present) | TCP 127.0.0.1:60449 LISTEN |
| llama-server.exe | 9560 | 4.0 MiB | `C:\Einrichtung\05_AI\ollama\lib\ollama\llama-server.exe --model ...sha256-dde5aa3fc5ffc17176b5e8bdc82f587b24b2678c6c66101bf7da77af9f7ccdff --port 58742 --host 127.0.0.1 --no-webui --offline -c 32768 -np 1 ...` | 23168 (not present) | TCP 127.0.0.1:58742 LISTEN |
| llama-server.exe | 22836 | 3.9 MiB | `C:\Einrichtung\05_AI\ollama\lib\ollama\llama-server.exe --model ...sha256-dde5aa3fc5ffc17176b5e8bdc82f587b24b2678c6c66101bf7da77af9f7ccdff --port 64641 --host 127.0.0.1 --no-webui --offline -c 32768 -np 1 ...` | 22260 (not present) | TCP 127.0.0.1:64641 LISTEN |
| llama-server.exe | 11612 | 3.8 MiB | `C:\Einrichtung\05_AI\ollama\lib\ollama\llama-server.exe --model ...sha256-dde5aa3fc5ffc17176b5e8bdc82f587b24b2678c6c66101bf7da77af9f7ccdff --port 50558 --host 127.0.0.1 --no-webui --offline -c 32768 -np 1 ...` | 11012 (not present) | TCP 127.0.0.1:50558 LISTEN |
| llama-server.exe | 17136 | 303.8 MiB | `C:\Einrichtung\05_AI\ollama\lib\ollama\llama-server.exe --model ...sha256-dde5aa3fc5ffc17176b5e8bdc82f587b24b2678c6c66101bf7da77af9f7ccdff --port 63581 --host 127.0.0.1 --no-webui --offline -c 32768 -np 1 ...` | 8876 (not present) | TCP 127.0.0.1:63581 LISTEN |
| llama-server.exe | 6136 | 4.6 MiB | `C:\Einrichtung\05_AI\ollama\lib\ollama\llama-server.exe --model ...sha256-dde5aa3fc5ffc17176b5e8bdc82f587b24b2678c6c66101bf7da77af9f7ccdff --port 57896 --host 127.0.0.1 --no-webui --offline -c 32768 -np 1 ...` | 20332 (not present) | TCP 127.0.0.1:57896 LISTEN |
| llama-server.exe | 24068 | 4.7 MiB | `C:\Einrichtung\05_AI\ollama\lib\ollama\llama-server.exe --model ...sha256-f5f1dd8920d417aac2718b0bda3403da274301efdd6760b4f0f4b864ff2ad57d --port 59200 --host 127.0.0.1 --no-webui --offline -c 65536 -np 1 ...` | 23868 (not present) | TCP 127.0.0.1:59200 LISTEN |
| llama-server.exe | 7496 | **17,611.5 MiB** | `C:\Einrichtung\05_AI\ollama\lib\ollama\llama-server.exe --model ...sha256-f5f1dd8920d417aac2718b0bda3403da274301efdd6760b4f0f4b864ff2ad57d --port 53634 --host 127.0.0.1 --no-webui --offline -c 32768 -np 1 ...` | 13216 (not present) | TCP 127.0.0.1:53634 LISTEN |

No matching process was found for `ollama.exe`, `hermes`, `python`, `lmstudio` or `vllm` at the time of capture.

The ellipses in the table shorten repeated command-line options only for readability. The decisive model path, port, host and context arguments are retained above; the complete command lines were observed in the diagnostic output.

### Complete llama-server command lines

```text
PID 9680: C:\Einrichtung\05_AI\ollama\lib\ollama\llama-server.exe --model C:\Einrichtung\05_AI\models\blobs\sha256-2af3b81862c6be03c769683af18efdadb2c33f60ff32ab6f83e42c043d6c7816 --port 58360 --host 127.0.0.1 --no-webui --offline -c 2048 -np 1 --log-verbosity 4 --no-log-prefix --no-log-timestamps --no-jinja --chat-template chatml --load-mode none --flash-attn auto -b 512 -ub 512 --context-shift --keep 4
PID 27332: C:\Einrichtung\05_AI\ollama\lib\ollama\llama-server.exe --model C:\Einrichtung\05_AI\models\blobs\sha256-dde5aa3fc5ffc17176b5e8bdc82f587b24b2678c6c66101bf7da77af9f7ccdff --port 60449 --host 127.0.0.1 --no-webui --offline -c 32768 -np 1 --log-verbosity 4 --no-log-prefix --no-log-timestamps --no-jinja --chat-template chatml --load-mode none --flash-attn auto -b 1024 -ub 1024 --context-shift --keep 4
PID 9560: C:\Einrichtung\05_AI\ollama\lib\ollama\llama-server.exe --model C:\Einrichtung\05_AI\models\blobs\sha256-dde5aa3fc5ffc17176b5e8bdc82f587b24b2678c6c66101bf7da77af9f7ccdff --port 58742 --host 127.0.0.1 --no-webui --offline -c 32768 -np 1 --log-verbosity 4 --no-log-prefix --no-log-timestamps --no-jinja --chat-template chatml --load-mode none --flash-attn auto -b 1024 -ub 1024 --context-shift --keep 4
PID 22836: C:\Einrichtung\05_AI\ollama\lib\ollama\llama-server.exe --model C:\Einrichtung\05_AI\models\blobs\sha256-dde5aa3fc5ffc17176b5e8bdc82f587b24b2678c6c66101bf7da77af9f7ccdff --port 64641 --host 127.0.0.1 --no-webui --offline -c 32768 -np 1 --log-verbosity 4 --no-log-prefix --no-log-timestamps --no-jinja --chat-template chatml --load-mode none --flash-attn auto -b 1024 -ub 1024 --context-shift --keep 4
PID 11612: C:\Einrichtung\05_AI\ollama\lib\ollama\llama-server.exe --model C:\Einrichtung\05_AI\models\blobs\sha256-dde5aa3fc5ffc17176b5e8bdc82f587b24b2678c6c66101bf7da77af9f7ccdff --port 50558 --host 127.0.0.1 --no-webui --offline -c 32768 -np 1 --log-verbosity 4 --no-log-prefix --no-log-timestamps --no-jinja --chat-template chatml --load-mode none --flash-attn auto -b 1024 -ub 1024 --context-shift --keep 4
PID 17136: C:\Einrichtung\05_AI\ollama\lib\ollama\llama-server.exe --model C:\Einrichtung\05_AI\models\blobs\sha256-dde5aa3fc5ffc17176b5e8bdc82f587b24b2678c6c66101bf7da77af9f7ccdff --port 63581 --host 127.0.0.1 --no-webui --offline -c 32768 -np 1 --log-verbosity 4 --no-log-prefix --no-log-timestamps --no-jinja --chat-template chatml --load-mode none --flash-attn auto -b 512 -ub 512 --context-shift --keep 4
PID 6136: C:\Einrichtung\05_AI\ollama\lib\ollama\llama-server.exe --model C:\Einrichtung\05_AI\models\blobs\sha256-dde5aa3fc5ffc17176b5e8bdc82f587b24b2678c6c66101bf7da77af9f7ccdff --port 57896 --host 127.0.0.1 --no-webui --offline -c 32768 -np 1 --log-verbosity 4 --no-log-prefix --no-log-timestamps --no-jinja --chat-template chatml --load-mode none --flash-attn auto -b 512 -ub 512 --context-shift --keep 4
PID 24068: C:\Einrichtung\05_AI\ollama\lib\ollama\llama-server.exe --model C:\Einrichtung\05_AI\models\blobs\sha256-f5f1dd8920d417aac2718b0bda3403da274301efdd6760b4f0f4b864ff2ad57d --port 59200 --host 127.0.0.1 --no-webui --offline -c 65536 -np 1 --log-verbosity 4 --no-log-prefix --no-log-timestamps --no-jinja --chat-template chatml --mmproj C:\Einrichtung\05_AI\models\blobs\sha256-ac3714bfdddeca31351f2752bf1a63f266f4df87c0b68c895e44945ca704448e --spec-type draft-mtp --spec-draft-n-max 4 --spec-draft-backend-sampling --load-mode none --flash-attn auto -b 512 -ub 512 --context-shift --keep 4
PID 7496: C:\Einrichtung\05_AI\ollama\lib\ollama\llama-server.exe --model C:\Einrichtung\05_AI\models\blobs\sha256-f5f1dd8920d417aac2718b0bda3403da274301efdd6760b4f0f4b864ff2ad57d --port 53634 --host 127.0.0.1 --no-webui --offline -c 32768 -np 1 --log-verbosity 4 --no-log-prefix --no-log-timestamps --no-jinja --chat-template chatml --mmproj C:\Einrichtung\05_AI\models\blobs\sha256-ac3714bfdddeca31351f2752bf1a63f266f4df87c0b68c895e44945ca704448e --spec-type draft-mtp --spec-draft-n-max 4 --spec-draft-backend-sampling --load-mode none --flash-attn auto -b 512 -ub 512 --context-shift --keep 4
```

## Ollama

Command executed:

```text
C:\Einrichtung\05_AI\ollama\ollama.exe ps
```

Result:

```text
Error: Head "http://127.0.0.1:11434/": dial tcp 127.0.0.1:11434: connectex: Es konnte keine Verbindung hergestellt werden, da der Zielcomputer die Verbindung verweigerte.
```

Conclusion: no reachable Ollama API/daemon on the default local endpoint. The visible `llama-server.exe` processes are child/runtime processes from the Ollama installation path, but the owning Ollama daemon process was not present in the process-name query.

## NVIDIA / GPU

`nvidia-smi` reported:

```text
GPU: NVIDIA GeForce RTX 3090 Ti
Driver: 591.86
CUDA: 13.1
Driver model: WDDM
GPU memory: 23716 MiB / 24564 MiB used
GPU memory free: 594 MiB
GPU utilization: 17–19 %
```

GPU compute-process listing included these native Windows AI processes:

```text
PID 6136   C:\Einrichtung\05_AI\ollama\lib\ollama\llama-server.exe
PID 7496   C:\Einrichtung\05_AI\ollama\lib\ollama\llama-server.exe
PID 9560   C:\Einrichtung\05_AI\ollama\lib\ollama\llama-server.exe
PID 9680   C:\Einrichtung\05_AI\ollama\lib\ollama\llama-server.exe
PID 11612  C:\Einrichtung\05_AI\ollama\lib\ollama\llama-server.exe
PID 17136  C:\Einrichtung\05_AI\ollama\lib\ollama\llama-server.exe
PID 22836  C:\Einrichtung\05_AI\ollama\lib\ollama\llama-server.exe
PID 24068  C:\Einrichtung\05_AI\ollama\lib\ollama\llama-server.exe
PID 27332  C:\Einrichtung\05_AI\ollama\lib\ollama\llama-server.exe
```

NVIDIA did not expose per-process memory in this WDDM capture (`N/A`), but the aggregate GPU memory is clear.

## System RAM

Windows reported:

```text
Total visible RAM: 32,380,892 KiB = approximately 30.88 GiB
Free RAM:          3,914,252 KiB  = approximately 3.73 GiB
Used RAM:          approximately 27.15 GiB
```

## WSL / Docker GPU processes

WSL status:

```text
Default distribution: Ubuntu-24.04
Default version: 2
Ubuntu-24.04: Stopped
```

No WSL Linux process listing was started because the distribution was already stopped; the diagnostic therefore did not start WSL merely to inspect it. Host-side related processes observed were `wslservice.exe` and `vmmemCmZygote`, with no active WSL Linux workload identified.

Docker checks:

```text
docker: The term 'docker' is not recognized as a name of a cmdlet, function, script file, or executable program.
```

No Docker CLI or Docker GPU workload was identifiable from the current Windows environment. No Docker process/container was observed in the host process filter.

## Origin of the large `llama-server`

Large process:

```text
PID: 7496
RAM: 17,611.5 MiB
Port: 127.0.0.1:53634
Model blob: sha256-f5f1dd8920d417aac2718b0bda3403da274301efdd6760b4f0f4b864ff2ad57d
Parent PID: 13216
```

The parent PID `13216` was no longer present when inspected. The same was true for the parent PIDs of the other `llama-server.exe` instances. Therefore the current process table cannot identify the original starter executable with evidence. The executable path establishes that this is a native Windows runtime from the Ollama installation, but the exact historical launcher/parent is **NOT IDENTIFIED** from the live process tree.

## Decision

- No new Qwen benchmark executed.
- No process terminated.
- No migration or optimization performed.
- Current resource state is unsuitable for starting another heavy Qwen benchmark without explicit review: approximately 3.73 GiB system RAM and 594 MiB VRAM are free.
- WSL is not participating in the observed workload; the active `llama-server` processes are native Windows processes using Windows paths.

**STATUS: WAITING FOR EXPLICIT USER APPROVAL**
