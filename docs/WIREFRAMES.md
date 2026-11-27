# WIREFRAMES — GH Token Broker WebUI 低保真

状态：draft 0.1，待人工审核

日期：2026-11-27

入口：[design/wireframes/index.html](../design/wireframes/index.html)

审核辅助讲解 Demo：[design/wireframes/walkthrough.html](../design/wireframes/walkthrough.html)。该 Demo 只用于帮助理解低保真和后端 Phase 1 POC 的决策含义，不是高保真设计、不是产品原型、也不构成下一阶段批准。

## 1. 审核范围

本阶段只确认：

- 页面是否完整。
- 页面入口和导航是否清楚。
- 核心流程是否闭环。
- 空、加载、错误、危险确认状态是否覆盖。
- 信息是否足以支撑后续高保真和 Demo。

本阶段不确认：

- 最终颜色、字体、图标、阴影和品牌风格。
- 前端技术栈。
- 具体组件库。
- 最终文案措辞。

## 2. 产物索引

| ID | 文件 | 内容 | 主要对应需求 |
|---|---|---|---|
| WF-00 | [00-overview-flow.svg](../design/wireframes/00-overview-flow.svg) | 页面结构与核心流程总览 | 全局导航、流程闭环 |
| WF-01 | [01-dashboard.svg](../design/wireframes/01-dashboard.svg) | Dashboard：授权健康、需要行动、最近事件 | FR-19、错误恢复、安全提醒 |
| WF-02 | [02-onboarding-device-flow.svg](../design/wireframes/02-onboarding-device-flow.svg) | 首次配置、添加 GitHub App、显式 device flow | FR-1、FR-2、FR-20、空/错误状态 |
| WF-03 | [03-github-apps.svg](../design/wireframes/03-github-apps.svg) | GitHub App/account 列表、详情、reauth | FR-1、FR-2、FR-3、FR-26 |
| WF-04 | [04-agents-policies.svg](../design/wireframes/04-agents-policies.svg) | agent credential、启用/禁用、repo/profile 策略 | FR-9、FR-10、FR-11、高风险权限 |
| WF-05 | [05-token-issues-grants.svg](../design/wireframes/05-token-issues-grants.svg) | child token inventory、grant 列表、revoke 确认 | FR-7、FR-8、FR-13、FR-26 |
| WF-06 | [06-audit.svg](../design/wireframes/06-audit.svg) | 审计筛选、列表、详情 drawer | FR-24、FR-25 |
| WF-07 | [07-settings-security.svg](../design/wireframes/07-settings-security.svg) | loopback、secret store、min_ttl、raw token、备份恢复 | FR-18、FR-21、FR-22、FR-23 |
| WF-08 | [08-states-errors.svg](../design/wireframes/08-states-errors.svg) | 空/加载/网络错误/reauth/policy denied/secret store/Host-Origin/高风险确认状态 | PRD 第 7 章 |
| WF-09 | [09-approval-inbox.svg](../design/wireframes/09-approval-inbox.svg) | 审批模式默认页：生成 agent 授权码、待审批列表、申请详情、全部/部分/拒绝 | agent-initiated approval 新方向 |
| WF-10 | [10-agent-code-flow.svg](../design/wireframes/10-agent-code-flow.svg) | 授权码、agent discovery public node、权限申请提交、审批生效的跨角色流程 | agent 对接协议、授权码边界 |
| WF-11 | [11-partial-approval.svg](../design/wireframes/11-partial-approval.svg) | 按仓库部分批准示例：只勾选/取消仓库，profile 只读展示，最终差异确认 | 部分批准粒度、高风险默认不批准 |

可维护生成脚本：[generate_wireframes.py](../design/wireframes/generate_wireframes.py)。SVG 是评审主产物；脚本只是为了重新生成，不是产品代码。

## 3. 导航与页面结构

顶部必须有明确模式切换，默认进入 **Agent 审批模式**。两套 UI 不混在同一左侧导航里。

审批模式左侧只显示：

1. Dashboard
2. Approvals
3. Audit
4. Settings

人工模式左侧只显示：

1. Dashboard
2. GitHub Apps
3. Agents
4. Token / Grants
5. Audit
6. Settings

设计意图：

- 审批模式是默认路径：用户只生成授权码并审批 agent 主动提交的申请，不要求用户手工编写复杂 policy。
- 人工模式是独立高级界面：用于手工修正策略、rotate/disable、revoke、GitHub App 细节和高级排障。
- 顶部模式切换不是普通 tab；切换后整页信息架构和左侧导航一起变化，避免两种心智模型混杂。
- Dashboard 在两种模式下都保留“需要用户行动”优先级，但审批模式突出 pending approvals，人工模式突出高级排障入口。

## 4. 核心流程覆盖

### 4.1 审批模式：默认 agent 接入流程

流程：

1. 用户登录本地 GH Token Broker，在 Approvals 生成一次性/短寿命 agent 授权码。
2. 用户把授权码交给 agent。授权码只代表“允许提交申请”，不代表已经获得 GitHub 权限。
3. agent 读取 broker 的 localhost discovery public node，了解 API version、endpoint、支持的 profile 和申请格式。这里 public 指无需凭证可读协议元数据，不是公网公开。
4. agent 根据项目上下文提交权限申请：host/owner/repo/profile/min_ttl/reason。
5. 用户在 Approvals 查看申请和风险提示，可以全部批准、按仓库部分批准或拒绝；第一版不能在审批页编辑原子权限或 profile。
6. 批准后 broker 自动生成或更新 agent credential、policy 和后续 grant/token 边界；结果写 audit。
7. agent 后续按公开协议请求 token；用户不需要手工配置每个 repo pattern/profile。

