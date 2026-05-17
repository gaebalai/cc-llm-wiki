---
name: daily-digest
description: 매일 외부 자료 5 건을 검색·요약해 vault/02_wiki/digests/YYYY-MM-DD.md 로 저장하고 Slack 통지(선택). vault/positioning.md (사용자 관심사·금기) + 기존 topics 를 컨텍스트로 사용. 수동 호출은 "/daily-digest" 또는 daily-digest routine (매일 07:00 KST) 만. 자동 발사 금지.
disable-model-invocation: true
allowed-tools:
  - Read
  - Grep
  - Glob
  - Write
  - WebSearch
  - WebFetch
  - Edit
  - Bash(git checkout -b auto-digest:*)
  - Bash(git add vault/02_wiki/digests:*)
  - Bash(git commit:*)
  - Bash(git push:*)
  - Bash(gh pr create:*)
  - Bash(python3 scripts/post_slack.py:*)
  - Bash(date:*)
---

# daily-digest Skill — 매일 5 건 외부 자료 수집

## 목적

사용자의 `positioning.md` (관심사·금기 토픽·신뢰 출처) + `vault/02_wiki/topics/` 카탈로그를 컨텍스트로,
**외부 자료 5 건**을 골라 `vault/02_wiki/digests/YYYY-MM-DD.md` 에 저장.
Slack Webhook 이 있으면 요약 통지.

## 전제 조건 (활성화 체크리스트)

| 항목 | 위치 | 없으면 |
|---|---|---|
| `vault/positioning.md` | 사용자가 직접 작성 | Skill 즉시 abort + 템플릿 안내 |
| `.env` 의 `SLACK_WEBHOOK_URL` | 사용자 채움 | Slack dry-run (stdout) |
| `gh` CLI 인증 | `gh auth login` | PR 자동 생성 skip, 로컬 commit 만 |

## 트리거

- **Routine (`/schedule create` 등록 후)**: 매일 07:00 KST
- 명시: `/daily-digest`
- **`disable-model-invocation: true`** — AI 자동 발사 금지, Routine + 명시 호출만

## 절대 금지

- `positioning.md` 무시하고 임의 토픽 선택
- 같은 URL 7 일 내 중복 (digest sources grep 검사 필수)
- self/ 페이지 본문을 외부 검색에 포함
- raw 자동 정리 (digest 는 새 raw 가 아니라 새 digest 페이지로 저장)
- main 직커밋 (auto-digest/ 브랜치 + PR 필수)

## 7 단계 절차

### Step 1. 전제 조건 검증
```bash
[ -f vault/positioning.md ] || abort "positioning.md 작성 필요. 템플릿: skills/daily-digest/positioning.template.md"
```
abort 시 사용자에게 템플릿 경로 안내.

### Step 2. positioning + topics 카탈로그 로드
- `positioning.md` 의 `interests` · `avoid` · `trusted_sources` 추출
- `vault/index.md` 의 topics 섹션 읽기 (JIT, 전수 로드 X)

### Step 3. 검색 쿼리 자동 설계 (3~5 쿼리)
- `interests` 키워드 조합 + 최근 기간 한정 (after:2026-05-15 등)
- `trusted_sources` site 한정 옵션
- `avoid` 토픽 부정형 (-...)

### Step 4. WebSearch + WebFetch (각 쿼리당 3~5 결과)

```python
# 의사 코드
candidates = []
for q in queries:
    results = WebSearch(q)
    for r in results[:5]:
        if r.url not in seen_urls_last_7days:
            body = WebFetch(r.url, prompt="핵심 1 단락 요약 + 근거 인용 2 줄")
            candidates.append({title, url, summary, source_domain})
```

`seen_urls_last_7days`: `vault/02_wiki/digests/` 의 최근 7 파일에서 `sources` grep.

### Step 5. 상위 5 건 선정 (사람이 검토하기 좋게)
- positioning 의 interests 와 매칭 강도
- trusted_sources 가중치
- 새 토픽 우선 (기존 topics 와 키워드 겹침이 낮은 것)

### Step 6. digest 페이지 생성

`vault/02_wiki/digests/YYYY-MM-DD.md`:

```markdown
---
id: 2026-05-18T070000-daily-digest
type: digest
status: reviewed
locale: ko
sources:
  - <URL 1>
  - <URL 2>
  - <URL 3>
  - <URL 4>
  - <URL 5>
related: []
updated_at: 2026-05-18T07:00:00+09:00
graph_synced_at: null
---

# Daily Digest — 2026-05-18

## 1. <제목 1>
- 출처: <도메인>
- 요약: <1~2 줄>
- 근거: > <인용 1>
- 관련: [[<기존 topic 이 있으면>]]

## 2~5. (반복)

## 메타
- 검색 쿼리: <쿼리 목록>
- positioning 매칭 강도: <건별>
```

### Step 7. 브랜치 + PR + Slack

```bash
git checkout -b auto-digest/$(date +%Y-%m-%d)
git add vault/02_wiki/digests/$(date +%Y-%m-%d).md
git commit -m "[digest] $(date +%Y-%m-%d) — N 건"
git push origin HEAD
gh pr create --title "[digest] $(date +%Y-%m-%d)" --body "$(head -20 vault/02_wiki/digests/$(date +%Y-%m-%d).md)"

# Slack (Webhook 있으면)
python3 scripts/post_slack.py \
  --title "[daily-digest] $(date +%Y-%m-%d)" \
  --body-file vault/02_wiki/digests/$(date +%Y-%m-%d).md \
  --env .env
```

## 실패 시

- `positioning.md` 없음 → 즉시 abort, 템플릿 경로 안내
- WebSearch 0 결과 → "오늘은 새 자료 없음" digest 1 줄만 작성
- Slack 호출 실패 → stderr 만, PR 은 그대로 머지 가능
- PR 생성 실패 → 브랜치만 push, 사용자가 수동 PR

## v0.4.0+ dry-run 골격

`positioning.md` 작성 직후 정책 시뮬레이션:

```bash
cp skills/daily-digest/positioning.template.md ~/my-knowledge-base/positioning.md
$EDITOR ~/my-knowledge-base/positioning.md

DRY_RUN=1 /daily-digest   # 쿼리 설계만, 외부 호출 없음
DRY_RUN=0 /daily-digest   # 실 WebSearch + digest 생성
```

활성 체크리스트:
- [ ] `vault/positioning.md` 작성
- [ ] `.env` 의 `SLACK_WEBHOOK_URL` (선택, 통지용)
- [ ] `gh auth login` (PR 자동 생성)
- [ ] weekly-review 첫 회고 (positioning 검증)
- [ ] `/schedule create` 로 실 cron 등록

## 미해결 / 향후

- 한국어/영어 자료 비율 조정 (현재는 keyword 기반)
- 트렌드 감지 (같은 토픽이 N 일 연속 등장 시 합치기)
- `morning-digest-recap` routine 과의 연결 (Slack 리액션 수집 → positioning 자동 갱신)
- v0.4.0+ ingest_llm.py 와 연동: digest 의 entity 도 LLM 추출 → 그래프 통합
