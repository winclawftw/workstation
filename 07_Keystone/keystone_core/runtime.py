import shlex
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from .contracts import AgentRuntime, ExecutionFailed, RuntimeUnavailable

__all__ = ["AgentRuntime", "HermesRuntime"]


class HermesRuntime:
    name = "hermes"
    version = "0.21.3"

    def __init__(self, distro: str = "Ubuntu-24.04", hermes_home: str = "/mnt/c/Einrichtung/06_Hermes/home", timeout: int = 180):
        self.distro = distro
        self.hermes_home = hermes_home
        self.timeout = timeout

    def capabilities(self) -> set[str]:
        return {"chat", "local_model", "tool_calling"}

    def _command(self, args: list[str]) -> list[str]:
        command = " ".join(shlex.quote(arg) for arg in args)
        env = f'export HERMES_HOME={shlex.quote(self.hermes_home)}; export PATH="/root/.local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"; '
        return ["wsl.exe", "-d", self.distro, "--", "bash", "-lc", env + command]

    def health(self) -> dict[str, Any]:
        try:
            result = subprocess.run(self._command(["command", "-v", "hermes"]), capture_output=True, text=True, timeout=15, check=False)
        except OSError as exc:
            raise RuntimeUnavailable(str(exc)) from exc
        if result.returncode != 0:
            raise RuntimeUnavailable(result.stderr.strip() or "Hermes unavailable")
        return {"status": "ok", "runtime": self.name, "path": result.stdout.strip()}

    def run(self, prompt: str, *, model: str | None = None) -> str:
        args = ["hermes", "chat", "--provider", "custom", "--reasoning", "none", "--toolsets", ""]
        if model:
            args.extend(["--model", model])
        args.extend(["--oneshot", "-Q", "-q", prompt])
        try:
            with tempfile.TemporaryDirectory(prefix="keystone-hermes-") as directory:
                stdout_path = Path(directory) / "stdout.txt"
                stderr_path = Path(directory) / "stderr.txt"
                with stdout_path.open("w", encoding="utf-8") as stdout, stderr_path.open("w", encoding="utf-8") as stderr:
                    result = subprocess.run(self._command(args), stdout=stdout, stderr=stderr, text=True, timeout=self.timeout, check=False)
                stdout_text = stdout_path.read_text(encoding="utf-8", errors="replace")
                stderr_text = stderr_path.read_text(encoding="utf-8", errors="replace")
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise ExecutionFailed(str(exc)) from exc
        if result.returncode != 0:
            raise ExecutionFailed(stderr_text.strip() or stdout_text.strip() or "Hermes execution failed")
        return stdout_text.strip()
