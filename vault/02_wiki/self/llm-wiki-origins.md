---
id: 2026-05-17T210000-llm-wiki-origins
type: self
status: reviewed
locale: ko
sources:
  - vault/01_raw/articles/2026-05-17-2do-brain-neo4j-graphrag-poc.md
related:
  - "[[2do-brain-architecture]]"
updated_at: 2026-05-17T21:00:00+09:00
graph_synced_at: null
---

# LLM Wiki — 원전 vs 확장 경계

이 페이지는 본 vault 의 **DNA 기록**이다. 어느 결정이 Karpathy 원전에서 왔고
어느 결정이 후속 확장(11 docs)에서 추가됐는지 명시한다. self/ 폴더에 두는 이유는
외부 노출이 부적절하기 때문이 아니라 **사적 회고**이기 때문 (개인 학습 일기).

## DNA 트리

```
Karpathy 원전 (2024-25)
├── 3층 구조 (raw / wiki / schema)
├── ingest / query / lint 3 operations
├── 개념 페이지 = 횡단적 지견의 응축
└── "AI 가 연결, 사람이 이해" 분업 원칙
        │
        ▼
        ├─ 2번 docs: Obsidian + Claude Code 매핑
        │   ├── YAML frontmatter (type/sources/related)
        │   ├── 2계층 index 구조
        │   └── /skill-creator 활용
        │
        ├─ 3번 docs: 함정 10가지 + CLAUDE.md 9 섹션
        │   └── "금지 우선 배치" 원칙
        │
        ├─ 4번 docs: Context Engineering 6 기법 매핑
        │   └── Anthropic 가이드와 일대일 대응
        │
        ├─ 5번 docs: routine + Slack + auto-digest PR  ← (Slack 옵션, publish 제거)
        ├─ 6번 docs: self/decisions/synthesis 3 분리
        ├─ 7번 docs: 다국어 publish + Cloudflare      ← (전체 제거, 로컬 전용)
        ├─ 8번 docs: disable-model-invocation + allowed-tools 스코핑
        ├─ 9번 docs: Kagura 3중 인덱스 + MCP            ← (P6 옵션, 4주 자생 후 결정)
        ├─ 10번 docs: SCHEMA.md "사서 규율"
        └─ 11번 docs: Neo4j + LangChain GraphRAG PoC   ← (P5 골격)
```

## 본 vault 가 채택한 것 vs 거른 것

### 채택

| 출처 | 무엇을 | 어디서 살아있는가 |
|---|---|---|
| Karpathy 원전 | 3층 격리, ingest/query/lint, 횡단적 지견 | vault/SCHEMA.md, ingest SKILL §5 본문 구조 |
| 2 docs | YAML frontmatter, 2계층 index | SCHEMA §2, vault/index.md |
| 3 docs | CLAUDE.md 금지 우선 배치, raw 불변 Hook | CLAUDE.md §3, .claude/settings.json PreToolUse |
| 4 docs | Context Engineering — quarantine/JIT/lint | Hook + lint Skill + index.md JIT 진입점 |
| 5 docs | routine + auto-* PR 패턴 | .claude/routines/weekly-lint.md |
| 6 docs | self/decisions/topics 분리 | vault/02_wiki/{self,decisions,topics}/ |
| 8 docs | disable-model-invocation, allowed-tools 스코핑 | compile/daily-digest SKILL frontmatter |
| 10 docs | SCHEMA.md 사서 규율 | vault/SCHEMA.md §4 |
| 11 docs | Neo4j + 고정 Cypher + entity disambiguation | infra/neo4j/, services/graph/, vault/03_schema/aliases.yaml |

### 거른 것 (의도된 제외)

| 출처 | 무엇을 | 이유 |
|---|---|---|
| 7 docs | 다국어 자동 publish, Cloudflare Pages | **로컬 전용** 결정 (2026-05-17). 외부 공개 의도 없음 |
| 9 docs | Kagura MCP (BM25+Qdrant+Hebbian) | 외부 의존 늘리기 전 4주 자생 검증. P6+ 옵션 |
| 5 docs | morning-digest-recap (Slack 리액션 수집) | Slack 의존 + 운영 부담. daily-digest 안정 후 결정 |
| 6 docs | morning/evening hook 자동 호출 | Hook 폭주 위험. 명시적 인사 매칭만 settings.json 에 (미구현) |
| Karpathy 원전 | "전체 vault 매번 LLM 통째 입력" 권유 부분 | 4 docs Context Rot 와 모순. JIT 진입점으로 대체 |

### 의도적으로 미루기

| 항목 | 언제 결정 |
|---|---|
| `daily-digest` Skill 본체 작성 | positioning.md 작성 후 |
| `publish` 복원 | 외부 공개 의도가 생기는 시점 (현재 없음) |
| Kagura MCP 등록 | 4주 운영 후 검색 한계가 진짜 느껴질 때 |
| PostToolUse graph queue hook | P5 보완 (이번 P6 에서 처리) |
| morning/evening hook 자동화 | 1개월 운영 후 패턴이 보일 때 |

## 회고 메모 (운영 시 누적)

> 본 페이지는 self/ 라 LLM 이 외부로 인용하지 않는다(SCHEMA §4-④).
> 운영 중 "이 결정이 정말 옳았나" 를 발견하면 본 페이지에 timestamp 와 함께 append.

- 2026-05-17 — **raw 불변 완전 금지는 비현실적**. 원전이 메타 노이즈(SEO 후보·번역 노트·이미지 자리 표시) 로 오염된 채 ingest 되면 wiki 본문의 인용도 같이 오염된다. → **SCHEMA §6 신설**: 사람의 1 회 정리 허용 (메타-only, 본문 의미 무변경, 트레일러 marker + `[raw-clean]` commit). 첫 적용: `vault/01_raw/articles/2026-05-17-2do-brain-neo4j-graphrag-poc.md`.
- (예시) 2026-06-XX — Kagura 없이도 topics 50건까지는 grep + Dataview 로 충분. 4주 검증 결과
- (예시) 2026-06-XX — Slack 통지 한 번도 안 봄. daily-digest routine 자체를 비활성 검토

## 외부에 묻고 싶다면

본 vault 의 운영 경험을 외부 공개하고 싶어지는 시점이 오면:
1. **이 페이지는 영원히 self/** — 회고 본문은 비공개
2. 별도 `topics/llm-wiki-public-recap.md` 를 만들고 공개 가능한 정리만 거기에
3. 그 시점에 publish 라인 복원 검토 (CLAUDE.md §4 publish Skill 부활 PR)
