# Keystone

Keystone is a local-first control plane for the Workstation. Models propose; Keystone owns policy and execution. The initial milestone is intentionally small: a model-provider contract, a Bonsai adapter, a request engine, and a local terminal chat.

## Current vertical slice

- **Model provider:** Bonsai via the local OpenAI-compatible endpoint at `http://127.0.0.1:8080`
- **Engine:** validates the request boundary and delegates text generation
- **Interface:** terminal chat in `scripts/keystone_chat.py`
- **Safety boundary:** no tool execution, no filesystem actions from model output, and no cloud fallback

## Run on Windows

From PowerShell:

```powershell
Set-Location C:\Einrichtung\07_Keystone
python .\scripts\keystone_chat.py
```

The existing Bonsai server must already be running. Chat commands:

- `/status` — provider health
- `/models` — list model IDs
- `/exit` — exit the session

## Current limitations

This is a first vertical slice, not the finished agent UI. Conversations are not persisted yet. The model cannot call tools. Approvals, audit records, storage, and the web UI are future increments and must be implemented in Keystone rather than delegated to model authority.

The current live smoke-test discrepancy is tracked as unresolved; the direct completion request has returned the expected user-facing content. Do not block core development on repeated endpoint-only tests.
