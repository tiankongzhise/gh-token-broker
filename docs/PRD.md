# GH Token Broker 产品需求文档（PRD）

## 1. 产品概述

### 1.1 产品名称

- 产品名：GH Token Broker
- 仓库名：`gh-token-broker`

### 1.2 一句话定义

一个运行在 Windows 本地开发环境中的 GitHub 凭据代理，为本地 AI coding agents、CLI 和 Git 操作按需签发短期、最小权限、可审计的 GitHub 访问凭据。

### 1.3 背景

用户需要在多个 GitHub 仓库中让 agent 通过 HTTPS 执行 clone、push、PR 等操作。传统做法是把 PAT 或长期 OAuth token 写入 Windows Credential Manager 或 Git Credential Manager，但这带来长期泄露风险。PAT 又不能通过公开 API 自动续签，因此单纯做“Windows 凭据轮换器”无法闭环。

更合适的路径是使用 GitHub App 的 user access token + refresh token：user access token 默认 8 小时过期，refresh token 可滚动刷新，且操作仍归因于用户本人。本项目将该机制本地 broker 化，并补充 agent 授权码接入、机器可读权限申请、用户审批、scoped token、审计与安全交付通道。

### 1.4 参考而非依赖

本项目参考 `ghtkn` 的公开设计思想，尤其是：

- 使用短期 GitHub App user access token 替代长期 PAT。
- 用 `exec` 和 git credential helper 避免 token 进入终端或 agent transcript。
- 明确区分交互式 device flow 与非交互 token 获取。
- 支持最小剩余有效期策略。

但本项目不直接依赖 ghtkn，不复用其代码作为运行时依赖，也不要求用户安装 ghtkn。

---

## 2. 用户与使用场景

### 2.1 主要用户

- 在 Windows 上进行日常开发的个人开发者。
- 使用多个 coding agents / IDE agents / CLI agents 的用户。
- 需要让 agent 对多个 GitHub 仓库执行 Git 和 GitHub API 操作的用户。

### 2.2 次要用户

- 小型开发团队中的个人工作站用户。
- 需要向安全负责人解释本地凭据生命周期的技术用户。

### 2.3 核心场景

#### 场景 A：首次配置 GitHub App 授权

1. 用户在 WebUI 或 CLI 中添加 GitHub App client id。
2. broker 启动 device flow 或 web flow。
3. 用户在浏览器中显式确认授权。
4. broker 保存 refresh token，并记录授权账号、app、过期时间和安装范围。
5. 未明确由用户启动时，普通 token 请求不得自动发起 device flow。

#### 场景 B：agent 发起接入与权限申请（默认审批模式）

1. 用户登录本地 broker，生成一次性或短寿命 agent 授权码，并把授权码交给 agent。
2. agent 读取 broker localhost discovery public node，了解协议版本、endpoint、支持的 profile 和申请格式。这里 public 指无需凭证可读协议元数据，不是公网公开。
3. agent 用授权码提交权限申请，内容包括项目上下文、host、owner/repo、permission profile、min_ttl 和用途说明。
4. 用户在 Approval Inbox 查看申请、风险提示和 broker 校验结果，可以全部批准、按仓库部分批准/降权或拒绝。
5. 批准后 broker 创建或更新 agent credential、policy 和后续 grant/token 边界；拒绝则返回机器可读结果。
6. 后续 agent 请求仓库操作时，broker 再验证 credential、policy、parent token 状态并生成 scoped child token 或使用受控执行路径。
7. 原手工配置 agent credential/repo/profile 的方式保留为高级人工模式，不是默认接入路径。

#### 场景 C：git push/pull

1. git 调用 credential helper。
2. helper 根据 host/path 识别仓库。
3. broker 找到适用的授权或 grant。
4. broker 向 git 返回短期凭据。
5. token 不经过 shell 输出、MCP tool result 或模型上下文。

#### 场景 D：GitHub CLI / API 操作

1. 用户或 agent 使用 broker 的 `exec` wrapper 启动 `gh` 或脚本。
2. broker 将 token 注入子进程环境变量。
3. 子进程退出后 token 不再存在于该环境。
4. wrapper 不把 token 打印到 stdout/stderr。

#### 场景 E：refresh token 失效或授权被撤销

1. broker 收到 `bad_refresh_token`、401、权限失效或组织策略错误。
2. 状态转为 `reauth_required`。
3. broker 不自动启动 device flow。
4. WebUI/CLI 提醒用户显式重新授权。

