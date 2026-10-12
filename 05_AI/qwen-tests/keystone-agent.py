import json
import requests
import sys
import os
import hashlib
import py_compile
import subprocess
import re
from datetime import datetime
from pathlib import Path

OLLAMA_ENDPOINT = "http://127.0.0.1:11434/api/generate"
ORCHESTRATOR_MODEL = "hermes3:latest"
WORKER_MODEL = "qwen2.5-coder:14b"

WORKSPACE_ROOT = Path(r"C:\Einrichtung\05_AI\qwen-tests\workspace").resolve()
MEMORY_FILE = Path(r"C:\Einrichtung\05_AI\qwen-tests\memory_store.json").resolve()

def log_event(run_dir, event_type, details):
    events_file = run_dir / "events.jsonl"
    event = {
        "timestamp": datetime.now().isoformat(),
        "type": event_type,
        "details": details
    }
    with open(events_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(event) + "\n")

def load_memory():
    if MEMORY_FILE.exists():
        try:
            with open(MEMORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {"lessons": []}
    return {"lessons": []}

def save_memory(lesson):
    memory = load_memory()
    memory["lessons"].append(lesson)
    memory["lessons"] = memory["lessons"][-20:]
    MEMORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(memory, f, indent=2)

def query_ollama(model, prompt, json_schema=None, temperature=0.1):
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "num_ctx": 8192,
            "temperature": temperature,
            "repeat_penalty": 1.1
        }
    }
    if json_schema:
        payload["format"] = json_schema

    try:
        response = requests.post(OLLAMA_ENDPOINT, json=payload, timeout=300)
        response.raise_for_status()
        data = response.json()
        raw_text = data.get("response", "").strip()
        clean_text = raw_text.replace("```json", "").replace("```", "").strip()
        return json.loads(clean_text)
    except Exception as e:
        print(f"[FEHLER bei Modell {model}]: {e}")
        return None

def clear_vram():
    print("   [*] Räume VRAM auf (Ollama Keep-Alive = 0)...")
    for model in [ORCHESTRATOR_MODEL, WORKER_MODEL]:
        try:
            requests.post(OLLAMA_ENDPOINT, json={"model": model, "keep_alive": 0}, timeout=5)
        except Exception:
            pass
    print("   [OK] VRAM freigegeben.")

def run_unit_tests_in_sandbox(run_dir):
    print(f"\n   [TEST RUNNER] Starte automatisierte Unit-Tests in Sandbox...")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "unittest", "discover", "-s", str(run_dir), "-p", "test_*.py"],
            capture_output=True,
            text=True,
            timeout=30
        )
        output = result.stdout + "\n" + result.stderr
        
        if result.returncode == 0 and "Ran 0 tests" not in output and "NO TESTS RAN" not in output:
            print(f"   [TEST RUNNER] ERFOLG: Alle Unit-Tests bestanden!")
            return True, output
        else:
            print(f"   [TEST RUNNER] FEHLGESCHLAGEN: Tests fehlerhaft oder keine Tests gefunden.")
            return False, output
    except subprocess.TimeoutExpired:
        return False, "Test-Ausführung abgebrochen: Timeout nach 30 Sekunden."
    except Exception as e:
        return False, f"Fehler beim Ausführen der Tests: {str(e)}"

def extract_expected_filename(task_desc):
    """Sucht mit Regex hart nach einem Dateinamen (z.B. script.py) im Text."""
    match = re.search(r'([a-zA-Z0-9_]+\.py)', task_desc)
    return match.group(1) if match else None

def sanitize_filename(filename, is_test_step=False):
    if not filename or not str(filename).strip():
        filename = "unnamed_artifact.py"
    p = Path(filename)
    name = p.name
    
    if is_test_step and not name.startswith("test_"):
        name = "test_" + name.lstrip("test").lstrip("_")
    elif "test" in name.lower() and not name.startswith("test_"):
        name = "test_" + name.lstrip("test").lstrip("_")
        
    return name

