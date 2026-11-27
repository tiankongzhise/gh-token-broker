# THREAT_MODEL — GH Token Broker

状态：初始草案，属于发现/需求/架构基线的一部分，尚未获得完整人工批准。

## 1. 范围

本文覆盖 Windows 本地 GH Token Broker 的威胁模型：daemon、secret store、SQLite、MCP 控制面、exec wrapper、git credential helper、localhost WebUI 和 GitHub API 交互。

v1 不承诺防御同 Windows 用户上下文下完全恶意且具备任意代码执行能力的进程；但即使该攻击者超出范围，设计仍应减少秘密的无意暴露和长久留存。

## 2. 资产与安全目标

| 资产 | 保密性 | 完整性 | 可用性/备注 |
|---|---|---|---|
| refresh token | 高；只在 broker secret store 中 | 高；滚动链不能被并发写坏 | 丢失后应进入显式 reauth |
| parent access token | 高；不跨越 daemon 边界 | 高；有效性状态必须准确 | 可短期内存缓存 |
| child scoped token | 高；默认不进 MCP tool result/日志 | 高；scope/expiry 不得被放大 | 主动撤销依赖 inventory/可 revoke 材料 |
| client secret/private key | 高；不随程序分发 | 高 | 只由 daemon 使用 |
| master key/encryption key | 高；只放 Windows Credential Manager | 高；key version 必须正确 | 丢失后密文不可恢复，应走 reauth |
| agent credential | 高；只存 hash/派生校验材料 | 高；禁用/轮换必须生效 | 泄露后应可单独轮换 |
| 审计记录 | 不含秘密；元数据敏感性中 | 高；不能伪造“未发生”的授权结论 | v1 不承诺抵御同用户恶意篡改 |
| broker 可用性 | 不适用 | 不适用 | 本地开发依赖；故障应明确可恢复 |

## 3. 信任边界

| 边界 | 描述 | 主要风险 |
|---|---|---|
| TB-1 agent/MCP client ↔ broker | 模型、CLI 或 IDE agent 调用控制面 | token 泄入 transcript、凭证伪造、权限放大 |
| TB-2 browser ↔ localhost WebUI | 浏览器访问 loopback 管理界面 | DNS rebinding、CSRF、恶意网页触发管理操作 |
| TB-3 helper/shim ↔ daemon IPC | git credential helper、stdio shim、exec wrapper 请求 daemon | confused deputy、grant 重放、本地进程冒充 |
| TB-4 daemon ↔ GitHub API | device flow、refresh、scoped mint、check、revoke | 网络错误、API 语义变化、响应权限过宽 |
| TB-5 daemon ↔ SQLite/filesystem | 元数据、审计、加密 secret payload | 离线复制、损坏、非原子写入、备份泄露 |
| TB-6 daemon ↔ Windows Credential Manager/DPAPI | master key 或秘密材料的 OS 保护 | 同用户读取、换机不可恢复 |
| TB-7 source/dependencies ↔ build/runtime | Go/module/前端依赖与构建供应链 | 恶意依赖、篡改构建、未锁定版本 |

## 4. 攻击者与滥用场景

| ID | 攻击者/场景 | v1 态度 |
|---|---|---|
| A-1 | 诚实但会把 tool result 写入 transcript/log 的 agent | 重点防御：默认不返回 raw token |
| A-2 | 被 compromised 但只拥有既定 agent credential 的 agent | 重点防御：最小 repo/profile、grant 限制、审计、禁用/轮换 |
| A-3 | 同 Windows 用户完全恶意进程 | v1 非目标；后续 service account/operation-only API 增强 |
| A-4 | 同机其他用户或离线复制数据目录者 | 尽量防御：OS 文件权限、加密 secret payload、WCM/DPAPI |
| A-5 | 恶意网页/本地网页脚本 | 重点防御：Host/Origin validation、无默认 CORS、认证与 CSRF 设计 |
| A-6 | 网络中间人/GitHub API 异常 | TLS 与官方 API；处理错误语义，不自定义绕过 |
| A-7 | 恶意/受损依赖或构建链 | 后续发布前重点防御：锁定、扫描、最小依赖 |

## 5. 主要威胁与缓解

| ID | 威胁 | 现有/计划缓解 | 残余风险/待办 |
|---|---|---|---|
| T-01 | token 进入 MCP tool result、终端或模型上下文 | 默认不返回 raw token；grant id、exec wrapper、git credential helper、操作型 MCP | raw token 兼容模式仍未决；若存在必须显式启用并审计 |
| T-02 | refresh 并发导致滚动链断裂 | 单实例、account mutex/single-flight、持久化后再可用、重启恢复 | D-0002 已批准加密 SQLite 事务路径；实现时仍需并发/崩溃恢复测试 |
| T-03 | scoped token 权限或有效期被放大 | 请求/响应 scope 校验、以 `expires_at` 为准、min_ttl、safety margin | 父/子 token 失效语义必须实测 |
| T-04 | SQLite 离线复制导致秘密泄露 | 已批准字段级 AEAD + master key in WCM；SQLite 不只依赖文件隐藏 | key rotation/恢复细节待实现设计 |
| T-05 | 同用户恶意进程读取 WCM/内存 | v1 明确非目标；文档不得夸大安全性 | 后续可评估独立 service account |
| T-06 | 恶意网页对 WebUI 发起 CSRF/DNS rebinding | loopback bind、Host/Origin validation、默认无 CORS | 本地认证、session/CSRF token、随机端口或固定端口策略仍需详细设计 |
| T-07 | 本地进程冒充 agent/helper 使用 broker | per-agent credential、grant 单次使用、绑定 transport 上下文、审计 | named pipe/loopback IPC 的认证与 ACL 细节未完全设计 |
| T-08 | grant 重放或跨 agent 兑换 | 高熵 grant id、单次使用、expires/max_uses、绑定 agent/transport | 需要实现测试覆盖并发兑换 |
| T-09 | 日志/审计泄露秘密 | 禁止字段、fingerprint/last-eight、日志脱敏测试、secret scan | 需要实现期持续验证 GitHub 错误响应不透出秘密 |
| T-10 | 审计被篡改导致无法追责 | 追加式审计、correlation id、文件权限 | v1 不承诺抵抗同用户恶意篡改；可考虑后续签名链/WORM/export |
| T-11 | 备份包含可恢复秘密 | 只备份非秘密配置与 SQLite 密文/元数据；master key 不随备份 | 恢复演练和 master key 丢失 UX 待定义 |
| T-12 | 依赖供应链攻击 | 未开始实现；后续要求锁定版本、最小依赖、审查更新 | CI、依赖扫描、签名/发布校验尚未定义 |

## 6. 明确安全非目标

- 不防御同 Windows 用户上下文下已经完全恶意、可任意读写该用户内存/凭据的进程。
- 不阻止已授权 agent 在授权范围内故意滥用权限；只能通过最小权限、审计、撤销和禁用降低影响。
- 不保证 GitHub API、组织策略、SAML 或父/子 token 失效语义永远不变。
- 不依赖“流程保密”获得安全性。

## 7. 当前最需要补齐的安全设计

1. WebUI localhost 认证、session/CSRF 和 DNS rebinding 的完整机制。
2. helper/shim ↔ daemon IPC 的认证、ACL、transport context 绑定方式。
3. 审计与 token inventory 的保留期限、清理、导出和删除策略。
4. master key rotation、丢失恢复、备份恢复演练。
5. scoped token 父/子失效语义实测与 revoke 行为矩阵。
