# PROJECT_DISCOVERY — GH Token Broker

## 1. 发现范围与当前事实

本文记录项目初始化阶段的需求发现、技术判断、参考项目分析和未决事项。当前仓库是全新仓库，没有既有代码、测试、CI 或产品实现。

| 项目 | 事实 |
|---|---|
| 仓库类型 | 新建 Git 仓库 |
| 当前阶段 | 见 [PROJECT_STATUS](PROJECT_STATUS.md) |
| 产品形态 | Windows 本地 daemon + MCP 控制面 + CLI/exec/git credential helper + localhost WebUI |
| 主要语言方向 | Go（建议，尚未开始实现） |
| 持久化方向 | SQLite 元数据/审计；加密 SQLite secret payload + Windows Credential Manager 保存 master key（D-0002 已批准） |
| 部署形态 | 本地单用户，不公网暴露 |
| 许可证 | `LGPL-2.1-only`（用户已确认） |
| 实现状态 | 见 [PROJECT_STATUS](PROJECT_STATUS.md) |

## 2. 用户明确目标

来自初始化对话的明确要求，整理为事实：

1. 用户有多个 GitHub 仓库，希望 agent 能通过 HTTPS 执行 PR 等操作。
2. 不希望长期 token 不符合安全规范。
3. 使用环境是 Windows 本地开发环境，不对公网服务。
4. 倾向于 GitHub App user access token + refresh token 模型。
5. agent 需要操作时向本项目申请 access token。
6. 希望发放 token 时至少还有 2 小时有效期。
7. 希望配置校验码，并校验校验码与申请的 GitHub 访问范围一致。
8. 希望 access/refresh token 加密保存在 SQLite，密钥放 Windows Credential Manager。
9. 可以参考 `ghtkn` 的设计，但不要直接依赖它。
10. 不把机密信息上传；push 前必须做机密信息检查，并作为项目约束写入 AGENTS。
11. 流程设计不应该是保密性的一部分；安全不得依赖 obscurity。
12. 仓库可见性选择为 public。
13. Git 作者名使用 `notebook`，邮箱使用用户指定的邮箱。

## 3. 关键判断

### 3.1 PAT 自动轮换不是合适目标

**判断类型：事实**

GitHub PAT 需要在网页中创建；公开 PAT 管理 API 不支持以普通用户自动化方式签发一个新的 PAT。因此本项目不以“自动轮换 PAT”为核心目标。

影响：

- 原初“通用 Windows 凭据轮换器”的方向被收窄为 GitHub 专用 token broker。
- PAT 最多支持半自动提醒、替换和验证流程，不是 v1 目标。

### 3.2 GitHub App user access token 适合用户身份归因场景

**判断类型：事实**

GitHub App user access token 默认 8 小时过期，可通过 refresh token 滚动刷新。操作归因于用户本人，而不是 app/bot。它还受用户权限与 GitHub App 权限/installation 范围交集约束。

影响：

- 满足“agent 操作仍然像用户本人操作”的需求。
- refresh token 与 client secret 的保护成为核心安全设计。

### 3.3 parent token 不应直接发给 agent

**判断类型：建议**

refresh parent token 会使旧 parent access token 立即失效。如果 agents 直接持有 parent token，broker 为保证新请求的有效期而刷新时，可能提前杀死已发出 token。

影响：

- parent token 只留在 broker 内。
- agent 应获得 scoped child token、grant id、exec/credential helper 结果，或由 broker 直接执行操作。

### 3.4 scoped child token 是最小权限方向，但存在验证义务

**判断类型：推断**

GitHub 提供创建 scoped user access token 的 API，可限制仓库和权限。该端点需要 client secret。文档表明响应含 `expires_at`，但父子 token 失效联动语义不能仅凭文档假设。

影响：

- 初版必须将 scoped token 行为写成可测试的适配层。
- 不能硬编码 child token 一定 8 小时有效，必须以 API 返回的 `expires_at` 为准。
- 首次实现需要用真实测试 app/repo 验证 parent refresh、parent revoke 与 child token 的关系。

### 3.5 MCP 直接返回 token 是高风险兼容路径

**判断类型：建议**

MCP tool result 通常进入 client/模型上下文和日志。直接返回 access token 会增加泄露面。

