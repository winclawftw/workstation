# Qwen Benchmark Cleanup Report

**Zeitpunkt:** 2026-09-16 08:34 CEST  
**Aktion:** Ausschließlich PID 7496 beendet  
**Status:** COMPLETE — WAITING FOR FURTHER APPROVAL

## Authorization and scope

The user explicitly authorized termination of **only** PID 7496. No global kill command was used. No other `llama-server`, Ollama, Codex, Python or system process was terminated. No software was started automatically, and no Qwen benchmark was started.

## Pre-termination verification

PID 7496 was verified immediately before the action:

```text
Name:            llama-server.exe
PID:             7496
ExecutablePath:  C:\Einrichtung\05_AI\ollama\lib\ollama\llama-server.exe
ParentProcessId: 13216
```

Complete command line:

```text
C:\Einrichtung\05_AI\ollama\lib\ollama\llama-server.exe --model C:\Einrichtung\05_AI\models\blobs\sha256-f5f1dd8920d417aac2718b0bda3403da274301efdd6760b4f0f4b864ff2ad57d --port 53634 --host 127.0.0.1 --no-webui --offline -c 32768 -np 1 --log-verbosity 4 --no-log-prefix --no-log-timestamps --no-jinja --chat-template chatml --mmproj C:\Einrichtung\05_AI\models\blobs\sha256-ac3714bfdddeca31351f2752bf1a63f266f4df87c0b68c895e44945ca704448e --spec-type draft-mtp --spec-draft-n-max 4 --spec-draft-backend-sampling --load-mode none --flash-attn auto -b 512 -ub 512 --context-shift --keep 4
```

The Windows service query returned no service with `ProcessId = 7496`. Therefore the process was not identified as belonging to an active Windows system service.

## Controlled action

The only termination command used was the PID-specific operation:

```text
Stop-Process -Id 7496 -Confirm:$false
```

No `taskkill /IM`, wildcard, global kill or service stop was used.

## Post-termination verification

```text
PID 7496 present after termination: False
```

The remaining `llama-server.exe` PIDs were:

```text
6136, 9560, 9680, 11612, 17136, 22836, 24068, 27332
```

No new `llama-server.exe` PID appeared compared with the pre-termination snapshot.

## Resource state after cleanup

```text
System RAM free:  20,531.7 MiB / approximately 20.05 GiB
System RAM total: 31,622.0 MiB / approximately 30.88 GiB

GPU:              NVIDIA GeForce RTX 3090 Ti
VRAM free:        2,639 MiB
VRAM used:        21,671 MiB / 24,564 MiB
GPU utilization:  14 %
```

Active NVIDIA compute processes after cleanup:

```text
6136   C:\Einrichtung\05_AI\ollama\lib\ollama\llama-server.exe
9560   C:\Einrichtung\05_AI\ollama\lib\ollama\llama-server.exe
9680   C:\Einrichtung\05_AI\ollama\lib\ollama\llama-server.exe
11612  C:\Einrichtung\05_AI\ollama\lib\ollama\llama-server.exe
17136  C:\Einrichtung\05_AI\ollama\lib\ollama\llama-server.exe
22836  C:\Einrichtung\05_AI\ollama\lib\ollama\llama-server.exe
24068  C:\Einrichtung\05_AI\ollama\lib\ollama\llama-server.exe
27332  C:\Einrichtung\05_AI\ollama\lib\ollama\llama-server.exe
```

WDDM did not expose per-process GPU memory values (`N/A`) in `nvidia-smi`; aggregate GPU memory values above are authoritative for this capture.

## Final decision

- Authorized PID 7496 terminated successfully.
- No other requested process class was terminated.
- No automatic restart occurred.
- No Qwen benchmark executed.

**STATUS: WAITING FOR FURTHER USER APPROVAL**
