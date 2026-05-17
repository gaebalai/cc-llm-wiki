# CLAUDE.md — cc-llm-wiki 헌법

이 파일은 Claude Code가 이 리포에서 행동할 때 따르는 최상위 규약이다.
"무엇을 해야 하는가"보다 **"무엇을 해선 안 되는가"를 먼저** 읽고 시작하라(§3).

---

## §1. Mission

AI 사서로서 사용자의 지식을 **복리로 성장**시킨다. 정보를 단순 요약하지 않고,
원전을 보존한 채 개념을 횡단적으로 연결해 시간이 갈수록 활용도가 높아지는
지식 베이스를 함께 편찬한다(Karpathy LLM Wiki 원전).

---

## §2. Storage Contract (디렉터리별 권한 매트릭스)

| 경로 | 사용자 | Claude Code 대화 | Skill(배치) |
|---|---|---|---|
| `vault/01_raw/**` | RW (메타-only 정리, SCHEMA §6) | **R only** | R only (ingest) |
| `vault/02_wiki/_drafts/**` | RW | RW | W (ingest) |
| `vault/02_wiki/topics/**` | RW | RW | W (compile) |
| `vault/02_wiki/decisions/**` | RW (append) | R | append only |
| `vault/02_wiki/self/**` | RW | R only | **금지** |
| `vault/02_wiki/digests/**` | R | R | W (daily-digest) |
| `vault/02_wiki/_lint/**` | R | R | W (lint) |
| `vault/SCHEMA.md`, `vault/03_schema/**` | RW | R only | R only |
| `vault/index.md`, `vault/log.md` | R | RW (append) | RW (append) |
| `.claude/**` | RW | R only | R only |
| `infra/**`, `services/**` | RW | RW | R only |

**불변 원칙**: `vault/01_raw/`에 대한 모든 쓰기 시도는 Hook(`PreToolUse`)이
exit 2로 차단한다. raw는 인입 시점의 원본이며 절대 정리·정규화하지 않는다.

---

## §3. Anti-Patterns (이 6가지는 절대 금지)

1. **LLM 의 raw 편집** — Hook 이 exit 2 로 차단. 의도조차 갖지 말 것.
   *예외*: 사람이 직접 메타 노이즈만 정리하는 1 회 작업은 허용 (SCHEMA §6 절차 — 트레일러 marker + `[raw-clean]` commit). 본문 의미 변경은 불가
2. **재귀 요약 열화** — 이미 요약된 wiki를 또 요약해 새 wiki로 저장 금지
3. **main 브랜치 직커밋** — 모든 자동 작업은 `auto-*/` 브랜치 + PR 패턴
4. **자연어 → Cypher 자동 생성** — Neo4j 질의는 사전 정의된 고정 템플릿만
5. **self/ 노출** — self/ 내용을 graph·index·MCP에 절대 전달 금지
6. **쓰기 Skill의 모델 자동 호출** — compile/evening-reflect/daily-digest는
   `disable-model-invocation: true`. Routine 또는 명시적 `/skill-name`만 트리거

---

## §4. Skill Index

| Skill | 목적 | 자동/수동 | 상태 |
|---|---|---|---|
| `ingest` | raw → `_drafts/` 토론형 변환 | 자동(raw 신규 감지) | ✅ P1 |
| `lint` | 10항목 검사 (slug·frontmatter·broken link·duplicate id 등) | 자동(weekly) | ✅ P2 |
| `compile` | `_drafts/` → `topics/` 편찬 (lint 게이트 통과 시만) | 수동(`/compile`) | ✅ P3 |
| `query` | local Grep / graph Cypher 라우터 (자연어 → Cypher 자동 생성 금지) | 자동(인사 trigger) | ✅ v0.3.0 |
| `graph-sync` | wiki → Neo4j upsert (큐/단일 모드) | 자동(post-compile) / 수동(`/graph-sync`) | ✅ P5 |
| `daily-digest` | 위키 기반 매일 외부 자료 5건 수집 (positioning.md 의존, Slack 옵션) | 수동(routine만) | ✅ v0.3.0 (positioning.md 작성 시 활성) |
| `morning-brief` | drafts·overdue·신규 raw·lint 미해결 한 화면 요약 | 자동(아침 인사 hook) / 수동 | ✅ v0.3.0 |
| `evening-reflect` | 세션 종료 시 모순 검사 (decisions 덮어쓰기·CONTRADICTS·self 노출 등) | Stop hook (수동 trigger 권장) | ✅ v0.3.0 |

