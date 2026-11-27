# DOCUMENTATION_AUDIT — GH Token Broker

最近审计：2026-11-27

范围：README、AGENTS、LICENSE、SECURITY、VERSION、docs/PRD、ARCHITECTURE、DEVELOPMENT、TEST_PLAN、PROJECT_DISCOVERY、CI_CD、VERSIONING、BRANCHING、COMMIT_MESSAGES、GITIGNORE_POLICY、INFORMATION_AUTHORITY、authority-registry.json、branch-ownership.json、scripts/check_secrets.py。

目的：确认文档是否覆盖项目治理、需求、架构、安全、开发、测试和交付要求，并识别缺失或不一致。

## 1. 总体结论

现有文档对产品目标、token 生命周期、refresh 并发、MCP/WebUI 安全约束、测试分层、秘密扫描、CI/CD 和 Git 治理已有较好覆盖。早期“可变状态塞进 AGENTS”“缺少决策/安全/威胁模型入口”的高优先级问题已关闭。

当前主要风险转为：

1. 同一可变事实在 artifact、policy、决策和状态文档中重复登记，导致状态漂移。
2. 若干实现前必须回答的本地认证、数据保留、运维和权限 profile 细节仍未定义。
3. CI 已落地但供应链、发布和完整安全门禁尚未实现。
4. 版本控制基础刚建立，但 release notes、artifact packaging 和自动发布流程仍未设计或批准。

本轮已新增单一权威来源机制来降低第一类风险；剩余缺口见第 3 节。

## 2. 本轮已关闭/部分关闭的问题

| ID | 问题 | 证据/影响 | 状态 |
|---|---|---|---|
| DOC-001 | 许可证未确定且没有许可证文本 | README 原声明“许可证尚未确定”；仓库无 LICENSE | **已关闭**：用户确认 `LGPL-2.1-only`，新增 `LICENSE`，README 和 D-0001 已更新 |
| DOC-002 | `AGENTS.md` 同时包含长期规则、当前阶段、批准、角色状态、验证状态等可变内容 | 可变状态容易过期，agent 不知道更新哪里 | **已关闭**：AGENTS 改为框架约束 + 文档地图；可变状态迁入 `docs/PROJECT_STATUS.md` |
| DOC-003 | 缺少决策日志/ADR 入口 | license、secret store、并行 worktree 等选择无统一状态 | **已关闭**：新增 `docs/DECISIONS.md` |
| DOC-004 | secret store 表述不一致/矛盾 | 用户初始目标是加密 SQLite；发现文档曾倾向直接 Credential Manager；测试计划已包含加密测试 | **已关闭**：用户已批准 D-0002，MVP 采用加密 SQLite + WCM master key |
| DOC-005 | 缺少独立安全政策和泄露响应入口 | 秘密约束分散在 README/AGENTS/DEVELOPMENT | **已关闭**：新增根 `SECURITY.md` |
| DOC-006 | 缺少结构化威胁模型 | 安全边界散见于发现/架构，缺少资产/攻击者/信任边界视图 | **已关闭**：新增 `docs/THREAT_MODEL.md` |
| DOC-007 | AI 署名和贡献者身份政策的详细记录占用 AGENTS 顶部且难以演进 | 推送前必须可见，但历史证据不应挤占主规则 | **已关闭**：新增 `docs/GIT_GOVERNANCE.md`，AGENTS 保留简要硬约束 |
| DOC-008 | CI/CD 和 `.gitignore` 缺少专门规范，存在被写死进 AGENTS 的风险 | CI/CD 只在审计/威胁模型中零散出现；`.gitignore` 有规则文件但没有维护原则 | **已关闭**：新增 `docs/CI_CD.md` 与 `docs/GITIGNORE_POLICY.md` 并接入文档地图；首个 CI 实施由 DOC-109/D-0009 跟踪 |
| DOC-009 | artifact/状态文档会写死审批或验证状态，导致与 PROJECT_STATUS/DECISIONS 漂移 | WIREFRAMES draft 状态与低保真批准不一致；CI 配置状态也多处漂移 | **已关闭/持续 enforcement**：新增 `INFORMATION_AUTHORITY.md`、`authority-registry.json` 和 checker；后续新增事实类型必须登记 |

