---
name: evening-reflect
description: 세션 종료(Stop hook) 시 자동 호출. 그 세션에서 vault/02_wiki/ 가 변경됐다면 모순 검사 (덮어쓴 결정·CONTRADICTS 신규 등) 수행. 모순 발견 시 exit 2 로 세션 종료 차단 (사람 검토 강제). log.md 에 정정 메모 1 줄 append. 사용자가 명시적으로 "/evening-reflect" 로 호출해도 발동.
disable-model-invocation: true
allowed-tools:
  - Read
  - Grep
  - Glob
  - Edit
  - Bash(git diff:*)
  - Bash(git log:*)
  - Bash(git status:*)
  - Bash(rg:*)
  - Bash(date:*)
---

# evening-reflect Skill — 세션 종료 모순 게이트

## 목적

세션 종료 직전에 **"오늘 한 일이 vault 의 다른 결정과 모순되지 않는지"** 검사.
모순 발견 시 `exit 2` 로 세션 종료 자체를 차단하고 사람에게 결정 요청.

## 트리거

- **Hook (Stop, settings.json)**: 그 세션에서 `vault/02_wiki/` Edit 이 1 건 이상이면 자동
- 명시: `/evening-reflect`
- `disable-model-invocation: true` — Stop hook 또는 명시 호출만, AI 자동 발사 금지

## 절대 금지

- 자동 수정 — 모순 발견 시 **사람에게 알리고 종료 차단**만, 내용 변경 X
- self/ 본문 인용 (frontmatter 만)
- raw 변경 (이미 Hook 이 차단하지만 의도조차 갖지 말 것)
- 새 wiki 페이지 생성 (`compile` Skill 역할)

## 5 단계 절차

### Step 1. 세션 변경 범위 파악

```bash
# 이 세션에서 변경된 wiki 파일 (마지막 commit 이후 차이)
git diff HEAD --name-only | grep '^vault/02_wiki/'
git diff --cached --name-only | grep '^vault/02_wiki/'
git status --short vault/02_wiki/
```

변경 파일 0 건이면 즉시 종료 (모순 없음).

### Step 2. 모순 패턴 검사 (5 가지)

#### 2-1. decisions/ 덮어쓰기
- `git diff HEAD vault/02_wiki/decisions/` 에 `D` 또는 `R` 라인이 있으면 위반 (decisions 는 append-only)

#### 2-2. CONTRADICTS 신규 등장
```bash
git diff HEAD vault/02_wiki/ | grep -E '^\+.*CONTRADICTS|^\+.*\[\[contradicts'
```
새 모순 메모는 "사람 검토 후 결정 필요" 신호

#### 2-3. 같은 id 의 status 역행
- 변경된 파일들의 frontmatter `status` 가 `published → draft` 또는 `reviewed → draft` 로 후퇴했는지 검사

#### 2-4. self/ 페이지가 외부에 인용된 흔적
```bash
git diff HEAD vault/02_wiki/{topics,digests}/ | grep -E '^\+.*\[\[.*self.*\]\]'
```

#### 2-5. topic 의 sources 가 raw 와 mtime 모순
- topic frontmatter `sources` 의 raw 가 변경된 후 topic 본문이 갱신 안 됐을 때 (stale)
- `find vault/01_raw -newer <topic>` 결과 + topic 변경 없음이면 검토 필요

### Step 3. 모순 보고

발견된 항목을 stdout 으로 출력:

```text
🚨 evening-reflect — 모순/검토 항목

[1] decisions/<ADR>.md 가 수정됨 (덮어쓰기 의심)
    - 권장: git restore 또는 새 ADR 작성
[2] topics/<slug>.md 에 CONTRADICTS 신규 추가
    - 권장: 사람이 검토 후 confirm/revert
```

### Step 4. 게이트 결정

- ERROR (decisions 덮어쓰기·status 역행·self 노출) 발견 → `exit 2`
  - Hook 컨텍스트에서 exit 2 = 세션 종료 차단, 사용자가 강제 종료 또는 수정해야 함
- WARN (CONTRADICTS·stale) 만 → exit 0 + 사용자에게 표시만

### Step 5. log.md append

```
- <ISO8601> | [evening-reflect] | cc-session | E=<n> W=<n> | <세션 변경 파일 수>
```

## broken case 처리

- git repo 가 아니면 Step 1 의 git diff 가 실패 → 모순 검사 자체를 skip 하고 안내만
- 너무 큰 diff (>100 파일) → 사람 직접 검토 요청 + skip

## 사용 예

```
[Hook 자동 호출]
🚨 evening-reflect — 변경 12 건 검토

✓ decisions 덮어쓰기 없음
⚠ topics/2026-05-18-foo.md 에 CONTRADICTS [[bar]] 신규 (WARN)
  사람이 검토 후 confirm/revert 권장

WARN 1 / ERROR 0 → 세션 종료 허용
log.md 1 줄 append
```

```
[ERROR 케이스]
🚨 evening-reflect — 변경 5 건 검토
✗ decisions/ADR-001.md 가 수정됨 (덮어쓰기 의심)
  decisions 는 append-only (CLAUDE.md §2). 새 ADR-002 작성 권장
  
ERROR 1 → 세션 종료 차단 (exit 2)
사용자: 수정을 되돌리거나 새 ADR 로 분리 후 세션 재개
```

## 메모

- 본 Skill 은 LLM 추론 호출 없음 (git diff + grep + regex 만)
- "모순" 정의는 보수적 — 의심스러우면 WARN 으로 통과, 확실하면 ERROR 로 차단
- decisions append-only 가 ERROR 인 이유: 사고의 화석화 원칙 (CLAUDE.md §2, vault/02_wiki/decisions 행)
