# BRANCHING — 分支与文件 Ownership 规则

最近更新：2026-11-27

本文定义分支生命周期、集成顺序和文件 ownership 原则。机器可读 ownership 登记表是 [branch-ownership.json](branch-ownership.json)；本文不复制具体归属清单。

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

## 3. 集成队列

1. 同一时刻只允许一个 feature integration。
2. feature 分支开 integration PR 前必须合并最新 `origin/main`。
3. 一个 feature 合入 main 且 main CI 通过后，其他活跃 feature 分支必须先同步新 main，再继续或发起自己的 integration。
4. 当前队列状态记录在 [PROJECT_STATUS](PROJECT_STATUS.md)；静态 ownership 规则登记在 `branch-ownership.json`。
5. 已验收成果默认应尽快集成进 main；若暂不合入，必须在 PROJECT_STATUS 记录原因和解除条件。

## 4. 文件 ownership 边界

- feature 分支可以继承 main 的文件，但不得独立修改未登记路径。
- 共享治理文件包括 AGENTS、DECISIONS、PROJECT_STATUS、CI/Git 治理、workflow 和仓库脚本；它们不归属长期 feature 分支。
- 新路径若不属于任何已登记 ownership，长期 feature 分支必须先更新 registry 再修改。
- 例外必须有原因和解除条件；集成完成后应清除临时例外。
- 释放 ownership 不等于删除分支；只表示其他分支可按流程接管该路径。

## 5. 自动检查

`python scripts/check_branch_ownership.py` 会：

1. 校验 registry 结构和 active feature ownership 是否重叠。
2. 基于 `origin/main...HEAD` 检查当前分支改动路径。
3. 对 `feat/**`：只允许改动自己登记的路径或登记例外。
4. 对 `chore/**`/`fix/**`：禁止改动 active feature 分支登记路径。

检查失败时不得 push 或合并。该检查是 merge gate，不是对本地编辑能力的绝对限制。
