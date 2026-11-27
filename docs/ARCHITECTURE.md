# GH Token Broker 架构设计

## 1. 架构目标

GH Token Broker 的架构目标是：

1. 长期秘密只留在 broker secret store 中。
2. parent access token 不直接暴露给 agent。
3. 每次 GitHub 访问尽可能使用短期、仓库/权限受限的凭据。
4. token 不进入终端输出、MCP tool result、模型上下文或日志。
5. per-agent 身份、授权策略和审计可管理。
6. Windows 本地单用户运行，不公网暴露。
7. 架构和流程可以公开；安全只依赖密钥材料保密，而不依赖流程保密。

---

## 2. 总体架构

```text
┌──────────────────────────────────────────────────────────────┐
│                         User / Agent                          │
│                                                              │
│  Browser WebUI   MCP client   git   gh/script   manual CLI    │
└───────┬──────────────┬─────────┬──────────┬─────────┬────────┘
        │              │         │          │         │
        │              │         │          │         │
        ▼              ▼         ▼          ▼         ▼
┌──────────────────────────────────────────────────────────────┐
│                        Edge / Transport                       │
│                                                              │
│ localhost WebUI │ MCP HTTP │ MCP stdio shim │ git helper │ exec│
└───────┬──────────────┬─────────┬──────────┬─────────┬────────┘
        │              │         │          │         │
        └──────────────┴────┬────┴──────────┴─────────┘
                            ▼
┌──────────────────────────────────────────────────────────────┐
│                       Broker Core Daemon                      │
│                                                              │
│  AuthN/AuthZ  │ Policy Engine │ Grant Service │ Audit Service │
│  Token Service│ Refresh Worker│ Secret Store  │ GitHub Client │
└───────┬──────────────────────┬───────────────────┬───────────┘
        │                      │                   │
        ▼                      ▼                   ▼
┌──────────────┐     ┌──────────────────┐   ┌──────────────────┐
│   SQLite     │     │ Windows Credential│   │     GitHub       │
│ metadata/audit│     │ Manager / secrets │   │ API / Git HTTPS  │
└──────────────┘     └──────────────────┘   └──────────────────┘
```

---

## 3. 模块设计

### 3.1 Broker Core Daemon

常驻 Windows 用户会话内，负责全部秘密访问与 GitHub token 生命周期。

职责：

- 加载配置与策略。
- 管理 GitHub App 授权状态。
- 维护 refresh token chain。
- 缓存 parent access token。
- 创建和验证 scoped child token。
- 签发/兑换 grant。
- 记录审计。
- 为 MCP、WebUI、CLI、exec、credential helper 提供内部 API。

边界：

- daemon 是唯一允许接触 refresh token/client secret 的组件。
- transport 层不得直接读取 secret store。
- helper/shim 只与 daemon通信，不直接访问 SQLite 秘密字段。

### 3.2 Token Service

负责 parent token 与 child token 生命周期。

核心接口概念：

```text
GetParentToken(accountRef) -> internal parent token state
RefreshParentToken(accountRef) -> rotated token pair
MintScopedToken(accountRef, repo, permissionProfile, minTTL) -> child token metadata
ValidateIssuedToken(issueID) -> validity/scope status
RevokeIssuedToken(issueID) -> revocation result
```

关键规则：

- parent token 不跨越 daemon 边界。
- refresh 必须按 account/app chain 互斥。
- refresh 响应必须先持久化，再标记可用。
- child token 以 GitHub 返回的 `expires_at` 为准，不硬编码 8h。
- 签发时检查 `expires_at - now >= min_ttl + safety_margin`。

### 3.3 Refresh Coordinator

refresh token 是滚动凭证，并发刷新可能导致链断裂。Refresh Coordinator 必须提供：

- 单进程单实例约束。
- account-level mutex / single-flight。
- 数据库事务更新。
- 状态机：
  - `valid`
  - `refresh_required`
  - `refreshing`
  - `reauth_required`
  - `revoked`
  - `unknown_error`
- 重启后的状态恢复。

推荐逻辑：

