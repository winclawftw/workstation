"""Minimal local Keystone terminal chat. No tools and no cloud fallback."""
from __future__ import annotations

import sys
from pathlib import Path

# Support direct execution from the scripts directory without installation.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT.parent) not in sys.path:
    sys.path.insert(0, str(ROOT.parent))

from keystone_core.bonsai import BonsaiModelProvider
from keystone_core.engine import KeystoneEngine


def main() -> int:
    provider = BonsaiModelProvider(
        base_url="http://127.0.0.1:8080",
        default_model="bonsai2-gguf/27B",
        timeout=10,
        generation_timeout=180,
    )
    engine = KeystoneEngine(provider)

    print("Keystone local chat")
    print("Provider: Bonsai | Endpoint: http://127.0.0.1:8080")
    print("Commands: /status, /models, /exit")
    print("Safety: chat only; no tools, file access, or cloud fallback.\n")

    try:
        status = engine.status()
        print(f"Connected: {status['provider_health']}\n")
    except Exception as exc:
        print(f"Could not connect to Bonsai: {type(exc).__name__}: {exc}")
        print("Start the existing Bonsai server and run this command again.")
        return 1

    while True:
        try:
            prompt = input("You > ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nKeystone session ended.")
            return 0

        if not prompt:
            continue
        if prompt.lower() in {"/exit", "/quit"}:
            print("Keystone session ended.")
            return 0
        if prompt.lower() == "/status":
            try:
                print(engine.status())
            except Exception as exc:
                print(f"Status error: {type(exc).__name__}: {exc}")
            continue
        if prompt.lower() == "/models":
            try:
                for model in engine.available_models():
                    print(f"- {model}")
            except Exception as exc:
                print(f"Model listing error: {type(exc).__name__}: {exc}")
            continue

        try:
            reply = engine.respond(prompt)
            print(f"\nKeystone [{reply.provider}] > {reply.text}\n")
        except Exception as exc:
            print(f"\nRequest failed: {type(exc).__name__}: {exc}\n")


if __name__ == "__main__":
    raise SystemExit(main())
