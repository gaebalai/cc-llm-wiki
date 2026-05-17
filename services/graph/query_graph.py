#!/usr/bin/env python3
"""GraphRAG Query — 사전 정의 Cypher 템플릿으로 그래프 질의.

설계 원칙 ([[graphrag-poc-with-neo4j]]):
- 자연어 → Cypher 자동 생성 **금지**. 입력 질의는 키워드 매칭으로 템플릿 선택.
- 결과는 LLM 컨텍스트로 직접 주입 가능한 JSON.

사용:
    # 인과 경로 (Company → Challenge → Solution → Technology)
    python services/graph/query_graph.py causal_path --param company_canonical=Anthropic

    # 개념 이웃
    python services/graph/query_graph.py concept_neighbors --param canonical=GraphRAG

    # 고립 노드 감사
    python services/graph/query_graph.py orphan_audit

    # 템플릿 목록
    python services/graph/query_graph.py --list

환경 (.env):
    NEO4J_URI / NEO4J_USERNAME / NEO4J_PASSWORD  — Neo4j 연결
    DRY_RUN=1  — Cypher 만 출력하고 실행 안 함

새 템플릿 추가:
    services/graph/templates/<name>.cypher 파일을 만들면 자동 인식.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
TEMPLATES_DIR = REPO_ROOT / "services" / "graph" / "templates"


def load_env(env_path: Path) -> dict[str, str]:
    env: dict[str, str] = {}
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip().strip('"').strip("'")
    return env


def list_templates() -> list[str]:
    return sorted(p.stem for p in TEMPLATES_DIR.glob("*.cypher"))


def load_template(name: str) -> str:
    path = TEMPLATES_DIR / f"{name}.cypher"
    if not path.exists():
        raise FileNotFoundError(f"템플릿 없음: {path}. 사용 가능: {list_templates()}")
    return path.read_text(encoding="utf-8")


def parse_params(items: list[str]) -> dict:
    out: dict = {}
    for item in items:
        if "=" not in item:
            raise ValueError(f"--param 형식 오류 (key=value): {item}")
        k, v = item.split("=", 1)
        if v.lstrip("-").isdigit():
            out[k] = int(v)
        else:
            out[k] = v
    return out


def run_query(uri: str, user: str, password: str, cypher: str, params: dict) -> list[dict]:
    try:
        from neo4j import GraphDatabase  # type: ignore
    except ImportError:
        print("[error] neo4j 드라이버 미설치. `pip install neo4j`", file=sys.stderr)
        return []

    with GraphDatabase.driver(uri, auth=(user, password)) as driver:
        with driver.session() as session:
            result = session.run(cypher, **params)
            return [dict(r) for r in result]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("template", nargs="?", help="템플릿 이름 (확장자 없이)")
    parser.add_argument("--list", action="store_true", help="템플릿 목록")
    parser.add_argument("--param", action="append", default=[], help="key=value 형식, 여러 번 가능")
    parser.add_argument("--dry-run", action="store_true", help="Cypher 출력만, 실행 안 함")
    parser.add_argument("--env", default=".env", help=".env 경로")
    args = parser.parse_args()

    if args.list:
        templates = list_templates()
        print("사용 가능한 템플릿:")
        for t in templates:
            print(f"  - {t}")
        return 0

    if not args.template:
        parser.error("템플릿 이름 또는 --list 필요")

    env = {**os.environ, **load_env(REPO_ROOT / args.env)}
    dry_run = args.dry_run or env.get("DRY_RUN", "0").strip() in ("1", "true", "yes")

    cypher = load_template(args.template)
    params = parse_params(args.param)

    if dry_run:
        print(f"[dry-run] template={args.template}")
        print(f"[dry-run] params={json.dumps(params, ensure_ascii=False)}")
        print("[dry-run] cypher:")
        print(cypher)
        return 0

    uri = env.get("NEO4J_URI", "").strip()
    user = env.get("NEO4J_USERNAME", "neo4j").strip()
    password = env.get("NEO4J_PASSWORD", "").strip()
    if not uri or not password:
        print("[error] NEO4J_URI / NEO4J_PASSWORD 필요. .env 또는 --dry-run", file=sys.stderr)
        return 1

    rows = run_query(uri, user, password, cypher, params)
    print(json.dumps(rows, ensure_ascii=False, indent=2, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
