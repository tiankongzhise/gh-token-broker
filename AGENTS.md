# 项目操作规则

> ⚠️ **AI 署名约定**（AI Signature Policy）：每次单独询问；未获当次明确同意，不得在提交中加入 AI 署名。
> 详细记录、检查流程和变更日志见 [GIT_GOVERNANCE](docs/GIT_GOVERNANCE.md)。
>
> ⚠️ **贡献者身份约定**（Author Identity Policy）：每次单独询问；本地提交允许身份为 `notebook <tiankongzhise@163.com>`；GitHub PR merge commits 允许身份为 `tiankongzhise <104021016+tiankongzhise@users.noreply.github.com>`。
> 详细记录、检查流程和变更日志见 [GIT_GOVERNANCE](docs/GIT_GOVERNANCE.md)。

本文件只保存框架性约束、长期不变的安全/Git 规则和文档地图。会随进度变化的状态、批准、worktree、验证结果和未决事项不写在本文，必须读写 [PROJECT_STATUS](docs/PROJECT_STATUS.md)。

## 1. 每次任务开始时的最低阅读

1. 先读 [PROJECT_STATUS](docs/PROJECT_STATUS.md)：当前阶段、批准证据、允许修改范围、worktree 分工、验证状态和未决事项。
2. 再按任务类型读文档地图中的专门文档；不要只读本文件就推断产品细节。
3. 只有明确记录在 PROJECT_STATUS 或 DECISIONS 中的用户批准才可作为批准证据。文件存在、自评通过、用户沉默、超时或“看起来合理”都不是批准。
4. 新任务默认续接当前状态；只读审查和局部维护不重启项目发现。影响已批准基线时先走变更控制。

## 2. 文档地图：什么内容去哪里读，改了写到哪里

| 目的/任务 | 先读 | 修改后记录到哪里 |
|---|---|---|
| 当前阶段、审核门、批准证据、允许目录、活跃 worktree、验证状态、未决事项 | [PROJECT_STATUS](docs/PROJECT_STATUS.md) | 立即更新 [PROJECT_STATUS](docs/PROJECT_STATUS.md) |
| 事实归属、单一权威来源、stale 状态检查 | [INFORMATION_AUTHORITY](docs/INFORMATION_AUTHORITY.md) + [authority-registry.json](docs/authority-registry.json) | 新事实类型/文档归属变化更新 registry；原则变化更新 INFORMATION_AUTHORITY |
| 分支集成顺序、文件 ownership、跨分支冲突控制 | [BRANCHING](docs/BRANCHING.md) + [branch-ownership.json](docs/branch-ownership.json) | ownership/例外/分支状态变化更新 registry；原则变化更新 BRANCHING |
| 产品目标、用户、范围、功能/非功能需求、验收标准 | [PRD](docs/PRD.md) | 未批准前修订 PRD；批准后实质变化先建 `docs/changes/CR-<id>.md` |
| 发现证据、技术判断、参考项目分析、风险来源 | [PROJECT_DISCOVERY](docs/PROJECT_DISCOVERY.md) | 新证据写入该文件；已经形成选择的事项同步到 [DECISIONS](docs/DECISIONS.md) |
| 架构边界、模块、数据模型、核心流程、部署、恢复 | [ARCHITECTURE](docs/ARCHITECTURE.md) | 未批准前修订架构；批准后实质变化先建 CR |
| 许可证、secret store、并行 worktree 等重要选择的备选方案、理由和状态 | [DECISIONS](docs/DECISIONS.md) | 新增或更新对应 decision entry；禁止只改实现不改决策记录 |
| 开发环境、目录约定、实现顺序、代码风格、Git 细则、真实命令 | [DEVELOPMENT](docs/DEVELOPMENT.md) | 工具链/命令/约定变化更新该文件，并把当前验证快照同步到 PROJECT_STATUS |
| CI/CD 门禁、引入时机、发布/供应链边界 | [CI_CD](docs/CI_CD.md) | CI/CD 原则、分层门禁和实际配置状态写该文件；当前验证快照仍写 PROJECT_STATUS |
| 版本号、release tag、版本注入和发布控制边界 | [VERSIONING](docs/VERSIONING.md) + 根 `VERSION` | 原则写 VERSIONING；当前开发目标版本只写根 `VERSION`；实际验证快照写 PROJECT_STATUS |
| `.gitignore` 何时修改、规则分类、审查清单 | [GITIGNORE_POLICY](docs/GITIGNORE_POLICY.md) + 根 `.gitignore` | 原则写 policy；实际规则写根 `.gitignore`；工具链/目录变化同步 DEVELOPMENT |
| 测试分层、测试设计、Windows/安全/冒烟测试 | [TEST_PLAN](docs/TEST_PLAN.md) | 测试策略变化更新该文件；实际运行结果写 PROJECT_STATUS 或后续验证记录 |
| 威胁模型、资产、信任边界、攻击者、缓解与非目标 | [THREAT_MODEL](docs/THREAT_MODEL.md) | 新威胁/缓解/残余风险写该文件；影响批准架构时另建 CR |
| 漏洞报告、秘密边界、泄露响应、push 前扫描要求 | [SECURITY](SECURITY.md) | 安全政策和泄露响应流程变化写该文件；扫描结果快照写 PROJECT_STATUS |
| 文档覆盖度、缺失项、文档结构审计 | [DOCUMENTATION_AUDIT](docs/DOCUMENTATION_AUDIT.md) | 文档结构性变化后更新审计状态或新增 findings |
| AI 署名、贡献者身份、push 前身份检查 | [GIT_GOVERNANCE](docs/GIT_GOVERNANCE.md) | 政策、允许身份、检查记录和变更证据写该文件 |
| 已批准基线的实质变化 | 相关基线文档 + `docs/changes/` | 先创建 `docs/changes/CR-<id>.md`，记录 proposed/approved/rejected 和批准证据 |

