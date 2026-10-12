# Bonsai 2 Model Provider (Experimental)

**Status:** adapter code and focused unit tests are committed; workstation test execution and orchestration integration remain pending.
**Purpose:** qualify Bonsai 2 as an optional local inference backend for the Workstation Adobe-first Keystone system.

## Decision

Keep Bonsai as a replaceable `ModelProvider`. Keystone remains the control plane and owns routing, policy, approval, tool execution, verification, and audit. Bonsai is neither an agent runtime nor an authority.

The current Keystone contract is defined in `keystone_core/contracts.py`:

```python
class ModelProvider(Protocol):
    name: str
    def capabilities(self) -> set[str]: ...
    def health(self) -> dict[str, Any]: ...
    def list_models(self) -> list[str]: ...
    def generate(self, prompt: str, *, model: str | None = None) -> str: ...
```

The first implementation should satisfy this existing contract without expanding it unnecessarily. The current interface only supports plain prompt-in / text-out generation; structured chat messages, images, and tool calls need an explicit future contract extension before they can be exposed through Keystone's core API.

## Local workstation configuration

| Setting | Observed value |
|---|---|
| Server base URL | `http://127.0.0.1:8080` |
| OpenAI-compatible API base | `http://127.0.0.1:8080/v1` |
| Health endpoint | `GET /health` |
| Model discovery | `GET /v1/models` |
| Chat endpoint | `POST /v1/chat/completions` |
| API model identifier used successfully | `bonsai2-gguf/27B` |
| Local install directory | `C:\\Einrichtung\\05_AI\\bonsai` |
| Main GGUF | `Ternary-Bonsai-2-27B-PQ2_0.gguf` |
| Vision projector | `Ternary-Bonsai-2-27B-mmproj-Q8_0.gguf` |
| Serving context observed | 32,768 tokens |
| Server launch | PrismML-customized llama.cpp CUDA build, `-ngl 99` |
| Network binding observed | `127.0.0.1` |

The API model identifier is based on a successful local request; verify it via `/v1/models` on server startup rather than assuming it is immutable.

## Smoke-test evidence (2026-10-12)

| Check | Result | Evidence and limits |
|---|---|---|
| Health | Pass | `/health` returned `status: ok`. |
| Model discovery | Pass | `/v1/models` listed the loaded model; metadata reported about 26.9B parameters. |
| Text generation | Pass | German text prompts returned responses. Informal logs showed about 72–81 generated tokens/s; not a benchmark. |
| GPU | Pass with qualification | `nvidia-smi` showed `llama-server.exe`; total GPU memory use was about 11.8 GiB at the observed time. WDDM did not provide per-process VRAM accounting. |
| Vision | Partially pass | The screenshot was recognized as Windows Task Manager and visible process/UI details were named. However, `content` was empty, the description appeared in `reasoning_content`, and `finish_reason` was `length`. |
| Function calling | Pass for one basic case | With two functions offered and `tool_choice: required`, Bonsai emitted `finish_reason: tool_calls` and `calculate_budget({"design":120,"printing":80})`. Keystone did not execute the function. |

These are smoke tests, not a comprehensive benchmark or reliability assessment.

## Adapter responsibilities

Implement a thin `BonsaiModelProvider` (suggested module: `keystone_core/bonsai.py`) using the Python standard library initially, matching the style of `keystone_core/models.py`.

- Configuration: base URL, model identifier, and timeout should be injectable; avoid hard-coding values across Keystone.
- `health()`: call `/health`; return stable fields such as status, provider, model/runtime when known.
- `list_models()`: read `/v1/models` and return model IDs.
- `generate()`: call `/v1/chat/completions` with a user message and `stream: false`, then return only the user-facing `message.content` string.
- Map transport errors, HTTP errors, malformed JSON, missing model fields, and timeouts to `ModelUnavailable` with useful but sanitized diagnostics.
- Keep the existing Ollama provider unchanged. Do not add automatic provider fallback or autostart.
- Add focused tests using a fake/local HTTP response for health, listing, generation, malformed responses, and timeout/error mapping.

## Tool-call boundary — mandatory

The model proposes; Keystone decides and executes.

- Treat `tool_calls` as untrusted proposals, never as executed actions.
- Do not execute tools inside the model provider.
- Validate tool name and JSON arguments against the tool definitions offered for that turn.
- Policy-check project scope, permissions, protected paths, approval requirements, and side effects in Keystone before execution.
- Record proposal, validation, approval decision, execution result, and verification in Keystone's existing event/audit path.
- Model text or `reasoning_content` must never grant permissions or override policy.

The current Keystone `ModelProvider.generate(prompt) -> str` contract does not represent structured tool calls. Keep the first adapter implementation text-only. Add a normalized chat/completion result contract only when the orchestration layer is ready to handle multi-turn tool loops explicitly.

## Vision and response normalization

The installed server loaded the MMProj file and recognized a screenshot, but the observed response was not safe to surface directly:

- `message.content` was empty.
- `message.reasoning_content` contained the visual description.
- `finish_reason` was `length`.

Do not promote `reasoning_content` to user-facing content. For the first adapter, an empty `content` should be treated as an empty/incomplete model response and logged safely. Vision remains experimental until output behavior is consistent and the contract supports image content.

## Local-first safeguards

- Keep the endpoint loopback-only (`127.0.0.1)); do not bind to `0.0.0.0` without explicit review and user approval.
- The observed server logged permissive CORS and no API key; do not treat it as authenticated. Loopback binding is a security boundary.
- No cloud fallback by default. Remote inference requires an explicit visible decision and policy approval.
- Do not automatically start or stop the model server from inference calls.
- Keep Bonsai under `C:\\Einrichtung\\05_AI\\bonsai`; do not modify Ollama, other AI folders, or the protected ADATA drive.

## Implementation sequence

1. **Done in GitHub:** add `keystone_core/bonsai.py` implementing the existing text-only `ModelProvider` contract.
2. **Done in GitHub:** add `tests/test_bonsai_provider.py` for health, model discovery, text generation, empty-content handling, and transport/schema errors.
3. **Next:** run the new tests and the existing Keystone suite in the workstation's Python environment; fix any failures before integration.
4. Register Bonsai as an optional provider only after those checks pass and after the runtime/model routing boundary is clarified.
5. Extend contracts for structured chat, image input, and tool-call proposals separately; keep vision/tool calling experimental until then.

## Not claimed yet

- The Bonsai adapter and focused tests are committed, but have not yet been verified by running the suite on the workstation.
- No model-driven multi-step tool loop has been tested.
- No full Adobe workflow benchmark has been run.
- The 262K training context is not the serving limit; current server context was 32K.
