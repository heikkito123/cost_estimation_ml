from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

@dataclass
class AgentContext:
    project_root: Path
    memory_file: Path
    allowed_dirs: list[Path] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    #tools: list[Any] = field(default_factory=list)

    def is_allowed_path(self, path: Path) -> bool:
        path = path.resolve()
        return any(path.is_relative_to(d.resolve()) for d in self.allowed_dirs)
    