def validate_and_fix_python_code(target_path, code_content, filename):
    max_retries = 2
    current_code = code_content
    for attempt in range(max_retries + 1):
        with open(target_path, "w", encoding="utf-8") as f:
            f.write(current_code)
        if not filename.endswith(".py"):
            return current_code, "SYNTAX_VALID"
        try:
            py_compile.compile(str(target_path), doraise=True)
            return current_code, "SYNTAX_VALID"
        except py_compile.PyCompileError as e:
            if attempt >= max_retries:
                return current_code, "FAILED"
            repair_schema = {
                "type": "object",
                "properties": {
                    "reasoning": {"type": "string"},
                    "filename": {"type": "string"},
                    "code": {"type": "string"},
                    "explanation": {"type": "string"}
                },
                "required": ["reasoning", "filename", "code", "explanation"],
                "additionalProperties": False
            }
            repair_prompt = f"Syntaxfehler in '{filename}':\n{str(e)}\nKorrigiere den Code im JSON-Schema."
            fixed_result = query_ollama(WORKER_MODEL, repair_prompt, json_schema=repair_schema, temperature=0.1)
            if fixed_result and "code" in fixed_result:
                current_code = fixed_result["code"]
            else:
                break
    return current_code, "FAILED"

def secure_write_artifact(run_id, relative_path, content, is_test=False):
    WORKSPACE_ROOT.mkdir(parents=True, exist_ok=True)
    relative_path = sanitize_filename(relative_path, is_test)
    target_path = (WORKSPACE_ROOT / run_id / relative_path).resolve()
    
    if not str(target_path).startswith(str(WORKSPACE_ROOT)):
        raise ValueError("SICHERHEITSVERLETZUNG: Path Traversal erkannt!")
        
    target_path.parent.mkdir(parents=True, exist_ok=True)
    final_content, validation_state = validate_and_fix_python_code(target_path, content, Path(relative_path).name)
    
    file_hash = hashlib.sha256(final_content.encode("utf-8")).hexdigest()
    artifact_id = hashlib.md5(relative_path.encode()).hexdigest()[:8]
    
    metadata = {
        "project_id": run_id,
        "artifact_id": artifact_id,
        "relative_path": str(relative_path),
        "sha256": file_hash,
        "created_by": WORKER_MODEL,
        "validation_state": validation_state
    }
    with open(target_path.with_suffix(target_path.suffix + ".meta.json"), "w", encoding="utf-8") as fm:
        json.dump(metadata, fm, indent=2)
        
    print(f"   [WRITTEN_TO_SANDBOX] {target_path.name} [Status: {validation_state}]")
    return metadata

def fix_code_based_on_test_failure(run_dir, test_output, last_error_output, expected_test_filename=None):
    print(f"\n   [AUTO-HEAL] Stagnations-Prüfung & Analyse...")
    if test_output.strip() == last_error_output.strip():
        print(f"   [AUTO-HEAL STAGNATION] Fehler unverändert. Stoppe Auto-Heal.")
        return False, test_output

    files_context = ""
    for file_path in run_dir.glob("*.py"):
        if file_path.name != "test_execution_report.log":
            try:
                files_context += f"\n=== DATEI: {file_path.name} ===\n{file_path.read_text(encoding='utf-8')}\n"
            except Exception:
                pass

    fix_schema = {
        "type": "object",
        "properties": {
            "reasoning": {"type": "string"},
            "filename": {"type": "string"},
            "code": {"type": "string"},
            "explanation": {"type": "string"}
        },
        "required": ["reasoning", "filename", "code", "explanation"],
        "additionalProperties": False
    }
    
    prompt = f"Fehlerbericht:\n{test_output}\n\nQuellcode:\n{files_context}\n\nKorrigiere den Fehler gezielt."
    result = query_ollama(WORKER_MODEL, prompt, json_schema=fix_schema, temperature=0.1)
    if result and "filename" in result and "code" in result:
        # Auch hier hartes Extrahierten nutzen falls LLM spinnt
        fname = result["filename"]
        if not fname or not fname.strip():
            fname = expected_test_filename or "unnamed_artifact.py"
        
        filename = sanitize_filename(fname, is_test_step=("test" in fname.lower()))
        target_file = run_dir / filename
        with open(target_file, "w", encoding="utf-8") as f:
            f.write(result["code"])
        log_event(run_dir, "AUTO_HEAL_FIX", f"Datei '{filename}' korrigiert.")
        return True, test_output
    return False, test_output

def should_require_coder(task_desc):
    keywords = [".py", "test", "schreib", "erstell", "implementier", "klasse", "code"]
    return any(k in task_desc.lower() for k in keywords)

