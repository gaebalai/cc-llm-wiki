# Claude Code 로 만드는 "복리로 자라는" 개인 지식 베이스 — cc-llm-wiki 소개

> Karpathy 의 LLM Wiki 원전부터 Neo4j GraphRAG PoC 까지 11 개 설계 문서를 토대로 한 환경으로 통합했다.
> Plugin 한 줄로 깔고 `/install` 명령으로 7 단계 셋업이 끝난다.
> RAG 의 "매번 0 부터 검색" 패턴 대신, **위키화한 지식이 시간이 갈수록 복리로 자라는** 구조다.

---

## 0. 왜 또 PKM 도구인가

요즘 Personal Knowledge Management 도구는 차고 넘친다. Obsidian, Notion, Logseq, Roam, Reflect...
그런데 LLM 시대에 와서 새 문제가 생겼다.

**"AI 가 매번 0 부터 검색하고 합성하는 RAG 패턴은 지식이 축적되지 않는다."**

RAG 는 매 질의마다:
1. 임베딩으로 비슷한 청크 찾고
2. LLM 에게 통째 던지고
3. 합성된 답을 받고
4. **답은 휘발**된다

이게 반복되면 똑같은 질문에 매번 다른 답이 나오고, 발견한 통찰은 어디에도 안 쌓인다.

Andrej Karpathy 는 작년에 이런 글을 썼다 (요약):

> RAG 의 "검색 → 합성" 으로 끝낼 게 아니라, **"검색 → 합성 → 컴파일 → 축적"** 으로 가야 한다.
> LLM 의 진짜 가치는 요약이 아니라 **여러 자료를 가로질러 만드는 개념 페이지**에 있다.

