# DEVELOPMENT — GH Token Broker

## 1. 开发状态入口

本文记录相对稳定的开发环境、目录约定、实现顺序、代码风格和命令来源。当前阶段、批准范围、产品实现状态和最近一次验证结果见 [PROJECT_STATUS](PROJECT_STATUS.md)。

不要因为本文存在而假定任何启动/测试命令已经可用；每条命令必须区分“已配置”“计划配置”和“本轮是否验证”。

## 2. 技术方向

### 2.1 核心实现

建议核心使用 Go：

- 单二进制包含 daemon、CLI、exec wrapper、git credential helper、MCP shim。
- 适合 Windows 本地分发。
- 方便将传输层与核心 token/policy 逻辑解耦。

后端 Phase 1 POC 已在 `feat/backend-core` worktree 初始化 Go module；在合并进 `main` 前，相关命令应在后端 worktree 执行。`go.mod` 当前要求 Go 1.26+，本轮开发环境实际使用 Go 1.27.1 windows/amd64。

### 2.2 存储

方向：

- SQLite：元数据、策略、审计、token inventory 和已批准方案中的加密 secret payload。
- Windows Credential Manager：已批准方案中只保存 master key。
- MVP secret store 已批准为加密 SQLite + master key in Credential Manager；批准证据见 [DECISIONS](DECISIONS.md#d-0002-secret-store-mvp)。

### 2.3 WebUI

WebUI 是管理面，技术栈待低保真/高保真阶段确认。当前不预设 React/Vue/Svelte 或 SSR。

## 3. 环境要求

初始开发环境建议：

- Windows 10/11
- Git for Windows
- Go stable toolchain；Phase 1 POC 的 `go.mod` 要求 Go 1.26+，本轮使用 Go 1.27.1 验证
- Python 3.x（用于当前仓库的 secret scan 脚本）
- PowerShell 5.1+ 或 PowerShell 7+
- GitHub App 测试实例与测试仓库

不应要求公网服务、数据库服务或额外系统依赖来完成基础开发。

## 4. 本地目录约定

计划目录结构：

```text
cmd/                    # 二进制入口；Phase 1 目前只有 gh-token-broker POC 命令
internal/               # 核心逻辑，不导出为公共 API
  config/               # 配置加载与校验
  githubapp/            # GitHub OAuth/device flow client
  platform/winmutex/    # Windows named mutex
  secretstore/          # secret store 抽象
  storage/sqlite/       # 加密 SQLite secret/account persistence
  tokenchain/           # device flow 完成、refresh chain、parent token cache
  broker/               # 未来：核心 broker facade
  policy/               # 未来：repo/profile policy
  audit/                # 未来：审计
  grant/                # 未来：grant lifecycle
  mcp/                  # 未来：MCP transport/tools
  web/                  # 未来：WebUI backend
docs/                   # 产品、架构、开发、测试文档
scripts/                # 仓库维护脚本
testdata/               # 未来：不包含真实秘密的测试数据
design/                 # 低保真/高保真设计产物
prototype/              # 未来：可运行示意 Demo
```

`cmd/` 与 `internal/` 当前只存在于后端 POC 分支 `feat/backend-core`；`design/wireframes/` 当前只存在于 WebUI 低保真分支 `feat/webui-wireframes`。合并前不要在主 worktree 假定这些文件可用。

### 4.1 CI/CD 与生成物归属

- CI/CD 门禁、workflow 引入时机、发布和供应链边界不在本文写死，统一见 [CI_CD](CI_CD.md)。
- `.gitignore` 修改时机和审查原则不在本文写死，统一见 [GITIGNORE_POLICY](GITIGNORE_POLICY.md)；实际规则以根 `.gitignore` 为准。
- 引入新工具链、编译产物、测试报告、runtime cache 或日志目录时，必须在同一任务中检查是否需要更新根 `.gitignore`。
- Go 源码、go.mod 和 go.sum 必须通过 `.gitattributes` 保持 LF；否则 Windows runner 的 CRLF checkout 会让 `gofmt -l` 误报全部文件。

## 5. 秘密与配置约束

### 5.1 绝不提交的内容

- GitHub access token / refresh token
- GitHub App client secret / private key
- agent credential 明文
- master key / encryption key
- 任意 bearer token、密码、私钥、session cookie
- 真实 token 的完整派生值或可用于认证的片段

### 5.2 示例写法

文档和示例只能使用明显占位符：

```text
<access-token>
<refresh-token>
<client-secret>
<agent-credential>
```

不得使用真实格式长度接近的假秘密做“逼真示例”，避免扫描误报和误用。

### 5.3 流程公开原则

架构、流程、威胁模型、策略结构和错误语义可以公开。项目安全不得依赖“攻击者不知道流程”。保密边界只覆盖秘密材料本身。

### 5.4 push 前秘密扫描

每次 push 前必须在仓库根目录运行：

```powershell
python scripts/check_secrets.py
```

要求：

- 扫描失败时不得 push。
- 不得为了绕过扫描而删除/弱化规则。
- 如果扫描误报，应先确认不是秘密，再用最小范围 allowlist 或调整示例写法处理。
- 如果真实秘密已经提交过，视为泄露：先撤销/轮换，再评估历史清理；不得只删除最新文件就当无事发生。

当前脚本是基线，不保证覆盖所有秘密格式。后续可引入 gitleaks/trufflehog 等成熟工具作为补充。

## 6. 实现顺序建议

### Phase 0：文档基线

交付：

- README
- PRD
- PROJECT_DISCOVERY
- ARCHITECTURE
- DEVELOPMENT
- TEST_PLAN
- AGENTS
- secret scan baseline

完成后停在人工审核门，不自动进入实现。

### Phase 1：核心 token chain POC

目标：

- 初始化 Go module。
- 实现配置加载。
- 实现 secret store 抽象；按已批准 D-0002 实现加密 SQLite + Windows Credential Manager master key。
- 实现 device flow 授权。
- 实现 refresh token 持久化和互斥刷新。
- 实现 parent token memory/cache。
- 用 mock GitHub API 完成核心单元测试。

不做：

- MCP
- WebUI
- scoped token
- 多 agent 策略

### Phase 2：安全交付通道

目标：

- `exec` wrapper。
- git credential helper。
- `min_ttl` 检查。
- 基础审计。
- Windows 手动/集成验证。

### Phase 3：policy + scoped token + grant

目标：

- per-agent credential hash。
- repo/profile policy engine。
- scoped child token mint/check/revoke。
- grant id 生命周期。
- token inventory。

### Phase 4：MCP

目标：

- localhost Streamable HTTP MCP。
- stdio shim。
- 授权状态、grant、audit、reauth 等 tools。
- transport authentication 与 DNS rebinding 防护。

### Phase 5：WebUI

按项目审核门先做：

1. 低保真 wireframes
2. 高保真设计
3. 可运行示意 Demo
4. 批准后正式联调实现

## 7. 代码约定

Phase 1 POC 已建立初始 Go 代码；约定如下，后续以实际配置为准：

### Go

- `gofmt` 格式化。
- Go naming conventions。
- 核心包放 `internal/`。
- 不在 transport 层处理秘密持久化细节。
- 错误必须带上下文，不吞错。
- 网络调用必须有 timeout。
- 不记录秘密值。

### 日志

- 使用结构化字段或清晰键值。
- 包含 correlation id。
- 禁止字段：`authorization`、`access_token`、`refresh_token`、`client_secret`、`password`、`token`、`secret`、`grant_secret` 的明文值。

### 配置

- 配置只放非秘密。
- secret 使用引用，例如 `secret_ref`。
- 配置示例使用占位符。

## 8. Git 约定

- 默认分支：`main`。
- 协作流程：GitHub Flow。
- 短期分支：`feat/<short-kebab>`、`fix/<short-kebab>`、`chore/<short-kebab>`。
- commit message：Conventional Commits 1.0.0，默认英文。
- 合并：独立 PR，默认 squash。
- 本项目初始作者：`notebook <tiankongzhise@163.com>`。
- push 前必须运行 secret scan。
- 不得提交 `.env`、私钥、token dump、运行时 SQLite 数据库或本地 Credential Manager 导出物。

## 9. 验证命令状态

| 用途 | 命令 | 状态 |
|---|---|---|
| 秘密扫描 | `python scripts/check_secrets.py` | 已配置，需每次 push 前运行 |
| Go 格式化 | 后端 worktree：`gofmt -w cmd internal`；检查时 `gofmt -l cmd internal` 应无输出 | 已在 Phase 1 POC 使用 |
| Go 单元测试 | 后端 worktree：`go test -count=1 -timeout=90s ./...` | 已在 Phase 1 POC 使用 |
| Go vet/build | 后端 worktree：`go vet ./... && go build ./...` | 已在 Phase 1 POC 使用 |
| Go race spot check | 后端 worktree：`CGO_ENABLED=1 go test -race -count=1 -timeout=90s ./internal/tokenchain ./internal/platform/winmutex` | 局部验证命令；尚未成为完整 CI 门禁 |
| MCP 测试 | 未定 | 未配置 |
| WebUI 测试 | 未定 | 未配置 |

## 10. 变更控制

以下内容一旦在后续阶段被批准，实质变化需要先创建 `docs/changes/CR-<id>.md`：

- 页面数量/核心 WebUI 流程
- MCP tool 契约
- 权限 profile 语义
- 数据模型和迁移
- secret store 方案
- 部署形态
- raw token 是否允许返回

CR 中写明原因、原/新行为、影响、迁移回滚、需要重审的门和批准状态。
