# [Neo4j 도입편] Claude Code × Obsidian제 "2do BRAIN"을 GraphRAG에 대응시키는 최소 PoC

> **SEO 제목 후보 3안 (한국 환경 기준)**
> 1. **[Neo4j 도입편] Claude Code × Obsidian제 "2do BRAIN"을 GraphRAG에 대응시키는 최소 PoC**
> 2. **LangChain + Neo4j로 만드는 GraphRAG 최소 PoC — 명명 일치(엔티티 정규화)부터 Cypher 검증까지**
> 3. **벡터 RAG 위에 "관계 탐색" 층을 더한다 — Claude Code × Obsidian × Neo4j 구축 실전**
>
> *(1안은 시리즈 원문 그대로의 후크형, 2안은 검색 의도("LangChain · Neo4j · 명명 일치") 매칭형, 3안은 RAG 대비 차별 포인트("관계 탐색")를 앞세운 클릭 유도형이다.)*

---

## 들어가며 — 다음에 더해야 할 것은 "관계성"을 다루는 층

지난 글에서는 Claude Code × Obsidian으로, 1차 정보를 깨지 않고 축적·편집하기 위한 자율형 지식 OS **"2do BRAIN"** 의 기본 구성을 소개했다.

> *[번역자 보완] 원문에는 이 자리에 "지난 글은 여기"라는 자체 사이트 링크 카드가 들어가 있다. 한국 독자가 이 글을 읽을 때는 시리즈의 [구현편]에 해당하는 글을 먼저 보면 맥락이 자연스럽다.*

이 구성으로 `01_raw/`에 원전을 남기면서 `02_wiki/`에 구조화 지식을 키울 수 있는 토대는 만들 수 있다. 그런데 **실무에서 계속 쓰다 보면 다음 벽에 부딪힌다.** 바로 **"지식끼리의 연결을 기계적으로 따라갈 수 없다"** 는 문제다.

예컨대 마크다운 기반 위키 운용만 가지고도 **"A사의 과제는 무엇인가"** 는 읽을 수 있다. 하지만 **"그 과제에 대해 과거에 어떤 해결책을 제안했고, 어떤 기술을 묶었는가"** 를 횡단적으로 따라가려고 하면, **사람이 수동으로 링크를 따라가며 찾아야 한다.**

일반적인 벡터 검색은 모호 검색이나 의미 검색에 강한 한편, **복수 실체의 관계성을 명시적으로 따라가는 용도에서는 그래프 구조 쪽이 다루기 좋은 장면**이 있다. 이 글에서는 **Vector RAG를 대체하는 게 아니라, 관계 탐색의 층으로서 Neo4j를 보조적으로 추가한다.**

> *[원문 이미지 자리 — 본 번역에는 옮기지 않았다.]*

---

## 이번에 하지 않을 것

이 글에서는 **GraphRAG를 프로덕션 운용 가능한 상태까지는 다루지 않는다.**

특히 다음은 다음 회 이후의 테마다.

- 복수 문서에 걸친 완전한 명명 일치(entity disambiguation, 名寄せ)
- APOC를 쓴 재통합 배치
- 자연어로부터의 Cypher 생성
- 차분 갱신과 재인제스트(re-ingest) 전략

이번에는 어디까지나 **"Neo4j에 안전하게 흘려보내고, Cypher로 물리 검증까지 가능하게 하는 것"** 을 골로 잡았다.

> *[번역자 보완] **명명 일치(名寄せ)**는 한국 데이터 업계에서 보통 **"엔티티 해소(entity resolution)"** 또는 **"엔티티 정규화"** 라고 부른다. 같은 개념이다. 본문에서는 LangChain 공식 용어 "entity disambiguation"을 우선 표기하되, 한국 독자 가독성을 위해 "명명 일치"로 한 차례 옮긴 곳을 두었다.*

---

## 이번의 방어선 (추출의 규칙화)

그래프 DB는 강력하지만, **LLM에게 자유롭게 추출시키면 그래프는 금세 망가진다.** 특히 위험한 게 다음 셋이다.

- **스키마의 무질서화**
- **명명 일치 부족에 의한 노드 분열**
- **검증 전에 자연어 쿼리로 넘어가 버리는 것**

Neo4j의 그래프 모델에서는 **노드와 관계 양쪽에 프로퍼티를 가질 수 있고, 관계는 타입 부여(typed)된다.** 뒤집어 말하면, **타입 설계를 게을리하면 `Company`와 `Organization` 같은 비슷한 개념이 섞이기 시작하고, 나중에 운용이 급속히 괴로워진다.**

