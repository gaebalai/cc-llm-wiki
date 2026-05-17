---
name: weekly-lint
cron: "0 6 * * 0"           # 매주 일요일 06:00 KST
timezone: Asia/Seoul
status: active                # active | dry-run | disabled
phase: P4
skills: [lint]
mcp: []
env_required: []              # Slack 통지는 옵션 (없으면 stdout 만)
---

# Routine: weekly-lint

매주 일요일 06:00 KST 에 `lint` Skill 을 호출해 vault 전체 정합성을 검사하고
리포트(`vault/02_wiki/_lint/YYYY-MM-DD.md`)를 만든 뒤 Slack 으로 요약을 통지한다.

## 실행 절차

1. `Skill: lint` 호출 (인자 없음 → 기본 스코프 = SKILL.md "검사 대상" 표 전체)
2. 새로 생성된 `vault/02_wiki/_lint/YYYY-MM-DD.md` 파일 1건 식별
3. ERROR/WARN 카운트 추출 (리포트 헤더의 표에서)
4. ERROR > 0 또는 WARN > 5 일 때만 Slack 통지:
   ```bash
   python scripts/post_slack.py \
     --title "[weekly-lint] YYYY-MM-DD: ERROR=<n> WARN=<n>" \
     --body-file vault/02_wiki/_lint/YYYY-MM-DD.md
   ```
   (Slack 토큰 없으면 dry-run 으로 stdout 만)
5. git 작업:
   - 브랜치 `auto-lint/YYYY-WW` 생성
   - `git add vault/02_wiki/_lint/YYYY-MM-DD.md vault/log.md`
   - 커밋 메시지: `[lint] weekly: E=<n> W=<n>`
   - 원격 있으면 `gh pr create` (`auto-lint/...` → `main`)
6. `vault/log.md` 1줄 append (lint Skill 이 이미 수행)

## 통지 임계 정책

| 조건 | 동작 |
|---|---|
| ERROR = 0 AND WARN ≤ 5 | Slack 통지 없음, PR 만 자동 머지 가능 |
| ERROR > 0 | Slack 통지 + PR 머지 보류(사람 리뷰 필요) |
| WARN > 5 | Slack 통지 + PR 자동 머지 |

## 수동 호출

```
사용자: /weekly-lint
또는
사용자: /lint   (Skill 직접 호출, routine 의 PR 자동화 없이 lint 만)
```

## 검증 (수동)

```bash
# routine 등록 확인 (Claude Code /schedule list)
claude /schedule list | grep weekly-lint

# dry-run 실행
python scripts/post_slack.py --title "[weekly-lint] test" --body "OK" --env .env.example
```

## 미해결

- Claude Code `/schedule` skill 의 정확한 routine 등록 인터페이스는 P4 후속 세션에서 결정.
  본 파일은 routine 의 "명세" 이며 실제 등록은 `/schedule create` 로 별도 수행.
