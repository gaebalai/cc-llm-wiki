---
name: weekly-review
cron: "0 21 * * 0"             # 매주 일요일 21:00 KST (weekly-lint 06:00 보다 늦게)
timezone: Asia/Seoul
status: active
phase: P6
skills: []                      # Skill 호출 없음 — 사용자가 직접 회고
mcp: []
env_required: []
---

# Routine: weekly-review

매주 일요일 21:00 KST 에 사용자에게 회고 슬롯을 알려준다.
**자동 처리는 없다** (회고는 사람만 할 수 있다). routine 의 역할은 "지금 시간이다" 라고
SessionStart hook 의 표시를 일회성 강화하는 것 + 회고 템플릿을 stdout 으로 출력.

## 출력 (cron 트리거 시)

```text
=== weekly-review YYYY-WW ===
이번 주 vault 통계:
  - 신규 raw       : <find vault/01_raw -mtime -7 | wc -l>
  - 신규 topic 승급: <git log --since="7 days ago" --grep="[compile]" | wc -l>
  - lint ERROR/WARN: <vault/02_wiki/_lint/ 최신 리포트의 헤더 발췌>
  - graph 상태     : <services/graph/query_graph.py orphan_audit --env .env 결과 행 수>

회고 체크리스트:
  □ self/llm-wiki-origins.md 의 "회고 메모" 섹션에 1~3줄 append
  □ 이번 주 만든 topics 의 broken wikilink 잔재 (lint WARN-DRAFT) 정리
  □ aliases.yaml 누락 발견 → 사람이 수동 추가
  □ daily-digest Skill 실호출 여부 결정 (positioning.md 작성 진척)
  □ macos 임시 파일 (있다면) 처리 — 리네임/inbox/삭제
  □ Slack 통지 한 번도 안 봤다면 SLACK_WEBHOOK_URL 제거 검토
```

## 절차

1. `bash -lc '<위 통계 명령들>'` 실행 → stdout 표시
2. macOS notification 또는 Slack 메시지 (옵션):
   ```bash
   python scripts/post_slack.py \
     --title "[weekly-review] YYYY-WW" \
     --body "회고 슬롯입니다. 통계 출력은 터미널 확인."
   ```
   (Slack 없으면 dry-run)
3. 사용자가 self/llm-wiki-origins.md 를 열고 회고 append
4. `vault/log.md` 1줄 (사용자가 직접):
   ```
   - <ISO8601> | [weekly-review] | human | 회고 완료 | <비고>
   ```

## 활성화 조건

- 본 routine 자체는 의존 0 — 즉시 active
- Slack 알림이 필요하면 `.env` 에 `SLACK_WEBHOOK_URL` 채우기

## 미해결

- 4주 운영 후 본 routine 의 유용성 자체를 재평가 (회고 시간이 매주 같은 슬롯에 와도 좋은가)
- 통계 자동 수집 vs 수동 입력 비율 조정
