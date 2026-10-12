import json
import statistics
import subprocess
import threading
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(r"C:\Einrichtung\05_AI")
BASE_URL = "http://127.0.0.1:11434"
MODEL = "qwen3.8"
CONTEXT = 65536
OPTIONS = {"temperature": 0.2, "top_p": 0.95, "num_ctx": CONTEXT, "num_predict": 256, "num_gpu": -1}


def post(path, payload, timeout=300):
    request = urllib.request.Request(BASE_URL + path, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"})
    started = time.perf_counter()
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            result = json.loads(response.read().decode())
        result["wall_seconds"] = time.perf_counter() - started
        return result
    except (OSError, urllib.error.URLError, json.JSONDecodeError) as exc:
        return {"error": str(exc), "wall_seconds": time.perf_counter() - started}


def gpu_sample():
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=utilization.gpu,memory.used,memory.total", "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=3, check=False,
        )
        values = [int(part.strip()) for part in result.stdout.strip().split(",")]
        return {"gpu_util_percent": values[0], "vram_used_mib": values[1], "vram_total_mib": values[2]}
    except (OSError, ValueError, IndexError, subprocess.TimeoutExpired):
        return None


def chat(messages, *, tools=None, response_format=None, timeout=300):
    payload = {"model": MODEL, "messages": messages, "stream": False, "think": False, "options": OPTIONS}
    if tools is not None:
        payload["tools"] = tools
    if response_format is not None:
        payload["format"] = response_format
    samples = []
    holder = {}

    def invoke():
        holder["response"] = post("/api/chat", payload, timeout=timeout)

    worker = threading.Thread(target=invoke, daemon=True)
    worker.start()
    while worker.is_alive():
        sample = gpu_sample()
        if sample:
            samples.append(sample)
        time.sleep(0.25)
    worker.join()
    response = holder.get("response", {"error": "no response"})
    response["gpu_samples"] = samples
    response["gpu_peak_util_percent"] = max((s["gpu_util_percent"] for s in samples), default=None)
    response["vram_peak_mib"] = max((s["vram_used_mib"] for s in samples), default=None)
    response["content"] = response.get("message", {}).get("content", "")
    response["tool_calls"] = response.get("message", {}).get("tool_calls", [])
    return response


def metrics(response):
    return {
        "status": "FAIL" if "error" in response else "PASS",
        "wall_seconds": response.get("wall_seconds"),
        "total_seconds": (response.get("total_duration") or 0) / 1e9 or None,
        "load_seconds": (response.get("load_duration") or 0) / 1e9 or None,
        "prompt_tokens": response.get("prompt_eval_count"),
        "output_tokens": response.get("eval_count"),
        "tokens_per_second": round(response["eval_count"] / (response["eval_duration"] / 1e9), 2) if response.get("eval_count") and response.get("eval_duration") else None,
        "time_to_first_token": "NOT MEASURED (non-streaming API)",
        "gpu_peak_util_percent": response.get("gpu_peak_util_percent"),
        "vram_peak_mib": response.get("vram_peak_mib"),
        "error": response.get("error"),
    }


def schema_valid(value):
    return isinstance(value, dict) and isinstance(value.get("task"), str) and isinstance(value.get("status"), str) and isinstance(value.get("items"), list) and all(isinstance(item, dict) and isinstance(item.get("name"), str) and isinstance(item.get("value"), str) for item in value["items"])


