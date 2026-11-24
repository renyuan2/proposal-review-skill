# 解决方案成果评测

## 安装一次

把下面这段话发给**桌面版 Codex 的本机对话**，让它帮你安装。

> 请通过 HTTPS 从 GitHub 仓库 https://github.com/renyuan2/proposal-review-skill 克隆评测工具到我的用户目录下的 `proposal-review-skill` 文件夹。然后进入仓库，用 Python 3 执行 `scripts/install_local.py`。如果仓库仍是私有，请告诉我如何授权。

安装需要本机具备 Git 和 Python 3。仓库为公开时，安装和检查更新都无需登录 GitHub。也可在终端自行执行：

```sh
git clone https://github.com/renyuan2/proposal-review-skill.git
cd proposal-review-skill
python3 scripts/install_local.py
```

Windows 如果没有 `python3` 命令，可用 `py -3`。

## 日常使用

在新的本机对话中附上方案和适用模板，发送 `$proposal-review 请评测这份方案`。新安装后如果没有看到入口，重启桌面应用。

每次评测先从 GitHub 核对发布版本。本地版本落后时会自动尝试更新，再读取最新评测规则。报告注明实际版本。无法核对最新版本时，Codex 会说明原因并暂停评测。

首次处理 HTML 需要 Node.js、Playwright 和 Chromium。PDF 需要 `pdfplumber`。可让 Codex 优先检查已有环境，按文件格式补齐依赖。客户材料以及生成的报告保存在自己的任务目录。
