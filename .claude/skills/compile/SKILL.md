---
name: compile
description: vault/02_wiki/_drafts/ 의 draft 1건을 사람 승인 후 vault/02_wiki/topics/ 또는 decisions/ 로 승급한다. 승급 전 lint 동등 검사를 수행해 ERROR 가 있으면 거부한다. status 를 draft → reviewed 로 갱신하고 index.md 에 등록하며 log.md 에 기록한다. 사용자가 명시적으로 "/compile <draft_path>" 라고 호출했을 때만 발동한다 (자동 호출 금지).
disable-model-invocation: true
allowed-tools:
  - Read
  - Grep
  - Glob
  - Edit
  - Write
  - Bash(git mv:*)
  - Bash(git status:*)
  - Bash(git diff:*)
  - Bash(rg:*)
  - Bash(date:*)
---

# compile Skill — _drafts/ → topics/·decisions/ 승급

## 목적

ingest Skill이 만든 `_drafts/` 파일 1건을 **사람 승인** 후 정식 wiki 페이지로 승급한다.
status `draft → reviewed`로 갱신하고, `index.md`에 등록하며 `log.md`에 기록한다.

이 Skill은 **자동 호출 금지**(`disable-model-invocation: true`). 오직 사용자가
`/compile <draft_path>` 또는 "이 draft를 컴파일해줘" 같은 명시적 호출만 수용한다.

## 입력

- `draft_path` (필수): 승급할 draft 파일 절대경로 또는 vault 상대경로
  예: `vault/02_wiki/_drafts/2026-05-17-graphrag-poc-with-neo4j.md`

## 절대 금지

- 한 번에 여러 draft 동시 승급 금지 (1회 호출 = 1건)
- draft의 본문을 **재요약·재구성하지 말 것**. ingest에서 사람이 토론으로 확정한 형태 유지
- broken wikilink가 있는데도 강제 승급 금지 (lint 검사 거부)
- `vault/02_wiki/self/` 로 승급 금지 — self/는 ingest 시점부터 사람이 직접 작성하는 폴더, compile 대상 아님
- `vault/index.md`를 LLM이 임의 재구조화 금지 — 신규 항목 1줄만 append

## 7단계 절차

### Step 1. draft 읽기
- `Read`로 draft 전문 읽기 (frontmatter + 본문)
- frontmatter에서 `id`·`type`·`status`·`slug` 추출
- `status != draft` 이면 즉시 중단 ("이미 승급된 페이지 또는 잘못된 상태")

### Step 2. lint 동등 검사 (승급 게이트)
- ERROR 항목 1~8을 draft 단독으로 검사 (lint Skill의 부분 호출 또는 동등 로직)
- 핵심: **항목 5 wikilink 끊김**을 ERROR로 적용 (draft 강등 규칙은 `_drafts/` 내부일 때만 — 승급 직전이므로 격상됨)
- 발견된 ERROR를 사용자에게 표로 보고하고 즉시 중단

### Step 3. 분류 확인 (체크포인트 ①)
사용자에게 질문:
- `type` 이 `topic`인지 `decision`인지 재확인 (대부분 topic, ADR이면 decision)
- 승급 대상 폴더: `topics/` vs `decisions/`
- `decision`이면 ADR 번호 부여 (`decisions/ADR-<n>-<slug>.md`)

### Step 4. status 갱신 + 파일 이동
- frontmatter `status: draft` → `status: reviewed`
- frontmatter `updated_at` → 현재 시각 (ISO8601 +09:00)
- `graph_synced_at`은 그대로 (`null`) — graph-sync Skill이 나중에 채움
- 파일 이동:
  - topic: `vault/02_wiki/_drafts/<slug>.md` → `vault/02_wiki/topics/<slug>.md`
  - decision: `vault/02_wiki/_drafts/<slug>.md` → `vault/02_wiki/decisions/ADR-<n>-<slug>.md`
- **반드시 `git mv` 사용** (히스토리 보존)

### Step 5. index.md 등록 (1줄만 append)
- `Edit`로 `vault/index.md`의 적절한 섹션(`### topics/` 또는 `### decisions/`)에 1줄 추가:
  ```markdown
  - [[<slug>]] — <한 줄 요약, draft 본문 첫 문단의 첫 줄 또는 frontmatter `description` 키>
  ```
- 섹션 미존재 시 새로 만들지 말 것 (index.md 구조 변경은 사람만)
- index.md 통계 카운트도 1 증가

### Step 6. log.md append
- `Edit`로 `vault/log.md` 끝에 1줄 추가:
  ```
  - <ISO8601> | [compile] | cc-session | <slug> draft → reviewed | _drafts/<slug>.md -> topics/<slug>.md
  ```

### Step 7. 후속 안내
- 사용자에게 보고:
  - "승급 완료: `vault/02_wiki/topics/<slug>.md` (status=reviewed)"
  - "다음: status를 `published`로 올리려면 사람이 직접 frontmatter 수정 (publish Skill 호출 전 필요)"
  - "Neo4j 동기는 `graph-sync` Skill 호출 또는 `sleep-maintenance` routine 대기"
- **git commit은 하지 않음** — 사용자가 별도로 검토 후 직접 commit

## 성공 조건

- draft 파일이 `_drafts/`에 더 이상 존재하지 않음 (`git mv` 결과)
- `topics/` 또는 `decisions/`에 새 파일 존재, `status=reviewed`
- index.md에 1줄 추가, log.md에 1줄 추가
- ERROR 0건으로 통과

## 실패 시

- Step 2에서 ERROR 발견 → **승급 거부**, 사용자에게 ERROR 표 출력. draft 그대로 유지
- Step 3 사용자 응답 없음 → 진행 중단, 응답 요청만 출력
- `git mv` 실패 (권한·충돌) → 원상 복구, log.md에 실패 기록 후 중단

## broken wikilink 처리 패턴 (P1~P3 전환기에 자주 발생)

draft에 미작성 `[[other-slug]]`가 있고 즉시 ingest로 해소 못 할 때:
1. **순환 ingest**: 다른 draft의 broken link가 본 draft를 가리키면 두 draft를 함께 컴파일 (1회 호출 = 1건 원칙 예외)
2. **링크 강등**: 본문에서 `[[other-slug]]` → `other-slug` (일반 텍스트)로 강등하고 compile. 나중에 link 복구는 사람이.
3. **placeholder 페이지**: `vault/02_wiki/topics/<other-slug>.md`를 frontmatter만 있는 stub로 미리 생성(`status: draft`로 둠) — lint가 통과되지만 stub임을 본문에 1줄 명시
4. **승급 보류**: ingest 1건 더 실행해서 정상 페이지로 만든 뒤 compile

권장 순서: **4 > 3 > 2 > 1**. 1번은 마지막 수단.

## 사용 예

```
사용자: /compile vault/02_wiki/_drafts/2026-05-17-graphrag-poc-with-neo4j.md
Claude: [Step 1] draft 읽음. status=draft, type=topic, slug=graphrag-poc-with-neo4j
        [Step 2] lint 검사: ERROR 2건 발견
                 - 항목 5: [[entity-disambiguation-strategy]] broken
                 - 항목 5: [[2do-brain-architecture]] broken
                 승급 거부. broken link 처리 방식을 선택하세요 (위 4가지 패턴).
사용자: 4번. entity-disambiguation-strategy를 먼저 ingest 하자.
Claude: [중단] 사용자가 별도 ingest 진행 후 다시 /compile 호출 권장.
```
