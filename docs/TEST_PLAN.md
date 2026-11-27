# TEST_PLAN — GH Token Broker

## 1. 测试目标

验证 GH Token Broker 能在 Windows 本地安全、可靠地管理 GitHub App user token 生命周期，并按策略向 agent/git/gh 交付短期凭据。

重点不是追求任意覆盖率数字，而是覆盖高风险行为：

- refresh token 滚动与并发。
- parent token 不泄露。
- scoped token 有效期与权限边界。
- agent policy 一致性。
- grant/exec/credential helper 交付路径。
- 秘密不脱敏、不入库、不入 git。
- 异常和撤销路径可恢复。

## 2. 测试分层

| 层级 | 目标 | 是否依赖 GitHub |
|---|---|---|
| 单元测试 | 纯逻辑、状态机、策略、加密、时间计算 | 否 |
| 集成测试 | SQLite、secret store、MCP/HTTP、helper、mock GitHub API | 否或可选 |
| 合约测试 | GitHub API 请求/响应 schema 与错误处理 | mock 为主 |
| Windows 手动测试 | Credential Manager、git HTTPS、Task Scheduler、WebUI loopback | 是 |
| 安全测试 | 日志脱敏、secret scan、Host/Origin、raw token 不泄露 | 否/是 |
| 冒烟测试 | 发布前核心链路 | 是，测试仓库 |

## 3. 单元测试计划

### 3.1 Token Service

覆盖：

- parent token 仍有效时直接复用。
- parent token 剩余不足时触发 refresh。
- refresh 成功后新旧状态更新。
- refresh 失败进入正确状态。
- `bad_refresh_token` 进入 `reauth_required`。
- refresh response 缺字段时不得写坏状态。
- clock skew / safety margin 计算。
- `min_ttl` 恰好满足、差 1 秒、超过时的边界。
- scoped token `expires_at` 为空、过去、不足、满足时的行为。

### 3.2 Refresh Coordinator

覆盖：

- 同一 account 并发 N 个请求只执行一次 refresh。
- refresh 期间后续请求等待并可复用结果。
- refresh 失败不会留下半更新状态。
- 进程重启后可从持久化状态恢复。
- 多 account 互不影响。
- 状态机非法迁移被拒绝。

### 3.3 Policy Engine

覆盖：

- 不存在/禁用的 agent credential 被拒绝。
- host 不匹配被拒绝。
- owner/repo 不匹配被拒绝。
- permission profile 不在允许列表被拒绝。
- 高风险权限默认拒绝。
- rate limit 触发。
- repo pattern 边界，防止 `repo` 误匹配 `repo-evil`。
- 全局 credential 不能越权访问未绑定 repo。

### 3.4 Grant Service

覆盖：

- grant id 高熵且不直接包含 token。
- grant 创建、兑换、过期、撤销状态迁移。
- 单次 grant 不能重复兑换。
- grant 与 agent/repo/profile 绑定。
- 过期边界。
- grant hash 存储而不是明文存储。

### 3.5 Secret Store / 加密

覆盖：

- put/get/delete round-trip。
- 错误 key 无法解密。
- nonce 不重复。
- key version 兼容。
- associated data 被篡改时解密失败。
- secret store 不可用时错误可行动。
- 日志输出不包含明文秘密。

如果使用 Windows Credential Manager：

- credential target 不存在。
- credential blob 损坏/格式错误。
- 多账号引用隔离。
- 不读取不属于本项目的 target。

### 3.6 SQLite Store / Migration

覆盖：

- schema migration 顺序执行。
- 重复启动不重复迁移。
- 事务失败回滚。
- token inventory 唯一约束。
- audit append 查询。
- 数据库损坏/锁定时的错误路径。

### 3.7 时间/有效期逻辑

覆盖：

- UTC 存储。
- 本地时区不影响比较。
- 系统时间小幅偏差。
- `min_ttl=2h` 边界。
- 过期 grant/token 清理任务。

## 4. 集成测试计划

### 4.1 Mock GitHub API

建立可控 mock server，覆盖：

#### Device flow

- authorization pending
- slow down
- access denied
- device code expired
- success

#### Refresh

- success + rolling refresh token
- bad refresh token
- network timeout
- 429/500
- malformed response

#### Scoped token

- success with repo/permission restrictions
- expires_at 缺失
- 401/403/404/422
- parent token invalid
- repository inaccessible
- permission escalation rejected

#### Check/revoke

- token valid
- invalid token returns 404
- revoke success
- revoke failure

要求 mock server 测试不得使用真实秘密。

### 4.2 MCP integration

覆盖：

- 无 credential 被拒绝。
- 错误 credential 被拒绝。
- credential 不通过 URL query 传递。
- Host/Origin 不合法被拒绝。
- 允许 agent 只能看到/申请授权范围内 repo。
- grant tool result 不包含 GitHub token。
- audit summary 不包含秘密。
- MCP stdio shim 与 daemon 的失败重连/错误传播。

### 4.3 exec wrapper integration

使用本地打印/测试命令验证：

