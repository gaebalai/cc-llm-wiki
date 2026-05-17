#!/usr/bin/env python3
"""GraphRAG Ingest with LLM (v0.4.0) — LangChain LLMGraphTransformer 기반.

vs ingest_graph.py (룰베이스):
- 룰베이스 (aliases.yaml 매칭): MENTIONS / REFERS_TO 만 추출, 빠르고 무료
- LLM (본 파일): SOLVES / USES / CONTRADICTS 같은 의미 관계 추출, OpenAI API 비용

설계 ([[graphrag-poc-with-neo4j]] 의 방어선):
1. 노드 라벨 enum 고정 (allowed_nodes 파라미터로 LLM 출력 제약)
2. 관계 타입 enum 고정 (allowed_relationships)
3. aliases.yaml canonical_name 으로 정규화 (LLM 후 룰 적용)
4. Cypher 는 services/graph/templates/ 의 사전 정의만 사용 (자연어 → Cypher 금지)

사용:
    # dry-run (LLM 호출 없이 청크 분할만 미리보기)
    python services/graph/ingest_llm.py vault/02_wiki/topics/<slug>.md --dry-run

    # 실 LLM 추출 (OpenAI 사용)
    DRY_RUN=0 python services/graph/ingest_llm.py vault/02_wiki/topics/<slug>.md --env .env

    # 전체 topics
    DRY_RUN=0 python services/graph/ingest_llm.py --all --env .env

환경 (.env):
    OPENAI_API_KEY                              — LangChain LLMGraphTransformer 필수
    OPENAI_MODEL                                 — 기본 gpt-4o-mini
    NEO4J_URI / NEO4J_USERNAME / NEO4J_PASSWORD — Neo4j 연결
    DRY_RUN=1                                    — LLM 호출 안 함

의존 (.venv):
    pip install langchain langchain-community langchain-openai langchain-experimental neo4j
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
TOPICS_DIR = REPO_ROOT / "vault" / "02_wiki" / "topics"
ALIASES_YAML = REPO_ROOT / "vault" / "03_schema" / "aliases.yaml"

# ingest_graph.py 와 동일한 enum (그래프 일관성)
NODE_LABELS = ["Person", "Company", "Technology", "Challenge", "Solution"]
RELATION_TYPES = ["REFERS_TO", "CONTRADICTS", "MENTIONS", "SOLVES", "USES"]


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


def parse_frontmatter(md_text: str) -> tuple[dict, str]:
    """ingest_graph.py 와 동일 — frontmatter + body 분리."""
    if not md_text.startswith("---\n"):
        return {}, md_text
    end = md_text.find("\n---\n", 4)
    if end == -1:
        return {}, md_text
    yaml_block = md_text[4:end]
    body = md_text[end + 5:]
    fm: dict = {}
    current_key: str | None = None
    for raw in yaml_block.splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        if raw.startswith("  - "):
            if current_key:
                fm.setdefault(current_key, []).append(raw[4:].strip().strip('"'))
            continue
        m = re.match(r"^([a-zA-Z_][a-zA-Z0-9_]*):\s*(.*)$", raw)
        if not m:
            continue
        key, value = m.group(1), m.group(2)
        current_key = key
        if value == "":
            fm[key] = []
        elif value.lower() == "null":
            fm[key] = None
        else:
            fm[key] = value.strip().strip('"')
    return fm, body


def load_aliases(path: Path) -> dict[str, tuple[str, str]]:
    """aliases.yaml → {alias_lower: (canonical, type)} 매핑.
    LLM 추출 후 canonical_name 정규화에 사용."""
    if not path.exists():
        return {}
    lookup: dict[str, tuple[str, str]] = {}
    current: dict | None = None
    aliases_mode = False
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.rstrip()
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if line.startswith("aliases:"):
            continue
        if line.startswith("  - canonical:"):
            current = {"canonical": line.split(":", 1)[1].strip(), "type": None, "aliases": []}
            aliases_mode = False
            lookup[current["canonical"].lower()] = (current["canonical"], "")
        elif current and line.startswith("    type:"):
            current["type"] = line.split(":", 1)[1].strip()
            lookup[current["canonical"].lower()] = (current["canonical"], current["type"])
        elif current and line.startswith("    aliases:"):
            rhs = line.split(":", 1)[1].strip()
            if rhs.startswith("[") and rhs.endswith("]"):
                for a in rhs[1:-1].split(","):
                    a = a.strip().strip('"')
                    if a:
                        lookup[a.lower()] = (current["canonical"], current["type"] or "")
            aliases_mode = True
        elif aliases_mode and line.startswith("      - "):
            a = line[8:].strip().strip('"')
            lookup[a.lower()] = (current["canonical"], current["type"] or "")
    return lookup


def normalize_with_aliases(name: str, lookup: dict[str, tuple[str, str]]) -> tuple[str, str | None]:
    """LLM 추출 entity 이름을 aliases.yaml 의 canonical 로 정규화.
    매칭 없으면 (name, None) — 신규 entity 후보 (사람 검토용)."""
    hit = lookup.get(name.lower())
    if hit:
        return hit
    return (name, None)


def chunk_body(body: str, max_chars: int = 2000) -> list[str]:
    """LLM 토큰 한계 회피용 청크 분할 (단순 길이 기반).
    실제로는 문단·헤더 기준이 좋지만 PoC 는 단순."""
    if len(body) <= max_chars:
        return [body]
    chunks = []
    for i in range(0, len(body), max_chars):
        chunks.append(body[i:i + max_chars])
    return chunks


def extract_with_llm(chunks: list[str], openai_key: str, model: str = "gpt-4o-mini") -> dict:
    """LangChain LLMGraphTransformer 호출.
    반환: {nodes: [...], rels: [...], candidates: [...]} (신규 entity 후보 포함)"""
    try:
        from langchain_experimental.graph_transformers import LLMGraphTransformer
        from langchain_openai import ChatOpenAI
        from langchain_core.documents import Document
    except ImportError as e:
        print(f"[error] LangChain 미설치: {e}", file=sys.stderr)
        print("  pip install langchain langchain-openai langchain-experimental", file=sys.stderr)
        return {"nodes": [], "rels": [], "candidates": []}

    os.environ["OPENAI_API_KEY"] = openai_key
    llm = ChatOpenAI(model=model, temperature=0)
    transformer = LLMGraphTransformer(
        llm=llm,
        allowed_nodes=NODE_LABELS,
        allowed_relationships=RELATION_TYPES,
    )

    all_nodes = {}
    all_rels = []
    for i, chunk in enumerate(chunks):
        doc = Document(page_content=chunk)
        try:
            result = transformer.convert_to_graph_documents([doc])
            for graph_doc in result:
                for n in graph_doc.nodes:
                    all_nodes[n.id] = {"label": n.type, "name": n.id}
                for r in graph_doc.relationships:
                    all_rels.append({
                        "src": r.source.id,
                        "dst": r.target.id,
                        "type": r.type,
                    })
        except Exception as e:
            print(f"[warn] chunk {i+1}/{len(chunks)} LLM 호출 실패: {e}", file=sys.stderr)

    return {
        "nodes": list(all_nodes.values()),
        "rels": all_rels,
    }


def upsert_to_neo4j(uri: str, user: str, pw: str, source_id: str,
                    nodes: list[dict], rels: list[dict], lookup: dict) -> tuple[int, list[str]]:
    """Neo4j upsert + aliases.yaml 미등록 candidate 수집."""
    try:
        from neo4j import GraphDatabase
    except ImportError:
        print("[error] neo4j 드라이버 미설치", file=sys.stderr)
        return 0, []

    candidates = []
    upsert_count = 0
    with GraphDatabase.driver(uri, auth=(user, pw)) as driver:
        with driver.session() as session:
            for n in nodes:
                canonical, canonical_type = normalize_with_aliases(n["name"], lookup)
                if canonical_type is None:
                    candidates.append(f"{n['label']}: {n['name']} (LLM 추출, aliases 미등록)")
                    canonical_type = n["label"]
                # 노드 upsert
                session.run(
                    f"MERGE (x:{canonical_type} {{canonical_name: $canon}}) "
                    "SET x.last_llm_extracted = datetime()",
                    canon=canonical,
                )
                # Source → 노드 MENTIONS (기본 관계, 추가로 LLM 의 SOLVES/USES 도)
                session.run(
                    "MATCH (s:Source {id: $sid}), (x {canonical_name: $canon}) "
                    "MERGE (s)-[:MENTIONS]->(x)",
                    sid=source_id, canon=canonical,
                )
                upsert_count += 1

            for r in rels:
                src_canonical, _ = normalize_with_aliases(r["src"], lookup)
                dst_canonical, _ = normalize_with_aliases(r["dst"], lookup)
                rel_type = r["type"] if r["type"] in RELATION_TYPES else "MENTIONS"
                session.run(
                    f"MATCH (a {{canonical_name: $a}}), (b {{canonical_name: $b}}) "
                    f"MERGE (a)-[:{rel_type}]->(b)",
                    a=src_canonical, b=dst_canonical,
                )
                upsert_count += 1
    return upsert_count, candidates


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", nargs="?", help="단일 .md 경로")
    parser.add_argument("--all", action="store_true", help="topics/ 전체")
    parser.add_argument("--dry-run", action="store_true", help="LLM 호출 안 함, 청크만 미리보기")
    parser.add_argument("--env", default=".env", help=".env 경로")
    parser.add_argument("--max-chars", type=int, default=2000, help="청크 분할 길이")
    args = parser.parse_args()

    if not args.path and not args.all:
        parser.error("path 또는 --all 필요")

    env = {**load_env(REPO_ROOT / args.env), **os.environ}
    dry_run = args.dry_run or env.get("DRY_RUN", "0").strip() in ("1", "true", "yes")
    openai_key = env.get("OPENAI_API_KEY", "").strip()
    openai_model = env.get("OPENAI_MODEL", "gpt-4o-mini").strip()

    lookup = load_aliases(ALIASES_YAML)
    print(f"[info] aliases lookup: {len(lookup)} entries", file=sys.stderr)

    paths = sorted(TOPICS_DIR.glob("*.md")) if args.all else [Path(args.path)]

    for p in paths:
        if not p.exists():
            print(f"[warn] not found: {p}", file=sys.stderr)
            continue
        text = p.read_text(encoding="utf-8")
        fm, body = parse_frontmatter(text)
        source_id = fm.get("id") or p.stem
        chunks = chunk_body(body, args.max_chars)
        print(f"[info] {p.name}: {len(chunks)} chunks, source_id={source_id}", file=sys.stderr)

        if dry_run:
            print(json.dumps({
                "source_id": source_id,
                "chunks": len(chunks),
                "first_chunk_preview": chunks[0][:200] + "..." if chunks else "",
            }, ensure_ascii=False, indent=2))
            continue

        if not openai_key:
            print("[error] OPENAI_API_KEY 필요 (또는 --dry-run)", file=sys.stderr)
            return 1

        extracted = extract_with_llm(chunks, openai_key, openai_model)
        print(f"[info] LLM 추출: nodes={len(extracted['nodes'])} rels={len(extracted['rels'])}", file=sys.stderr)

        uri = env.get("NEO4J_URI", "").strip()
        user = env.get("NEO4J_USERNAME", "neo4j").strip()
        pw = env.get("NEO4J_PASSWORD", "").strip()
        if not uri or not pw:
            print("[error] NEO4J_URI/PASSWORD 필요", file=sys.stderr)
            return 1

        upserts, candidates = upsert_to_neo4j(uri, user, pw, source_id,
                                              extracted["nodes"], extracted["rels"], lookup)
        print(f"[ok] {p.name}: {upserts} upserts, {len(candidates)} new candidates")
        if candidates:
            print("  신규 entity 후보 (aliases.yaml 검토 필요):")
            for c in candidates[:10]:
                print(f"    - {c}")
            # candidates 를 vault/02_wiki/_lint/aliases-candidates-YYYY-MM-DD.md 에 기록 (옵션)

    return 0


if __name__ == "__main__":
    sys.exit(main())