文档之间冲突时，以较新的明确用户批准为准；没有发现批准证据时标为待确认，不得自行选择后冒充已批准。

## 3. 阶段与人工审核框架

| 阶段 | 产物与验证 | 人工重点 |
|---|---|---|
| 发现/需求/架构 | 首批文档、secret scan baseline | 确认范围、保密边界、技术方向、阶段配置 |
| A 低保真 | `design/wireframes/` 与 `docs/WIREFRAMES.md` | WebUI 页面、流程、状态是否完整 |
| B 高保真 | `design/high-fidelity/` 与 `docs/DESIGN_SPEC.md` | 视觉层级、信息密度、桌面使用体验 |
| C 示意 Demo | `prototype/` 可运行可点击、模拟数据与状态切换 | 确认最终产品形态和 WebUI 基线 |
| 后端/联调 | 按批准契约实现 daemon/MCP/storage/helper | 不破坏已批准基线；高风险变化走 CR |
| 测试/审查/发布检查 | 真实运行检查、Windows 冒烟、安全测试、secret scan | 验收结果和高风险项 |

核心 token chain POC 与 WebUI 低保真可以在用户明确授权的范围内并行。并行分工、分支和允许修改目录以 [PROJECT_STATUS](docs/PROJECT_STATUS.md) 为准；不得把一个 worktree 的授权扩大解释为全产品批准。

## 4. 机密信息硬约束

以下要求优先于便利性，任何 agent/贡献者必须遵守：

1. 不得把机密信息提交或上传，包括但不限于 GitHub access token、refresh token、client secret、private key、master key、agent credential、bearer token、密码、私钥和会话材料。
2. 不得把真实秘密写入文档、示例、测试 fixtures、日志、MCP tool result、WebUI、issue、PR、commit message 或临时脚本输出。
3. 每次 push 前必须在仓库根目录运行 `python scripts/check_secrets.py` 并确认通过；扫描失败不得 push。
4. 不得通过删除、弱化或绕过扫描规则来让 push 通过。误报必须用最小范围 allowlist 或改写示例处理；真实命中必须撤销/轮换相关秘密。
5. 如果秘密曾经进入 Git 历史，即使后续删除文件，也必须按泄露处理：先撤销/轮换，再评估历史清理和通知范围。
6. **流程设计不是保密性的一部分。** 架构、认证流程、威胁模型、策略结构和错误语义可以公开；项目安全不得依赖 security through obscurity。需要保密的只有密钥材料及其可用派生值。
7. 扫描脚本输出不得打印完整匹配秘密，只能输出文件、行号和类型。

