---
name: wiki-ingest-sweep
cron: "0 * * * *"             # 매시 정각
timezone: Asia/Seoul
status: active
phase: P1+
skills: []                      # Skill 자동 호출 없음 — 사용자에게 알림만
mcp: []
env_required: []
---

# Routine: wiki-ingest-sweep

매시 정각에 raw 디렉터리의 신규 파일 (지난 1 시간) 을 감지해 사용자에게 알림.
**자동 ingest 안 함** — CLAUDE.md §3-⑥ "쓰기 Skill 의 모델 자동 호출 금지" 원칙.

## 목적

- Web Clipper 로 사용자가 클립한 raw 파일이 누락되지 않도록 1 시간 단위 확인
- 새 raw 가 있으면 morning-brief Skill 의 입력으로도 활용
- 자동 ingest 는 사람이 명시 호출 (사람 게이트 우선)

## 트리거

- **Cron**: 매시 정각 (`0 * * * *`)
- **수동**: `/wiki-ingest-sweep`
- 부수효과 0 — Read 만, log 1 줄 append (옵션)

## 4-step 절차

### Step 1. 신규 raw 감지

```bash
find $VAULT_DIR/01_raw -name '*.md' -mtime -1h -not -name '.*' 2>/dev/null
```

VAULT_DIR 자동 감지 (install.sh 와 동일 로직):
- flat 모드: `~/<vault>` (TARGET_DIR 자체)
- subdir 모드: `~/<vault>/vault`

### Step 2. ingest 후보 분류

- **신규 raw**: 마지막 sweep 이후 추가됨
- **장르 분포**: articles/speeches/journals/podcasts/books/conversations 별 카운트
- **슬러그 규칙 위반** (한글·공백): SCHEMA §3 권장 형식 안내 (WARN-RAW, ERROR 아님)

### Step 3. 알림 (옵션, 채널별)

```text
📥 wiki-ingest-sweep — YYYY-MM-DD HH:MM KST

신규 raw (지난 1 시간): 2 건
  - 01_raw/articles/2026-05-18-foo.md
  - 01_raw/conversations/2026-05-18-bar.md

추천 액션:
  /ingest 01_raw/articles/2026-05-18-foo.md
```

- **stdout 표시** (기본)
- **macOS notification** (옵션, `osascript -e 'display notification ...'`)
- **Slack** (옵션, `.env` 에 SLACK_WEBHOOK_URL 있을 때)

### Step 4. log (선택)

```
- <ISO8601> | [wiki-ingest-sweep] | routine | 신규 raw N건 | <list>
```

신규 0 건이면 log.md 갱신 안 함 (노이즈 회피).

## 절대 금지

- 자동 ingest (사람 게이트 — CLAUDE.md §3-⑥)
- raw 파일 변경·삭제·이동 (SCHEMA §6 의 사람 메타-only 정리 외)
- 1 시간 이상 오래된 raw 알림 (옛 정보 노이즈)

## 등록

```bash
claude /schedule create \
  --name wiki-ingest-sweep \
  --cron "0 * * * *" \
  --command "/wiki-ingest-sweep"
```

## 활성화 조건

- `$VAULT_DIR/01_raw/` 디렉터리 존재 (install.sh 가 자동 생성)
- 다른 환경 의존 없음 (Read 만)

## 미해결 / 향후

- 신규 raw 감지 시 morning-brief Skill 자동 머지 (현재는 별도)
- 슬러그 권장 형식 자동 rename 옵션 (사람 승인 필요)
