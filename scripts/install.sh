#!/usr/bin/env bash
# cc-llm-wiki — 원스톱 설치 스크립트
#
# 사용:
#   bash scripts/install.sh           # 전체 진행 (idempotent)
#   bash scripts/install.sh --check   # 환경 검사만 (변경 없음)
#   bash scripts/install.sh --step N  # 특정 step 만 실행 (1~7)
#
# 7 단계:
#   1. macOS/명령어 사전 검사
#   2. Obsidian 설치 확인 (+ Vault 안내)
#   3. Dataview 플러그인 + status.md 안내
#   4. Docker 확인 + Neo4j compose up
#   5. .env 생성 + NEO4J_PASSWORD 보장
#   6. Slack 토큰 안내 (수동 입력 권장)
#   7. weekly-review 슬롯 안내

set -euo pipefail

# ───── 색상 ─────
if [ -t 1 ]; then
  C_RESET=$'\033[0m' C_BOLD=$'\033[1m' C_DIM=$'\033[2m'
  C_GREEN=$'\033[32m' C_YELLOW=$'\033[33m' C_RED=$'\033[31m' C_BLUE=$'\033[34m'
else
  C_RESET= C_BOLD= C_DIM= C_GREEN= C_YELLOW= C_RED= C_BLUE=
fi

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

# ───── 인자 파싱 ─────
MODE="full"
ONLY_STEP=""
while [ $# -gt 0 ]; do
  case "$1" in
    --check) MODE="check" ;;
    --step) ONLY_STEP="$2"; shift ;;
    -h|--help) sed -n '1,16p' "$0"; exit 0 ;;
    *) echo "${C_RED}unknown arg: $1${C_RESET}" >&2; exit 1 ;;
  esac
  shift
done

ok()    { echo "${C_GREEN}✓${C_RESET} $*"; }
warn()  { echo "${C_YELLOW}⚠${C_RESET} $*"; }
fail()  { echo "${C_RED}✗${C_RESET} $*" >&2; }
info()  { echo "${C_BLUE}ℹ${C_RESET} $*"; }
hdr()   { echo; echo "${C_BOLD}── $* ──${C_RESET}"; }
prompt(){ printf "${C_YELLOW}?${C_RESET} %s " "$*"; }

run_step() {
  local n="$1"
  [ -z "$ONLY_STEP" ] && return 0
  [ "$ONLY_STEP" = "$n" ] && return 0
  return 1
}

# ───── 1. 사전 검사 ─────
step1_precheck() {
  hdr "STEP 1: 환경 사전 검사"

  case "$(uname -s)" in
    Darwin) ok "macOS 감지" ;;
    Linux)  warn "Linux 감지 — Obsidian/Docker 설치 명령은 macOS 기준입니다. 수동 조정 필요" ;;
    *)      fail "지원 OS 아님: $(uname -s)"; return 1 ;;
  esac

  for cmd in git python3 bash; do
    if command -v "$cmd" >/dev/null 2>&1; then
      ok "$cmd: $(command -v "$cmd")"
    else
      fail "$cmd 없음 — 설치 후 재시도"
      return 1
    fi
  done

  if command -v brew >/dev/null 2>&1; then
    ok "Homebrew: $(brew --version | head -1)"
  else
    warn "Homebrew 없음 — 자동 설치 안내만 가능 (https://brew.sh)"
  fi

  ok "git repo: $(git rev-parse --is-inside-work-tree 2>/dev/null || echo NO)"
}