#### 场景 F：token 泄露或高风险操作结束

1. 用户或系统请求撤销某个已发放 token。
2. broker 使用 token 值调用 GitHub 单 token revoke 能力。
3. broker 更新本地 inventory 和审计记录。
4. 如果整个授权不再可信，提示用户撤销 GitHub App authorization/grant。

---

## 3. 产品目标

### 3.1 业务目标

- 替代长期保存和共享 PAT 的本地工作方式。
- 降低 token 出现在模型上下文、终端和日志中的概率。
- 让多个 agent 的 GitHub 访问具备独立身份、策略和审计。
- 让 Windows 本地环境能够无人值守地维护短期 user access token。
- 在不依赖流程保密的前提下提供清晰的公开安全设计。

### 3.2 安全目标

- 发放的凭据尽可能短期、最小权限、限定仓库。
- parent access token 不直接发给 agent。
- refresh token、client secret 等长期秘密只由 broker secret store 保护。
- 任何 push 到远端的提交不得包含秘密材料。
- 日志、错误信息和审计不得包含完整秘密值。
- 默认只监听 localhost 或使用本机 IPC，不对公网提供服务。

---

## 4. 范围

### 4.1 v1 范围内

1. Windows 本地单用户 daemon。
2. GitHub.com 支持；GitHub Enterprise host 作为可配置扩展点。
3. 一个或多个 GitHub App 配置。
4. device flow 首次授权。
5. expiring user access token + refresh token 管理。
6. parent token 内部缓存与刷新互斥。
7. agent 授权码 bootstrap、discovery public node、权限申请与用户审批。
8. per-agent credential 与策略校验。
9. repo/permission profile 映射。
10. scoped child token 签发与剩余有效期检查。
11. `exec` wrapper 与 git credential helper。
12. MCP 控制面。
13. SQLite 元数据和审计存储。
14. Windows Credential Manager 或加密 SQLite 的秘密存储。
15. localhost-only WebUI 管理界面。
16. push 前机密信息扫描脚本。

### 4.2 v1 非目标

1. 公网部署、多租户 SaaS。
2. 自动轮换或创建 PAT。
3. 强制替代 Git Credential Manager 的全部能力。
4. 防御同用户上下文中完全恶意且拥有任意代码执行能力的进程。
5. 企业级 HSM/TPM/KMS 深度集成。
6. 多用户并发服务端权限模型。
7. 插件式通用 secret rotation 框架。原初设想中的通用轮换器已被更具体的 GitHub token broker 取代。
8. 把真实秘密值写入测试、示例、文档或 fixtures。

---

## 5. 关键需求

### 5.1 GitHub App 与授权管理

#### FR-1：GitHub App 配置

系统必须支持配置多个 GitHub App，每个配置至少包括：

- 名称
- host
- client id
- 可选 client secret 引用
- 授权用户 login
- app installation 范围缓存
- 是否启用 expiring user token

#### FR-2：首次授权

系统必须支持 device flow。web flow 可以作为后续增强。授权时必须使用 `offline_access` 或确认 app 已启用 user-to-server token expiration。

#### FR-3：授权状态

系统至少区分：

- `not_configured`
- `authorized`
- `refreshing`
- `reauth_required`
- `revoked`
- `error`

### 5.2 token 生命周期

#### FR-4：refresh chain

- refresh token 必须滚动保存。
- 使用 refresh token 后必须原子更新新 refresh token 与 parent access token 状态。
- 同一授权链的 refresh 必须互斥执行，避免并发刷新导致链断裂。
- `bad_refresh_token` 不得静默重试，必须进入 `reauth_required` 并告警。

#### FR-5：parent token 使用边界

parent access token 只用于 broker 内部：

- 创建 scoped child token。
- 查询 installation/repo/user 状态。
- 执行 broker 自己承担的 GitHub 操作。

parent token 默认不得作为 API/MCP 结果返回。

#### FR-6：scoped child token

在配置 client secret 且 GitHub API 可用时，系统应使用 scoped token 端点为请求生成按仓库和权限缩小的 child token。

发放前必须检查：

- `expires_at` 存在。
- 剩余有效期不少于请求或策略要求的 `min_ttl`。
- 仓库与权限匹配策略。

#### FR-7：child token inventory

如果 broker 发放 child token，必须记录：

