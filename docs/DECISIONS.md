# DECISIONS — GH Token Broker

本文记录重要技术/产品/治理决策。每个条目必须包含状态、证据、理由和后果。状态使用：`proposed`、`approved`、`rejected`、`superseded`。用户明确授权可作为 approved 证据；仅创建条目不等于批准。

## D-0001 License: LGPL 2.1

- 日期：2026-11-27
- 状态：`approved`
- 证据：用户明确说明“本项目使用 LGPL 2.1 许可”，并在 2026-11-27 进一步确认选择 `LGPL-2.1-only`。
- 当前记录：仓库按 SPDX `LGPL-2.1-only` 处理，并在根目录保存完整许可证文本 `LICENSE`。

`LGPL-2.1-only` 与 `LGPL-2.1-or-later` 的核心区别：

- `LGPL-2.1-only`：下游只能按 LGPL 2.1 本版本的条款使用/修改/再分发。优点是条款确定、保守、可预期；缺点是不会自动获得未来 LGPL 版本可能带来的澄清、兼容性或法律文本改进。
- `LGPL-2.1-or-later`：下游可以选择 LGPL 2.1 或自由软件基金会之后发布的更新版本。优点是更能随许可证体系演进；缺点是版权方预先授权了当时尚未存在、尚未审阅的未来条款。
- 实务上，LGPL 2.1 与 LGPL 3 系列在专利授权、用户产品安装信息/反锁定等方面存在文本差异；是否接受这些未来/后续条款应作为明确选择，不应默认推断。

理由：

- 用户明确选择 LGPL 2.1，并提及其允许动态链接/动态库使用的意图。
- 用户进一步明确选择 `LGPL-2.1-only`，因此本项目不额外授予未来 LGPL 版本；这比 `or-later` 更保守、条款更确定。

后果：

- README 不再声明“许可证未定”。
- 后续新增源文件是否需要许可证头，应在 Go module 初始化时确定并写入 DEVELOPMENT。
- 如果未来要改成 `LGPL-2.1-or-later`，属于扩大授权，必须形成新的明确决策，并同步修改 README、本文和可能的源码头声明。
- 注意：LGPL 2.1 的动态链接/重新链接机制主要面向“库”。本项目当前主要产物是 daemon/CLI 应用；许可证仍然可用，但“动态库外挂”并不是对主可执行产物最精确的适配场景。若未来明确区分 core library 与 CLI/daemon，应在架构和许可证说明中分别表述。

## D-0002 Secret Store MVP

- 日期：2026-11-27
- 状态：`approved`
- 批准证据：2026-11-27 用户明确回复“批准 d-0002”。
- 决策：**MVP 采用“秘密材料字段级加密后存 SQLite，master key 存 Windows Credential Manager”**。
- 备选：秘密材料直接逐条存 Windows Credential Manager。

### 已批准方案

- SQLite 保存元数据、审计、token inventory 以及加密后的 secret payload。
- Windows Credential Manager 只保存 broker 的随机 master key。
- 使用 AEAD（例如 AES-256-GCM），每条记录唯一随机 nonce，并携带 key version。
- 使用 record type、account id、secret ref 等上下文作为 associated data，防止密文错位。
- master key 的 Credential Manager target name 不是秘密；master key 值是秘密。

### 为什么采用加密 SQLite，而不是直接逐条 Credential Manager

