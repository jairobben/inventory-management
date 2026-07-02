"""Analizador de transcripts de Claude Code.

Lee los ficheros JSONL de ~/.claude/projects (o del directorio indicado en
CLAUDE_DASHBOARD_DIR) y produce agregados por día, skill, tool, agente y modelo.
Solo usa la biblioteca estándar.
"""

from __future__ import annotations

import json
import os
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

# Precio por millón de tokens (entrada, salida). El coste de caché se aproxima:
# lectura 0.1x entrada, escritura 1.25x entrada.
PRICING = {
    "claude-fable-5": (10.0, 50.0),
    "claude-mythos-5": (10.0, 50.0),
    "claude-opus-4-8": (5.0, 25.0),
    "claude-opus-4-7": (5.0, 25.0),
    "claude-opus-4-6": (5.0, 25.0),
    "claude-sonnet-5": (3.0, 15.0),
    "claude-sonnet-4-6": (3.0, 15.0),
    "claude-haiku-4-5": (1.0, 5.0),
}
DEFAULT_PRICE = (5.0, 25.0)


def _price_for(model: str) -> tuple[float, float]:
    for key, price in PRICING.items():
        if model.startswith(key):
            return price
    return DEFAULT_PRICE


def claude_dir() -> Path:
    env = os.environ.get("CLAUDE_DASHBOARD_DIR")
    if env:
        return Path(env)
    return Path.home() / ".claude"


def _iter_transcript_files(base: Path):
    projects = base / "projects"
    if not projects.is_dir():
        return
    yield from projects.glob("*/*.jsonl")