```text
func ensureParent(account):
    if cached parent is usable:
        return cached parent

    lock(account.refreshMutex)
    reload state from persistent store
    if another execution already refreshed:
        return reloaded parent

    response := github.refresh(refreshToken)
    persist atomically(response.refreshToken, response.parentExpiry, metadata)
    keep parent access token in memory or encrypted cache
    unlock
```

注意：如果使用 refresh token，GitHub 会使旧 refresh token 和旧 parent access token 失效。因此不能让 transport 层并发绕过 coordinator。

### 3.4 GitHub Client

封装 GitHub API：

- device flow start/poll。
- refresh token exchange。
- scoped token creation。
- token check。
- token revoke。
- installation/repository metadata lookup。

要求：

- 所有请求带超时、User-Agent、API version。
- 可注入 base URL 以支持 GitHub Enterprise。
- 可 mock，用于单元和集成测试。
- 不把 token 写入错误 message。

### 3.5 Policy Engine

验证 agent 请求是否符合授权策略。

策略模型概念：

```yaml
agents:
  - id: agent-example
    credential_hash: <hash>
    enabled: true
    allowed_hosts:
      - github.com
    rules:
      - owner: example-org
        repositories:
          - repo-a
        profiles:
          - pr-write
    min_ttl: 2h
    rate_limit:
      requests_per_minute: 20

profiles:
  read-only:
    metadata: read
    contents: read
  pr-write:
    metadata: read
    contents: write
    pull_requests: write
```

校验顺序：

1. agent credential 是否存在且启用。
2. host 是否允许。
3. owner/repo 是否匹配规则。
4. permission profile 是否允许。
5. 高风险权限是否需要额外确认。
6. rate limit 是否通过。
7. min_ttl 是否可满足。

### 3.5A Agent Enrollment / Approval Service

默认 agent 接入采用审批模式，而不是要求用户手工编写完整 policy。

核心概念：

- **agent authorization code**：用户生成的一次性或短寿命高熵授权码，只允许 agent 提交接入/权限申请或完成绑定；不直接代表 GitHub 权限。
- **discovery public node**：严格绑定 `127.0.0.1`、无需凭证可读的协议元数据 endpoint，公开 API version、申请 schema、支持的 profile、能力标记和错误码。这里 public 指协议元数据公开，不是公网或 LAN 公开。
- **permission application**：agent 用授权码提交的机器可读申请，包含自报身份/项目上下文、host、owner/repo、profile、min_ttl、reason。
- **approval decision**：用户全部批准、按仓库部分批准/降权或拒绝。第一版支持 permission profile 降权，但不开放 GitHub 原子权限逐项编辑；对一次性跨多个仓库申请大量权限的申请必须突出批量/高风险警告。批准后系统创建或更新 agent credential、policy 和后续 grant/token 边界。

安全约束：

- agent 自报 project/name/version/reason 是未验证声明，不是安全事实。
- 授权码明文只应在生成时显示一次；服务端只保存 hash/派生值。
- 授权码过期、已使用或被撤销后不得再提交申请。
- 批准、部分批准、降权和拒绝都必须写审计。
- 高风险权限默认不批准或需要单独确认。

### 3.6 Grant Service

grant 用于解耦“授权决策”和“实际秘密交付”。

生命周期：

```text
create -> active -> redeemed -> expired/revoked
```

属性：

- grant id：高熵随机值。
- agent id。
- host/owner/repo/profile。
- 使用次数限制。
- 过期时间。
- 关联 token issue id。
- 创建来源（MCP/CLI/WebUI）。

兑换规则：

- grant id 不是 GitHub token，不包含可用 GitHub 秘密。
- 默认单次使用。
- 只允许绑定 agent/transport 上下文兑换。
- 兑换记录审计。

### 3.7 Audit Service

审计目标：

- 能回答“哪个 agent 在何时因为什么请求获得了哪个仓库的什么权限”。
- 能追踪 token issue、grant、revoke 和 reauth。
- 不记录秘密全文。

事件类型：

