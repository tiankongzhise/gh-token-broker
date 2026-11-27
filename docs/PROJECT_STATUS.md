# PROJECT_STATUS — GH Token Broker

本文是项目可变状态的当前事实源：阶段、批准、worktree、验证结果和未决事项都记录在这里。`AGENTS.md` 只保存框架规则和文档地图。

最近更新：2026-11-27

## 1. 当前快照

| 字段 | 当前值 | 证据/备注 |
|---|---|---|
| 当前阶段 | WebUI 审批优先低保真已获用户确认；后端 Phase 1 core token chain POC 已通过审查；下一阶段入口为 B 高保真，但尚未开始 | 2026-11-27 用户修正降权语义并确认“低保真确认”；高保真未获开始指令 |
| 批准状态 | **有限授权，不是完整产品基线批准** | 后端 token chain 已接受为 Phase 2 技术地基；审批优先低保真已确认；仍不视为高保真、Demo、完整后端、raw token 策略或 WebUI 技术栈批准 |
| 后端核心解释 | 已确认采用保守解释：按 [DEVELOPMENT](DEVELOPMENT.md) Phase 1 的核心 token chain POC 边界执行 | 2026-11-27 用户确认“采取保守解释”；不自动包含 MCP、WebUI、scoped token、多 agent policy |
| 产品实现状态 | 后端 Phase 1 POC 已在后端 worktree 提交；WebUI 低保真与审核讲解 Demo 已在 WebUI worktree 提交 | 后端 `feat/backend-core` commit `9c1ba2a`；WebUI `feat/webui-wireframes` commits 已包含低保真、讲解 Demo、审批模式与降权语义修正；均未 push、未合并 |
| 许可证 | **已确认**：`LGPL-2.1-only` | 2026-11-27 用户明确选择；见 [DECISIONS](DECISIONS.md#d-0001-license-lgpl-21) |
| secret store MVP | **已批准**：加密 SQLite + Windows Credential Manager 保存 master key | 2026-11-27 用户批准 D-0002；见 [DECISIONS](DECISIONS.md#d-0002-secret-store-mvp) |
| 当前审核门 | **低保真已通过；高保真开始前的显式工作指令门** | 后端 POC 已通过但仍未启动 Phase 2；低保真确认不等于高保真/Demo/Phase 2 开始指令 |

## 2. 批准与授权记录

| 日期 | 用户授权/决定 | 适用范围 | 不构成对什么事项的批准 |
|---|---|---|---|
| 2026-11-27 | “本项目使用 LGPL 2.1 许可” | 许可证族与版本 2.1 | 当时尚未明确 `only` vs `or-later` |
| 2026-11-27 | 明确选择 `LGPL-2.1-only` | 许可证精确 SPDX 语义 | 不表示未来自动接受 or-later |
| 2026-11-27 | 开两个 worktree：一个前端低保真确认，一个后端核心 | 并行工作组织方式 | 不批准完整后端、MCP、WebUI 实现、scoped token 或 raw token 策略 |
| 2026-11-27 | 批准 D-0002 secret store MVP | 加密 SQLite + master key in Windows Credential Manager | 不批准跳过 AEAD/key rotation/恢复设计要求 |
| 2026-11-27 | “采取保守解释” | 后端核心按 Phase 1 core token chain POC | 不扩展到 MCP、WebUI、scoped token、多 agent policy |
| 2026-11-27 | 允许 commit | 授权创建本地 git commit | 不授权 push、强推、改写历史或添加 AI 署名 |
| 2026-11-27 | 审批模式方向 | 默认 UX：用户生成授权码，agent discovery 并提交权限申请，用户全部/部分审批；人工模式高级保留 | 不批准具体前端技术栈、高保真、discovery API 最终实现契约 |
| 2026-11-27 | “后端通过，token chain 当作 Phase 2 的技术地基” | 接受 Phase 1 token chain 核心语义作为 Phase 2 地基 | 不表示 Phase 2 已启动，不批准所有实现细节或真实 GitHub 语义 |
| 2026-11-27 | 审批模式交互细化 | 授权码一次性/短寿命；第一版不开放原子权限编辑；discovery 严格 127.0.0.1；审批/人工两套 UI 顶部切换且默认审批模式 | 不批准高保真、Demo、最终 API schema 或高风险权限确认文案 |
| 2026-11-27 | 用户修正降权语义并确认“低保真确认” | 第一版允许按仓库批准/拒绝并降权 permission profile；低保真信息架构与审批交互方向通过 | 不批准最终视觉、前端技术栈、后端 API schema 或自动开始高保真 |

没有任何记录表明以下内容已批准：完整 PRD/架构基线、WebUI 技术栈、高保真设计、Demo、raw token 兼容模式、GitHub Enterprise 优先级、完整发布流程。

## 3. Worktree 与修改边界

| 工作流 | 路径 | 分支 | 允许修改/目标 | 禁止事项 |
|---|---|---|---|---|
| 主文档/治理 | `E:\github\gh-token-broker` | `main` | 根文档、`docs/`、`scripts/check_secrets.py`、`.gitignore`、许可证与本阶段用户明确要求的文档治理 | 不开始产品实现；首个 CI workflow 已配置 |
| WebUI 低保真 | `E:\github\gh-token-broker-webui` | `feat/webui-wireframes` | `design/wireframes/`、`docs/WIREFRAMES.md` 及低保真所需文档索引 | 不定最终视觉、不实现后端、不改后端核心文件 |
| 后端核心 | `E:\github\gh-token-broker-backend` | `feat/backend-core` | 按 Phase 1：Go module、配置、secret store 抽象/实现、device flow、refresh chain、mock GitHub 单元测试 | 不做 MCP/WebUI/scoped token/多 agent policy；不返回 raw token 给模型上下文 |

注意：两个工作流 worktree 创建时基于 `main` 的 commit `c55ea97`；2026-11-27 文档治理基线提交后，两个分支曾 fast-forward 到同一文档基线。当前两个分支已分别携带本阶段产物 commit：WebUI `d1f8157`、后端 `9c1ba2a`，均未合并回 main。后续实时分支状态以 `git worktree list` 为准。

## 4. 未决事项

按优先级排序：

1. scoped token 父/子失效语义在目标 GitHub App 上的实测结果。
2. 高保真阶段开始前需确认：高风险项确认强度、审批模式 Dashboard 精简程度、人工模式页面合并/拆分。
3. discovery public node 与 permission application 的最终 API/schema 契约。
4. WebUI 技术栈。
5. raw token 兼容模式是否默认存在，还是仅编译/配置为高级模式。
6. GitHub Enterprise host 支持优先级。
7. operation-only MCP 是否作为第一交付通道。
8. SQLite schema migration 方案；Phase 1 POC 已选用 `modernc.org/sqlite` 作为纯 Go 驱动，但该选型尚未被批准为长期架构决策。
9. 依赖扫描、构建复现、SBOM/签名/校验和与发布自动化仍未配置；首个 GitHub Actions CI 已配置并完成首轮真实验证；原则见 [CI_CD](CI_CD.md)。

## 5. 当前验证状态

| 用途 | 工作目录与命令 | 状态 | 最近结果 |
|---|---|---|---|
| 秘密扫描 | 仓库根：`python scripts/check_secrets.py` | 已配置；每次 push 前必须运行 | 2026-11-27 后端提交前通过；WebUI 提交前通过 |
| 文档权威检查 | 仓库根：`python scripts/check_doc_authority.py` | 本轮新增，已接入 CI workflow | 2026-11-27 本地通过；远端待本轮 PR 验证 |
| CI workflow | `.github/workflows/ci.yml` 已配置；GitHub Actions job/context 为 `ci` | PR #1 分支 CI 与 merge 后 main CI 已通过；backend 首次同步 CI 暴露 Windows CRLF/gofmt 问题，本轮用 `.gitattributes` 修复 | 已真实运行 |
| main 分支保护 | GitHub branch protection | 已配置：要求 PR、要求 `ci` 且 strict、enforce admins、禁止 force push/deletion | 2026-11-27 API 验证 |
| Go 格式检查 | 后端 worktree：`gofmt -l cmd internal`（应无输出） | 已在 `feat/backend-core` 验证 | 2026-11-27 通过 |
| Go 单元测试 | 后端 worktree：`go test -count=1 -timeout=90s ./...` | 已在 `feat/backend-core` 验证 | 2026-11-27 通过，全部为 mock/test key，无真实 GitHub 调用 |
| Go vet/build | 后端 worktree：`go vet ./... && go build ./...` | 已在 `feat/backend-core` 验证 | 2026-11-27 通过 |
| Go race spot check | 后端 worktree：`CGO_ENABLED=1 go test -race -count=1 -timeout=90s ./internal/tokenchain ./internal/platform/winmutex` | 已做局部验证，不是完整 CI 门禁 | 2026-11-27 通过 |
| Wireframe artifact 检查 | WebUI worktree：生成脚本运行、12 个 SVG XML parse、模式分离检查、walkthrough JS syntax、本地 HTTP 访问 | 已验证 | 2026-11-27 模式分离与仓库级审批更新后通过 |
| 启动/真实 GitHub 冒烟 | 未运行 | 需要真实 GitHub App 与用户授权，不能在审查前虚构 | 未运行 |

## 6. 角色与委派状态

当前会话已知通用子代理类型为 `subagent_explore` 与 `subagent_general`；没有发现可直接调用的 agency-agents 命名角色。后续需要委派时必须重新核对运行时能力，不能把角色库文件当作可调用事实。

| 阶段职责 | 请求角色完整名 | 当前运行时实际可用名 | 状态 |
|---|---|---|---|
| 需求/产品 | Product Manager | 当前会话未可用 | 未委派 |
| 架构 | Software Architect | 当前会话未可用 | 未委派 |
| 实现 | 匹配 Go/Windows 的实现角色 | 当前会话未可用 | 未发现专门实现角色；后端 POC 由主会话直接实现，未委派给通用子代理 |
| 审查 | Code Reviewer / Reality Checker | 当前会话未可用 | 到验证阶段再核对 |

## 7. 状态变更日志

| 日期 | 变更 | 记录 |
|---|---|---|
| 2026-11-27 | 初始化项目文档和 secret scan baseline | commit `c55ea97` |
| 2026-11-27 | 用户指定 LGPL 2.1、要求并行 worktree、要求审计文档并重构 AGENTS 为文档地图 | 本轮文档治理变更 |
| 2026-11-27 | 用户批准 D-0002、确认后端核心保守解释为 Phase 1，并允许创建本地 commit | 并行执行边界已确认 |
| 2026-11-27 | 文档治理基线提交到本地 main `be69311`；两个 worktree 已 fast-forward | 尚未 push |
| 2026-11-27 | 用户确认许可证为 `LGPL-2.1-only` | 精确许可证语义已关闭 |
| 2026-11-27 | WebUI worktree 提交低保真 wireframes 与 `docs/WIREFRAMES.md` | `feat/webui-wireframes` commit `d1f8157`；待用户审查 |
| 2026-11-27 | 后端 worktree 提交 Phase 1 core token chain POC | `feat/backend-core` commit `9c1ba2a`；测试/build/vet/secret scan 通过；待用户审查 |
| 2026-11-27 | WebUI worktree 增加低保真/后端 POC 审核讲解 Demo | `feat/webui-wireframes` commit `e0266c1`；用于辅助当前审核，不代表进入高保真或 Demo 阶段 |
| 2026-11-27 | 用户指出原前端过于繁琐，确认审批模式方向 | D-0004 approved；人工模式高级保留 |
| 2026-11-27 | 用户接受后端 POC 为 Phase 2 技术地基 | D-0005 approved；Phase 2 未启动 |
| 2026-11-27 | WebUI worktree 增加审批优先低保真 | `feat/webui-wireframes` commit `4fe1a13`；待用户复审 |
| 2026-11-27 | 用户确认审批模式细化并要求两套 UI 分离 | D-0006 approved；授权码一次性/短寿命、仓库级审批、严格 loopback、顶部模式切换 |
| 2026-11-27 | 用户修正降权语义并确认低保真 | D-0007 approved；第一版允许 profile 降权但不开放原子权限编辑；低保真阶段通过 |
| 2026-11-27 | 用户指出 CI/CD 与 `.gitignore` 治理缺口 | D-0008 approved；新增 CI/CD 与 gitignore 专门规范并接入文档地图；当时首个 CI 尚未实施，后续见 D-0009 |
| 2026-11-27 | 用户要求 main 分支保护、添加 CI 并真实 push 验证 | D-0009 approved；禁止直接 push main，main 修改走分支 + PR；首轮远端验证已完成 |
| 2026-11-27 | main 保护与首轮 CI 实测结果 | PR #1 CI 通过并合并；main CI 通过；main protection 已配置；backend 同步后发现并修复 CRLF/gofmt CI 兼容问题 |
| 2026-11-27 | 用户要求审计状态漂移并建立单一权威来源机制 | D-0010 approved；新增 authority registry/checker，WIREFRAMES 状态修正在 WebUI 分支同步处理 |
