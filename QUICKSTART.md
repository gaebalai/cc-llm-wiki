# QUICKSTART — 첫 사용자 가이드

이 문서는 **cc-llm-wiki 를 처음 쓰는 사람**이 30분 안에 설치부터 첫 wiki 페이지 생성까지 끝낼 수 있게 안내합니다.

대상 OS: **macOS** (Linux 도 대부분 동작, 일부 명령만 조정 필요).

---

## 0. 이게 뭐냐

**Claude Code 안에서 도는 개인 지식 베이스**입니다.

- Obsidian vault 안의 markdown 파일들을 **3 층**으로 격리: `01_raw/`(원전 보존) → `02_wiki/`(LLM 편찬) → 스키마
- Claude Code가 **사서 역할**: ingest(자료 가져오기) / compile(편찬) / lint(검사) / graph-sync(Neo4j 동기)
- **로컬 전용** — 외부 공개·발신 없음 (필요해지면 별도 PR 로 복원)
- 자료가 쌓일수록 **복리로 성장**하는 지식 그래프

---

## 1. 설치 (3 가지 방법, 위에서 아래로 쉬운 순)

### 방법 ① Claude Code Plugin (v0.2.0+ 권장)

새 작업 디렉터리에서:

```bash
mkdir ~/my-knowledge-base && cd ~/my-knowledge-base
claude
```

세션 안에서:
```
/plugin marketplace add gaebalai/cc-llm-wiki
/plugin install cc-llm-wiki@claudecode-to-marketplace
/install
```

`install.sh` 가 PLUGIN_INSTALL 자동 감지 → 템플릿을 `~/my-knowledge-base/` 로 복사 + 사용자 `.claude/settings.json` 에 Hook 안전 머지 + 7-단계 대화형 셋업.

### 방법 ② Git clone + 직접 설치

```bash
git clone https://github.com/gaebalai/cc-llm-wiki.git ~/cc-llm-wiki
cd ~/cc-llm-wiki
bash scripts/install.sh
```

→ 7-단계 셋업이 `~/cc-llm-wiki/` 안에서 모두 동작.

### 방법 ③ 환경만 검사 (변경 없음)

```bash
bash scripts/install.sh --check
```

### 방법 ④ 특정 TARGET_DIR 강제

```bash
bash scripts/install.sh --target-dir ~/another-vault
```

---

## 2. `/install` 7+1 단계 흐름

| Step | 자동화 | 사용자 액션 | 소요 |
|---|---|---|---|
| **1** 환경 검사 | git/python3/brew/docker 존재 확인 + PLUGIN_INSTALL 감지 시 템플릿 복사 (`vault`·`infra`·`services`·`scripts`·`.claude/`·`CLAUDE.md` 등) | 없음 | 5~10초 |
| **2** Obsidian | `brew install --cask obsidian` (동의 시) | y/N 한 번 + Obsidian 첫 실행 시 권한 부여 | 2분 |
| **3** Dataview | `vault/dashboards/status.md` 자동 열기 | Obsidian 내부에서 `Settings → Community plugins → Browse → Dataview → Enable` | 2분 |
| **5** `.env` 생성 | `cp .env.example .env` + `NEO4J_PASSWORD` 자동 생성 | y/N 한 번 | 5초 |
| **5.5** Hook 머지 (PLUGIN_INSTALL only) | 사용자 `.claude/settings.json` 에 plugin hooks 4 종 안전 머지 (기존 hook 보존) | 없음 | 1초 |
| **4** Docker + Neo4j | Docker Desktop 기동 polling + `docker compose up -d` | Docker.app 최초 1회 권한 부여 | 1~2분 |
| **6** Slack 토큰 | 발급 안내 + dry-run 검증 | (선택) `$EDITOR .env`로 `SLACK_WEBHOOK_URL=...` 채우기 | 5분 (Slack App 만들기) |
| **7** weekly-review | 운영 명령 요약 + 현재 통계 출력 | 없음 | 10초 |

Step 5 가 Step 4 보다 먼저 실행됩니다 (`NEO4J_PASSWORD` 가 compose 의 prerequisite).
Step 5.5 는 PLUGIN_INSTALL 일 때만 발동 (git clone 환경에서는 자동 skip).

### 도중에 실패하면

```bash
bash scripts/install.sh --step 4   # Docker 단계만 다시
```

7 단계는 모두 **idempotent** (몇 번 다시 돌려도 안전).

---

## 3. 첫 wiki 페이지 만들기 (Claude Code 세션 안에서)

