// causal_path: Company → Challenge → Solution → Technology 경로 탐색
// 입력 파라미터:
//   $company_canonical : Anthropic | OpenAI | ...
//   $max_hops          : 3 (기본), 5 까지 권장 한도
// 출력:
//   path : 노드/엣지 시퀀스
//   nodes_canonical : 경로 상 canonical_name 배열
//
// 주의: v0.3.0 의 룰베이스 ingest_graph.py 는 MENTIONS·REFERS_TO 만 생성.
// SOLVES/USES 는 v0.4.0 의 LangChain LLMGraphTransformer 도입 후 활성.
// 그 때까지는 MENTIONS|REFERS_TO 만으로 fallback (의미적으로는 "같이 등장한 노드들의 경로").

MATCH path = (c:Company {canonical_name: $company_canonical})
  -[:MENTIONS|REFERS_TO|SOLVES|USES*1..3]-(ch:Challenge)
  -[:MENTIONS|REFERS_TO|SOLVES|USES*1..3]-(s:Solution)
  -[:MENTIONS|REFERS_TO|SOLVES|USES*0..3]-(t:Technology)
WHERE c <> ch AND ch <> s AND s <> t
RETURN
  [n IN nodes(path) | n.canonical_name] AS nodes_canonical,
  [r IN relationships(path) | type(r)]  AS rel_types,
  length(path) AS hops
ORDER BY hops ASC
LIMIT 10;