def _parse_ts(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    # Se agrupa por fecha local: el usuario ejecuta esto en su propia máquina.
    return dt.astimezone()


def _content_blocks(message: dict) -> list[dict]:
    content = message.get("content")
    if isinstance(content, list):
        return [b for b in content if isinstance(b, dict)]
    return []


def _text_of(message: dict) -> str:
    content = message.get("content")
    if isinstance(content, str):
        return content
    parts = []
    for block in _content_blocks(message):
        if block.get("type") == "text":
            parts.append(block.get("text", ""))
    return "\n".join(parts)


def installed_skills(base: Path, project_dirs: set[str]) -> list[str]:
    """Skills instaladas: las de usuario (~/.claude/skills) y las de cada proyecto."""
    names: set[str] = set()
    roots = [base / "skills"]
    for cwd in project_dirs:
        roots.append(Path(cwd) / ".claude" / "skills")
    for root in roots:
        if not root.is_dir():
            continue
        for child in sorted(root.iterdir()):
            if child.is_dir() and (child / "SKILL.md").exists():
                names.add(child.name)
    return sorted(names)


class Aggregator:
    def __init__(self) -> None:
        self.days: dict[str, dict] = defaultdict(
            lambda: {
                "sessions": set(),
                "prompts": 0,
                "assistant_turns": 0,
                "tool_calls": 0,
                "errors": 0,
                "input_tokens": 0,
                "output_tokens": 0,
                "cache_read_tokens": 0,
                "cache_write_tokens": 0,
                "cost_usd": 0.0,
                "skills": defaultdict(int),
                "tools": defaultdict(int),
                "agents": defaultdict(int),
            }
        )
        self.skill_last_used: dict[str, str] = {}
        self.tool_errors: dict[str, int] = defaultdict(int)
        self.tool_calls: dict[str, int] = defaultdict(int)
        self.models: dict[str, dict] = defaultdict(
            lambda: {"requests": 0, "input_tokens": 0, "output_tokens": 0, "cost_usd": 0.0}
        )
        self.agents: dict[str, dict] = defaultdict(
            lambda: {
                "invocations": 0,
                "failures": 0,
                "internal_errors": 0,
                "tokens": 0,
                "tool_calls": 0,
                "tools": defaultdict(int),
                "durations_s": [],
            }
        )
        self.project_dirs: set[str] = set()
        self.sessions_meta: dict[str, dict] = {}

    def to_dict(self) -> dict:
        days = {}
        for day, d in sorted(self.days.items()):
            days[day] = {
                "sessions": len(d["sessions"]),
                "prompts": d["prompts"],
                "assistant_turns": d["assistant_turns"],
                "tool_calls": d["tool_calls"],
                "errors": d["errors"],
                "input_tokens": d["input_tokens"],
                "output_tokens": d["output_tokens"],
                "cache_read_tokens": d["cache_read_tokens"],
                "cache_write_tokens": d["cache_write_tokens"],
                "cost_usd": round(d["cost_usd"], 4),
                "skills": dict(d["skills"]),
                "tools": dict(d["tools"]),
                "agents": dict(d["agents"]),
            }
        agents = {}
        for name, a in self.agents.items():
            durations = a["durations_s"]
            agents[name] = {
                "invocations": a["invocations"],
                "failures": a["failures"],
                "internal_errors": a["internal_errors"],
                "tokens": a["tokens"],
                "tool_calls": a["tool_calls"],
                "tools": dict(a["tools"]),
                "avg_duration_s": round(sum(durations) / len(durations), 1) if durations else None,
            }
        return {
            "days": days,
            "skill_last_used": self.skill_last_used,
            "tools": {
                name: {"calls": count, "errors": self.tool_errors.get(name, 0)}
                for name, count in self.tool_calls.items()
            },
            "models": {
                name: {**m, "cost_usd": round(m["cost_usd"], 4)}
                for name, m in self.models.items()
            },
            "agents": agents,
        }


def _record_usage(agg: Aggregator, day: dict, model: str, usage: dict) -> None:
    inp = usage.get("input_tokens", 0) or 0
    out = usage.get("output_tokens", 0) or 0
    cache_read = usage.get("cache_read_input_tokens", 0) or 0
    cache_write = usage.get("cache_creation_input_tokens", 0) or 0
    in_price, out_price = _price_for(model)
    cost = (
        inp * in_price
        + out * out_price
        + cache_read * in_price * 0.1
        + cache_write * in_price * 1.25
    ) / 1_000_000
    day["input_tokens"] += inp
    day["output_tokens"] += out
    day["cache_read_tokens"] += cache_read
    day["cache_write_tokens"] += cache_write
    day["cost_usd"] += cost
    m = agg.models[model]
    m["requests"] += 1
    m["input_tokens"] += inp
    m["output_tokens"] += out
    m["cost_usd"] += cost


def _analyze_file(agg: Aggregator, path: Path) -> None:
    entries = []
    with path.open(encoding="utf-8", errors="replace") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(obj, dict):
                entries.append(obj)

    by_uuid = {e["uuid"]: e for e in entries if e.get("uuid")}
    seen_requests: set[str] = set()
    # tool_use id -> (nombre de tool, entrada, fecha, uuid del assistant, sidechain)
    tool_uses: dict[str, dict] = {}
    task_prompts: list[dict] = []  # llamadas al tool de agentes (Task/Agent)

    for e in entries:
        etype = e.get("type")
        ts = _parse_ts(e.get("timestamp"))
        if e.get("cwd"):
            agg.project_dirs.add(e["cwd"])
        if not ts or etype not in ("user", "assistant"):
            continue
        day_key = ts.strftime("%Y-%m-%d")
        day = agg.days[day_key]
        if e.get("sessionId"):
            day["sessions"].add(e["sessionId"])
        sidechain = bool(e.get("isSidechain"))
        message = e.get("message") or {}

        if etype == "assistant":
            if not sidechain:
                day["assistant_turns"] += 1
            model = message.get("model") or "unknown"
            usage = message.get("usage") or {}
            request_id = e.get("requestId")
            # Varias líneas assistant pueden compartir requestId (una por bloque);
            # el uso se contabiliza una sola vez por petición.
            if usage and (request_id not in seen_requests):
                if request_id:
                    seen_requests.add(request_id)
                _record_usage(agg, day, model, usage)
            skill_attr = e.get("attributionSkill")
            for block in _content_blocks(message):
                if block.get("type") != "tool_use":
                    continue
                name = block.get("name") or "unknown"
                block_input = block.get("input") or {}
                tool_uses[block.get("id")] = {
                    "name": name,
                    "day": day_key,
                    "sidechain": sidechain,
                    "uuid": e.get("uuid"),
                }
                day["tool_calls"] += 1
                day["tools"][name] += 1
                agg.tool_calls[name] += 1
                if name in ("Skill",) and block_input.get("skill"):
                    skill = str(block_input["skill"])
                    day["skills"][skill] += 1
                    prev = agg.skill_last_used.get(skill)
                    if not prev or day_key > prev:
                        agg.skill_last_used[skill] = day_key
                if name in ("Task", "Agent") and block_input.get("subagent_type"):
                    agent = str(block_input["subagent_type"])
                    day["agents"][agent] += 1
                    agg.agents[agent]["invocations"] += 1
                    task_prompts.append(
                        {
                            "agent": agent,
                            "prompt": str(block_input.get("prompt", ""))[:400],
                            "tool_use_id": block.get("id"),
                        }
                    )
            if skill_attr and isinstance(skill_attr, str):
                prev = agg.skill_last_used.get(skill_attr)
                if not prev or day_key > prev:
                    agg.skill_last_used.setdefault(skill_attr, day_key)

        elif etype == "user":
            content = message.get("content")
            is_tool_result = False
            if isinstance(content, list):
                for block in _content_blocks(message):
                    if block.get("type") != "tool_result":
                        continue
                    is_tool_result = True
                    use = tool_uses.get(block.get("tool_use_id"))
                    if block.get("is_error"):
                        day["errors"] += 1
                        if use:
                            agg.tool_errors[use["name"]] += 1
                            if use["name"] in ("Task", "Agent"):
                                for tp in task_prompts:
                                    if tp["tool_use_id"] == block.get("tool_use_id"):
                                        agg.agents[tp["agent"]]["failures"] += 1
            if not is_tool_result and not e.get("isMeta") and not sidechain:
                text = _text_of(message)
                if text and not text.startswith("<"):
                    day["prompts"] += 1

    _link_sidechains(agg, entries, by_uuid, task_prompts, seen_requests)


def _link_sidechains(
    agg: Aggregator,
    entries: list[dict],
    by_uuid: dict[str, dict],
    task_prompts: list[dict],
    seen_requests: set[str],
) -> None:
    """Asocia cadenas sidechain (transcript del subagente) con el tipo de agente
    que las lanzó, emparejando el primer mensaje del sidechain con el prompt
    de la llamada a Task/Agent."""
    roots = [
        e
        for e in entries
        if e.get("isSidechain")
        and e.get("type") == "user"
        and (e.get("parentUuid") is None or e.get("parentUuid") not in by_uuid)
    ]
    children: dict[str, list[dict]] = defaultdict(list)
    for e in entries:
        if e.get("isSidechain") and e.get("parentUuid"):
            children[e["parentUuid"]].append(e)

    for root in roots:
        root_text = _text_of(root.get("message") or {})
        agent = None
        for tp in task_prompts:
            if tp["prompt"] and root_text.startswith(tp["prompt"][:120]):
                agent = tp["agent"]
                break
        if agent is None:
            agent = "(desconocido)"
        stats = agg.agents[agent]
        # Recorre la cadena completa a partir de la raíz.
        stack = [root]
        first_ts = last_ts = _parse_ts(root.get("timestamp"))
        while stack:
            node = stack.pop()
            stack.extend(children.get(node.get("uuid") or "", []))
            ts = _parse_ts(node.get("timestamp"))
            if ts:
                first_ts = min(first_ts or ts, ts)
                last_ts = max(last_ts or ts, ts)
            message = node.get("message") or {}
            if node.get("type") == "assistant":
                usage = message.get("usage") or {}
                stats["tokens"] += (usage.get("input_tokens", 0) or 0) + (
                    usage.get("output_tokens", 0) or 0
                )
                for block in _content_blocks(message):
                    if block.get("type") == "tool_use":
                        stats["tool_calls"] += 1
                        stats["tools"][block.get("name") or "unknown"] += 1
            elif node.get("type") == "user":
                for block in _content_blocks(message):
                    if block.get("type") == "tool_result" and block.get("is_error"):
                        stats["internal_errors"] += 1
        if first_ts and last_ts and last_ts > first_ts:
            stats["durations_s"].append((last_ts - first_ts).total_seconds())


def analyze() -> dict:
    base = claude_dir()
    agg = Aggregator()
    files = list(_iter_transcript_files(base))
    for path in files:
        try:
            _analyze_file(agg, path)
        except OSError:
            continue
    result = agg.to_dict()
    used_skills = set(result["skill_last_used"])
    installed = installed_skills(base, agg.project_dirs)
    result["skills_installed"] = installed
    result["skills_unused"] = sorted(set(installed) - used_skills)
    result["generated_at"] = datetime.now(timezone.utc).isoformat()
    result["transcript_files"] = len(files)
    return result


if __name__ == "__main__":
    print(json.dumps(analyze(), indent=2, ensure_ascii=False))
