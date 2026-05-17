#!/usr/bin/env python3
"""daily-digest Skill 의 실행 골격 (v0.4.1).

WebSearch + WebFetch 는 Claude Code 세션에서만 가능하므로 본 스크립트는:
- dry-run: positioning.md 파싱 → 검색 쿼리 설계 → 출력 (실 호출 없음)
- 실 실행: Skill (Claude Code) 가 본 스크립트의 쿼리를 받아 WebSearch 호출

사용:
    # dry-run (positioning.md 검증 + 쿼리 설계 미리보기)
    python scripts/daily_digest_runner.py --vault ~/my-knowledge-base --dry-run

    # 또는 (Skill 안에서)
    /daily-digest

설계:
- positioning.md 의 interests/avoid/trusted_sources 파싱
- 검색 쿼리 자동 설계 (interests + 기간 + site 제한 + 부정형)
- 출력: 쿼리 목록 + 기대 digest 페이지 경로 + Slack 통지 안내
- 실 WebSearch/WebFetch 는 Claude Code Skill 이 담당
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path
from datetime import datetime, timezone, timedelta


def parse_positioning(path: Path) -> dict:
    """positioning.md 의 섹션 단위 파싱.
    반환: {interests: [...], avoid: [...], trusted_sources: [...], avoid_sources: [...], tone: str, frequency_hint: str}
    """
    if not path.exists():
        return {}
    text = path.read_text(encoding="utf-8")

    # `## <section>` 헤더 기준 분할
    sections = {}
    current_key = None
    current_lines = []
    for line in text.splitlines():
        m = re.match(r'^## (.+)$', line)
        if m:
            if current_key:
                sections[current_key] = current_lines
            # section name → key (정규화)
            name = m.group(1).strip().split()[0].lower().rstrip("·").rstrip("(")
            current_key = name
            current_lines = []
        elif current_key:
            current_lines.append(line)
    if current_key:
        sections[current_key] = current_lines

    # 각 섹션에서 `- item` 리스트 추출
    def list_items(lines: list[str]) -> list[str]:
        out = []
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("- ") and not stripped.startswith("- ("):
                # "(필요한 만큼...)" 같은 예시 제외
                value = stripped[2:].strip()
                if value and not value.startswith("("):
                    # `**...**` 또는 backtick 정리
                    value = re.sub(r'\*\*|`', '', value).strip()
                    out.append(value)
        return out

    return {
        "interests": list_items(sections.get("interests", [])),
        "avoid": list_items(sections.get("avoid", [])),
        "trusted_sources": list_items(sections.get("trusted_sources", [])),
        "avoid_sources": list_items(sections.get("avoid_sources", [])),
        "tone": "\n".join(sections.get("tone", [])).strip() or "한국어, 1 출처당 2~3 문장",
        "frequency_hint": "\n".join(sections.get("frequency_hint", [])).strip() or "매일 5 건",
    }


def design_queries(positioning: dict, today: str) -> list[str]:
    """positioning → 검색 쿼리 설계.
    - interests 각 키워드별 1 쿼리 (최대 5 개)
    - trusted_sources site: 제한 추가 (옵션)
    - avoid 키워드는 부정형 (-keyword)
    - 최근 7 일 (after:<today-7>)
    """
    queries = []
    interests = positioning.get("interests", [])[:5]   # 상위 5 개
    avoid_terms = positioning.get("avoid", [])
    trusted = positioning.get("trusted_sources", [])

    avoid_part = " ".join(f'-{a.split()[0]}' for a in avoid_terms[:3]) if avoid_terms else ""

    # interests 별 1 쿼리
    for kw in interests:
        q = f'"{kw}"'
        if avoid_part:
            q += f" {avoid_part}"
        # 최근 1 주
        wk_ago = (datetime.strptime(today, "%Y-%m-%d") - timedelta(days=7)).strftime("%Y-%m-%d")
        q += f" after:{wk_ago}"
        queries.append(q)

    # trusted_sources 별 보너스 쿼리 (interests 가 적을 때 보강)
    if len(queries) < 3 and trusted:
        primary_kw = interests[0] if interests else "AI"
        for src in trusted[:2]:
            domain = src.split()[0]   # 도메인만 추출
            queries.append(f'"{primary_kw}" site:{domain}')

    return queries[:5]   # 최대 5 개


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--vault", required=True, type=Path,
                        help="vault 디렉터리 경로 (positioning.md 가 있는 곳)")
    parser.add_argument("--dry-run", action="store_true",
                        help="쿼리 설계만 출력, 실 WebSearch 호출 X")
    args = parser.parse_args()

    pos_file = args.vault / "positioning.md"
    if not pos_file.exists():
        print(f"[error] {pos_file} 없음", file=sys.stderr)
        print("  템플릿 복사:", file=sys.stderr)
        print(f"  cp skills/daily-digest/positioning.template.md {pos_file}", file=sys.stderr)
        return 1

    positioning = parse_positioning(pos_file)
    today = datetime.now(timezone(timedelta(hours=9))).strftime("%Y-%m-%d")

    print(f"[daily-digest runner] {today} (KST)")
    print()
    print("positioning.md 분석:")
    print(f"  interests:       {len(positioning.get('interests', []))} 건")
    print(f"  avoid:           {len(positioning.get('avoid', []))} 건")
    print(f"  trusted_sources: {len(positioning.get('trusted_sources', []))} 건")
    print(f"  tone:            {positioning.get('tone', '')[:60]}...")
    print()

    queries = design_queries(positioning, today)
    print(f"검색 쿼리 {len(queries)} 건 설계:")
    for i, q in enumerate(queries, 1):
        print(f"  [{i}] {q}")
    print()

    digest_path = args.vault / "02_wiki/digests" / f"{today}.md"
    print(f"기대 digest 페이지: {digest_path}")
    print()

    if args.dry_run:
        print("[dry-run] 실 WebSearch 호출 없음. Claude Code Skill 에서 실 실행.")
        return 0

    print("[note] 실 WebSearch/WebFetch 는 Claude Code Skill 에서만 가능.")
    print("       이 스크립트는 쿼리 설계까지만 — Skill 이 결과를 받아 digest 페이지 생성.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
