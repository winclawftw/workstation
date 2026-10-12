# GATE 6 — KEYSTONE CORE

**STATUS: PASS**

## Repository

`C:\Einrichtung\07_Keystone` was empty before Gate 6 and was not a Git repository. No existing Keystone source, database artifact, bootstrap script, or documentation was overwritten. The Hermes Git repository at `C:\Einrichtung\06_Hermes\app` was inspected but not modified.

## Core

Implemented a minimal modular monolith with Projects, Tasks, Agents, Jobs, Approvals, Policies, Runtime, Model, Tool, Storage, Events, Audit, and Artifact domain boundaries.

## Runtime / Hermes

`HermesRuntime` implements the `AgentRuntime` contract and invokes the already-installed Hermes 0.21.3 in WSL2 Ubuntu-24.04. Hermes remains an adapter, not the Keystone core.

## Model Provider / Ollama

`OllamaModelProvider` implements health, model listing, and local generation against the existing Ollama 0.34.1 HTTP API. No cloud provider or API key is used. The compatible local model is `llama3.2:3b`; the earlier TinyLlama model remains untouched.

## Tool Provider

`ReadOnlyToolProvider` exposes only `get_current_directory`. Discovery and execution are separate. No delete, overwrite, publish, credential, or system-modification tool exists.

## Policy / Approval

`PolicyEngine` allows the read-only path and marks delete, overwrite, publish, credentials, and system changes as approval-required. `ApprovalService` is a deterministic contract stub; no UI is included.

## Storage

`LocalStorage` persists minimal records as JSONL and can be replaced by Postgres/Supabase later without changing the core boundary. No database service was installed.

## Events / Audit

`EventBus` persists lifecycle and tool events. `AuditLogger` records completed tool and task actions. Runtime failure is categorized as `ExecutionFailed` and emits `runtime.failed`.

## Health

Live health check passed for Core, Hermes runtime, Ollama provider, local storage, and read-only tools.

## Tests

Offline automated tests: 5 passed and 1 explicitly skipped (the live test is opt-in).

Live E2E test: passed with `KEYSTONE_LIVE_E2E=1`; flow was Keystone → HermesRuntime → local Hermes/WSL → Ollama → response → persisted events/audit.

Live read-only tool test: passed through `ReadOnlyToolProvider`; tool execution and audit records were verified.

## Security

- Cloud: OFF
- API keys: NONE
- Credentials: NONE added
- Autostart / Task Scheduler / Windows service: NONE
- Production MCP: NONE
- Docker/Postgres/Supabase: NONE
- Bootloader/BCD: unchanged
- ADATA / Disk 1: UNCHANGED

## WSL filesystem

The Gate-5 decision remains unchanged. Hermes is still under `C:\Einrichtung\06_Hermes` and accessed from WSL through `/mnt/c`; no measured Gate-5 problem exists. The placement is documented as a future architecture optimization, not migrated during Gate 6.

## Files created

- `ARCHITECTURE.md`
- `GATE-6-REPORT.md`
- `.gitignore`
- `.env.example`
- `pyproject.toml`
- `keystone_core/` contracts, domain, core, providers, runtime, policy, storage, events, and CLI health entry point
- `tests/` contract, core, and E2E smoke tests

## Known limitations

Local JSONL storage is intentionally minimal, Hermes/WSL paths are configuration-bound, Ollama remains manually started, and the future Postgres/MCP/UI/memory layers are not implemented.

## Next Gate

**GATE 7** — not started.
