# PROJECT_STATUS — GH Token Broker

本文是项目可变状态的当前事实源：阶段、批准、worktree、验证结果和未决事项都记录在这里。`AGENTS.md` 只保存框架规则和文档地图。

最近更新：2026-11-27

## 1. 当前快照

| 字段 | 当前值 | 证据/备注 |
|---|---|---|
| 当前阶段 | WebUI B 高保真与后端 Phase 2 已获开始授权；正在补齐 open-main-PR 与 feature freshness 门禁基线 | 2026-11-27 用户明确要求完成分支处理后开始高保真和后端阶段2；见 D-0016；悬空 main PR 暴露后用户批准 D-0019 |
| 批准状态 | **有限授权，不是完整产品基线批准** | 后端 token chain 已接受为 Phase 2 技术地基；审批优先低保真已确认；仍不视为高保真、Demo、完整后端、raw token 策略或 WebUI 技术栈批准 |
| 后端核心解释 | 已确认采用保守解释：按 [DEVELOPMENT](DEVELOPMENT.md) Phase 1 的核心 token chain POC 边界执行 | 2026-11-27 用户确认“采取保守解释”；不自动包含 MCP、WebUI、scoped token、多 agent policy |
| 产品实现状态 | 已批准低保真 wireframes 与 Phase 1 core token chain POC 均已集成进 `main` | WebUI integration PR #9 已合并且 main CI 通过；backend integration PR #10 已合并且 main CI 通过；仍无完整 daemon、MCP server、WebUI 或 credential helper 实现 |
| 许可证 | **已确认**：`LGPL-2.1-only` | 2026-11-27 用户明确选择；见 [DECISIONS](DECISIONS.md#d-0001-license-lgpl-21) |
| secret store MVP | **已批准**：加密 SQLite + Windows Credential Manager 保存 master key | 2026-11-27 用户批准 D-0002；见 [DECISIONS](DECISIONS.md#d-0002-secret-store-mvp) |
| 当前审核门 | **B 高保真与后端 Phase 2 进行中；高保真完成后停在人工审核门，Phase 2 完成后停在集成/验证审核门** | 用户已明确授权开始；不自动批准 Demo、正式 WebUI 技术栈、MCP、scoped token 完整实现或自动发布 |

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
| 2026-11-27 | 用户要求 merged branches 及时清理，并选择只删除短分支 | 已合并 chore/fix 分支清理；feature 分支暂存但失去 active 写入权 | 不授权删除仍有未合并工作的分支或改写历史 |
| 2026-11-27 | 用户选择推荐版本管理方案 | SemVer + VERSION + vX.Y.Z tag + CI consistency check + Go ldflags 注入 | 不批准自动 release/CD、签名、SBOM 或 artifact 上传 |
| 2026-11-27 | 用户要求治理基线同步后开始高保真和后端阶段2 | 启动 B 高保真与 backend Phase 2 safe delivery | 不批准 Demo、正式 WebUI 技术栈、MCP、完整 policy engine 或 raw token 兼容模式 |

没有任何记录表明以下内容已批准：完整 PRD/架构基线、WebUI 技术栈、高保真设计、Demo、raw token 兼容模式、GitHub Enterprise 优先级、完整发布流程。

## 3. Worktree 与修改边界

| 工作流 | 路径 | 分支 | 允许修改/目标 | 禁止事项 |
|---|---|---|---|---|
| 主文档/治理 | `E:\github\gh-token-broker` | `main` | 根文档、`docs/`、`scripts/check_secrets.py`、`.gitignore`、许可证与本阶段用户明确要求的文档治理 | 不开始产品实现；首个 CI workflow 已配置 |
| WebUI 高保真 | `E:\github\gh-token-broker-webui` | `feat/webui-high-fidelity` | `design/high-fidelity/`、`docs/DESIGN_SPEC.md` | 不定正式前端技术栈、不进入 Demo、不改后端核心文件 |
| 后端 Phase 2 | `E:\github\gh-token-broker-backend` | `feat/backend-safe-delivery` | `cmd/`、`internal/`、`go.mod`、`go.sum`、`config.example.yaml`；范围按 CR-0001 为 scoped/grant 基础、exec wrapper、credential helper、min_ttl、基础审计与 Windows 验证 | 不做 MCP/WebUI/scoped token 完整实现；不返回 raw token 给模型上下文 |

注意：`feat/webui-wireframes` 与 `feat/backend-core` 已按用户选择暂存，但在 ownership registry 中为 `integrated`，不再拥有写入权。后续高保真与 Phase 2 使用新 active 分支；实时状态以 `git worktree list` 和 `docs/branch-ownership.json` 为准。

## 3.1 当前 integration queue

| 顺序 | 分支 | 集成内容 | 当前状态 |
|---|---|---|---|
| — | 当前无进行中 integration | merged-branch/versioning 治理基线合并后，再按 queue 处理高保真/Phase 2 成果 | 等待新 feature 分支产生可集成成果 |

规则：同一时刻只处理一个 integration；main CI 通过后再同步另一个分支。权威原则见 [BRANCHING](BRANCHING.md)。

## 4. 未决事项

按优先级排序：

1. scoped token 父/子失效语义在目标 GitHub App 上的实测结果；CR-0001 已允许提前实现基础能力，但真实语义仍需冒烟矩阵。
2. 高保真阶段开始前需确认：高风险项确认强度、审批模式 Dashboard 精简程度、人工模式页面合并/拆分。
3. discovery public node 与 permission application 的最终 API/schema 契约。
4. WebUI 技术栈。
5. raw token 兼容模式是否默认存在，还是仅编译/配置为高级模式。
6. GitHub Enterprise host 支持优先级。
7. operation-only MCP 是否作为第一交付通道。
8. SQLite schema migration 方案；Phase 1 POC 已选用 `modernc.org/sqlite` 作为纯 Go 驱动，但该选型尚未被批准为长期架构决策。
9. 依赖扫描、构建复现、SBOM/签名/校验和与发布自动化仍未配置；版本控制基础已建立但 release notes/artifact/CD 未批准；原则见 [CI_CD](CI_CD.md) 与 [VERSIONING](VERSIONING.md)。
10. GitHub 仓库级 auto-delete merged branches 尚未配置；当前按用户确认后的及时删除执行。

## 5. 当前验证状态

| 用途 | 工作目录与命令 | 状态 | 最近结果 |
|---|---|---|---|
| 秘密扫描 | 仓库根：`python scripts/check_secrets.py` | 已配置；每次 push 前必须运行 | 2026-11-27 后端提交前通过；WebUI 提交前通过 |
| 文档权威检查 | 仓库根：`python scripts/check_doc_authority.py` | 已配置，已接入 CI workflow | 2026-11-27 本地通过；PR #3 分支 CI 与 merge 后 main CI 通过 |
| 分支 ownership 检查 | 仓库根：`python scripts/check_branch_ownership.py` | 已配置，已接入 CI workflow；本轮新增 feature freshness 规则 | 2026-11-27 本地通过；PR #7 修复后 main CI 通过；PR #9/#10 integration CI 通过 |
| open main PR 门禁 | 仓库根：`python scripts/check_main_pr_gate.py` | 本轮新增并接入 CI workflow；只对 `feat/**` 生效 | 2026-11-27 本地已实现；远端 CI 尚无结果 |
| 高摩擦政策证据检查 | 仓库根：`python scripts/check_policy_evidence.py` | 本轮新增并接入 CI workflow | 2026-11-27 本地已实现；远端 CI 尚无结果 |
| 版本格式检查 | 仓库根：`python scripts/check_version.py` | 已接入 CI workflow；tag 上下文校验 tag 与 VERSION 一致 | 2026-11-27 本地通过 |
| commit message 检查 | 仓库根：`python scripts/check_commit_messages.py` | 本轮新增并接入 CI workflow；GitHub merge commit 豁免 | 2026-11-27 本地通过 |
| CI workflow | `.github/workflows/ci.yml` 已配置；GitHub Actions job/context 为 `ci` | PR #1 分支 CI 与 merge 后 main CI 已通过；backend 首次同步 CI 暴露 Windows CRLF/gofmt 问题，本轮用 `.gitattributes` 修复 | 已真实运行 |
| main 分支保护 | GitHub branch protection | 已配置：要求 PR、要求 `ci` 且 strict、enforce admins、禁止 force push/deletion | 2026-11-27 API 验证 |
| Go 格式检查 | 后端 worktree：`gofmt -l cmd internal`（应无输出） | 已在 `feat/backend-core` 验证 | 2026-11-27 通过 |
| Go 单元测试 | 仓库根：`go test -count=1 -timeout=90s ./...` | 已在 integration 前后的 `feat/backend-core` 与 main CI 验证 | 2026-11-27 通过，全部为 mock/test key，无真实 GitHub 调用 |
| Go vet/build | 后端 worktree：`go vet ./... && go build ./...` | 已在 `feat/backend-core` 验证 | 2026-11-27 通过 |
| Go race spot check | 后端 worktree：`CGO_ENABLED=1 go test -race -count=1 -timeout=90s ./internal/tokenchain ./internal/platform/winmutex` | 已做局部验证，不是完整 CI 门禁 | 2026-11-27 通过 |
| Wireframe artifact 检查 | WebUI worktree/main artifact：生成脚本运行、12 个 SVG XML parse、模式分离检查、walkthrough JS syntax、本地 HTTP 访问 | 已验证并随 PR #9 集成 | 2026-11-27 模式分离与仓库级审批更新后通过 |
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
| 2026-11-27 | WebUI worktree 提交低保真 wireframes 与 `docs/WIREFRAMES.md` | `feat/webui-wireframes` commit `d1f8157`；当时待用户审查，后续批准见 D-0007 |
| 2026-11-27 | 后端 worktree 提交 Phase 1 core token chain POC | `feat/backend-core` commit `9c1ba2a`；测试/build/vet/secret scan 通过；当时待用户审查，后续接受见 D-0005 |
| 2026-11-27 | WebUI worktree 增加低保真/后端 POC 审核讲解 Demo | `feat/webui-wireframes` commit `e0266c1`；用于辅助当前审核，不代表进入高保真或 Demo 阶段 |
| 2026-11-27 | 用户指出原前端过于繁琐，确认审批模式方向 | D-0004 approved；人工模式高级保留 |
| 2026-11-27 | 用户接受后端 POC 为 Phase 2 技术地基 | D-0005 approved；Phase 2 未启动 |
| 2026-11-27 | WebUI worktree 增加审批优先低保真 | `feat/webui-wireframes` commit `4fe1a13`；当时待用户复审，后续批准见 D-0007 |
| 2026-11-27 | 用户确认审批模式细化并要求两套 UI 分离 | D-0006 approved；授权码一次性/短寿命、仓库级审批、严格 loopback、顶部模式切换 |
| 2026-11-27 | 用户修正降权语义并确认低保真 | D-0007 approved；第一版允许 profile 降权但不开放原子权限编辑；低保真阶段通过 |
| 2026-11-27 | 用户指出 CI/CD 与 `.gitignore` 治理缺口 | D-0008 approved；新增 CI/CD 与 gitignore 专门规范并接入文档地图；当时首个 CI 尚未实施，后续见 D-0009 |
| 2026-11-27 | 用户要求 main 分支保护、添加 CI 并真实 push 验证 | D-0009 approved；禁止直接 push main，main 修改走分支 + PR；首轮远端验证已完成 |
| 2026-11-27 | main 保护与首轮 CI 实测结果 | PR #1 CI 通过并合并；main CI 通过；main protection 已配置；backend 同步后发现并修复 CRLF/gofmt CI 兼容问题 |
| 2026-11-27 | 用户要求审计状态漂移并建立单一权威来源机制 | D-0010 approved；新增 authority registry/checker，WIREFRAMES 状态修正在 WebUI 分支同步处理 |
| 2026-11-27 | 用户允许 GitHub PR merge commit 自动作者身份 | D-0011 approved；仅限 GitHub merge commit，本地普通提交身份不变 |
| 2026-11-27 | 用户批准 CI 触发策略去重 | D-0012 approved；push CI 保留 main 与 feat/**，chore/fix 短分支依靠 PR CI |
| 2026-11-27 | 用户批准两个已验收 feature 分支均集成，并选择实用严格 ownership 模式 | D-0013 approved；建立 integration queue 与 branch ownership registry |
| 2026-11-27 | WebUI integration 完成 | PR #9 已合并；main CI 通过；低保真成果成为共同 main 基线，但不启动高保真 |
| 2026-11-27 | backend integration 完成 | PR #10 已合并；main CI 通过；Phase 1 POC 成为共同 main 基线，但不启动 Phase 2 |
| 2026-11-27 | 用户要求 merged branch cleanup、指出版本管理缺失，并授权之后开始高保真与后端 Phase 2 | 已删除已合并 chore/fix 短分支；feature 分支按用户选择暂存但转为 integrated；D-0014/D-0015/D-0016 记录 |
| 2026-11-27 | 用户选择提前 scoped/grant 基础 | CR-0001/D-0017 approved；Phase 2 先实现 scoped token 与最小 grant 基础，exec/helper 不得使用 parent token |
| 2026-11-27 | 用户要求后续 commit 使用中文并补充约束 | D-0018 approved；新增 COMMIT_MESSAGES 与结构性 checker，历史 commit 不回溯改写 |
| 2026-11-27 | 用户指出悬空 main PR 会击穿仅靠 Git 历史的同步机制 | D-0019 approved；采用通用 open-main-PR gate 与 feature freshness；feature 工作必须先处理/同步 main PR |
| 2026-11-27 | 用户要求修正 push 前每次确认政策并沉淀防复发机制 | D-0020 approved；改为异常触发型署名/身份政策，新增高摩擦政策证据检查 |
