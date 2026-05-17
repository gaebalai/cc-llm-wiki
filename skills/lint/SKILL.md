---
name: lint
description: vault/02_wiki/ 전체를 검사해 SCHEMA.md 위반·orphan·stale·반각공백·끊긴 wikilink·duplicate id 를 검출하고 리포트를 vault/02_wiki/_lint/YYYY-MM-DD.md 에 저장한다. 사용자가 "lint 해줘", "위키 검사해줘" 같은 요청을 하거나 weekly-lint routine이 호출할 때 발동한다.
disable-model-invocation: false
allowed-tools:
  - Read
  - Grep
  - Glob
  - Write
  - Bash(rg:*)
  - Bash(find vault:*)
  - Bash(date:*)
---

# lint Skill — 위키 정합성 검사

## 목적

`vault/SCHEMA.md`의 §5 규칙을 기준으로 `vault/02_wiki/` 전체를 검사하고
리포트 1건을 `vault/02_wiki/_lint/YYYY-MM-DD.md`에 저장한다.

## 입력

- `path?` (옵션): 특정 폴더만 검사 (예: `vault/02_wiki/topics`). 미지정 시 wiki 전체

## 절대 금지

- 검출된 문제를 **자동 수정하지 말 것**. 리포트만 작성 (사람이 결정)
- raw 파일의 **본문**은 읽지 않음 — 파일명 검사만 (SCHEMA §3 명명 규칙)
- self/ 페이지는 frontmatter만 검사. 리포트 본문에 self/ 본문 인용 절대 금지

## 검사 대상

| 폴더 | 무엇을 검사 | 비고 |
|---|---|---|
| `vault/02_wiki/topics/` | frontmatter + 본문(wikilink) | 전체 |
| `vault/02_wiki/decisions/` | frontmatter + 본문(wikilink) | 전체 |
| `vault/02_wiki/digests/` | frontmatter + 본문(wikilink) | 전체 |
| `vault/02_wiki/_drafts/` | frontmatter + 본문(wikilink) | **포함**(승급 전 사전 검출) |
| `vault/02_wiki/self/` | frontmatter만 | 본문 인용 금지 |
| `vault/01_raw/**/*.md` | **파일명 슬러그 규칙만** | 본문 미열람 (원전 보호) |

`path?` 인자로 특정 폴더 한정 가능.

## 검사 항목 (10가지)

| # | 항목 | 심각도 | 검출 방법 |
|---|---|---|---|
| 1 | frontmatter 필수 키 누락(`id`, `type`, `status`, `locale`, `sources`, `updated_at`) | ERROR | YAML 파싱 후 키 존재 확인 |
| 2 | `type` enum 위반 (topic/decision/self/digest 외) | ERROR | enum 매칭 |
| 3 | `status` enum 위반 (draft/reviewed/published 외) | ERROR | enum 매칭 |
| 4 | `sources` 빈 배열 (topic·digest만) | ERROR | 배열 길이 0 |
| 5 | wikilink 끊김 (참조한 slug가 존재하지 않음) | ERROR | `[[...]]` 추출 후 파일 존재 확인 (단, `_drafts/`의 끊긴 링크는 **WARN-DRAFT** 로 강등 — 의도된 미작성일 수 있음) |
| 6 | duplicate `id` (4층 공유 키 충돌) | ERROR | 전체 id 수집 후 중복 검사 |
| 7 | wiki 슬러그 규칙 위반 (`vault/02_wiki/` 하위 `.md`) | ERROR | 파일명 regex `^[a-z0-9-]+\.md$` 검사 (단, `YYYY-MM-DD-` 접두는 권장) |
| 8 | **raw 슬러그 권장 형식** (`vault/01_raw/` 또는 `01_raw/` 하위 `.md`) | **WARN-RAW** | 권장 regex `^[0-9]{4}-[0-9]{2}-[0-9]{2}-[a-z0-9-]+\.md$`. 위반 시 알림만 (원문 보존 우선, Web Clipper 한글 자료 친화 — SCHEMA §3·§5) |
| 9 | orphan 페이지 (어디서도 링크되지 않음) | WARN | 전체 wikilink 그래프 빌드 후 in-degree 0 (단, `_drafts/`·`digests/`·`self/`는 orphan 정상 — 제외) |
| 10 | stale (updated_at이 90일 이상 + sources의 raw가 더 최근) | WARN | mtime 비교 |

## 절차

### Step 1. 스코프 결정
- `path?`가 있으면 그 폴더만, 없으면 위 "검사 대상" 표의 전체 폴더 사용
- `Glob`으로 wiki 대상 `.md` 목록 수집 + `find vault/01_raw -name '*.md'`로 raw 파일명 목록 별도 수집

### Step 2. 메타 추출
- 각 파일에서 frontmatter YAML 블록만 Read (앞 50줄로 충분)
- id·type·status·locale·sources·updated_at·related 수집

### Step 3. 검사 1~7 (ERROR)
- 위 표의 1~7을 순차 검사, 결과를 `errors` 리스트에 누적
- 각 에러 형식: `{file, line, rule, message}`

### Step 4. 검사 8~9 (WARN)
- 전체 wikilink 그래프 빌드 (Grep으로 `\[\[([a-z0-9-]+)\]\]` 추출)
- in-degree 0인 파일 → orphan WARN
- `find vault/01_raw -newer <wiki-file>` 결과가 있으면 stale WARN

### Step 5. 리포트 작성
- 파일: `vault/02_wiki/_lint/YYYY-MM-DD.md`
- 포맷:
  ```markdown
  # Lint Report — YYYY-MM-DD

  - 검사 대상: <개수>
  - ERROR: <개수>
  - WARN: <개수>

  ## ERROR

  | 파일 | rule | 메시지 |
  |---|---|---|
  | vault/02_wiki/topics/foo.md | 5 (broken wikilink) | `[[nonexistent]]` 참조 |
  | ...

  ## WARN

  | 파일 | rule | 메시지 |
  |---|---|---|
  | ...

  ## 권장 조치
  - ERROR는 PR 머지 전 반드시 해결
  - WARN은 사람 판단 (의도된 orphan은 무시 가능)
  ```

### Step 6. 로그
- `vault/log.md`에 1줄 append:
  ```
  - <ISO8601> | [lint] | (cc-session|routine:weekly-lint) | E=<n> W=<n> | _lint/YYYY-MM-DD.md
  ```

## 성공 조건

- 리포트 1건 생성, ERROR/WARN 카운트 명시
- 사용자에게 "ERROR n건, WARN n건. 자세한 내용은 `vault/02_wiki/_lint/YYYY-MM-DD.md`" 라고 안내

## 실패 시

- 파일 1건 파싱 실패 → 그 파일을 ERROR로 기록하고 계속 진행 (전체 중단 금지)
- 권한 부족 → 즉시 중단, 사용자에게 권한 확인 요청

## 사용 예

```
사용자: /lint
Claude: [Step 1] 검사 대상: wiki .md = N, raw .md = M
        [Step 5] 리포트: vault/02_wiki/_lint/YYYY-MM-DD.md
        ERROR n건, WARN n건. 자세한 내용은 리포트 참조.
```

P0 직후에는 모두 0건이지만, P1 이후 draft·raw가 들어오면 SCHEMA §3·§5 위반을 실시간 검출한다.
