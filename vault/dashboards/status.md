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
정확한 lint는 `.claude/skills/lint/` Skill 호출.

## 6. lint 리포트 인덱스

```dataview
LIST file.link
FROM "02_wiki/_lint"
SORT file.name DESC
LIMIT 10
```

---

## Skill 호출 단축키

- 새 raw 추가 후: `/ingest <raw_path>` → draft 생성
- draft 검토 완료: `/compile <draft_path>` → topics/로 승급 (ERROR 0건일 때만)
- 주간 검사: `/lint` → vault/02_wiki/_lint/YYYY-MM-DD.md
- 그래프 동기 (P5 이후): `/graph-sync <topic_path>`