覆盖图：WF-00、WF-09、WF-10、WF-11。

### 4.2 首次配置与授权

入口：Dashboard 空状态或 GitHub Apps 空状态。

流程：

1. 用户添加 GitHub App 非秘密配置。
2. client secret 使用 write-only 字段。
3. 用户显式点击开始授权。
4. device flow 进入 pending。
5. 成功显示账号、过期时间和范围摘要。
6. 失败显示 expired/access_denied/network/config/secret store 错误。

覆盖图：WF-02、WF-03、WF-08。

### 4.3 reauth

触发：refresh token 失效、授权撤销、组织/SAML 策略变化或 unknown_error。

原则：

- Dashboard 和 GitHub Apps 都能看到需要行动。
- reauth 必须显式用户确认。
- 普通 token 请求不得自动触发 device flow。

覆盖图：WF-01、WF-03、WF-08。

### 4.4 人工模式：agent credential 与 policy

流程：

1. 创建 agent credential。
2. credential 只在创建时显示一次。
3. 之后只显示 fingerprint/last-eight。
4. 配置 host/owner/repo/profile/min_ttl/rate limit。
5. 高风险权限默认禁用，启用需要显著确认。
6. disable/rotate 都有审计。

覆盖图：WF-04、WF-08。

### 4.5 token issue、grant 与 revoke

流程：

1. 查看 token issue inventory。
2. 按 agent/repo/profile/status 筛选。
3. 查看 fingerprint/last-eight 和 expiry，不显示完整 token。
4. revoke 前显示影响说明。
5. pending 防重复点击。
6. 成功/失败写 audit。

覆盖图：WF-05、WF-06、WF-08。

### 4.6 审计追踪

流程：

1. 从 Dashboard 最近事件进入 Audit。
2. 按 correlation id、actor、event type、repo、result 过滤。
3. 查看详情 drawer。
4. 详情中只显示脱敏 secret metadata。

覆盖图：WF-01、WF-06。

## 5. 状态覆盖矩阵

| 状态 | 覆盖位置 | 说明 |
|---|---|---|
| 未配置 GitHub App | WF-02、WF-03 | 引导创建/添加 app |
| 未授权 | WF-02、WF-03 | 明确需要显式 device flow |
| 无 agent credential | WF-04、WF-09 | 人工模式引导创建；审批模式优先生成授权码 |
| 无审计记录 | WF-06 | 正常空状态 |
| 加载/pending | WF-08 和各页面说明 | refresh、token、revoke、audit 查询都防重复操作 |
| GitHub 网络不可达 | WF-08 | code + message + retry |
| refresh token 失效 | WF-01、WF-03、WF-08 | reauth_required，可行动 |
| app 未安装/用户无权限 | WF-03 | 在详情和授权状态中解释 |
| policy denied | WF-04、WF-08 | 不包含秘密，指出 repo/profile 拒绝 |
| secret store unavailable | WF-02、WF-07、WF-08 | 显示恢复路径，不显示秘密 |
| Host/Origin rejected | WF-08 | localhost 安全错误页 |
| 高风险操作确认 | WF-04、WF-05、WF-08、WF-09、WF-11 | revoke/disable/high-risk permission/reauth/高风险申请批准 |

## 6. 低保真阶段待确认问题

已确认边界：

1. 授权码默认一次性、短寿命；泄露/失败则撤销并重新生成。
2. 第一版部分批准只按仓库批准/拒绝；不开放 GitHub 原子权限操作，也不在审批页编辑 permission profile。
3. permission profile 仍可作为 agent 申请中的机器可读风险标签和后端授权语义，但在审批页只读展示。
4. discovery public node 严格仅限 `127.0.0.1`；public 只是无需凭证可读协议元数据，不是公网公开。
5. agent 自报 project/name/version/reason 只作为未验证声明显示。
6. 审批模式与人工模式必须通过顶部模式切换明确分离，默认审批模式。

仍待后续确认：

1. Token Issues 与 Grants 在人工模式中合并为一个页面，还是拆成两个导航项？
2. 高风险权限启用是否只二次确认，还是要求输入仓库名/类型化确认短语？
3. 审批模式中 Dashboard 是否只需要 pending approvals/reauth/system health 三类卡片？

这些问题只影响信息架构和交互细节，不影响后端 Phase 1 POC 并行推进。

## 7. 与高保真阶段的交接要求

高保真阶段必须保持或明确变更：

- 顶部模式切换；默认 Agent 审批模式；审批模式与人工模式左侧导航完全分离。
- Dashboard 的“需要用户行动”优先级。
- write-only secret 输入与不显示完整秘密约束。
- reauth 显式确认。
- revoke/disable/high-risk 的危险确认。
- 空/加载/错误状态覆盖。

任何减少页面、合并核心流程、隐藏危险操作或弱化安全警告的变化，都需要按项目变更控制处理。
