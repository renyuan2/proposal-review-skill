"""Install a Codex skill that reads the current rules from this Git checkout."""

from pathlib import Path
import sys

from check_release import ROOT, check_release


SKILL = ROOT / "plugins/proposal-review/skills/proposal-review/SKILL.md"
CHECKER = ROOT / "scripts/check_release.py"


def install(home):
    launcher = home / ".agents/skills/proposal-review/SKILL.md"
    instructions = f"""---
name: proposal-review
description: 从甲方视角逐页评测空间智能、智慧园区及行政数字化方案，输出可跳转原页的分级建议报告。用于评测方案成稿和汇报前审稿。
---

# 解决方案成果评测

每次评测先用 Python 3 运行以下版本检查脚本，传入 `--update`。路径各作为独立参数，保留路径中的空格。

```text
{CHECKER}
```

成功后，从磁盘读取以下评测规则，按其执行，并把版本检查输出的版本和提交编号加入报告的评测依据。

```text
{SKILL}
```

无法确认 GitHub 最新版本时，说明原因并暂停评测。评测材料和报告保存在使用者的任务文件夹，避免放入工具仓库。
"""
    legacy = home / ".codex/skills/proposal-review/SKILL.md"
    if legacy.exists():
        raise FileExistsError(f"发现原有同名评测工具，请先确认如何保留或迁移：{legacy}")
    launcher.parent.mkdir(parents=True, exist_ok=True)
    try:
        with launcher.open("x", encoding="utf-8") as file:
            file.write(instructions)
    except FileExistsError:
        if launcher.is_symlink() or not launcher.is_file() or launcher.read_text(encoding="utf-8") != instructions:
            raise FileExistsError(f"发现原有同名评测工具，请先确认如何保留或迁移：{launcher}") from None
    return launcher


if __name__ == "__main__":
    if check_release(update=True):
        raise SystemExit(1)
    try:
        path = install(Path.home())
    except OSError as error:
        print(error, file=sys.stderr)
        raise SystemExit(1) from None
    print(f"安装完成。新开一个本机 Codex 对话即可使用 $proposal-review。入口：{path}")
