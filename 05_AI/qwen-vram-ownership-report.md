# Qwen VRAM Ownership Report

**Zeitpunkt:** 2026-09-16 08:36 CEST  
**Modus:** Read-only diagnostic  
**Status:** COMPLETE — WAITING FOR EXPLICIT APPROVAL

## Safety

- Keine Prozessbeendigung durchgeführt.
- Keine Dienste gestartet.
- Kein Benchmark gestartet.
- Keine Modell-, Konfigurations- oder Pfadänderung durchgeführt.

## NVIDIA summary

```text
GPU:              NVIDIA GeForce RTX 3090 Ti
Driver:           591.86
CUDA:             13.1
Driver model:     WDDM
VRAM total:       24,564 MiB
VRAM used:        21,808 MiB
VRAM free:        2,502 MiB
GPU utilization:  12 %
```

`nvidia-smi` lists the active processes, but WDDM reports `N/A` for the per-process GPU-memory column. The aggregate 21,808 MiB is therefore measurable, while an exact split by PID is not exposed by this capture.

## Active GPU processes

The following processes were listed by `nvidia-smi`. All entries reported `VRAM: N/A` at per-process level.

| PID | Process | VRAM reported | CommandLine / executable evidence |
|---:|---|---|---|
| 1980 | `dwm.exe` | N/A | CommandLine unavailable; Windows Desktop Window Manager |
| 4996 | `ShellHost.exe` | N/A | `C:\Windows\System32\ShellHost.exe` |
| 18312 | `explorer.exe` | N/A | `C:\WINDOWS\Explorer.EXE` |
| 17700 | `CrossDeviceResume.exe` | N/A | Windows system app, CrossDeviceResume |
| 18212 | `StartMenuExperienceHost.exe` | N/A | Windows Start Menu system app |
| 4256 | `SearchHost.exe` | N/A | Windows Search system app |
| 19612 | `msedgewebview2.exe` | N/A | WebView2 GPU process |
| 18448 | `WidgetBoard.exe` | N/A | Windows Widget Board |
| 25504 | `WindowsTerminal.exe` | N/A | CommandLine unavailable due permissions |
| 19336 | `TextInputHost.exe` | N/A | Windows text input system app |
| 3224 | `ShellExperienceHost.exe` | N/A | Windows shell system app |
| 1532 | `ChatGPT.exe` | N/A | OpenAI Codex desktop GPU process (`ChatGPT.exe --type=gpu-process ...`) |
| 16428 | `codex-computer-use-swift.exe` | N/A | `...codex-computer-use-swift.exe --parent-pid 4016` |
| 9680 | `llama-server.exe` | N/A | Native Ollama runtime, port 58360 |
| 27332 | `llama-server.exe` | N/A | Native Ollama runtime, port 60449 |
| 9560 | `llama-server.exe` | N/A | Native Ollama runtime, port 58742 |
| 22836 | `llama-server.exe` | N/A | Native Ollama runtime, port 64641 |
| 11612 | `llama-server.exe` | N/A | Native Ollama runtime, port 50558 |
| 17136 | `llama-server.exe` | N/A | Native Ollama runtime, port 63581 |
| 6136 | `llama-server.exe` | N/A | Native Ollama runtime, port 57896 |
| 24068 | `llama-server.exe` | N/A | Native Ollama runtime, port 59200 |
| 15268 | `SnippingTool.exe` | N/A | Windows Snipping Tool |
| 9324 | `Taskmgr.exe` | N/A | CommandLine unavailable due permissions |
| 27352 | `msedge.exe` | N/A | Microsoft Edge GPU process |

## Target ownership checks

### `llama-server.exe`

Eight active native Windows `llama-server.exe` processes were found in the NVIDIA process list:

```text
6136, 9560, 9680, 11612, 17136, 22836, 24068, 27332
```

All executable paths resolve to:

```text
C:\Einrichtung\05_AI\ollama\lib\ollama\llama-server.exe
```

They are the strongest identifiable compute candidates for the large aggregate VRAM allocation. Exact per-instance MiB cannot be established because WDDM returns `N/A`.

### `ollama.exe`

No active `ollama.exe` process appeared in the GPU process list or the target-process inspection.

### `codex.exe` and `codex-code-mode-host`

The main `codex.exe` process and `codex-code-mode-host.exe` were present in the Windows process table, but neither appeared in the NVIDIA GPU process list. The Codex desktop GPU subprocess appears as `ChatGPT.exe` PID 1532, with per-process VRAM reported as `N/A`.

### `python.exe`, Docker/WSL, `lmstudio`, `vllm`

No matching active GPU process was found for:

```text
python.exe
docker.exe / com.docker / containerd
WSL Linux workloads
lmstudio
vllm
```

WSL was stopped at the time of inspection. Docker was not available in the current Windows `PATH`, and no Docker host process was observed.

## Windows Desktop Window Manager

`dwm.exe` was present as NVIDIA PID 1980:

```text
Name:            dwm.exe
PID:             1980
Working set:     approximately 66 MiB
Per-process VRAM: N/A under WDDM
```

Therefore DWM participates in the GPU process list, but this diagnostic cannot quantify how much of the 21,808 MiB aggregate it owns. The observed DWM working set does not itself represent VRAM usage.

## Ownership conclusion

The NVIDIA driver reports 21,808 MiB used and 2,502 MiB free. The process list shows eight active `llama-server.exe` CUDA processes and ordinary Windows graphics processes. `nvidia-smi` does **not** expose per-PID VRAM amounts in this WDDM configuration, so the total cannot be apportioned exactly among the llama servers, DWM, Codex desktop GPU process and other Windows graphics processes.

The evidence supports `llama-server.exe` as the principal identifiable compute owner, but does not prove an exact per-process VRAM allocation. No Ollama daemon, Python, Docker/WSL, LM Studio or vLLM GPU owner was found.

**STATUS: WAITING FOR EXPLICIT USER APPROVAL**