- 发放时间
- 到期时间
- agent identity
- host、owner、repo
- 权限 profile
- token fingerprint / last-eight 或非敏感标识
- 是否已撤销
- 撤销时间与原因

如需支持主动撤销，token 值必须加密保存到过期或撤销成功为止；否则只能依赖自然过期。

#### FR-8：有效性验证

系统可以使用 GitHub token check API 或响应元数据验证 token 状态。验证结果不得记录完整 token。

### 5.3 agent 身份与策略

#### FR-8A：agent 授权码 bootstrap

系统应支持用户生成一次性或短寿命 agent 授权码。授权码必须高熵、可撤销、带过期时间，并且只能用于提交接入/权限申请或完成绑定，不得直接代表 GitHub 权限。

授权码批准前不得让 agent 获得 token、grant 或任意仓库访问能力。授权码明文最多只在生成时显示一次；之后只能显示 fingerprint/prefix、状态和过期时间。

#### FR-8B：discovery public node 与 permission application

broker 应提供严格绑定 `127.0.0.1` 的 discovery public node，返回协议版本、endpoint、支持的 permission profile、申请 schema、错误码和能力标记。该节点不返回秘密；这里 public 仅指本机无需凭证可读协议元数据，不表示公网或 LAN 可访问。

agent 应能使用授权码提交机器可读 permission application。application 至少包括 agent 自报身份/项目上下文、host、owner/repo、permission profile、min_ttl 和 reason。系统必须把 agent 自报信息标记为未验证声明，而不是安全事实。

#### FR-8C：用户审批与部分批准

系统应提供 Approval Inbox。用户可以全部批准、按仓库部分批准/降权或拒绝申请。第一版支持 permission profile 降权，但不开放 GitHub 原子权限逐项编辑。对一次性跨多个仓库申请大量权限的申请，必须突出批量/高风险警告，并要求用户逐仓库批准、降权或拒绝；高风险权限默认不勾选或需单独确认。

批准后系统应原子创建或更新 agent credential、policy 和后续 grant/token 边界；拒绝应返回机器可读结果。所有审批决定必须写审计。

#### FR-9：per-agent credential

系统不得只有一个全局校验码。每个 agent 应有独立 credential，服务端只保存 hash 或等效派生值。

credential 必须绑定：

- agent 名称
- 允许 host
- 允许 owner/repo 或 repo pattern
- 允许权限 profile
- 最小剩余有效期要求
- 速率限制与启用状态

#### FR-10：请求一致性校验

broker 必须验证“agent credential × host × owner/repo × permission profile × min_ttl”一致。仅知道校验码不能访问任意仓库。

#### FR-11：credential 传递位置

agent credential 不得作为 MCP tool 的普通业务参数传递。应使用 transport authentication、环境变量或 shim-local 配置，避免进入模型上下文。

### 5.4 token 交付通道

#### FR-12：默认不返回 raw token

默认路径不得把 access token 作为 MCP tool result 返回。优先级如下：

1. 操作型 MCP 工具，由 broker 内部使用 token。
2. grant id + `exec` wrapper / credential helper。
3. 显式启用的兼容模式才允许返回 raw scoped token，并必须记录高风险审计事件。

#### FR-13：grant id

grant id 必须：

- 高熵、不可猜测。
- 短期有效。
- 单次或限次使用。
- 绑定 host/repo/profile/agent。
- 不包含 GitHub token 本身。

#### FR-14：exec wrapper

系统必须提供把 token 注入子进程环境变量的执行方式，不向 stdout/stderr 打印 token。

#### FR-15：git credential helper

系统必须提供 git credential helper，支持 `credential.useHttpPath` 以识别仓库路径，并按策略选择授权。

### 5.5 MCP 控制面

#### FR-16：MCP 能力

MCP至少应提供以下逻辑能力，具体 tool 命名在实现阶段确定：

- 查询授权状态
- 查询 agent 可用仓库/权限 profile
- 申请 git/gh 操作 grant
- 撤销 grant 或 token issue
- 查询审计摘要
- 显式启动重新授权流程
- 查询系统健康状态

#### FR-17：传输形态

优先支持 localhost Streamable HTTP MCP。对于只支持 stdio 的 client，应提供无秘密 shim：

```text
agent ↔ stdio MCP shim ↔ broker daemon（named pipe 或 localhost authenticated IPC）
```

#### FR-18：localhost 安全

HTTP 监听必须：

