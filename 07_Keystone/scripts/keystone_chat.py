"""Local Keystone chat with session context and local project commands."""
from __future__ import annotations
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from keystone_core.bonsai import BonsaiModelProvider
from keystone_core.engine import KeystoneEngine
from keystone_core.workspace import WorkspaceError, WorkspaceStore

SYSTEM_PROMPT = """You are Keystone, a practical local-first work assistant.
Be direct and collaborative. Ask only the next important question, and state
reasonable assumptions when helpful. You cannot directly save files; only the
local workspace commands can do that. Do not claim a file was saved unless the
application confirms it. No cloud fallback."""


def main() -> int:
    provider = BonsaiModelProvider(base_url="http://127.0.0.1:8080",
        default_model="bonsai2-gguf/27B", timeout=10, generation_timeout=180)
    engine = KeystoneEngine(provider)
    workspace = WorkspaceStore(ROOT / "data")
    history: list[dict[str, str]] = []
    active = None
    last_reply = ""

    print("Keystone local workspace | Bonsai: http://127.0.0.1:8080")
    print("Commands: /status, /models, /project new <name>, /project list,")
    print(" /project open <id>, /project note <text>, /project show,")
    print(" /artifact save <filename.md>, /clear, /exit")
    print("Data stays under:", workspace.root, "\n")
    try:
        print("Connected:", engine.status()["provider_health"], "\n")
    except Exception as exc:
        print(f"Could not connect to Bonsai: {type(exc).__name__}: {exc}")
        print("Start the existing Bonsai server, then retry.")
        return 1

    while True:
        try:
            prompt = input(f"You [{active['name'] if active else 'no project'}] > ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nKeystone session ended.")
            return 0
        if not prompt:
            continue
        lower = prompt.lower()
        if lower in {"/exit", "/quit"}:
            print("Keystone session ended.")
            return 0
        if lower == "/status":
            try: print(engine.status())
            except Exception as exc: print(f"Status error: {type(exc).__name__}: {exc}")
            continue
        if lower == "/models":
            try:
                for model in engine.available_models(): print("-", model)
            except Exception as exc: print(f"Model listing error: {type(exc).__name__}: {exc}")
            continue
        if lower == "/clear":
            history.clear()
            last_reply = ""
            print("Conversation cleared; saved projects remain.")
            continue
        if lower == "/project list":
            projects = workspace.list_projects()
            if not projects: print("No projects yet. Use /project new <name>.")
            for item in projects:
                mark = "*" if active and item["id"] == active["id"] else " "
                print(f"{mark} {item['id']}  {item['name']}")
            continue
        if lower.startswith("/project new "):
            try:
                active = workspace.create_project(prompt[len("/project new "):].strip())
                history.clear()
                print(f"Created and opened: {active['name']} (ID {active['id']})")
            except WorkspaceError as exc: print("Project error:", exc)
            continue
        if lower.startswith("/project open "):
            try:
                active = workspace.get_project(prompt[len("/project open "):].strip())
                history.clear()
                print(f"Opened: {active['name']} (ID {active['id']})")
            except WorkspaceError as exc: print("Project error:", exc)
            continue
        if lower == "/project show":
            if not active: print("No active project. Create or open one first.")
            else:
                print(f"{active['name']} [{active['id']}]")
                print(active.get("description") or "(no description)")
                print(f"Notes: {len(active['notes'])} | Artifacts: {len(active['artifacts'])}")
                for item in active["artifacts"]: print(" -", item["filename"], item["path"])
            continue
        if lower.startswith("/project note "):
            if not active:
                print("Create or open a project first.")
                continue
            try:
                active = workspace.add_note(active["id"], prompt[len("/project note "):].strip())
                print("Project note saved.")
            except WorkspaceError as exc: print("Project error:", exc)
            continue
        if lower.startswith("/artifact save "):
            if not last_reply:
                print("No assistant response to save yet.")
                continue
            try:
                path = workspace.save_artifact(prompt[len("/artifact save "):].strip(),
                    last_reply, active["id"] if active else None)
                if active: active = workspace.get_project(active["id"])
                print("Artifact saved:", path)
            except WorkspaceError as exc: print("Artifact error:", exc)
            continue

        project_context = "No active project."
        if active:
            notes = "\n".join("- " + item["text"] for item in active.get("notes", [])[-12:])
            project_context = (f"Active project: {active['name']} (ID {active['id']})\n"
                f"Description: {active.get('description') or '(none)'}\nProject notes:\n{notes or '(none)'}")
        try:
            reply = engine.respond(prompt, history=history[-16:],
                system_prompt=SYSTEM_PROMPT + "\n\n" + project_context)
            last_reply = reply.text
            history.extend([{"role": "user", "content": prompt},
                            {"role": "assistant", "content": reply.text}])
            history = history[-16:]
            print(f"\nKeystone [{reply.provider}] > {reply.text}\n")
        except Exception as exc:
            print(f"\nRequest failed: {type(exc).__name__}: {exc}\n")


if __name__ == "__main__":
    raise SystemExit(main())
