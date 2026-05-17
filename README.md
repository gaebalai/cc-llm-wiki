# cc-llm-wiki

> Karpathy 의 LLM Wiki 원전부터 Neo4j GraphRAG PoC 까지 11 개 설계 문서를 통합한
> **Claude Code 중심 로컬 전용 LLM Wiki**.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Plugin: Claude Code](https://img.shields.io/badge/Plugin-Claude_Code-blue)](https://github.com/gaebalai/cc-llm-wiki)
[![Phase: P6](https://img.shields.io/badge/Phase-P6_complete-green)](#phase-로드맵)

## 무엇

- **Obsidian vault + Claude Code 9 Skills + Neo4j 그래프**의 통합 환경
- 외부 공개·발신 없는 **로컬 전용** (Cloudflare 등 publish 라인 제외)
- 자료가 쌓일수록 **복리로 성장**하는 지식 베이스 (요약 자동화 아님)

## 빠른 시작

```
/plugin marketplace add gaebalai/cc-llm-wiki
/plugin install cc-llm-wiki@claudecode-to-marketplace
/install
```

자세한 단계별 가이드: **[QUICKSTART.md](QUICKSTART.md)** ← 첫 사용자는 여기부터

## 핵심 원칙

1. **3 층 격리** — `vault/01_raw/`(불변) · `vault/02_wiki/`(LLM 편찬) · `vault/SCHEMA.md`(사람 규율)
2. **단방향 흐름** — raw → wiki → graph (역방향 쓰기 금지)
3. **컨텍스트 위생** — raw 읽기 전용 강제, JIT 검색, 인간 승인 게이트

## 디렉터리

```
cc-llm-wiki/
├── CLAUDE.md                    # 헌법 (11 섹션)
├── QUICKSTART.md                # ← 첫 사용자 가이드
├── README.md                    # 본 파일
│
├── .claude-plugin/              # Plugin marketplace + manifest
│   ├── marketplace.json
│   └── plugin.json
├── .claude/
│   ├── skills/                  # 4 활성 (ingest·lint·compile·graph-sync)
│   ├── commands/                # /install
│   ├── routines/                # weekly-lint·weekly-review·daily-digest
│   ├── queue/                   # PostToolUse hook 이 graph 큐 적재
│   ├── settings.json            # 공유 (Hook·permissions)
│   └── settings.local.json      # 개인 (글로벌 ignore)
│
├── vault/
│   ├── 01_raw/                  # 원전 보존 (Read-Only Hook)
│   ├── 02_wiki/
│   │   ├── self/                # 비공개, 어디에도 노출 금지
│   │   ├── decisions/           # ADR (append-only)
│   │   ├── topics/              # 지식 노드 (현재 3 건)
│   │   ├── digests/             # daily-digest routine 산출
│   │   ├── _drafts/             # ingest 임시 산출
│   │   └── _lint/               # 주간 lint 리포트
│   ├── 03_schema/aliases.yaml   # entity 정규화 (14 canonical / 47 aliases)
│   ├── SCHEMA.md                # 사서 규율 (5 섹션)
│   ├── index.md                 # 카탈로그
│   ├── log.md                   # 모든 LLM 행동 기록
│   └── dashboards/status.md     # Dataview 6 쿼리
│
├── infra/neo4j/                 # docker-compose.yml (Neo4j 5.18.1 + APOC)
├── services/graph/              # ingest_graph.py / query_graph.py / templates
├── scripts/                     # install.sh (7-step) / post_slack.py
├── docs/                        # 11 개 설계 문서 (gitignore)
└── docs-internal/               # 저자용 (PUBLISH.md)
```

## 활성 자산

| 영역 | 자산 | 비고 |
|---|---|---|
| Skill | `ingest` · `lint` · `compile` · `graph-sync` | 4 종, P1~P5 |
| Command | `/install` | 7-단계 원스톱 installer |
| Routine | `weekly-lint` (일 06:00) · `weekly-review` (일 21:00) | KST cron |
| Hook | PreToolUse (raw 차단, main 차단) · PostToolUse (graph 큐) · SessionStart | |
| 인프라 | Neo4j 5.18.1 + APOC (Docker) | dry-run 가능 |
| 검색 | Cypher 템플릿 3 종 (causal_path / concept_neighbors / orphan_audit) | 고정 템플릿만 |

## Phase 로드맵

| Phase | 목표 | 상태 |
|---|---|---|
| P0 | git·골격·헌법 + raw Read-Only Hook | ✅ |
| P1 | raw → wiki 토론 ingest | ✅ (3 topics) |
| P2 | Context 가드 (lint 10 항목 + SCHEMA §5 명문화) | ✅ |
| P3 | compile Skill + Dataview 보드 | ✅ |
| P4 | weekly-lint routine + Slack 골격 | ✅ (daily-digest 본체 후속) |
| P5 | Neo4j GraphRAG PoC + PostToolUse 큐 hook | ✅ |
| P6 | llm-wiki-origins + weekly-review | ✅ |
| Plugin | marketplace.json + plugin.json + install.sh | ✅ |

설계 plan 전체: `~/.claude/plans/docs-11-twinkling-lemon.md`

## 이 환경에서 하지 않는 것

- **외부 공개·다국어 HTML 발행** (publish Skill·Cloudflare Pages·`dist/` 제외) — 로컬 전용 결정
- **자연어 → Cypher LLM 자동 생성** (고정 템플릿만)
- `self/` 폴더 내용을 graph·digest·MCP·query 응답에 노출
- 쓰기 Skill 의 모델 자동 호출 (Routine·명시 명령만)
- raw/ 직접 편집·자동 정리 (Hook 이 exit 2 로 차단)
- Kagura MCP (P6 옵션 — 4 주 자생 검증 후 결정)

## Plugin 으로 사용

본 리포는 **단일-plugin 마켓플레이스** 패턴 (`.claude-plugin/marketplace.json` + `.claude-plugin/plugin.json`).

```
/plugin marketplace add gaebalai/cc-llm-wiki        # 추가 (1 회)
/plugin install cc-llm-wiki@claudecode-to-marketplace              # 설치 (1 회)
/plugin update cc-llm-wiki@claudecode-to-marketplace               # 업데이트
```

설치 후 자동 활성화:
- Commands: `/install` (1 건)
- Skills: `ingest` · `lint` · `compile` · `graph-sync` (4 건)

⚠ Plugin 활성 시 `.claude/settings.json` 의 hooks 는 자동 로드되지 않습니다.
별도 프로젝트에서 사용 시 `/install` 이 사용자 `.claude/settings.json` 에 hooks 를 머지하는 흐름은 **다음 release** 에서 추가.

## 보안

- `.env.example` 은 placeholder 만. 실제 시크릿은 `.env` 에 (`.gitignore` 자동 무시).
- 시크릿 push 사고 방지: `git ls-files | xargs grep -lE 'xox[abeops]-|sk-[a-zA-Z0-9_-]{20,}'` 로 push 전 검사.
- `install.sh` 가 `.env` 안전성 (gitignore 처리) 자동 검증.

## 기여 / 게시

- 첫 사용자: **[QUICKSTART.md](QUICKSTART.md)**
- 저자 (push/release): **[docs-internal/PUBLISH.md](docs-internal/PUBLISH.md)**
- 설계 결정 회고: **[vault/02_wiki/self/llm-wiki-origins.md](vault/02_wiki/self/llm-wiki-origins.md)**

## 라이선스

[MIT](LICENSE)