1. **refresh chain 需要事务一致性。** refresh token 滚动更新必须与 expiry、状态机和 inventory 元数据保持一致。加密 SQLite 可以把密文和元数据放进同一事务；直接 Credential Manager + SQLite 是两个存储，无法真正原子提交。
2. **child token inventory 和主动撤销更适合结构化存储。** 如果为了主动 revoke 而保留 child token，加密 SQLite 能把密文、scope、expiry、revoke 状态放在同一记录/事务中；逐条 Credential Manager 会产生孤儿项、清理和一致性问题。
3. **安全边界并没有因为直接 Credential Manager 显著更强。** 两种方案的根信任都落在当前 Windows 用户的 Credential Manager/DPAPI；它们都不能防御同用户完全恶意进程，这与 v1 威胁模型一致。
4. **符合用户最初明确目标。** 初始化发现中用户已表达希望 access/refresh token 加密保存在 SQLite，密钥放 Windows Credential Manager。
5. **备份语义更清楚。** SQLite 可以备份密文和审计；master key 不可用时明确进入 reauth/无法主动 revoke 路径。直接 Credential Manager 的秘密通常也不适合备份，且分散在 OS 凭据库中。

### 代价与必须满足的约束

- 需要正确实现 AEAD、nonce 唯一性、key version、associated data 和密钥轮换；不得自研加密算法。
- master key 泄露等价于该机器上 SQLite 内所有加密秘密泄露；但 v1 本就不承诺防御同用户完全恶意进程。
- 需要明确 master key 丢失、SQLite 损坏、备份恢复和轮换行为。
- 单元测试必须覆盖 round-trip、错误 key、篡改 ciphertext/nonce/associated data、key version 兼容和日志脱敏。

### 直接 Credential Manager 的处置

直接逐条 Credential Manager 不再作为 MVP 主方案。若未来因实现风险要临时或永久重新启用它，必须重新评估 refresh chain 事务一致性、child token inventory、主动撤销和孤儿 credential 清理，并按项目变更控制处理；不得在后端实现中静默替换已批准方案。

## D-0003 并行 worktree 工作流

- 日期：2026-11-27
- 状态：`approved`
- 证据：用户明确指示开两个 worktree：一个用于前端低保真确认，一个用于后端核心。
- 决策：采用并行 worktree，而不是串行等待 WebUI 审核结束后再做后端核心。

后果：

- `feat/webui-wireframes` 负责低保真页面/流程确认。
- `feat/backend-core` 负责后端核心 POC。
- 两边不得互相修改对方负责的产物；共享规则/状态变更在主 worktree 或明确的文档治理分支处理。
- 并行授权不等于完整产品基线批准；后端 POC 范围仍以 PROJECT_STATUS 为准。

## D-0004 默认 agent 接入 UX：审批模式优先，人工模式高级保留

- 日期：2026-11-27
- 状态：`approved`
- 批准证据：用户明确说明原低保真“前端太过繁琐……需要我设置的东西过多”，并提出希望：登录 GH Token Broker 后生成授权码，把授权码交给 agent；agent 读取公开节点了解协议，用授权码提交项目所需 GitHub 权限申请；用户只审批，并可全部或部分批准。用户同时说明原低保真“可以保留做人工模式”，但更希望有“审批模式”。
- 决策：**agent 接入的默认 UX 采用 agent-initiated approval mode；原手工配置 agent credential/repo/profile 的界面保留为高级人工模式，不作为默认路径。**

### 核心含义

- 用户默认只需要：
  1. 登录本地 GH Token Broker。
  2. 生成一次性或短寿命 agent 授权码。
  3. 把授权码交给 agent。
  4. 在 Approval Inbox 审批 agent 提交的权限申请，可全部批准、部分批准/降权或拒绝。
- agent 需要能够读取 broker 的 localhost discovery public node，了解协议版本、endpoint、支持的 profile 和申请格式。这里 “public” 指无需凭证可读的协议元数据，不是公网公开。
- 授权码只代表“允许提交申请/建立接入请求”，不代表已经获得 GitHub 访问能力。
- 批准后系统才创建或更新 agent credential、policy、grant/token 边界。
- 手工 Agents/Token/Grants 管理能力仍保留，用于高级修正、排障、rotate/disable/revoke。

### 理由

