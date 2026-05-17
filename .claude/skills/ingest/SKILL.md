---
name: ingest
description: vault/01_raw/ 의 새 파일 1건을 읽어 vault/02_wiki/_drafts/ 에 토론형 wiki draft 1개를 생성한다. raw는 절대 수정하지 않으며, 결과는 사람이 검토할 수 있도록 draft 상태로만 남긴다. raw에 새 파일이 추가됐거나 사용자가 명시적으로 "이거 ingest 해줘" 같은 요청을 한 경우에 발동한다.
disable-model-invocation: false
allowed-tools:
  - Read
  - Grep
  - Glob
  - Write
  - Bash(git status:*)
  - Bash(git log:*)
---

# ingest Skill — raw → _drafts/ 토론형 변환

## 목적

`vault/01_raw/<genre>/YYYY-MM-DD-<slug>.md` 1건을 읽어 `vault/02_wiki/_drafts/`에
**토론형 draft** 1건을 생성한다. 자동 진행이 아니라 **사람과 토론**해서 진행하는 것이 핵심.

## 입력

- `target_path`: ingest할 raw 파일 절대경로 또는 vault 상대경로
- 미지정 시: `vault/01_raw/`에서 가장 최근 추가된 파일(또는 `_drafts/`에 짝이 없는 raw)을 후보로 제시

## 절대 금지

- `vault/01_raw/**` 어떤 파일도 수정·삭제·이동 금지 (Hook이 차단하지만 의도조차 갖지 말 것)
- `vault/02_wiki/topics/`로 바로 쓰지 말 것. **반드시 `_drafts/`에만 쓴다**
- 자동으로 여러 raw를 한 번에 처리하지 말 것 (1회 호출 = 1건)
- index.md·log.md·SCHEMA.md 자동 수정 금지 (compile Skill의 역할)

## 7단계 절차 (토론형)

### Step 1. 대상 파악
- `target_path`를 Read로 전문 읽기 (frontmatter + 본문)
- 파일 경로에서 `<genre>` 추출 (articles/speeches/journals/podcasts/books/conversations 중 1)

### Step 2. 유사 wiki 검색
- Grep으로 `vault/02_wiki/topics/`에서 본문의 핵심 키워드 3~5개로 기존 페이지 검색
- 결과를 사용자에게 보여주고 **신규 토픽인지, 기존 토픽 확장인지 확인 요청**

### Step 3. 토론 체크포인트 ①
다음 항목을 사용자에게 질문(`AskUserQuestion` 또는 명시적 텍스트 질문):
- 이 raw의 **핵심 토픽 1~3개**는 무엇인가
- 기존 topic 페이지를 확장할 것인가, 신규 토픽을 만들 것인가
- 공개 가능한 토픽인가, `self/`로 분류할 사적 내용인가

**사용자 응답 없이 다음 단계 진행 금지.**

### Step 4. draft 골격 작성
- 파일명: `vault/02_wiki/_drafts/YYYY-MM-DD-<slug>.md` (slug는 사용자가 승인한 것)
- frontmatter 채우기:
  ```yaml
  ---
  id: <ISO8601-timestamp>-<slug>          # 현재 시각 기준 생성
  type: topic                              # 또는 self (사용자 확인 결과)
  status: draft
  locale: ko
  sources:
    - <target_path를 vault 상대경로로>
  related: []                              # Step 2에서 발견한 기존 페이지가 있으면 채움
  updated_at: <현재 ISO8601 with +09:00>
  graph_synced_at: null
  ---
  ```

### Step 5. 본문 작성 (토론형)
- 단순 요약 금지 — **횡단적 지견** 섹션을 만들어 다른 페이지와의 연결을 명시
- 본문 구조:
  ```markdown
  ## 핵심 주장
  (3~5줄, raw의 핵심)

  ## 횡단적 지견
  - [[related-slug-1]]과의 공통점: ...
  - [[related-slug-2]]와의 차이: ...

  ## 인용
  > raw에서 발췌 (페이지/타임코드/줄 번호 보존)

  ## 미해결 질문
  - (사용자와 다음 ingest에서 다룰 토픽)
  ```

### Step 6. 토론 체크포인트 ②
- draft 본문을 사용자에게 보여주고 다음을 확인:
  - frontmatter 키 빠짐 없음?
  - related 링크가 실제 존재하는 페이지를 가리키는가?
  - self/ 분류로 옮겨야 할 내용이 섞이지 않았는가?
- 수정 요청이 있으면 반영 후 다시 보여주기 (Step 6 반복)

### Step 7. 쓰기 + 로그
- 승인 후에만 `Write`로 `_drafts/` 파일 생성
- `vault/log.md`에 다음 1줄 append:
  ```
  - <ISO8601> | [ingest] | cc-session | draft 생성 | <target_path> -> <draft_path>
  ```
- 사용자에게 다음 단계 안내:
  - "draft가 `<draft_path>`에 있습니다. P3 이후 `/compile`로 topics/에 승격하거나, Obsidian에서 직접 편집하세요."

## 성공 조건

- raw 1건당 draft 1건 생성, raw 파일은 변경되지 않음
- frontmatter가 SCHEMA.md를 100% 준수
- log.md에 1줄 추가

## 실패 시

- Step 3·6 응답 없음 → 진행 중단, 사용자에게 응답 요청 메시지만 남김
- raw 읽기 실패 → 에러 메시지, draft 생성 안 함
- 동일 `id`가 이미 존재 → 새 timestamp로 재생성 시도, 3회 실패 시 중단

## 사용 예

```
사용자: vault/01_raw/articles/2026-05-17-context-engineering.md 를 ingest 해줘
Claude: [Step 1] 파일 읽음. genre=articles, 본문 1200단어.
        [Step 2] topics/에서 유사 페이지 검색 중...
                 → context-rot, llm-wiki 2개 발견
        [Step 3] 질문:
                 1. 이 글의 핵심 토픽은 'context engineering 6기법'으로 보입니다. 맞나요?
                 2. 신규 topic으로 만들까요, 아니면 [[context-rot]]을 확장할까요?
                 3. 공개 가능한가요?
사용자: 1. 맞음, 2. 신규, 3. 공개
Claude: [Step 4-7] draft 작성 후 보여주기 → 승인 → 쓰기
```