### 3-1. 자료 한 건을 raw 폴더에 넣기

Obsidian Web Clipper 또는 직접 markdown 파일을 만들어 다음 위치에 저장:

**flat 모드** (v0.3.6+ 기본, Obsidian 친화):
```
01_raw/articles/2026-05-17-<my-slug>.md
```

**subdir 모드** (옛 컨벤션 또는 dev repo):
```
vault/01_raw/articles/2026-05-17-<my-slug>.md
```

파일명 규칙 (SCHEMA §3, v0.3.6+):
- **wiki**: `<kebab-slug>.md` 강제 — 영문 소문자·숫자·하이픈만 (wikilink 호환성)
- **raw**: `YYYY-MM-DD-<slug>.md` 권장. **한글·공백 허용** (Web Clipper 친화). 위반 시 lint WARN-RAW (ERROR 아님)

장르 폴더는 6 가지: `articles` · `speeches` · `journals` · `podcasts` · `books` · `conversations`.

### 3-2. ingest — raw → draft

Claude Code 세션에서 (작업 디렉터리에서 `claude` 실행 후):

```
/ingest 01_raw/articles/2026-05-17-<my-slug>.md
```
(또는 한글 파일명도 OK: `/ingest 01_raw/articles/클립한자료.md`)

`ingest` Skill 이 7 단계 토론을 시작합니다:

1. 파일 읽기
2. 기존 wiki 에서 유사 페이지 grep
3. **사용자 질문 ①**: 핵심 토픽? 신규 vs 기존? 공개 가능?
4. draft frontmatter 작성
5. 본문 작성 (횡단적 지견 + 인용 + 미해결 질문 포함)
6. **사용자 질문 ②**: draft 검토 → OK / 수정 요청
7. 승인 후 `vault/02_wiki/_drafts/<slug>.md` 에 저장

⚠ raw 파일은 절대 수정되지 않습니다 (Hook 차단).

### 3-3. lint — 정합성 검사

```
/lint
```

10 항목 검사:
- frontmatter 필수 키, enum, sources
- 끊긴 wikilink (단, `_drafts/` 내부는 WARN-DRAFT 강등)
- duplicate id, 슬러그 규칙, orphan, stale

결과는 `vault/02_wiki/_lint/YYYY-MM-DD.md` 에 저장.

### 3-4. compile — draft → topics 승급

```
/compile vault/02_wiki/_drafts/2026-05-17-<my-slug>.md
```

- lint ERROR 1 건이라도 있으면 **승급 거부**
- `status: draft → reviewed` 갱신
- `git mv` 로 `topics/` 로 이동 (히스토리 보존)
- `vault/index.md` 에 1 줄 자동 등록

### 3-5. (선택) Neo4j 그래프 동기

Docker Neo4j 가 떠 있고 `pip install neo4j` 끝났다면:

```
/graph-sync vault/02_wiki/topics/2026-05-17-<my-slug>.md
```

→ entity 추출 (aliases.yaml 룰베이스) + Neo4j 노드/엣지 upsert + frontmatter `graph_synced_at` 갱신.

자동 큐 모드 (`PostToolUse` hook 이 적재):
```
/graph-sync --queue
```

---

## 4. 자주 쓰는 명령 cheat sheet

| 명령 | 무엇 |
|---|---|
| `/install` | 7-단계 환경 셋업 (처음 한 번만) |
| `/install --check` | 환경만 검사 (변경 없음) |
| `/install --step 4` | 특정 단계만 |
| `/ingest <raw_path>` | raw → draft 토론형 |
| `/lint` | 전체 vault 정합성 검사 |
| `/lint <path>` | 특정 폴더만 검사 |
| `/compile <draft_path>` | draft → topics 승급 (lint 게이트) |
| `/graph-sync <topic_path>` | 단일 topic 그래프 동기 |
| `/graph-sync --queue` | hook 큐 일괄 동기 |

### Bash 명령 (Claude Code 밖)

```bash
# Slack 알림 수동 (dry-run)
python3 scripts/post_slack.py --title "test" --body "hi" --env .env

# Neo4j 그래프 통계
python3 services/graph/query_graph.py orphan_audit --env .env

# Neo4j 인과 경로 검색 (Anthropic → Challenge → Solution → Technology)
python3 services/graph/query_graph.py causal_path --param company_canonical=Anthropic --env .env

# 컨테이너 로그
docker compose -f infra/neo4j/docker-compose.yml logs neo4j --tail 30
docker compose -f infra/neo4j/docker-compose.yml down  # 종료
```

---

## 5. 일주일 운영 사이클

