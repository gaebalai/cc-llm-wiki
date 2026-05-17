---
name: install
description: cc-llm-wiki plugin 의 원스톱 설치 명령. Obsidian → Dataview → .env+Neo4j Docker → Slack 토큰 → weekly-review 슬롯까지 7 단계를 대화형으로 진행한다. 안전한 idempotent 스크립트라 여러 번 실행해도 OK.
allowed-tools:
  - Bash(bash scripts/install.sh:*)
  - Bash(open:*)
  - Read
---

# /install — cc-llm-wiki 환경 셋업

## 무엇을 하나

`scripts/install.sh` 를 호출해 다음 7 단계를 순차 진행합니다.
사용자 입력이 필요한 부분은 대화형으로 묻고, 자동화 가능한 부분은 알아서 처리합니다.

| Step | 내용 | 사용자 액션 | 자동화 |
|---|---|---|---|
| 1 | macOS/명령어 사전 검사 (git, python3, brew) | 없음 | 검사 결과 표시 |
| 2 | Obsidian 설치 확인 → 없으면 `brew install --cask obsidian` | 설치 동의 | URI 로 vault 열기 |
| 3 | Dataview 안내 + `vault/dashboards/status.md` 열기 | Obsidian 안에서 수동 설치 | URI 로 status.md 열기 |
| 5 | `.env` 생성 + `NEO4J_PASSWORD` 자동 생성 (없을 때만) | 비번 생성 동의 | sed 로 .env 갱신 |
| 4 | Docker Desktop 확인 → Neo4j 컨테이너 기동 | Docker.app 권한 부여 | `docker compose up -d` + Browser 준비 polling |
| 6 | Slack Webhook 토큰 발급 절차 안내 | `\$EDITOR .env` 로 직접 입력 권장 | dry-run 1건 검증 |
| 7 | weekly-review 슬롯 + 운영 명령 요약 | 없음 | 통계 카운트 출력 |

## 호출 모드

| 인자 | 의미 |
|---|---|
| (없음) | 전체 7 단계 진행 |
| `--check` | 변경 없이 환경 검사만 |
| `--step N` | N 번째 단계만 실행 |

## 사용 예

```
사용자: /install
Claude: bash scripts/install.sh 호출. 대화형 단계 진행 중...

사용자: /install --check
Claude: bash scripts/install.sh --check 호출. 환경만 검사.

사용자: /install --step 4
Claude: Docker + Neo4j 단계만 다시 실행.
```

## 절대 금지

- `.env.example` 에 실제 시크릿 적기 (placeholder 만)
- `.env` 를 Read·cat 으로 노출 (시크릿 컨텍스트 유입)
- Slack 토큰을 명령 인자로 받기 (셸 history 노출)
- 사용자 동의 없이 Obsidian/Docker 자동 설치
- NEO4J_PASSWORD 자동 생성 후 사용자에게 안 알리기 (.env 보존 → 사용자가 알 수 있어야 함)

## 실행

`bash scripts/install.sh` 를 그대로 실행합니다. 사용자가 인자(`--check`, `--step N`)를 줬다면 그대로 전달합니다.

스크립트가 끝나면 결과를 한 줄로 요약하고, 다음 자연스러운 단계(예: 첫 ingest, weekly-review 일정)를 안내합니다.