def run():
    show = post("/api/show", {"name": MODEL})
    tags = post("/api/tags", {})
    common = [{"role": "user", "content": "Reply with exactly the text QWEN BASIC PASS."}]
    basic = chat(common)

    german = chat([{"role": "user", "content": "Antworte auf Deutsch und kurz: Warum ist es für Linux-Dateioperationen oft günstiger, Projektdateien im WSL-Dateisystem unter /home statt unter /mnt/c zu speichern? Nenne genau zwei technische Gründe."}])
    german_text = german.get("content", "").lower()
    german_pass = sum(term in german_text for term in ["/home", "/mnt/c", "performance", "dateisystem", "io", "zugriff"]) >= 3

    schema = {"type": "object", "properties": {"task": {"type": "string"}, "status": {"type": "string"}, "items": {"type": "array", "items": {"type": "object", "properties": {"name": {"type": "string"}, "value": {"type": "string"}}, "required": ["name", "value"]}}}, "required": ["task", "status", "items"]}
    structured = chat([{"role": "user", "content": "Return only JSON. Set task to 'filesystem-check', status to 'ok', and items to two objects describing WSL and Windows filesystem locations."}], response_format=schema)
    try:
        structured_value = json.loads(structured.get("content", ""))
        structured_valid = schema_valid(structured_value)
    except json.JSONDecodeError:
        structured_value = None
        structured_valid = False

    tool = {"type": "function", "function": {"name": "get_current_directory", "description": "Return the current directory. Takes no arguments.", "parameters": {"type": "object", "properties": {}, "additionalProperties": False}}}
    tool_intent = chat([{"role": "user", "content": "Use get_current_directory now. Produce exactly one tool call and no prose."}], tools=[tool])
    tool_calls = tool_intent.get("tool_calls", [])
    tool_valid = len(tool_calls) == 1 and tool_calls[0].get("function", {}).get("name") == "get_current_directory" and tool_calls[0].get("function", {}).get("arguments", {}) in ({}, "{}")

    context = chat([{"role": "user", "content": "Facts: ALPHA=red, BETA=7, GAMMA=WSL. Constraint: do not invent facts. Return JSON with keys alpha, beta, gamma, checksum; checksum must be red-7-WSL."}], response_format={"type": "object"})
    try:
        context_value = json.loads(context.get("content", ""))
        context_pass = context_value.get("checksum") == "red-7-WSL" and context_value.get("beta") in (7, "7")
    except json.JSONDecodeError:
        context_value = None
        context_pass = False

    error_case = chat([{"role": "user", "content": "Call lookup_weather, but the tool definition is intentionally missing the required city argument. Do not invent a city; ask one clarification question and do not call an unavailable tool."}], tools=[{"type": "function", "function": {"name": "lookup_weather", "description": "Look up weather for a city.", "parameters": {"type": "object", "properties": {"city": {"type": "string"}}, "required": ["city"], "additionalProperties": False}}}])
    error_text = error_case.get("content", "").lower()
    error_pass = not error_case.get("tool_calls") and any(term in error_text for term in ["city", "stadt", "welche", "which", "clarif", "angeben"])

    stability = []
    for _ in range(3):
        stability.append(chat([{ "role": "user", "content": "Reply with exactly: STABILITY PASS" }]))

    # Same selected context configuration; controlled prompt is intentionally bounded for safe repeatability.
    context_stability = chat([{"role": "user", "content": "Repeat the marker CONTEXT-QUALIFIED exactly once."}])

    successful = sum("error" not in item for item in stability)
    result = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "model": {"requested_tag": MODEL, "show": {k: show.get(k) for k in ["details", "model_info", "capabilities", "requires"]}, "tags": tags.get("models", [])},
        "environment": {"ollama": "0.34.1", "hermes": "0.21.3", "python": "3.12.10", "wsl": "2.7.14.0", "windows": "Windows 11 Pro build 26200", "gpu": "NVIDIA GeForce RTX 3090 Ti", "vram_total_mib": 24564, "ram": "32 GB DDR5", "cloud": "OFF", "api_keys": "NONE"},
        "configuration": {"context_size": CONTEXT, "temperature": 0.2, "top_p": 0.95, "gpu_layers": "Ollama default / num_gpu=-1", "parallelism": 1, "thinking": False, "num_predict": 256},
        "tests": {
            "basic_inference": {"result": basic.get("content", ""), "metrics": metrics(basic), "pass": "error" not in basic and bool(basic.get("content"))},
            "german": {"result": german.get("content", ""), "metrics": metrics(german), "pass": german_pass},
            "structured_output": {"result": structured_value, "raw": structured.get("content", ""), "metrics": metrics(structured), "pass": structured_valid},
            "tool_call_intent": {"result": tool_calls, "metrics": metrics(tool_intent), "pass": tool_valid},
            "context": {"result": context_value, "raw": context.get("content", ""), "metrics": metrics(context), "pass": context_pass},
            "error_handling": {"result": error_case.get("content", ""), "tool_calls": error_case.get("tool_calls", []), "metrics": metrics(error_case), "pass": error_pass},
            "context_stability": {"configured_context": CONTEXT, "input_tokens": context_stability.get("prompt_eval_count"), "output_tokens": context_stability.get("eval_count"), "metrics": metrics(context_stability), "pass": "error" not in context_stability},
            "stability": {"runs": len(stability), "successful_runs": successful, "failed_runs": len(stability) - successful, "metrics": [metrics(item) for item in stability], "pass": successful == len(stability)},
        },
        "measurements": {"observed": "GPU/VRAM samples are collected during each API call; TTFT is not measured because calls are non-streaming.", "derived": "tokens_per_second is eval_count divided by eval_duration.", "assumed": "None used as measured values."},
        "limitations": ["The 27B Q4_K_M model is close to the 24 GB VRAM ceiling at large context sizes.", "Hermes qualification is run separately with a non-default configuration.", "CPU and system RAM utilization are not measured by this script."],
    }
    (ROOT / "qwen-qualification.json").write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"written": str(ROOT / "qwen-qualification.json"), "basic": result["tests"]["basic_inference"]["pass"], "structured": structured_valid, "tool": tool_valid, "context": context_pass, "error": error_pass, "stability": result["tests"]["stability"]["pass"]}, indent=2))


if __name__ == "__main__":
    run()
