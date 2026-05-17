---
type: dashboard
locale: ko
---

# Wiki Status Dashboard

이 페이지는 **Obsidian Dataview 플러그인**으로 동작합니다.
설치: `Settings → Community plugins → Browse → Dataview → Install → Enable`.
플러그인 설정에서 **JavaScript Queries** 옵션은 켤 필요 없음 (DQL만 사용).

`dashboard` type 은 SCHEMA.md 의 4 타입(topic/decision/self/digest)에 속하지 않으므로 lint 검사에서 제외됩니다(SCHEMA §5 예외 항목 추가 필요 시 별도 PR).

---

## 1. 상태별 카운트 (topics/decisions/digests)

```dataview
TABLE WITHOUT ID
  status as "status",
  length(rows) as "count"
FROM "02_wiki/topics" OR "02_wiki/decisions" OR "02_wiki/digests"
WHERE type != null
GROUP BY status
SORT status DESC
```

## 2. 미검토 draft 목록 (_drafts/)

```dataview
TABLE
  file.ctime as "작성",
  type as "type",
  length(file.outlinks) as "links"
FROM "02_wiki/_drafts"
WHERE type != null
SORT file.ctime DESC
```

## 3. 최근 7일 갱신된 topics

```dataview
TABLE
  status as "status",
  updated_at as "updated_at",
  length(file.outlinks) as "outlinks"
FROM "02_wiki/topics"
WHERE type = "topic" AND date(updated_at) > date(today) - dur(7 days)
SORT date(updated_at) DESC
```

## 4. orphan 후보 (어디서도 링크되지 않은 topics)

```dataview
TABLE WITHOUT ID
  file.link as "file",
  type as "type",
  updated_at as "updated_at"
FROM "02_wiki/topics"
WHERE type = "topic" AND length(file.inlinks) = 0
SORT file.ctime DESC
```

(주의: `_drafts/`·`digests/`·`self/`는 orphan 정상 폴더라 본 쿼리에서 자동 제외됨)

## 5. broken wikilink가 남은 draft (수동 확인용)

```dataview
TABLE
  file.outlinks as "outlinks (마우스 hover로 미존재 확인)"
FROM "02_wiki/_drafts"
WHERE length(file.outlinks) > 0
```

Dataview의 `file.outlinks`는 미존재 링크도 그대로 표시합니다. 마우스로 hover했을 때 빨간색이면 broken.
정확한 lint는 `skills/lint/` Skill 호출.

## 6. lint 리포트 인덱스

```dataview
LIST file.link
FROM "02_wiki/_lint"
SORT file.name DESC
LIMIT 10
```

## 7. graph 동기 큐 (미처리 wiki 변경)

`.claude/queue/graph.txt` 는 `PostToolUse` hook 이 위키 편집을 적재하는 큐.
큐가 비어있지 않으면 `sleep-maintenance` routine 이 매일 03:00 KST 에 `graph-sync --queue` 로 처리.
즉시 동기화하려면 `/graph-sync --queue` 수동 호출.

```dataview
TABLE WITHOUT ID
  file.link as "topic",
  graph_synced_at as "마지막 동기"
FROM "02_wiki/topics"
WHERE type = "topic" AND (graph_synced_at = null OR date(graph_synced_at) < date(updated_at))
SORT date(updated_at) DESC
LIMIT 20
```

> `graph_synced_at` 이 `updated_at` 보다 오래된 (또는 null) topic 만 표시 → graph 미반영 후보.

## 8. 최근 30 일 digest 도달 카운트 (positioning 운영 추이)

```dataview
TABLE WITHOUT ID
  dateformat(file.ctime, "yyyy-MM-dd") as "date",
  length(file.outlinks) as "links"
FROM "02_wiki/digests"
WHERE date(file.ctime) > date(today) - dur(30 days)
SORT file.ctime DESC
```

> `daily-digest` routine 이 매일 07:00 KST 에 추가하는 디제스트. 빈 날짜 = positioning 매칭 0 건 또는 routine 미발사.

## 9. type 별 분포

```dataview
TABLE WITHOUT ID
  type as "type",
  length(rows) as "count"
FROM "02_wiki"
WHERE type != null AND !contains(file.folder, "_lint") AND !contains(file.folder, "_drafts")
GROUP BY type
SORT length(rows) DESC
```

## 10. status 누락/잘못 검출 (lint 보강)

```dataview
TABLE WITHOUT ID
  file.link as "file",
  type as "type",
  status as "status"
FROM "02_wiki"
WHERE type != null
  AND !contains(file.folder, "_lint")
  AND !contains(file.folder, "_drafts")
  AND (status = null OR !contains(list("draft", "reviewed", "published"), status))
```

> `lint` Skill 이 같은 검사를 수행하지만 Dataview 로 즉시 시각화. enum 외 값이거나 누락된 page 만 표시.

---

## Skill 호출 단축키

- 새 raw 추가 후: `/ingest <raw_path>` → draft 생성
- draft 검토 완료: `/compile <draft_path>` → topics/로 승급 (ERROR 0건일 때만)
- 주간 검사: `/lint` → vault/02_wiki/_lint/YYYY-MM-DD.md
- 그래프 동기 (P5 이후): `/graph-sync <topic_path>`
