# GIT_GOVERNANCE — GH Token Broker

本文记录 Git 署名、贡献者身份和 push 前检查的可变政策与证据。`AGENTS.md` 只保留必须立即可见的简要约束。

## AI 署名约定

当前约定：**每次单独询问**。未获当次明确同意，不得在 commit message、trailer 或正文中加入 AI 署名。

初始保守记录：

- 记录日期：2026-11-27
- 触发场景：首次 push 前预防性记录
- 当时扫描结果：检出 0 条 AI 署名
- 初始默认：首次提交不包含 AI 署名

push 前处理规则：

1. 检查待推送提交是否含 `Co-Authored-By`、`Generated with`、AI 工具署名或类似标记。
2. 如果命中且用户未明确知情同意，暂停 push 并询问处置方式。
3. 用户决定改变政策时，更新本节和下方变更日志；不要只改 AGENTS 摘要。

## 贡献者身份约定

当前约定：**每次单独询问**。

允许身份：

- `notebook <tiankongzhise@163.com>`：本地提交身份
- `tiankongzhise <104021016+tiankongzhise@users.noreply.github.com>`：仅允许作为 GitHub 在合并 PR 时自动创建的 merge commit author；不得用作本地普通提交身份

初始保守记录：

- 记录日期：2026-11-27
- 触发场景：首次 push 前预防性记录
- 当时扫描结果：检出 0 个名单外作者
- 初始默认：首次提交使用用户指定身份

push 前处理规则：

1. 检查待推送提交 author name/email。
2. 如果作者不属于允许身份，暂停 push 并询问是否知情、是否允许或是否需要修正。
3. 不擅自修改 git config；确需单次提交身份时必须获得用户明确指示。

## 变更日志

| 日期 | 变更 | 证据 |
|---|---|---|
| 2026-11-27 | 建立初始保守策略：AI 署名和贡献者身份均每次单独询问 | 首次 push 前预防性记录 |
| 2026-11-27 | 将 GitHub PR merge commit 自动作者身份加入允许名单，仅限 merge commit | 用户明确选择“加入允许名单”；本地普通提交身份不变 |

## main 分支保护约束

- 2026-11-27 用户明确要求：禁止直接向远端 `main` push，任何对 `main` 的修改必须通过分支和 Pull Request 合并。
- GitHub 分支保护的实际配置状态见 [PROJECT_STATUS](PROJECT_STATUS.md)；本文件只记录治理约束。
- 修改、绕过或删除 main 保护规则必须另行获得用户明确授权。

## commit message 规范入口

- 2026-11-27 用户指出此前 commit 信息量不足，并要求后续 commit 使用中文。
- 当前规范：Conventional Commits type 前缀保持英文机器可读，摘要和正文必须使用中文；正文必须说明原因/变更/边界并包含 `验证：` 记录。
- 详细规范和示例见 [COMMIT_MESSAGES](COMMIT_MESSAGES.md)；自动检查脚本为 `scripts/check_commit_messages.py`。
- 本规范不改变 AI 署名和贡献者身份政策。