이 발상에서 시작된 [LLM Wiki](https://github.com/karpathy/llm-wiki) 원전과, 그 위에 제작자(JAEWOO KIM)가 실무에서 적용한 몇가지 테스트와 실무 내용을 토대로 구축했던 10가지 설계 문서를 통합해 **"Claude Code 안에서 도는 개인 지식 베이스"** 를 만들었다.

GitHub: https://github.com/gaebalai/cc-llm-wiki

---

## 1. 핵심 아이디어 — 지식을 한 번 "컴파일" 해 두면

### 3 층 격리

```
L0 Source     사람 입력 · Web Clipper · 외부 SaaS
   ↓
L1 Raw        vault/01_raw/  ← 원전 보존, Read-Only (Hook 차단)
   ↓ Gate ① 청킹·요약·schema 검증
L2 Wiki       vault/02_wiki/
              ├── topics/    공개 가능 지식
              ├── decisions/ ADR (append-only)
              ├── self/      비공개 (어디에도 노출 금지)
              └── digests/   routine 산출
   ↓ Gate ② PII·라이선스 필터
L3 Graph      Neo4j + 고정 Cypher 템플릿 (다중-홉 관계 탐색)
   ↓ Gate ③ top-K 만 컨텍스트 주입
L4 Skills     ingest · lint · compile · graph-sync · ...
   ↓
L5 Surface    Obsidian · CLI · (외부 발신 라인은 의도적 제외)
```

이 구조의 핵심은:

- **단방향 흐름** — raw → wiki → graph. 역방향 쓰기는 모든 층에서 금지
- **사람이 게이트** — ingest 토론·compile 승인이 자동화 폭주를 막는다
- **자료는 손상 없이 영원히 보존** — raw 폴더는 Hook 이 모든 LLM Edit 를 exit 2 로 차단

### Context Engineering 6 기법을 아키텍처에 직접 박았다

| Anthropic Context Engineering 기법 | 본 vault 에서 구현 |
|---|---|
| Quarantine | `vault/01_raw/` Read-Only, Hook 으로 강제 |
| Pruning | `compile` Skill 의 lint 게이트 (ERROR 0 일 때만 승급) |
| Compaction | `_drafts/` → `topics/` 단계적 증류 |
| Just-in-Time Retrieval | `vault/index.md` 2 계층 카탈로그 |
| Structured note-taking | YAML frontmatter (`id`/`type`/`status`/`sources`/`updated_at`/`graph_synced_at`) |
| 가비지 컬렉션 | weekly `lint` routine 10 항목 검사 |

"컨텍스트 윈도가 크다 = 뭐든 욱여넣으면 된다" 가 아니다.
**무엇을 싣지 않을지** 가 답변 품질의 90% 를 결정한다는 것을 아키텍처로 강제했다.

---

## 2. 기술 스택

| 영역 | 기술 |
|---|---|
| **사서** | Claude Code (**8 Skills + 5 Hooks + 1 Command + 5 Routines**, v0.4.4 기준) |
| **저장소** | Obsidian Vault (markdown + frontmatter + wikilink) |
| **상태 보드** | Obsidian Dataview (**10 쿼리**, v0.4.4) |
| **그래프 DB** | Neo4j 5.18.1 + APOC (Docker) |
| **엔티티 추출** | 룰베이스 (`aliases.yaml`, 18 canonical / 60 aliases) + **LangChain `LLMGraphTransformer`** (v0.4.0+ active, SOLVES/USES 의미 관계) |
| **Cypher 템플릿** | `causal_path` / `concept_neighbors` / `orphan_audit` (3 종 고정) |
| **추출 평가** | precision/recall/F1 자동 (`services/graph/eval.py`, v0.4.2+) — gold YAML + CI 통합 |
| **알림** | Slack Incoming Webhook (옵션, dry-run 가능) |
| **버전 관리** | Git (`auto-{ingest,digest,lint,graph}/` 브랜치 + PR 패턴 + Keep a Changelog) |
| **CI** | GitHub Actions (10 항목, v0.3.7+) — JSON·SKILL frontmatter·bash syntax·python compile·vault lint·시크릿 grep·eval |
| **외부 의존** | Python 3.10+, Docker Desktop, Obsidian — 모두 옵션화 |

**의도적으로 외부 의존을 최소화**했다. ingest/query 스크립트는 표준 라이브러리만 쓴다 (urllib + 자체 YAML 파서). neo4j 드라이버는 실제 upsert 때만 필요하고, dry-run 은 의존 0 으로 동작한다.

---

## 3. 18 개 자산이 합쳐서 만드는 시스템 (v0.4.4)

### Skills (8 종)

| Skill | 무엇 | 자동 vs 수동 |
|---|---|---|
| `ingest` | raw 1 건 → `_drafts/` 토론형 변환 (7-step) | 수동 호출 |
| `lint` | 10 항목 정합성 검사 → 리포트 | weekly 자동 |
| `compile` | `_drafts/` → `topics/` 승급 (lint 게이트) | 수동 (`/compile`) |
| `query` | local Grep / graph Cypher 라우터 (자연어→Cypher 자동 생성 금지) | 자동(인사 trigger) / 수동 |
| `graph-sync` | wiki → Neo4j upsert (룰베이스 + LLM 머지, 큐/단일 모드) | hook 적재 + 명시 호출 |
| `morning-brief` | drafts·overdue·신규 raw·lint 미해결 한 화면 요약 | 아침 인사 자동 trigger |
| `evening-reflect` | 세션 종료 시 모순 검사 (decisions 덮어쓰기·CONTRADICTS·self 노출 등) | Stop hook 자동 |
| `daily-digest` | `positioning.md` 기반 5 쿼리 WebSearch → digest 페이지 + Slack 통지 (옵션) | routine만 (v0.4.3 본체) |

### Hooks (5 종)

| Hook | 트리거 | 목적 |
|---|---|---|
| **PreToolUse** | Edit/Write on `01_raw/**` | raw 쓰기 exit 2 차단 |
| **PreToolUse** | Bash `git push.*main\|gh pr merge.*--admin` | main 직커밋 사용자 승인 강제 |
| **PostToolUse** | Edit on `02_wiki/topics/**` | `.claude/queue/graph.txt` 적재 (그래프 동기 큐) |
| **SessionStart** | startup | drafts·신규 raw 카운트 표시 |
| **UserPromptSubmit** | "좋은 아침" 등 인사 정규식 | `morning-brief` 자동 trigger |
| **Stop** | 세션 종료 시 wiki Edit ≥1 | `evening-reflect` 호출, 모순 검출 시 exit 2 |

### Routines (5 active, cron KST)

| Routine | cron | 무엇 |
|---|---|---|
| `wiki-ingest-sweep` | `0 * * * *` | 매시 정각 raw 신규 감지, 알림만 (자동 ingest 금지) |
| `sleep-maintenance` | `0 3 * * *` | `graph-sync --queue` + `orphan_audit` + aliases-candidates 발견 |
| `daily-digest` | `0 7 * * *` | `positioning.md` 5 쿼리 외부 자료 5건 수집 (Slack 옵션) |
| `weekly-lint` | `0 6 * * 0` | 일 06:00 vault 전체 정합성 검사 → `auto-lint/YYYY-WW` PR |
| `weekly-review` | `0 21 * * 0` | 일 21:00 사람 회고 슬롯 (자동 처리 없음, 통계만) |

⚠ routine 5 종은 `.claude/routines/*.md` 에 명세만 있고, 실제 cron 등록은 `/schedule create` 로 사용자 환경마다 1 회.

**쓰기 권한이 있는 Skill 3 종 (`compile`/`evening-reflect`/`daily-digest`) 은 `disable-model-invocation: true`** 로 잠궈, AI 가 사이드 컨텍스트에서 자동 발사하는 경로를 차단했다. Routine 과 명시적 `/skill-name` 만 트리거할 수 있다.

---

## 4. 설치 — Plugin 한 줄

### 가장 쉬운 길

Claude Code 세션 안에서:

```
/plugin marketplace add gaebalai/cc-llm-wiki
/plugin install cc-llm-wiki@claudecode-to-marketplace
/install
```

`/install` 은 7 단계 대화형 installer 를 실행한다:

| Step | 자동화 | 사용자 액션 | 소요 |
|---|---|---|---|
| 1 환경 검사 | git·python3·brew·docker 존재 확인 | 없음 | 5 초 |
| 2 Obsidian | `brew install --cask obsidian` (동의 시) + URI 로 vault 자동 열기 | y/N 한 번 | 2 분 |
| 3 Dataview | `vault/dashboards/status.md` 열기 | Community plugins 에서 enable | 2 분 |
| 5 `.env` | placeholder 복사 + `NEO4J_PASSWORD` 자동 생성 (`secrets.token_urlsafe(16)`) | y/N | 5 초 |
| 4 Docker + Neo4j | Docker.app 기동 polling + `compose up -d` + Browser 준비 대기 60 초 | Docker 권한 최초 1 회 | 1~2 분 |
| 6 Slack | 토큰 발급 절차 안내 + dry-run 검증 | `$EDITOR .env` (history 안전) | 5 분 |
| 7 weekly-review | 운영 명령 요약 + 현재 통계 출력 | 없음 | 10 초 |

총 10~15 분이면 풀스택 환경 완성.

### Step 5 가 Step 4 보다 먼저 실행되는 이유

`NEO4J_PASSWORD` 가 비어 있으면 컨테이너가 의도적으로 기동 실패한다 (안전장치). install.sh 에서 step 순서를 코드로 강제했다.

### 옵션

- `bash scripts/install.sh --check` — 변경 없이 환경만 검사
- `bash scripts/install.sh --step 4` — 특정 단계만 다시
- 전부 **idempotent** — 몇 번 다시 돌려도 안전

---

## 5. 첫 wiki 페이지 만들기 (5 분 데모)

### 자료를 raw 폴더에 떨궈라

Obsidian Web Clipper 또는 직접 markdown 파일을 다음 위치에 저장:

```
vault/01_raw/articles/2026-05-17-my-first-source.md
```

파일명 규칙 (v0.3.6+):
- **wiki** (`02_wiki/`): `<kebab-slug>.md` 영문 소문자·숫자·하이픈만 (wikilink 호환)
- **raw** (`01_raw/`): `YYYY-MM-DD-<slug>.md` 권장. **한글·공백 허용** (Web Clipper 친화). 위반 시 lint WARN-RAW (ERROR 아님)

### Claude Code 에게 ingest 시켜라

```
/ingest vault/01_raw/articles/2026-05-17-my-first-source.md
```

7-step 토론이 시작된다:

```
[Step 1] 파일 읽음. genre=articles, 본문 1200 단어
[Step 2] topics/ 에서 유사 페이지 검색...
         → 0 건 (신규 토픽)
[Step 3] 질문:
         1. 이 글의 핵심 토픽 1~3 개는?
         2. 신규 topic 으로 만들까요, 기존 확장?
         3. 공개 가능한가요, 사적인 내용?
```

사람이 답하면 draft 가 만들어진다. 핵심: **단순 요약이 아니라 "횡단적 지견" 섹션이 들어간다.**

```markdown
## 횡단적 지견
- [[other-topic]] 와의 공통점: ...
- [[another-topic]] 와의 차이: ...
```

다른 topic 들과의 관계를 명시적으로 적는다. 이게 RAG 와 LLM Wiki 의 결정적 차이다.

### lint → compile 로 승급

```
/lint
/compile vault/02_wiki/_drafts/2026-05-17-my-slug.md
```

`lint` 가 ERROR 0 건이면 `compile` 이 `_drafts/` → `topics/` 로 이동시킨다. `git mv` 라 히스토리가 보존된다. `vault/index.md` 에 한 줄 자동 등록.

### (선택) Neo4j 그래프 동기

```
/graph-sync vault/02_wiki/topics/2026-05-17-my-slug.md
```

`aliases.yaml` (**18 canonical / 60 aliases**, v0.3.8+ 한국 AI 시장 entity 보강) 룰베이스로 entity 추출 → Neo4j upsert → `frontmatter.graph_synced_at` 갱신.

룰베이스가 놓치는 의미 관계 (SOLVES / USES) 는 v0.4.0+ 에 추가된 LangChain `LLMGraphTransformer` 가 보강:

```bash
# 룰베이스 + LLM 머지
python3 services/graph/ingest_merge.py vault/02_wiki/topics/<slug>.md --env .env
```

그 다음 사전 정의된 Cypher 템플릿으로 관계 탐색:

```bash
python3 services/graph/query_graph.py causal_path \
  --param company_canonical=Anthropic --env .env
```

→ "Anthropic → Challenge → Solution → Technology" 같은 3-hop 경로가 JSON 으로 반환된다.

**자연어 → Cypher 자동 생성은 절대 안 한다.** 11 번 docs 의 PoC 가 강조한 방어선을 그대로 계승했다. 라우터 Skill 이 질의 의도를 분류해 적절한 고정 템플릿만 호출한다.

---

## 6. 의도적으로 안 한 것 (over-engineering 회피)

11 개 docs 를 다 합치면 비대해질 수 있다. 본 환경은 다음을 **의도적으로 거부**했다:

| 거른 것 | 이유 |
|---|---|
| **외부 공개·다국어 HTML 발행** (Cloudflare Pages 등) | 로컬 전용 정책 — 외부 발신 의도 없음 |
| **자연어 → Cypher LLM 생성** | 비결정적 쿼리는 신뢰도 0. 고정 템플릿이 안전 |
| **morning/evening hook 자동 호출** | Hook 폭주 위험. 명시적 매칭만 |
| **raw 자동 정리** | 사람이 메타-only 1 회 정리는 허용 (SCHEMA §6), 그 외 절대 불변 |

**"무엇을 하지 않을 것인가" 의 목록을 README 에 명시**하는 게 운영 안정성의 핵심이라는 것을 6 phase 거쳐 학습했다.

---

## 7. 헌법으로서의 CLAUDE.md

본 환경의 모든 동작은 [CLAUDE.md](https://github.com/gaebalai/cc-llm-wiki/blob/main/CLAUDE.md) 11 섹션에 박혀 있다:

| § | 내용 |
|---|---|
| 1 Mission | "AI 사서로서 지식을 복리 성장시킨다" |
| 2 Storage Contract | 디렉터리별 RW 권한 매트릭스 |
| **3 Anti-Patterns** | 6 대 금기 (raw 편집·재귀 요약·main 직커밋·자연어 Cypher·self 노출·자동 호출) |
| 4 Skill Index | **8 종 카탈로그** (v0.3.0 완성, v0.4.x 본체 강화) |
| 5 Tool Permission Policy | `allowed-tools` 스코핑 원칙 |
| 6 Frontmatter Spec | id/type/status/locale/sources/updated_at/graph_synced_at |
| 7 Git/PR Convention | `auto-*/` 브랜치 + squash merge |
| 8 Review Discipline | Dataview + Stop hook 모순 검출 |
| 9 Failure Playbook | 5 가지 장애 복구 |
| **10 Graph Layer** | Neo4j 스키마 + 동기 경로 + 자연어 Cypher 금지 |
| **11 MCP & Routine Registry** | **MCP 3 종 (github · slack · neo4j-cypher) + Routine 5 종** 상태 |

**"금지를 먼저"** — Karpathy 원전 + 함정 문서가 강조한 원칙을 §3 에 명시적 우선 배치했다. LLM 은 "해야 할 것" 보다 "해선 안 되는 것" 을 먼저 학습하는 게 동작이 안정적이다.

---

## 8. 보안

시크릿 누출 방지에 신경 썼다.

- `.env.example` 은 placeholder 만. 실제 시크릿은 `.env` 에 (`.gitignore` 자동 무시)
- `install.sh` 가 `.env` 안전성 (`git check-ignore` 통과 여부) 자동 검증
- Slack 토큰은 명령 인자가 아니라 `$EDITOR .env` 권장 (셸 history 노출 차단)
- push 전 시크릿 grep 자동 (PUBLISH.md 절차)

게시 직전 한 번 사고가 있었다. `.env.example` 에 실제 토큰을 적었던 것. **commit 전이라 git 히스토리에는 안 들어갔고**, 사용자가 직접 복원했다. 이 사고 회고를 SCHEMA §6 (raw 메타-only 정리) 신설 계기로 활용했다.

---

## 9. Plugin Marketplace 구조

본 리포는 **단일-plugin 마켓플레이스** 패턴이다.

```
cc-llm-wiki/
├── .claude-plugin/
│   ├── marketplace.json     # 마켓플레이스 정의 (name, owner, plugins[])
│   └── plugin.json          # 플러그인 정의 (name, version, requirements)
├── commands/                # /install 등 슬래시 명령 (자동 발견, v0.3.5+)
├── skills/                  # 8 종 Skill (자동 발견)
├── .claude/
│   └── settings.json        # Hook 정의
└── ...
```

**v0.3.3 학습**: 처음엔 `source = "."` 또는 `{"source":"github",...}` 를 시도했으나 plugin loader 가 인식 못 함. Anthropic 공식 marketplace 35 개 plugin 을 분석해 보니 35/35 가 url 형식 — 그래서 v0.3.3 에서 `{"source":"url","url":"https://github.com/gaebalai/cc-llm-wiki.git"}` 로 정정했다.

**v0.3.4 학습**: plugin.json 의 `commands`/`skills` 필드를 명시적으로 두니 validation 실패. 디렉터리를 plugin root 로 옮기고 (`.claude/` 안이 아니라) 필드 자체를 제거하니 자동 발견 — v0.3.5 에서 안정화.

사용자가 `/plugin marketplace add gaebalai/cc-llm-wiki` 하면 GitHub raw URL 에서 marketplace.json 을 fetch → plugin 목록 표시 → `/plugin install` 로 설치 (실제로는 `git clone` 이 일어남). 그 다음 `/install` 슬래시 명령이 사용자 환경에 자동 노출된다.

---

## 10. Phase 진척 (오픈소스 6 단계 + Plugin 게시)

| Phase | 목표 | 상태 |
|---|---|---|
| P0 | git·골격·헌법 + raw Hook | ✅ |
| P1 | raw → wiki 토론 ingest | ✅ |
| P2 | Context 가드 + lint 10 항목 | ✅ |
| P3 | compile + Dataview | ✅ |
| P4 | weekly-lint routine | ✅ |
| P5 | Neo4j GraphRAG PoC | ✅ |
| P6 | 정착 + 회고 + queue hook | ✅ |
| Plugin v0.1.0 | marketplace 게시 + installer | ✅ |
| Plugin v0.2.0 | PLUGIN_INSTALL 자동 감지 + Hook 머지 | ✅ |
| Plugin v0.3.0 | 8 Skills 완성 + 인사/Stop hook 신설 | ✅ |
| Plugin v0.3.1~v0.3.5 | 실 Neo4j 검증 + plugin install validation 5 회 패치 | ✅ |
| Plugin v0.3.6 | vault 평탄화 + raw 슬러그 한글 허용 | ✅ |
| Plugin v0.3.7 | GitHub Actions CI 10 항목 + Obsidian Excluded files 머지 | ✅ |
| Plugin v0.3.8~v0.3.10 | 외부 vault 절대경로 + env 우선순위 + wikilink stem/short 양쪽 매칭 | ✅ |
| Plugin v0.4.0~v0.4.1 | **LangChain LLMGraphTransformer + 헤더 청크 + 머지 runner** | ✅ |
| Plugin v0.4.2 | **P/R/F1 평가 cycle (rule/llm/consistency)** | ✅ |
| Plugin v0.4.3 | **`daily-digest` 본체 (`positioning.md` + 5 쿼리 자동 설계)** | ✅ |
| Plugin v0.4.4 | **CHANGELOG.md (Keep a Changelog) + Dataview 6→10 쿼리 + contributors 가이드** | ✅ |

각 Phase 마다 **종료 조건이 한 줄로 검증 가능** 하다는 원칙으로 만들었다. 깨지면 즉시 `git restore` 단위로 되돌릴 수 있게.

---

## (후기) v0.3.x 운영 학습 — 정책의 진화

작성 후 실 운영하면서 두 가지 정책 변경:

1. **raw 슬러그 한글 허용** (v0.3.6): 처음엔 raw 도 영문 슬러그 강제 (`YYYY-MM-DD-<kebab>.md`). Web Clipper 로 한글 자료 클립 시 매번 rename 부담 → 정책 완화. raw 는 원문 보존 우선, wiki 만 wikilink 호환 위해 영문 강제.
2. **vault 평탄화** (v0.3.6): 옛 `TARGET_DIR/vault/01_raw/` 구조 → Obsidian Web Clipper 의 vault URI 매칭이 폴더명 기준이라 충돌 발생. `TARGET_DIR` 자체가 vault 인 평탄화 모드 도입. install.sh 가 `.obsidian` 위치로 자동 감지.

이런 게 헌법화 가치 있는 변화 — self/llm-wiki-origins.md 회고 메모에 누적된다.

---

## (후기) v0.4.x 운영 학습 — 그래프 의미 관계 + 외부 자료 수집 + 정착

### 1. LangChain `LLMGraphTransformer` 도입 (v0.4.0~v0.4.1)

룰베이스 (`aliases.yaml` 매칭) 단독으로는 `MENTIONS` / `REFERS_TO` 같은 표면 관계만 뽑힌다. `causal_path` 템플릿 ("회사 → 과제 → 해결책 → 기술" 다중 hop) 을 돌렸더니 0 결과가 나왔다. 11번 docs 의 PoC 가 SOLVES / USES 같은 의미 관계를 추출하라고 한 이유를 그제서야 체감.

LangChain 의 `LLMGraphTransformer` 를 `services/graph/ingest_llm.py` 로 래핑하면서 두 가지 제약을 걸었다:

- `NODE_LABELS` enum 강제 — 6 종 (`Source`·`Person`·`Company`·`Technology`·`Challenge`·`Solution`) 만 허용. LLM 이 자유롭게 라벨을 만들면 그래프가 카오스가 된다.
- `RELATION_TYPES` enum 강제 — 5 종 (`REFERS_TO`·`CONTRADICTS`·`MENTIONS`·`SOLVES`·`USES`) 만.
- 4000 자 초과 시 헤더 (`##`·`###`) 기반 청크 분할 — LLM 의 attention 분산 방지 (v0.4.1).

룰베이스 + LLM 머지는 `services/graph/ingest_merge.py` 가 담당 (--skip-rule / --skip-llm 옵션). 한쪽이 실패해도 다른 한쪽은 살아난다.

### 2. 추출 정확도를 측정 가능하게 (v0.4.2 — P/R/F1)

"LLM 이 추출한 entity 가 맞나?" 를 인상이 아니라 숫자로 평가하기 위해 `services/graph/eval.py` 를 만들었다:

- **gold YAML** (`vault/03_schema/eval-gold/<slug>.yaml`) — 사람이 라벨링한 정답. 룰베이스 결과를 자동 시드로 깔고 검수 보강.
- **3 mode**: `rule` (룰베이스 vs gold) · `llm` (LLM vs gold) · `consistency` (룰베이스 vs LLM, gold 없을 때).
- **메트릭**: precision · recall · F1 — entity 단위 + relation 단위 별도.
- **CI 통합**: `.github/workflows/ci.yml` 의 10번째 항목으로 매 push 마다 자동 평가 (vault 변경 시).

"평가가 없으면 개선이 없다" 는 LLM 운영의 기본 — 작은 PoC 라도 측정 가능하게 만들어 두는 게 가치 있다.

### 3. `daily-digest` 본체 — `positioning.md` 의존 (v0.4.3)

매일 외부 자료 5건을 자동 수집하는 routine 은 v0.3.0 부터 카탈로그에는 있었지만 본체가 비어 있었다. v0.4.3 에서 두 가지 결정으로 완성:

- **`positioning.md` 가 의도 헌법**: 사용자 vault 의 `positioning.md` 에 interests (관심 키워드) / avoid (피할 토픽) / trusted_sources (신뢰 도메인) / tone / frequency_hint 를 사람이 직접 적는다. routine 은 이걸 컨텍스트로 5 검색 쿼리를 자동 설계 (`scripts/daily_digest_runner.py`).
- **결정론적 쿼리 설계, 비결정론적 본문 수집**: 쿼리 설계는 Python script 로 명확하고 재현 가능. 실 WebSearch 호출과 본문 요약만 Claude Code Skill 에 위임.
- 중복 배제: 최근 7일 digest 의 URL 을 grep 해서 같은 자료 두 번 안 보내기.

"AI 가 알아서 흥미로운 거 찾아줘" 는 비결정적이고 운영 불가능. **"사용자 의도를 헌법으로 명시 → 그 헌법을 컨텍스트로 결정론적 쿼리 → 외부 호출만 LLM"** 패턴이 핵심.

### 4. 정착 묶음 (v0.4.4 — CHANGELOG + Dataview + Contributors)

14 개 release 가 누적된 시점에 운영 가시성 강화:

- **`CHANGELOG.md`** (Keep a Changelog 1.1.0) — 그동안 commit 메시지에만 흩어져 있던 변경 이력을 사용자 입장에서 정리.
- **Dataview 보드 6→10 쿼리**: graph 동기 큐 미처리 / 최근 30일 digest 도달 추이 / type 별 분포 / status 누락 검출.
- **GitHub Releases backfill**: v0.3.3~v0.4.3 의 12 개 tag 가 release 누락된 채 누적되었다 (commit + tag 만 했고 `gh release create` 를 빠뜨림). v0.4.4 에서 일괄 backfill + PUBLISH.md §4 에 6 단계 표준 절차 추가 (다음 release 부터 빠뜨리지 않게).
- **README contributors 가이드**: 자료 vs 코드 경계, PR 패턴, 변경 카테고리, 보안 6 항목.

이 묶음으로 **외부 노출 + 운영 안정성** 동시 강화. 새 사용자가 GitHub 와서 변경 이력을 추적 가능하고, 기여자가 PR 패턴을 알 수 있고, 운영자가 매 release 마다 빠뜨리지 않는다.

### 종합 학습 (v0.3.x → v0.4.x)

- **숫자가 없으면 개선 없다** — 룰베이스 vs LLM 의 정확도를 P/R/F1 로 측정하니 어디를 보강할지 명확해졌다. 인상으로 "잘 되는 것 같다" 와는 차원이 다르다.
- **AI 가 알아서 ≠ 결정론** — `daily-digest` 는 사용자가 헌법 (positioning.md) 을 쓰고, 시스템이 결정론적으로 쿼리를 설계하고, LLM 은 외부 호출과 요약만 한다. "흥미로운 거 알아서" 는 비결정적이고 운영 불가능.
- **운영 가시성은 14 release 즈음에 필수** — CHANGELOG / Dataview / 기여 가이드가 없으면 본인도 잊고 사용자도 모른다. v0.4.4 의 정착 묶음을 이 시점에 한 건 늦지도 이르지도 않았다.
- **Release 누락 같은 운영 사고는 표준 절차로 막는다** — PUBLISH.md §4 에 6 단계를 코드 블록으로 박아두면 사람이 다음에 빠뜨릴 확률이 낮아진다.

---

## 11. 가서 써보세요

```
/plugin marketplace add gaebalai/cc-llm-wiki
/plugin install cc-llm-wiki@claudecode-to-marketplace
/install
```

| 자원 | URL |
|---|---|
| GitHub | https://github.com/gaebalai/cc-llm-wiki |
| **Latest Release** | https://github.com/gaebalai/cc-llm-wiki/releases/latest (v0.4.4) |
| 변경 이력 (Keep a Changelog) | https://github.com/gaebalai/cc-llm-wiki/blob/main/CHANGELOG.md |
| 첫 사용자 가이드 (30 분) | https://github.com/gaebalai/cc-llm-wiki/blob/main/QUICKSTART.md |
| 헌법 (CLAUDE.md, 11 섹션) | https://github.com/gaebalai/cc-llm-wiki/blob/main/CLAUDE.md |
| 사서 규율 (SCHEMA.md) | https://github.com/gaebalai/cc-llm-wiki/blob/main/vault/SCHEMA.md |
| 기여 가이드 (README §Contributing) | https://github.com/gaebalai/cc-llm-wiki#기여-contributing |

---

## 12. 한 줄 요약

> raw 는 손대지 마라. 토론하면서 draft 를 빚어라. lint 가 통과한 것만 topics 로 올려라.
> 관계는 wikilink 와 그래프가 자동으로 따라간다.
> **사람의 역할은 무엇을 들이고 무엇을 들이지 않을지 결정하는 것이다.**

지식은 요약이 아니다. **연결**이다.

---

## 부록 — 영감을 준 자료

- [Andrej Karpathy — LLM Wiki](https://github.com/karpathy/llm-wiki) (원전)
- [Anthropic — Context Engineering Guide](https://docs.anthropic.com/) (6 기법)
- [Tiago Forte — Building a Second Brain](https://www.buildingasecondbrain.com/) (BASB 방법론)
- [Microsoft — GraphRAG](https://github.com/microsoft/graphrag) (Neo4j PoC 영감)
- [Obsidian Dataview Plugin](https://blacksmithgu.github.io/obsidian-dataview/) (상태 보드)

본 vault 의 [self/llm-wiki-origins.md](https://github.com/gaebalai/cc-llm-wiki/blob/main/vault/02_wiki/self/llm-wiki-origins.md) 에 11 docs DNA 트리 (어느 결정이 어디서 왔는가) 를 정리해 두었다. 후속 vault 를 만드는 사람에게 도움이 되길.

---

*2026-05-18 (v0.4.4 기준 갱신), Claude Code 와 함께 작성. 본 글 자체는 [vault/02_wiki/](https://github.com/gaebalai/cc-llm-wiki/tree/main/vault/02_wiki) 의 출력물이 아니라 별도 블로그 글입니다 (외부 발신 라인이 없는 환경이라). 최초 작성 v0.1.0, v0.3.x 후기 + v0.4.x 후기 누적 갱신.*
