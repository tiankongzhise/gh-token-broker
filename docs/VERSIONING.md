# VERSIONING — 版本管理与发布控制

最近更新：2026-11-27

本文定义版本号、开发目标版本、release tag 和构建注入的边界。它只建立版本控制基础；**不批准或实现自动发布/CD**。

## 1. 事实来源分工

| 事实 | 权威位置 | 说明 |
|---|---|---|
| 版本管理原则与操作流程 | 本文 | 不复制具体当前版本号作为唯一事实 |
| 当前开发目标版本 | 根目录 `VERSION` | 表示当前 main 正在迈向的目标版本，不代表已经发布 |
| 正式发布事件 | Git tag `vX.Y.Z` | tag 是发布事件；release 时 tag 版本必须与 `VERSION` 一致 |
| 实际 CI/发布门禁 | `.github/workflows/` | 当前只有 CI；自动发布仍需单独批准 |
| 当前验证/发布状态 | [PROJECT_STATUS](PROJECT_STATUS.md) | 不在这里维护易漂移状态快照 |

## 2. 版本号规则

1. 使用 [Semantic Versioning 2.0.0](https://semver.org/lang/zh-CN/)：`MAJOR.MINOR.PATCH`。
2. 当前处于 pre-1.0 阶段， breaking change 不承诺自动提升 major；每次 release 的 bump 必须在 release PR 中明确。
3. 开发中的目标版本使用 prerelease 后缀 `-dev`，例如 `0.1.0-dev`。
4. 可选预发布使用 `-alpha.N`、`-beta.N`、`-rc.N`；`dev` 不得作为正式发布 tag。
5. release tag 使用 `v` 前缀，例如 `v0.1.0`；tag 去前缀后必须与根目录 `VERSION` 完全一致。
6. build metadata（例如 commit hash）只作为构建元数据注入，不写入 `VERSION`，也不参与版本优先级比较。

## 3. 开发/发布流程

### 日常开发

1. `VERSION` 记录当前开发目标版本；pre-1.0 阶段初始值为 `0.1.0-dev`。
2. 普通 feature/fix/chore PR 不随意修改 `VERSION`。
3. 只有 release preparation 或用户明确要求的版本节奏调整可以修改 `VERSION`。
4. CI 必须校验 `VERSION` 是合法 SemVer；tag CI 还必须校验 tag 与 `VERSION` 一致。

### Release preparation（未来，需单独批准执行）

1. 从最新 main 创建短生命周期 release prep 分支。
2. 将 `VERSION` 从 `X.Y.Z-dev` 改成目标 release 版本 `X.Y.Z`，并补充 release notes/changelog（格式另行批准）。
3. PR CI 通过后合并进 main。
4. main CI 通过后，在 merge commit 上创建 annotated tag `vX.Y.Z`。
5. tag CI 验证版本一致性；只有在这之后才允许进入任何打包/发布流程。
6. 发布后下一个开发周期再把 `VERSION` 调整为下一目标开发版本。

### 暂不实施的内容

- 不启用自动 release、自动 tag、自动上传 artifact 或自动发布 release notes。
- 不引入 release-please/semantic-release 等自动 bump 工具；未来如需引入必须单独评审供应链和权限边界。
- 不把 GitHub Release、签名、SBOM、校验和或依赖扫描视为已配置。

## 4. 构建注入与 CLI 表现

1. Go 二进制版本不硬编码为当前 release；默认开发值只能是 `dev`。
2. 正式构建通过 linker flags 注入版本，例如 `-X gh-token-broker/internal/version.Version=<version>`。
3. CLI 必须提供 `--version` 或等价命令，输出版本、commit 和构建日期（后两者未注入时显示 `unknown`）。
4. 测试不得依赖真实发布版本号；只能验证注入机制和输出格式。
5. 版本输出不得包含秘密、配置路径以外的敏感环境信息或 token material。

## 5. 检查

- `python scripts/check_version.py`：校验 `VERSION` 是单行合法 SemVer。
- 在 tag 上下文运行时：校验 `v*` tag 与 `VERSION` 一致，并禁止 `-dev` 作为 tag 版本。
- 该检查已接入 CI 的 repository hygiene 步骤。

## 6. 已知边界

- `VERSION` 与 tag 在 release 点受控重复：前者表示仓库目标版本，后者表示发布事件；CI 校验二者一致，这不是不受控的多头维护。
- 版本控制基础不等于发布自动化。首次正式发版前仍需补齐 release notes、artifact、checksum、签名/SBOM 和供应链门禁评审。
