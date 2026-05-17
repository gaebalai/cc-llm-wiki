---
id: 2026-05-17T184500-entity-disambiguation-strategy
type: topic
status: reviewed
locale: ko
sources:
  - vault/01_raw/articles/2026-05-17-2do-brain-neo4j-graphrag-poc.md
related:
  - "[[graphrag-poc-with-neo4j]]"
  - "[[2do-brain-architecture]]"
updated_at: 2026-05-17T18:50:00+09:00
graph_synced_at: null
---

# Entity Disambiguation Strategy

## 핵심 주장

GraphRAG에서 노드 분열(같은 회사가 "Acme", "Acme Inc.", "에이크미"로 3노드가 되는 문제)을
**LLM 추론에 맡기지 않고 룰베이스로 처리**한다. `canonical_name + aliases[]` 정규화 테이블을
스키마에 박아 추출 시점부터 표기 흔들림을 차단한다.

## 3가지 방어선

1. **사전 라벨링**: 노드 라벨 enum 고정 (`Person`·`Company`·`Challenge`·`Solution`·`Technology`).
   추출기가 라벨을 생성하는 게 아니라 정해진 라벨 중에서 고른다.
2. **정규화 규칙 물리적 결합**: 추출 직후 `aliases[]` 매칭으로 `canonical_name`으로 강제 매핑.
   `vault/03_schema/aliases.yaml`(P5에서 생성)에 룰 누적.
3. **Cypher 물리 검증**: 자연어 QA 직전에 고정 Cypher로 노드 수·중복·고립을 검증.
   pass 하지 못한 노드는 답변 합성에서 제외.

## 횡단적 지견

- **[[graphrag-poc-with-neo4j]]의 전제 조건**: 정규화 없이 그래프를 만들면 인과 경로(`Company → Challenge → Solution`)가 노드 분열로 끊긴다. 본 전략은 PoC 품질의 90%를 좌우.
- **[[2do-brain-architecture]] L3a 정합성 키**: wiki frontmatter `id`가 Neo4j `metadata.id`와 같으므로, alias 매핑은 entity 단위(Acme=acme-inc)와 source 단위(wiki id)를 분리해야 함.
- **컨텍스트 절약 효과**: top-K 후보가 정규화 전 10개에서 정규화 후 3~5개로 축소 → LLM 합성 단계 토큰 절약.

## 운영 메모

- alias 테이블은 사람이 직접 편집. LLM이 자동 추가 금지(오정렬 위험)
- `sleep-maintenance` routine이 alias 변경 감지 시 그래프 전체 재정렬
- 한국어 자료에서는 음차/한자/영문 3중 표기 빈발 → alias 초기값을 사용자가 미리 충분히 채워야 함

## 미해결 질문

- alias 발견 자체를 어떻게 자동화할 것인가 (LLM 제안 → 사람 승인 패턴?)
- 동음이의 회사(Apple inc. vs apple 과일)는 entity_type까지 매칭 키에 넣어 해결할지
