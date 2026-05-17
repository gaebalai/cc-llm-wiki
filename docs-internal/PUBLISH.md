# Plugin 공개 게시 가이드

이 문서는 `cc-llm-wiki` 를 GitHub 공개 리포지토리로 게시하고
Claude Code Plugin Marketplace 로 노출하는 절차다.

**대상**: 저자(소유자) 1인. 일반 사용자 가이드는 [README.md](../README.md) 의 "Claude Code Plugin 으로 사용" 섹션.

---

## 1. GitHub 리포 생성 (web)

1. https://github.com/new 접속
2. Repository name: **`cc-llm-wiki`**
3. Owner: **`gaebalai`**
4. Visibility: **Public** ✅
5. README/.gitignore/license 추가 옵션 **체크 해제** (이미 로컬에 있음 — 충돌 회피)
6. Create repository

생성 후 표시되는 SSH 또는 HTTPS URL 복사. 예:
- SSH: `git@github.com:gaebalai/cc-llm-wiki.git`
- HTTPS: `https://github.com/gaebalai/cc-llm-wiki.git`

## 2. 로컬 → 원격 연결 (저자가 직접 실행)

```bash
cd /Users/gaebalai/Workspace2/cc-llm-wiki

# 원격 추가 (한 번만)
git remote add origin git@github.com:gaebalai/cc-llm-wiki.git
# (HTTPS 면) git remote add origin https://github.com/gaebalai/cc-llm-wiki.git

# 원격 확인
git remote -v

# 최초 push
git push -u origin main

# 첫 release 태그 (semver)
git tag v0.1.0 -m "release: 0.1.0 — Karpathy 원전~Neo4j GraphRAG PoC 통합 풀스택 골격"
git push origin v0.1.0
```

⚠ **push 전 최종 확인**:
- `git ls-files | xargs grep -l 'xox[abeops]-\|sk-[a-zA-Z0-9_-]\{20,\}' 2>/dev/null` → 결과 비어있어야 함
- `git check-ignore .env` → `.gitignore:2:.env` 출력 (안전)
- `.env.example` 의 모든 토큰 값이 빈 placeholder 인지 직접 확인

## 3. 사용자 측 설치 흐름 검증

자신이 다른 디렉터리에서 직접 설치해 본다:

```bash
# 새 Claude Code 세션 (다른 폴더)
cd /tmp/test-cc-llm-wiki
mkdir -p test && cd test
claude
```

세션 안에서:
```
/plugin marketplace add gaebalai/cc-llm-wiki
/plugin install cc-llm-wiki@claudecode-to-marketplace
/install
```

다음 신호로 성공 판단:
- `/plugin list` → `cc-llm-wiki` 가 active
- `/install` 명령이 슬래시 자동완성에 나타남
- `/install --check` 실행 시 7 단계 검사 메시지 출력

## 4. 업데이트 게시 (v0.4.4+ 표준 절차)

```bash
# 1) 변경 작업 (Skill·service·docs 등)

# 2) 버전 bump (3 곳 sync — CI 항목 2 가 교차참조 검증)
$EDITOR .claude-plugin/plugin.json          # .version
$EDITOR .claude-plugin/marketplace.json     # .metadata.version + .plugins[0].version

# 3) CHANGELOG.md 의 [Unreleased] 섹션을 새 버전 섹션으로 변환
$EDITOR CHANGELOG.md
# 형식: ## [0.4.5] — YYYY-MM-DD
#       ### Added / Changed / Fixed / Removed (해당 항목만)

# 4) commit + push (CI 자동 실행, ~10 초)
git add CHANGELOG.md .claude-plugin/plugin.json .claude-plugin/marketplace.json <변경 파일>
git commit -m "[release] v0.4.5 — <한 줄 요약>"
git push origin main

# 5) tag + push
git tag -a v0.4.5 -m "v0.4.5 — <한 줄 요약>"
git push origin v0.4.5

# 6) GitHub Release 생성 (CHANGELOG 섹션을 notes 로)
gh release create v0.4.5 \
  --title "v0.4.5 — <한 줄 요약>" \
  --notes "$(awk '/^## \[0\.4\.5\]/{found=1; print; next} found && /^## \[/{exit} found' CHANGELOG.md)"

# (참고) release 가 published 시간 순으로 Latest 잡혀 의도와 다를 수 있음 → 강제 지정
gh release edit v0.4.5 --latest
```

