---
name: sleep-maintenance
cron: "0 3 * * *"             # 매일 03:00 KST
timezone: Asia/Seoul
status: active
phase: P5+
skills: [graph-sync]
mcp: [neo4j-cypher]
env_required: [NEO4J_URI, NEO4J_PASSWORD]
---

# Routine: sleep-maintenance

매일 새벽 03:00 KST 에 Neo4j 그래프 의 누적 큐를 일괄 처리 + 정합성 검사.
조용한 시간대에 무거운 작업을 모아서 실행해 낮 시간 응답성 유지.

## 트리거

- **Cron**: 매일 03:00 KST (정확히)
- **수동**: `/sleep-maintenance` 또는 `/graph-sync --queue`
- env 없으면 dry-run (NEO4J_PASSWORD 미설정 시 skip)

## 5-step 절차

### Step 1. 큐 처리
- `.claude/queue/graph.txt` 의 누적 path 들을 `graph-sync` Skill 로 일괄 upsert
- 큐 비어있어도 다음 단계 진행 (전체 sync 옵션)

### Step 2. orphan_audit
- `services/graph/query_graph.py orphan_audit --env .env`
- 결과 (관계 없는 entity 노드) 가 N>5 이면 Slack 통지 또는 log.md WARN

### Step 3. aliases.yaml 일관성 검사
- 그래프의 `canonical_name` 중에서 aliases.yaml 미등록인 게 있나 검사
- 신규 entity 후보 발견 시 `vault/02_wiki/_lint/aliases-candidates.md` 에 기록 (사람이 검토 후 aliases.yaml 에 수동 추가)

### Step 4. stale Source 노드 정리 (선택)
- `MATCH (s:Source) WHERE s.updated_at < <30 days ago> RETURN s`
- stale 노드는 자동 삭제 X — 사람 검토 (log 알림만)

### Step 5. 통계 log
- `vault/log.md` 에 1 줄:
  ```
  - <ISO8601> | [sleep-maintenance] | routine | upserts=N orphans=M aliases-candidates=K | -
  ```
- (Slack 옵션) `python3 scripts/post_slack.py --title "[sleep-maintenance] YYYY-MM-DD" --body "..."`

## 절대 금지

- Neo4j 데이터 자동 삭제 (사람 검토 필수)
- aliases.yaml 자동 추가 (LLM 추론 결과 비신뢰)
- 사용자 cwd 변경 (routine 은 read-only 스캔만)

## 등록

```bash
# Claude Code /schedule 로 등록 (실 cron 진입)
claude /schedule create \
  --name sleep-maintenance \
  --cron "0 3 * * *" \
  --command "/graph-sync --queue && /sleep-maintenance-report"
```

routine 명세 (본 파일) 와 실제 cron 등록은 별개. 본 파일은 진실의 소스, cron 등록은 운영 행위.

## 활성화 조건

1. Neo4j 컨테이너 가동
2. `.env` 의 `NEO4J_PASSWORD` 가 컨테이너 실 비번과 일치 (v0.3.8 운영 메모 참조)
3. `pip install neo4j` (drypy-run 만 쓸 게 아니면)
4. `.claude/queue/` 디렉터리 존재 (PostToolUse hook 이 만듦)

## 미해결

- aliases 후보 발견을 LLM 으로 자동 제안 (v0.4.0 LangChain LLMGraphTransformer 연계)
- stale Source 의 자동 archive 정책 (현재는 사람 검토만)