- `auth_started`
- `auth_completed`
- `auth_failed`
- `refresh_started`
- `refresh_succeeded`
- `refresh_failed`
- `token_scoped_minted`
- `token_checked`
- `token_revoked`
- `grant_created`
- `grant_redeemed`
- `grant_expired`
- `grant_revoked`
- `policy_denied`
- `agent_credential_created`
- `agent_credential_rotated`
- `agent_credential_disabled`
- `webui_admin_action`

审计字段至少包含：

- event id
- timestamp UTC
- actor type/id
- event type
- host/owner/repo
- profile
- result
- error code
- correlation id
- secret fingerprint/last eight（如适用）

### 3.8 Secret Store

负责长期秘密和必要 child token 的保密存储。已批准的 MVP 方案是 D-0002：**秘密材料字段级加密后存 SQLite，master key 存 Windows Credential Manager**。

接口仍应抽象为：

```text
PutSecret(ref, secret, metadata)
GetSecret(ref) -> secret
DeleteSecret(ref)
RotateSecretRef(ref, newSecret)
```

推荐数据形态：

- SQLite secret payload：`secret_ref`、`key_version`、`nonce`、`ciphertext`、`associated_data_context`、created/updated/revoked metadata。
- Windows Credential Manager：只保存 master key 值；target name 可公开，key 值不可公开。
- 加密算法使用 AEAD（例如 AES-256-GCM）；每条记录唯一随机 nonce。
- associated data 至少绑定 record type、account/secret ref 和 key version，防止密文错位。

要求：

- secret 不进入普通配置。
- 内存中尽量缩短明文驻留时间。
- 日志中脱敏。
- secret ref 可出现在数据库和审计中，secret value 不可。
- refresh token 密文和 refresh metadata 必须在同一 SQLite 事务中更新。
- child token 若为主动 revoke 而持久化，也必须与其 inventory 状态保持事务一致。

### 3.9 SQLite Store

SQLite 存非秘密或加密后的结构化数据。初版建议表：

#### `github_accounts`

- id
- host
- app_client_id
- user_login
- auth_status
- parent_expires_at
- refresh_expires_at
- refresh_secret_ref
- client_secret_ref nullable
- last_refresh_at
- last_error_code
- created_at / updated_at

#### `agents`

- id
- name
- credential_hash
- enabled
- created_at / updated_at
- disabled_at

#### `agent_authorization_codes`

- id
- code_hash
- label nullable
- expires_at
- max_uses
- use_count
- created_at
- revoked_at
- last_used_at

#### `permission_applications`

- id
- code_id
- agent_claimed_name/project metadata
- host/owner/repo/profile request_json
- min_ttl_seconds
- reason
- status pending/approved/partially_approved/rejected/expired
- created_at
- decided_at
- decision_json
- decision_reason

#### `agent_policies`

- id
- agent_id
- host
- owner
- repo_pattern
- profile
- min_ttl_seconds
- rate_limit_json
- enabled

#### `token_issues`

- id
- account_id
- agent_id nullable
- host/owner/repo
- permission_profile
- token_fingerprint
- token_last_eight
- encrypted_token_ref nullable
- expires_at
- issued_at
- revoked_at
- revoke_reason
- revoke_result

#### `grants`

- id
- grant_hash
- agent_id
- token_issue_id nullable
- host/owner/repo/profile
- expires_at
- max_uses
- use_count
- created_at
- redeemed_at
- revoked_at

#### `audit_events`

- id
- timestamp
- actor_type
- actor_id
- event_type
- host/owner/repo/profile
- result
- error_code
- correlation_id
- details_json

#### `schema_migrations`

- version
- applied_at

---

## 4. 核心流程

### 4.1 首次 device flow 授权

```text
User explicitly starts auth
  -> broker creates device code request
  -> browser displays verification page instructions
  -> user approves in browser
  -> broker polls token endpoint
  -> broker receives access token + refresh token
  -> secret store persists refresh token/client state
  -> account status becomes authorized
  -> audit auth_completed
```

安全约束：

- 普通 token/grant 请求不得自动启动 device flow。
- reauth 必须由用户显式确认。
- device code/user code 不能视为长期秘密，但也应避免日志持久化。

### 4.2 agent 接入、申请与审批（默认审批模式）

