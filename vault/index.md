# index — 위키 카탈로그

이 파일은 `vault/02_wiki/` 전체를 두 단계로 탐색할 수 있게 하는 카탈로그다.
LLM이 매번 전수 스캔하지 않도록 **JIT(Just-in-Time)** 진입점으로 동작한다.

## 사용 원칙

- 모든 `topics/`·`decisions/` 페이지는 **반드시 이 index에 등록**된다(compile Skill이 강제)
- `self/`·`_drafts/`·`_lint/`·`digests/`는 등록 대상 아님
- Claude Code는 질의 시 **이 index 헤더 + 관련 장르 섹션만** 읽어 컨텍스트 절약
- 5엔트리 초과 시 장르별 sub-index 분할(`vault/02_wiki/_index/{genre}.md`)

## 장르별 카탈로그

### topics/

- [[2026-05-17-graphrag-poc-with-neo4j]] — Neo4j + 고정 Cypher 로 인과 경로(Company→Challenge→Solution→Technology) 추출·검증
- [[2026-05-17-entity-disambiguation-strategy]] — canonical_name + aliases + Cypher 물리 검증 3 방어선으로 노드 분열 차단
- [[2026-05-17-2do-brain-architecture]] — Claude Code × Obsidian × Neo4j 5 층 자율 지식 OS 청사진

### decisions/

(아직 비어 있음 — 첫 ADR 작성 시 ADR-001 부터)

---

## Index 통계

- topics 총 개수: 3
- decisions 총 개수: 0
- 최종 갱신: 2026-05-17T18:50:00+09:00 (P3 클러스터 compile)