影响：

- 默认交付通道应是操作型 MCP、grant id + exec wrapper、git credential helper。
- raw token 返回只能作为显式启用的兼容模式，并记录高风险审计。

### 3.6 Windows 同用户隔离有限

**判断类型：事实 + 推断**

Windows Credential Manager/DPAPI 能保护静态秘密不被其他用户或离线副本直接读取，但不能作为同用户恶意进程的强隔离边界。`ghtkn` 作者也正是基于类似原因在 Windows 上禁用 refresh-token agent backend。

影响：

- 本项目 v1 不声称防御同用户完全恶意进程。
- 项目价值主要是减少长期 token、避免 transcript/logging 泄露、集中审计和最小权限，而不是创建无法穿透的本机安全边界。
- 后续可增强为独立 service account + operation-only API。

## 4. `ghtkn` 参考分析

### 4.1 `ghtkn` 是什么

`ghtkn` 是一个本地 CLI，用 GitHub App Device Flow 创建 8 小时 user access token，并通过 OS keyring、exec wrapper、git credential helper 等机制供本地命令使用。

### 4.2 可借鉴点

- 用短期 user access token 替代 PAT。
- `exec` 注入环境变量，不打印 token。
- git credential helper 是最安全的 git 交付方式。
- 普通获取命令不自动启动 device flow，防止诱导授权。
- 支持最小剩余有效期。
- 多 GitHub App/多 owner 映射。

### 4.3 与本项目差异

| 方面 | ghtkn | GH Token Broker |
|---|---|---|
| 产品形态 | CLI | 本地 daemon + MCP + CLI/helper + WebUI |
| Windows 自动 refresh | 当前明确禁用 | 核心目标之一 |
| client secret | 默认不需要 | scoped token 模式需要保护 client secret |
| per-agent policy | 无 | 核心需求 |
| MCP | 无 | 核心控制面 |
| WebUI | 无 | v1 目标 |
| 动态 scoped token | 非核心/受限 | 核心方向 |
| SQLite 审计 | 非核心 | 核心需求 |
| 依赖关系 | 参考对象 | 不直接依赖 |

## 5. 技术选型判断

### 5.1 核心语言：Go

**判断类型：建议；置信度：中**

选择 Go 作为核心实现方向：

优点：

- 单二进制分发适合 Windows 本地工具。
- 后台 daemon、CLI、helper 可以共享同一二进制。
- 适合实现 MCP/HTTP/IPC 服务。
- 与参考项目的生态方向一致，但不形成依赖。
- 静态编译降低部署复杂度。

代价与不确定性：

- Windows Credential Manager、Named Pipe、DPAPI 集成需要 Windows-specific 代码。
- WebUI 若复杂，仍需单独前端技术选择。
- SQLite 驱动选择需要评估纯 Go/ cgo 的发布影响。

备选：

- .NET/C#：Windows 集成最自然，但用户此前提到 Python/Go，且 Go 单文件 CLI 生态更贴近参考设计。
- Python：原型快，但运行时分发、脚本篡改和后台服务化较弱。

### 5.2 持久化：SQLite

**判断类型：建议；置信度：高**

项目需要本地结构化状态、事务、审计和 inventory，但不需要服务端数据库。SQLite 适合：

- 单用户本地 daemon
- 事务性 refresh state 更新
- 审计追加查询
- token inventory
- 备份和恢复相对简单

需要后续确定：

- SQLite 驱动。
- schema migration 方案。
- D-0002 已批准，秘密字段采用字段级 AEAD；SQLCipher 不再是主路径，除非未来用新的 decision/CR 重新评估整库加密、备份和 key 管理语义。

### 5.3 秘密存储：建议加密 SQLite + master key in Credential Manager

**判断类型：技术选择；状态：已批准为 D-0002**

候选 A：秘密直接逐条存 Windows Credential Manager。

- 简单，不需要 master key。
- generic credential blob 有大小限制，但 parent/refresh/client secret 通常足够。
- 与 SQLite 元数据分散在两个存储中，refresh chain 和 inventory 更新无法同事务提交。
- 大量 child token inventory 不适合全部塞入 Credential Manager，容易产生孤儿项和清理问题。

