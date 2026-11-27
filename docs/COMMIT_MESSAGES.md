# COMMIT_MESSAGES — 提交信息规范

最近更新：2026-11-27

本文定义本项目 commit message 的必填结构、语言、信息密度和自动检查边界。目标不是追求格式本身，而是让后续开发者、agent 和发布工具能从历史中理解“为什么改、改了什么、边界是什么、如何验证”。

## 1. 基本格式

本项目继续使用 Conventional Commits 1.0.0 的 type 前缀，但摘要和正文必须使用中文：

```text
<type>(<scope>): 中文摘要，说明结果或意图

中文正文第一段：背景、原因或要解决的问题。

中文正文后续段落：主要变更、行为边界、不做什么、兼容性/迁移影响。

验证：实际运行过的检查；未验证但重要的项目也必须明确说明。
```

- `type` 保持英文机器可读 token：`feat`、`fix`、`docs`、`chore`、`ci`、`test`、`refactor`、`perf`、`build`、`revert`。
- `scope` 可选，使用小写 ASCII，例如 `backend`、`webui`、`ci`、`docs`、`version`。
- 摘要必须包含中文语义，不得超过 72 个字符；不要只写“更新文档”“修复问题”这类空泛表述。
- 摘要结尾不使用句号。

## 2. 正文信息密度

除 GitHub 自动 merge commit 外，非 merge commit 必须有正文。正文至少回答以下问题：

1. **为什么改**：用户要求、bug、风险、治理缺口或技术原因。
2. **改了什么**：列出关键行为或文件级变化，不复制 diff，但要能让人理解意图。
3. **边界/影响**：明确不做什么、是否影响批准基线、是否有迁移/回滚注意事项。
4. **验证**：记录实际运行过的检查。没运行的重要检查不得假装已运行。

小而机械的单行变更也建议写正文；如果确实无法提供这些信息，通常说明它应该和其他逻辑合并，或者根本不是有效变更。

## 3. 决策、CR 与 PR 关联

- 涉及已批准决策时，在正文引用 `D-<id>`，例如 `D-0017`。
- 涉及变更控制时，引用 `CR-<id>`，例如 `CR-0001`。
- 修 bug 时说明触发条件和复现/验证方式。
- 与安全边界有关时，必须说明 secret/token 是否会被打印、持久化或跨进程传递。
- PR 编号通常由 GitHub merge commit 或 PR 页面记录，不强制写进每个本地 commit。

## 4. 禁止事项

1. 不得使用只有 `update`、`fix`、`wip`、`tmp`、`misc` 这类无信息量摘要。
2. 不得把多个无关逻辑塞进一个 commit 来“顺便处理”。
3. 不得伪造验证结果；例如只运行文档检查却写“测试通过”。
4. 不得包含秘密、token、密钥、credential、完整 bearer 值或可认证派生值。
5. 未获当次明确同意，不得加入 AI 署名、AI trailer 或类似标记。
6. 不得用 commit message 替代决策记录；重要决策仍必须写入 `docs/DECISIONS.md` 或 CR。

## 5. 示例

```text
docs: 提前 scoped token 与 grant 的 Phase 2 顺序

记录 CR-0001/D-0017，解决 exec wrapper 和 git credential helper
在缺少 scoped token 时只能交付 parent token 的顺序冲突。

本次调整 Phase 2/3 边界：先实现 client secret 安全配置、scoped
child token、inventory、min_ttl 和最小 grant lifecycle，再接通
exec wrapper 与 git credential helper。明确 parent token 不得注入
子进程或通过 helper 返回，scoped token 不可用时必须失败关闭。

验证：Markdown links、documentation authority、branch ownership、
version check、git diff --check。
```

```text
fix(backend): 避免 refresh 并发导致链状态错乱

在 account-level mutex 内重新读取持久化状态，避免两个进程同时
refresh 后后者覆盖前者的新 refresh token。

该修复只影响 parent token refresh 协调，不改变 scoped token、
grant 或 WebUI 行为；仍不包含真实 GitHub 冒烟验证。

验证：go test ./internal/tokenchain；race spot check。
```

## 6. 自动检查边界

`python scripts/check_commit_messages.py` 检查待集成分支中的非 merge commit：

- header 是否符合允许的 Conventional Commit type。
- 摘要是否包含中文且长度不超过 72 字符。
- 是否存在正文。
- 正文是否至少包含两条非空信息行。
- 正文是否包含 `验证：` 记录。

该检查只能防止结构性空 commit，不能证明正文语义真实或充分。review 时仍必须人工/agent 检查信息质量。GitHub 自动 merge commit 豁免该格式检查。