사용자는:
```
/plugin update cc-llm-wiki@claudecode-to-marketplace
```

### 검증 체크리스트 (push 직전)

- [ ] `jq -r '.version' .claude-plugin/plugin.json` 과 `.plugins[0].version` `.metadata.version` (marketplace) 셋 다 동일
- [ ] `CHANGELOG.md` 에 새 버전 섹션 추가 (Keep a Changelog 1.1.0 형식)
- [ ] `git ls-files | xargs grep -lE 'xox[abeops]-|sk-[a-zA-Z0-9_-]{30,}' 2>/dev/null` → 결과 비어있음
- [ ] CI 통과 (직전 push 의 `gh run list --branch main --limit 1` → `completed success`)

## 5. marketplace 등록 (선택)

Anthropic 공식 디렉터리에 등록하려면 별도 절차 필요 (현재 시점에는 PR 또는 신청 폼).
즉시 사용자에게 노출하려면 본 절차(개인 GitHub repo) 만으로도 충분 —
사용자는 `/plugin marketplace add gaebalai/cc-llm-wiki` 한 줄로 즉시 접근.

## 6. push 후 추가 권장 사항

- GitHub repo Settings:
  - Topics 12 종 (v0.3.10): `anthropic-claude` · `claude-code` · `obsidian` · `neo4j` · `graphrag` · `langchain` · `knowledge-base` · `personal-knowledge-management` · `llm-wiki` · `karpathy` · `context-engineering` · `pkm`
  - About: 한 줄 소개 + plugin marketplace URL
  - Pages: 비활성 (로컬 전용 정책 그대로)
- **GitHub Actions** (✅ v0.3.7+ active — `.github/workflows/ci.yml` 10 항목):
  1. JSON 유효성 (marketplace·plugin·settings)
  2. plugin ↔ marketplace 교차참조 (name·version)
  3. SKILL.md frontmatter 필수 키
  4. Bash syntax (install.sh)
  5. Python compile (ingest_graph·query_graph·post_slack)
  6. install.sh --check step 1
  7. vault lint 10 규칙 (frontmatter·enum·wikilink·duplicate id 등)
  8. 시크릿 패턴 grep (xox/sk-/bot)
  9. .env gitignore 보호
  10. extraction eval rule vs gold (P/R/F1)

## 7. 미해결 항목 (역사 기록)

원래 두 항목은 v0.2.0 의 `install.sh` 패치로 해결됨:

- ~~plugin 활성 시 settings.json hooks 가 자동 로드 안 됨~~ → ✅ v0.2.0: `install.sh merge_hooks()` 가 사용자 `.claude/settings.json` 에 안전 머지
- ~~plugin 디렉터리에서 `/install` 실행 시 vault/ 가 plugin 내부에 생성~~ → ✅ v0.2.0: `PLUGIN_INSTALL` 환경변수 자동 감지, 사용자 cwd 가 TARGET_DIR

### 현재 알려진 한계

- **5 routines 의 cron 등록은 사용자 환경마다 1 회 수동** (`/schedule create`). plugin install 시 자동 등록 안 됨 (Claude Code Plugin spec 에 routine schedule 자동 등록 hook 없음)
- **GitHub Releases 누락 위험**: v0.3.3~v0.4.3 가 release 누락된 채 12 release 가 누적되었던 사례 (v0.4.4 에 일괄 backfill). §4 의 6 번 단계 (gh release create) 를 매 release 마다 빠뜨리지 말 것.
