# cc-llm-wiki

> Karpathy 의 LLM Wiki 원전부터 Neo4j GraphRAG PoC 까지 11 개 설계 문서를 통합한
> **Claude Code 중심 로컬 전용 LLM Wiki**.

[![CI](https://github.com/gaebalai/cc-llm-wiki/actions/workflows/ci.yml/badge.svg)](https://github.com/gaebalai/cc-llm-wiki/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Plugin: Claude Code](https://img.shields.io/badge/Plugin-Claude_Code-blue)](https://github.com/gaebalai/cc-llm-wiki)
[![Version](https://img.shields.io/badge/version-0.4.4-green)](https://github.com/gaebalai/cc-llm-wiki/releases)
[![Changelog](https://img.shields.io/badge/changelog-keep--a--changelog-blue)](CHANGELOG.md)

## 무엇

- **Obsidian vault + Claude Code 9 Skills + Neo4j 그래프**의 통합 환경
- 외부 공개·발신 없는 **로컬 전용** (Cloudflare 등 publish 라인 제외)
- 자료가 쌓일수록 **복리로 성장**하는 지식 베이스 (요약 자동화 아님)

## 빠른 시작

### Plugin 경로 (권장, v0.2.0+)

```bash
mkdir ~/my-knowledge-base && cd ~/my-knowledge-base
claude   # Claude Code 세션
```

세션 안에서:
```
/plugin marketplace add gaebalai/cc-llm-wiki
/plugin install cc-llm-wiki@claudecode-to-marketplace
/install
```

→ `install.sh` 가 PLUGIN_INSTALL 자동 감지 → 템플릿을 `~/my-knowledge-base/` 로 복사 + 사용자 `.claude/settings.json` 에 Hook 안전 머지.

### git clone 경로 (v0.1.0 또는 plugin 없이)

```bash
git clone https://github.com/gaebalai/cc-llm-wiki.git ~/cc-llm-wiki
cd ~/cc-llm-wiki
bash scripts/install.sh
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
│   ├── 03_schema/aliases.yaml   # entity 정규화 (18 canonical / 60 aliases)
│   ├── 03_schema/eval-gold/     # P/R/F1 정답셋 (사람 검수 보강)
│   ├── SCHEMA.md                # 사서 규율 (5 섹션)
│   ├── index.md                 # 카탈로그
│   ├── log.md                   # 모든 LLM 행동 기록
│   └── dashboards/status.md     # Dataview 6 쿼리
│
├── infra/neo4j/                 # docker-compose.yml (Neo4j 5.18.1 + APOC)
├── services/graph/              # ingest_graph/ingest_llm/ingest_merge/eval.py + templates
├── scripts/                     # install.sh / post_slack.py / daily_digest_runner.py
├── docs/                        # 11 개 설계 문서 (gitignore)
└── docs-internal/               # 저자용 (PUBLISH.md)
```

## 활성 자산

| 영역 | 자산 | 비고 |
|---|---|---|
| Skill | `ingest` · `lint` · `compile` · `query` · `graph-sync` · `morning-brief` · `evening-reflect` · `daily-digest` | **8 종** (v0.3.0+) |
| Command | `/install` | 7+1 단계 원스톱 installer (PLUGIN_INSTALL 자동 감지) |
| Routine | `weekly-lint` (일 06:00) · `weekly-review` (일 21:00) · `wiki-ingest-sweep` (매시) · `sleep-maintenance` (매일 03:00) · `daily-digest` (매일 07:00) | KST cron, **5 active** (v0.4.3+) |
| Hook | PreToolUse (raw·main 차단) · PostToolUse (graph 큐) · SessionStart · UserPromptSubmit · Stop | **5 종** (v0.3.0+) |
| 인프라 | Neo4j 5.18.1 + APOC (Docker) | dry-run 가능, 실 검증 완료 (v0.3.1) |
| 검색 | Cypher 템플릿 3 종 (causal_path / concept_neighbors / orphan_audit) | 고정 템플릿만 |
| GraphRAG | 룰베이스 (`ingest_graph.py`) + LangChain LLM (`ingest_llm.py`) + 머지 (`ingest_merge.py`) | v0.4.0+, SOLVES/USES 의미 관계 |
| 평가 | P/R/F1 자동 측정 (`services/graph/eval.py`) + gold YAML | v0.4.2+, CI 통합 (10 항목) |
| daily-digest | `positioning.md` 의존 + 5 쿼리 자동 설계 (`daily_digest_runner.py`) | v0.4.3+, Slack 옵션 |
| vault 컨벤션 | **flat** (TARGET_DIR 자체) 또는 **subdir** (TARGET_DIR/vault) | v0.3.6+ 자동 감지 (Obsidian 친화 = flat 기본) |

## Phase 로드맵

| Phase | 목표 | 상태 |
|---|---|---|
| P0 | git·골격·헌법 + raw Read-Only Hook | ✅ |
| P1 | raw → wiki 토론 ingest | ✅ (3 topics) |
| P2 | Context 가드 (lint 10 항목 + SCHEMA §5 명문화) | ✅ |
| P3 | compile Skill + Dataview 보드 | ✅ |
| P4 | weekly-lint routine + Slack 골격 | ✅ |
| P5 | Neo4j GraphRAG PoC + PostToolUse 큐 hook | ✅ |
| P6 | llm-wiki-origins + weekly-review | ✅ |
| Plugin v0.1.0 | marketplace.json + plugin.json + install.sh | ✅ |
| Plugin v0.2.0 | PLUGIN_INSTALL 자동 감지 + Hook 머지 + 템플릿 복사 | ✅ |
| Plugin v0.3.0 | 8 Skills 완성 (query·morning-brief·evening-reflect·daily-digest) + 2 hooks 신설 | ✅ |
| Plugin v0.3.1~v0.3.5 | 실 Neo4j 검증 + plugin install validation 5 회 패치 | ✅ |
| Plugin v0.3.6 | vault 평탄화 컨벤션 (flat) 지원 + raw 슬러그 한글 허용 | ✅ |
| Plugin v0.3.7 | GitHub Actions CI (10 항목) + Obsidian Excluded files 자동 머지 | ✅ |
| Plugin v0.3.8~v0.3.10 | 외부 vault 절대경로 + env 우선순위 + wikilink stem/short 양쪽 매칭 | ✅ |
| Plugin v0.4.0~v0.4.1 | LangChain LLMGraphTransformer + 헤더 청크 + 머지 runner | ✅ |
| Plugin v0.4.2 | P/R/F1 평가 cycle (rule/llm/consistency 3 mode) | ✅ |
| Plugin v0.4.3 | daily-digest 본체 (positioning.md + WebSearch 호출 명세) | ✅ |
| Plugin v0.4.4 | CHANGELOG + Dataview 강화 (6→10 쿼리) + contributors 가이드 | ✅ |

설계 plan 전체: `~/.claude/plans/docs-11-twinkling-lemon.md`
변경 이력 전체: **[CHANGELOG.md](CHANGELOG.md)**

## 이 환경에서 하지 않는 것

- **외부 공개·다국어 HTML 발행** (publish Skill·Cloudflare Pages·`dist/` 제외) — 로컬 전용 결정
- **자연어 → Cypher LLM 자동 생성** (고정 템플릿만)
- `self/` 폴더 내용을 graph·digest·MCP·query 응답에 노출
- 쓰기 Skill 의 모델 자동 호출 (Routine·명시 명령만)
- raw/ 직접 편집·자동 정리 (Hook 이 exit 2 로 차단)

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

## 기여 (Contributing)

본 리포는 **개인 vault 운영 + plugin marketplace 두 가지 모드**로 동작.
기여 방향에 따라 작업 위치가 다릅니다.

### 1. 자료 추가 (개인 vault, 가장 흔함)

본인의 vault (`~/my-knowledge-base/` 등) 에서 자료 추가는 본 repo 와 무관.
다만 vault 자체를 별도 private git repo 로 만드는 것을 권장 (self/ 백업).

```bash
cd ~/my-knowledge-base && git init && git add . && git commit -m "[init] my vault"
gh repo create my-knowledge-base --private --source=. --push   # 본인 계정에 private
```

### 2. Skill / Hook / Routine 수정 (본 repo PR)

| 영역 | 위치 | 수정 시 검증 |
|---|---|---|
| Skill 본문 | `skills/<name>/SKILL.md` | frontmatter 필수 키 (`name`·`description`·`allowed-tools`) — CI 항목 3 |
| Hook | `.claude/settings.json` 의 hooks 섹션 | `python -c "import json; json.load(open('.claude/settings.json'))"` |
| Routine | `.claude/routines/<name>.md` | `/schedule create` 로 사용자 환경 등록 (자동 X) |
| GraphRAG | `services/graph/*.py` | `python -m py_compile services/graph/<file>.py` |
| install.sh | `scripts/install.sh` | `bash -n scripts/install.sh && bash scripts/install.sh --step 1 --check` |
| Cypher 템플릿 | `services/graph/templates/*.cypher` | 자연어→Cypher 자동 생성 금지 (CLAUDE.md §3-4) — 고정 템플릿만 |

### 3. 자료 vs 코드 경계

- **자료 (vault/)**: 본인 vault 변경은 본 repo 와 별개 (gitignore 권장)
- **코드 (skills/·services/·infra/)**: 본 repo PR
- **헌법 (CLAUDE.md)**: PR 필수, 변경 시 vault SCHEMA.md / dashboards 영향 확인

### 4. PR 패턴

| 단계 | 명령 / 위치 |
|---|---|
| 브랜치 | `git checkout -b auto-{ingest,digest,lint,graph}/YYYY-MM-DDTHHMM-{slug}` (자동) <br> 또는 `feat/...` `fix/...` `docs/...` (수동) |
| 커밋 | 한국어 1줄 + Skill prefix (`[ingest] ...` / `[ci] ...` / `[docs-sync] ...`) |
| 검증 | CI 10 항목 자동 (push 시) — JSON·SKILL frontmatter·bash syntax·python compile·install --check·vault lint·시크릿 leak·.env 보호·eval |
| 머지 | squash merge, PR 제목 = 첫 커밋 제목 |
| 금기 | main 직커밋·force-push·`--no-verify` (Hook 이 차단) |

### 5. 변경 카테고리 (CHANGELOG 작성 시)

`CHANGELOG.md` 는 **Keep a Changelog 1.1.0** 형식.

- **Added** / **Changed** / **Deprecated** / **Removed** / **Fixed** / **Security**
- 사람이 읽는 톤 (commit 메시지 그대로 복붙 X)
- 사용자 입장에서 의미 있는 변경만 (내부 리팩터·CI 미세 패치는 묶어 1 줄)

### 6. 보안 / 시크릿

- **`.env.example` 에 placeholder 만** — 실제 토큰 입력 시 git push 전 차단 필수
- `git ls-files | xargs grep -lE 'xox[abeops]-|sk-[a-zA-Z0-9_-]{20,}'` push 전 검사 (CI 항목 8 이 자동)
- `self/` 폴더 내용을 graph·digest·MCP·query 응답에 절대 노출 금지 (CLAUDE.md §3-5)

## 게시 / 회고

- 첫 사용자: **[QUICKSTART.md](QUICKSTART.md)**
- 저자 (push/release): **[docs-internal/PUBLISH.md](docs-internal/PUBLISH.md)**
- 설계 결정 회고: **[vault/02_wiki/self/llm-wiki-origins.md](vault/02_wiki/self/llm-wiki-origins.md)**
- 변경 이력: **[CHANGELOG.md](CHANGELOG.md)**

## 라이선스

[MIT](LICENSE)
