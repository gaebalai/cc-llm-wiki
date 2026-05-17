# Changelog

본 프로젝트의 의미 있는 변경사항을 기록합니다.
형식은 [Keep a Changelog](https://keepachangelog.com/ko/1.1.0/) 기반,
버저닝은 [Semantic Versioning](https://semver.org/lang/ko/) 을 따릅니다.

릴리스 노트는 [GitHub Releases](https://github.com/gaebalai/cc-llm-wiki/releases) 에도 동일 정리됨.

---

## [Unreleased]

### Added
- (다음 사이클 후보 → README §Phase 로드맵 참조)

---

## [0.4.4] — 2026-05-18

운영 정착: CHANGELOG · Dataview 강화 · contributors 가이드.

### Added
- `CHANGELOG.md` (본 파일) — v0.1.0~v0.4.4 누적 정리.
- `vault/dashboards/status.md` 에 쿼리 4 종 추가:
  - 7. graph 동기 큐 (`.claude/queue/graph.txt`) 미처리 항목 수
  - 8. 최근 30 일 digest 도달 카운트 (positioning 운영 추이)
  - 9. type 별 분포 (topic/decision/digest/self)
  - 10. status 미설정/누락 검출 (lint 보강)
- `README.md` 에 "기여 (CONTRIBUTING)" 섹션 — 자료 추가·Skill 수정·PR 패턴.

### Changed
- `README.md` 활성 자산 표 v0.4.3 반영 (8 Skills · 5 routines · entity 18 canonical / 60 aliases).
- `README.md` Phase 로드맵 v0.3.7~v0.4.3 누적.

---

## [0.4.3] — 2026-05-18

`daily-digest` Skill 본체 — `positioning.md` 의존 + 검색 쿼리 자동 설계 runner.

### Added
- `scripts/daily_digest_runner.py` — positioning.md 파싱 + 5 검색 쿼리 자동 설계 + digest 페이지 골격 출력.
- `skills/daily-digest/positioning.template.md` — 사용자 vault 의 의도 헌법 템플릿 (interests/avoid/trusted_sources/tone).
- `skills/daily-digest/SKILL.md` 7-step 절차 (positioning 검증 → WebSearch → 중복 배제 → digest 페이지 → PR → Slack).

### Changed
- `daily-digest` 가 stub 감지 (markdown 코드 블록 안 frontmatter) 시 abort + 자동 활성 안내.

---

## [0.4.2] — 2026-05-18

LLM 추출 정확도 측정 cycle.

### Added
- `services/graph/eval.py` — precision/recall/F1 자동 측정. rule/llm/consistency 3 mode.
- `vault/03_schema/eval-gold/*.yaml` — 룰베이스 결과 자동 시드 (사람 검수 보강 필요).
- CI `.github/workflows/ci.yml` 항목 10: rule vs gold 전체 평가 (vault 변경 시).

### Changed
- `services/graph/ingest_graph.py` — Source 노드는 평가에서 제외 (의미 entity 만).

---

## [0.4.1] — 2026-05-18

P/R/F1 측정 준비 + 헤더 청크 + 머지 runner.

### Added
- `services/graph/ingest_llm.py` 헤더 (`##`·`###`) 기반 청크 분할 — 4000 자 초과 시.
- `services/graph/ingest_merge.py` — 룰베이스 → LLM 순차 머지 (--skip-rule/--skip-llm 옵션).
- `scripts/daily_digest_runner.py` 쿼리 설계 (dry-run, 외부 호출 없음).

---

## [0.4.0] — 2026-05-17

LangChain LLMGraphTransformer 도입 — SOLVES/USES 의미 관계 추출 경로 확보.

### Added
- `services/graph/ingest_llm.py` — LangChain `LLMGraphTransformer` 호출, `NODE_LABELS`·`RELATION_TYPES` enum 제약, aliases-candidates 자동 발견.
- `scripts/daily_digest_runner.py` dry-run 골격 — positioning.md 검증 + 쿼리 미리보기.
- `services/graph/templates/causal_path.cypher` — Company → Challenge → Solution → Technology 다중 hop.

### Changed
- `services/graph/ingest_graph.py` — 룰베이스 단독 사용 시도 시 MENTIONS/REFERS_TO 만 추출. SOLVES/USES 는 ingest_llm 의 책임.

---

## [0.3.10] — 2026-05-17

wikilink 매칭 완화 + 발견성 강화.

### Added
- GitHub Topics 12 종 (`anthropic-claude`, `obsidian`, `langchain`, `neo4j`, `graphrag` 등) — repo 검색성 향상.

### Fixed
- CI `vault lint` 항목 7: `[[2026-05-17-slug]]` 도 valid (full stem)·`[[slug]]` (short slug) 양쪽 매칭.
- `skills/lint/SKILL.md` 양식 동일하게 갱신.

---

## [0.3.9] — 2026-05-17

운영 자동화 트랙: routine 5 종 추가 + graph-sync 외부 vault 지원 + .env 비번 sync 감지.

### Added
- `.claude/routines/sleep-maintenance.md` — 매일 03:00 graph-sync 큐 처리 + orphan_audit + aliases-candidates 발견.
- `.claude/routines/wiki-ingest-sweep.md` — 매시 정각 `01_raw/` 신규 감지 (알림만, **자동 ingest 금지**).
- `install.sh` step 4 에 Neo4j 컨테이너 비번 ↔ `.env` 불일치 자동 감지 + 환경변수 override 안내.

### Changed
- `services/graph/ingest_graph.py` 외부 vault 절대경로 지원 (try/except `relative_to`).
- env 우선순위 변경: 옛 `{**os.environ, **load_env(.env)}` → 새 `{**load_env(.env), **os.environ}` — 환경변수 override 가능.

---

## [0.3.8] — 2026-05-17

한국 시장 entity 보강 + env 우선순위 안정화.

### Added
- `vault/03_schema/aliases.yaml` 에 한국 AI 시장 4 entity (한국AI교육진흥원·바이브코딩·VRL·gobigbuja).

### Fixed
- `services/graph/ingest_graph.py` 외부 vault 절대경로에서 `Path.relative_to` ValueError → try/except 우회.

---

## [0.3.7] — 2026-05-17

CI 활성화 + Obsidian Excluded files 자동 머지.

### Added
- `.github/workflows/ci.yml` — 10 항목 자동 검증 (JSON·SKILL frontmatter·bash syntax·python compile·install --check·vault lint·시크릿 leak·.env 보호·eval).
- `install.sh` 의 `merge_obsidian_ignore()` — 사용자 vault 의 `.obsidian/app.json` Excluded files 안전 머지 (`docs-internal/`·`docs/` 자동 추가).

---

## [0.3.6] — 2026-05-17

vault 평탄화 컨벤션 (flat) 지원 — Obsidian 친화 기본값.

### Added
- `install.sh` 가 `.obsidian/` 위치로 vault 모드 자동 감지:
  - **flat 모드** (Obsidian 권장): `TARGET_DIR` 자체가 vault, `01_raw/`·`02_wiki/` 가 root 에 직접
  - **subdir 모드** (옛 컨벤션): `TARGET_DIR/vault/` 아래

### Changed
- `CLAUDE.md` §2 권한 매트릭스 — `(vault/)` 표기로 양쪽 모드 동시 표현.
- `SCHEMA.md` §3 raw 슬러그 — 한글 허용 (ERROR → WARN-RAW), Web Clipper 친화.

---

## [0.3.5] — 2026-05-16

Plugin install validation 5 회 패치 — `/install` 디렉터리를 plugin root 이동.

### Fixed
- `commands/` `skills/` 가 `.claude/` 안에 있을 때 plugin loader 가 발견 못 함 → plugin root 로 이동.
- `plugin.json` validation 통과 (commands/skills 필드 제거 → 자동 발견).

---

## [0.3.4] — 2026-05-16

`plugin.json` validation 3 항목 패치.

### Fixed
- `repository` 필드 object → string (URL).
- `commands` `skills` 경로에 `./` prefix + trailing slash.

---

## [0.3.3] — 2026-05-16

Plugin source 형식 url 로 (anthropic-official 패턴).

### Fixed
- `.claude-plugin/marketplace.json` 의 `source` 가 `"."` / `{"source":"github",...}` 양쪽 모두 인식 실패 → `{"source":"url","url":"https://github.com/gaebalai/cc-llm-wiki.git"}` 로 성공.
  - Anthropic 공식 marketplace 35 건 중 35 건이 url 형식.

---

## [0.3.2] — 2026-05-16

Plugin source 를 GitHub object 형식으로 (실패, v0.3.3 으로 재도전).

---

## [0.3.1] — 2026-05-16

실 Neo4j 검증 + 2 graph-sync 이슈 패치.

### Fixed
- `docker compose --env-file` 누락 (compose 가 `infra/neo4j/` 기준으로 `.env` 찾아 실패) → `--env-file $TARGET_DIR/.env` 명시.
- `ingest_graph.py` 외부 vault path 에서 `Path.relative_to` ValueError.

---

## [0.3.0] — 2026-05-16

8 Skills 완성 + 2 hooks 신설.

### Added
- 신설 Skill 4 종: `query` · `morning-brief` · `evening-reflect` · `daily-digest` (전부 8 종 완성).
- 신설 Hook 2 종: `UserPromptSubmit` (인사 → morning-brief 자동) · `Stop` (모순 검출 → 세션 차단).
- `query` Skill — local Grep / graph Cypher 라우터 (자연어 → Cypher 자동 생성 금지).
- `morning-brief` — drafts·overdue·신규 raw·lint 미해결 한 화면 요약.
- `evening-reflect` — 세션 종료 시 모순 검사 (decisions 덮어쓰기·CONTRADICTS·self 노출).

### Removed
- Kagura MCP 흔적 8 파일 15 라인 — 로컬 전용 결정 후 외부 의존 제거.

---

## [0.2.0] — 2026-05-15

Plugin 글로벌 설치 안정화.

### Added
- `install.sh` PLUGIN_INSTALL 자동 감지 (`CLAUDE_PLUGIN_ROOT` 환경변수).
- `install.sh` 가 사용자 `.claude/settings.json` 에 Hook 안전 머지 (덮어쓰기 X, 키 충돌 시 보존).
- `install.sh` 가 템플릿 파일 (CLAUDE.md·SCHEMA.md 등) 을 사용자 vault 로 복사.

---

## [0.1.0] — 2026-05-14

첫 게시 — GitHub Public repo + tag + Release.

### Added
- P0~P6 전체 골격 — vault 디렉터리 트리, 4 Skills (ingest·lint·compile·graph-sync), CLAUDE.md 11 섹션 헌법.
- Plugin marketplace (`.claude-plugin/marketplace.json` + `plugin.json`) 첫 등록.
- `infra/neo4j/docker-compose.yml` (Neo4j 5.18.1 + APOC, read-only vault 마운트).
- `services/graph/{ingest_graph,query_graph}.py` + 3 Cypher templates.
- `scripts/install.sh` 7-step + `scripts/post_slack.py`.
- `docs/` 11 개 설계 문서 (원전·context·routines·publish·SCHEMA·Neo4j PoC 등).

---

## 변경 카테고리

- **Added**: 새 기능
- **Changed**: 기존 기능 동작 변경
- **Deprecated**: 곧 제거될 기능
- **Removed**: 제거된 기능
- **Fixed**: 버그 수정
- **Security**: 보안 관련
