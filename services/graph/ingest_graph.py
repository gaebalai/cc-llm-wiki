#!/usr/bin/env python3
"""GraphRAG Ingest — vault/02_wiki/topics/*.md → Neo4j 노드/엣지.

설계 원칙 ([[graphrag-poc-with-neo4j]], [[entity-disambiguation-strategy]]):
1. 노드 라벨 enum 고정 (Person/Company/Technology/Challenge/Solution/Source)
2. aliases.yaml 로 canonical_name 강제 매핑 (LLM 추론 금지)
3. wiki frontmatter id == Neo4j metadata.id (4층 공유 키)
4. Cypher 는 services/graph/templates/ 의 사전 정의 템플릿만 사용 (자동 생성 금지)

사용:
    # dry-run (Neo4j/OpenAI 없이 추출 결과만 stdout JSON)
    python services/graph/ingest_graph.py --dry-run

    # 단일 토픽
    python services/graph/ingest_graph.py vault/02_wiki/topics/2026-05-17-graphrag-poc-with-neo4j.md

    # 전체
    python services/graph/ingest_graph.py --all

환경 (.env 또는 환경 변수):
    NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD  — Neo4j 연결
    OPENAI_API_KEY                              — LLMGraphTransformer (선택, 미지정 시 룰베이스 추출만)
    DRY_RUN=1                                   — 외부 호출 안 함
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
TOPICS_DIR = REPO_ROOT / "vault" / "02_wiki" / "topics"
ALIASES_YAML = REPO_ROOT / "vault" / "03_schema" / "aliases.yaml"

NODE_LABELS = ("Person", "Company", "Technology", "Challenge", "Solution", "Source")
RELATION_TYPES = ("REFERS_TO", "CONTRADICTS", "MENTIONS", "SOLVES", "USES")


@dataclass
class Node:
    id: str
    label: str
    canonical_name: str
    aliases: list[str] = field(default_factory=list)
    props: dict = field(default_factory=dict)


@dataclass
class Relation:
    src_id: str
    dst_id: str
    type: str
    props: dict = field(default_factory=dict)


# ─────────── env / .env 로더 (외부 의존 없이) ────────────


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


# ─────────── frontmatter / aliases 파서 (외부 의존 없이) ────────────


def parse_frontmatter(md_text: str) -> tuple[dict, str]:
    """YAML 프런트매터를 손수 파싱 (간단 케이스만). 키-값/리스트/null 지원."""
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


def load_aliases(path: Path) -> list[dict]:
    """aliases.yaml 의 단순 파싱 (외부 의존 없이)."""
    if not path.exists():
        return []
    entries: list[dict] = []
    current: dict | None = None
    aliases_mode = False
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.rstrip()
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if line.startswith("aliases:"):
            continue
        if line.startswith("  - canonical:"):
            if current:
                entries.append(current)
            current = {"canonical": line.split(":", 1)[1].strip(), "aliases": [], "type": None}
            aliases_mode = False
            continue
        if current is None:
            continue
        if line.startswith("    type:"):
            current["type"] = line.split(":", 1)[1].strip()
            aliases_mode = False
        elif line.startswith("    aliases:"):
            rhs = line.split(":", 1)[1].strip()
            if rhs.startswith("[") and rhs.endswith("]"):
                current["aliases"] = [a.strip().strip('"') for a in rhs[1:-1].split(",") if a.strip()]
            aliases_mode = True
        elif line.startswith("    note:"):
            current["note"] = line.split(":", 1)[1].strip()
            aliases_mode = False
        elif aliases_mode and line.startswith("      - "):
            current["aliases"].append(line[8:].strip().strip('"'))
    if current:
        entries.append(current)
    return entries


def build_alias_lookup(entries: list[dict]) -> dict[str, tuple[str, str]]:
    """alias 텍스트 → (canonical, type) 매핑. 대소문자 무시."""
    lookup: dict[str, tuple[str, str]] = {}
    for e in entries:
        canon = e["canonical"]
        typ = e["type"] or "Source"
        lookup[canon.lower()] = (canon, typ)
        for a in e.get("aliases", []):
            lookup[a.lower()] = (canon, typ)
    return lookup


# ─────────── 룰베이스 entity 추출 (LLM 없이도 동작) ────────────


def extract_entities_rule_based(body: str, lookup: dict[str, tuple[str, str]]) -> list[tuple[str, str]]:
    """본문에서 alias 룩업으로 매칭되는 엔티티만 추출. LLM 호출 없음."""
    found: dict[str, str] = {}
    lowered = body.lower()
    for alias, (canon, typ) in lookup.items():
        if alias in lowered:
            found[canon] = typ
    return list(found.items())


# ─────────── 그래프 빌드 ────────────


def build_graph_for_topic(md_path: Path, lookup: dict[str, tuple[str, str]]) -> tuple[Node, list[Node], list[Relation]]:
    text = md_path.read_text(encoding="utf-8")
    fm, body = parse_frontmatter(text)

    source_id = fm.get("id") or md_path.stem
    source_node = Node(
        id=source_id,
        label="Source",
        canonical_name=fm.get("id", md_path.stem),
        props={
            "path": str(md_path.relative_to(REPO_ROOT)),
            "type": fm.get("type"),
            "status": fm.get("status"),
            "locale": fm.get("locale"),
            "updated_at": fm.get("updated_at"),
        },
    )

    entities = extract_entities_rule_based(body, lookup)
    nodes: list[Node] = []
    rels: list[Relation] = []
    for canon, typ in entities:
        node_id = f"{typ}:{canon}"
        nodes.append(Node(id=node_id, label=typ, canonical_name=canon))
        rels.append(Relation(src_id=source_id, dst_id=node_id, type="MENTIONS"))

    # REFERS_TO: wikilink 참조
    for m in re.finditer(r"\[\[([a-z0-9-]+)\]\]", body):
        target_slug = m.group(1)
        target_path = next(TOPICS_DIR.glob(f"*-{target_slug}.md"), None)
        if target_path is None:
            continue
        target_fm, _ = parse_frontmatter(target_path.read_text(encoding="utf-8"))
        target_id = target_fm.get("id") or target_path.stem
        rels.append(Relation(src_id=source_id, dst_id=target_id, type="REFERS_TO"))

    return source_node, nodes, rels


# ─────────── Neo4j upsert (드라이버 있을 때만) ────────────


def upsert_to_neo4j(uri: str, user: str, password: str, sources: list[Node], nodes: list[Node], rels: list[Relation]) -> int:
    try:
        from neo4j import GraphDatabase  # type: ignore
    except ImportError:
        print("[error] neo4j 드라이버 미설치. `pip install neo4j` 후 재시도.", file=sys.stderr)
        return 2

    upsert_count = 0
    with GraphDatabase.driver(uri, auth=(user, password)) as driver:
        with driver.session() as session:
            for s in sources:
                session.run(
                    "MERGE (n:Source {id:$id}) SET n += $props, n.canonical_name=$canon",
                    id=s.id, props=s.props, canon=s.canonical_name,
                )
                upsert_count += 1
            for n in nodes:
                session.run(
                    f"MERGE (n:{n.label} {{id:$id}}) SET n.canonical_name=$canon",
                    id=n.id, canon=n.canonical_name,
                )
                upsert_count += 1
            for r in rels:
                session.run(
                    f"MATCH (a {{id:$src}}), (b {{id:$dst}}) MERGE (a)-[:{r.type}]->(b)",
                    src=r.src_id, dst=r.dst_id,
                )
                upsert_count += 1
    return upsert_count


# ─────────── main ────────────


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", nargs="?", help="단일 .md 경로 (생략 시 --all 필요)")
    parser.add_argument("--all", action="store_true", help="vault/02_wiki/topics/ 전체")
    parser.add_argument("--dry-run", action="store_true", help="Neo4j 호출 없이 JSON 만 출력")
    parser.add_argument("--env", default=".env", help=".env 경로")
    args = parser.parse_args()

    if not args.path and not args.all:
        parser.error("path 또는 --all 필요")

    env = {**os.environ, **load_env(REPO_ROOT / args.env)}
    dry_run = args.dry_run or env.get("DRY_RUN", "0").strip() in ("1", "true", "yes")

    aliases = load_aliases(ALIASES_YAML)
    lookup = build_alias_lookup(aliases)
    print(f"[info] aliases loaded: {len(aliases)} canonical, {len(lookup)} aliases", file=sys.stderr)

    if args.all:
        paths = sorted(TOPICS_DIR.glob("*.md"))
    else:
        paths = [Path(args.path)]

    all_sources: list[Node] = []
    all_nodes: list[Node] = []
    all_rels: list[Relation] = []
    seen_node_ids: set[str] = set()
    for p in paths:
        if not p.exists():
            print(f"[warn] not found: {p}", file=sys.stderr)
            continue
        source, nodes, rels = build_graph_for_topic(p, lookup)
        all_sources.append(source)
        for n in nodes:
            if n.id not in seen_node_ids:
                all_nodes.append(n)
                seen_node_ids.add(n.id)
        all_rels.extend(rels)

    summary = {
        "sources": [asdict(s) for s in all_sources],
        "nodes": [asdict(n) for n in all_nodes],
        "relations": [asdict(r) for r in all_rels],
        "stats": {
            "sources": len(all_sources),
            "nodes": len(all_nodes),
            "relations": len(all_rels),
        },
    }

    if dry_run:
        print("[dry-run] Neo4j 호출 없이 추출 결과:")
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return 0

    uri = env.get("NEO4J_URI", "").strip()
    user = env.get("NEO4J_USERNAME", "neo4j").strip()
    password = env.get("NEO4J_PASSWORD", "").strip()
    if not uri or not password:
        print("[error] NEO4J_URI / NEO4J_PASSWORD 필요. .env 확인 또는 --dry-run", file=sys.stderr)
        return 1

    upserts = upsert_to_neo4j(uri, user, password, all_sources, all_nodes, all_rels)
    print(f"[ok] {upserts} 노드/엣지 upsert 완료. sources={len(all_sources)} nodes={len(all_nodes)} rels={len(all_rels)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
