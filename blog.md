# Claude Code 로 만드는 "복리로 자라는" 개인 지식 베이스 — cc-llm-wiki 소개

> Karpathy 의 LLM Wiki 원전부터 Neo4j GraphRAG PoC 까지 11 개 설계 문서를 한 환경으로 통합했다.
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

이 발상에서 시작된 [LLM Wiki](https://github.com/karpathy/llm-wiki) 원전과, 그 위에 누적된 10 편의 후속 설계 문서를 통합해
**"Claude Code 안에서 도는 개인 지식 베이스"** 를 만들었다.

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
| **사서** | Claude Code (4 Skills + 3 Hooks + 1 Command + 2 Routines) |
| **저장소** | Obsidian Vault (markdown + frontmatter + wikilink) |
| **상태 보드** | Obsidian Dataview (6 쿼리) |
| **그래프 DB** | Neo4j 5.18.1 + APOC (Docker) |
| **엔티티 추출** | 룰베이스 (aliases.yaml) → LangChain LLMGraphTransformer (옵션, P6+) |
| **Cypher 템플릿** | causal_path / concept_neighbors / orphan_audit (3 종 고정) |
| **알림** | Slack Incoming Webhook (옵션, dry-run 가능) |
| **버전 관리** | Git (auto-{ingest,digest,lint}/ 브랜치 + PR 패턴) |
| **외부 의존** | Python 3.10+, Docker Desktop, Obsidian — 모두 옵션화 |

**의도적으로 외부 의존을 최소화**했다. ingest/query 스크립트는 표준 라이브러리만 쓴다 (urllib + 자체 YAML 파서). neo4j 드라이버는 실제 upsert 때만 필요하고, dry-run 은 의존 0 으로 동작한다.

---

## 3. 9 개 자산이 합쳐서 만드는 시스템

| Skill / Routine | 무엇 | 자동 vs 수동 |
|---|---|---|
| `ingest` | raw 1 건 → `_drafts/` 토론형 변환 (7-step) | 수동 호출 |
| `lint` | 10 항목 정합성 검사 → 리포트 | weekly 자동 |
| `compile` | `_drafts/` → `topics/` 승급 (lint 게이트) | 수동 (`/compile`) |
| `graph-sync` | wiki → Neo4j upsert (큐/단일 모드) | hook 적재 + 명시 호출 |
| **Hook PreToolUse** | raw 쓰기·main 직커밋 차단 | 항상 |
| **Hook PostToolUse** | topics/* 편집 시 `.claude/queue/graph.txt` 적재 | 항상 |
| **Hook SessionStart** | drafts·신규 raw 카운트 표시 | 매 세션 |
| **weekly-lint** | 일 06:00 KST 정합성 검사 + Slack 통지 | cron |
| **weekly-review** | 일 21:00 KST 사람 회고 슬롯 | cron |

**쓰기 권한이 있는 모든 Skill 은 `disable-model-invocation: true`** 로 잠궈, AI 가 사이드 컨텍스트에서 자동 발사하는 경로를 차단했다. Routine 과 명시적 `/skill-name` 만 트리거할 수 있다.

---

## 4. 설치 — Plugin 한 줄

### 가장 쉬운 길

Claude Code 세션 안에서:

```
/plugin marketplace add gaebalai/cc-llm-wiki
/plugin install cc-llm-wiki@claudecode.to-marketplace
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

파일명 규칙: `YYYY-MM-DD-<kebab-slug>.md` (영문 소문자·숫자·하이픈만, 한글 금지).

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

`aliases.yaml` (14 canonical / 47 aliases 초기값) 룰베이스로 entity 추출 → Neo4j upsert → `frontmatter.graph_synced_at` 갱신.

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
| **Kagura MCP** (BM25+Qdrant+Hebbian 3중 인덱스) | 외부 의존 늘리기 전 4 주 자생 검증 후 결정 |
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
| 4 Skill Index | 9 종 카탈로그 |
| 5 Tool Permission Policy | `allowed-tools` 스코핑 원칙 |
| 6 Frontmatter Spec | id/type/status/locale/sources/updated_at/graph_synced_at |
| 7 Git/PR Convention | `auto-*/` 브랜치 + squash merge |
| 8 Review Discipline | Dataview + Stop hook 모순 검출 |
| 9 Failure Playbook | 5 가지 장애 복구 |
| **10 Graph Layer** | Neo4j 스키마 + 동기 경로 + 자연어 Cypher 금지 |
| **11 MCP & Routine Registry** | MCP 4 종 + Routine 5 종 상태 |

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
│   ├── marketplace.json     # 마켓플레이스 정의 (owner, plugins[])
│   └── plugin.json          # 플러그인 정의 (name, commands, skills)
├── .claude/
│   ├── commands/install.md  # /install 슬래시 명령
│   └── skills/              # ingest, lint, compile, graph-sync
└── ...
```

`marketplace.json` 의 `plugins[0].source = "."` 로 자기 자신을 plugin 으로 지정. plugin.json 의 `commands` / `skills` 필드를 디렉터리 string 으로 두면 Claude Code 가 자동으로 .md / SKILL.md 를 발견한다.

사용자가 `/plugin marketplace add gaebalai/cc-llm-wiki` 하면 GitHub raw URL 에서 marketplace.json 을 fetch → plugin 목록 표시 → `/plugin install` 로 설치. 그 다음 `/install` 슬래시 명령이 사용자 환경에 자동 노출된다.

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
| Plugin | marketplace 게시 + installer | ✅ v0.1.0 |

각 Phase 마다 **종료 조건이 한 줄로 검증 가능** 하다는 원칙으로 만들었다. 깨지면 즉시 `git restore` 단위로 되돌릴 수 있게.

---

## 11. 가서 써보세요

```
/plugin marketplace add gaebalai/cc-llm-wiki
/plugin install cc-llm-wiki@claudecode.to-marketplace
/install
```

| 자원 | URL |
|---|---|
| GitHub | https://github.com/gaebalai/cc-llm-wiki |
| Release v0.1.0 | https://github.com/gaebalai/cc-llm-wiki/releases/tag/v0.1.0 |
| 첫 사용자 가이드 (30 분) | https://github.com/gaebalai/cc-llm-wiki/blob/main/QUICKSTART.md |
| 헌법 (CLAUDE.md) | https://github.com/gaebalai/cc-llm-wiki/blob/main/CLAUDE.md |
| 사서 규율 (SCHEMA.md) | https://github.com/gaebalai/cc-llm-wiki/blob/main/vault/SCHEMA.md |

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

*2026-05-18, Claude Code 와 함께 작성. 본 글 자체는 [vault/02_wiki/](https://github.com/gaebalai/cc-llm-wiki/tree/main/vault/02_wiki) 의 출력물이 아니라 별도 블로그 글입니다 (외부 발신 라인이 없는 환경이라).*