| 시점 | 일 | 활성 routine |
|---|---|---|
| 매일 (수동) | raw 1~3 건 ingest → draft 검토 → compile | — |
| 매시 (자동, 활성화 시) | `wiki-ingest-sweep` — raw 신규 감지 | — |
| 일 06:00 KST | `weekly-lint` 자동 실행 → 리포트 PR | ✅ active |
| 일 21:00 KST | `weekly-review` 슬롯 알림 | ✅ active |
| (매일 07:00, dry-run) | `daily-digest` | ⏸ Skill 본체 미작성 |

회고 시: `vault/02_wiki/self/llm-wiki-origins.md` 의 "회고 메모" 섹션에 timestamp 와 함께 1~3 줄 append.

---

## 6. Obsidian 사이드 설정 권장

설치 후 한 번:

| 설정 | 위치 | 값 |
|---|---|---|
| Vault 열기 | Open folder as vault | `<repo>/vault` |
| Excluded files | Settings → Files & Links | `plans/`, `.claude/queue/`, `docs/` |
| Strict line breaks | Settings → Editor | **ON** (markdown 호환) |
| Dataview | Community plugins → Browse | Install + Enable |
| Graph view | Sidebar | 보기 만 활성화 (편집 X) |

---

## 7. 문제 해결 (FAQ)

### "Hook 이 raw 편집을 차단했습니다" 에러
의도된 동작입니다 (CLAUDE.md §3-①). raw 는 절대 수정 안 됩니다.
정리가 필요하면 **새 wiki 페이지에 인용 + 보완 메모** 패턴으로.

### `/compile` 이 ERROR 로 거부함
draft 의 `[[some-slug]]` 가 가리키는 파일이 `_drafts/` 안에만 있을 수 있습니다.
- 옵션 A: 그 페이지를 별도 ingest 해서 topics/ 로 미리 승급
- 옵션 B: `[[some-slug]]` → `some-slug` (일반 텍스트) 강등
- 옵션 C: stub topic 페이지 (frontmatter 만) 먼저 만들기
- 옵션 D: 세 draft 클러스터 compile (예외 패턴 — compile SKILL §broken wikilink 처리)

### Neo4j 가 기동 안 됨
```bash
docker compose -f infra/neo4j/docker-compose.yml logs neo4j --tail 50
```
- `NEO4J_PASSWORD 가 비어 있음` → `.env` 채우기
- `bind: address already in use` → 다른 Neo4j 인스턴스 켜져 있음 (port 7474/7687 충돌)

### Slack 통지가 안 옴
- `.env` 의 `SLACK_WEBHOOK_URL` 확인. 없으면 자동 dry-run (stdout 만)
- `DRY_RUN=0` 인지 확인
- `python3 scripts/post_slack.py --title test --body hi --env .env` 직접 호출 결과 검사

### Dataview 보드가 비어 있음
- Obsidian 안에서 Dataview 플러그인 **enable** 했는지
- `vault/dashboards/status.md` 를 reading view (Cmd+E) 로 열어야 쿼리 실행됨

### plugin 업데이트 받기
```
/plugin update cc-llm-wiki@claudecode-to-marketplace
```

---

## 8. 더 깊이 알고 싶다면

| 문서 | 내용 |
|---|---|
| [CLAUDE.md](CLAUDE.md) | 11 섹션 헌법. 권한 매트릭스·금기·Skill 카탈로그·MCP·Routine 레지스트리 |
| [vault/SCHEMA.md](vault/SCHEMA.md) | 사서 규율 (page type 4 종, frontmatter, lint 10 규칙) |
| [vault/02_wiki/self/llm-wiki-origins.md](vault/02_wiki/self/llm-wiki-origins.md) | 11 docs DNA 트리: 어느 결정이 Karpathy 원전, 어느 게 후속 확장 |
| [docs/](docs/) | 11 개 설계 문서 원본 (gitignore, 로컬 참조용) |
| [docs-internal/PUBLISH.md](docs-internal/PUBLISH.md) | (저자용) plugin 게시 절차 |
| `~/.claude/plans/docs-11-twinkling-lemon.md` | 풀스택 통합 설계 plan (Phase 0~6 로드맵) |

---

## 9. 한 줄 요약

> raw 는 손대지 마라. 토론하면서 draft 를 빚어라. lint 가 통과한 것만 topics 로 올려라.
> 관계는 wikilink 와 그래프가 자동으로 따라간다.
> 사람의 역할은 **무엇을 들이고 무엇을 들이지 않을지** 결정하는 것이다.