候选 B：秘密材料字段级加密后存 SQLite，master key 存 Windows Credential Manager。

- 更适合结构化秘密、refresh chain 与 child token inventory。
- 可以把密文、expiry、状态和审计元数据放进同一 SQLite 事务。
- 支持 key version、AEAD associated data 和较清晰的备份语义。
- 实现复杂度更高，必须正确处理 nonce、key rotation 和恢复。

当前决策：MVP 采用候选 B，已由用户批准为 D-0002。直接 Credential Manager 是被比较后未采用的备选方案；若未来要重新启用，必须重新评估 refresh chain 事务一致性、token inventory、主动撤销和孤儿 credential 清理。详细理由和批准证据见 [DECISIONS](DECISIONS.md#d-0002-secret-store-mvp)。

### 5.4 前端复杂度：低到中

**判断类型：推断；置信度：中**

WebUI 是管理界面，不是高交互消费级产品。主要页面：

- dashboard/status
- GitHub Apps/授权
- agents/policies
- token issues/audit
- settings/security

复杂度来自状态可视化、表单、确认流和错误状态，而非复杂图形或实时协作。可以先用服务端渲染或轻量 SPA。最终技术选择在低保真/高保真阶段确认。

## 6. 安全约束

### 6.1 机密信息边界

秘密包括：

- access token / refresh token
- client secret / private key
- master key / encryption key
- agent credential
- bearer secret、密码、私钥、会话材料

这些秘密及真实派生值不得进入：

- Git 仓库
- 文档示例
- 测试 fixtures
- 日志
- MCP tool result
- WebUI 页面
- issue/PR 描述

### 6.2 流程公开原则

流程设计、架构、威胁模型和策略结构不是秘密。项目安全性不得依赖攻击者不知道流程。公开仓库中可以完整描述认证流程、存储结构和撤销逻辑；真正保密的是密钥材料。

### 6.3 push 前检查

每次 push 前必须执行：

```powershell
python scripts/check_secrets.py
```

该脚本检查当前工作区和 Git 历史中的常见秘密模式，只输出文件、行号和类型，不输出匹配秘密值。该脚本是基线，不排除后续引入 gitleaks/trufflehog 等更成熟工具。

## 7. 风险与缓解

| 风险 | 影响 | 缓解 |
|---|---|---|
| refresh 并发导致链断裂 | 需要重新授权 | 单实例、账户级 mutex、事务写入 |
| scoped token 父/子失效语义变化 | 已发 token 提前失效 | 以 expires_at 为准、真实环境验证、inventory、错误可观测 |
| MCP tool result 泄露 token | token 进入模型/日志 | 默认不返回 raw token，使用 grant/helper/exec |
| client secret 本地泄露 | 可滥用 OAuth/scoped API | 加密存储、最小权限、不随程序分发、支持轮换 |
| 同用户恶意进程 | 可能读取用户秘密或调用 broker | v1 明确非目标；后续 service account/operation-only API |
| organization/SAML 策略变化 | token 失效 | reauth_required、清晰恢复路径 |
| 误把秘密提交到 public repo | 必须旋转和清理历史 | push 前扫描、.gitignore、文档约束、泄露响应流程 |

## 8. 未决事项

1. scoped token 父子失效语义在目标 GitHub App 上的实测结果。
2. SQLite 驱动与 schema migration 方案。
3. WebUI 技术栈与页面范围。
4. 是否支持 GitHub Enterprise host 的优先级。
5. raw token 兼容模式是否默认存在，还是仅编译/配置为高级模式。
6. 是否需要 operation-only MCP 作为第一交付通道。

## 9. 置信度摘要

| 判断 | 置信度 | 依据 |
|---|---|---|
| PAT 不能完整自动轮换 | 高 | GitHub 公开文档/API 能力 |
| user access token + refresh 适合本场景 | 高 | GitHub 官方 token 生命周期 |
| Go 适合核心实现 | 中 | 项目形态与部署需求，未开始验证 |
| SQLite 适合本地状态/审计 | 高 | 单用户、事务、结构化查询需求 |
| scoped token 可作为主要发放方式 | 中 | 官方端点存在，但父/子语义需实测 |
| Windows 同用户强隔离不可承诺 | 高 | OS 安全边界与参考项目设计约束 |