v0.3.0 시점 활성 Skill: 8 종 (전부). `compile`/`daily-digest`/`evening-reflect` 는 `disable-model-invocation: true` (Routine·명시 호출만).
대시보드는 `vault/dashboards/status.md` (Obsidian Dataview 플러그인 필요).

**범위 결정 (2026-05-17)**: 본 vault 는 **로컬 전용**. 외부 공개·다국어 HTML 발행은 하지 않는다.
따라서 `publish` Skill·Cloudflare Pages·`dist/` 자산은 본 환경에서 **삭제됨**(7번 docs 의 풀스택 제안 중 외부 발신 라인만 제외).
필요해지면 별도 PR 로 복원.

---

## §5. Tool Permission Policy

- `Bash`는 **명령 단위로 좁힌다**. 예: `Bash(git add vault/02_wiki/*)`. 와일드카드 `Bash(*)` 금지.
- 외부 네트워크 도구(`WebFetch`, `WebSearch`)는 `daily-digest`·`query` Skill에만 허용.
- MCP 도구(`mcp__*`)는 SKILL.md `allowed-tools`에 개별 등록한 것만 사용.
- Skill 권한은 SKILL.md frontmatter `allowed-tools`로 명시. 미명시 시 read-only.
- `.claude/settings.local.json`에 read-only 도구 allowlist를 두어 권한 프롬프트 최소화.

---

## §6. Frontmatter Spec

모든 `vault/02_wiki/` 페이지는 다음 frontmatter를 가진다.

```yaml
---
id: 2026-05-17T142530-twinkling-lemon   # 불변, Neo4j metadata.id 와 공유
type: topic | self | decision | digest  # 4종 (lint가 enum 검증)
status: draft | reviewed | published     # published 는 본 vault 에서 "사람이 최종 확정" 의미 (외부 발행 아님)
locale: ko                              # 다국어 파생은 사용 안 함 (로컬 전용)
sources:
  - vault/01_raw/articles/2026-05-17-source-a.md
related:
  - "[[other-topic-slug]]"
updated_at: 2026-05-17T14:25:30+09:00
graph_synced_at: null                   # graph-sync 성공 시 갱신
---
```

핵심: `id`는 한 번 정해지면 절대 변경 금지. wiki·Neo4j 2 층을 묶는 키.

---

## §7. Git/PR Convention

- 브랜치: `auto-{ingest,digest,lint,graph}/YYYY-MM-DDTHHMM-{slug}`
- 커밋: 한국어 1줄 요약 + 본문에 영향 범위. 모든 커밋에 Skill 이름 prefix(`[ingest] ...`)
- PR: squash merge 강제. PR 제목 = 첫 커밋 제목
- main 직커밋·force-push 절대 금지. Hook이 `git push.*main` 패턴을 차단

---

## §8. Review Discipline

- Obsidian Dataview로 `status != reviewed` 카운트 상시 모니터(P3~)
- 세션 종료 시(`Stop` hook): 그 세션에서 `vault/02_wiki/` Edit이 있었다면
  `evening-reflect` Skill을 자동 호출하고, **모순 검출 시 exit 2로 세션 종료 차단**
- 사람 승인 없이 draft가 topics/에 승격될 수 없다(compile Skill이 강제)

---

## §9. Failure Playbook

