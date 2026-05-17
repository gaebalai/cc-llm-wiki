// concept_neighbors: 특정 canonical 의 1~2 hop 이웃 (관계 종류별 그룹화)
// 입력:
//   $canonical : 검색 대상 canonical_name
// 출력:
//   neighbor_canonical, rel_type, hop, source_count (몇 개 Source 에서 등장했는지)

MATCH (target {canonical_name: $canonical})
WITH target
MATCH (target)-[r1]-(n1)
OPTIONAL MATCH (n1)-[r2]-(n2)
  WHERE n2 <> target AND NOT n2:Source
RETURN
  coalesce(n2.canonical_name, n1.canonical_name) AS neighbor_canonical,
  CASE WHEN n2 IS NULL THEN type(r1) ELSE type(r2) END AS rel_type,
  CASE WHEN n2 IS NULL THEN 1 ELSE 2 END AS hop,
  count(DISTINCT n1) AS source_count
ORDER BY hop, source_count DESC
LIMIT 30;