- 项目面向 agent 使用；agent 最了解自己的项目上下文和所需权限，比用户手工猜测 repo pattern/profile 更准确。
- 用户主要职责应是风险判断和审批，而不是理解并维护复杂策略语法。
- 部分批准能在“全拒绝”和“全批准”之间提供实际可用的最小权限路径。

### 后果与待细化边界

- 低保真必须增加审批模式页面/流程；原 wireframes 不应删除，而应重新标注为高级人工模式。
- 后端契约需要增加 discovery document、authorization code bootstrap、permission application、approval result 等概念。
- 授权码建议一次性、短寿命、可撤销；具体 TTL 和是否允许重复使用仍需实现前确认。
- 部分批准粒度建议第一版按仓库 + permission profile；是否细化到单个 GitHub permission 仍待确认。
- agent 自报 project/name/version/reason 不能作为安全证明，UI 必须标为未验证声明。
- 该决策不批准具体前端技术栈，也不代表高保真或 Demo 阶段已经开始。

## D-0005 Phase 1 backend token chain POC 作为 Phase 2 技术地基

- 日期：2026-11-27
- 状态：`approved`
- 批准证据：2026-11-27 用户明确回复“后端通过，token chain 当作 Phase 2 的技术地基”。
- 决策：接受 `feat/backend-core` 中 Phase 1 core token chain POC 的核心语义作为 Phase 2 技术地基。

### 接受的语义范围

- device flow 显式授权。
- refresh token 加密存 SQLite，master key 存 Windows Credential Manager。
- refresh token 轮换与状态/过期时间同事务持久化。
- refresh 互斥，避免同一账户并发刷新导致链损坏。
- parent token 仅内存缓存，不明文落盘。
- 普通 token 请求不得自动启动 device flow；refresh 失效进入显式 reauth。

### 不构成批准的内容

- 不表示 Phase 2 已经开始；进入 Phase 2 仍需用户明确任务指示。
- 不表示 `modernc.org/sqlite`、当前 schema、CLI 命令表面或所有实现细节成为永久架构决策。
- 不批准 MCP、WebUI、scoped token、多 agent policy、raw token 兼容模式。
- 不替代真实 GitHub App device-flow/refresh 冒烟验证。

## D-0006 审批模式交互细化与 UI 模式分离

- 日期：2026-11-27
- 状态：`approved`
- 批准证据：2026-11-27 用户逐项确认：授权码一次性/短寿命；第一版不开放原子性操作、只授权仓库；discovery 严格 `127.0.0.1`；低保真其他没问题，但两套 UI 必须明确分开，顶部设置模式切换，默认 agent-initiated approval mode，切到人工模式后整个页面才切换。
- 决策：审批模式按以下交互边界推进低保真复审。

### 已确认边界

1. **agent 授权码**：默认一次性、短寿命；泄露、过期或使用失败后可撤销并重新生成。
2. **第一版审批粒度**：原始记录为只按仓库批准/拒绝；该解释随后被用户修正，并由 D-0007 取代。
3. **permission profile 的定位**：原始记录为只读展示；该解释随后被用户修正，并由 D-0007 取代。
4. **discovery public node**：严格绑定 `127.0.0.1`，暂不考虑公网或 LAN 访问。
5. **agent 自报信息**：project/name/version/reason 只作为未验证声明显示，不得被 UI 或 policy 当作安全事实。
6. **UI 模式分离**：顶部有明确模式切换，默认 Agent 审批模式。审批模式左侧只显示审批模式内容；切换到人工模式后，整个页面和左侧导航一起切换，不混杂两套信息架构。

### 含义

- 审批模式中的部分批准不是 GitHub 原子权限编辑器。
- 原“不能降权 profile”的解释已被用户修正；正确语义见 D-0007。
- 后续高保真不得把 Agents/Token/Grants 等人工模式入口混入审批模式左侧导航。


## D-0007 审批降权语义修正与低保真批准