def run_keystone_workflow(user_goal):
    run_id = datetime.now().strftime("run_%Y%m%d_%H%M%S")
    run_dir = WORKSPACE_ROOT / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"\n[KEYSTONE] Starte Workflow [{run_id}] für Ziel: '{user_goal}'")
    log_event(run_dir, "WORKFLOW_START", user_goal)

    with open(run_dir / "manifest.json", "w", encoding="utf-8") as f:
        json.dump({"run_id": run_id, "goal": user_goal, "timestamp": datetime.now().isoformat(), "status": "PLANNED"}, f, indent=2)

    planning_schema = {
        "type": "object",
        "properties": {
            "reasoning": {"type": "string"},
            "objective": {"type": "string"},
            "steps": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "step_id": {"type": "integer"},
                        "task_description": {"type": "string"},
                        "requires_coder": {"type": "boolean"}
                    },
                    "required": ["step_id", "task_description", "requires_coder"]
                }
            }
        },
        "required": ["reasoning", "objective", "steps"],
        "additionalProperties": False
    }

    plan_prompt = f"ZIEL: {user_goal}\nREGELN:\n1. Erstelle exakt 2 Schritte. Schritt 1 = Hauptdatei, Schritt 2 = Unit-Tests.\n2. ZWINGEND: Nenne in JEDER task_description explizit den exakten Dateinamen (z.B. test_datei.py)!\n3. Beide Schritte MÜSSEN requires_coder=true haben!"
    plan = query_ollama(ORCHESTRATOR_MODEL, plan_prompt, json_schema=planning_schema, temperature=0.1)
    if not plan:
        print("[ABBRUCH] Orchestrator konnte keinen Plan erstellen.")
        clear_vram()
        return

    for step in plan.get("steps", []):
        if should_require_coder(step["task_description"]):
            step["requires_coder"] = True

    with open(run_dir / "plan.json", "w", encoding="utf-8") as f:
        json.dump(plan, f, indent=2)

    print(f"\n[PLAN ERSTELLT]: {plan.get('objective')}")
    
    artifacts_list = []
    test_filename_memory = None
    
    for step in plan.get("steps", []):
        print(f"  -> Schritt {step['step_id']}: {step['task_description']} (Coder: {step['requires_coder']})")
        if step["requires_coder"]:
            is_test_step = "test" in step["task_description"].lower()
            
            # NEU: Wir extrahieren den Dateinamen HART aus dem Plan!
            expected_filename = extract_expected_filename(step['task_description'])
            if is_test_step and expected_filename:
                test_filename_memory = expected_filename
            
            code_schema = {
                "type": "object",
                "properties": {
                    "reasoning": {"type": "string"},
                    "filename": {"type": "string"},
                    "code": {"type": "string"},
                    "explanation": {"type": "string"}
                },
                "required": ["reasoning", "filename", "code", "explanation"],
                "additionalProperties": False
            }
            coder_prompt = f"Aufgabe: {step['task_description']}\nZiel: {user_goal}\nWICHTIG: Dateiname MUSS '{expected_filename}' sein! Verwende nur die Standardbibliothek."

            code_result = query_ollama(WORKER_MODEL, coder_prompt, json_schema=code_schema, temperature=0.1)
            if code_result:
                # Fallback Logik: Vertraue niemals dem JSON allein
                filename = code_result.get("filename", "")
                if not filename or not filename.strip():
                    filename = expected_filename or "unnamed_artifact.py"
                    
                meta = secure_write_artifact(run_id, filename, code_result.get("code", ""), is_test=is_test_step)
                artifacts_list.append(meta)

    with open(run_dir / "artifacts.json", "w", encoding="utf-8") as f:
        json.dump(artifacts_list, f, indent=2)

    max_test_retries = 2
    tests_passed = False
    test_output = ""
    last_error = ""

    for attempt in range(max_test_retries + 1):
        tests_passed, test_output = run_unit_tests_in_sandbox(run_dir)
        if tests_passed:
            break
        if attempt < max_test_retries:
            fixed, last_error = fix_code_based_on_test_failure(run_dir, test_output, last_error, expected_test_filename=test_filename_memory)
            if not fixed:
                break

    with open(run_dir / "test_report.txt", "w", encoding="utf-8") as fr:
        fr.write(test_output)

    final_status = "PASS" if tests_passed else "FAILED"
    with open(run_dir / "final_status.json", "w", encoding="utf-8") as f:
        json.dump({"status": final_status}, f, indent=2)

    if tests_passed:
        save_memory(f"Erfolg bei Ziel '{user_goal}'.")

    clear_vram()
    print(f"\n[KEYSTONE] Workflow abgeschlossen!")
    print(f"   - Sandbox Ordner: {run_dir}")
    print(f"   - Finaler Status: {final_status}")

if __name__ == "__main__":
    goal = "Schreibe ein robustes Modul."
    if len(sys.argv) > 1:
        goal = " ".join(sys.argv[1:])
    run_keystone_workflow(goal)
