import json
import os
from pathlib import Path

from .core import Keystone


def main() -> int:
    data_dir = Path(os.getenv("KEYSTONE_DATA_DIR", "data"))
    core = Keystone(data_dir, os.getenv("KEYSTONE_OLLAMA_URL", "http://127.0.0.1:11434"), os.getenv("KEYSTONE_OLLAMA_MODEL", "llama3.2:3b"))
    print(json.dumps(core.health(), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
