#!/usr/bin/env python3
"""GraphRAG Merge Ingest (v0.4.1) — 룰베이스 + LLM 하이브리드 일괄 실행.

vs ingest_graph.py 또는 ingest_llm.py 단독:
- 두 도구를 순차 실행하고 결과를 통합 보고
- entity 중복 제거 (둘 다 같은 entity 면 1번만 upsert)
- LLM 추출한 신규 candidate 와 aliases.yaml 매칭 (분리)
- DRY_RUN 일관 지원

사용:
    # dry-run (LLM 호출 없이 둘 다의 추출 결과 미리보기)
    python services/graph/ingest_merge.py vault/02_wiki/topics/<slug>.md --dry-run --env .env

    # 실 머지 (룰베이스 → LLM → Neo4j 통합)
    DRY_RUN=0 python services/graph/ingest_merge.py vault/02_wiki/topics/<slug>.md --env .env

    # 전체 topics
    DRY_RUN=0 python services/graph/ingest_merge.py --all --env .env

설계 원칙:
- ingest_graph.py 가 먼저 실행 (룰베이스 = 빠르고 신뢰 ↑)
- ingest_llm.py 가 그 다음 (LLM = SOLVES/USES 보강)
- aliases.yaml 정규화는 양쪽 모두 적용 → 같은 canonical 로 매핑되면 entity 중복 없음
- candidates (LLM 만 발견, aliases 미등록) 는 vault/02_wiki/_lint/aliases-candidates-YYYY-MM-DD.md 에 기록
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from datetime import datetime, timezone, timedelta

REPO_ROOT = Path(__file__).resolve().parents[2]


def run(cmd: list[str], env_override: dict | None = None) -> tuple[int, str, str]:
    """subprocess.run 래퍼. (returncode, stdout, stderr)."""
    import os
    e = os.environ.copy()
    if env_override:
        e.update(env_override)
    p = subprocess.run(cmd, capture_output=True, text=True, env=e)
    return p.returncode, p.stdout, p.stderr


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", nargs="?", help="단일 .md 경로")
    parser.add_argument("--all", action="store_true", help="topics/ 전체")
    parser.add_argument("--dry-run", action="store_true", help="둘 다 dry-run")
    parser.add_argument("--env", default=".env", help=".env 경로")
    parser.add_argument("--skip-rule", action="store_true", help="룰베이스 ingest 생략 (LLM 만)")
    parser.add_argument("--skip-llm", action="store_true", help="LLM ingest 생략 (룰베이스 만)")
    args = parser.parse_args()

    if not args.path and not args.all:
        parser.error("path 또는 --all 필요")

    base_args = ["--env", args.env]
    if args.dry_run:
        base_args.append("--dry-run")
    if args.path:
        base_args.append(args.path)
    elif args.all:
        base_args.append("--all")

    print("[merge] Step 1: 룰베이스 추출 (ingest_graph.py)")
    if not args.skip_rule:
        rc, out, err = run(
            ["python3", str(REPO_ROOT / "services/graph/ingest_graph.py")] + base_args
        )
        print(out, end="")
        if err:
            print(err, file=sys.stderr, end="")
        if rc != 0:
            print(f"[merge] 룰베이스 실패 (exit {rc}) — LLM 단계 skip", file=sys.stderr)
            return rc
    else:
        print("  skip (--skip-rule)")

    print()
    print("[merge] Step 2: LLM 추출 (ingest_llm.py)")
    if not args.skip_llm:
        rc, out, err = run(
            ["python3", str(REPO_ROOT / "services/graph/ingest_llm.py")] + base_args
        )
        print(out, end="")
        if err:
            print(err, file=sys.stderr, end="")
        if rc != 0:
            print(f"[merge] LLM 실패 (exit {rc}) — 룰베이스 결과만 유지", file=sys.stderr)
            # 룰베이스는 이미 적용됨 → 부분 성공으로 처리
            return 0
    else:
        print("  skip (--skip-llm)")

    print()
    kst_now = datetime.now(timezone(timedelta(hours=9))).strftime("%Y-%m-%dT%H:%M:%S+09:00")
    print(f"[merge] 완료. 시각: {kst_now}")
    print("[merge] aliases-candidates (LLM 발견 신규 entity) 검토:")
    candidates_file = REPO_ROOT / "vault/02_wiki/_lint" / f"aliases-candidates-{kst_now[:10]}.md"
    print(f"  파일: {candidates_file}")
    print("  → 사람이 검토 후 vault/03_schema/aliases.yaml 에 수동 추가")

    return 0


if __name__ == "__main__":
    sys.exit(main())