- token 被注入子进程环境。
- wrapper stdout 不包含 token。
- wrapper stderr 不包含 token。
- 子进程失败时 exit code 正确传递。
- grant 过期后不能执行。
- grant 单次使用后不能重复使用。

注意：测试命令不得打印环境变量中的真实 token；用 mock secret 时也只检查不出现，不输出。

### 4.4 git credential helper integration

使用本地 mock git credential input 或测试仓库验证：

- `credential.useHttpPath` 下能解析 owner/repo。
- host 不匹配返回空/失败。
- policy deny 时 helper 不返回密码。
- helper stdout 只在协议要求字段中包含密码，不写额外日志。
- token 不写入磁盘 cache。
- 多个 GitHub App/owner 映射选择正确。

### 4.5 WebUI integration

未来实现后验证：

- loopback 可访问，外部地址不可绑定。
- 未授权访问被拒绝。
- CSRF/Origin 防护。
- secret 字段 write-only。
- reauth 需要显式确认。
- revoke 高风险操作有确认。

## 5. Windows 专项测试

- Windows Credential Manager 存取。
- `%LOCALAPPDATA%` 数据目录权限。
- 非 ASCII 用户路径。
- 锁屏/注销/重启后的状态恢复。
- Task Scheduler 登录启动。
- 不追加以 SYSTEM 身份读取用户凭据的测试路径；若后续支持 service account，单独设计。
- 长路径与空格路径。
- Windows Named Pipe ACL（如果实现）。
- DNS rebinding/Host header 防护。

## 6. 安全测试

### 6.1 日志脱敏

构造包含假 token 字段的错误对象，验证日志不会输出完整值。重点字段：

- authorization
- access_token
- refresh_token
- client_secret
- token
- secret
- password
- grant_secret

### 6.2 secret scan

当前脚本：`python scripts/check_secrets.py`

测试要求：

- 干净仓库通过。
- 含模拟 GitHub token 的临时文件失败。
- 输出不包含完整模拟 token。
- 删除/修正后再次通过。

不得把真实秘密作为测试 fixture。

### 6.3 MCP transport 安全

- 不接受 query string credential。
- 不开放 CORS。
- Origin/Host 校验。
- 错误响应不泄露配置路径中可能敏感的用户信息以外的秘密。
- localhost-only 绑定验证。

### 6.4 权限升级防护

- agent 请求超过 profile 的权限被拒绝。
- scoped token API 返回权限超出请求时拒绝发放并记录。
- 请求 repo 与 scoped repo 不一致时拒绝。

## 7. 真实 GitHub 冒烟测试

只在手动/受控环境执行，使用测试 GitHub App 和测试仓库。不得用生产重要仓库。

### 前置条件

- 测试 GitHub App 已启用 device flow 和 expiring user token。
- 测试仓库无重要数据。
- app installation 只包含测试仓库。
- 测试人员知道如何撤销授权。

### 冒烟步骤

1. 显式启动 device flow 并完成授权。
2. 验证授权状态为 authorized。
3. 强制或等待 parent token 接近过期，触发 refresh。
4. 验证旧 refresh token 不再保留在状态里。
5. 申请一个 repo/profile scoped grant。
6. 使用 exec wrapper 调用只读 GitHub API。
7. 使用 git credential helper fetch 测试仓库。
8. 在测试分支 push 一个无害 commit 或由测试人员选择跳过 push。
9. 撤销 token issue，验证后续使用失败。
10. 禁用 agent credential，验证新 grant 被拒绝。
11. 撤销 GitHub App authorization，验证状态进入 reauth_required。
12. 检查审计记录完整且无完整秘密。

## 8. 回归测试原则

发现 bug 时优先增加能触发原缺陷的测试，例如：

- refresh 并发导致状态覆盖。
- min_ttl 边界错误。
- scoped token expiry 误判。
- grant 单次使用被重复兑换。
- 错误日志泄露 token。
- repo pattern 越权匹配。

## 9. 测试数据规则

- 不使用真实 token/client secret/private key。
- 模拟秘密应明显标记为 fake，并避免真实前缀完整格式，除非 fixture 专门用于验证扫描会被拒绝且不入库。
- 测试仓库名、账号名使用占位或测试专用资源。
- 测试结束后清理临时授权和 token。

## 10. 当前验证状态

| 项目 | 状态 |
|---|---|
| 单元测试框架 | 未配置 |
| 集成测试框架 | 未配置 |
| mock GitHub API | 未配置 |
| Windows 手动测试 | 未运行 |
| secret scan | 脚本已配置，初始提交前运行 |
| CI | 未配置 |

## 11. 发布前最低检查清单

实现达到可发布阶段前，至少完成：

- 所有核心单元测试通过。
- refresh 并发测试通过。
- policy/scoped/grant 集成测试通过。
- exec/git credential helper Windows 测试通过。
- secret scan 通过。
- 日志脱敏测试通过。
- 真实测试仓库冒烟通过。
- 文档中的启动、配置、恢复步骤与实际一致。
