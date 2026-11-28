# DESIGN_SPEC — GH Token Broker WebUI 高保真设计说明

状态：高保真完整评审稿，待人工审核；权威当前状态以 [PROJECT_STATUS](PROJECT_STATUS.md) 为准。

入口：[design/high-fidelity/index.html](../design/high-fidelity/index.html)

## 1. 设计目标

本阶段把已批准低保真信息架构转成可评审的高保真桌面界面，重点验证：

- 审批模式是否足够低负担：用户主要只生成授权码并审批申请。
- 批量/高风险申请是否一眼可见。
- 部分批准是否能在**申请权限组上限内**做细粒度降级，而不是只能在 `repo-admin` / `read-only` / 拒绝之间粗选。
- 人工模式是否作为独立高级界面；点击人工模式侧栏中的 Audit、Settings 等页面不得意外跳回 Agent 审批模式。
- Dashboard、授权码、GitHub Apps、Agents、Token/Grants、Audit、Settings、reauth 和危险确认是否都有明确页面或明确交互目标。
- 空、错误、reauth、policy denied、secret store、revoke 等安全状态是否具有明确行动路径。

本设计为 implementation-neutral HTML/CSS artifact，不代表正式前端技术栈、组件库或最终产品实现。

## 2. 页面入口

### 2.1 索引与共享状态

| 页面 | 文件 | 评审重点 |
|---|---|---|
| 高保真索引 | [index.html](../design/high-fidelity/index.html) | 页面清单、完整性修正说明 |
| 状态与危险确认 | [states.html](../design/high-fidelity/states.html) | 空状态、policy denied、secret store、revoke 区分 |

### 2.2 Agent 审批模式

| 页面 | 文件 | 评审重点 |
|---|---|---|
| Dashboard | [dashboard.html](../design/high-fidelity/dashboard.html) | 待审批、reauth、快速操作、最近事件均可点击 |
| 生成授权码 | [authorization-code.html](../design/high-fidelity/authorization-code.html) | 一次性/短寿命/用途限制/撤销状态 |
| Approvals | [approval-inbox.html](../design/high-fidelity/approval-inbox.html) | 申请列表、风险详情、全部/部分/拒绝入口 |
| 部分批准与细粒度授权 | [partial-approval.html](../design/high-fidelity/partial-approval.html) | 每仓库独立权限矩阵、受限仓库管理操作、最终差异 |
| Audit | [audit-agent.html](../design/high-fidelity/audit-agent.html) | 审批视角审计、管理操作请求、重新授权入口、denied/token 元数据详情 |
| 重新授权 | [reauth.html](../design/high-fidelity/reauth.html) | 显式启动 device flow，不自动续期 |
| Settings | [settings-agent.html](../design/high-fidelity/settings-agent.html) | 低风险审批偏好与只读安全边界 |

### 2.3 人工模式

| 页面 | 文件 | 评审重点 |
|---|---|---|
| 人工模式总览 | [manual-mode.html](../design/high-fidelity/manual-mode.html) | 高级模块入口与模式边界 |
| GitHub Apps | [github-apps.html](../design/high-fidelity/github-apps.html) | App 元数据、secret ref、refresh chain、添加 App 表单示意 |
| GitHub App 重新授权 | [reauth-manual.html](../design/high-fidelity/reauth-manual.html) | 人工模式内完成显式 reauth，不跳回审批模式 |
| Agents | [agents.html](../design/high-fidelity/agents.html) | credential fingerprint、状态、编辑入口 |
| 编辑 Agent | [agents-edit.html](../design/high-fidelity/agents-edit.html) | 策略编辑、禁用、rotation、撤销 grants |
| Token / Grants | [token-grants.html](../design/high-fidelity/token-grants.html) | scoped token inventory、grant lifecycle、revoke 语义区分 |
| Audit | [audit-manual.html](../design/high-fidelity/audit-manual.html) | 完整筛选、导出脱敏审计、跨对象排障 |
| Settings | [settings-manual.html](../design/high-fidelity/settings-manual.html) | 本地服务、安全默认值、高风险变更确认 |

