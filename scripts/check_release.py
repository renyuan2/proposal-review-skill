"""Confirm the checked-out review plugin matches the published main branch."""

import json
import os
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
PLUGIN = Path("plugins/proposal-review")
BRANCH = "refs/heads/main"
REPOSITORY = "renyuan2/proposal-review-skill"
ORIGIN_URLS = {
    f"https://github.com/{REPOSITORY}",
    f"https://github.com/{REPOSITORY}.git",
    f"git@github.com:{REPOSITORY}.git",
    f"ssh://git@github.com/{REPOSITORY}.git",
}


def git(*args):
    return subprocess.run(
        ["git", *args],
        cwd=ROOT,
        env={**os.environ, "GIT_TERMINAL_PROMPT": "0"},
        capture_output=True,
        check=True,
        text=True,
        timeout=20,
    ).stdout.strip()


def main():
    try:
        origin = git("remote", "get-url", "origin")
        if origin not in ORIGIN_URLS:
            raise ValueError(f"当前任务未连接正式仓库 {REPOSITORY}。")
        current = git("rev-parse", "HEAD")
        published, ref = git("ls-remote", "--exit-code", "origin", BRANCH).split()
        if ref != BRANCH:
            raise ValueError("未能确认 GitHub 正式发布分支。")
        if current != published:
            raise ValueError(
                f"当前提交 {current[:8]} 与 GitHub 正式版本 {published[:8]} 不一致。"
            )
        if git("status", "--porcelain", "--", str(PLUGIN)):
            raise ValueError("当前任务中的评测工具含本地改动。请使用全新的云端任务。")
        manifest = json.loads((ROOT / PLUGIN / "plugin.json").read_text(encoding="utf-8"))
    except (subprocess.SubprocessError, OSError):
        print("无法读取 GitHub 正式版本。请检查任务是否已连接私有仓库。", file=sys.stderr)
        return 1
    except ValueError as error:
        print(error, file=sys.stderr)
        return 1

    print(f"已核对 GitHub 正式版本 · 评测工具 v{manifest['version']} · {current[:8]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
