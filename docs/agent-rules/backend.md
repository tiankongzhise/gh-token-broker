# AGENT RULES — Backend Phase 2 领域

适用范围：`feat/backend-safe-delivery` 及其登记的 `cmd/`、`internal/`、`go.mod`、`go.sum`、`config.example.yaml` 工作。

## 读取顺序

1. 根 `AGENTS.md` 与 [PROJECT_STATUS](../PROJECT_STATUS.md)。
2. [ARCHITECTURE](../ARCHITECTURE.md)、[DEVELOPMENT](../DEVELOPMENT.md)、[CR-0001](../changes/CR-0001.md) 与相关决策。
3. 本文件只记录 backend 领域经验；当前审核门仍以 PROJECT_STATUS 为准。

## 领域约束

- Phase 2 按 CR-0001 先建立 scoped token、inventory、`min_ttl` 和最小 grant lifecycle；exec wrapper 与 credential helper 不得使用 parent token。
- scoped token 不可用时必须失败关闭，不得回退 parent token 或返回 raw token。
- 不声明真实 GitHub/device flow/Windows Credential Manager 冒烟已通过；真实验证结果只能写入 PROJECT_STATUS。
- 不修改 WebUI 设计路径、全局治理文档或其他领域 ownership。