## 3. 仍开放的文档缺口

| ID | 严重程度 | 缺失/不一致 | 建议处理方式 |
|---|---|---|---|
| DOC-101 | 高 | WebUI localhost 认证、session、CSRF、DNS rebinding 细节不完整 | 在低保真前至少补充架构约束；实现前形成明确设计 |
| DOC-102 | 高 | helper/shim ↔ daemon IPC 的认证、ACL、transport context 绑定方式不完整 | 后端 Phase 2 前补架构；影响 API 时建 CR |
| DOC-103 | 高 | scoped token 父/子失效语义没有实测矩阵 | 后端核心 POC 中用真实测试 app/repo 验证并记录到 PROJECT_DISCOVERY/TEST_PLAN |
| DOC-104 | 中 | 审计、token inventory、日志的保留期限、清理、导出和删除策略未定义 | 增补 PRD/ARCHITECTURE；批准前作为需求问题确认 |
| DOC-105 | 中 | permission profile 只有示例，没有 canonical catalog、高风险权限确认矩阵和 GitHub permission 映射 | 低保真/后端 policy 设计前补 PRD 附录或专门文档 |
| DOC-106 | 中 | 安装、启动、停止、卸载、升级、故障恢复 runbook 缺失 | 实现达到可运行阶段前新增 `docs/OPERATIONS.md` |
| DOC-107 | 中 | master key rotation、丢失恢复、备份恢复演练只有原则，没有操作流程 | 后端实现/运维文档阶段补架构与 OPERATIONS |
| DOC-108 | 中 | WebUI 可访问性、键盘操作、密度、语言和错误文案 baseline 未定义 | 低保真阶段补 `docs/WIREFRAMES.md` 或设计约束 |
| DOC-109 | 中 | 首个 CI workflow 已配置并真实运行；依赖扫描、构建复现、发布签名/校验和供应链实现仍未配置 | 发布前按 `docs/CI_CD.md` 分层落实；不得把首个 CI 当作完整供应链门禁 |
| DOC-110 | 低 | GitHub Enterprise host 支持优先级未确认 | 保留在 PROJECT_STATUS 未决事项 |
| DOC-111 | 低 | raw token 兼容模式的默认态和审计级别未最终确认 | 作为专门决策项，不应在实现中偷偷加入 |
| DOC-112 | 低 | 漏洞报告渠道未配置 | 首次发布前更新 SECURITY.md；不要虚构联系渠道 |
| DOC-113 | 中 | 版本控制基础已建立，但 release notes/changelog、artifact packaging、签名/SBOM 与自动发布流程仍未设计或批准 | 首次 release preparation 前补专门流程；不得把 VERSION/tag checker 当作发布自动化 |
| DOC-114 | 低 | merged branch cleanup 已写入 BRANCHING，但 GitHub auto-delete merged branches 尚未配置 | 后续可由用户明确授权启用仓库级 auto-delete；当前按人工确认后的及时删除执行 |
| DOC-115 | 中 | commit message 曾只有英文短句和表层 Conventional Commits 格式，缺少原因/边界/验证信息 | **本轮关闭**：新增 COMMIT_MESSAGES 与结构性 checker；语义质量仍需 review，不能由脚本完全证明 |

## 4. 文档一致性维护规则

- 当前状态只写 `docs/PROJECT_STATUS.md`；其他文档需要引用状态时链接到该文件。
- 决策理由和状态只写 `docs/DECISIONS.md`；其他文档可以引用决策，不复制大段备选分析。
- 已批准基线的实质变化必须有 `docs/changes/CR-<id>.md`。
- 文档新增/删除/改归属后，更新本审计、AGENTS 文档地图和 `docs/authority-registry.json`。
- 不得为了“看起来完整”把未实现命令、未运行测试或未获得批准写成事实。