```text
user -> WebUI create agent authorization code
user -> agent: provide authorization code out-of-band
agent -> broker discovery public node: read protocol metadata
agent -> broker submit permission application(code, project, repos, profiles, minTTL, reason)
broker -> validate code expiry/use/revocation and request shape
broker -> create pending approval; no GitHub access granted yet
user -> Approval Inbox: approve all / approve or downgrade selected repositories / reject
broker -> atomically create or update agent credential + policy
broker -> write audit and return machine-readable decision
```

后续已批准 agent 请求访问：

```text
agent -> MCP authorize(repo, operation/profile, minTTL)
  -> transport authenticate agent credential
  -> policy engine validates host/repo/profile
  -> token service ensures parent token
  -> token service mints scoped child token
  -> validate expires_at >= minTTL + margin
  -> inventory token issue
  -> grant service creates short-lived grant
  -> MCP returns grant id and non-secret metadata
```

人工模式仍可直接编辑 agent credential/policy，但仅作为高级管理路径。

不返回内容：

- parent token
- refresh token
- client secret
- child token（默认路径）

### 4.3 exec wrapper

```text
agent runs: gtb exec --grant <id> -- gh ...
  -> CLI/daemon validates grant id
  -> grant marked redeemed or use_count incremented
  -> broker retrieves scoped child token internally
  -> child process environment gets GH_TOKEN/GITHUB_TOKEN
  -> stdout/stderr passthrough, but wrapper never prints token
```

限制：

- 子进程自己可以打印环境，无法完全防止恶意子进程泄露。
- 该设计主要防止 token 默认进入 shell/model transcript，不是对恶意子进程的强隔离。

### 4.4 git credential helper

```text
git operation -> credential helper get
  -> helper receives protocol/host/path
  -> helper asks daemon for credential matching repo and optional grant context
  -> daemon validates policy/grant
  -> daemon returns username x-access-token and scoped token to git
  -> token never passes through shell output
```

配置要求：

- 启用 `credential.useHttpPath`，让 helper 看到 repo path。
- helper 配置应明确覆盖或排在其他 helper 前，避免长期凭据优先命中。

### 4.5 操作型 MCP

对于高风险或强审计操作，MCP 可以直接提供操作而不是凭据：

- create pull request
- push branch
- comment issue
- read repo metadata

broker 在内部调用 GitHub API/git，仅返回操作结果。此模式是后续强化方向。

### 4.6 撤销流程

```text
user/agent requests revoke issue/grant
  -> broker validates permission
  -> grant: mark revoked locally
  -> token issue: if token value available, call GitHub single-token revoke
  -> update inventory
  -> audit revoke result
```

注意：

- 只 revoke parent token 不能假定 scoped child token 一并失效。
- child token 应逐个登记和撤销。
- 如需撤销整个 GitHub App authorization，应走 grant/app authorization 层级，并提示影响范围。

---

## 5. MCP 设计

### 5.1 控制面与数据面分离

MCP 是控制面，负责：

- 授权申请
- 状态查询
- grant 管理
- revoke
- audit summary
- reauth 入口

MCP 默认不是 secret data plane，不直接返回 raw token。

数据面由以下组件承担：

- git credential helper
- exec wrapper
- broker-side operation executor

### 5.2 Transport

优先：localhost Streamable HTTP。

备选兼容：stdio shim。

```text
stdio-only MCP client
  ↔ stdio MCP shim（无秘密）
  ↔ broker daemon authenticated IPC
```

HTTP 安全要求：

- bind `127.0.0.1`
- Authorization header，不接受 query token
- Host/Origin validation
- 默认无 CORS
- 不暴露到 LAN/WAN

### 5.3 初步工具草案

命名可在实现阶段调整：

- `github_auth_status`
- `github_list_allowed_access`
- `github_get_discovery_document`（或通过 localhost well-known HTTP endpoint，不一定是 MCP tool）
- `github_submit_permission_application`
- `github_get_application_decision`
- `github_request_access_grant`
- `github_revoke_grant`
- `github_revoke_token_issue`
- `github_audit_summary`
- `github_begin_reauth`
- `github_broker_health`

工具返回不得包含完整秘密。

---

## 6. WebUI 设计约束

