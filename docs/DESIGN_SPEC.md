# DESIGN_SPEC — GH Token Broker WebUI 高保真设计说明

状态：高保真首版设计稿，待人工审核；权威当前状态以 [PROJECT_STATUS](PROJECT_STATUS.md) 为准。

入口：[design/high-fidelity/index.html](../design/high-fidelity/index.html)

## 1. 设计目标

本阶段把已批准低保真信息架构转成可评审的高保真桌面界面，重点验证：

- 审批模式是否足够低负担：用户主要只生成授权码并审批申请。
- 批量/高风险申请是否一眼可见。
- 部分批准/降权是否在确认前清楚呈现最终差异。
- 人工模式是否作为独立高级界面，不与默认审批路径混杂。
- 空、错误、reauth、policy denied、revoke 等安全状态是否具有明确行动路径。

本设计为 implementation-neutral HTML/CSS artifact，不代表正式前端技术栈、组件库或最终产品实现。

## 2. 页面入口

| 页面 | 文件 | 评审重点 |
|---|---|---|
| 高保真索引 | [index.html](../design/high-fidelity/index.html) | 页面结构、评审范围 |
| Approvals 默认页 | [approval-inbox.html](../design/high-fidelity/approval-inbox.html) | 授权码、待审批列表、风险详情、默认模式信息密度 |
| 部分批准/降权 | [partial-approval.html](../design/high-fidelity/partial-approval.html) | 仓库级决定、profile 降权、最终差异、高风险确认 |
| 人工模式 | [manual-mode.html](../design/high-fidelity/manual-mode.html) | 模式分离、高级策略、credential fingerprint、危险操作入口 |
| 状态与危险确认 | [states.html](../design/high-fidelity/states.html) | reauth、policy denied、secret store、revoke 确认 |

## 3. 视觉与交互原则

1. **安全信息优先**：风险 chips、批量警告和权限/理由不匹配提示比 agent 自述身份更醒目。
2. **桌面密度**：使用双栏/三栏布局减少滚动；审批列表和详情同屏展示。
3. **模式分离**：顶部模式切换控制整个信息架构；审批模式左侧只保留 Dashboard、Approvals、Audit、Settings。
4. **不显示秘密**：授权码示例脱敏；credential 只显示 fingerprint；错误状态不输出 token/secret。
5. **危险操作显式确认**：repo-admin、revoke、disable、高风险批量批准都需要明显确认状态。
6. **未验证声明明确标注**：agent 自报 project/name/version/reason 不作为安全事实。

## 4. 与低保真基线的保持关系

保持以下已批准低保真约束：默认 Agent 审批模式；审批/人工模式分离；按仓库批准、拒绝、降权 permission profile；不开放 GitHub 原子权限逐项编辑；discovery 严格 `127.0.0.1`；授权码一次性、短寿命；reauth 显式确认；高风险操作写审计。

## 5. 待评审选择

这些是高保真设计提案，不是最终批准：

1. Approvals 默认页采用“左侧申请列表 + 右侧详情”的双栏桌面布局。
2. 批量高风险申请使用顶部危险 banner + 风险排序。
3. 部分批准确认要求输入最终授权仓库数量；是否保留这种 type-to-confirm 形式需要用户评审。
4. 人工模式暂时将 Token / Grants 合并为一个导航项。
5. Dashboard 高保真尚未单独展开；本首版优先验证 Approvals、partial approval、人工模式和安全状态。

## 6. 非目标

不实现真实交互、路由、API 或前端状态管理；不代表 React/Vue/Svelte 或任何正式 WebUI 技术栈已批准；不进入可运行 Demo 阶段；不改变后端 API/schema 或批准新的权限模型。
