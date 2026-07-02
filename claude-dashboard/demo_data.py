"""Genera transcripts sintéticos para probar el dashboard con datos de semanas.

Uso:
    python3 demo_data.py /tmp/claude-demo
    CLAUDE_DASHBOARD_DIR=/tmp/claude-demo python3 server.py
"""

from __future__ import annotations

import json
import random
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

MODELS = ["claude-fable-5", "claude-opus-4-8", "claude-sonnet-5", "claude-haiku-4-5"]
TOOLS = ["Bash", "Read", "Edit", "Write", "Grep", "Glob", "WebSearch", "WebFetch"]
SKILLS = ["test", "optimize", "code-review", "dataviz", "verify", "start", "stop"]
AGENTS = {
    "vue-expert": 0.06,        # nombre: probabilidad de fallo
    "code-reviewer": 0.03,
    "Explore": 0.02,
    "general-purpose": 0.12,
    "security-auditor": 0.20,
}
TOOL_ERROR_RATE = {"Bash": 0.09, "Edit": 0.05, "WebFetch": 0.15}


def _line(session: str, ts: datetime, **kw) -> dict:
    return {
        "sessionId": session,
        "timestamp": ts.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
        "uuid": str(uuid.uuid4()),
        "isSidechain": kw.pop("isSidechain", False),
        "cwd": "/home/user/inventory-management",
        "version": "2.1.198",
        **kw,
    }


def _usage(rng: random.Random) -> dict:
    return {
        "input_tokens": rng.randint(500, 6000),
        "output_tokens": rng.randint(100, 3000),
        "cache_read_input_tokens": rng.randint(5000, 120000),
        "cache_creation_input_tokens": rng.randint(0, 30000),
    }


def generate(base: Path, weeks: int = 6, seed: int = 7) -> None:
    rng = random.Random(seed)
    proj = base / "projects" / "-home-user-inventory-management"
    proj.mkdir(parents=True, exist_ok=True)
    skills_dir = base / "skills"
    for s in SKILLS + ["keybindings-help", "init"]:  # dos skills que nunca se usan
        d = skills_dir / s
        d.mkdir(parents=True, exist_ok=True)
        (d / "SKILL.md").write_text(f"---\nname: {s}\n---\n")

    now = datetime.now(timezone.utc)
    for day_offset in range(weeks * 7, -1, -1):
        day = now - timedelta(days=day_offset)
        # Más actividad entre semana; fines de semana flojos.
        weekday = day.weekday()
        base_sessions = [3, 4, 3, 4, 2, 1, 0][weekday]
        n_sessions = max(0, base_sessions + rng.randint(-1, 1))
        for _ in range(n_sessions):
            session = str(uuid.uuid4())
            lines: list[dict] = []
            ts = day.replace(hour=rng.randint(8, 19), minute=rng.randint(0, 59))
            model = rng.choice(MODELS)
            for _turn in range(rng.randint(2, 7)):
                ts += timedelta(minutes=rng.randint(1, 9))
                lines.append(
                    _line(session, ts, type="user",
                          message={"role": "user", "content": f"tarea {_turn}"})
                )
                # Respuesta con tool calls
                for _call in range(rng.randint(1, 5)):
                    ts += timedelta(seconds=rng.randint(20, 200))
                    req = f"req_{uuid.uuid4().hex[:12]}"
                    roll = rng.random()
                    if roll < 0.06:
                        skill = rng.choice(SKILLS)
                        tool = {"type": "tool_use", "id": f"toolu_{uuid.uuid4().hex[:12]}",
                                "name": "Skill", "input": {"skill": skill}}
                    elif roll < 0.16:
                        agent = rng.choice(list(AGENTS))
                        prompt = f"subtarea {uuid.uuid4().hex[:8]} para {agent}"
                        tool = {"type": "tool_use", "id": f"toolu_{uuid.uuid4().hex[:12]}",
                                "name": "Task",
                                "input": {"subagent_type": agent, "prompt": prompt,
                                          "description": "demo"}}
                    else:
                        name = rng.choice(TOOLS)
                        tool = {"type": "tool_use", "id": f"toolu_{uuid.uuid4().hex[:12]}",
                                "name": name, "input": {}}
                    lines.append(
                        _line(session, ts, type="assistant", requestId=req,
                              message={"role": "assistant", "model": model,
                                       "usage": _usage(rng), "content": [tool]})
                    )
                    # Resultado (con error según la tasa del tool/agente)
                    ts += timedelta(seconds=rng.randint(5, 120))
                    if tool["name"] == "Task":
                        err = rng.random() < AGENTS[tool["input"]["subagent_type"]]
                        _sidechain(lines, rng, session, ts, tool["input"]["prompt"], model)
                    else:
                        err = rng.random() < TOOL_ERROR_RATE.get(tool["name"], 0.01)
                    lines.append(
                        _line(session, ts, type="user",
                              message={"role": "user", "content": [
                                  {"type": "tool_result", "tool_use_id": tool["id"],
                                   "is_error": err,
                                   "content": "error" if err else "ok"}]})
                    )
                ts += timedelta(seconds=rng.randint(10, 60))
                req = f"req_{uuid.uuid4().hex[:12]}"
                lines.append(
                    _line(session, ts, type="assistant", requestId=req,
                          message={"role": "assistant", "model": model,
                                   "usage": _usage(rng),
                                   "content": [{"type": "text", "text": "hecho"}]})
                )
            out = proj / f"{session}.jsonl"
            with out.open("w") as fh:
                for line in lines:
                    fh.write(json.dumps(line) + "\n")
    print(f"Datos de demo generados en {base}")


def _sidechain(lines: list[dict], rng: random.Random, session: str,
               ts: datetime, prompt: str, model: str) -> None:
    """Transcript del subagente enlazado por parentUuid a partir de una raíz."""
    root = _line(session, ts, type="user", isSidechain=True, parentUuid=None,
                 message={"role": "user", "content": prompt})
    lines.append(root)
    parent = root["uuid"]
    for _ in range(rng.randint(2, 8)):
        ts += timedelta(seconds=rng.randint(10, 90))
        name = rng.choice(TOOLS[:6])
        tool_id = f"toolu_{uuid.uuid4().hex[:12]}"
        node = _line(session, ts, type="assistant", isSidechain=True, parentUuid=parent,
                     requestId=f"req_{uuid.uuid4().hex[:12]}",
                     message={"role": "assistant", "model": model, "usage": _usage(rng),
                              "content": [{"type": "tool_use", "id": tool_id,
                                           "name": name, "input": {}}]})
        lines.append(node)
        parent = node["uuid"]
        ts += timedelta(seconds=rng.randint(5, 60))
        err = rng.random() < TOOL_ERROR_RATE.get(name, 0.01)
        node = _line(session, ts, type="user", isSidechain=True, parentUuid=parent,
                     message={"role": "user", "content": [
                         {"type": "tool_result", "tool_use_id": tool_id,
                          "is_error": err, "content": "error" if err else "ok"}]})
        lines.append(node)
        parent = node["uuid"]


if __name__ == "__main__":
    target = Path(sys.argv[1] if len(sys.argv) > 1 else "/tmp/claude-demo")
    generate(target)