또 LangChain의 지식 그래프 구축에서는 **청크 단위로 처리되는 사정상**, 다른 청크 사이에서 같은 인물이나 회사가 별도 노드로 떨어질 가능성이 있다. 그래서 **entity disambiguation(명명 일치)이 후단에서 중요해진다.**

그래서 이 도입편에서는 다음 방어선을 긋는다.

- **추출할 노드 타입과 릴레이션 타입을 처음부터 좁힌다**
- **사전 규칙으로 `canonical_name`과 `aliases`를 의식한 추출에 맞춰 둔다**
- **`include_source=True`를 쓸 때는 `metadata.id`를 명시한다**
- **갑자기 자연어 QA로 가지 말고, 고정 Cypher로 물리 검증한다**

---

## Neo4j 셋업

우선 받을 그릇이 되는 Neo4j를 띄운다. 이번에는 M1 Mac 같은 로컬 개발 환경에서도 다루기 쉽도록, **메모리를 조여 둔 `docker-compose.yml`** 로 시작한다.

> **보충:** 이 글에서는 APOC를 향후의 재통합 배치 용도뿐 아니라, **LangChain의 `Neo4jGraph`가 수행하는 스키마 갱신과 노드·릴레이션 투입에도 사용**한다. 그래서 이 최소 PoC에서도 APOC를 도입 전제로 둔다.

> *[번역자 보완] M1 Mac은 한국 개발자에게도 익숙한 표현이지만, **인텔 Mac, Apple Silicon(M2/M3/M4) Mac**, 그리고 **WSL2 환경의 Windows**, **Ubuntu 데스크톱**에서도 동일하게 동작한다. Neo4j 5.18.1 공식 이미지는 멀티 아키텍처 빌드라 ARM/AMD 모두 지원한다.*

### `docker-compose.yml`

```yaml
version: "3.8"
services:
  neo4j:
    image: neo4j:5.18.1
    container_name: 2do-brain-neo4j
    restart: unless-stopped
    ports:
      - "7474:7474" # Browser UI
      - "7687:7687" # Bolt
    environment:
      - NEO4J_AUTH=neo4j/strong_password_2026
      - NEO4J_PLUGINS=["apoc"]
      - NEO4J_apoc_export_file_enabled=true
      - NEO4J_apoc_import_file_enabled=true
      - NEO4J_apoc_import_file_use__neo4j__config=true
      - NEO4J_dbms_memory_pagecache_size=512M
      - NEO4J_dbms_memory_heap_initial__size=512M
      - NEO4J_dbms_memory_heap_max__size=512M
    volumes:
      - ./neo4j/data:/data
      - ./neo4j/logs:/logs
      - ./neo4j/import:/var/lib/neo4j/import
      - ./neo4j/plugins:/plugins
```

기동한다.

```bash
docker compose up -d neo4j
```

이어서 Python 쪽 `.env`를 만든다.

### `.env`

```env
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=strong_password_2026
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

라이브러리는 이렇게 깔아 둔다.

```bash
pip install langchain langchain-community langchain-experimental langchain-openai neo4j python-dotenv
```

---

## 최소 인제스트 (지식의 추출과 투입)

여기서부터 실제 텍스트를 그래프로 투입한다. 이번 PoC에서는 LangChain의 **`LLMGraphTransformer`** 와 **`Neo4jGraph`** 를 쓴다.

### 왜 `metadata.id`를 넣는가

LangChain의 `add_graph_documents()`는 `include_source=True`를 붙이면, **소스 문서 노드를 저장해 각 엔티티에 묶을 수 있다.** `include_source=True`는 편리하지만, **`metadata.id`를 넣지 않으면 소스 문서의 머지 키가 `page_content`의 MD5 기반**이 된다. PoC에서는 그래도 돌지만, **실무에서는 본문의 미세한 수정만으로도 다른 소스로 다뤄질 가능성이 있어, 고정 ID를 명시하는 편이 안전하다.**

### 추출 규칙의 "해킹"에 대해

> **보충:** `LLMGraphTransformer`에는 `prompt` 지정도 가능하지만, **실 운용에서는 버전 차이나 structured output 주변의 흔들림으로 결과가 변하는 경우가 있다.** 그래서 이 글에서는 **재현성을 우선해, 대상 텍스트 머리에 추출 규칙을 물리적으로 결합하는 방식**을 채택했다.

### `ingest_graph.py`

```python
import os
from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_openai import ChatOpenAI
from langchain_community.graphs import Neo4jGraph
from langchain_experimental.graph_transformers import LLMGraphTransformer

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not NEO4J_PASSWORD or not OPENAI_API_KEY:
    raise ValueError("환경 변수 NEO4J_PASSWORD 또는 OPENAI_API_KEY가 설정되어 있지 않습니다.")

