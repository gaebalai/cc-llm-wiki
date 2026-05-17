#!/usr/bin/env python3
"""Slack incoming-webhook 게시 유틸 (P4 daily-digest·weekly-lint routine 공용).

사용:
    python scripts/post_slack.py --title "Weekly Lint" --body "ERROR 0, WARN 2"
    python scripts/post_slack.py --title "..." --body-file vault/02_wiki/_lint/2026-05-17.md

환경:
    .env 의 SLACK_WEBHOOK_URL 또는 SLACK_BOT_TOKEN 사용. 둘 다 없으면 dry-run.
    DRY_RUN=1 이면 실제 호출 없이 stdout 만 출력.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path


def load_env(env_path: Path) -> dict[str, str]:
    env: dict[str, str] = {}
    if not env_path.exists():
        return env
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        env[k.strip()] = v.strip().strip('"').strip("'")
    return env


def post(webhook_url: str, payload: dict, timeout: int = 10) -> tuple[int, str]:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        webhook_url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.status, resp.read().decode("utf-8", errors="replace")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--title", required=True, help="메시지 헤더")
    grp = parser.add_mutually_exclusive_group(required=True)
    grp.add_argument("--body", help="메시지 본문 (텍스트)")
    grp.add_argument("--body-file", help="본문을 읽어올 파일 경로")
    parser.add_argument("--channel", default=None, help="채널 override (Webhook 고정 시 무시)")
    parser.add_argument("--env", default=".env", help="환경 변수 파일 경로")
    args = parser.parse_args()

    env = {**os.environ, **load_env(Path(args.env))}
    webhook = env.get("SLACK_WEBHOOK_URL", "").strip()
    dry_run = env.get("DRY_RUN", "1").strip() in ("1", "true", "yes")

    if args.body_file:
        body = Path(args.body_file).read_text(encoding="utf-8")
    else:
        body = args.body or ""

    payload = {
        "text": f"*{args.title}*\n{body}",
    }
    if args.channel:
        payload["channel"] = args.channel

    if not webhook or dry_run:
        reason = "no SLACK_WEBHOOK_URL" if not webhook else "DRY_RUN=1"
        print(f"[dry-run: {reason}]")
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    try:
        status, resp = post(webhook, payload)
    except urllib.error.URLError as e:
        print(f"[error] Slack post failed: {e}", file=sys.stderr)
        return 2

    if status >= 400:
        print(f"[error] Slack returned {status}: {resp}", file=sys.stderr)
        return 3
    print(f"[ok] Slack {status}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