- 日期：2026-11-27
- 状态：`approved`
- 批准证据：2026-11-27 用户明确修正：“第一版开放这种降权编辑，我要拒绝的 agent 一次性给多个 github 仓库申请大量权限授权这种情况。而不是拒绝 permission profile 力度调整。”并确认“低保真确认”。
- 决策：第一版审批模式允许 permission profile 降权，但不开放 GitHub 原子权限编辑；低保真 wireframes 在采纳该修正后作为本阶段批准基线。

### 正确语义

1. 用户可以按仓库批准、拒绝或降权 permission profile，例如把 `pr-write` 降为 `read-only` 或 `issue-read`。
2. 第一版仍不开放 `contents:write`、`issues:write` 等 GitHub 原子权限逐项编辑。
3. 对一次性跨多个仓库申请大量权限的 agent 申请，UI 必须突出批量/高风险警告，并让用户逐仓库批准、降权或拒绝。
4. agent 自报 project/name/version/reason 仍是未验证声明；审批真正生效的是仓库与最终权限包。
5. 两套 UI 模式分离、授权码一次性/短寿命、discovery 严格 `127.0.0.1` 的既有决定继续有效。

### 低保真批准边界

- 批准的是当前低保真信息架构和审批交互方向，包括模式分离与部分批准/降权语义。
- 不批准最终视觉设计、前端技术栈、真实后端 API schema 或高保真实现。
- 高保真阶段可以开始，但仍需在开始前获得用户明确工作指令；本决策本身不自动执行下一阶段。


## D-0008 CI/CD 与 .gitignore 治理归属

- 日期：2026-11-27
- 状态：`approved`
- 批准证据：2026-11-27 用户指出项目缺少 CI/CD 相关内容，并要求不要把 CI/CD 和 `.gitignore` 规范写死在 AGENTS 中，而是让 AGENTS 只定原则并把真正规范文件加入文档地图。
- 决策：CI/CD 与 `.gitignore` 采用“原则在 AGENTS、规范在专门文档、执行配置在实际文件”的三层治理方式。

### 内容

1. `docs/CI_CD.md` 记录 CI/CD 原则、分层门禁、引入时机、发布/供应链边界和当前配置事实。
2. `docs/GITIGNORE_POLICY.md` 记录 `.gitignore` 修改时机、规则分类和审查清单；根 `.gitignore` 是实际执行文件。
3. `AGENTS.md` 只保留原则与文档地图入口，不复制具体 workflow 命令、平台细节或 ignore 规则。
4. 截至 D-0008 创建时尚未配置 CI workflow，也没有批准 CD/自动发布；首个 CI 后续由 D-0009 实施。不得把 policy 文档当作 CI 已通过或完整供应链门禁。
5. 引入新工具链、编译产物、测试报告、runtime cache 或日志目录时，必须在同一任务中检查并更新根 `.gitignore`。


## D-0009 main 分支保护与首个 CI 实施

- 日期：2026-11-27
- 状态：`approved`
- 批准证据：2026-11-27 用户明确要求“main禁止直接push，任何对main的修改应该通过分支然后pr合并”，授权操作 GitHub 添加保护，并要求“添加ci，并push真实测试，分支ci通过后，合并到main，main ci通过后，为分支同步最新的main变化”。
- 决策：main 采用分支保护 + PR 合并流程；首个 CI 使用 GitHub Actions 实现仓库卫生检查和条件化 Go 检查。

### 边界

1. 禁止直接向远端 `main` push；所有 main 修改必须通过分支和 PR。
2. CI job/context 为 `ci`；分支保护和 CI 的实际远端状态以 PROJECT_STATUS 记录为准。
3. 首个 CI 只覆盖仓库卫生、Markdown 链接、secret scan、wireframe XML/ignore hygiene，以及存在 `go.mod` 时的 Go 检查。
4. 这不批准 CD、自动发布、签名、SBOM、依赖扫描或完整供应链门禁。
5. 同步 feature 分支时优先使用普通 merge，避免改写历史和 force-push。


