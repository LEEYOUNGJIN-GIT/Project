#!/usr/bin/env python3
"""
CISA 문제 생성 — 단일 진입점 (로직 트리)

환경변수:
  CISA_MODE   D1 | D2 | D3 | D4 | D5 | CROSS  (워크플로 YAML에서 고정)
  CISA_PHASE  1 = 문제만, 2 = 정답+해설
  CISA_COUNT  문항 수 (미설정 시 domains.yaml default_count)
  GEMINI_API_KEY
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

try:
    import google.generativeai as genai
except ImportError:
    print("pip install -r CISA/scripts/requirements.txt", file=sys.stderr)
    raise

ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / "CISA" / "config" / "domains.yaml"
PROMPTS_DIR = ROOT / "CISA" / "prompts"


@dataclass
class GenerationPlan:
    mode: str
    mode_type: str  # single | cross
    label: str
    question_count: int
    phase: str
    context_files: list[Path] = field(default_factory=list)
    user_instructions: str = ""
    cross_pairs: list[dict[str, Any]] = field(default_factory=list)


def load_config() -> dict[str, Any]:
    with CONFIG_PATH.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def read_text(path: Path, max_chars: int | None = None) -> str:
    if not path.exists():
        raise FileNotFoundError(f"Missing material: {path}")
    text = path.read_text(encoding="utf-8")
    if max_chars and len(text) > max_chars:
        return text[:max_chars] + "\n\n[... 이하 MASTER 본문 생략 — 토큰 한도 ...]\n"
    return text


def master_excerpt(materials: Path, max_chars: int) -> str:
    master = materials / "MASTER_SYSTEM.md"
    text = read_text(master)
    marker = "**도메인 간 교차 출제 매핑"
    idx = text.find(marker)
    head = text[: min(80000, len(text))]
    cross_block = text[idx : idx + 12000] if idx != -1 else ""
    combined = head + "\n\n---\n\n" + cross_block
    if len(combined) > max_chars:
        combined = combined[:max_chars]
    return combined


def domain_file(materials: Path, domain_id: str) -> Path:
    mapping = {
        "D1": "D1_IS감사프로세스.md",
        "D2": "D2_거버넌스IT관리.md",
        "D3": "D3_시스템도입개발구현.md",
        "D4": "D4_운영비즈니스복원성.md",
        "D5": "D5_정보자산보호.md",
    }
    return materials / mapping[domain_id]


# ─── 로직 트리: MODE 분기 ───────────────────────────────────────────

def resolve_plan(cfg: dict[str, Any], mode: str) -> GenerationPlan:
    """CISA_MODE → GenerationPlan (파일 목록 + user 프롬프트)."""
    materials = ROOT / cfg["repo"]["materials_dir"]
    shared = cfg["shared"]
    modes = cfg["modes"]
    if mode not in modes:
        raise ValueError(f"Unknown CISA_MODE={mode}. Expected: {list(modes.keys())}")

    spec = modes[mode]
    count_raw = os.environ.get("CISA_COUNT", "").strip()
    count = int(count_raw) if count_raw else int(spec.get("default_count", 2))
    phase = os.environ.get("CISA_PHASE", shared.get("phase_default", "1"))

    always: list[Path] = []
    for name in shared["always_load"]:
        p = materials / name
        if p.exists():
            always.append(p)
    brief = PROMPTS_DIR / "generation_brief.md"
    if brief.exists():
        always.insert(0, brief)

    master = materials / "MASTER_SYSTEM.md"
    ctx: list[Path] = list(always)
    if master.exists():
        ctx.append(master)

    mode_type = spec["type"]

    if mode_type == "single":
        ctx.append(materials / spec["source_file"])
        user = _single_domain_prompt(mode, spec, count, phase)
        return GenerationPlan(
            mode=mode,
            mode_type="single",
            label=spec["label"],
            question_count=count,
            phase=phase,
            context_files=_dedupe_paths(ctx),
            user_instructions=user,
        )

    if mode_type == "cross":
        pairs = spec["cross_pairs"]
        for pair in pairs:
            for d in pair["domains"]:
                ctx.append(domain_file(materials, d))
        user = _cross_domain_prompt(spec, pairs, count, phase)
        return GenerationPlan(
            mode=mode,
            mode_type="cross",
            label=spec["label"],
            question_count=count,
            phase=phase,
            context_files=_dedupe_paths(ctx),
            user_instructions=user,
            cross_pairs=pairs,
        )

    raise ValueError(f"Unsupported mode type: {mode_type}")


def _dedupe_paths(paths: list[Path]) -> list[Path]:
    seen: set[str] = set()
    out: list[Path] = []
    for p in paths:
        key = str(p.resolve())
        if key not in seen:
            seen.add(key)
            out.append(p)
    return out


def _single_domain_prompt(mode: str, spec: dict, count: int, phase: str) -> str:
    phase_rule = (
        "1단계만 출력: 문제와 선지(A~D)만. 정답·해설·정답 문자 절대 금지."
        if phase == "1"
        else "2단계만 출력: 정답 문자와 해설(§18 형식). 문제 본문은 반복하지 않는다."
    )
    return f"""