## 3. 视觉与交互原则

1. **安全信息优先**：风险 chips、批量警告和权限/理由不匹配提示比 agent 自述身份更醒目。
2. **桌面密度**：使用双栏/三栏布局减少滚动；审批列表和详情同屏展示。
3. **模式隔离**：顶部模式切换是唯一显式切换入口；每个模式的侧栏只链接本模式页面。人工模式下点击 Audit/Settings 必须停留在人工模式。
4. **可点击完整性**：侧边导航必须有页面；按钮至少要进入对应页面或页内目标状态。静态稿没有后端，因此“保存/复制/撤销”等动作以 `:target` 状态示意，不伪装成真实持久化。
5. **不显示秘密**：授权码示例使用明确伪数据；credential 只显示 fingerprint；token inventory 只显示 hash prefix；错误状态不输出 token/secret。
6. **危险操作显式确认**：高风险授权、revoke、disable、rotation 都需要明显确认状态。
7. **未验证声明明确标注**：agent 自报 project/name/version/reason 不作为安全事实。

## 4. 细粒度授权规则修正

用户明确指出：如果 agent 申请 `repo-admin`，用户不希望只能“全给 / read-only / 拒绝”；并且同一个 application 中的多个仓库不能共用同一组细粒度结果。因此本设计修正为：

- 申请 profile 定义本次授权的**权限上限**。
- 每个仓库都有独立决定：拒绝、按申请上限批准、或使用自定义子集。
- 每个仓库都有独立权限矩阵；repo-a 的最终授权不得自动覆盖 repo-c，repo-b 被拒绝时必须明确显示为无权限。
- 用户可以在每个仓库的申请上限内逐项调整 GitHub 原子权限，例如保留 `contents:write`、`pull_requests:write`，把 `issues` 降为 `read`，并关闭 `actions` 与 `administration`。每项最高只能选择该仓库的申请上限，不能超出。
- 不得通过细粒度编辑器增加申请权限组之外的权限；不在申请组内的权限应显示为不可选择。
- 确认前必须按仓库展示“申请 → 最终授予”的差异。
- 最终决定必须按仓库写审计，包含上限、被降低/关闭权限和被拒绝仓库，但不包含秘密。

这是对低保真“第一版不开放原子权限逐项编辑”的交互修正；它仍然是设计提案，待用户审核后才成为后续实现约束。

### 4.1 Contents / Administration 边界速查

以下解释依据 GitHub 官方文档中 scoped token 权限描述和 GitHub App permissions endpoint 表；最终仍以真实 GitHub App 冒烟矩阵为准：

| 权限 | `none` | `read` | `write` |
|---|---|---|---|
| `contents` | 不授予仓库内容权限；公开资源的隐式可读性不等于私有仓库授权 | 读取仓库内容、提交、分支、下载、release/merge 相关读操作；HTTPS clone/fetch/pull 需要该类读取能力 | 包含 read，并可写入仓库内容、创建/更新/删除文件、push/merge/branch mutation 等；修改 workflow 文件可能还需要单独的 `workflows` 权限 |
| `administration` | 不授予仓库管理能力 | 读取部分仓库管理/配置状态；不等于普通仓库 metadata 读取 | 仓库创建、删除、设置、团队/协作者/Actions 配置等高风险管理能力；普通 clone/push/PR 不需要它 |

关键边界：

- `contents` 管“仓库代码和内容”，`administration` 管“仓库管理和设置”；二者不能互相替代。
- 普通 agent 开发流程通常需要 `contents`，有时需要 `pull_requests`/`issues`；通常不应需要 `administration`。
- `metadata` 是独立的基础元数据权限，不应把 `administration:read` 误解成“只是看仓库”。
- 某些 endpoint 需要多个权限叠加；例如修改 `.github/workflows` 内文件可能同时涉及 `contents` 与 `workflows`。
- GitHub App user access token 的有效能力是用户权限、App 已批准权限和 scoped token 权限的交集；broker 不能通过 scoped token 放大用户或 App 原本没有的能力。
- GitHub scoped token API 的权限枚举只有 `read`/`write`；UI 中的 `none` 应在实现时转换为“不发送该 permission key”，而不是发送 `none` 字符串。

