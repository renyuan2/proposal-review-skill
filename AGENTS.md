# 解决方案成果评测

收到评测方案的请求时，先在仓库根目录运行 `python3 scripts/check_release.py --update`。它核对本次任务的代码与 GitHub 正式发布分支。成功后，从磁盘重新读取 `plugins/proposal-review/skills/proposal-review/SKILL.md` 并按该版本完成评测。

- 版本检查通过时，将它输出的版本号和提交编号加入报告的「评测依据」。
- 无法访问 GitHub 或仍无法确认版本时，说明具体原因，暂停评测。仓库文件或已有报告中的版本号不足以证明已检查更新。

仅将工具源文件纳入 Git。客户方案、调研、截图和报告放在仓库外的任务文件夹。
