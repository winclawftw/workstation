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
  -> selected ModelProvider (Ollama today; Bonsai optional after implementation)
  -> response
  -> EventBus + AuditLogger + LocalStorage
```

Tool calls use the separate path:

```text
request -> PolicyEngine -> ReadOnlyToolProvider -> result -> event/audit
```

Dangerous categories (`delete`, `overwrite`, `publish`, `credentials`, `system`) are approval-required by policy. No write-capable tool is registered.

## Model provider boundary

The current `ModelProvider` contract is intentionally small: `capabilities()`, `health()`, `list_models()`, and `generate(prompt)`. `OllamaModelProvider` remains the existing implementation.

**Bonsai 2 now has an experimental text-only adapter** in `keystone_core/bonsai.py` plus focused tests in `tests/test_bonsai_provider.py`. The adapter is not yet registered in the main Keystone orchestration path; its tests still need to run in the workstation environment. Structured chat, image input, and tool-call proposals need an explicit contract extension before they are exposed to orchestration. Details and workstation test evidence are in [BONSAI_PROVIDER.md](BONSAI_PROVIDER.md).

Keystone owns provider selection and policy. A model provider must never execute tools, grant permissions, start an unrequested process, or silently fall back to a remote model.

## Configuration and storage

Configuration is environment-based and documented in `.env.example`. No secrets are stored in source or example configuration. Runtime data is written to the caller-selected `data/` directory, which is ignored by Git.

The existing Hermes installation remains under `C:\Einrichtung\06_Hermes` and is not migrated. Keystone itself is under `C:\Einrichtung\07_Keystone`. Bonsai's separately installed model server is under `C:\Einrichtung\05_AI\bonsai`; the adapter must not change Ollama or other AI directories.

## Known limitations

- LocalStorage is intentionally JSONL and is not a concurrency-oriented truth layer.
- Hermes invocation currently depends on the installed WSL distro and Hermes home path.
- Ollama must be started manually for live checks; no service or autostart is configured.
- Bonsai has passed basic local text and function-call smoke tests, and an isolated text-only provider adapter is committed. The adapter is not yet wired into the main orchestration path; no multi-step tool loop exists.
- Bonsai vision recognized one screenshot, but its response was truncated and the description appeared in `reasoning_content` while `content` was empty; vision remains experimental.
- MCP, Postgres/Supabase, UI, memory, and production deployment are intentionally out of scope.