## D-0010 文档事实单一权威来源机制

- 日期：2026-11-27
- 状态：`approved`
- 批准证据：2026-11-27 用户指出 WIREFRAMES draft 状态与低保真批准不一致，要求审计同类问题，并明确提出“某个事项在哪里登记，应该只有一个权威文档记录和更改，其他文档只是引用”，同时允许提出更好方案。
- 决策：采用单一权威来源机制；`docs/INFORMATION_AUTHORITY.md` 记录治理原则，`docs/authority-registry.json` 作为机器可读登记表，`scripts/check_doc_authority.py` 作为 CI/本地检查。

### 边界

1. 决策和批准证据只登记在 DECISIONS；当前状态、审核门和验证快照只登记在 PROJECT_STATUS。
2. artifact 文档不独立维护审批状态，只链接权威记录。
3. policy、执行配置和运行结果分别登记，禁止混写。
4. checker 只能防止已登记的 stale/缺失引用问题，不能替代语义审查；发现新类型漂移时必须补登记规则。
5. 本决策批准治理原则和首版 enforcement 机制，不表示 registry 覆盖已经完整。


## D-0011 GitHub PR merge commit 作者身份

- 日期：2026-11-27
- 状态：`approved`
- 批准证据：2026-11-27 push 前身份检查发现 GitHub 合并 PR 自动创建的 merge commit 使用 GitHub noreply 作者身份；用户明确选择“加入允许名单”。
- 决策：允许 `tiankongzhise <104021016+tiankongzhise@users.noreply.github.com>` 仅作为 GitHub PR merge commit 作者身份；本地普通提交仍使用 `notebook <tiankongzhise@163.com>`。

### 边界

1. 该 noreply 身份不得作为本地普通提交身份。
2. 这不改变 AI 署名每次单独询问的政策。
3. 若未来更换 GitHub 账号、合并方式或允许其他贡献者，必须先更新 GIT_GOVERNANCE。


## D-0012 CI 触发策略去重

- 日期：2026-11-27
- 状态：`approved`
- 批准证据：2026-11-27 用户发现同一 commit 的 push CI 与 PR CI 重复，询问是否必须；在解释 PR CI 仍是合并前门禁后，明确选择“推荐方案 1”并要求继续修。
- 决策：GitHub Actions `push` 触发只保留 `main` 和 `feat/**`；`pull_request` 对所有 PR 运行；`workflow_dispatch` 保留。

### 边界

1. `fix/**` 与 `chore/**` 短生命周期分支不单独跑 push CI，避免与 PR CI 重复；它们仍必须通过 PR CI 才能合入 main。
2. 长期 `feat/**` 分支保留 push CI，用于未开 PR 前的早期反馈。
3. 该调整不降低 main 分支保护、required status check 或 strict up-to-date 要求。
4. 若未来分支模型、PR 流程或 CI 成本约束变化，应重新评估该策略。
5. 后续 D-0015 为版本一致性检查新增 `v*` tag push CI；这不改变 chore/fix 去重原则。


## D-0013 分支集成与文件 ownership 机制

- 日期：2026-11-27
- 状态：`approved`
- 批准证据：2026-11-27 用户指出两个 feature 分支已领先 main，要求建立机制协调 feature 分支同步、防止 main 成为影子分支和分支间冲突；随后明确选择“两个都集成”和“实用严格模式”。
- 决策：`main` 是唯一集成交汇点；长期 feature 分支必须登记文件 ownership；集成按队列进行；越权 diff 由本地/CI 检查拦截。

### 边界

1. 长期 feature 分支只独立修改 `docs/branch-ownership.json` 登记的路径。
2. 短生命周期 `chore/**`/`fix/**` 不永久登记 lease，但不得修改 active feature ownership 路径。
3. 已验收成果默认及时集成进 main；暂不合入必须有明确原因和解除条件。
4. 该机制不能阻止本地编辑，只能通过检查阻止越权修改进入 main。
5. 集成当前两个已验收分支不代表启动高保真或 Phase 2。


