---
id: 2026-05-17T184500-2do-brain-architecture
type: topic
status: reviewed
locale: ko
sources:
  - vault/01_raw/articles/2026-05-17-2do-brain-neo4j-graphrag-poc.md
related:
  - "[[graphrag-poc-with-neo4j]]"
  - "[[entity-disambiguation-strategy]]"
updated_at: 2026-05-18T02:30:00+09:00
graph_synced_at: 2026-05-18T03:30:00+09:00
---

# 2do BRAIN Architecture

## 핵심 주장

**Claude Code × Obsidian × Neo4j**를 묶은 "자율형 지식 OS"의 전체 청사진.
사람은 raw를 던지고 핵심 결정만 하며, LLM은 정해진 권한·게이트 안에서 위키를 편찬·검색·발신한다.
핵심은 "AI 자동화"가 아니라 "**사람 토론 + 권한 분리 + 단방향 흐름**" 3축의 결합.

## 5층 구조

| 층 | 구성 | 책임 |
|---|---|---|
| L0 Source | Web Clipper, 외부 SaaS, 수동 메모 | 원전 인입 |
| L1 Raw | `vault/01_raw/` (Read-Only) | 불변 보존 |
| L2 Wiki | `vault/02_wiki/` (LLM 편찬) | 정합성·관계 부여 |
| L3 Graph | Neo4j + 고정 Cypher | 다중-홉 관계 탐색 — [[graphrag-poc-with-neo4j]] |
| L4 Skills | Claude Code: ingest·compile·lint·query·publish·digest | 오케스트레이션 |
| L5 Surface | Obsidian·Cloudflare Pages·Slack | 사람·외부 인터페이스 |

## 횡단적 지견

- **[[entity-disambiguation-strategy]] 가 L3 품질의 핵심**: 정규화 없는 그래프는 인과 경로가 끊긴다.
- **검색 라우팅**: 의미·키워드 검색은 Obsidian Dataview + grep + Cypher 템플릿 조합. 외부 인덱스 서비스 불필요.
- **단방향 데이터 흐름**: L0 → L1 → L2 → L3 → L4 → L5. 역방향 쓰기는 모든 층에서 금지.
- **사람 게이트**: ingest 토론·compile lint 승인·decisions append-only 등 3대 게이트가 자동화 폭주를 막는다.

## Claude Code 메커니즘 매핑

- **Skill**: 9종 (ingest·compile·query·lint·graph-sync·daily-digest·publish·morning-brief·evening-reflect)
- **Hook**: PreToolUse(raw 차단·main 직커밋 차단), SessionStart(상태 가시화), Stop(모순 검출 게이트)
- **Routine**: 6종 (daily-digest·wiki-ingest-sweep·weekly-lint·sleep-maintenance·publish-multilang·morning-digest-recap)
- **MCP**: GitHub(P0), Slack(P4 옵션), Neo4j(P5)
- **권한 분리**: 쓰기 Skill 4종은 `disable-model-invocation: true`로 자동 호출 차단

## 미해결 질문

- L5 Surface 의 다국어(ko→en→ja) 자동 번역 품질 임계는 (P4 진입 시 실측 필요)
- 본 아키텍처 자체를 다른 사용자에게 이식할 때 어디까지 일반화 가능한가