ALLOWED_NODES = ["Person", "Company", "Challenge", "Solution", "Technology"]
ALLOWED_RELATIONSHIPS = [
    "HAS_CHALLENGE",
    "PROPOSES",
    "USES_TECHNOLOGY",
    "SOLVES",
    "RELATED_TO",
]

EXTRACTION_RULES = """
【중요: 엔티티 추출 규칙(명명 일치와 정규화)】
다음 텍스트에서 지식 그래프를 추출할 때, 같은 대상은 반드시 하나의 「정규화된 ID(canonical_name)」로 통일해 주세요.
1. 회사명: 「주식회사 〇〇」 「〇〇사」는 모두 「〇〇사」를 ID로 해 주세요. (예: A사)
2. 표기 흔들림: 텍스트 안에 있는 별명이나 약칭은 반드시 `aliases` 프로퍼티에 배열로 저장해 주세요.
---
[대상 텍스트 시작]
"""

# ⚠️ 공개용으로 완전히 익명화된 가공의 업무 메모
RAW_TEXT = """
2026년 3월, 주식회사 알파(A사)와의 면담을 향한 전략 메모.
A사의 최대 과제는 「속인적인 CSV 수작업 연계」와, SaaS 간 연계 시의 「메모리 부족에 의한 처리 불안정화」다.
이에 대해 나는 n8n을 쓴 「방어적 아키텍처」를 제안한다. 또 AI의 환각(hallucination) 대책으로는 LangGraph를 채택하고, 정보 유출 리스크를 억제하는 해결책을 제시한다.
"""

def main():
    print("🔌 Neo4j 에 접속 중...")
    graph = Neo4jGraph(
        url=NEO4J_URI,
        username=NEO4J_USERNAME,
        password=NEO4J_PASSWORD,
    )

    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0,
        api_key=OPENAI_API_KEY,
    )

    combined_text = EXTRACTION_RULES + RAW_TEXT.strip()

    document = Document(
        page_content=combined_text,
        metadata={
            "id": "doc_alpha_strategy_202603_001",
            "source": "2do_brain_poc_markdown",
            "title": "A사 면담 전략 메모",
            "created_at": "2026-03",
        },
    )

    print("🧠 LLM에 의한 그래프 추출 개시...")
    transformer = LLMGraphTransformer(
        llm=llm,
        allowed_nodes=ALLOWED_NODES,
        allowed_relationships=ALLOWED_RELATIONSHIPS,
        node_properties=["description", "canonical_name", "aliases"],
        relationship_properties=["description"],
    )

    graph_documents = transformer.convert_to_graph_documents([document])

    print("=== 추출 노드 검품 ===")
    for node in graph_documents[0].nodes:
        aliases = node.properties.get("aliases", "없음") if hasattr(node, "properties") else "없음"
        print(f"[{node.type}] ID: {node.id} / aliases: {aliases}")

    print("💾 Neo4j 에 저장 중...")
    graph.add_graph_documents(
        graph_documents,
        baseEntityLabel=True,
        include_source=True,
    )
    graph.refresh_schema()
    
    print("✅ 인제스트 완료")

if __name__ == "__main__":
    main()
```

> *[번역자 보완] 원문 샘플 텍스트는 일본 기업 컨텍스트(주식회사 알파 = "株式会社アルファ")로 되어 있다. 한국 환경에서 자기 PoC에 그대로 가져갈 때는 **"주식회사 ○○ → ○○㈜ → ○○사"** 처럼 한국 기업 표기 흔들림 패턴을 그대로 `EXTRACTION_RULES`에 적어 두면 동일하게 동작한다. 영문 별칭(A사, ABC Inc., 알파)도 같은 규칙으로 묶을 수 있다.*

### 이 단계에서 하고 있는 것

이 스크립트가 하는 일은 사실 꽤 단조롭다. 다만 **그 단조로움이 중요하다.**

- 추출 타입을 최소한으로 제한한다
- 별명을 `aliases`로 모은다
- 소스 문서에 **고정 ID**를 붙인다
- 우선 **단일 문서로 인제스트해 동작을 본다**

LangChain의 지식 그래프 구축에서는 청크 단위로 entity consistency가 무너질 가능성이 있다. 그래서 **도입편에서는 "우선 한 줄 통과시킨다"는 데 집중하는 게 안전하다.**

---

## 고정 Cypher로 검증한다

데이터가 들어오면, 바로 자연어 QA로 가지 말고 **우선 고정 Cypher로 "정말로 선이 이어져 있는지"** 를 본다. 그래프 DB에서는, **여기를 건너뛰면 추출 실패인지 쿼리 생성 실패인지의 절단(切り分け)이 불가능해진다.**

### `query_graph.py`

```python
import os
from dotenv import load_dotenv
from langchain_community.graphs import Neo4jGraph

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