详细泄露响应和安全政策见 [SECURITY](SECURITY.md)。

## 5. Git 与并行工作约束

- 默认分支：`main`；协作流程为 GitHub Flow；短期分支使用 `feat/<short-kebab>`、`fix/<short-kebab>`、`chore/<short-kebab>`。
- 禁止直接向远端 `main` push；所有对 `main` 的修改必须通过分支和 Pull Request 合并。确需变更保护规则时必须另行获得用户明确授权。
- 提交格式：Conventional Commits 1.0.0，默认英文。
- 先检查工作区，保留用户和其他代理已有改动；不擅自清理、强推、改写历史或执行其他不可逆操作。
- 提交仅含本任务文件；提交前检查 diff 和 staged diff。
- 规则配置不自动授予 commit/push/merge/deploy 权限；按当前用户明确授权执行。
- 推送前必须完成 secret scan，并检查 AI 署名约定与贡献者身份约定。
- `.gitignore` 的具体规则不写死在本文；修改时机和审查原则见 [GITIGNORE_POLICY](docs/GITIGNORE_POLICY.md)，实际规则以根 `.gitignore` 为准。
- 多 worktree 并行时不得跨 worktree 修改对方负责的文件来“顺手修复”；必要共享文档变更先回到主 worktree 或按 PROJECT_STATUS 的归属执行。
- 已合并分支不得长期堆积；merged branch 清理时机、确认边界和 feature 分支暂存规则见 [BRANCHING](docs/BRANCHING.md)。

## 6. 编码与验证约束

- 不得虚构命令、测试结果、批准状态或已实现能力。
- 变更聚焦当前任务，不夹带全库格式化、依赖升级或无关重构。
- 新 Go 代码默认 `gofmt`；lint/test/build 命令以 [DEVELOPMENT](docs/DEVELOPMENT.md) 和 PROJECT_STATUS 中已配置内容为准。
- CI/CD 门禁和引入时机不写死在本文；以 [CI_CD](docs/CI_CD.md) 为准。未在 PROJECT_STATUS 或 CI_CD 标为已配置的流水线不得当作事实。
- 错误处理、日志、配置和依赖规则见 [DEVELOPMENT](docs/DEVELOPMENT.md)；安全边界见 [THREAT_MODEL](docs/THREAT_MODEL.md)。

## 7. 角色与委派框架

委派前必须核对当前运行时实际可调用的角色/子代理类型；磁盘文件、角色库说明或历史会话不能证明当前可调用。记录请求角色与实际调用角色。必需角色缺失时，按 PROJECT_STATUS 中的授权降级路径处理；不得静默把专门角色工作接管为已实现事实。

## 8. 变更控制框架

已批准页面、核心流程、数据/权限/API、数据库、部署方式、secret store 方案、raw token 返回策略和产品基线的实质变化，需先建立 `docs/changes/CR-<id>.md`。记录原因、原/新行为、影响、迁移回滚、需重审阶段、proposed/approved/rejected 和批准证据。明确授权的用户变更可作为批准；只创建 CR 不等于批准。

## 9. Definition of Done 与审核包

每次完成输出一页以内 Review Packet：

1. 完成内容和产物入口。
2. 已验证结果和置信度；未运行的检查明确说明。
3. 至多三项必须人工决定的问题。
4. 风险、未完成事项。
5. 当前停在哪个审核门，以及通过后允许做什么。

审核门处暂停，不能自行进入下一阶段。
