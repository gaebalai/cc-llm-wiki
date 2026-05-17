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
/plugin install cc-llm-wiki@cc-llm-wiki
/install
```

다음 신호로 성공 판단:
- `/plugin list` → `cc-llm-wiki` 가 active
- `/install` 명령이 슬래시 자동완성에 나타남
- `/install --check` 실행 시 7 단계 검사 메시지 출력

## 4. 업데이트 게시

```bash
# 변경 작업 후
$EDITOR .claude-plugin/{plugin,marketplace}.json  # version 두 곳 모두 bump

git add -A
git commit -m "[release] 0.2.0: <변경 요약>"
git tag v0.2.0 -m "release: 0.2.0 — ..."
git push origin main --tags
```

사용자는:
```
/plugin update cc-llm-wiki@cc-llm-wiki
```

## 5. marketplace 등록 (선택)

Anthropic 공식 디렉터리에 등록하려면 별도 절차 필요 (현재 시점에는 PR 또는 신청 폼).
즉시 사용자에게 노출하려면 본 절차(개인 GitHub repo) 만으로도 충분 —
사용자는 `/plugin marketplace add gaebalai/cc-llm-wiki` 한 줄로 즉시 접근.

## 6. push 후 추가 권장 사항

- GitHub repo Settings:
  - Topics 추가: `claude-code`, `obsidian`, `neo4j`, `graphrag`, `pkm`, `knowledge-base`
  - About: 한 줄 소개 + plugin marketplace URL
  - Pages: 비활성 (로컬 전용 정책 그대로)
- GitHub Actions (선택, 향후):
  - JSON 유효성 검사 (marketplace.json/plugin.json)
  - SKILL.md frontmatter 검증
  - install.sh shellcheck

## 7. 미해결 항목

- plugin 활성 시 settings.json 의 hooks (raw 보호 등) 가 사용자 환경에 자동 로드되지 않음.
  `/install` 명령이 사용자 `.claude/settings.json` 에 hooks 를 머지하는 흐름을 추가 필요 (다음 release)
- plugin 디렉터리에서 `/install` 실행 시 vault/ 가 plugin 내부에 생성되는 동작 — 사용자 cwd 기준으로 셋업되도록 install.sh 조정 필요
