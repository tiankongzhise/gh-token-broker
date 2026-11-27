# GH Token Broker

`gh-token-broker` 是一个规划中的 **Windows 本地 GitHub 凭据代理（Token Broker）**：它为本地 AI coding agents、CLI 和 Git 操作按需签发短期、最小权限、可审计的 GitHub 访问凭据，避免在开发机上长期保存和传播 PAT。

> 当前状态：需求与架构文档阶段。仓库尚未包含产品实现。

## 要解决的问题

本地开发环境中常见的 GitHub 凭据形态存在这些问题：

- PAT 或 OAuth token 有效期较长，泄露后的影响窗口大。
- 多个仓库、组织和 agent 混用同一凭据，权限边界不清。
- token 容易被打印进终端、MCP tool result、模型上下文或会话日志。
- PAT 无法通过 GitHub 公开 API 自动续签，所谓“自动轮换 PAT”无法真正闭环。
- Windows 上缺少一个面向 agent 场景的集中授权、发放、审计和撤销层。

## 核心思路

项目参考 `ghtkn` 的设计思想，但**不直接依赖 ghtkn**：

1. 使用 GitHub App 的 **expiring user access token + refresh token**，让操作仍然归因于用户本人。
2. broker 在本地维护 refresh chain；parent access token 只留在 broker 内部。
3. 优先通过 GitHub scoped token 能力，为每次请求生成按仓库和权限缩小的短期 token。
4. agent 不直接持有长期凭据；高风险场景尽量避免把 access token 放进 MCP tool result。
5. 通过 git credential helper、`exec` wrapper 或操作型 MCP 工具传递/使用凭据。
6. 本地 WebUI 负责配置、授权状态、策略、审计和重新授权。

## 保密边界

本项目公开讨论架构、流程和威胁模型。**流程设计本身不是保密性的一部分**，项目安全性不得依赖“攻击者不知道流程”。

真正需要保密的是：

- GitHub access token / refresh token
- GitHub App client secret / private key
- 本地 master key、加密密钥、agent credential
- 任何可用作认证的 bearer secret、私钥、密码和会话材料

这些秘密值及其派生值不得提交到仓库，不得写入日志，也不得作为示例使用真实值。每次 push 前必须运行机密信息检查；当前基线工具是 `scripts/check_secrets.py`。

## 目标使用方式

```text
agent / user / git / gh
        │
        │ MCP、exec wrapper 或 git credential helper
        ▼
Windows 本地 GH Token Broker daemon
        │
        ├── 验证 agent 身份与仓库/权限策略
        ├── 维护 refresh token chain
        ├── 按需签发/验证短期 scoped token
        ├── 记录审计与撤销状态
        └── 只返回授权结果、grant id 或操作结果
        ▼
GitHub API / Git over HTTPS
```

## 计划能力

- GitHub App device flow / web flow 首次授权。
- refresh token 滚动刷新、并发互斥和失效恢复。
- access token 剩余有效期检查，支持“发放时至少剩余 2 小时”这类策略。
- per-agent credential、仓库与权限 profile 绑定。
- scoped child token 发放、登记、到期清理与单独撤销。
- MCP 控制面：授权、状态、撤销、审计、重新授权。
- 数据面：`exec` wrapper 与 git credential helper，避免 token 进入模型上下文。
- localhost-only WebUI。
- SQLite 元数据/审计存储；秘密材料放 Windows Credential Manager 或加密存储。
- push 前机密信息扫描。

## 非目标

- 不做公网 SaaS 或多租户服务。
- 不实现“PAT 自动续签”；GitHub PAT 不支持这种完整自动化模型。
- 不声称能防御同 Windows 用户上下文下已经完全恶意的进程。
- 不把 client secret、private key 或用户 token 随项目分发。
- 不直接复制或依赖 `ghtkn`；仅借鉴其公开设计思想。

## 文档

- [产品需求文档](docs/PRD.md)
- [项目发现记录](docs/PROJECT_DISCOVERY.md)
- [架构设计](docs/ARCHITECTURE.md)
- [开发说明](docs/DEVELOPMENT.md)
- [测试计划](docs/TEST_PLAN.md)
- [项目操作规则](AGENTS.md)

## 当前实现状态

当前仓库只有产品、架构、开发和测试文档，以及基础的 push 前机密信息检查脚本。尚无 daemon、MCP server、WebUI 或 credential helper 实现。

## License

许可证尚未确定。虽然仓库当前为 public，但在选择并添加许可证前，不应假定本项目授予额外的再使用/再分发许可。
