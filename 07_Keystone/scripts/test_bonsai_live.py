"""Small live smoke test for the local Bonsai llama.cpp endpoint."""
import json
import sys
import urllib.error
import urllib.request

BASE = "http://127.0.0.1:8080"

def request(path, payload=None, timeout=120):
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    headers = {"Accept": "application/json"}
    if data is not None:
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(BASE + path, data=data, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))

def main():
    print("=== LIVE BONSAI SMOKE TEST ===", flush=True)
    try:
        health = request("/health", timeout=3)
    except (OSError, urllib.error.URLError, TimeoutError) as exc:
        print(f"FAIL: Bonsai server is not reachable at {BASE}: {type(exc).__name__}: {exc}")
        print("Start the existing Bonsai server with its normal start script, then rerun this test.")
        return 2
    if health.get("status") != "ok":
        print(f"FAIL: unexpected health response: {health!r}")
        return 2
    print("PASS: /health reports status=ok")

    try:
        listing = request("/v1/models", timeout=10)
        models = [m.get("id") for m in listing.get("data", []) if isinstance(m, dict)]
    except Exception as exc:
        print(f"FAIL: model listing: {type(exc).__name__}: {exc}")
        return 2
    print(f"PASS: /v1/models returned {models}")
    if not models:
        print("FAIL: no model IDs returned")
        return 2

    payload = {
        "model": models[0],
        "messages": [{"role": "user", "content": "Reply with exactly: KEYSTONE_BONSAI_OK"}],
        "max_tokens": 32,
        "stream": False,
    }
    try:
        completion = request("/v1/chat/completions", payload=payload, timeout=120)
        choices = completion.get("choices", [])
        message = choices[0].get("message", {}) if choices else {}
        answer = message.get("content")
    except Exception as exc:
        print(f"FAIL: live generation: {type(exc).__name__}: {exc}")
        return 2
    if not isinstance(answer, str) or not answer.strip():
        print("FAIL: server returned no user-facing content; reasoning_content is intentionally not accepted")
        return 2
    print(f"PASS: live generation returned content: {answer.strip()!r}")
    print("LIVE RESULT: PASS (health + model listing + generation)")
    return 0

if __name__ == "__main__":
    sys.exit(main())