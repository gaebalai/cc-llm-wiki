# log — LLM 행동 일지

모든 Skill 실행은 이 파일에 한 줄 append 한다. 시간 역순(최신 위)이 아니라
**시간 정순**(최신이 아래)이다 — 5번 routine·11번 PoC가 시간순 grep을 가정.

## 포맷

```
- YYYY-MM-DDTHH:MM:SS±09:00 | [skill-name] | actor | action | refs
```

- actor: `human` · `cc-session` · `routine:<name>`
- refs: `vault/...` 경로나 PR URL을 공백으로 분리

## 진입

- 2026-05-17T17:30:00+09:00 | [scaffold] | human | P0 스캐폴드 생성 | CLAUDE.md vault/ .claude/
