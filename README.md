# cc-llm-wiki

Claude Code 중심의 **로컬 전용** LLM Wiki 환경.
Karpathy의 LLM Wiki 원전(1·2번) + Context Engineering(4번) + Routine 자동화(5번 일부) + Skills 권한 분리(8번) + Neo4j GraphRAG PoC(11번)를 모노 리포로 통합.

**범위 결정 (2026-05-17)**: 외부 공개·다국어 HTML 발행은 하지 않는다.
7번 docs 의 풀스택 제안 중 publish/Cloudflare 라인은 **제외**.

## 핵심 원칙

1. **3층 격리**: `vault/01_raw/`(불변) · `vault/02_wiki/`(LLM 편찬) · `vault/SCHEMA.md`(사람 규율)
2. **단방향 흐름**: raw → wiki → graph/index (역방향 쓰기 금지, 외부 발신 없음)
3. **컨텍스트 위생**: raw 읽기 전용 강제, JIT 검색, 인간 승인 게이트

## 디렉터리

```
cc-llm-wiki/
├── CLAUDE.md              # 헌법 (11 섹션)
├── vault/
│   ├── 01_raw/            # 원전 보존 (Read-Only, Hook 차단)
│   ├── 02_wiki/
│   │   ├── self/          # 비공개, 어디에도 노출 금지
│   │   ├── decisions/     # ADR (덮어쓰기 금지)
│   │   ├── topics/        # 지식 노드
│   │   ├── digests/       # daily-digest routine 산출
│   │   ├── _drafts/       # ingest 임시 산출
│   │   └── _lint/         # 주간 lint 리포트
│   ├── 03_schema/         # frontmatter/aliases.yaml
│   ├── SCHEMA.md          # 사람이 정의한 사서 규율
│   ├── index.md           # 전체 카탈로그
│   ├── log.md             # 모든 LLM 행동 로그
│   └── dashboards/        # Obsidian Dataview 보드
├── .claude/
│   ├── skills/            # ingest·lint·compile·graph-sync (활성 4종)
│   ├── routines/          # weekly-lint·daily-digest (활성/dry-run)
│   ├── queue/             # Hook 이 graph-sync 큐 적재
│   ├── settings.json      # 공유 설정 (Hook·permissions)
│   └── settings.local.json # 개인 설정 (글로벌 ignore)
├── infra/neo4j/           # P5 GraphRAG PoC (docker-compose)
├── services/graph/        # ingest_graph.py / query_graph.py / templates
├── scripts/               # post_slack.py 등
└── docs/                  # 11개 설계 문서 (참조용, .gitignore)
```

## Phase 로드맵

| Phase | 목표 | 상태 |
|---|---|---|
| **P0** | git·골격·헌법 + raw Read-Only Hook | ✅ |
| **P1** | 1편 raw → wiki 토론 ingest | ✅ (3 topics 승급) |
| **P2** | Context 가드 (lint 10 항목 + SCHEMA §5 명문화) | ✅ |
| **P3** | compile Skill + Dataview 보드 | ✅ |
| **P4** | daily-digest + weekly-lint routine | ✅ 골격 (Skill 본체 후속) |
| **P5** | Neo4j GraphRAG PoC | ✅ 골격 + PostToolUse queue hook 활성 |
| **P6** | 정착 (origins 회고 + weekly-review routine) | ✅ |

자세한 설계: `~/.claude/plans/docs-11-twinkling-lemon.md`

## 이번 환경에서 하지 않는 것

- **외부 공개·다국어 HTML 발행** (publish Skill·Cloudflare Pages·dist/ 라인 전체 제외)
- 자연어 → Cypher LLM 생성 (고정 템플릿만)
- `self/` 폴더 내용을 graph·digest·MCP·query 응답에 노출
- 쓰기 Skill 의 모델 자동 호출 (Routine·명시 명령만)
- raw/ 직접 편집·자동 정리 (Hook 이 exit 2 로 차단)
- Kagura MCP (P6 옵션 — 4주 자생 검증 후 결정)

## 다음 단계

1. Obsidian 에서 `vault/` 폴더를 Vault 로 열기
2. `Settings → Files & Links → Excluded files` 에 `plans/` 추가
3. `Settings → Community plugins` 에서 Dataview 설치 후 `vault/dashboards/status.md` 열기
4. 실 동작 (선택):
   - Neo4j: `cp .env.example .env` → `NEO4J_PASSWORD` 채우기 → `docker compose -f infra/neo4j/docker-compose.yml up -d` → `pip install neo4j`
   - Slack 알림(선택): `.env` 에 `SLACK_WEBHOOK_URL` 추가, 안 채우면 자동 dry-run
