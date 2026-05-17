# index — 위키 카탈로그

이 파일은 `vault/02_wiki/` 전체를 두 단계로 탐색할 수 있게 하는 카탈로그다.
LLM이 매번 전수 스캔하지 않도록 **JIT(Just-in-Time)** 진입점으로 동작한다.

## 사용 원칙

- 모든 `topics/`·`decisions/` 페이지는 **반드시 이 index에 등록**된다(compile Skill이 강제)
- `self/`·`_drafts/`·`_lint/`·`digests/`는 등록 대상 아님
- Claude Code는 질의 시 **이 index 헤더 + 관련 장르 섹션만** 읽어 컨텍스트 절약
- 5엔트리 초과 시 장르별 sub-index 분할(`vault/02_wiki/_index/{genre}.md`)

## 장르별 카탈로그

### topics/

(아직 비어 있음 — P1에서 첫 항목 추가)

### decisions/

(아직 비어 있음 — P3 이후 ADR-001부터 시작)

---

## Index 통계

- topics 총 개수: 0
- decisions 총 개수: 0
- 최종 갱신: 2026-05-17 (P0 스캐폴드)