def main():
    graph = Neo4jGraph(
        url=NEO4J_URI,
        username=NEO4J_USERNAME,
        password=NEO4J_PASSWORD,
    )

    print("=== 검증: 회사 → 과제 → 해결책 → 기술 ===")
    
    query = """
    MATCH (c:Company)-[:HAS_CHALLENGE]->(ch:Challenge)<-[:SOLVES]-(s:Solution)-[:USES_TECHNOLOGY]->(t:Technology)
    WHERE toLower(c.id) CONTAINS 'alpha' OR toLower(c.id) CONTAINS 'a사'
    RETURN 
      c.id AS Company, 
      ch.id AS TargetChallenge, 
      s.id AS Solution, 
      collect(DISTINCT t.id) AS Technologies
    """
    
    result = graph.query(query)
    
    if not result:
        print("⚠️ 전략 경로가 이어져 있지 않습니다.")
        return
        
    for record in result:
        print(f"[{record['Company']}]")
        print(f"  └─(과제)→ {record['TargetChallenge']}")
        print(f"               └─(제안)→ {record['Solution']}")
        print(f"                            └─(기술)→ {', '.join(record['Technologies'])}")
        print()

if __name__ == "__main__":
    main()
```

> *[번역자 보완] 원문은 `'a社'`(일본어)를 검색 키워드로 썼지만, 한국 독자가 자기 PoC를 굴릴 때는 위처럼 `'a사'`로 두면 한국어 텍스트에서 그대로 동작한다. Cypher의 `toLower()` 함수는 한국어 입력도 정상 처리한다.*

### 실행 결과

이 스크립트를 실행하면 터미널에는 다음처럼 출력된다.

```
=== 검증: 회사 → 과제 → 해결책 → 기술 ===
[A사]
  └─(과제)→ 속인적인 CSV 수작업 연계
               └─(제안)→ 방어적 아키텍처
                            └─(기술)→ n8n, LangGraph
