from pathlib import Path
from typing import Optional

import yaml

from .runbook import Runbook, Step

FLOW_DIR = Path.home() / ".flow" / "runbooks"


def _ensure() -> None:
    FLOW_DIR.mkdir(parents=True, exist_ok=True)


def _path(name: str) -> Path:
    return FLOW_DIR / f"{name}.yaml"


def parse_runbook(data: dict) -> Runbook:
    steps = [
        Step(
            name=s["name"],
            cmd=s["cmd"],
            desc=s.get("desc", ""),
            confirm=s.get("confirm", False),
        )
        for s in data.get("steps", [])
    ]
    return Runbook(
        name=data["name"],
        desc=data.get("desc", ""),
        tags=data.get("tags", []),
        steps=steps,
    )


def load_all() -> list[Runbook]:
    _ensure()
    runbooks = []
    for f in sorted(FLOW_DIR.glob("*.yaml")):
        try:
            runbooks.append(load_one(f.stem))
        except Exception:
            pass
    return runbooks


def load_one(name: str) -> Optional[Runbook]:
    path = _path(name)
    if not path.exists():
        return None
    data = yaml.safe_load(path.read_text())
    return parse_runbook(data)


def save(runbook: Runbook) -> None:
    _ensure()
    data = {
        "name": runbook.name,
        "desc": runbook.desc,
        "tags": runbook.tags,
        "steps": [
            {
                "name": s.name,
                "cmd": s.cmd,
                **( {"desc": s.desc} if s.desc else {} ),
                **( {"confirm": True} if s.confirm else {} ),
            }
            for s in runbook.steps
        ],
    }
    _path(runbook.name).write_text(
        yaml.dump(data, default_flow_style=False, allow_unicode=True, sort_keys=False)
    )


def delete(name: str) -> bool:
    path = _path(name)
    if path.exists():
        path.unlink()
        return True
    return False


def exists(name: str) -> bool:
    return _path(name).exists()


def runbook_template(name: str) -> str:
    return f"""\
name: {name}
desc: ""
tags: []

steps:
  - name: First step
    cmd: echo "hello {{{{who}}}}"

  - name: Second step
    cmd: echo "done"
"""
