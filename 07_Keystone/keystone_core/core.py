from pathlib import Path
from typing import Any

from .contracts import ModelUnavailable, PolicyDenied
from .domain import Agent, Job, Project, Task, new_id
from .events import AuditLogger, EventBus
from .models import OllamaModelProvider
from .policy import ApprovalService, PolicyEngine
from .runtime import HermesRuntime
from .storage import LocalStorage
from .tools import ReadOnlyToolProvider


class Keystone:
    def __init__(self, data_dir: str | Path = "data", ollama_url: str = "http://127.0.0.1:11434", model: str = "llama3.2:3b"):
        self.storage = LocalStorage(data_dir)
        self.events = EventBus(self.storage)
        self.audit = AuditLogger(self.storage)
        self.policy = PolicyEngine()
        self.approvals = ApprovalService()
        self.runtime = HermesRuntime()
        self.model_provider = OllamaModelProvider(ollama_url, model)
        self.tools = ReadOnlyToolProvider()

    def health(self) -> dict[str, Any]:
        return {
            "core": {"status": "ok", "name": "keystone"},
            "runtime": self.runtime.health(),
            "model_provider": self.model_provider.health(),
            "storage": self.storage.health(),
            "tool_provider": self.tools.health(),
        }

    def create_project(self, name: str, description: str = "") -> Project:
        project = Project(new_id("prj"), name, description)
        self.storage.save("projects", project)
        self.events.publish("project.created", project_id=project.id)
        return project

    def create_task(self, project_id: str, title: str) -> Task:
        task = Task(new_id("tsk"), project_id, title)
        self.storage.save("tasks", task)
        self.events.publish("task.created", task_id=task.id, project_id=project_id)
        return task

    def register_agent(self, name: str, runtime: str = "hermes") -> Agent:
        agent = Agent(new_id("agt"), name, runtime)
        self.storage.save("agents", agent)
        return agent

    def run_task(self, task: Task, prompt: str, *, model: str | None = None) -> str:
        job = Job(new_id("job"), task.id, "running")
        self.storage.save("jobs", job)
        self.events.publish("task.started", task_id=task.id, job_id=job.id)
        self.events.publish("runtime.started", runtime=self.runtime.name, job_id=job.id)
        try:
            selected_model = model or self.model_provider.default_model
            self.model_provider.health()
            if selected_model not in self.model_provider.list_models():
                raise ModelUnavailable(f"model unavailable: {selected_model}")
            result = self.runtime.run(prompt, model=selected_model)
        except Exception as exc:
            self.events.publish("runtime.failed", job_id=job.id, error=type(exc).__name__)
            self.audit.record("runtime.failed", job_id=job.id, error=type(exc).__name__)
            raise
        self.events.publish("runtime.completed", job_id=job.id)
        self.events.publish("task.completed", task_id=task.id, job_id=job.id)
        self.audit.record("task.completed", task_id=task.id, job_id=job.id)
        return result

    def execute_tool(self, name: str, arguments: dict[str, Any] | None = None) -> Any:
        decision = self.policy.evaluate("read")
        if not decision.approved:
            self.events.publish("tool.denied", tool=name, reason=decision.reason)
            raise PolicyDenied(decision.reason)
        self.events.publish("tool.requested", tool=name)
        result = self.tools.execute(name, arguments)
        self.events.publish("tool.executed", tool=name)
        self.audit.record("tool.executed", tool=name)
        return result
