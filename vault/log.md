# log — LLM 행동 일지

모든 Skill 실행은 이 파일에 한 줄 append 한다. 시간 역순(최신 위)이 아니라
**시간 정순**(최신이 아래)이다 — 5번 routine·11번 PoC가 시간순 grep을 가정.

## 포맷

```
- YYYY-MM-DDTHH:MM:SS±09:00 | [skill-name] | actor | action | refs
```

- actor: `human` · `cc-session` · `routine:<name>`
- refs: `vault/...` 경로나 PR URL을 공백으로 분리

## 진입

- 2026-05-17T17:30:00+09:00 | [scaffold] | human | P0 스캐폴드 생성 | CLAUDE.md vault/ .claude/
- 2026-05-17T17:48:00+09:00 | [ingest] | cc-session | draft 생성 (사용자 승인) | vault/01_raw/articles/2026-05-17-2do-brain-neo4j-graphrag-poc.md -> vault/02_wiki/_drafts/2026-05-17-graphrag-poc-with-neo4j.md
- 2026-05-17T18:00:00+09:00 | [lint] | cc-session | E=1 W-DRAFT=2 W=0 | vault/02_wiki/_lint/2026-05-17.md
- 2026-05-17T18:05:00+09:00 | [schema-update] | human-via-cc | SCHEMA §5 lint 규칙 10항목으로 확장, draft 강등(WARN-DRAFT)·예외 처리 절차 추가 | vault/SCHEMA.md
- 2026-05-17T18:05:00+09:00 | [skill-update] | human-via-cc | lint Skill 검사 대상 확장: _drafts/ 포함, 01_raw/ 파일명 검사 추가 (8→10 항목) | skills/lint/SKILL.md
- 2026-05-17T18:20:00+09:00 | [skill-create] | cc-session | compile Skill 신설: 7-step 승급 절차, lint 게이트, broken link 4가지 처리 패턴 | skills/compile/SKILL.md
- 2026-05-17T18:20:00+09:00 | [dashboard] | cc-session | Dataview 상태 보드 신설 (6 쿼리: 상태 카운트·draft 목록·최근 7일·orphan·broken link·lint 리포트 인덱스) | vault/dashboards/status.md
- 2026-05-17T18:20:00+09:00 | [claude-md] | cc-session | §4 Skill Index 상태 갱신 (P1·P2·P3 활성 표기) | CLAUDE.md
- 2026-05-17T18:45:00+09:00 | [ingest] | cc-session | 약식 ingest (사용자 "진행" 승인) | docs/11 raw에서 entity-disambiguation-strategy draft 추출
- 2026-05-17T18:45:00+09:00 | [ingest] | cc-session | 약식 ingest (사용자 "진행" 승인) | docs/11 raw에서 2do-brain-architecture draft 추출
- 2026-05-17T18:50:00+09:00 | [compile] | cc-session | 클러스터 compile (SKILL 예외 패턴 1, 3건 동시) | _drafts/{graphrag-poc-with-neo4j,entity-disambiguation-strategy,2do-brain-architecture}.md -> topics/
- 2026-05-17T18:50:00+09:00 | [index] | cc-session | index.md topics/ 섹션에 3건 등록, 통계 0→3 | vault/index.md
- 2026-05-17T19:10:00+09:00 | [scaffold] | cc-session | P4 골격: .env.example, scripts/post_slack.py (dry-run 검증 OK), 3 routine 명세 | .env.example scripts/post_slack.py .claude/routines/{weekly-lint,daily-digest,publish-multilang}.md
- 2026-05-17T19:10:00+09:00 | [claude-md] | cc-session | §11 routine 표 상태 갱신 (active/dry-run/TBD) | CLAUDE.md
- 2026-05-17T19:40:00+09:00 | [scaffold] | cc-session | P5 GraphRAG PoC 골격: docker-compose, aliases.yaml(14 entries), ingest_graph.py, query_graph.py, Cypher 템플릿 3건, graph-sync SKILL | infra/neo4j/ services/graph/ vault/03_schema/aliases.yaml skills/graph-sync/
- 2026-05-17T19:40:00+09:00 | [dry-run] | cc-session | ingest_graph.py --all --dry-run 검증 OK | sources=3 nodes=N rels=N (Neo4j 미연결, 추출만)
- 2026-05-17T19:40:00+09:00 | [claude-md] | cc-session | §10 Graph Layer active 갱신, §4 graph-sync 활성 표기 | CLAUDE.md
- 2026-05-17T20:00:00+09:00 | [scope-decision] | human | "공개 의도 없음, 로컬 전용" 결정. publish 라인 전체 제거 | .claude/routines/publish-multilang.md dist/ Cloudflare 키 §4 publish Skill §11 publish-multilang 행
- 2026-05-17T20:00:00+09:00 | [cleanup] | cc-session | CLAUDE.md §3-⑤ self 노출 publish 제거, §6 frontmatter locale 주석 갱신, §7 브랜치 prefix publish 제거, §9 publish 실패 행 제거, §11 slack 옵션 표기 | CLAUDE.md README.md .env.example .gitignore
- 2026-05-17T20:15:00+09:00 | [security] | human-via-cc | .env.example 에 실제 시크릿 유입 사고 → 사용자가 직접 복원 + .env 분리. commit 전 차단 | .env.example .env (gitignore)
- 2026-05-17T21:00:00+09:00 | [self-page] | cc-session | self/llm-wiki-origins.md 작성: 11 docs DNA 트리, 채택/거른/미루기 매트릭스, 회고 메모 슬롯 | vault/02_wiki/self/llm-wiki-origins.md
- 2026-05-17T21:00:00+09:00 | [routine] | cc-session | weekly-review routine 신설 (일 21:00 KST, 사람 회고 슬롯) | .claude/routines/weekly-review.md
- 2026-05-17T21:00:00+09:00 | [hook] | cc-session | PostToolUse 에 graph 큐 적재 hook 추가 (topics/*.md Edit 시 .claude/queue/graph.txt append) — P5 보완 | .claude/settings.json
- 2026-05-17T21:00:00+09:00 | [claude-md] | cc-session | §10 동기 경로 ✅ P6 active, §11 weekly-review 추가 | CLAUDE.md README.md
- 2026-05-17T22:00:00+09:00 | [plugin] | cc-session | Claude Code plugin packaging: .claude-plugin/plugin.json manifest, /install 슬래시 명령 신설 | .claude-plugin/plugin.json commands/install.md
- 2026-05-17T22:00:00+09:00 | [installer] | cc-session | scripts/install.sh 작성: 7 단계 (precheck/Obsidian/Dataview/Docker+Neo4j/.env/Slack/weekly-review), idempotent, --check 안전 모드, --step N 부분 실행 | scripts/install.sh
- 2026-05-17T22:00:00+09:00 | [verify] | cc-session | install.sh --check 통과 (Docker daemon 만 미실행, 그 외 모두 OK) | -
- 2026-05-17T22:30:00+09:00 | [marketplace] | cc-session | .claude-plugin/marketplace.json 신설, plugin.json 정정 (commands/skills 를 디렉터리 string 으로). 단일-plugin 마켓플레이스 패턴 | .claude-plugin/marketplace.json .claude-plugin/plugin.json
- 2026-05-17T22:30:00+09:00 | [docs] | cc-session | PUBLISH.md 작성: GitHub repo 생성 → remote add → push → tag 절차, 사용자 측 /plugin marketplace add gaebalai/cc-llm-wiki 흐름 | docs-internal/PUBLISH.md README.md
- 2026-05-17T22:30:00+09:00 | [verify] | cc-session | JSON 유효성 + 교차참조 검증 (commands 1건, skills 4건 자동 발견 가능) | -
- 2026-05-17T23:00:00+09:00 | [docs] | cc-session | QUICKSTART.md 신설 (첫 사용자 9 섹션: 설치 3 방법, /install 7 단계, ingest~graph-sync 워크플로, cheat sheet, FAQ, 한 줄 요약) | QUICKSTART.md
- 2026-05-17T23:00:00+09:00 | [docs] | cc-session | README.md 재구성: 정체성 중심으로 슬림화. plugin 빠른 시작 → QUICKSTART 연결, badges 추가, Phase 로드맵 현황표, 활성 자산 카탈로그 | README.md
- 2026-05-17T23:00:00+09:00 | [docs] | cc-session | LICENSE 신설 (MIT, Jaewoo Kim 2026) | LICENSE
- 2026-05-17T23:00:00+09:00 | [installer] | cc-session | install.sh step 7 마무리에 QUICKSTART.md 안내 추가 | scripts/install.sh
- 2026-05-17T23:30:00+09:00 | [raw-clean][schema] | human-via-cc | SCHEMA §6 신설: raw 메타-only 정리 허용 + 트레일러 marker 권장 + 적용 사례 1건. CLAUDE.md §2 권한, §3-① 예외 갱신. self/llm-wiki-origins.md 회고 메모 1건 append | vault/SCHEMA.md CLAUDE.md vault/02_wiki/self/llm-wiki-origins.md
- 2026-05-17T23:30:00+09:00 | [raw-clean] | human | docs/11 raw 파일에서 메타 노이즈 제거 (SEO 후보 블록·번역 노트 3건·이미지 자리 1건·APOC 인용 형식 정정). 본문 의미 무변경 | vault/01_raw/articles/2026-05-17-2do-brain-neo4j-graphrag-poc.md
- 2026-05-18T00:00:00+09:00 | [release] | human-via-cc | GitHub Public repo 생성 + push origin main + tag v0.1.0 + Release 게시 | https://github.com/gaebalai/cc-llm-wiki | https://github.com/gaebalai/cc-llm-wiki/releases/tag/v0.1.0
- 2026-05-18T00:00:00+09:00 | [verify] | cc-session | marketplace.json·plugin.json raw.githubusercontent.com 에서 fetch 확인. 사용자 측 /plugin marketplace add gaebalai/cc-llm-wiki 즉시 가능 | -
- 2026-05-18T00:15:00+09:00 | [raw-rename] | human-via-cc | macos 숨겨진 폴더 raw 파일을 SCHEMA §3 슬러그 규칙에 맞게 리네임. ERROR 1→0 | "vault/01_raw/articles/macos 숨겨진 폴더 - Google 검색.md" -> "vault/01_raw/articles/2026-05-17-macos-show-hidden-folder.md"
- 2026-05-18T00:25:00+09:00 | [obsidian] | human-via-cc | .gitignore 에 vault/.obsidian/plugins/ 추가 (바이너리 무시), community-plugins.json 만 commit (Dataview enable 명세 보존) — 표준 패턴 적용 | .gitignore vault/.obsidian/community-plugins.json
- 2026-05-18T00:35:00+09:00 | [health] | cc-session | 14 영역 sanity check: PASS 28 / FAIL 0 / WARN 0 (JSON/YAML/SKILL frontmatter/Python compile/Bash syntax/lint 10항목/내부링크/marketplace 교차참조/git 상태/시크릿 leak/hook 시뮬레이션/dry-run/install.sh --check) | -
- 2026-05-18T01:00:00+09:00 | [docs] | cc-session | blog.md 신설 (353줄): cc-llm-wiki 블로그 소개글. 도입(RAG 한계·Karpathy 영감)부터 3층 격리·Context Engineering 6기법·기술 스택·9 자산·설치·5분 데모·의도 거부·CLAUDE.md 11섹션·보안·Plugin marketplace 구조·Phase 진척·한 줄 요약·영감 자료 | blog.md
- 2026-05-18T01:30:00+09:00 | [marketplace-rename] | human-via-cc | marketplace 이름 cc-llm-wiki → claudecode.to-marketplace 로 변경 (사용자 도메인 반영). plugin 이름은 cc-llm-wiki 유지. 9 곳 install/update 명령 일괄 갱신 (README 3·QUICKSTART 2·blog 2·PUBLISH 2). marketplace.json name 만 변경 | .claude-plugin/marketplace.json README.md QUICKSTART.md blog.md docs-internal/PUBLISH.md
- 2026-05-18T01:35:00+09:00 | [marketplace-rename] | human-via-cc | claudecode.to-marketplace → claudecode-to-marketplace 로 fallback (kebab-case 호환성 보장). 9 곳 일괄 갱신 | .claude-plugin/marketplace.json README.md QUICKSTART.md blog.md docs-internal/PUBLISH.md
- 2026-05-18T02:00:00+09:00 | [release-prep] | cc-session | v0.2.0 준비: install.sh 재설계 (PLUGIN_INSTALL 감지·--target-dir·copy_templates·merge_hooks). plugin-install 시뮬레이션 OK (11 핵심 파일 + 4 hooks 머지). README/QUICKSTART Plugin 권장으로 복구. plugin.json/marketplace.json 0.1.0 → 0.2.0 | scripts/install.sh README.md QUICKSTART.md .claude-plugin/plugin.json .claude-plugin/marketplace.json
- 2026-05-18T02:30:00+09:00 | [kagura-remove] | human-via-cc | Kagura MCP 흔적 전부 삭제: 8 파일 15 라인. id 주석 "Neo4j·Kagura" → "Neo4j 만", §11 MCP 표에서 kagura-memory 행 제거, README/blog "거른 것" 항목 삭제, self/origins DNA 트리·매트릭스·미루기·회고 메모 4 곳, 2do-brain-architecture L3a/L3b → L3 단일, graphrag-poc-with-neo4j 횡단 지견 갱신, SCHEMA duplicate id 설명. 2 topic 의 updated_at 갱신. lint ERROR 0 / WARN 0 | CLAUDE.md vault/SCHEMA.md vault/02_wiki/self/llm-wiki-origins.md vault/02_wiki/topics/{2do-brain-architecture,graphrag-poc-with-neo4j}.md README.md blog.md skills/graph-sync/SKILL.md
- 2026-05-18T03:00:00+09:00 | [skill-expand] | cc-session | v0.3.0: 미완성 Skill 4 종 신설. query (lookup/relation/complex 라우터, 자연어→Cypher 금지), morning-brief (drafts/raw/lint 한 화면 요약, Read 만), evening-reflect (Stop hook 모순 게이트, decisions 덮어쓰기/CONTRADICTS/self 노출 검사), daily-digest (positioning.md 의존, 외부 5건 → digests/, Slack/PR). positioning.template.md 동봉. settings.json 에 UserPromptSubmit (아침 인사 trigger) + Stop hook (모순 안내) 신설. CLAUDE.md §4 갱신: 8 종 전부 ✅ | skills/{query,morning-brief,evening-reflect,daily-digest}/SKILL.md skills/daily-digest/positioning.template.md .claude/settings.json CLAUDE.md
- 2026-05-18T03:00:00+09:00 | [version] | cc-session | plugin.json + marketplace.json 0.2.0 → 0.3.0 | .claude-plugin/{plugin,marketplace}.json
- 2026-05-18T03:30:00+09:00 | [graph-sync] | cc-session | 실 Neo4j ingest 첫 성공: 38 statements (3 sources + 10 nodes + 25 rels). 3 topic 의 graph_synced_at 갱신 | vault/02_wiki/topics/*.md
- 2026-05-18T03:30:00+09:00 | [graph-query] | cc-session | 실 Cypher 검증: concept_neighbors(GraphRAG)=5+ 결과, orphan_audit=0, causal_path(OpenAI)=6-hop 경로 성공, Anthropic=0(본문 미등장으로 정상) | -
- 2026-05-18T03:30:00+09:00 | [bugfix] | cc-session | v0.3.1: install.sh 의 docker compose 호출에 --env-file $TARGET_DIR/.env 명시 (compose 가 infra/neo4j/ 기준으로 .env 찾던 버그). causal_path.cypher: SOLVES/USES 외 MENTIONS/REFERS_TO 도 fallback (룰베이스 호환). 0.3.0 → 0.3.1 | scripts/install.sh services/graph/templates/causal_path.cypher .claude-plugin/{plugin,marketplace}.json
- 2026-05-18T03:45:00+09:00 | [plugin-install-fix] | cc-session | v0.3.2: 사용자 보고 — Claude Code 2.1.140 에서 source: "." 인식 실패 ("source type your Claude Code version does not support"). 해결: source 를 GitHub object 형식으로 변경 ({"source": "github", "repo": "gaebalai/cc-llm-wiki"}). 0.3.1 → 0.3.2 | .claude-plugin/marketplace.json .claude-plugin/plugin.json
- 2026-05-18T04:00:00+09:00 | [plugin-install-fix] | cc-session | v0.3.3: v0.3.2 도 같은 에러. anthropic-official marketplace 분석 결과 url 형식이 35건으로 최다, github object 는 1건. source 를 url 형식으로 변경 ({"source": "url", "url": "https://github.com/gaebalai/cc-llm-wiki.git"}). sha 핀 없이 main HEAD 자동 추적. 0.3.2 → 0.3.3 | .claude-plugin/marketplace.json .claude-plugin/plugin.json
- 2026-05-18T04:15:00+09:00 | [ssh-setup] | human-via-cc | SSH key (ed25519) 생성 + macOS Keychain 영구 등록 + GitHub 등록 (사용자가 web 또는 gh ssh-key add). 사용자 환경에서 git clone over SSH 가능 | ~/.ssh/id_ed25519
- 2026-05-18T04:30:00+09:00 | [plugin-install-fix] | cc-session | v0.3.4: clone 성공 후 plugin.json validation 3종 에러. 패치: repository object→string, commands/skills 에 ./ prefix + trailing slash. 검증된 형식 (사용자 본인 claudecode-to/harness-edit, gaebalai-marketplace/cc-jarvis) 모방. 0.3.3 → 0.3.4 | .claude-plugin/plugin.json
- 2026-05-18T04:45:00+09:00 | [milestone] | human-via-cc | ✅ plugin install 성공. 4 release (0.3.0→0.3.4) + SSH 등록 거쳐 anthropic plugin marketplace 시스템 호환 달성 | -
- 2026-05-18T05:00:00+09:00 | [plugin-install-fix] | cc-session | v0.3.5: /install 명령 미노출 원인 = commands/skills 가 .claude/ 안에 있어 plugin context 에서 미발견. plugin root 로 git mv. plugin.json commands/skills 필드 제거 (자동 발견). 9 파일 path 참조 갱신 | commands/ skills/ plugin.json + 9 파일
- 2026-05-18T05:15:00+09:00 | [vault-rename] | human-via-cc | Web Clipper URI 충돌 (vault 폴더명 동명) → ~/my-knowledge-base/vault 평탄화. ~/my-knowledge-base 자체가 vault. Obsidian config 갱신 (옛 path 제거, 새 path 등록). 클립 정상 작동 확인 | ~/my-knowledge-base/{01_raw,02_wiki,...}
- 2026-05-18T05:30:00+09:00 | [schema-policy] | cc-session | SCHEMA §3 raw 슬러그 규칙 완화 (영문 강제 → 권장, 한글·공백 허용). lint 항목 8 ERROR → WARN-RAW. 이유: Web Clipper 한글 자료 친화 + 원문 보존 우선. wiki 슬러그는 강제 유지 (wikilink 호환성) | vault/SCHEMA.md skills/lint/SKILL.md
- 2026-05-18T05:45:00+09:00 | [install-flatten] | cc-session | v0.3.6: install.sh VAULT_DIR + VAULT_MODE 자동 감지 (flat vs subdir). copy_templates vault 콘텐츠를 모드별 분기. step1/2/3/7 의 vault path 모두 $VAULT_DIR 사용. flat 모드 (TARGET_DIR/.obsidian 또는 01_raw 존재) 와 subdir 모드 (TARGET_DIR/vault/.obsidian 존재) 양쪽 시뮬 검증 OK | scripts/install.sh
- 2026-05-18T05:45:00+09:00 | [claude-md] | cc-session | §2 권한 매트릭스 path 를 (vault/) 표기로 변경 (flat/subdir 모두 지원). 불변 원칙 본문 갱신 | CLAUDE.md
- 2026-05-18T05:45:00+09:00 | [version] | cc-session | plugin.json/marketplace.json 0.3.5 → 0.3.6 | .claude-plugin/{plugin,marketplace}.json
