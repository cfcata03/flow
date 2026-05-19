
import re
from dataclasses import dataclass, field


@dataclass
class Step:
    name: str
    cmd: str
    desc: str = ""
    confirm: bool = False


@dataclass
class Runbook:
    name: str
    desc: str = ""
    tags: list[str] = field(default_factory=list)
    steps: list[Step] = field(default_factory=list)

    def all_vars(self) -> list[str]:
        seen, result = set(), []
        for step in self.steps:
            for v in re.findall(r'\{\{(\w+)\}\}', step.cmd):
                if v not in seen:
                    result.append(v)
                    seen.add(v)
        return result

    def render_step_cmd(self, cmd: str, values: dict[str, str]) -> str:
        for k, v in values.items():
            cmd = cmd.replace(f'{{{{{k}}}}}', v)
        return cmd