# ───── 2. Obsidian + Vault ─────
step2_obsidian() {
  hdr "STEP 2: Obsidian 확인 + Vault 안내"

  local app_path="/Applications/Obsidian.app"
  if [ -d "$app_path" ]; then
    ok "Obsidian 설치 확인: $app_path"
  else
    warn "Obsidian 미설치"
    if [ "$MODE" = "check" ]; then
      info "설치 명령: brew install --cask obsidian"
      return 0
    fi
    if command -v brew >/dev/null 2>&1; then
      prompt "Homebrew 로 Obsidian 설치할까요? [y/N]"
      read -r ans || ans="n"
      case "$ans" in
        y|Y)
          brew install --cask obsidian || { fail "Obsidian 설치 실패"; return 1; }
          ok "Obsidian 설치 완료"
          ;;
        *) warn "건너뜀. 수동 설치: brew install --cask obsidian"; return 0 ;;
      esac
    else
      warn "수동 설치 필요: https://obsidian.md/download"
      return 0
    fi
  fi

  info "Vault 폴더: $REPO_ROOT/vault/"
  if [ "$MODE" != "check" ]; then
    prompt "Obsidian 으로 vault 열까요? (URI scheme 호출) [y/N]"
    read -r ans || ans="n"
    case "$ans" in
      y|Y) open "obsidian://open?path=$(python3 -c "import urllib.parse,sys; print(urllib.parse.quote(sys.argv[1]))" "$REPO_ROOT/vault")" && ok "Obsidian 열기 요청" || warn "URI 열기 실패 (직접 열어주세요)" ;;
      *)   info "수동: Obsidian → Open folder as vault → $REPO_ROOT/vault" ;;
    esac
  fi

  info "Obsidian 설정 권장:"
  info "  • Settings → Files & Links → Excluded files: plans/, .claude/queue/"
  info "  • Settings → Editor → Strict line breaks: ON (markdown 호환)"
}

# ───── 3. Dataview + status.md ─────
step3_dataview() {
  hdr "STEP 3: Dataview 플러그인 + status.md 안내"

  info "Obsidian 내부에서 수동 설치 (URI 자동화 안 됨):"
  info "  1) Settings → Community plugins → Turn on community plugins"
  info "  2) Browse → 검색 'Dataview' → Install → Enable"
  info "  3) 보드 열기: vault/dashboards/status.md"

  if [ "$MODE" != "check" ]; then
    prompt "status.md 를 Obsidian 에서 열까요? [y/N]"
    read -r ans || ans="n"
    case "$ans" in
      y|Y) open "obsidian://open?vault=vault&file=dashboards/status.md" 2>/dev/null \
              || open "vault/dashboards/status.md" \
              || warn "열기 실패 (직접 열기)"
           ok "status.md 열기 요청" ;;
      *)   info "수동: Obsidian 사이드바에서 dashboards/status.md 클릭" ;;
    esac
  fi

  local fpath="vault/dashboards/status.md"
  [ -f "$fpath" ] && ok "$fpath 존재" || fail "$fpath 누락 — git 상태 확인"
}

