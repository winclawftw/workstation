# Qwen Model Qualification

## Environment

- Windows 11 Pro, build 26200
- CPU: AMD Ryzen 7 7800X3D
- RAM: 32 GB DDR5
- GPU: NVIDIA GeForce RTX 3090 Ti, 24,564 MiB, driver 591.86
- WSL: 2.7.14.0, Ubuntu 24.04.5 LTS
- Ollama: 0.34.1
- Hermes: 0.21.3
- Cloud: OFF; API keys: NONE
- ADATA SX8200PNP / Disk 1: untouched

## Selected Candidate

Selected exactly one candidate: `qwen3.8:latest`.

Observed Ollama metadata: Qwen3.8 27.3B, Q4_K_M, 17.74 GB installed model size, native context 262,144, capabilities `completion`, `vision`, `tools`, and `thinking`. The model is substantially heavier than Qwen3:8b, but it is the requested current candidate and fits the 24 GB card only with a narrow memory margin.

Official references: [Ollama qwen3.8](https://ollama.com/library/qwen3.8), [Ollama tool calling](https://docs.ollama.com/capabilities/tool-calling).

## Exact Configuration

- Model tag: `qwen3.8`
- Quantization: Q4_K_M
- Requested context: 65,536 tokens
- Hermes-observed context: 32,768 tokens
- Temperature: 0.2
- Top-p: 0.95
- Thinking: disabled for deterministic qualification calls
- Output limit: 256 tokens
- GPU layers: Ollama default / `num_gpu=-1`
- Parallelism: 1
- Ollama model storage: `C:\Einrichtung\05_AI\models`
- Hermes qualification config: `C:\Einrichtung\05_AI\qwen-hermes-config.yaml`
- Hermes qualification home: `C:\Einrichtung\05_AI\qwen-hermes-home`

The existing Hermes home/configuration was not overwritten. Qwen was not made the default model.

## Test Results

### Basic Inference

PASS. The model loaded and returned `QWEN BASIC PASS`. No crash occurred. Direct API calls completed successfully. Peak measured VRAM was approximately 23,907 MiB in the basic run.

### German

PASS. The model correctly explained `/home` versus `/mnt/c`, native ext4 versus Windows NTFS access, and metadata/I/O overhead. The rubric required at least three relevant technical terms; the response met it.

### Structured Output

PASS. The response parsed as JSON and matched the required `task`, `status`, and `items[{name,value}]` schema.

### Tool-Call Intent

PASS. With a simulated `get_current_directory` definition, the model emitted exactly one tool call, selected the correct tool, and supplied an empty argument object without invented parameters.

### Context

PASS. A deterministic multi-fact checksum task preserved all facts and returned `red-7-WSL`.

### Error Handling

PASS. When asked to use a tool requiring a missing city, the model asked for the city instead of fabricating one or calling with invented arguments.

### Performance

Observed direct Ollama results:

- Basic: 34.67 s total, 7.40 tok/s, peak VRAM 23,907 MiB
- German: 49.99 s total, 3.13 tok/s, peak VRAM 23,929 MiB
- Structured JSON: 15.77 s total, 5.95 tok/s, peak VRAM 23,728 MiB
- Tool intent: 4.72 s total, 7.12 tok/s, peak VRAM 23,681 MiB
- Context task: 8.93 s total, 6.25 tok/s, peak VRAM 23,719 MiB
- Time to first token: NOT MEASURED; qualification calls used non-streaming API
- CPU/system RAM: NOT MEASURED by the qualification script

Critical runtime observation from `ollama ps` during Hermes: `97% CPU / 3% GPU`, model context 32,768. This indicates heavy CPU fallback/offload for the Hermes workload.

### Stability

PASS for the measured sample: 3/3 repeated representative runs succeeded; 0 failures, 0 crashes, and no malformed output in those repetitions.

### Hermes Integration

PASS technically, CONDITIONAL operationally. Hermes 0.21.3 reached `qwen3.8` through the separate qualification configuration and returned the requested JSON. The Hermes request completed, but latency was 127.8 seconds and `ollama ps` observed 97% CPU / 3% GPU at context 32,768. No cloud provider or API key was used.

## Measurements

Observed values are recorded in `qwen-qualification.json`. Derived tokens/sec equals Ollama `eval_count / eval_duration`. Assumptions are not presented as measurements.

## Failures

No functional test failure occurred. The material limitation is resource behavior: near-full VRAM, low effective GPU share during Hermes, and very high Hermes latency.

## Known Limitations

- Qwen3.8 is a 27.3B model, not a lightweight local agent model.
- The 24 GB GPU has little headroom at large context sizes.
- Hermes used 32,768 context in the observed `ollama ps` run despite the 65,536 requested qualification setting.
- Hermes auxiliary/title work contributed to the long end-to-end latency.
- CPU and system RAM were not measured by the script.
- Qwen remains a qualification candidate only; no Keystone or Gate-7 configuration was changed.

## Final Qualification

**CONDITIONAL**

The model is technically usable: all standalone functional tests passed and Hermes returned a response. It is not unconditionally qualified for default Keystone agent use because of the measured CPU fallback, near-limit VRAM usage, and 127.8-second Hermes latency.

## Recommended Use

- Offline German technical work
- Structured-output and tool-intent experiments
- Controlled, low-concurrency research tasks
- Future Gate-7 evaluation only with explicit resource/latency budgets

## Not Recommended For

- Replacing the current Keystone default model
- Low-latency interactive agent sessions
- High-concurrency workloads
- Large-context Hermes sessions on this 24 GB GPU without further tuning

## Reproduction Procedure

1. Start the existing manual Ollama test server with `C:\Einrichtung\05_AI\start-ollama-test.ps1`.
2. Run `py -3 C:\Einrichtung\05_AI\qwen-qualification.py`.
3. For Hermes, use the separate home/configuration and temporary WSL-reachable Ollama binding; do not modify `C:\Einrichtung\06_Hermes\home\config.yaml`.
4. Inspect `C:\Einrichtung\05_AI\qwen-qualification.json`.
5. Stop the manual Ollama process after testing.

## Final safety state

- Gate 7: NOT STARTED
- Keystone architecture: unchanged
- Hermes production configuration: unchanged
- Cloud: OFF
- API keys: NONE
- Autostart: NONE
- ADATA / Disk 1: UNCHANGED