[CISA_MODE={mode}] {spec["label"]}
ECO 비중: {spec.get("eco_weight", "")}
문항 수: {count}문항 (이 도메인 집중 — 다른 도메인 혼입 금지)
Track: {spec.get("track_ratio", "A 70% / B 30%")}
난이도: 고난도 집중 (상·최상 90% 목표)
함축 밀도: 2·3 위주

{phase_rule}

§16 STEP 0~8 순서를 내부적으로 따른 뒤 출력한다.
품질 미달 문항은 제외하고, 확보된 문항만 PART 단위로 출력한다.
"""


def _cross_domain_prompt(spec: dict, pairs: list[dict], count: int, phase: str) -> str:
    phase_rule = (
        "1단계만: 문제와 선지만."
        if phase == "1"
        else "2단계만: 정답+해설."
    )
    pair_lines = "\n".join(
        f"- {p['id']} ({p['frequency']}): {p['topics']}"
        for p in pairs
    )
    return f"""
[CISA_MODE=CROSS] {spec["label"]}
문항 수: {count}문항 — **모두 2개 이상 도메인 지식이 교차**되어야 한다.
Track: {spec.get("track_ratio", "A 80% / B 20%")}
{phase_rule}

교차 출제 매핑 (문항당 서로 다른 pair 우선):
{pair_lines}

각 문항 헤더에 적용 pair를 명시: 예) `[CROSS D2-D5]`
정답은 ISACA 감사인 관점(§7)으로만 판단한다.
"""


def build_system_instruction(plan: GenerationPlan, cfg: dict[str, Any]) -> str:
    materials = ROOT / cfg["repo"]["materials_dir"]
    max_master = cfg["shared"]["master_excerpt_max_chars"]
    parts: list[str] = []

    for path in plan.context_files:
        if path.name == "MASTER_SYSTEM.md":
            parts.append(
                f"## MASTER_SYSTEM (발췌)\n{master_excerpt(materials, max_master)}"
            )
        else:
            rel = path.relative_to(ROOT) if path.is_relative_to(ROOT) else path
            parts.append(f"## {rel}\n{read_text(path)}")

    parts.append(
        f"""
## 실행 컨텍스트
- mode: {plan.mode} ({plan.mode_type})
- label: {plan.label}
- phase: {plan.phase}
- questions: {plan.question_count}
"""
    )
    return "\n\n".join(parts)


def call_gemini(system: str, user: str, model_name: str) -> str:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise EnvironmentError("GEMINI_API_KEY is not set")
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(
        model_name=model_name,
        system_instruction=system,
    )
    response = model.generate_content(user)
    return response.text or ""


def write_output(plan: GenerationPlan, body: str, cfg: dict[str, Any]) -> Path:
    out_dir = ROOT / cfg["repo"]["output_dir"]
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    name = f"{plan.mode}_phase{plan.phase}_{plan.question_count}q_{ts}.md"
    path = out_dir / name
    header = f"""---
cisa_mode: {plan.mode}
mode_type: {plan.mode_type}
label: {plan.label}
phase: {plan.phase}
question_count: {plan.question_count}
generated_at: {ts}
---

"""
    path.write_text(header + body, encoding="utf-8")
    print(f"Wrote {path.relative_to(ROOT)}")
    return path


def main() -> None:
    mode = os.environ.get("CISA_MODE", "").strip().upper()
    if not mode:
        print("Set CISA_MODE to D1|D2|D3|D4|D5|CROSS", file=sys.stderr)
        sys.exit(1)

    cfg = load_config()
    plan = resolve_plan(cfg, mode)
    system = build_system_instruction(plan, cfg)
    model_name = os.environ.get("GEMINI_MODEL", cfg["shared"]["model"])
    text = call_gemini(system, plan.user_instructions, model_name)
    write_output(plan, text, cfg)


if __name__ == "__main__":
    main()
