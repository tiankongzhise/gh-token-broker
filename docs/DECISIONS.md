# DECISIONS — GH Token Broker

本文记录重要技术/产品/治理决策。每个条目必须包含状态、证据、理由和后果。状态使用：`proposed`、`approved`、`rejected`、`superseded`。用户明确授权可作为 approved 证据；仅创建条目不等于批准。

## D-0001 License: LGPL 2.1

- 日期：2026-11-27
- 状态：`approved`（许可证族与版本）；`only` vs `or-later` 精确语义待确认
- 证据：用户明确说明“本项目使用 LGPL 2.1 许可”。
- 当前记录：仓库按 SPDX `LGPL-2.1-only` 处理，并在根目录保存完整许可证文本 `LICENSE`。

`LGPL-2.1-only` 与 `LGPL-2.1-or-later` 的核心区别：

- `LGPL-2.1-only`：下游只能按 LGPL 2.1 本版本的条款使用/修改/再分发。优点是条款确定、保守、可预期；缺点是不会自动获得未来 LGPL 版本可能带来的澄清、兼容性或法律文本改进。
- `LGPL-2.1-or-later`：下游可以选择 LGPL 2.1 或自由软件基金会之后发布的更新版本。优点是更能随许可证体系演进；缺点是版权方预先授权了当时尚未存在、尚未审阅的未来条款。
- 实务上，LGPL 2.1 与 LGPL 3 系列在专利授权、用户产品安装信息/反锁定等方面存在文本差异；是否接受这些未来/后续条款应作为明确选择，不应默认推断。

理由：

- 用户明确选择 LGPL 2.1，并提及其允许动态链接/动态库使用的意图。
- 在未明确“or later”的情况下，`LGPL-2.1-only` 是较保守解释，不额外授予未来许可证版本。

后果：

- README 不再声明“许可证未定”。
- 后续新增源文件是否需要许可证头，应在 Go module 初始化时确定并写入 DEVELOPMENT。
- 如果用户意图是 `LGPL-2.1-or-later`，需要修改 README、本文和可能的源码头声明。
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