### 6.1 页面初稿

- 顶部模式切换：默认 Agent 审批模式；审批模式与人工模式整套导航分离。
- Dashboard：授权状态、refresh 状态、pending approvals、最近失败、reauth 提醒。
- Approvals：生成 agent 授权码、审批 permission application、全部/按仓库部分批准、降权或拒绝。
- GitHub Apps：app/account/installation 状态。
- Agents：agent credential、策略、启用/禁用（仅人工模式）。
- Token Issues：发放、到期、revoke 状态。
- Grants：active/redeemed/expired。
- Audit：事件查询和详情。
- Settings：secret store、min_ttl 默认、bind 地址、日志级别。

### 6.2 安全约束

- 不显示完整 secret。
- 新 secret 输入 write-only。
- 高风险操作二次确认。
- 只 loopback 访问。
- WebUI 与 MCP 共享同一个 policy/audit core。

---

## 7. 配置设计

配置文件只存非秘密内容，例如：

```yaml
server:
  bind: 127.0.0.1
  port: 0 # 0 表示随机端口或启动时固定配置，最终实现决定
security:
  default_min_ttl: 2h
  raw_token_output: disabled
storage:
  sqlite_path: <local-app-data-path>
  secret_backend: encrypted-sqlite-with-wcm-master-key
github_apps:
  - name: example
    host: github.com
    client_id: <public-client-id>
```

不得写入：

- access token
- refresh token
- client secret
- private key
- master key
- agent credential plaintext

---

## 8. 错误处理

统一错误结构：

```json
{
  "error": {
    "code": "policy_denied",
    "message": "agent is not allowed to access this repository with this profile",
    "retryable": false,
    "correlation_id": "..."
  }
}
```

原则：

- code 机器可读。
- message 面向用户。
- 不包含 secret。
- GitHub 响应中的敏感授权内容不得原样透出。
- 网络错误与授权错误区分。
- reauth_required 必须清晰可行动。

---

## 9. 部署形态

### 9.1 v1：当前用户会话

- Task Scheduler 登录后启动，或用户手动启动。
- 以当前用户身份运行。
- 使用当前用户 Windows Credential Manager。
- 数据目录放 `%LOCALAPPDATA%`。
- 不作为 SYSTEM service 读取用户 Credential Manager。

### 9.2 后续增强：独立 service account

如需要更强长期秘密隔离，可评估：

- broker 以独立低权限服务账户运行。
- secret store 属于该账户。
- 当前用户/agent 只能通过 ACL 控制的 named pipe 请求操作。
- 尽量只暴露 operation-level API，不发放 raw token。

这不是 v1 承诺。

---

## 10. 可观测性

日志：

- 结构化 JSON 或文本日志。
- 包含 correlation id。
- 记录事件、结果、错误码。
- 不记录 token、authorization header、client secret、refresh token、grant secret。

指标（可选）：

- refresh 成功/失败次数。
- token mint 成功/失败次数。
- policy denied 次数。
- grant redeem/expire/revoke 次数。
- GitHub API latency。

---

## 11. 备份与恢复

需要备份：

- SQLite metadata/audit。
- 配置文件中非秘密部分。

不能备份或需要特殊处理：

- Windows Credential Manager 中秘密通常不适合直接备份。
- 如果换机/重装，应支持重新 device flow 授权。

恢复原则：

- 缺少 secret 时进入 reauth_required。
- 不得因为恢复失败而生成或猜测秘密。
- 审计和 inventory 可以保留，但秘密不可用时标记无法主动 revoke。

---

## 12. 安全架构边界

本项目能降低以下风险：

- 长期 PAT 泄露。
- token 进入模型上下文/终端/日志。
- 多 agent 混用同一 broad token。
- 缺少审计和撤销能力。

本项目 v1 不能解决：

- 同 Windows 用户完全恶意进程读取用户内存/凭据。
- agent 被授权后故意滥用其已授权仓库权限。
- GitHub 侧撤销、组织策略变化或 API 行为变化。
- 用户把秘密手动粘贴到不安全位置。

因此安全声明必须准确，不得把“本地加密 + 校验码”宣传成强恶意进程防御。