- 只绑定 `127.0.0.1` 或等价 loopback。
- 不在 URL query 中接受 bearer secret。
- 校验 Host/Origin，降低 DNS rebinding/浏览器误调用风险。
- 默认关闭 CORS。

### 5.6 WebUI

#### FR-19：管理功能

localhost-only WebUI 至少提供：

- 授权状态列表
- GitHub App 配置列表
- Approval Inbox：生成 agent 授权码、查看待审批申请、全部/按仓库部分批准、降权或拒绝
- 顶部模式切换：默认 Agent 审批模式；人工模式为独立界面
- agent credential 与策略管理（仅人工模式）
- token issue / grant 审计
- reauth 入口
- revoke 操作
- 安全警告与状态解释

#### FR-20：秘密显示限制

WebUI 不得回显完整 token、refresh token、client secret、master key 或 agent credential。输入新秘密时采用 write-only 字段。

### 5.7 存储与加密

#### FR-21：SQLite

SQLite 用于元数据、策略、审计和 token inventory。必须明确区分秘密字段与非秘密字段。

#### FR-22：secret store

MVP 采用已批准的 D-0002 方案：秘密材料字段级加密后存 SQLite，master key 存 Windows Credential Manager。决策状态和批准证据见 [DECISIONS](DECISIONS.md#d-0002-secret-store-mvp)。

直接逐条使用 Windows Credential Manager 是被比较后未采用的备选方案；若未来要重新启用，必须先评估 refresh chain 事务一致性、child token inventory、主动 revoke 和孤儿 credential 清理，并按变更控制处理。

#### FR-23：加密要求

如果使用字段级加密：

- 使用 AEAD 算法，例如 AES-256-GCM。
- 每条记录使用唯一随机 nonce。
- 使用 key version。
- 使用 record type/account 等上下文作为 associated data，防止密文错位。

如果使用 SQLCipher 等成熟方案，也必须说明密钥来源、备份和恢复行为。

### 5.8 审计与撤销

#### FR-24：审计事件

至少记录：

- 授权创建/刷新/失败
- agent credential 创建/禁用/轮换
- token 发放/验证/撤销
- grant 创建/兑换/过期/拒绝
- 策略变更
- WebUI 管理操作

#### FR-25：审计脱敏

审计只记录秘密的 fingerprint、last-eight 或不可逆 hash，不记录完整秘密。

#### FR-26：撤销

支持：

- 撤销单个 child token。
- 撤销 grant。
- 禁用 agent credential。
- 标记整个 GitHub App authorization 为不可信并进入 reauth 流程。

---

## 6. 非功能需求

### 6.1 安全

- 默认 loopback only。
- 不提交秘密材料。
- 每次 push 前执行秘密扫描。
- 秘密扫描失败时必须阻止 push，除非用户明确了解并处理；不得通过删除扫描规则绕过。
- 安全不得依赖流程保密。流程、架构和威胁模型都可以公开，秘密仅限于密钥材料本身。
- 高风险权限（例如 workflow write、administration、secrets）默认禁用，需要单独启用并显著标记。

### 6.2 可用性

- refresh 失效时给出明确恢复路径。
- 用户不应需要理解 GitHub token 类型细节才能完成基本配置。
- agent 侧失败信息应可行动，但不泄露秘密。

### 6.3 可靠性

- refresh 操作单实例互斥。
- SQLite 状态更新具备事务语义。
- daemon 异常退出后可以根据持久化状态恢复。
- 崩溃导致无法恢复 refresh chain 时进入 reauth_required，而不是猜测状态。

### 6.4 性能

- 常规 token/grant 请求应在本地毫秒级完成，不包含 GitHub 网络请求时目标 p95 < 100ms。
- GitHub 网络操作必须有超时和重试边界。
- token 缓存不得突破 min_ttl 安全边界。

### 6.5 可维护性

- Go 单二进制作为主要实现方向。
- 核心逻辑与 MCP/WebUI/CLI 传输层分离。
- GitHub API 访问可 mock。
- 配置与秘密分离。

---

## 7. 状态与错误需求

### 7.1 空状态

- 未配置 GitHub App：引导用户创建/添加 app。
- 未授权：说明需要显式 device flow。
- 无 agent credential：引导创建第一个 agent credential。
- 无审计记录：显示正常空状态。

### 7.2 加载状态

- 授权查询、refresh、token 发放、revoke 都应有 pending/in-progress 状态，避免重复点击或并发操作。

### 7.3 错误状态

- GitHub 网络不可达。
- refresh token 失效。
- app 未安装到目标仓库。
- 用户没有仓库权限。
- agent credential 无效或禁用。
- 请求 repo/profile 不符合策略。
- token 剩余有效期不足 min_ttl。
- scoped token 创建失败。
- secret store 不可用。

错误返回必须包含机器可读 code 和人类可读 message，但不得包含秘密值。

---

## 8. 验收标准

### 8.1 MVP 验收

1. 可以在 Windows 上完成一次显式 device flow 授权。
2. 可以在不重新 device flow 的情况下用 refresh token 获取新 parent access token。
3. 并发请求不会同时触发多次 refresh。
4. 可以配置至少两个 agent credential，并验证不同 repo/profile 策略。
5. 可以按 repo/profile 生成 scoped child token，且签发时剩余有效期不少于配置的 2h。
6. parent token 不出现在 MCP tool result、日志或 WebUI。
7. git credential helper 可以完成一次私有仓库 HTTPS fetch/push 测试。
8. `exec` wrapper 可以运行一次 `gh` API 测试且不打印 token。
9. child token inventory 中有审计记录。
10. 可以手动撤销一个已发放 token，并记录撤销结果。
11. `scripts/check_secrets.py` 在仓库中运行通过，且发现测试用模拟秘密时能失败。

### 8.2 WebUI 验收

1. 只能 loopback 访问。
2. 能展示授权状态、agent 策略、审计摘要。
3. 任何页面不回显完整秘密。
4. reauth 必须显式用户确认后才开始。

---

## 9. 需求与测试映射

| 需求 | 主要验证 |
|---|---|
| FR-4 refresh chain | 单元测试 + mock GitHub integration + 并发测试 |
| FR-6 scoped token | mock scoped endpoint + expires_at 边界测试 |
| FR-9/10 agent policy | policy engine 单元测试 |
| FR-12/14/15 交付通道 | credential helper/exec wrapper 集成测试 |
| FR-16/17 MCP | MCP protocol integration test |
| FR-21/22/23 storage | 加密/decryption round-trip、错误 key、nonce 唯一性测试 |
| FR-24/25 audit | audit 写入与脱敏测试 |
| NFR secret scan | 阳性/阴性 fixture 测试 |

详细测试策略见 [TEST_PLAN.md](TEST_PLAN.md)。

## 附录：授权粒度与 operation capability 契约草案（CR-0002）

2026-11-28 高保真审核发现，授权模型需要从“仓库 + profile 降权”升级为统一用户授权心智加内部两层实现契约：

1. **per-repository permission matrix**：同一 application 内每个仓库独立决定；每个仓库可在申请 profile 上限内对 GitHub 原子权限选择 `write/read/none`；`none` 在 scoped token 请求中应表现为省略 permission key。
2. **统一用户授权心智**：Agent 审批模式只呈现“agent 能做什么”；用户不需要区分能力由 GitHub token permission、broker 代执行或未来其他安全机制实现。
3. **broker operation capability layer（内部实现）**：创建仓库、设置 approved branch protection template 等 GitHub 原生权限无法安全细分的高风险操作，不通过向 agent 交付 `administration:write` token 实现，而通过 broker 代执行的受控 operation capability 实现；该实现细节不属于审批模式主界面。

该附录是 CR-0002 契约草案索引，不是冻结需求；冻结以前端高保真审核和后续批准为准。


## 附录：Capability-based authorization broker 契约草案（CR-0003）

2026-11-28 用户进一步指出，项目不应被 GitHub 原生权限模型限制。授权需求应升级为用户层 capability-based authorization：

1. 用户决定“哪个 agent 对哪些资源在什么约束下能做什么”，而不是选择 GitHub permission 或理解底层实现方式。
2. 仓库管理能力必须按 agent 单独配置，并取代粗粒度 `Administration` 授权项。
3. scoped token、GitHub ruleset/protection、broker-side executor 和未来 proxy 都只是内部 enforcement substrate。
4. 核心安全不变量是 no-bypass：若授予受限 capability，agent 不得同时持有能绕过该限制的 token、credential 或操作入口。

该附录是 CR-0003 契约草案索引，不是冻结需求；冻结以用户明确批准为准。CR-0002 暂时保留为中间上下文，CR-0003 定稿后必须归档或标记 superseded。
