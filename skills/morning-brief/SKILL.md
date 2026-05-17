---
name: morning-brief
description: 사용자가 아침 인사 ("좋은 아침", "morning", "굿모닝") 또는 "/morning-brief" 로 호출하면 발동. vault 의 현재 상태를 한 화면 요약. drafts 미검토·overdue lint·신규 raw·어제 갱신한 topic 을 stdout 으로 보여준다. 부수효과 없음 (Read 만).
disable-model-invocation: false
allowed-tools:
  - Read
  - Grep
  - Glob
  - Bash(find vault:*)
  - Bash(git log:*)
  - Bash(git diff:*)
  - Bash(rg:*)
  - Bash(date:*)
---

# morning-brief Skill — 아침 상태 요약

## 목적

세션 시작 직후 사용자에게 **"오늘 어디부터 시작할지"** 한 화면 안내.
부수효과 0 (변경·쓰기 없음, Read 만).

## 트리거

- 명시: `/morning-brief`
- Hook (UserPromptSubmit, settings.json): regex `^(좋은\s*아침|morning|굿모닝|gm)` 매칭 시 자동
- SessionStart 직후 사용자가 첫 메시지 보낼 때 (옵션)

## 출력 (한 화면)

```text
☀ morning-brief — YYYY-MM-DD HH:MM KST

📥 미검토 drafts (≥1 일):
  - vault/02_wiki/_drafts/<slug>.md  (3 일 경과)

📂 신규 raw (지난 24 시간):
  - vault/01_raw/articles/2026-XX-XX-<slug>.md

📝 어제 갱신된 topics:
  - [[<slug>]]  ← /lint 권장

🚨 lint 미해결 (vault/02_wiki/_lint/ 최신):
  ERROR 2 / WARN 1  (vault/02_wiki/_lint/2026-XX-XX.md)

💡 추천 액션:
  1. /compile vault/02_wiki/_drafts/<oldest>.md   (가장 오래된 draft 처리)
  2. /ingest vault/01_raw/articles/<newest>.md    (신규 raw)
  3. /lint                                          (ERROR 해소)
```

## 4 단계 절차

### Step 1. 통계 수집 (각 1 줄, Bash 빠른 호출)

```bash
# drafts (1 일 이상 경과)
find vault/02_wiki/_drafts -name '*.md' -mtime +1 2>/dev/null

# 신규 raw (24 시간 이내)
find vault/01_raw -name '*.md' -mtime -1 2>/dev/null

# 어제 갱신 topics
find vault/02_wiki/topics -name '*.md' -mtime -1 2>/dev/null

# 최신 lint 리포트
ls -1t vault/02_wiki/_lint/*.md 2>/dev/null | head -1
```

### Step 2. 최신 lint 리포트 헤더에서 ERROR/WARN 카운트 추출

```bash
grep -E '^\| (ERROR|WARN) ' <latest-lint-report>
```

### Step 3. 추천 액션 결정 (간단한 우선순위)

1. lint ERROR > 0 → "/lint 결과 확인 + 해소" 1순위
2. drafts (3 일 이상) → "/compile" 우선
3. 신규 raw → "/ingest"
4. 모두 0 → "/weekly-review 슬롯 진입 검토"

### Step 4. 출력 + 로그 (선택)

- stdout 으로 위 한 화면 표시
- `vault/log.md` 에는 **append 안 함** (인사 트리거가 너무 자주라 노이즈)

## 절대 금지

- 어떤 파일도 수정·생성하지 않음
- self/ 폴더 본문 노출 (파일명만)
- digest 자동 호출 (별도 routine)
- 자동 lint 실행 (사용자가 추천 액션 보고 직접)

## 사용 예

```
사용자: 좋은 아침
Claude: ☀ morning-brief — 2026-05-18 09:15 KST
        
        📥 drafts 0 건
        📂 신규 raw 1 건 (2026-05-18-langchain-update.md)
        📝 어제 갱신된 topics 0 건
        🚨 lint: 마지막 검사 2026-05-17 (E=1, W=0) — macos*.md 해소됨, 재실행 필요
        
        💡 추천:
        1. /lint  (어제 결과 갱신)
        2. /ingest vault/01_raw/articles/2026-05-18-langchain-update.md
```

## 실패 시

- 모든 통계 명령은 `2>/dev/null` 로 silent — 한 항목 실패해도 다른 출력 계속
- lint 리포트 없으면 그 줄 생략

## 메모

본 Skill 은 "비싼" 작업 안 함 (LLM 호출 없이 정해진 grep + find 만). morning hook 의 자동 호출 비용을 최소화.