## D-0014 merged branch 清理与暂存规则

- 日期：2026-11-27
- 状态：`approved`
- 批准证据：2026-11-27 用户指出“对于已经合并的分支需要及时清理，不要堆积在本地和远端仓库中，这个需要沉淀到项目约束中去”；在逐项确认删除清单时选择“只删短分支”，即删除已合并 chore/fix 分支，暂存两个已合并 feature 分支。
- 决策：merged branch lifecycle 写入 `docs/BRANCHING.md`；短生命周期分支合并后必须及时清理，长期 feature 分支默认清理，只有用户明确保留时才可暂存且必须失去 active 写入权。

### 边界

1. 删除前必须确认分支 tip 已合并进 `origin/main` 或无独有提交；不得删除仍有未合并工作的分支。
2. 远端分支删除属于不可逆分支操作，必须获得用户明确确认。
3. 已合并短分支不得复用；新工作使用新分支。
4. 当前 `feat/webui-wireframes` 与 `feat/backend-core` 因用户选择暂存，但状态改为 `integrated`，不再拥有写入权。
5. GitHub 仓库级 auto-delete merged branches 尚未配置；如要启用需另行明确授权。


## D-0015 版本管理与 release tag 控制

- 日期：2026-11-27
- 状态：`approved`
- 批准证据：2026-11-27 用户指出“当前缺少版本管理和控制。如果后期发版的时候，这会不利于自动发布”；随后明确选择推荐方案“VERSION 文件 + SemVer tag + CI 校验 + Go ldflags 注入”。
- 决策：采用 Semantic Versioning 2.0.0；根目录 `VERSION` 记录当前开发目标版本，初始为 `0.1.0-dev`；正式发布使用 `vX.Y.Z` tag；CI 校验版本格式和 tag consistency；Go 二进制通过 ldflags 注入版本并提供 `--version`。

### 边界

1. `VERSION` 表示当前开发目标版本，不代表已经发布。
2. tag 是正式发布事件；release tag 去掉 `v` 前缀后必须与 `VERSION` 一致。
3. 普通 feature/fix/chore PR 不随意修改 `VERSION`。
4. 为支持 tag consistency 检查，CI push trigger 增加 `v*` tags；这不构成自动发布或 CD 批准。
5. release notes/changelog、artifact packaging、签名、SBOM、checksum 和自动发布流程仍未批准、未实现。


## D-0016 高保真与后端 Phase 2 开始授权

- 日期：2026-11-27
- 状态：`approved`
- 批准证据：2026-11-27 用户明确要求“同步了更新完的已合并分支的处理后，开始高保真和后端阶段2”。
- 决策：在 merged-branch/versioning 治理基线同步后，开始 WebUI B 高保真阶段和后端 Phase 2 安全交付通道阶段。

### 范围边界

1. 高保真阶段产物限定为 `design/high-fidelity/` 与 `docs/DESIGN_SPEC.md`；可以使用 implementation-neutral 静态 HTML/CSS 作为设计 artifact，不表示批准正式前端技术栈。
2. 后端 Phase 2 按 DEVELOPMENT 当前定义推进：`exec` wrapper、git credential helper、`min_ttl` 检查、基础审计、Windows 手动/集成验证。
3. 该授权不批准 Demo 阶段、正式 WebUI 技术栈、MCP、scoped token/policy engine 完整实现、raw token 兼容模式或自动发布。
4. 若实现中发现 Phase 2 与 scoped token/grant 依赖顺序冲突，必须先记录架构边界或 CR，不得 silently 扩大范围。


## D-0017 Phase 2 提前 scoped token 与 grant 基础

