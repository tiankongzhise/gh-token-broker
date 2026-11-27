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
| 部分批准与细粒度授权 | [partial-approval.html](../design/high-fidelity/partial-approval.html) | 仓库级决定、申请权限组内的原子权限降级、最终差异 |
| Audit | [audit-agent.html](../design/high-fidelity/audit-agent.html) | 审批视角审计、重新授权入口、denied/token 元数据详情 |
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

用户明确指出：如果 agent 申请 `repo-admin`，用户不希望只能“全给 / read-only / 拒绝”。因此本设计修正为：

- 申请 profile 定义本次授权的**权限上限**。
- 用户可以在该上限内逐项调整 GitHub 原子权限，例如保留 `contents:write`、`pull_requests:write`，把 `issues` 降为 `read`，并关闭 `actions` 与 `administration`。每项最高只能选择申请上限，不能超出。
- 不得通过细粒度编辑器增加申请权限组之外的权限；不在申请组内的权限应显示为不可选择。
- 确认前必须展示“申请 → 最终授予”的差异。
- 最终决定必须写审计，包含上限、被关闭权限和被拒绝仓库，但不包含秘密。

这是对低保真“第一版不开放原子权限逐项编辑”的交互修正；它仍然是设计提案，待用户审核后才成为后续实现约束。

## 5. 与低保真基线的保持关系

继续保留：默认 Agent 审批模式；审批/人工模式分离；授权码一次性、短寿命；discovery 严格 `127.0.0.1`；reauth 显式确认；高风险操作写审计；不显示秘密。

本轮修正：模式切换必须显式且稳定；高保真页面必须完整覆盖导航和主要操作；部分批准粒度提升为“申请权限组上限内的细粒度降级”。

## 6. 待评审选择

这些是高保真设计提案，不是最终批准：

1. Approvals 默认页采用“左侧申请列表 + 右侧详情”的双栏桌面布局。
2. 批量高风险申请使用顶部危险 banner + 风险排序。
3. 细粒度授权采用三态 select（write/read/none）；确认前是否仍需要输入最终授权仓库数量，或改成逐项高风险确认。
4. 人工模式将 Token / Grants 合并为一个导航项。
5. Dashboard 指标卡是否足够精简，是否需要增加“最近拒绝/最近 reauth”。
6. 静态示意中的 `:target` 确认状态是否足以表达真实交互。

## 7. 非目标

不实现真实交互、路由、API 或前端状态管理；不代表 React/Vue/Svelte 或任何正式 WebUI 技术栈已批准；不进入可运行 Demo 阶段；不改变后端 API/schema 或批准新的权限模型。后端实现仍应等待高保真审核结论，避免前后端契约分叉。
