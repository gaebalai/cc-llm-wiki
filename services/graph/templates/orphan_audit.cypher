// orphan_audit: 어떤 관계도 없는 entity 노드 (Source 제외)
// 정규화 누락 또는 alias 미등록 후보. weekly-lint 와 별도로 sleep-maintenance routine 에서 호출.

MATCH (n)
WHERE NOT n:Source
  AND NOT (n)--()
RETURN
  labels(n) AS labels,
  n.canonical_name AS canonical,
  n.id AS id
ORDER BY labels, canonical
LIMIT 100;
