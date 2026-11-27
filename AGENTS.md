# 项目操作规则

> ⚠️ **AI 署名约定**（AI Signature Policy）：初始默认采取保守策略；首次提交不包含 AI 署名。
> 记录于 2026-11-27，触发场景：首次 push 前预防性记录，检出 0 条署名。
> 约定：每次单独询问。
> 修改约定请直接编辑本行。

> ⚠️ **贡献者身份约定**（Author Identity Policy）：初始默认采取保守策略；首次提交使用用户指定身份。
> 记录于 2026-11-27，触发场景：首次 push 前预防性记录，检出 0 个名单外作者。
> 约定：每次单独询问。
> 允许身份：notebook <tiankongzhise@163.com>
> 修改约定请直接编辑本行。

## 项目事实与文档入口

- 目标：构建 Windows 本地 GitHub Token Broker，为本地 AI agents、CLI 和 Git 操作按需签发短期、最小权限、可审计的 GitHub 访问凭据。
- 用户：在 Windows 本地使用多个 coding agents 管理多个 GitHub 仓库的开发者。
- 非目标：公网 SaaS、多租户服务、PAT 自动续签、防御同用户完全恶意进程、随程序分发任何秘密。
- 类型：本地 daemon + MCP 控制面 + CLI/exec/git credential helper + localhost WebUI。
- 语言/框架：建议 Go；尚未初始化实现。WebUI 技术栈待设计阶段确认。
- 持久化：SQLite 元数据/审计；秘密材料使用 Windows Credential Manager 或加密 SQLite，最终方案待实现前确认。
- 部署：Windows 本地单用户，不公网暴露。
- 前端复杂度：低到中；以管理、状态、审计和表单为主。
- 关键目录：`docs/` 文档，`scripts/` 仓库维护脚本；实现目录尚未创建。
- 每次开始先读：本文件当前阶段表、[PRD](docs/PRD.md)、[ARCHITECTURE](docs/ARCHITECTURE.md)、[DEVELOPMENT](docs/DEVELOPMENT.md)。
- 详细发现证据与待确认项：[PROJECT_DISCOVERY](docs/PROJECT_DISCOVERY.md)。

## 当前阶段与审核记录

| 字段 | 当前值 |
|---|---|
| 当前阶段/状态 | 发现/需求/架构：待审核 |
| 本阶段允许修改 | `README.md`、`AGENTS.md`、`docs/`、`scripts/check_secrets.py`、`.gitignore`；不得开始产品实现 |
| 审核产物与版本 | 初始文档集；尚未获得人工批准 |
| 最近明确批准 | 未批准 |
| 未决问题/风险 | 许可证、secret store 最终方案、scoped token 父/子失效语义实测、WebUI 技术栈、raw token 兼容模式 |
| 下一阶段及进入条件 | 用户批准需求/架构后，进入 WebUI 低保真 wireframes；若先批准核心 POC，则可初始化 Go module 并仅实现 Phase 1 |

新任务根据该表和相关文档续接。只读审查和局部维护不重启项目发现；影响批准基线才走变更流程。不得将文件存在、自评通过或用户沉默当作批准。批准后更新表格；产物实质变更需要确认原批准是否适用。

## 本项目阶段与交付

| 阶段 | 产物与验证 | 人工重点 |
|---|---|---|
| 发现/需求/架构 | 本批文档、secret scan baseline | 确认范围、保密边界、技术方向、阶段配置 |
| A 低保真 | `design/wireframes/` 与 `docs/WIREFRAMES.md` | WebUI 页面、流程、状态是否完整 |
| B 高保真 | `design/high-fidelity/` 与 `docs/DESIGN_SPEC.md` | 视觉层级、信息密度、桌面使用体验 |
| C 示意 Demo | `prototype/` 可运行可点击、模拟数据与状态切换 | 确认最终产品形态和 WebUI 基线 |
| 后端/联调 | 按批准契约实现 daemon/MCP/storage/helper | 不破坏已批准基线；高风险变化走 CR |
| 测试/审查/发布检查 | 真实运行检查、Windows 冒烟、安全测试、secret scan | 验收结果和高风险项 |

核心 token chain POC 可在 WebUI 低保真之前作为技术验证进行，但必须在用户明确批准该范围后才开始；不得把 POC 当作已批准产品基线。

## 角色与委派

本会话当前可调用的通用子代理类型只有 `subagent_explore` 与 `subagent_general`；没有发现可直接调用的 agency-agents 命名角色。初始化文档阶段未进行子代理委派。后续如需委派，必须先核对当前运行时可调用角色，不得把磁盘文件或角色库说明当成可调用事实。

