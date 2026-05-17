#!/usr/bin/env python3
"""GraphRAG Extraction Eval (v0.4.2) — precision/recall/F1 자동 측정.

vs ingest_graph.py (룰베이스) / ingest_llm.py (LLM):
- 이 둘의 결과를 정답(gold)과 비교
- 또는 두 추출기 결과끼리 일관성 측정 (gold 없을 때)

설계:
- gold (정답): vault/03_schema/eval-gold/<slug>.yaml — 사람이 라벨링
  - 자동 시드: 룰베이스 결과를 gold 초안으로 (사람 검수 후 보강)
- 메트릭: precision (검출∩정답 / 검출), recall (검출∩정답 / 정답), F1
- entity 와 relation 별도 측정

사용:
    # 자동 시드 (룰베이스 결과 → gold 초안)
    python services/graph/eval.py --seed vault/02_wiki/topics/<slug>.md

    # rule vs gold
    python services/graph/eval.py --mode rule vault/02_wiki/topics/<slug>.md

    # LLM vs gold (LLM 호출 필요)
    DRY_RUN=0 python services/graph/eval.py --mode llm vault/02_wiki/topics/<slug>.md

    # rule vs LLM (일관성, gold 없어도 가능)
    python services/graph/eval.py --mode consistency vault/02_wiki/topics/<slug>.md

    # 전체 gold 디렉터리 일괄 평가
    python services/graph/eval.py --all --mode rule
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
GOLD_DIR = REPO_ROOT / "vault" / "03_schema" / "eval-gold"


def slugify(stem: str) -> str:
    """파일 stem 에서 날짜 prefix 제거 → 짧은 slug."""
    m = re.match(r'^\d{4}-\d{2}-\d{2}-(.+)$', stem)
    return m.group(1) if m else stem


def load_gold(slug: str) -> dict:
    """vault/03_schema/eval-gold/<slug>.yaml 로드.
    형식:
        entities:
          - canonical: Neo4j
            type: Technology
        relations:
          - src: Anthropic
            type: USES
            dst: Claude Code
    """
    path = GOLD_DIR / f"{slug}.yaml"
    if not path.exists():
        return {"entities": [], "relations": []}
    # 단순 YAML 파싱 (외부 의존 없이)
    text = path.read_text(encoding="utf-8")
    g = {"entities": [], "relations": []}
    current = None
    mode = None
    for raw in text.splitlines():
        line = raw.rstrip()
        if line.startswith("entities:"):
            if current and mode:   # mode 전환 시 미완 current append
                g[mode].append(current); current = None
            mode = "entities"
        elif line.startswith("relations:"):
            if current and mode:
                g[mode].append(current); current = None
            mode = "relations"
        elif line.startswith("  - ") and mode:
            if current:
                g[mode].append(current)
            key, _, val = line[4:].partition(":")
            current = {key.strip(): val.strip().strip('"').strip("'")}
        elif line.startswith("    ") and current and mode:
            key, _, val = line.strip().partition(":")
            current[key.strip()] = val.strip().strip('"').strip("'")
    if current and mode:
        g[mode].append(current)
    return g


def run_extractor(script: str, md_path: Path, env_path: str) -> dict:
    """ingest_graph.py 또는 ingest_llm.py 를 --dry-run 으로 실행하고 JSON 결과 파싱.
    반환: {entities: [{canonical, type}], relations: [{src, type, dst}]}
    """
    import subprocess
    cmd = ["python3", str(REPO_ROOT / "services/graph" / script),
           str(md_path), "--dry-run", "--env", env_path]
    p = subprocess.run(cmd, capture_output=True, text=True)
    # JSON 출력 시작점 찾기
    out = p.stdout
    json_start = out.find("{")
    if json_start < 0:
        return {"entities": [], "relations": []}
    try:
        data = json.loads(out[json_start:])
    except json.JSONDecodeError:
        return {"entities": [], "relations": []}

    # ingest_graph.py JSON 형식: {sources, nodes, relations}
    if "nodes" in data:
        # Source 라벨은 gold 와 비교 시 제외 (의미 entity 만 평가)
        ents = [{"canonical": n.get("canonical_name", n.get("name", "")),
                 "type": n.get("label", "")} for n in data.get("nodes", [])
                if n.get("label") != "Source"]
        rels = []
        return {"entities": ents, "relations": rels}

    # ingest_llm.py (향후 JSON 출력 추가 시)
    return {"entities": data.get("nodes", []), "relations": data.get("rels", [])}


def precision_recall_f1(pred: list, gold: list, key_func) -> tuple[float, float, float, int, int, int]:
    """집합 기반 P/R/F1."""
    p_set = {key_func(x) for x in pred}
    g_set = {key_func(x) for x in gold}
    tp = len(p_set & g_set)
    fp = len(p_set - g_set)
    fn = len(g_set - p_set)
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
    return precision, recall, f1, tp, fp, fn


def seed_gold(md_path: Path, env_path: str) -> Path:
    """룰베이스 결과를 gold 초안으로 자동 생성. 사람이 검수 후 보강."""
    slug = slugify(md_path.stem)
    rule = run_extractor("ingest_graph.py", md_path, env_path)
    GOLD_DIR.mkdir(parents=True, exist_ok=True)
    gold_path = GOLD_DIR / f"{slug}.yaml"

    lines = [
        "# auto-seeded from rule-based ingest_graph.py — 사람 검수 후 보강 필요",
        f"# 출처: {md_path.relative_to(REPO_ROOT) if md_path.is_absolute() else md_path}",
        "",
        "entities:",
    ]
    for e in rule["entities"]:
        if e.get("type") in ("Source",) or not e.get("canonical"):
            continue
        lines.append(f"  - canonical: {e['canonical']}")
        lines.append(f"    type: {e['type']}")
    lines.append("")
    lines.append("relations:")
    lines.append("  # 룰베이스는 MENTIONS 만 추출. SOLVES/USES 등 의미 관계는 사람이 추가:")
    lines.append("  # - src: Anthropic")
    lines.append("  #   type: USES")
    lines.append("  #   dst: Claude Code")
    lines.append("")

    gold_path.write_text("\n".join(lines), encoding="utf-8")
    return gold_path


def evaluate(md_path: Path, mode: str, env_path: str) -> dict:
    """mode: rule | llm | consistency"""
    slug = slugify(md_path.stem)
    gold = load_gold(slug)
    rule = run_extractor("ingest_graph.py", md_path, env_path)

    if mode == "rule":
        pred = rule
        gold_used = gold
    elif mode == "llm":
        pred = run_extractor("ingest_llm.py", md_path, env_path)
        gold_used = gold
    elif mode == "consistency":
        # rule 을 gold 로, llm 을 pred 로 — 일관성 측정
        pred = run_extractor("ingest_llm.py", md_path, env_path)
        gold_used = rule
    else:
        raise ValueError(f"unknown mode: {mode}")

    # entity P/R/F1 (canonical + type 키)
    ekey = lambda e: (e.get("canonical", ""), e.get("type", ""))
    ent_p, ent_r, ent_f, ent_tp, ent_fp, ent_fn = precision_recall_f1(
        pred["entities"], gold_used["entities"], ekey
    )

    return {
        "slug": slug,
        "mode": mode,
        "entity": {
            "precision": round(ent_p, 3), "recall": round(ent_r, 3), "f1": round(ent_f, 3),
            "tp": ent_tp, "fp": ent_fp, "fn": ent_fn,
        },
        "pred_count": len(pred["entities"]),
        "gold_count": len(gold_used["entities"]),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", nargs="?", help="단일 .md 경로")
    parser.add_argument("--all", action="store_true", help="GOLD_DIR 전체")
    parser.add_argument("--mode", choices=["rule", "llm", "consistency"], default="rule")
    parser.add_argument("--seed", action="store_true", help="룰베이스 결과를 gold 초안으로 저장")
    parser.add_argument("--env", default=".env", help=".env 경로")
    args = parser.parse_args()

    if args.seed:
        if not args.path:
            parser.error("--seed 는 path 필요")
        gold_path = seed_gold(Path(args.path), args.env)
        print(f"[seed] {gold_path}")
        print("  → 사람이 검수 후 SOLVES/USES 같은 관계 추가")
        return 0

    if not args.path and not args.all:
        parser.error("path 또는 --all 필요")

    paths = sorted((REPO_ROOT / "vault/02_wiki/topics").glob("*.md")) if args.all else [Path(args.path)]
    results = []
    for p in paths:
        if not p.exists():
            print(f"[warn] not found: {p}", file=sys.stderr)
            continue
        result = evaluate(p, args.mode, args.env)
        results.append(result)
        print(f"\n=== {result['slug']} ({result['mode']}) ===")
        print(f"  pred: {result['pred_count']} entities, gold: {result['gold_count']}")
        e = result["entity"]
        print(f"  entity: P={e['precision']} R={e['recall']} F1={e['f1']} "
              f"(TP={e['tp']} FP={e['fp']} FN={e['fn']})")

    if results:
        avg_p = sum(r["entity"]["precision"] for r in results) / len(results)
        avg_r = sum(r["entity"]["recall"] for r in results) / len(results)
        avg_f = sum(r["entity"]["f1"] for r in results) / len(results)
        print(f"\n=== 평균 ({len(results)} 건) ===")
        print(f"  P={avg_p:.3f} R={avg_r:.3f} F1={avg_f:.3f}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
