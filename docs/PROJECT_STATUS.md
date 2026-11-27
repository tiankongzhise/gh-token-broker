# PROJECT_STATUS — GH Token Broker

本文是项目可变状态的当前事实源：阶段、批准、worktree、验证结果和未决事项都记录在这里。`AGENTS.md` 只保存框架规则和文档地图。

最近更新：2026-11-27

## 1. 当前快照

| 字段 | 当前值 | 证据/备注 |
|---|---|---|
| 当前阶段 | 发现/需求/架构文档已形成；用户已授权并行推进 WebUI 低保真确认与后端核心工作 | 2026-11-27 用户指示“开 worktree……一个 worktree 与我确认低保真……一个做后端核心” |
| 批准状态 | **有限授权，不是完整产品基线批准** | 授权并行推进 A 低保真和后端核心；不视为高保真、Demo、完整后端、raw token 策略或 WebUI 技术栈批准 |
| 后端核心解释 | 已确认采用保守解释：按 [DEVELOPMENT](DEVELOPMENT.md) Phase 1 的核心 token chain POC 边界执行 | 2026-11-27 用户确认“采取保守解释”；不自动包含 MCP、WebUI、scoped token、多 agent policy |
| 产品实现状态 | 尚未开始；当前主 worktree 正在进行文档治理/结构修正 | 本文件创建时无产品代码 |
| 许可证 | LGPL 2.1 已由用户指定；仓库按 `LGPL-2.1-only` 记录 | 用户原话为“本项目使用 LGPL 2.1 许可”；only/or-later 精确语义仍需确认，见 [DECISIONS](DECISIONS.md#d-0001-license-lgpl-21) |
| secret store MVP | **已批准**：加密 SQLite + Windows Credential Manager 保存 master key | 2026-11-27 用户批准 D-0002；见 [DECISIONS](DECISIONS.md#d-0002-secret-store-mvp) |
| 当前审核门 | 两项并行工作可执行；许可证精确语义待选择 | secret store 与后端 POC 保守范围已确认；文档治理基线已提交到本地 main |

## 2. 批准与授权记录

| 日期 | 用户授权/决定 | 适用范围 | 不构成对什么事项的批准 |
|---|---|---|---|
| 2026-11-27 | “本项目使用 LGPL 2.1 许可” | 许可证族与版本 2.1 | 不自动明确 `only` vs `or-later` |
| 2026-11-27 | 开两个 worktree：一个前端低保真确认，一个后端核心 | 并行工作组织方式 | 不批准完整后端、MCP、WebUI 实现、scoped token 或 raw token 策略 |
| 2026-11-27 | 批准 D-0002 secret store MVP | 加密 SQLite + master key in Windows Credential Manager | 不批准跳过 AEAD/key rotation/恢复设计要求 |
| 2026-11-27 | “采取保守解释” | 后端核心按 Phase 1 core token chain POC | 不扩展到 MCP、WebUI、scoped token、多 agent policy |
| 2026-11-27 | 允许 commit | 授权创建本地 git commit | 不授权 push、强推、改写历史或添加 AI 署名 |

没有任何记录表明以下内容已批准：完整 PRD/架构基线、WebUI 技术栈、高保真设计、Demo、raw token 兼容模式、GitHub Enterprise 优先级、完整发布流程。

## 3. Worktree 与修改边界

| 工作流 | 路径 | 分支 | 允许修改/目标 | 禁止事项 |
|---|---|---|---|---|
| 主文档/治理 | `E:\github\gh-token-broker` | `main` | 根文档、`docs/`、`scripts/check_secrets.py`、`.gitignore`、许可证与本阶段用户明确要求的文档治理 | 不开始产品实现 |
| WebUI 低保真 | `E:\github\gh-token-broker-webui` | `feat/webui-wireframes` | `design/wireframes/`、`docs/WIREFRAMES.md` 及低保真所需文档索引 | 不定最终视觉、不实现后端、不改后端核心文件 |
| 后端核心 | `E:\github\gh-token-broker-backend` | `feat/backend-core` | 按 Phase 1：Go module、配置、secret store 抽象/实现、device flow、refresh chain、mock GitHub 单元测试 | 不做 MCP/WebUI/scoped token/多 agent policy；不返回 raw token 给模型上下文 |

注意：两个工作流 worktree 创建时基于 `main` 的 commit `c55ea97`；2026-11-27 文档治理基线提交后，两个分支已 fast-forward 到同一文档基线。后续实时分支状态以 `git worktree list` 为准。

## 4. 未决事项

按优先级排序：

1. **LGPL 精确 SPDX**：`LGPL-2.1-only` 还是 `LGPL-2.1-or-later`。
2. scoped token 父/子失效语义在目标 GitHub App 上的实测结果。
3. WebUI 技术栈与页面范围。
4. raw token 兼容模式是否默认存在，还是仅编译/配置为高级模式。
5. GitHub Enterprise host 支持优先级。
6. operation-only MCP 是否作为第一交付通道。
7. SQLite 驱动与 schema migration 方案。

## 5. 当前验证状态

| 用途 | 工作目录与命令 | 状态 | 最近结果 |
|---|---|---|---|
| 秘密扫描 | 仓库根：`python scripts/check_secrets.py` | 已配置；每次 push 前必须运行 | 2026-11-27 本轮文档修改后通过 |
| 启动 | 未配置 | 无产品实现 | 不适用 |
| 格式/lint/类型检查 | 未配置 | 无产品实现 | 未运行 |
| 测试/构建 | 未配置 | 无产品实现 | 未运行 |

## 6. 角色与委派状态

当前会话已知通用子代理类型为 `subagent_explore` 与 `subagent_general`；没有发现可直接调用的 agency-agents 命名角色。后续需要委派时必须重新核对运行时能力，不能把角色库文件当作可调用事实。

| 阶段职责 | 请求角色完整名 | 当前运行时实际可用名 | 状态 |
|---|---|---|---|
| 需求/产品 | Product Manager | 当前会话未可用 | 未委派 |
| 架构 | Software Architect | 当前会话未可用 | 未委派 |
| 实现 | 匹配 Go/Windows 的实现角色 | 当前会话未可用 | 后端 POC 开始前需重新核对 |
| 审查 | Code Reviewer / Reality Checker | 当前会话未可用 | 到验证阶段再核对 |

## 7. 状态变更日志

| 日期 | 变更 | 记录 |
|---|---|---|
| 2026-11-27 | 初始化项目文档和 secret scan baseline | commit `c55ea97` |
| 2026-11-27 | 用户指定 LGPL 2.1、要求并行 worktree、要求审计文档并重构 AGENTS 为文档地图 | 本轮文档治理变更 |
| 2026-11-27 | 用户批准 D-0002、确认后端核心保守解释为 Phase 1，并允许创建本地 commit | 并行执行边界已确认；许可证 only/or-later 仍待选择 |
| 2026-11-27 | 文档治理基线提交到本地 main `be69311`；两个 worktree 已 fast-forward | 尚未 push |
