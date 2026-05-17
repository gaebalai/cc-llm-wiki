---
id: 2026-05-17T174800-graphrag-poc-with-neo4j
type: topic
status: draft
locale: ko
sources:
  - vault/01_raw/articles/2026-05-17-2do-brain-neo4j-graphrag-poc.md
related:
  - "[[entity-disambiguation-strategy]]"
  - "[[2do-brain-architecture]]"
updated_at: 2026-05-17T17:48:00+09:00
graph_synced_at: null
---

# GraphRAG PoC with Neo4j

## 핵심 주장

위키화한 자료에서 단순 키워드/벡터 검색이 놓치는 **인과·경유 관계**(`Company → Challenge → Solution → Technology`)를
그래프로 추출·물리 검증한 뒤에만 LLM 컨텍스트로 주입한다. **자연어 → Cypher 자동 생성을 의도적으로 배제**하고
사전 정의된 고정 Cypher만 사용하는 것이 안정성의 핵심이다.

## 횡단적 지견

- **[[entity-disambiguation-strategy]]와의 결합**: `canonical_name + aliases` 정규화 없이 그래프를 만들면 같은 회사가 노드 분열되어 인과 경로가 끊긴다. 그래프 품질의 90%가 정규화에서 결정됨.
- **[[2do-brain-architecture]] 안에서의 위치**: 이 PoC는 L3a(Graph Layer). L3b(Kagura 인덱스)와 통합이 아니라 역할 분담 — 의미·키워드는 L3b, 다중-홉 관계는 L3a가 담당.
- **컨텍스트 위생 효과**: 그래프가 후보 노드 5~10개로 좁혀주면 raw 본문 직주입 없이도 답변이 만들어진다(4번 문서 Context Rot 회피의 실증 사례).

## 인용

> 노드·릴레이션 타입을 사전 선정한다 (Person, Company, Challenge, Solution, Technology).
> 추출 규칙에 정규화 규칙을 물리적으로 결합한다.
> **Cypher로 물리 검증을 자연어 QA 전에 수행한다.**

— `docs/11-2do_brain_neo4j_graphrag_poc.md` "3가지 방어선" 섹션

## 실행 절차 (요약)

1. `infra/neo4j/docker-compose.yml`로 Neo4j 5.18.1 + APOC 기동
2. `.env`에 `NEO4J_URI` / `OPENAI_API_KEY` 설정
3. `services/graph/ingest_graph.py` 실행 — `vault/02_wiki/topics/*.md`의 `id`를 그래프 노드 `metadata.id`로 고정
4. `services/graph/query_graph.py "A사 → 기술 경로"` — 사전 정의 Cypher 템플릿으로 3-hop 경로 JSON 반환
5. 결과 검증 후에만 LLM 답변 합성 단계로 전달

## 미해결 질문

- 이 PoC를 어느 시점에 운영화할 것인가 (P5 vs P6)
- LangChain `LLMGraphTransformer`의 추출 품질이 한국어 raw에서 어떻게 나오는지 실측 필요
- `sleep-maintenance` routine의 전체 재인덱싱이 N=1000 문서 규모에서 견디는가 (시간/비용)
- entity disambiguation을 LLM에 맡길지, 룰베이스(`03_schema/aliases.yaml`)로 둘지

## 다음 액션

- 이 페이지를 `_drafts/` → `topics/`로 승격하기 전에 `[[entity-disambiguation-strategy]]` 별도 ingest 1건 진행
- P5 진입 시 본 페이지를 "설계도"로 참조해 `infra/neo4j/docker-compose.yml` 작성