# ───── 4. Docker + Neo4j compose ─────
step4_docker_neo4j() {
  hdr "STEP 4: Docker 확인 + Neo4j 컨테이너 기동"

  if ! command -v docker >/dev/null 2>&1; then
    warn "docker 없음"
    if [ "$MODE" = "check" ]; then
      info "설치 명령: brew install --cask docker"
      return 0
    fi
    if command -v brew >/dev/null 2>&1; then
      prompt "Docker Desktop 설치할까요? [y/N]"
      read -r ans || ans="n"
      case "$ans" in
        y|Y) brew install --cask docker || { fail "Docker 설치 실패"; return 1; }
             ok "Docker Desktop 설치 완료. /Applications/Docker.app 을 한 번 실행해 권한 부여 후 재시도" ;;
        *) warn "건너뜀. 수동: brew install --cask docker"; return 0 ;;
      esac
    fi
    return 0
  fi

  ok "docker: $(docker --version)"

  if ! docker info >/dev/null 2>&1; then
    warn "Docker daemon 미실행 — Docker Desktop 을 켜주세요"
    if [ "$MODE" != "check" ]; then
      info "Applications/Docker.app 실행 또는: open -a Docker"
      prompt "지금 Docker 를 열까요? [y/N]"
      read -r ans || ans="n"
      case "$ans" in
        y|Y) open -a Docker || warn "열기 실패"
             info "Docker daemon 기동 대기 (최대 60초)..."
             for i in $(seq 1 30); do
               docker info >/dev/null 2>&1 && { ok "Docker 준비 완료"; break; }
               sleep 2
             done
             docker info >/dev/null 2>&1 || { fail "Docker 기동 안 됨. 수동으로 켜고 step 4 재시도"; return 1; } ;;
        *) warn "Docker 띄운 뒤 다시: bash scripts/install.sh --step 4"; return 0 ;;
      esac
    else
      return 0
    fi
  fi
  ok "Docker daemon 실행 중"

  local compose_file="infra/neo4j/docker-compose.yml"
  [ -f "$compose_file" ] || { fail "$compose_file 누락"; return 1; }

  # .env NEO4J_PASSWORD 확인은 step 5 가 먼저 보장. 여기는 .env 있다고 가정.
  if [ ! -f .env ]; then
    warn ".env 없음 — step 5 먼저 실행 권장 (skip)"
    return 0
  fi
  # shellcheck disable=SC1091
  set -a; . ./.env; set +a
  if [ -z "${NEO4J_PASSWORD:-}" ]; then
    fail "NEO4J_PASSWORD 비어 있음 — .env 채운 뒤 재시도"
    return 1
  fi

  if [ "$MODE" = "check" ]; then
    info "다음 명령으로 기동: docker compose -f $compose_file up -d"
    return 0
  fi

  info "Neo4j 컨테이너 기동..."
  docker compose -f "$compose_file" up -d || { fail "compose up 실패"; return 1; }

  info "Neo4j Browser 준비 대기 (최대 60초)..."
  for i in $(seq 1 30); do
    if curl -s -o /dev/null -w "%{http_code}" http://localhost:7474 2>/dev/null | grep -q 200; then
      ok "Neo4j Browser 준비 완료: http://localhost:7474"
      info "  로그인: neo4j / \$NEO4J_PASSWORD (.env)"
      return 0
    fi
    sleep 2
  done
  warn "Neo4j 준비 안 됨 (timeout). 컨테이너 로그 확인: docker compose -f $compose_file logs neo4j"
}

# ───── 5. .env 생성 + NEO4J_PASSWORD 보장 ─────
step5_env() {
  hdr "STEP 5: .env 생성 + NEO4J_PASSWORD 확인"

  if [ ! -f .env ]; then
    if [ "$MODE" = "check" ]; then
      info "생성 예정: cp .env.example .env"
      return 0
    fi
    cp .env.example .env
    ok ".env 신규 생성 (placeholder 만)"
  else
    ok ".env 이미 존재 — 보존"
  fi

  # NEO4J_PASSWORD 가 비어 있으면 자동 생성 제안
  # shellcheck disable=SC1091
  set -a; . ./.env; set +a
  if [ -z "${NEO4J_PASSWORD:-}" ]; then
    if [ "$MODE" = "check" ]; then
      warn "NEO4J_PASSWORD 비어 있음 — 채워야 step 4 진행 가능"
      return 0
    fi
    local generated
    generated="$(python3 -c 'import secrets; print(secrets.token_urlsafe(16))')"
    prompt "NEO4J_PASSWORD 자동 생성값 사용? ($generated) [Y/n]"
    read -r ans || ans="y"
    case "$ans" in
      n|N) info "직접 .env 편집 후 재시도"; return 0 ;;
      *)   # macOS sed in-place
           if [[ "$(uname -s)" == "Darwin" ]]; then
             sed -i '' "s|^NEO4J_PASSWORD=.*|NEO4J_PASSWORD=$generated|" .env
           else
             sed -i "s|^NEO4J_PASSWORD=.*|NEO4J_PASSWORD=$generated|" .env
           fi
           ok "NEO4J_PASSWORD 설정 완료 (.env)" ;;
    esac
  else
    ok "NEO4J_PASSWORD 이미 설정됨 (masked)"
  fi

  # .env 가 .gitignore 에 있는지 보호 확인
  if git check-ignore .env >/dev/null 2>&1; then
    ok ".env 는 .gitignore 처리됨 (안전)"
  else
    fail ".env 가 git 에 노출될 수 있음 — .gitignore 확인 필요!"
    return 1
  fi
}

