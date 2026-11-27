# CI/CD Policy — GH Token Broker

最近更新：2026-11-27

本文定义 CI/CD 的目标、分层门禁、引入时机和供应链边界。仓库已配置首个 CI workflow，但**没有已批准的 CD/发布自动化**。不得把 CI 配置当作“所有发布/供应链门禁已完成”的证据。

## 1. 原则

1. **本地验证优先，CI 做独立复核。** 开发者/agent 在提交前运行本地检查；CI 使用尽量相同的命令复核，避免“本地一套、CI 一套”。
2. **CI 门禁随代码风险分层引入。** 不为纯文档仓库虚构产品测试；一旦对应代码进入主干或合并流程，必须加入相应门禁。
3. **事实与计划分离。** “已配置”“计划配置”“本次已运行”必须明确区分，禁止把计划中的 CI 写成已存在能力。
4. **秘密不进 CI 日志。** CI 不打印 secret、token、master key、client secret、agent credential 或完整 bearer 值；秘密扫描失败必须阻塞。
5. **构建可复现优先。** 依赖版本锁定、工具链版本明确、构建输出可校验；供应链强化在发布前逐步加入。
6. **CD 不等于自动发布。** 本项目是 Windows 本地安全敏感软件；发布、签名、分发和自动更新需要单独批准。当前只允许把 CD 理解为“可审计的构建/打包/校验流程”。
7. **CI 触发避免无效重复，但不削弱合并门禁。** 短生命周期 PR 分支由 `pull_request` 检查把关；长期 `feat/**` 分支保留 push 早期反馈；`main` merge 后仍必须跑 push CI。
8. **PR 创建不等于合入 main。** PR CI 失败时分支保护必须阻止合并；修复应追加到同一分支并触发新的 PR 检查。
9. **首个 CI 平台已落地为 GitHub Actions。** 这是首个 CI workflow 的实现选择；CD/发布平台和发布自动化仍需单独决策。

## 2. 当前事实状态

| 项 | 当前状态 |
|---|---|
| CI workflow | **已配置首个 workflow**：`.github/workflows/ci.yml`，job/context 为 `ci` |
| CI 触发策略 | `pull_request` 对所有 PR 运行；`push` 只对 `main` 和 `feat/**` 运行；保留 `workflow_dispatch` 手动触发。`fix/**`/`chore/**` 短生命周期分支不单独跑 push CI，避免与 PR CI 重复 |
| CD/发布自动化 | **未配置、未批准** |
| secret scan | 本地脚本和 CI 均运行 `python scripts/check_secrets.py` |
| Go 条件检查 | workflow 在检测到 `go.mod` 时执行 gofmt/test/vet/build 及可用 race spot check；最近结果见 [PROJECT_STATUS](PROJECT_STATUS.md) |
| Windows 手动冒烟 | 未运行真实 GitHub/device flow/Credential Manager 端到端冒烟 |
| 依赖扫描/SBOM/签名/校验和 | 未配置 |

## 3. 分层门禁设计

### L0：仓库卫生门禁

适用：所有分支和文档变更。

首个 workflow 当前包括：

- secret scan。
- documentation authority check。
- whitespace/conflict marker 检查。
- Markdown 本地链接存在性检查。
- 生成的 wireframes 与设计源文件一致性检查（在对应工具链确定后）。

### L1：Go 基础门禁

适用：Go module 或后端代码进入合并流程后。

首个 workflow 当前包括：

- `gofmt` 检查。
- `go vet ./...`。
- `go test ./...`。
- `go build ./...`。
- 关键并发路径的 race spot check；是否全量 `-race` 取决于耗时和 Windows CI 能力。

### L2：Windows 与安全集成门禁

适用：daemon、secret store、helper、WebUI backend 可运行后。

计划包括：

- Windows runner 上的单元/集成测试。
- SQLite 加密 store 测试。
- loopback Host/Origin 防护测试。
- 日志脱敏测试。
- IPC/ACL 测试。
- Credential Manager 相关测试；交互式或真实账户链路可能需要手动冒烟，不应伪造为 CI 自动验证。

### L3：供应链与发布候选门禁

适用：首次对外发布或分发二进制前。

计划包括：

- 依赖版本锁定与 `go mod verify`。
- 漏洞/依赖扫描。
- license/notice 检查。
- SBOM 生成。
- 构建产物校验和。
- 签名/ provenance / 可复现构建评估。

### L4：发布/CD

适用：用户明确批准发布策略后。

可能包括 tag 构建、artifact packaging、checksum、release notes、签名和发布上传。当前没有任何自动发布授权。

## 4. 引入时机

1. **纯文档阶段**：可以先不配置完整 CI，但必须保留 secret scan。
2. **首次准备 push 到远端/开放协作前**：至少配置 L0。首个 L0/L1 workflow 已由用户授权添加。
3. **Go 代码准备合并到 main 前**：必须设计并尽量配置 L1；不能长期依赖人工记忆运行测试。
4. **可运行 daemon/helper/WebUI 出现前**：补 L2。
5. **首次发布前**：必须补 L3，并明确 L4 是否存在及其边界。

## 5. 文件归属

- 本文只定义 CI/CD 原则和门禁设计。
- 实际 workflow 一旦配置，应放在平台约定位置（例如未来的 `.github/workflows/`），并在本文记录“已配置”的事实。
- `AGENTS.md` 不写死具体 CI 命令、workflow 名称或平台细节，只链接本文。
- 本地命令和当前验证快照仍分别记录在 `docs/DEVELOPMENT.md` 与 `docs/PROJECT_STATUS.md`。
- CI 文档权威来源和 stale 状态检查规则登记在 `docs/authority-registry.json`。
