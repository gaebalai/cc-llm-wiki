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
- 2026-05-17T17:48:00+09:00 | [ingest] | cc-session | draft 생성 (사용자 승인) | vault/01_raw/articles/2026-05-17-2do-brain-neo4j-graphrag-poc.md -> vault/02_wiki/_drafts/2026-05-17-graphrag-poc-with-neo4j.md
- 2026-05-17T18:00:00+09:00 | [lint] | cc-session | E=1 W-DRAFT=2 W=0 | vault/02_wiki/_lint/2026-05-17.md
- 2026-05-17T18:05:00+09:00 | [schema-update] | human-via-cc | SCHEMA §5 lint 규칙 10항목으로 확장, draft 강등(WARN-DRAFT)·예외 처리 절차 추가 | vault/SCHEMA.md
- 2026-05-17T18:05:00+09:00 | [skill-update] | human-via-cc | lint Skill 검사 대상 확장: _drafts/ 포함, 01_raw/ 파일명 검사 추가 (8→10 항목) | .claude/skills/lint/SKILL.md
