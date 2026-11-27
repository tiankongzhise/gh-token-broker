# INFORMATION AUTHORITY — 单一权威来源规则

最近更新：2026-11-27

本文定义“同一事实只在一个权威位置登记和修改”的治理规则。机器可读登记表是 [authority-registry.json](authority-registry.json)；本文不复制完整登记项，避免再次形成双写。

## 1. 核心原则

1. **一个事实只有一个权威来源。** 其他文档可以链接、引用或摘录不可变语义，但不得独立维护同一份可变状态。
2. **批准/决策证据与当前状态分离。**
   - 决策内容、批准证据、替代方案：`docs/DECISIONS.md`。
   - 当前阶段、审核门、worktree、验证快照、远端 rollout 状态：`docs/PROJECT_STATUS.md`。
3. **artifact 文档不维护审批状态。** 例如 wireframes 文档应说明 artifact 内容和设计边界，并链接批准记录；不要写死“draft/待审核/已批准”等会过期状态。
4. **规范、执行文件和运行结果分离。** 例如 CI policy、workflow 文件、最近一次 CI 结果分别属于不同权威位置，不能混写。
5. **历史记录必须使用时间点语义。** changelog/decision 中的“当前/尚未/待验证”只代表当时；如果后来状态变化，应补时间限定或链接当前权威状态，不能留下看似仍然生效的旧事实。
6. **生成物不写死可变状态。** 生成脚本模板中的版本、审批状态、验证状态必须链接权威文档，或由生成时从权威数据源注入；不得手工同步多份副本。
7. **同 commit 更新。** 用户批准、否决或改变状态时，必须在同一提交中更新权威决策记录和当前状态；只有 artifact 内容本身变化时才修改 artifact 文档。

## 2. 变更操作流程

### 用户批准或否决某个事项

1. 在 `docs/DECISIONS.md` 新增或更新 decision entry，记录批准证据和边界。
2. 在 `docs/PROJECT_STATUS.md` 更新当前阶段/审核门/未决事项/验证快照。
3. 其他文档只添加或修正指向权威记录的链接；不要复制审批状态。
4. 如果 artifact 文档中存在旧状态文案，在同一任务中改为链接权威记录。
5. 运行 `python scripts/check_doc_authority.py`。

### 完成一次验证或远端 rollout

1. 把结果写入 `docs/PROJECT_STATUS.md` 的验证/状态快照。
2. 不把 transient 结果写进 policy 文档；policy 只描述门禁设计和静态配置。
3. 如果验证暴露了文档口径问题，补登记到 `docs/DOCUMENTATION_AUDIT.md`。

### 新增一类事实或新文档

1. 先判断权威来源属于哪类。
2. 如果是新类型，更新 `docs/authority-registry.json`。
3. 在 `AGENTS.md` 文档地图加入口，但不要在 AGENTS 复制细节。
4. 在 `docs/DOCUMENTATION_AUDIT.md` 更新文档覆盖状态。

## 3. 允许的引用方式

推荐：

```markdown
低保真审批状态见 [PROJECT_STATUS](PROJECT_STATUS.md)；批准证据见 D-0007。
```

不推荐：

```markdown
状态：draft 0.1，待人工审核
```

也不推荐在多个文档中分别维护“已批准/未批准/待复审”的副本。若确需面向读者展示状态，必须写成带权威链接的派生提示，并在权威状态变化时同 commit 更新；默认应避免这种副本。

## 4. 自动检查边界

`scripts/check_doc_authority.py` 能防止已登记的 stale 文案、缺失权威链接和登记表结构错误，但不能理解所有自然语言语义。因此：

- 新发现一类重复/过期状态，应把具体禁止文案或路径规则补进 `authority-registry.json`。
- 代码审查时仍需检查是否存在“事实看起来重复登记”的问题。
- 不能把 checker 通过当作文档语义无矛盾的完整证明。
