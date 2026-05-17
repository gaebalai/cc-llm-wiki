---
name: graph-sync
description: vault/02_wiki/topics/ 의 reviewed/published 페이지 1건 또는 .claude/queue/graph.txt 의 누적 변경분을 Neo4j 그래프에 upsert 한다. services/graph/ingest_graph.py 를 호출하며 dry-run 옵션 지원. PostToolUse hook 이 큐를 채우고 sleep-maintenance routine 또는 사용자가 명시적으로 호출했을 때 발동한다. graph_synced_at frontmatter 를 갱신한다.
disable-model-invocation: false
allowed-tools:
  - Read
  - Grep
  - Glob
  - Edit
  - Bash(python3 services/graph/ingest_graph.py:*)
  - Bash(python3 services/graph/query_graph.py:*)
  - Bash(cat:.claude/queue/graph.txt)
  - Bash(rm:.claude/queue/graph.txt)
  - Bash(date:*)
---

# graph-sync Skill — wiki → Neo4j upsert

## 목적

`vault/02_wiki/topics/` 의 wiki 페이지를 Neo4j 그래프에 동기한다. 두 가지 호출 경로:

1. **수동 호출** (`/graph-sync <topic_path>`): 사용자가 특정 토픽을 즉시 동기
2. **큐 일괄 처리** (`/graph-sync --queue` 또는 sleep-maintenance routine): `PostToolUse` hook 이 `.claude/queue/graph.txt` 에 누적한 변경 path 들을 한 번에 처리

## 입력

- `topic_path` (선택): 단일 파일 절대경로 또는 vault 상대경로
- `--queue` (선택): 큐 모드 (`.claude/queue/graph.txt` 일괄 처리)
- 둘 다 미지정 시 사용자에게 확인 요청 (전체 재동기는 위험, 명시 의도만)

## 절대 금지

- `.claude/queue/graph.txt` 자동 비우기 전 **upsert 성공 검증** 필수. 실패 시 큐 그대로 유지.
- `status` 가 `draft` 인 페이지는 동기 거부 (reviewed 이상만 그래프 진입)
- `vault/02_wiki/self/` 페이지는 동기 거부 (외부 노출 금지 폴더, CLAUDE.md §3-⑤)
- `vault/02_wiki/_drafts/`·`_lint/` 는 동기 대상 아님
- Cypher 직접 작성·실행 금지 — `ingest_graph.py` 만 통과

## 6단계 절차

### Step 1. 동기 대상 결정
- `topic_path` 인자가 있으면 그 1건
- `--queue` 모드면 `cat .claude/queue/graph.txt` 로 path 목록 수집 (중복 제거)
- 각 path 의 frontmatter `status` 확인 → `draft` 또는 `self` 폴더는 목록에서 제거

### Step 2. dry-run 검증
- `python3 services/graph/ingest_graph.py <path> --dry-run` 실행
- 추출 결과(JSON) 의 nodes/relations 카운트를 사용자에게 보고
- entity 추출 결과가 비정상이면(0건 등) 즉시 중단 + aliases.yaml 보강 안내

### Step 3. Neo4j 환경 검증
- `.env` 의 `NEO4J_URI`, `NEO4J_PASSWORD` 존재 확인
- 없으면 dry-run 결과만 출력하고 종료 (Neo4j 미기동 환경 안전)

### Step 4. 실제 upsert
- `python3 services/graph/ingest_graph.py <path>` (dry-run 없이)
- exit code 검사. 0 이외면 큐 유지 + 실패 보고

### Step 5. frontmatter 갱신
- 동기 성공한 topic 의 frontmatter `graph_synced_at` 을 현재 ISO8601 으로 갱신
- `Edit` 도구로 1줄 변경
- `updated_at` 은 **건드리지 않음** (그래프 동기는 wiki 본문 변경 아님)

### Step 6. 큐 정리 + 로그
- `--queue` 모드 성공 시: 처리된 path 만 큐에서 제거 (실패분은 유지)
- `vault/log.md` 1줄 append:
  ```
  - <ISO8601> | [graph-sync] | (cc-session|routine:sleep-maintenance) | sources=<n> nodes=<n> rels=<n> | <path 또는 queue>
  ```

## broken canonical 자동 검증

upsert 후 `query_graph.py orphan_audit` 자동 실행 → 신규 orphan 노드가 발견되면:
- aliases.yaml 누락 추정 → 사용자에게 보고 (자동 추가 금지, [[entity-disambiguation-strategy]] §운영 메모)
- orphan 수치를 log 에 같이 기록 (장기 추적)

## 사용 예

```
사용자: /graph-sync vault/02_wiki/topics/2026-05-17-graphrag-poc-with-neo4j.md
Claude: [Step 1] 대상 1건, status=reviewed OK
        [Step 2] dry-run: nodes=8 rels=10 (entity 추출 정상)
        [Step 3] Neo4j .env OK
        [Step 4] upsert 완료. 18 statements OK.
        [Step 5] frontmatter graph_synced_at 갱신
        [Step 6] orphan_audit: 0 신규 orphan. log 갱신.
        ✓ 동기 성공.

사용자: /graph-sync --queue
Claude: [Step 1] 큐에 3건. status 검증 후 3건 모두 통과.
        ... (Step 2-6 반복)
        ✓ 3 path 동기. 큐 비움.
```

## 실패 시

- Step 2 entity 추출 0건 → 중단, aliases.yaml 보강 안내
- Step 3 NEO4J_PASSWORD 없음 → dry-run 결과만 출력, exit 0
- Step 4 upsert 일부 실패 → 성공분만 큐에서 제거, 실패 path 와 stderr 그대로 보고
- neo4j 드라이버 미설치 → `pip install neo4j` 안내

## 관련

- 큐 채우기는 `.claude/settings.json` 의 PostToolUse hook (P5 후속 작업)
- sleep-maintenance routine (P5+) 이 매일 03:00 KST `/graph-sync --queue` 호출
- 자연어 검색은 `query` Skill (P3~P5) 이 의도 분류 후 `query_graph.py` 에 위임