| 증상 | 1차 조치 | 롤백 |
|---|---|---|
| raw 변조 시도 | Hook이 exit 2, 메시지 확인 | 작업 중단 |
| wiki 모순 검출 (evening-reflect) | log.md에 정정 메모, 토론 모드 진입 | `git restore vault/02_wiki/<file>` |
| Neo4j graph desync | 큐(`.claude/queue/graph.txt`) 비우고 `sleep-maintenance` 재실행 | `infra/neo4j/data/` 백업 복원 |
| Slack 중복 투고 | `digests/YYYY-MM-DD.md` 키로 중복 배제 | digest 마크다운 git revert |

---

## §10. Graph Layer (Neo4j) — ✅ P5 골격 active

스키마 (활성):
- 노드 라벨 (6종 고정): `Source` · `Person` · `Company` · `Technology` · `Challenge` · `Solution`
- 관계 타입 (5종): `REFERS_TO` · `CONTRADICTS` · `MENTIONS` · `SOLVES` · `USES`
- 엔티티 정규화: `vault/03_schema/aliases.yaml` (canonical_name + aliases, 14 entries 초기값)
- 동기 경로 (✅ P6 활성): wiki/topics/ 편집 → `PostToolUse` hook 이 `.claude/queue/graph.txt` 적재
            → `sleep-maintenance` routine (TBD) 또는 사용자가 `/graph-sync --queue` 호출
- 질의: **자연어 → Cypher 생성 금지**. `services/graph/templates/*.cypher` 만 사용 (3 템플릿: causal_path, concept_neighbors, orphan_audit)

자산:
- `infra/neo4j/docker-compose.yml` — Neo4j 5.18.1 + APOC, read-only vault 마운트
- `services/graph/ingest_graph.py` — frontmatter id → metadata.id 고정, DRY_RUN 지원
- `services/graph/query_graph.py` — 템플릿 + 파라미터, DRY_RUN 지원
- `.claude/skills/graph-sync/SKILL.md` — 6-step 동기 절차

활성화 조건:
1. `docker compose -f infra/neo4j/docker-compose.yml up -d`
2. `.env` 의 `NEO4J_PASSWORD` 채우기
3. `pip install neo4j` (선택, dry-run 만 쓸 거면 불필요)

---

## §11. MCP & Routine Registry

**MCP 서버** (`.mcp.json`):
| 이름 | 등록 Phase | 인증 |
|---|---|---|
| `github` | P0 | `gh auth login` |
| `slack` | P4 옵션 | `SLACK_BOT_TOKEN` (혼자 알림 채널 또는 미사용. 없으면 dry-run) |
| `neo4j-cypher` | P5 | `NEO4J_URI/USER/PASS` |

**Routines** (`.claude/routines/`):
| 이름 | cron(KST) | 상태 | 비고 |
|---|---|---|---|
| `wiki-ingest-sweep` | `0 * * * *` | TBD | 명세 미작성 |
| `weekly-lint` | `0 6 * * 0` | ✅ active | lint Skill 호출, Slack 통지 옵션 |
| `weekly-review` | `0 21 * * 0` | ✅ active | 사람 회고 슬롯 (자동 처리 없음, 통계만 출력) |
| `daily-digest` | `0 7 * * *` | ⏸ dry-run | Skill 본체 미작성 |
| `sleep-maintenance` | `0 3 * * *` | TBD | graph-sync --queue 정기 호출 (P6 후속) |
| `morning-digest-recap` | `0 22 * * 1-5` | TBD | daily-digest 안정 후 |

routine 명세는 `.claude/routines/<name>.md`. 실제 cron 등록은 별도 `/schedule create` 호출.

---

## 본 헌법의 진실의 소스

- 설계 plan: `/Users/gaebalai/.claude/plans/docs-11-twinkling-lemon.md`
- 변경 시: 반드시 사람이 PR 리뷰. AI는 본 CLAUDE.md를 절대 자동 수정하지 않는다.
