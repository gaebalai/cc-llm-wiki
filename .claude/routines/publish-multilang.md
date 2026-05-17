---
name: publish-multilang
cron: "0 9 * * *"             # 매일 09:00 KST (daily-digest 2h 뒤)
timezone: Asia/Seoul
status: dry-run                # publish Skill 본체 작성 전까지 dry-run
phase: P4 (Skill 본체 P4+ 후속)
skills: [publish]
mcp: [github]
env_required: [CLOUDFLARE_API_TOKEN, CLOUDFLARE_ACCOUNT_ID]
---

# Routine: publish-multilang

매일 09:00 KST 에 `vault/02_wiki/topics/` 에서 `status: published` 페이지를 골라
ko/en/ja 다국어 HTML 로 변환해 Cloudflare Pages 에 배포한다.

## 현재 상태 (2026-05-17)

- `publish` Skill 본체 **미작성**. 본 routine 은 명세만 존재.
- Cloudflare 토큰 없음 → dry-run 으로만 동작.
- 활성화 조건:
  1. `.claude/skills/publish/SKILL.md` 작성
  2. `wrangler` CLI 설치 + `cloudflared` 인증
  3. Cloudflare Pages 프로젝트 생성 + `.env` 에 토큰 채우기

## 트리거 조건

- `vault/02_wiki/topics/` 중 frontmatter `status: published` 가 **신규로 1개 이상** 있을 때만 동작
- `status: reviewed` 만 있고 `published` 가 없으면 skip

## 실행 절차 (P4+ 후속에서 구현)

1. `Skill: publish` 호출
   - locale 순서: ko (원본) → en (자동 번역) → ja (자동 번역)
   - 각 locale subagent 병렬 (3개 Explore subagent)
2. 마크다운 → HTML 변환 (Hugo 또는 자체 변환기)
3. `dist/i18n/{ko,en,ja}/<slug>/index.html` 생성
4. Cloudflare Pages 배포:
   ```bash
   npx wrangler pages deploy dist/ --project-name=cc-llm-wiki
   ```
5. 브랜치 `auto-publish/YYYY-MM-DDTHHMM-<slug>` → PR → squash merge

## 다국어 frontmatter 파생

- 원본: `locale: ko`
- 파생본: 같은 `id`, `locale: en` / `locale: ja`, `sources` 에 원본 추가
- 파생본은 `dist/` 에만 존재하고 `vault/` 에는 저장 안 함 (vault 비대화 방지)

## 미해결

- 번역 품질 게이트 (BLEU? back-translation?) — 첫 1주 실측 후 결정
- 부분 게시 vs 전체 게시 (한 토픽 변경 시 그것만 vs 전체 재빌드)
