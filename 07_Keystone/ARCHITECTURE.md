# Keystone Core — Gate 6

Keystone is a small modular monolith. It is the control plane over replaceable runtimes, model providers, tool providers, and storage providers.

`HermesRuntime` is an implementation of `AgentRuntime`. It is not Keystone itself.

## Boundaries

- `core.py` owns orchestration of projects, tasks, agents, jobs, health, and the execution path.
- `contracts.py` defines the stable protocols and typed error categories.
- `runtime.py` adapts the already-installed Hermes CLI through WSL2.
- `models.py` adapts the local Ollama HTTP API only.
- `tools.py` exposes one read-only tool: `get_current_directory`.
- `policy.py` separates policy decisions and approval requirements from tool execution.
- `storage.py` provides replaceable local JSONL storage; no database service is required.
- `events.py` persists structured events and audit records.
- `domain.py` contains the minimal domain objects.

## Execution flow

```text
Keystone
  -> PolicyEngine
  -> AgentRuntime / HermesRuntime
  -> local Hermes in WSL2
  -> OllamaModelProvider / local Ollama
  -> response
  -> EventBus + AuditLogger + LocalStorage
```

Tool calls use the separate path:

```text
request -> PolicyEngine -> ReadOnlyToolProvider -> result -> event/audit
```

Dangerous categories (`delete`, `overwrite`, `publish`, `credentials`, `system`) are approval-required by policy. No write-capable tool is registered.

## Configuration and storage

Configuration is environment-based and documented in `.env.example`. No secrets are stored in source or example configuration. Runtime data is written to the caller-selected `data/` directory, which is ignored by Git.

The existing Hermes installation remains under `C:\Einrichtung\06_Hermes` and is not migrated. Keystone itself is under `C:\Einrichtung\07_Keystone`.

## Known limitations

- LocalStorage is intentionally JSONL and is not a concurrency-oriented truth layer.
- Hermes invocation currently depends on the installed WSL distro and Hermes home path.
- Ollama must be started manually for live checks; no service or autostart is configured.
- MCP, Postgres/Supabase, UI, memory, and production deployment are intentionally out of scope.
