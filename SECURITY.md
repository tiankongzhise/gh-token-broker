# Security Policy

GH Token Broker 处理 GitHub 凭据和本地授权状态。安全边界、泄露响应和秘密扫描要求属于项目正确性的一部分。

## Supported Versions

项目尚未发布；当前没有受支持的稳定版本。发布前必须在本文补充版本支持和私密漏洞报告渠道。

## Reporting a Vulnerability

当前尚未配置专门的私密漏洞报告渠道；不要在公开 issue、PR、讨论或日志中提交真实秘密、可利用 token、未脱敏请求/响应或可复现的凭据材料。首次发布前维护者必须配置明确渠道（例如 GitHub Private Vulnerability Reporting 或安全联系人）并更新本节。

## 机密信息边界

秘密包括但不限于：

- GitHub access token / refresh token
- GitHub App client secret / private key
- master key / encryption key
- agent credential
- bearer token、密码、私钥、session cookie 和其他会话材料

这些秘密及可用派生值不得进入 Git 仓库、文档示例、测试 fixtures、日志、MCP tool result、WebUI、issue、PR、commit message 或临时脚本输出。

流程设计、认证流程、威胁模型、策略结构和错误语义可以公开；项目安全不得依赖 security through obscurity。

## push 前秘密扫描

每次 push 前必须在仓库根目录运行：

```powershell
python scripts/check_secrets.py
```

要求：

- 扫描失败不得 push。
- 不得删除、弱化或绕过扫描规则来让 push 通过。
- 误报用最小范围 allowlist 或改写示例处理。
- 扫描脚本只输出文件、行号和类型，不输出完整匹配秘密。

## 秘密泄露响应

如果真实秘密可能进入 Git 历史、公开页面、日志、模型上下文或其他不可控位置：

1. 立即撤销/轮换相关秘密；不要先花时间清理现场。
2. 评估影响范围：仓库历史、远端分支、issue/PR、日志、CI artifact、模型会话和备份。
3. 记录泄露类型、时间窗口、受影响身份/仓库和已执行轮换；记录中不得包含秘密值。
4. 评估是否需要清理 Git 历史、通知协作者或轮换派生凭据。
5. 只有把删除文件当作后续步骤；仅删除最新文件不能视为修复。

## 相关文档

- 威胁模型：[docs/THREAT_MODEL.md](docs/THREAT_MODEL.md)
- 架构安全边界：[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- 测试计划：[docs/TEST_PLAN.md](docs/TEST_PLAN.md)
