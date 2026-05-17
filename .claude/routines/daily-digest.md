---
name: daily-digest
cron: "0 7 * * *"             # 매일 07:00 KST
timezone: Asia/Seoul
status: dry-run                # daily-digest Skill 본체 작성 전까지 dry-run
phase: P4 (Skill 본체 P4+ 후속)
skills: [daily-digest]         # ← 아직 미작성, 본 routine 호출 시 stub 응답
mcp: [slack, github]
env_required: [SLACK_WEBHOOK_URL]
---

# Routine: daily-digest

매일 07:00 KST 에 위키와 `positioning.md`(P6 작성 예정)를 참고해 검색 쿼리를 자동
설계하고 외부 정보 5건을 골라 Slack 에 투고. 결과는 `vault/02_wiki/digests/YYYY-MM-DD.md`
에 저장하고 PR 로 자동 머지.

## 현재 상태 (2026-05-17)

- `daily-digest` Skill 본체 **미작성**. 본 routine 은 명세만 존재.
- Slack 토큰 없음 → dry-run 으로만 동작.
- 활성화 조건:
  1. `skills/daily-digest/SKILL.md` 작성
  2. `.env` 에 `SLACK_WEBHOOK_URL` 채우기
  3. `positioning.md` 작성 (사용자가 목표·관심사·금기 토픽 정의)

## 실행 절차 (P4+ 후속에서 구현)

1. `Skill: daily-digest` 호출
   - 입력: `vault/index.md` 의 topics 목록 + `positioning.md`
   - 출력: 5건의 (제목, URL, 한 줄 요약, 출처)
2. `vault/02_wiki/digests/YYYY-MM-DD.md` 작성
   - frontmatter: `type: digest`, `status: reviewed`, `sources: <원문 URL 배열>`
3. Slack 투고:
   ```bash
   python scripts/post_slack.py \
     --title "[daily-digest] YYYY-MM-DD" \
     --body-file vault/02_wiki/digests/YYYY-MM-DD.md
   ```
4. 브랜치 `auto-digest/YYYY-MM-DD` → PR → squash merge

## 중복 배제 정책

- 같은 URL 이 7일 내 다른 digest 에 있으면 제외 (Grep 으로 `sources:` 검사)
- 같은 토픽이 3일 연속이면 다른 토픽으로 강제 전환

## 미해결

- positioning.md 의 정확한 스키마는 P6 회고에서 결정
- 한국어 자료 우선순위·신뢰도 가중치는 첫 1주 운영 후 조정
