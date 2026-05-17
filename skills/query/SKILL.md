---
name: query
description: 사용자 자연어 질의를 받아 의도를 분류하고 적절한 검색층으로 라우팅한다. lookup(키워드/의미)은 Grep + Dataview, 관계/경로 탐색은 services/graph/query_graph.py 의 고정 Cypher 템플릿. 자연어 → Cypher 자동 생성 절대 금지. 결과는 LLM 컨텍스트로 주입 가능한 요약 + 출처 wikilink 리스트. 사용자가 "찾아줘", "어디 있어", "관계가 뭐야", "/query <질문>" 같은 형태로 호출하면 발동.
disable-model-invocation: false
allowed-tools:
  - Read
  - Grep
  - Glob
  - Bash(rg:*)
  - Bash(find vault:*)
  - Bash(python3 services/graph/query_graph.py:*)
---

# query Skill — 의도 분류 라우터

## 목적

자연어 질의를 받아 **3 가지 의도 분류** 후 적절한 검색층에 위임. 답변 합성 직전까지가 본 Skill 의 책임이며, **최종 답은 메인 세션이 사용자에게 보여준다** (이 Skill 은 후보 + 출처만 모아줌).

## 입력

- `question` (필수): 자연어 한 줄. 예시: "GraphRAG 가 뭐였지", "Anthropic 이 어떤 기술 쓰지", "raw 정리 정책 어디 적혔어"
- `mode?` (선택): `local` | `graph` | `auto`. 미지정 시 자동 분류

## 의도 분류 (auto 모드)

| 의도 | 신호 키워드 | 라우팅 |
|---|---|---|
| **lookup** | "어디", "뭐였지", "뭐야", "찾아줘", "정의", "어떻게 적혔어" | local (Grep + Dataview) |
| **relation** | "관계", "경로", "→", "어떤 X 쓰지", "왜 그게 X 와", "연결" | graph (Cypher 템플릿) |
| **complex** | "X 의 Y 와 어떤 차이", "전체 그림", "summary" | both (local → graph 보완) |

매칭 안 되면 기본은 `local`.

## 절대 금지

- **자연어 → Cypher 자동 생성** (CLAUDE.md §3-④). 새 Cypher 패턴이 필요하면 사용자에게 "services/graph/templates/<name>.cypher 를 만들어달라" 안내
- `vault/02_wiki/self/` 본문 인용 — frontmatter 만 표시
- 출처 없이 답변 합성 — 모든 후보는 `[[slug]]` 또는 raw 경로로 출처 명시
- raw 본문 직주입 — 항상 wiki 페이지를 거쳐

## 4 단계 절차

### Step 1. 의도 분류
- `mode` 인자 우선
- 자동: 키워드 매칭 → lookup / relation / complex

### Step 2. 검색 실행 (분기)

**local 분기**:
```bash
rg -l --type md '<question 핵심 키워드>' vault/02_wiki/topics vault/02_wiki/decisions
# 또는 자세히
rg --type md -C 2 '<키워드>' vault/02_wiki/topics
```
- 결과를 5 개 이하로 압축
- 각 결과의 frontmatter id + 본문 첫 단락만 추출

**graph 분기**:
- 사용 가능 템플릿 확인: `python3 services/graph/query_graph.py --list`
- 가장 적합한 템플릿 선택 (causal_path / concept_neighbors / orphan_audit)
- 파라미터 추출 (canonical_name 등)
- `python3 services/graph/query_graph.py <template> --param key=value --env .env`
- DRY_RUN 자동 감지 (Neo4j 미기동 시)

**both 분기**:
- local 먼저 → 후보 노드 ID 5 개 추출 → graph 로 경로 확장

### Step 3. 출처 정리
- 결과 각 항목에 `[[slug]]` 또는 `vault/02_wiki/topics/<slug>.md` 명시
- raw 경유면 raw 경로도 같이 표기 (`sources` frontmatter 의 raw)

### Step 4. 사용자에게 후보 + 출처 반환
- 자연어 한 단락 요약 + 후보 리스트 + 추천 다음 액션 (필요 시 `/compile` 등)
- **답변 단정 금지** — "이 정도가 후보입니다, 검토해주세요" 톤

## 사용 예

```
사용자: /query GraphRAG 가 뭐였지
Claude: [의도] lookup (키워드 "뭐였지")
        [local] rg 'GraphRAG' vault/02_wiki/topics
                 → 2 건: [[graphrag-poc-with-neo4j]], [[2do-brain-architecture]]
        [출처] frontmatter id 2 건, sources raw 1 건
        
        답변 후보:
        - [[graphrag-poc-with-neo4j]] — Neo4j + 고정 Cypher 로 인과 경로 추출·검증
        - [[2do-brain-architecture]] — 전체 5층 청사진 중 L3 (그래프 층)
        
        자세히 보려면 vault/02_wiki/topics/2026-05-17-graphrag-poc-with-neo4j.md 열기.

사용자: /query Anthropic 이 어떤 기술 쓰지
Claude: [의도] relation (키워드 "어떤 X 쓰지")
        [graph] query_graph.py causal_path --param company_canonical=Anthropic
                 → (Neo4j 미기동 → dry-run, Cypher 만 출력)
        
        Neo4j 미기동 상태입니다. docker compose up -d 후 다시 호출하세요.
        또는 local 검색으로 대체: [[2do-brain-architecture]] 의 "Claude Code 메커니즘" 섹션 참조.
```

## 실패 시

- 검색 결과 0 건 → "vault 에 후보 없음. 관련 raw 가 ingest 됐는지 확인" 안내
- graph 호출 실패 (Neo4j) → 자동으로 local 폴백 + 안내
- 모호한 질문 → 사용자에게 명확화 요청 (1 질문)

## 메모

- complex 분기는 LLM 추론을 요청하지 않는다. local + graph 결과를 병합만 함
- 새 의도 카테고리가 생기면 본 SKILL.md 의 분류 표 + 라우팅 확장 (lint 규칙은 영향 없음)