- 日期：2026-11-27
- 状态：`approved`
- 批准证据：2026-11-27 用户在 Phase 2 顺序冲突选择中明确选择“提前 scoped/grant”。
- 决策：批准 CR-0001；将 scoped child token、inventory、`min_ttl` 和最小 grant lifecycle 作为 Phase 2 前置基础，exec wrapper 与 git credential helper 不得使用 parent token。

### 边界

1. 这不批准完整 policy engine、approval backend、MCP、WebUI 或 raw token 兼容模式。
2. client secret 的存储必须沿用已批准加密 SQLite + WCM master key 方向。
3. scoped token 不可用时 exec/helper 必须失败关闭，不得回退 parent token。
4. 真实 GitHub scoped token 父/子失效语义仍未实测，不得提前宣称验证完成。


## D-0018 commit message 中文规范与结构检查

- 日期：2026-11-27
- 状态：`approved`
- 批准证据：2026-11-27 用户指出当前 commit 描述信息过少、对后续回看帮助不足，并明确要求“后续的commit提交使用中文，添加约束”。
- 决策：新增 `docs/COMMIT_MESSAGES.md` 作为 commit message 权威规范；Conventional Commits type 前缀保持英文机器可读，摘要和正文必须使用中文；新增结构性 checker 并接入 CI。

### 边界

1. 非 merge commit 必须有正文，正文至少说明原因/变更/边界并包含 `验证：` 记录。
2. checker 只能验证结构，不能证明正文语义真实或充分。
3. GitHub 自动 merge commit 豁免格式检查。
4. 该规范不改变 AI 署名每次单独询问和贡献者身份政策。
5. 历史 commit 不回溯改写；规范适用于后续新 commit。


## D-0019 open main PR 阻塞门禁与 feature freshness

- 日期：2026-11-27
- 状态：`approved`
- 批准证据：2026-11-27 用户指出，仅按内容穷举治理 PR 无法保证不遗漏，并提出更通用的规则：“如果存在 pr 到 main 分支的未合并 pr，应该先处理这个 pr，然后再同步到特性分支，再继续”；用户同时明确 base 不是 main 的 feature 子 PR 不需要阻塞。
- 决策：采用通用 open-main-PR gate。任何 `feat/**` 分支在存在其他 base 为 `main` 的 open PR 时不得继续新增 feature 工作；必须先处理该 PR，合并或关闭后同步最新 main 再继续。`origin/main` 必须是活跃 feature 分支 HEAD 的 ancestor。

### 边界

1. 不按 PR 内容、标题或路径判断重要性；任何 open main PR 默认阻塞 feature 新工作，避免治理分类遗漏。
2. 当前 feature 分支自己的 main integration PR 不阻塞自己，因为更新该分支、修复 CI 和响应 review 都属于处理该 integration；它会阻塞其他 feature 分支。
3. base 不是 `main` 的 PR 不触发门禁，允许子代理或协作者向 feature 分支提交局部实现 PR。
4. CI 中无法查询 GitHub open PR 状态时 fail closed；本地网络不可用时只警告，最终以 CI 为准。
5. 该门禁不替代 integration queue、branch ownership、secret scan 或 main branch protection；它只解决 main 尚未前进但已存在悬空 main PR 的同步空窗。


## D-0020 push 前身份与署名政策改为异常触发

- 日期：2026-11-27
- 状态：`approved`
- 批准证据：2026-11-27 用户追问“每次单独询问”的来源和意义，并明确指出该策略与技能规范设计目标存在张力；随后用户明确要求“修正”，并要求沉淀解决方案和防复发机制。
- 决策：AI 署名和贡献者身份检查改为异常触发型政策。扫描无 AI 署名且作者均属于允许身份时，可按当前任务授权执行 push/PR/merge，不再仅因该政策重复询问；命中 AI 署名或名单外作者时必须暂停询问。为保持技能/hook 可解析性，机器可读约定分别使用 `push 前必须剥离署名` 与 `push 前必须统一作者`，并在 GIT_GOVERNANCE 中明确执行解释。高摩擦 recurring confirmation policy 不得由 agent 作为长期默认值自行建立，必须有明确用户批准和 decision 记录。