```

이렇게 **회사를 기점으로 "과제 → 해결책 → 기술"의 경로를 따라갈 수 있다면 PoC로서는 성공**이다.

---

## 마치며 — 다음 회 예고

이번 도입편에서 한 일은 **GraphRAG를 완성시킨 게 아니다.** Neo4j를 접속하고, LangChain 경유로 지식을 그래프화하고, **Cypher로 물리 검증할 수 있는 토대를 만든** 것이다.

여기까지 되면 지난 글에서 만든 **2do BRAIN**은,

- **원전을 지키는 `01_raw/`**
- **편집 완료 지식을 키우는 `02_wiki/`**
- **연결을 다루는 Neo4j**

이렇게 3층으로 운용 가능해진다. 또한 이번 PoC에서는 **"단일 문서 안의 사전 정규화"** 까지만 다뤘다. **복수 문서 운용에서 반드시 문제가 되는 노드 분열은, 다음 회에서 APOC의 `apoc.refactor.mergeNodes`를 쓴 재통합 배치**로 다룬다.

지식은 **보존되기만 해서는 자산이 되지 않는다.** **"원전" · "정리된 지식" · "관계 그래프"** 를 나눠 운용해야, AI는 검색 도구가 아니라 **실무를 가로질러 떠받치는 두뇌**에 가까워진다.

---

## 도입 지원에 대해

이 글에서 소개한 **"2do BRAIN"** 및 **"GraphRAG 통합"** 의 구성은, 실무 도입 향으로 템플릿화해 제공하고 있다.

- 3층 스토리지 구조의 초기 구축
- 업무 전용 그래프 스키마 설계
- Claude Code / Obsidian / n8n / Neo4j의 운용 동선 정비
- 30일간의 동반 지원

상세는 아래를 참고.

> *[번역자 보완] 원문에는 자체 사이트의 도입 지원 페이지 링크 카드가 들어가 있지만, 실제 링크가 본문에 노출돼 있지 않아 그대로 옮기지는 않았다. 한국 독자가 비슷한 셋업을 사내에 도입하려 한다면 위 4가지 항목을 RFP/SOW의 체크리스트로 그대로 가져갈 수 있다.*

---

## 부록 — 번역자 보완 사항 모음

원문에 없는 보완 내용을 한곳에 모아 둔다.

1. **SEO 제목 3안** — 시리즈 원문 후크형 / 검색 의도 매칭형 / RAG 대비 차별 포인트 후킹형.
2. **시리즈 도입 안내 주석** — 원문 도입부의 "지난 글은 여기" 링크 자리에 한국 독자용 시리즈 안내 주석을 짧게 추가.
3. **명명 일치 용어 해소** — 일본어 `名寄せ(나요세)`는 한국 데이터 업계 표현 **"엔티티 해소(entity resolution) / 엔티티 정규화"** 와 동의어임을 명시. LangChain 공식 용어 "entity disambiguation"을 우선 표기하면서 "명명 일치"로 풀이.
4. **개발 환경 보완** — 원문 "M1 Mac"만 언급된 부분에 **인텔/Apple Silicon Mac, WSL2 Windows, Ubuntu** 환경 모두 동일하게 동작한다는 점, Neo4j 5.18.1 공식 이미지가 멀티 아키텍처 빌드라는 점을 보완.
5. **한국 기업 표기 흔들림 예시 보완** — `EXTRACTION_RULES` 부분에 일본 기업 표기 흔들림(株式会社/〇〇社) 외에 **한국 기업 표기(주식회사 ○○ / ○○㈜ / ○○사 / 영문 약칭)** 패턴도 같은 규칙으로 묶을 수 있음을 안내.
6. **Cypher 검색 키워드 한글 동작 안내** — 원문 `'a社'`를 한국 환경에서는 `'a사'`로 쓰면 그대로 동작한다는 점, Cypher의 `toLower()`가 한국어 입력도 정상 처리한다는 점을 명시.
7. **도입 지원 섹션 링크 자리 처리** — 원문에는 자체 사이트 링크 카드가 들어가 있었지만 실제 URL이 본문에 노출돼 있지 않아 옮기지 않았다는 점, 대신 RFP/SOW 체크리스트로 활용 가능하다는 안내를 보완.
8. **용어 표기** —
   - **`Neo4j`, `APOC`, `Cypher`, `LangChain`, `LangGraph`, `LLMGraphTransformer`, `Neo4jGraph`, `n8n`, `Docker`, `Bolt`, `MD5`, `Cypher`, `WSL2`, `Apple Silicon`** — 모두 영문 표기 유지(한국 개발 환경 표준).
   - **`canonical_name`, `aliases`, `allowed_nodes`, `allowed_relationships`, `include_source`, `metadata.id`, `entity disambiguation`, `entity consistency`, `structured output`** — 코드/사양 영문 그대로 보존.
   - **"속인적(屬人的)인"** — 한국 IT/SI 현장에서도 그대로 통하는 표현이라 살림.
   - **"방어적 아키텍처(defensive architecture)"** — 일반화된 영문 개념이라 그대로.
   - 일본어 `挙動(거동)` → **"동작"** 으로 일괄 교체. 한국 개발자에게는 "동작"이 압도적으로 자연스럽다.
   - 일본어 `名寄せ` → **"명명 일치"** 로 옮기되 영문 entity disambiguation 병기.
   - 일본어 `切り分け(키리와케)` → **"절단/분리"** 또는 **"원인 분리"** 의 의미인데, 본문에서는 가독성을 위해 "원인 절단(切り分け)"으로 한자 병기 처리했다.
9. **번역 방침** — 3-pass: ① 직역으로 의미 손실 방지(특히 코드 주석·로그 출력 메시지의 일관성), ② 한국어 자연스러움 우선의 표현 교체(번역투/상투구 최소화), ③ 시니어 엔지니어 가이드 톤 유지(단정적·결론 단단히 잡는 어미, "방어선·전제·전략"같은 무게감 있는 어휘). 자기 컨설팅 서비스 안내가 마지막에 붙어 있어, 광고 톤이 과해지지 않도록 절제했다.
10. **소스 코드·YAML·Dockerfile·bash·Python·Cypher·환경변수 그대로 유지** — 사용자 요청대로 요약하지 않았다. `docker-compose.yml`, `.env`, `pip install` 명령, `ingest_graph.py` 전체, `query_graph.py` 전체, Cypher 쿼리, 실행 결과 출력 모두 원문 그대로 옮겼다. **코드 내부 한국어 번역은 print 메시지와 텍스트 콘텐츠(EXTRACTION_RULES, RAW_TEXT)에만 적용했고, 변수명·키워드·함수명·환경 변수명은 영문 그대로 보존**했다.