| 阶段职责 | 请求角色完整名 | 当前运行时实际可用名 | 缺失处理/授权依据 |
|---|---|---|---|
| 需求/产品 | Product Manager | 当前会话未可用 | 暂未委派；如未来需要，先核对运行时角色 |
| 架构 | Software Architect | 当前会话未可用 | 暂未委派；如未来需要，先核对运行时角色 |
| 实现 | 匹配 Go/Windows 的实现角色 | 当前会话未可用 | 用户明确授权前不开始实现 |
| 审查 | Code Reviewer / Reality Checker | 当前会话未可用 | 到验证阶段再核对 |

## 编码与验证

- 当前没有产品代码、格式化/lint/typecheck/test 配置；不得虚构命令或验证结果。
- 新 Go 代码默认 `gofmt`；lint/test/build 命令在 Go module 初始化后补入本文件。
- 变更聚焦当前任务，不夹带全库格式化、依赖升级或无关重构。
- 错误处理、日志、配置和依赖规则见 [DEVELOPMENT](docs/DEVELOPMENT.md)。

| 用途 | 工作目录与命令 | 命令来源 | 当前验证状态 |
|---|---|---|---|
| 秘密扫描 | 仓库根：`python scripts/check_secrets.py` | 本项目脚本 | 已配置；每次 push 前必须运行 |
| 启动 | 未配置 | 无产品实现 | 不适用 |
| 格式/lint/类型检查 | 未配置 | 无产品实现 | 未运行 |
| 测试/构建 | 未配置 | 无产品实现 | 未运行 |

## 机密信息硬约束

以下要求优先于便利性，任何 agent/贡献者必须遵守：

1. 不得把机密信息提交或上传，包括但不限于 GitHub access token、refresh token、client secret、private key、master key、agent credential、bearer token、密码、私钥和会话材料。
2. 不得把真实秘密写入文档、示例、测试 fixtures、日志、MCP tool result、WebUI、issue、PR、commit message 或临时脚本输出。
3. 每次 push 前必须运行 `python scripts/check_secrets.py` 并确认通过；扫描失败不得 push。
4. 不得通过删除、弱化或绕过扫描规则来让 push 通过。误报必须用最小范围 allowlist 或改写示例处理；真实命中必须撤销/轮换相关秘密。
5. 如果秘密曾经进入 Git 历史，即使后续删除文件，也必须按泄露处理：先撤销/轮换，再评估历史清理和通知范围。
6. **流程设计不是保密性的一部分。** 架构、认证流程、威胁模型、策略结构和错误语义可以公开；项目安全不得依赖 security through obscurity。需要保密的只有密钥材料及其可用派生值。
7. 扫描脚本输出不得打印完整匹配秘密，只能输出文件、行号和类型。

## Git 与交付约定

- 默认分支：`main`。
- 协作流程：GitHub Flow；短期 `feat/<short-kebab>`、`fix/<short-kebab>`、`chore/<short-kebab>`。
- 提交格式：Conventional Commits 1.0.0，默认英文。
- 初始提交作者：`notebook <tiankongzhise@163.com>`。
- 先检查工作区，保留用户和其他代理已有改动；不擅自清理、强推或改写历史。
- 提交仅含本任务文件，提交前检查 diff 和 staged diff。
- 规则配置不自动授予 commit/push/merge/deploy 权限，按当前用户授权执行。
- 推送前除 secret scan 外，还应检查提交作者身份和是否存在 AI 署名约定。

## 变更控制

已批准页面、核心流程、数据/权限/API、数据库、部署方式、secret store 方案、raw token 返回策略和产品基线的实质变化，需先建立 `docs/changes/CR-<id>.md`。记录原因、原/新行为、影响、迁移回滚、需重审阶段、proposed/approved/rejected 和批准证据。明确授权的用户变更可作为批准；只创建 CR 不等于批准。

## Definition of Done 与审核包

当前文档阶段完成条件：

- README、PRD、ARCHITECTURE、PROJECT_DISCOVERY、DEVELOPMENT、TEST_PLAN、AGENTS 完整且相互一致。
- 明确记录 secret 边界、push 前扫描和“流程公开不是秘密”的约束。
- 不声明未实现的命令或能力。
- `python scripts/check_secrets.py` 运行通过。
- 初始 commit 与 push 仅在用户明确授权后执行。

每次完成输出一页以内 Review Packet：完成和产物入口、验证/置信度、至多三项待决定、风险/未完成、当前审核门和下一步。审核门处暂停，不能自行进入下一阶段。
