# Workstation Setup

This file is maintained by the bootstrap scripts. No credentials or secrets are recorded.

## Operating rules

- Setup root: `C:\Einrichtung`
- Primary system disk: detected from the read-only preflight.
- The protected 1-TB disk is read-only in scope and must never be formatted, partitioned, initialized, deleted, moved, mounted, or used as an installation target.
- Gates 3 and later require explicit activation and are not executed by default.
- Windows PowerShell 5.1 remains installed; PowerShell 7 is additive only.

## Current status (2026-09-16)

- Gate 0 Preflight: PASS.
- Gate 1 Windows Foundation: PASS; Defender and firewall enabled.
- Gate 2 Developer Tools: PASS with one unresolved 7-Zip verification failure. PowerShell 7, Git, Git LFS, Python, Node.js LTS, VS Code, and FFmpeg are available or prepared; 7-Zip is not confirmed on PATH.
- Gate 3 WSL2 Foundation: PASS. Ubuntu-24.04 (24.04.5 LTS) is installed and running on WSL2; Windows↔WSL communication passed.
- Gate 4 GPU / Local AI Foundation: PASS. RTX 3090 Ti and WSL passthrough are functional; Ollama 0.34.1 ran `tinyllama:1.1b-chat` at 100% GPU. Ollama was installed as a manual standalone CLI under `C:\Einrichtung\05_AI\ollama`; no autostart or cloud provider was configured.
- Gate 4.5 Update & Stabilization: PASS. Windows Update found no pending non-hidden updates; Ubuntu received 11 safe `--no-remove` package upgrades, with 9 phased updates deferred. NVIDIA 591.86 and Ollama 0.34.1 were retained after official-source review and successful GPU retests.
- The OS reports Windows 10 Pro, build 26200, despite the supplied context saying Windows 11. This discrepancy is documented and no OS change was attempted.
- `Disk 1` ADATA SX8200PNP is the protected approximately 1-TB disk. It is also reported by Windows as `IsSystem=True` / `BootFromDisk=True`; this conflict requires human review before any storage operation. No storage operation was performed.

Run `C:\Einrichtung\bootstrap.ps1 -Phase Preflight`, then `-Phase System`, then `-Phase Tools` to refresh the state. See `C:\Einrichtung\state\CODEX_STATE.json`, `C:\Einrichtung\state\machine-manifest.json`, and `C:\Einrichtung\08_Logs` for machine evidence. The 7-Zip diagnostic is under `C:\Einrichtung\09_Debug`.

## Explicitly deferred

Docker, PostgreSQL, Hermes, OpenClaw, Keystone application code, MCP/policy/approval, observability, memory, skills, routines, and real-world E2E are not automatically installed or started. Gate 5 is the next explicit gate.
