# BRANCHING — 分支与文件 Ownership 规则

最近更新：2026-11-27

本文定义分支生命周期、集成顺序、merged branch 清理和文件 ownership 原则。机器可读 ownership 登记表是 [branch-ownership.json](branch-ownership.json)；本文不复制具体归属清单。

## 1. 核心原则

1. `main` 是唯一集成交汇点；feature 分支不直接互相 merge。
2. feature 分支通过 merge 最新 `main` 间接获得其他分支已集成进度。
3. 某一时刻，同一路径最多只有一个长期 feature 分支拥有独立修改权。
4. 未分配给 feature 分支的路径默认归 main/governance 流程；只能在短生命周期 `chore/**`、`fix/**` 或明确授权的 docs/ci 分支中修改。
5. 所有权登记不能阻止本地编辑，但越权 diff 会被本地/CI 检查拦截，不能合并进 `main`。
6. ownership 的创建、转移、释放和例外必须写入 `branch-ownership.json`；禁止只靠口头约定。

## 2. 分支类型

| 类型 | 用途 | 修改权规则 |
|---|---|---|
| `main` | 受保护集成交汇点 | 不直接 push；只通过 PR 集成 |
| `feat/**` | 长期或阶段级 feature 分支 | 必须在 `branch-ownership.json` 登记；只能独立修改登记路径 |
| `chore/**` | 短生命周期治理/维护 PR 分支 | 不得修改 active feature 分支 ownership 路径 |
| `fix/**` | 短生命周期修复 PR 分支 | 不得修改 active feature 分支 ownership 路径 |

## 3. 分支状态与生命周期

`branch-ownership.json` 中的长期 feature 分支使用以下状态：

| 状态 | 含义 | 是否拥有写入权 |
|---|---|---|
| `active` | 正在开发或等待 integration | 是，仅限登记路径 |
| `integrated` | 成果已经合入 main；分支仅为历史/回退引用或用户明确要求暂存 | 否 |
| `inactive` | 暂停开发；恢复前必须通过治理变更重新设为 active | 否 |

## 4. 集成队列

1. 同一时刻只允许一个 feature integration。
2. feature 分支开 integration PR 前必须合并最新 `origin/main`。
3. 一个 feature 合入 main 且 main CI 通过后，其他活跃 feature 分支必须先同步新 main，再继续或发起自己的 integration。
4. 当前队列状态记录在 [PROJECT_STATUS](PROJECT_STATUS.md)；静态 ownership 规则登记在 `branch-ownership.json`。
5. 已验收成果默认应尽快集成进 main；若暂不合入，必须在 PROJECT_STATUS 记录原因和解除条件。

## 5. open main PR 阻塞门禁

1. 对任何 `feat/**` 分支，只要 GitHub 上存在其他尚未关闭、base 为 `main` 的 open PR，就不得继续新增 feature 工作。必须先处理该 PR：合并或关闭；若合并，还需等待 main CI 通过并把最新 `main` 同步进 feature 分支后才能继续。
2. 当前 feature 分支自己的 integration PR 不阻塞自己，因为更新该分支、修复 CI 和响应 review 都是在处理这个 integration。该 PR 仍会阻塞其他 feature 分支。
3. base 不是 `main` 的 PR 不触发该门禁；例如子代理向 feature 分支提交的局部实现 PR 不需要阻塞其他 feature 工作。
4. 该规则不按 PR 内容分类，也不要求判断 PR 是否“治理性”。任何 open main PR 都默认阻塞 feature 新工作；若 PR 已过时，应关闭而不是绕过。
5. 该门禁用 GitHub 当前 open PR 状态作为输入，因此能覆盖“main 尚未前进但规则/需求 PR 已悬空”的场景；仅检查 Git 历史的 freshness 规则不能覆盖该场景。
6. `origin/main` 必须是活跃 feature 分支 HEAD 的 ancestor。main 前进后，feature 分支必须先同步，再 push、开 PR 或继续实现。

## 6. 文件 ownership 边界

- feature 分支可以继承 main 的文件，但不得独立修改未登记路径。
- 共享治理文件包括 AGENTS、DECISIONS、PROJECT_STATUS、CI/Git 治理、workflow 和仓库脚本；它们不归属长期 feature 分支。
- 新路径若不属于任何已登记 ownership，长期 feature 分支必须先更新 registry 再修改。
- 例外必须有原因和解除条件；集成完成后应清除临时例外。
- 释放 ownership 不等于删除分支；只表示其他分支可按流程接管该路径。

## 7. merged branch 清理

1. 短生命周期 `chore/**`、`fix/**`、docs/ci/release prep 分支在 PR 合并后必须及时删除；默认在确认 merge 成功后删除远端分支，并在本地同步 main 后删除本地分支。若必须等待 main CI，应在 main CI 通过后立即删除，不得长期堆积。
2. 已合并短分支不得复用来提交新工作；新工作必须创建新分支。
3. 长期 `feat/**` 分支在阶段成果最终集成后默认也应删除。只有用户明确要求保留时才可以暂存；暂存期间必须在 registry 标记为 `integrated` 或 `inactive`，不再拥有写入权。
4. 删除任何分支前必须确认其 tip 已合并进 `origin/main` 或没有独有提交；不得删除仍有未合并工作的分支。远端删除属于不可逆分支操作，必须获得用户明确确认。
5. 删除分支不会删除已经合并进 main 的提交；cleanup 的目的是减少分支命名空间和所有权歧义，不是改写历史。
6. branch cleanup 结果应同步到 PROJECT_STATUS；若保留已合并 feature 分支，必须记录保留原因。

## 8. 自动检查

`python scripts/check_branch_ownership.py` 会：

1. 校验 registry 结构和 active feature ownership 是否重叠。
2. 基于 `origin/main...HEAD` 检查当前分支改动路径。
3. 对 `feat/**`：只允许改动自己登记的路径或登记例外，并要求 `origin/main` 是 HEAD 的 ancestor。
4. 对 `chore/**`/`fix/**`：禁止改动 active feature 分支登记路径。

`python scripts/check_main_pr_gate.py` 会：

1. 只对 `feat/**` 分支生效。
2. 查询 GitHub 当前 open PRs。
3. 若存在其他 base 为 `main` 的 open PR，则检查失败。
4. 当前 feature 分支自己的 main integration PR 会被排除；base 不是 `main` 的 PR 会被忽略。
5. CI 中无法查询 GitHub PR 状态时 fail closed；本地网络不可用时只警告，最终仍以 CI 为准。

检查失败时不得 push 或合并。该检查是 merge gate，不是对本地编辑能力的绝对限制。