参考：GitHub Docs — Create a scoped access token（`POST /applications/{client_id}/token/scoped`）与 Permissions required for GitHub Apps。

### 4.2 统一授权心智与高风险管理操作

用户明确指出：审批模式的心智负担不能暴露实现机制。用户只需要理解“我授权 agent 能做什么”；至于某项能力底层由 GitHub 原生 token permission 实现、由 broker 代执行，或由未来其他安全执行器实现，都不应该成为 Agent 审批模式的主界面概念。

因此 Agent 审批模式必须遵守：

- 不出现 `Broker operation capability`、内部 operation id、executor、模板实现机制等实现术语。
- 用户看到的是统一授权项，例如“创建仓库（受限）”“为新仓库保护 main（受限）”。
- 每个授权项仍然独立决定；仓库内容权限按仓库矩阵审批，仓库管理操作按能力项审批。
- 用户可见约束必须使用人类语言，例如“最多 1 个私有仓库”“只允许作用于本次创建的仓库”“必须使用安全保护模板”。
- `删除仓库`、`解除 main 保护`、`任意修改仓库设置`、`管理协作者`这类不可安全细分的能力不开放申请，固定禁止。
- 底层执行方式、内部 operation id、模板字段和机器审计细节可以出现在人工/高级模式、开发文档或后端契约中，但不能进入 Agent 审批模式主流程。

内部实现仍然需要分层：普通仓库数据面权限可以由 GitHub scoped token permission 表达；创建仓库、设置 branch protection 等 GitHub 原生权限拆不细的高风险操作，必须由 broker-side operation capability  enforcement 实现，且默认不得向 agent 交付 `administration:write` token。这个内部契约会影响后端 policy/schema/API、audit、threat model 和未来 MCP/operation executor；当前全局契约草案记录在 CR-0002，最终形态仍以高保真审核和契约冻结为准。

## 5. 与低保真基线的保持关系

继续保留：默认 Agent 审批模式；审批/人工模式分离；授权码一次性、短寿命；discovery 严格 `127.0.0.1`；reauth 显式确认；高风险操作写审计；不显示秘密。

本轮修正：模式切换必须显式且稳定；高保真页面必须完整覆盖导航和主要操作；部分批准粒度提升为“每仓库独立、申请权限组上限内的细粒度降级”；高风险管理操作以统一授权项展示给用户，底层安全执行机制放入高级模式和内部契约。

## 6. 待评审选择

这些是高保真设计提案，不是最终批准：

1. Approvals 默认页采用“左侧申请列表 + 右侧详情”的双栏桌面布局。
2. 批量高风险申请使用顶部危险 banner + 风险排序。
3. 细粒度授权采用三态 select（write/read/none）；确认前是否仍需要输入最终授权仓库数量，或改成逐项高风险确认。
4. 受限仓库管理操作的用户语言是否足够清楚，尤其是“创建仓库 + 只允许安全模板保护 main”的链式范围。
5. 人工模式将 Token / Grants 合并为一个导航项。
6. Dashboard 指标卡是否足够精简，是否需要增加“最近拒绝/最近 reauth”。
7. 静态示意中的 `:target` 确认状态是否足以表达真实交互。

## 7. 非目标

不实现真实交互、路由、API 或前端状态管理；不代表 React/Vue/Svelte 或任何正式 WebUI 技术栈已批准；不进入可运行 Demo 阶段；不改变后端 API/schema 或批准新的权限模型。后端实现仍应等待高保真审核结论，避免前后端契约分叉。