# ───── 6. Slack 토큰 안내 ─────
step6_slack() {
  hdr "STEP 6: Slack Webhook 토큰 안내 (선택)"

  info "Slack 알림은 옵션입니다. 안 채우면 자동 dry-run."
  info ""
  info "토큰 발급 절차:"
  info "  1) https://api.slack.com/apps → Create New App → From scratch"
  info "  2) Incoming Webhooks → Activate → Add New Webhook to Workspace"
  info "  3) 채널 선택 → 발급된 URL 복사"
  info "     (또는 OAuth Bot Token 이 필요하면 OAuth & Permissions → chat:write)"
  info ""
  info ".env 에 직접 붙여넣기 (터미널 history 안 남기려면 에디터로):"
  info "  ${C_DIM}\$EDITOR .env${C_RESET}   ← SLACK_WEBHOOK_URL=... 채우기"
  info ""

  # shellcheck disable=SC1091
  set -a; . ./.env 2>/dev/null || true; set +a
  if [ -n "${SLACK_WEBHOOK_URL:-}" ]; then
    ok "SLACK_WEBHOOK_URL 이미 설정됨 (masked)"
    if [ "$MODE" != "check" ]; then
      prompt "dry-run 으로 1건 보낼까요? [y/N]"
      read -r ans || ans="n"
      case "$ans" in
        y|Y) DRY_RUN=1 python3 scripts/post_slack.py --title "[install.sh] dry-run check" --body "$(date)" --env .env || warn "dry-run 실패" ;;
      esac
    fi
  else
    warn "SLACK_WEBHOOK_URL 미설정 — 모든 Slack 호출은 dry-run"
  fi
}

# ───── 7. weekly-review 안내 ─────
step7_weekly_review() {
  hdr "STEP 7: weekly-review 슬롯 + 운영 시작 안내"

  info "활성 routine:"
  info "  • weekly-lint   매주 일 06:00 KST  — lint Skill 자동 실행"
  info "  • weekly-review 매주 일 21:00 KST  — 사람 회고 슬롯"
  info ""
  info "회고 페이지: vault/02_wiki/self/llm-wiki-origins.md"
  info "  → 운영 중 발견한 결정·후회·재평가를 timestamp 와 함께 append"
  info ""
  info "수동 명령 (Claude Code 세션):"
  info "  /ingest <vault/01_raw/path>      raw → draft"
  info "  /compile <vault/02_wiki/_drafts/...>  draft → topics (lint 게이트)"
  info "  /lint                              전체 정합성 검사"
  info "  /graph-sync --queue                 hook 큐 일괄 동기"
  info ""
  info "Neo4j 실 ingest (Docker 가동 상태에서):"
  info "  pip install neo4j"
  info "  DRY_RUN=0 python3 services/graph/ingest_graph.py --all --env .env"
  info "  python3 services/graph/query_graph.py causal_path --param company_canonical=Anthropic --env .env"
  info ""
  info "운영 데이터:"
  info "  현재 topics: $(find vault/02_wiki/topics -name '*.md' 2>/dev/null | wc -l | tr -d ' ')"
  info "  현재 raw   : $(find vault/01_raw -name '*.md' 2>/dev/null | wc -l | tr -d ' ')"
  info ""
  ok "설치 완료. README.md 와 CLAUDE.md 도 한 번 훑어 주세요."
}

# ───── 메인 ─────
echo "${C_BOLD}cc-llm-wiki installer${C_RESET}"
[ "$MODE" = "check" ] && info "${C_DIM}--check 모드: 변경 없음, 검사만${C_RESET}"

if ! run_step 1 || ! step1_precheck; then [ -z "$ONLY_STEP" ] && exit 1; fi
run_step 2 && step2_obsidian || true
run_step 3 && step3_dataview || true
# 5 를 4 보다 먼저 (NEO4J_PASSWORD 가 4 의 prerequisite)
run_step 5 && step5_env || true
run_step 4 && step4_docker_neo4j || true
run_step 6 && step6_slack || true
run_step 7 && step7_weekly_review || true

echo
ok "${C_BOLD}installer 종료${C_RESET}"
