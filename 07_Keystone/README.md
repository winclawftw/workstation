# Keystone

Keystone is a local-first workstation assistant. Bonsai generates suggestions; Keystone controls session context and local project operations. Model output never gets direct shell, filesystem, or tool access.

## Requirements

- Windows 11 and Python 3.12 (standard library only; no separate Python packages required).
- The existing Bonsai server running locally at `http://127.0.0.1:8080`.
- The current workstation model is expected at `C:\Einrichtung\05_AI\bonsai\models\bonsai2-gguf\27B\Ternary-Bonsai-2-27B-PQ2_0.gguf`.

Keystone does not install Bonsai and does not use a cloud fallback. If Bonsai is not already running, open a separate PowerShell window and start its existing local server:

```powershell
Set-Location C:\Einrichtung\05_AI\bonsai
.\scripts\start_llama_server.ps1
```

The Bonsai server binds to `127.0.0.1:8080` by default and keeps that window open. Leave it running while using Keystone.

## Start

In PowerShell:

```powershell
Set-Location C:\Einrichtung\07_Keystone
py -3.12 .\scripts\keystone_chat.py
```

The CLI checks Bonsai health before accepting messages. Session history includes the system prompt, project context, and recent user/assistant messages; it is limited to the most recent 16 history messages. `/clear` clears only that in-memory conversation and last answer. It does not remove projects or artifacts.

## Terminal commands

- `/status` — check local provider health.
- `/models` — list model IDs exposed by Bonsai.
- `/project new <name>` — create and open a local project.
- `/project list` — list valid projects; `*` marks the active project. Unreadable, oversized, or linked records produce warnings.
- `/project open <id>` — load a project and its saved context.
- `/project note <text>` — add a persistent project note.
- `/project show` — show project description, notes, and artifact references.
- `/artifact save <filename.md>` — save the last complete assistant response as Markdown. An existing filename is preserved; Keystone chooses a numbered name such as `filename (2).md`.
- `/clear` — clear current conversation only.
- `/exit` — close Keystone.

Project IDs are 12 lowercase hexadecimal characters. Project names and filenames are validated. Project and artifact writes stay under the local data root; reparse-point workspace directories are rejected. On Windows, each operation verifies the opened directory handle and holds it with delete sharing disabled while using paths inside it, so the directory cannot be renamed or replaced during that operation. Project JSON is also opened without following a final reparse point. This race protection is tested on Windows 11 with NTFS; other platforms currently retain path checks but do not have the same race-resistant guarantee. No file is saved unless the user enters the artifact command.

## Local data

- Project JSON: `C:\Einrichtung\07_Keystone\data\projects\<id>.json`
- Markdown artifacts: `C:\Einrichtung\07_Keystone\data\artifacts\`
- Project JSON stores the ID, name, description, creation/update timestamps, notes, and artifact references.
- Project JSON is limited to 1 MB; unreadable, malformed, deeply nested, or oversized records return a workspace error instead of being loaded without a bound.
- Conversation history is in memory only; it is not persisted between CLI sessions.
- No database server is used.

## Tests

From `C:\Einrichtung\07_Keystone`:

```powershell
py -3.12 -m unittest discover -s tests -v
```

The tests use mocks or temporary directories. To verify the real local provider once, run the Keystone CLI, open the intended project, ask a short question, then exit. The CLI's startup check exercises `/health`; generation uses `/v1/chat/completions`.

## Scope and limitations

- Terminal-only interface; no web UI, database, background service, or automatic startup.
- Bonsai is text-only through the OpenAI-compatible chat endpoint in this adapter. Keystone does not execute model-proposed tools.
- Conversation history does not survive restart. Project notes and artifacts do.
- Business facts, decisions, and prices must come from the user; unknown items remain open.