### 边界

1. 该政策不授权 direct push main、force push、改写历史、跳过 secret scan 或绕过 branch protection。
2. 禁止 AI 署名仍是项目默认；命中署名不得静默剥离，必须暂停并由用户决定保留、剥离或取消。
3. `notebook <tiankongzhise@163.com>` 是本地普通提交身份；GitHub noreply 身份仅允许用于 GitHub 自动 PR merge commit。
4. “每次单独询问”等高摩擦政策未来如确需恢复，必须在对应政策行或决策记录中引用明确 `D-xxxx` 证据。
5. `check_policy_evidence.py` 是结构 tripwire，只能防止无证据的高摩擦措辞重新出现，不能证明政策选择本身合理。


## D-0021 AGENTS.md 既有约束 mutation 保护

- 日期：2026-11-27
- 状态：`approved`
- 批准证据：2026-11-27 用户指出不应该扩大人工审计面，真正需要保护的是“`AGENTS.md` 原有内容被因模糊授权而修改”；随后用户明确说“按这个来实现，人应该只做最核心的审核”。
- 决策：建立窄范围 `AGENTS.md` mutation guard。纯机械修正和不改变语义的整理可由 agent 按当前任务授权处理；修改、删除、弱化或因重排改变既有 `AGENTS.md` 约束含义时，必须有明确用户批准，并记录对应 D-xxxx 决策证据。

### 边界

1. 不建立泛化的 control-plane 人工审核机制；其他文档的日常问题修复可由 agent 按现有 ownership/CI 流程处理。
2. “修正”“按规范处理”“继续”等模糊指令不能直接视为 `AGENTS.md` 既有约束 mutation 授权。
3. 授权模糊时必须先展示“原约束 → 拟改约束”的最小差异并等待确认。
4. `check_agents_mutation.py` 检测实质删除/改写行并要求决策证据；它是 tripwire，不能证明用户授权语义本身。
5. 该规则只保护根 `AGENTS.md` 既有约束，不要求用户审计所有局部经验沉淀。


## D-0022 根/领域 agent 规则分层与经验晋升机制

- 日期：2026-11-27
- 状态：`approved`
- 批准证据：2026-11-27 用户提出“人的精力有限”，只需审核上升到 `AGENTS.md` 的公共约束；其他有沉淀价值的问题可由 agent 写入对应领域文档。用户同时提出 `AGENTS.md` 需要分层，并批准“根 AGENTS + docs/agent-rules/ 逻辑领域规则 + 必要且自包含目录才用嵌套 AGENTS.md”的修正版方案。用户随后纠正：阶段审核门属于可变状态，不应写入根 `AGENTS.md`，必须由专门状态文件统一记录。
- 决策：采用三层规则模型：根 `AGENTS.md` 只保存全局硬约束和规则地图；逻辑领域规则放入 `docs/agent-rules/`；真正自包含目录才可使用嵌套 `AGENTS.md`。局部经验优先沉淀到最近的有效文档，只有跨领域或全局高风险事项才可提议提升到根 `AGENTS.md`，且提升必须经用户批准。

### 边界

1. 当前阶段、审核门和批准证据是可变状态，只由 `docs/PROJECT_STATUS.md`、DECISIONS 和已批准 CR 记录；不得在根 `AGENTS.md` 或领域规则中复制阶段门。
2. 领域规则只能更严格或更具体，不得弱化根 `AGENTS.md`。
3. 领域规则按 `docs/agent-rules/registry.json` 登记，并与 `docs/branch-ownership.json` 的 active branch ownership 保持一致。
4. 一次性 bug 修复不强制写文档；有复用价值的领域经验先写入领域层，不直接写入根文件。
5. 当前登记 `webui` 与 `backend` 两个 active domain；新增/停用领域规则必须同步 registry。
