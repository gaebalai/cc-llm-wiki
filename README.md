# cc-llm-wiki

Claude Code 중심의 풀스택 LLM Wiki 환경.
Karpathy의 LLM Wiki 원전(1·2번) + Context Engineering(4번) + Routine 자동화(5·7번) + Skills 권한 분리(8번) + Neo4j GraphRAG PoC(11번)를 하나의 모노 리포로 통합.

## 핵심 원칙

1. **3층 격리**: `vault/01_raw/`(불변) · `vault/02_wiki/`(LLM 편찬) · `vault/SCHEMA.md`(사람 규율)
2. **단방향 흐름**: raw → wiki → graph/index → search (역방향 쓰기 금지)
3. **컨텍스트 위생**: raw 읽기 전용 강제, JIT 검색, 인간 승인 게이트

## 디렉터리

```
cc-llm-wiki/
├── CLAUDE.md              # 헌법 (11 섹션)
├── vault/
│   ├── 01_raw/            # 원전 보존 (Read-Only, Hook이 차단)
│   ├── 02_wiki/
│   │   ├── self/          # 비공개, 외부 발행 금지
│   │   ├── decisions/     # ADR (덮어쓰기 금지)
│   │   ├── topics/        # 공개 가능 지식 노드
│   │   ├── digests/       # routine 산출
│   │   ├── _drafts/       # ingest 임시 산출
│   │   └── _lint/         # 주간 lint 리포트
│   ├── 03_schema/         # frontmatter·node·relation 스키마 YAML
│   ├── SCHEMA.md          # 사람이 정의한 사서 규율
│   ├── index.md           # 전체 카탈로그
│   └── log.md             # 모든 LLM 행동 로그
├── .claude/
│   ├── skills/            # ingest·lint (P0~P1) → +compile·query·… (P3~)
│   ├── routines/          # daily-digest·weekly-lint·… (P4~)
│   ├── queue/             # Hook이 graph-sync 큐 적재
│   └── settings.local.json
├── infra/neo4j/           # P5 GraphRAG PoC
├── services/graph/        # LangChain ingest/query 스크립트 (P5)
├── dist/i18n/{ko,en,ja}/  # 다국어 정적 출력 (P4)
└── docs/                  # 11개 설계 문서 (참조용)
```

## Phase 로드맵

| Phase | 목표 | 산출 |
|---|---|---|
| **P0** ✅ | git·골격·금지 가드레일 | CLAUDE.md, vault/, .gitignore, settings.local.json |
| **P1** | 1편 raw → wiki 토론 ingest | `.claude/skills/ingest/SKILL.md` 실전 호출 |
| **P2** | Context Engineering 5대 가드 | `.claude/skills/lint/`, SCHEMA.md 본문 |
| **P3** | compile Skill + Dataview 보드 | `.claude/skills/compile/`, `vault/dashboards/status.md` |
| **P4** | daily-digest + 다국어 publish | `.claude/routines/`, `scripts/post_slack.py`, `dist/` |
| **P5** | Neo4j GraphRAG PoC | `infra/neo4j/docker-compose.yml`, `services/graph/` |
| **P6** | 정착·확장 (Kagura MCP 옵션) | `vault/02_wiki/private/llm-wiki-origins.md` |

자세한 설계는 `/Users/gaebalai/.claude/plans/docs-11-twinkling-lemon.md` 참조.

## 이번 단계에서 하지 않을 것

- 11문서 전체를 P0에서 한꺼번에 구현하지 않는다 (P0~P1만 스캐폴드)
- Kagura MCP는 P5 이후 옵션
- 자연어 → Cypher LLM 생성 금지 (고정 템플릿만)
- Self/ 폴더는 어떤 자동 발신·MCP·그래프 동기에도 노출 금지
- 쓰기 Skill의 모델 자동 호출 금지 (Routine·명시 명령만)
- raw/ 직접 편집·자동 정리 절대 금지 (Hook이 exit 2로 차단)

## 다음 단계

1. Obsidian에서 `vault/` 폴더를 Vault로 열기
2. `Settings → Files & Links → Excluded files`에 `plans/` 추가
3. Claude Code 세션에서 `/ingest` Skill로 첫 raw 1건 처리 (P1)
