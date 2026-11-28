from pathlib import Path

ROOT = Path(__file__).parent

AGENT_NAV = [
    ("Dashboard", "dashboard.html"),
    ("Approvals", "approval-inbox.html"),
    ("Audit", "audit-agent.html"),
    ("Settings", "settings-agent.html"),
]
MANUAL_NAV = [
    ("GitHub Apps", "github-apps.html"),
    ("Agents", "agents.html"),
    ("Token / Grants", "token-grants.html"),
    ("Audit", "audit-manual.html"),
    ("Settings", "settings-manual.html"),
]


def chips(items):
    return "".join(f'<span class="chip {kind}">{text}</span>' for text, kind in items)


def page(filename, title, mode, active, eyebrow, heading, sub, body):
    nav = AGENT_NAV if mode == "agent" else MANUAL_NAV
    other_href = "manual-mode.html" if mode == "agent" else "dashboard.html"
    mode_html = (
        f'<span class="on">Agent 审批模式</span><a href="{other_href}">人工模式</a>'
        if mode == "agent"
        else f'<a href="{other_href}">Agent 审批模式</a><span class="on">人工模式</span>'
    )
    nav_html = "".join(
        f'<a class="{"on" if label == active else ""}" href="{href}">{label}</a>' for label, href in nav
    )
    html = f'''<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>{title} — GH Token Broker</title>
  <link rel="stylesheet" href="styles.css">
</head>
<body>
<div class="app">
  <header class="topbar">
    <a class="logo" href="index.html">GH Token Broker</a>
    <span class="chip">高保真设计评审</span>
    <nav class="mode" aria-label="模式切换">{mode_html}</nav>
  </header>
  <div class="shell">
    <nav class="nav" aria-label="主导航">{nav_html}</nav>
    <main class="main">
      <div class="pagehead">
        <div>
          <div class="eyebrow">{eyebrow}</div>
          <h1>{heading}</h1>
          <div class="sub">{sub}</div>
        </div>
      </div>
      {body}
    </main>
  </div>
</div>
</body>
</html>
'''
    html = "\n".join(line.rstrip() for line in html.splitlines()) + "\n"
    (ROOT / filename).write_text(html, encoding="utf-8")


def write_index():
    body = '''
<div class="banner info">本目录是完整高保真评审稿。所有侧边导航均可点击；静态按钮会进入对应页面或页内确认状态。它仍不是正式前端实现。</div>
<div class="grid cols2" style="margin-top:16px">
  <a class="card emph linkcard" href="dashboard.html"><h2>Agent 审批模式</h2><p class="muted">Dashboard、授权码、申请审批、审计与设置。</p><span class="chip">默认模式</span></a>
  <a class="card linkcard" href="manual-mode.html"><h2>人工模式</h2><p class="muted">GitHub Apps、Agents、Token/Grants、审计与高级设置。</p><span class="chip">高级模式</span></a>
  <a class="card linkcard" href="partial-approval.html"><h2>细粒度部分批准</h2><p class="muted">按 agent、仓库和能力逐项授权，并用约束表达分支/仓库管理边界。</p><span class="chip warn">重点评审</span></a>
  <a class="card linkcard" href="states.html"><h2>异常与危险确认</h2><p class="muted">reauth、policy denied、secret store、revoke 等安全状态。</p><span class="chip danger">安全状态</span></a>
</div>
<div class="card" style="margin-top:16px"><h2>本轮修正的完整性要求</h2><div class="grid cols3 small"><div>✓ Dashboard 可点击</div><div>✓ 生成授权码有独立页面</div><div>✓ 审计/重新授权有目标页面</div><div>✓ Settings 不再缺失</div><div>✓ GitHub Apps / Agents / Token / Grants / Audit 均有页面</div><div>✓ 人工模式侧栏不再跳回 Agent 模式</div><div>✓ 高风险管理能力按 agent 独立配置，实现细节放入高级模式</div></div></div>
'''
    html = f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>GH Token Broker 高保真索引</title><link rel="stylesheet" href="styles.css"></head><body><div class="app"><header class="topbar"><span class="logo">GH Token Broker</span><span class="chip">高保真设计评审</span><nav class="mode"><a href="dashboard.html">Agent 审批模式</a><a href="manual-mode.html">人工模式</a></nav></header><main class="main" style="max-width:1180px;margin:0 auto"><div class="pagehead"><div><div class="eyebrow">Design Review</div><h1>高保真页面索引</h1><div class="sub">implementation-neutral HTML/CSS 设计稿，用于评审视觉层级、信息密度、交互路径和桌面使用体验；不代表正式前端技术栈。</div></div></div>{body}</main></div></body></html>'''
    html = "\n".join(line.rstrip() for line in html.splitlines()) + "\n"
    (ROOT / "index.html").write_text(html, encoding="utf-8")


write_index()

page(
    "dashboard.html", "Dashboard", "agent", "Dashboard", "Agent Approval Mode", "Dashboard",
    "默认模式只保留用户必须处理的事项：生成授权码、审批申请、查看安全状态与审计摘要。",
    '''
<div class="grid cols3">
  <div class="card"><div class="muted small">待审批申请</div><div class="metric">3</div><span class="chip warn">1 个批量高风险</span></div>
  <div class="card"><div class="muted small">活跃 Agents</div><div class="metric">5</div><span class="chip ok">凭证状态正常</span></div>
  <div class="card"><div class="muted small">需要重新授权</div><div class="metric">1</div><a class="chip danger" href="reauth.html">查看 reauth</a></div>
</div>
<div class="grid cols2" style="margin-top:16px">
  <div class="card emph"><div class="between"><h2>快速操作</h2><span class="chip">审批优先</span></div><div class="row wrap"><a class="btn primary" href="authorization-code.html">生成一次性授权码</a><a class="btn" href="approval-inbox.html">处理待审批申请</a><a class="btn ghost" href="audit-agent.html">查看审计</a></div><p class="muted small">授权码只用于提交申请，不直接代表 GitHub 权限。</p></div>
  <div class="card"><h2>系统状态</h2><table class="table"><tr><td>Discovery public node</td><td><span class="chip ok">127.0.0.1 only</span></td></tr><tr><td>Secret store</td><td><span class="chip ok">可用</span></td></tr><tr><td>GitHub App 授权链</td><td><span class="chip warn">1 个账号需 reauth</span></td></tr></table></div>
</div>
<div class="card" style="margin-top:16px"><div class="between"><h2>最近事件</h2><a class="btn ghost" href="audit-agent.html">查看全部审计</a></div><table class="table"><tr><th>时间</th><th>事件</th><th>对象</th><th>结果</th></tr><tr><td>10:42</td><td>permission application</td><td>devin / repo-a</td><td><span class="chip warn">pending</span></td></tr><tr><td>10:41</td><td>仓库管理能力请求</td><td>创建仓库（受限）</td><td><a class="chip warn" href="partial-approval.html#repository-management">pending · 去审批</a></td></tr><tr><td>10:17</td><td>grant redeemed</td><td>repo-b</td><td><span class="chip ok">success</span></td></tr><tr><td>09:58</td><td>refresh failed</td><td>github.com/octo</td><td><a class="chip danger" href="reauth.html">需要重新授权</a></td></tr></table></div>
''')

page(
    "authorization-code.html", "生成授权码", "agent", "Dashboard", "One-time Agent Authorization", "生成一次性授权码",
    "授权码只用于 agent 提交权限申请；它本身不是 GitHub token，也不会让 agent 直接访问仓库。",
    '''
<div class="grid cols2">
  <div class="card emph"><h2>新授权码</h2><p class="muted">以下示例是设计稿伪数据。真实实现中明文只显示一次，服务端只保存 hash。</p><div class="code">GTB-AGENT-EXAMPLE-ONLY-7K4Q-9M2X</div><div class="row wrap" style="margin-top:12px"><a class="btn primary" href="#copied">复制授权码</a><a class="btn" href="approval-inbox.html">等待申请</a><a class="btn danger" href="#revoked">撤销</a></div><div id="copied" class="target-note">已复制示意：真实 UI 会显示短暂 toast，不记录明文。</div><div id="revoked" class="target-note danger-note">撤销确认示意：撤销后该 code 不能提交申请。</div></div>
  <div class="card"><h2>约束</h2><table class="table"><tr><td>有效期</td><td>10 分钟</td></tr><tr><td>使用次数</td><td>1 次</td></tr><tr><td>用途</td><td>提交 permission application</td></tr><tr><td>绑定</td><td>本地 broker + loopback discovery</td></tr><tr><td>审计</td><td>创建、使用、撤销均记录</td></tr></table><div class="banner info" style="margin-top:12px">不要把授权码粘贴到不受信聊天或 issue；泄露后可撤销。</div></div>
</div>
''')

page(
    "approval-inbox.html", "Approvals", "agent", "Approvals", "Approval Inbox", "待审批申请",
    "左侧选择申请，右侧核对风险、仓库范围和 agent 自述用途；默认不批准高风险权限。",
    '''
<div class="row wrap" style="margin-bottom:14px"><a class="btn primary" href="authorization-code.html">生成授权码</a><a class="btn" href="audit-agent.html">查看申请审计</a><a class="btn ghost" href="settings-agent.html">审批设置</a></div>
<div class="grid approvals">
  <div class="list">
    <a class="item sel" href="#detail"><div class="between"><b>Devin Coding Agent</b><span class="chip danger">批量高风险</span></div><div class="muted small">3 repos + 受限管理能力 · 2h</div></a>
    <a class="item" href="partial-approval.html"><div class="between"><b>Local CLI Agent</b><span class="chip warn">部分降权建议</span></div><div class="muted small">1 repo · pr-write · 1h</div></a>
    <a class="item" href="#detail"><div class="between"><b>Research Bot</b><span class="chip ok">低权限</span></div><div class="muted small">1 repo · read-only · 30m</div></a>
  </div>
  <div class="card" id="detail"><div class="between"><h2>Devin Coding Agent</h2><span class="chip danger">高权限申请</span></div><div class="banner danger">一次申请 3 个仓库的广泛读写和受限仓库管理能力。高风险能力默认未勾选，必须逐仓库、逐项能力确认或降级。</div><table class="table"><tr><th>仓库</th><th>申请上限</th><th>min_ttl</th><th>建议</th></tr><tr><td>octo/repo-a</td><td>广泛读写 + 管理操作</td><td>2h</td><td><a href="partial-approval.html" class="chip warn">细粒度调整</a></td></tr><tr><td>octo/repo-b</td><td>广泛读写 + 管理操作</td><td>2h</td><td><span class="chip danger">默认拒绝</span></td></tr><tr><td>octo/repo-c</td><td>广泛读写 + 管理操作</td><td>2h</td><td><span class="chip warn">需确认</span></td></tr></table><h3>同时申请的仓库管理操作</h3><table class="table"><tr><th>能力</th><th>范围</th><th>风险</th></tr><tr><td>创建仓库（受限）</td><td>octo 账户，最多 1 个私有仓库</td><td><span class="chip warn">高风险但受限</span></td></tr><tr><td>为新仓库保护 main（受限）</td><td>仅作用于本次创建的仓库</td><td><span class="chip warn">必须使用安全模板</span></td></tr></table><h3>agent 自述用途（未验证）</h3><p class="muted">“需要创建分支、推送提交并打开 PR。”该说法不是安全事实。</p><div class="row wrap"><a class="btn primary" href="partial-approval.html">进入逐项授权审批</a><a class="btn" href="#approved">全部批准</a><a class="btn danger" href="#rejected">拒绝申请</a></div><div id="approved" class="target-note danger-note">全部批准确认示意：真实 UI 会要求再次确认高风险权限。</div><div id="rejected" class="target-note danger-note">拒绝确认示意：拒绝会返回机器可读结果并写审计。</div></div>
</div>
''')

page(
    "partial-approval.html", "部分批准与能力授权", "agent", "Approvals", "Capability Approval", "按 agent、仓库和能力逐项授权",
    "你只需要决定 Devin Coding Agent 能做什么；系统负责选择安全的执行方式。若限制无法被可靠执行，对应能力会不可用，而不是静默放大权限。",
    '''
<div class="banner danger">本次申请只针对 <b>Devin Coding Agent</b>，不是全局配置。agent 申请的上限较宽；下面把上限展开成可理解的能力，你可以按仓库逐项缩小或拒绝。</div>
<div class="row wrap" style="margin-top:12px"><a class="btn danger" href="#repository-management">先审仓库管理能力</a><a class="btn" href="#repo-a">配置 repo-a</a><a class="btn" href="#repo-b">查看 repo-b</a><a class="btn" href="#repo-c">配置 repo-c</a></div>
<div class="card" style="margin-top:16px"><h2>授权结果总览</h2><table class="table"><tr><th>对象</th><th>当前决定</th><th>最终能力摘要</th><th>配置位置</th></tr><tr><td>octo/repo-a</td><td><span class="chip warn">自定义子集</span></td><td>可读；只写 agent/*；只可删除符合条件的 agent/* 短期分支；可开 PR；不可 merge</td><td><a href="#repo-a">配置 repo-a</a></td></tr><tr><td>octo/repo-b</td><td><span class="chip danger">拒绝</span></td><td>无能力，不创建授权</td><td><a href="#repo-b">查看 repo-b</a></td></tr><tr><td>octo/repo-c</td><td><span class="chip warn">自定义子集</span></td><td>可读；只写 agent/exp-*；不可删分支；可开 PR；merge 仅在检查和 review 满足后允许</td><td><a href="#repo-c">配置 repo-c</a></td></tr></table></div>
<div class="card" style="margin-top:16px" id="repository-management"><div class="between"><h2>仓库管理能力</h2><span class="chip danger">高风险 · 仅本 agent</span></div><div class="banner info">这些同样是“agent 能做什么”的授权项。目标 owner 文案中的 octo 是示例 GitHub 账户/组织。删除仓库、解除保护、任意修改设置和管理协作者不开放。</div><table class="table" style="margin-top:12px"><tr><th>申请的能力</th><th>范围</th><th>约束</th><th>授权决定</th><th>最终效果</th></tr><tr><td><b>创建仓库</b></td><td>octo（示例 GitHub 账户/组织）</td><td>最多 1 个；只能私有；名称需符合 agent-exp-*</td><td><select><option selected>允许 1 次</option><option>拒绝</option></select></td><td>agent 可请求创建；不能删除</td></tr><tr><td><b>为新仓库保护 main</b></td><td>只允许作用于本次创建的仓库</td><td>必须使用安全保护模板；不能关闭或弱化保护</td><td><select><option selected>允许 1 次</option><option>拒绝</option></select></td><td>main 默认受保护</td></tr><tr><td><b>删除仓库 / 解除保护 / 修改设置 / 管理协作者</b></td><td>任意仓库</td><td>不开放申请</td><td><select disabled><option selected>固定禁止</option></select></td><td>始终禁止</td></tr></table></div>
<div class="card" style="margin-top:16px"><h2>能力含义速查</h2><div class="grid cols2 small"><div><b>写入分支</b><div class="muted">允许 agent 修改指定分支上的内容。可以通过 branch pattern 限制到 agent/*，并排除 main/release 等重要分支。</div></div><div><b>删除分支</b><div class="muted">删除是独立能力，不因“能写分支”自动允许。可限制为 agent/*、短期、已合并或超过指定时间的分支。</div></div><div><b>Pull Request</b><div class="muted">创建/更新 PR 与 merge PR 是不同能力。merge 可以要求 checks 和 review 满足。</div></div><div><b>不可安全执行</b><div class="muted">如果系统不能保证限制不被绕过，对应能力应显示不可用或拒绝，而不是用更宽权限代替。</div></div></div></div>
<div class="grid" style="margin-top:16px">
  <section class="card emph" id="repo-a"><div class="between"><h2>octo/repo-a</h2><span class="chip warn">独立能力矩阵</span></div><table class="table"><tr><td>决定</td><td><select><option selected>批准并使用自定义子集</option><option>按申请上限批准</option><option>拒绝</option></select></td></tr></table><h3>repo-a 能力</h3><table class="table"><tr><th>能力</th><th>申请上限</th><th>repo-a 最终授权</th><th>约束</th></tr><tr><td>读取仓库内容</td><td>允许</td><td><select><option selected>允许</option><option>拒绝</option></select></td><td>全部内容</td></tr><tr><td>写入分支</td><td>所有分支</td><td><select><option selected>仅 agent/*</option><option>所有分支</option><option>拒绝</option></select></td><td>禁止 main 和 release/*；最多 5 个活跃分支</td></tr><tr><td>删除分支</td><td>所有分支</td><td><select><option selected>仅符合条件的 agent/*</option><option>所有分支</option><option>拒绝</option></select></td><td>已合并或 7 天未更新；最多 5 次/天；受保护分支除外</td></tr><tr><td>创建/更新 Pull Request</td><td>允许</td><td><select><option selected>允许</option><option>拒绝</option></select></td><td>最多 3 个打开 PR</td></tr><tr><td>Merge Pull Request</td><td>允许</td><td><select><option selected>拒绝</option><option>仅 checks/review 满足后允许</option></select></td><td>本示例不授予 merge</td></tr><tr><td>Issues</td><td>读写</td><td><select><option>读写</option><option selected>只读/评论</option><option>拒绝</option></select></td><td>不可关闭他人 issue</td></tr></table><div class="diff" style="margin-top:14px"><div class="item"><b>repo-a 申请</b><div class="muted small">广泛读写 + 分支管理</div></div><div class="arrow">→</div><div class="item"><b>repo-a 最终</b><div class="muted small">读；写 agent/*；删除受限 agent/*；可开 PR；不可 merge</div></div></div></section>
  <section class="card" id="repo-b"><div class="between"><h2>octo/repo-b</h2><span class="chip danger">本仓库拒绝</span></div><table class="table"><tr><td>决定</td><td><select><option>批准并使用自定义子集</option><option>按申请上限批准</option><option selected>拒绝</option></select></td></tr></table><div class="banner danger">repo-b 当前被拒绝：不创建任何能力授权。下面的能力保持禁用，防止误读为已授权。</div><table class="table" style="margin-top:12px"><tr><th>能力</th><th>repo-b 最终授权</th></tr><tr><td>读取/写入/删除分支/PR/Issues</td><td><select disabled><option>全部拒绝</option></select></td></tr></table></section>
  <section class="card emph" id="repo-c"><div class="between"><h2>octo/repo-c</h2><span class="chip warn">独立能力矩阵</span></div><table class="table"><tr><td>决定</td><td><select><option selected>批准并使用自定义子集</option><option>按申请上限批准</option><option>拒绝</option></select></td></tr></table><h3>repo-c 能力</h3><table class="table"><tr><th>能力</th><th>申请上限</th><th>repo-c 最终授权</th><th>约束</th></tr><tr><td>读取仓库内容</td><td>允许</td><td><select><option selected>允许</option><option>拒绝</option></select></td><td>全部内容</td></tr><tr><td>写入分支</td><td>所有分支</td><td><select><option selected>仅 agent/exp-*</option><option>仅 agent/*</option><option>拒绝</option></select></td><td>最多 1 个活跃实验分支</td></tr><tr><td>删除分支</td><td>所有分支</td><td><select><option>仅符合条件的 agent/*</option><option selected>拒绝</option></select></td><td>本仓库不允许删除</td></tr><tr><td>创建/更新 Pull Request</td><td>允许</td><td><select><option selected>允许</option><option>拒绝</option></select></td><td>最多 1 个打开 PR</td></tr><tr><td>Merge Pull Request</td><td>允许</td><td><select><option selected>仅 checks/review 满足后允许</option><option>拒绝</option></select></td><td>required checks 通过且至少 1 个 review</td></tr><tr><td>Issues</td><td>读写</td><td><select><option>读写</option><option>只读/评论</option><option selected>拒绝</option></select></td><td>本仓库不使用 issues</td></tr></table><div class="diff" style="margin-top:14px"><div class="item"><b>repo-c 申请</b><div class="muted small">广泛读写 + 分支管理</div></div><div class="arrow">→</div><div class="item"><b>repo-c 最终</b><div class="muted small">读；写 agent/exp-*；不可删分支；可开 PR；条件满足后可 merge</div></div></div></section>
</div>
<div class="card" style="margin-top:16px"><h2>确认最终授权</h2><p class="muted">确认结果必须按 agent、仓库、能力和约束分别记录。底层由系统选择安全执行方式；如果某限制无法可靠执行，对应能力必须不可用或失败关闭。</p><div class="row wrap"><a class="btn primary" href="#confirmed">确认 2 个仓库授权与 2 个受限管理能力</a><a class="btn" href="approval-inbox.html">返回 inbox</a><a class="btn danger" href="#reject-all">全部拒绝</a></div><div id="confirmed" class="target-note">确认示意：repo-a 与 repo-c 使用各自独立能力矩阵；repo-b 被拒绝；两项仓库管理能力仅在受限约束内允许。审计按 agent、资源、能力和约束分别记录。</div><div id="reject-all" class="target-note danger-note">全部拒绝示意：不会创建任何授权或访问凭据。</div></div>
''')

page(
    "audit-agent.html", "Audit", "agent", "Audit", "Audit Log", "审计记录",
    "默认模式只展示与审批、安全状态和 grant/token 生命周期相关的审计，不显示秘密。",
    '''
<div class="row wrap" style="margin-bottom:14px"><a class="btn" href="#filters">筛选</a><a class="btn" href="reauth.html">处理重新授权</a><a class="btn ghost" href="dashboard.html">返回 Dashboard</a></div>
<div class="card" id="filters"><h2>筛选条件</h2><div class="grid cols3"><select><option>全部事件</option><option>grant</option><option>reauth</option></select><select><option>全部结果</option><option>success</option><option>denied</option></select><input class="input" value="octo/repo-a"></div></div>
<div class="card" style="margin-top:16px"><h2>事件列表</h2><table class="table"><tr><th>时间</th><th>事件</th><th>对象</th><th>结果</th><th>操作</th></tr><tr><td>10:42</td><td>permission application</td><td>devin / 3 repos</td><td><span class="chip warn">pending</span></td><td><a href="approval-inbox.html">去审批</a></td></tr><tr><td>10:41</td><td>仓库管理能力请求</td><td>创建仓库（受限）</td><td><span class="chip warn">pending</span></td><td><a href="partial-approval.html#repository-management">去审批</a></td></tr><tr><td>09:58</td><td>refresh failed</td><td>github.com/octo</td><td><span class="chip danger">reauth_required</span></td><td><a href="reauth.html">重新授权</a></td></tr><tr><td>09:12</td><td>policy denied</td><td>repo-c / 高权限申请</td><td><span class="chip danger">denied</span></td><td><a href="#denied-detail">查看原因</a></td></tr><tr><td>08:46</td><td>token_scoped_minted</td><td>repo-a</td><td><span class="chip ok">success</span></td><td><a href="#token-detail">查看元数据</a></td></tr></table></div>
<div class="grid cols2" style="margin-top:16px"><div class="card" id="denied-detail"><h2>policy denied 详情</h2><p class="muted">申请超出该 agent 已批准能力上限；未返回任何凭据。</p></div><div class="card" id="token-detail"><h2>token issue 元数据</h2><p class="muted">只显示 issue id、hash prefix、expires_at 和权限摘要；不显示 token。</p></div></div>
''')

page(
    "reauth.html", "重新授权", "agent", "Audit", "Explicit Reauthorization", "重新授权确认",
    "普通 token/grant 请求不得自动启动 device flow；必须由用户显式确认。",
    '''
<div class="grid cols2"><div class="card emph"><h2>github.com / octo</h2><p class="muted">refresh chain 返回 reauth_required。继续前请确认这是你本人发起的授权恢复。</p><div class="row wrap"><a class="btn primary" href="#device-flow">显式启动 device flow</a><a class="btn" href="audit-agent.html">查看触发审计</a><a class="btn danger" href="#disable">暂停该账号</a></div><div id="device-flow" class="target-note">device flow 启动示意：真实 UI 会显示 verification URI 和 user code，不会自动请求权限。</div><div id="disable" class="target-note danger-note">暂停确认示意：暂停后 grant/token 请求失败关闭。</div></div><div class="card"><h2>影响范围</h2><table class="table"><tr><td>现有 refresh token</td><td>不再使用</td></tr><tr><td>agent 请求</td><td>失败关闭</td></tr><tr><td>已签发 token</td><td>按 GitHub expiry/inventory 处理</td></tr><tr><td>审计</td><td>记录 reauth started/completed/failed</td></tr></table></div></div>
''')

page(
    "settings-agent.html", "Settings", "agent", "Settings", "Approval Mode Settings", "审批模式设置",
    "默认模式只暴露低风险偏好；高风险策略和 GitHub App 管理留在人工模式。",
    '''
<div class="grid cols2">
  <div class="card"><h2>审批偏好</h2><table class="table"><tr><td>默认 min_ttl</td><td><select><option>2 小时</option><option>1 小时</option><option>30 分钟</option></select></td></tr><tr><td>高风险权限默认</td><td><select><option>默认拒绝/不勾选</option><option>每次单独确认</option></select></td></tr><tr><td>批量申请提醒</td><td><select><option>强提醒</option><option>普通提醒</option></select></td></tr></table><div class="row" style="margin-top:12px"><a class="btn primary" href="#saved">保存设置</a></div><div id="saved" class="target-note">保存示意：真实实现只保存非秘密偏好。</div></div>
  <div class="card"><h2>安全边界（只读）</h2><table class="table"><tr><td>Discovery</td><td><span class="chip ok">仅 127.0.0.1</span></td></tr><tr><td>raw token 返回</td><td><span class="chip danger">未批准</span></td></tr><tr><td>client secret 管理</td><td><a href="manual-mode.html">人工模式</a></td></tr></table><div class="banner info" style="margin-top:12px">模式切换只能由顶部显式切换；侧栏页面不会让你误入另一模式。</div></div>
</div>
''')

# Manual mode pages
page(
    "manual-mode.html", "人工模式", "manual", "GitHub Apps", "Manual Mode", "人工模式总览",
    "高级管理界面，侧栏始终停留在人工模式；不会因为在人工模式点击 Audit 或 Settings 而跳回 Agent 模式。",
    '''
<div class="grid cols2">
  <a class="card linkcard" href="github-apps.html"><h2>GitHub Apps</h2><p class="muted">App client id、授权账号、refresh chain 状态和 secret ref 元数据。</p></a>
  <a class="card linkcard" href="agents.html"><h2>Agents</h2><p class="muted">agent credential fingerprint、启用状态和策略入口。</p></a>
  <a class="card linkcard" href="token-grants.html"><h2>Token / Grants</h2><p class="muted">scoped token inventory、grant lifecycle、revoke 与过期状态。</p></a>
  <a class="card linkcard" href="audit-manual.html"><h2>Audit</h2><p class="muted">完整审计筛选、导出与排障入口。</p></a>
</div>
<div class="banner info" style="margin-top:16px">人工模式是高级路径，不改变默认审批优先 UX；秘密值永不显示。</div>
''')

page(
    "github-apps.html", "GitHub Apps", "manual", "GitHub Apps", "Manual / GitHub Apps", "GitHub App 管理",
    "管理 GitHub App 元数据、授权账号和 secret ref；不显示 client secret、refresh token 或 private key。",
    '''
<div class="row wrap" style="margin-bottom:14px"><a class="btn primary" href="#add-app">添加 GitHub App</a><a class="btn" href="audit-manual.html">查看授权审计</a></div>
<div class="grid cols2"><div class="card"><h2>gh-token-broker-dev</h2><table class="table"><tr><td>client_id</td><td>Iv1.example</td></tr><tr><td>host</td><td>github.com</td></tr><tr><td>client secret</td><td><span class="chip ok">secret ref configured</span></td></tr><tr><td>授权账号</td><td>octo</td></tr><tr><td>refresh chain</td><td><span class="chip warn">reauth_required</span></td></tr></table><div class="row wrap"><a class="btn" href="reauth-manual.html">重新授权</a><a class="btn ghost" href="#app-detail">详情</a></div></div><div class="card" id="add-app"><h2>添加 App（表单示意）</h2><input class="input" value="Client ID" style="margin-bottom:8px"><input class="input" value="secret ref（不是 secret 明文）" style="margin-bottom:8px"><select><option>加密 SQLite secret ref</option><option>Windows Credential Manager ref</option></select><div class="row" style="margin-top:10px"><a class="btn primary" href="#saved-app">保存元数据</a></div><div id="saved-app" class="target-note">保存示意：secret 明文不能粘贴到普通配置。</div></div></div>
<div class="card" id="app-detail" style="margin-top:16px"><h2>App 详情</h2><p class="muted">只显示元数据、错误码和最近授权状态；秘密材料只能从 secret store 内部读取。</p></div>
''')

page(
    "reauth-manual.html", "人工模式重新授权", "manual", "GitHub Apps", "Manual / Reauthorization", "GitHub App 授权恢复",
    "人工模式下的显式重新授权页面；不会跳回 Agent 审批模式，也不会自动启动 device flow。",
    '''
<div class="grid cols2"><div class="card emph"><h2>gh-token-broker-dev / octo</h2><p class="muted">refresh chain 处于 reauth_required。必须由用户显式确认后才能启动 device flow。</p><div class="row wrap"><a class="btn primary" href="#start-flow">显式启动 device flow</a><a class="btn" href="github-apps.html">返回 GitHub Apps</a><a class="btn danger" href="#pause-account">暂停账号</a></div><div id="start-flow" class="target-note">device flow 启动示意：显示 verification URI 和 user code；这不是自动后台续期。</div><div id="pause-account" class="target-note danger-note">暂停确认示意：后续 scoped mint、grant 和 helper 请求失败关闭。</div></div><div class="card"><h2>审计要求</h2><table class="table"><tr><td>reauth_started</td><td>记录 actor 与 account</td></tr><tr><td>reauth_completed</td><td>不记录 token</td></tr><tr><td>reauth_failed</td><td>记录错误码，不记录秘密</td></tr></table><a class="btn" href="audit-manual.html" style="margin-top:10px">查看相关审计</a></div></div>
''')

page(
    "agents.html", "Agents", "manual", "Agents", "Manual / Agents", "Agent credential 管理",
    "每个 agent 有独立 credential；界面只显示 fingerprint/prefix，不显示 credential 明文。",
    '''
<div class="row wrap" style="margin-bottom:14px"><a class="btn primary" href="#create-agent">创建 Agent credential</a><a class="btn" href="audit-manual.html">查看 agent 审计</a></div>
<div class="card"><table class="table"><tr><th>Agent</th><th>fingerprint</th><th>状态</th><th>仓库/profile</th><th>操作</th></tr><tr><td>Devin Coding Agent</td><td><span class="code inline">sha256:9f2a…</span></td><td><span class="chip ok">enabled</span></td><td>repo-a · custom subset</td><td><a class="btn" href="agents-edit.html">编辑</a></td></tr><tr><td>Local CLI Agent</td><td><span class="code inline">sha256:71bc…</span></td><td><span class="chip warn">expiring</span></td><td>repo-b · pr-write</td><td><a class="btn" href="agents-edit.html">编辑</a></td></tr><tr><td>Research Bot</td><td><span class="code inline">sha256:aa10…</span></td><td><span class="chip danger">disabled</span></td><td>repo-c · read-only</td><td><a class="btn" href="agents-edit.html">编辑</a></td></tr></table></div>
<div class="card" id="create-agent" style="margin-top:16px"><h2>创建 credential（示意）</h2><p class="muted">真实实现只在创建时显示一次 credential，服务端保存 hash/派生值。</p><a class="btn primary" href="#created">生成 credential</a><div id="created" class="target-note">生成示意：后续只能看到 fingerprint，不能再次查看明文。</div></div>
''')

page(
    "agents-edit.html", "编辑 Agent", "manual", "Agents", "Manual / Agents", "编辑 Agent credential 与策略",
    "编辑 agent 启用状态、仓库/profile 边界和 credential rotation；所有高风险动作需要显式确认。",
    '''
<div class="grid cols2">
  <div class="card"><h2>Devin Coding Agent</h2><table class="table"><tr><td>fingerprint</td><td><span class="code inline">sha256:9f2a…</span></td></tr><tr><td>状态</td><td><select><option>enabled</option><option>disabled</option></select></td></tr><tr><td>host</td><td>github.com</td></tr><tr><td>允许仓库</td><td>octo/repo-a</td></tr><tr><td>能力策略上限</td><td>仅本 agent；application 只能缩小不得扩大</td></tr><tr><td>min_ttl</td><td>2h</td></tr><tr><td>分支写/删约束</td><td>写 agent/*；删除仅 agent/* 且已合并或 7 天未更新；受保护分支除外</td></tr><tr><td>仓库管理能力</td><td>创建私有仓库 1 次；仅可为新仓库应用安全 main 保护；删除/设置/协作者固定禁止</td></tr><tr><td>高级实现映射</td><td>create_repository_with_secure_baseline；configure_main_branch_protection（仅高级模式可见）</td></tr></table><div class="row wrap" style="margin-top:12px"><a class="btn primary" href="#saved">保存策略</a><a class="btn" href="audit-manual.html">查看审计</a><a class="btn danger" href="#disable-agent">禁用</a></div><div id="saved" class="target-note">保存示意：不允许扩大到审批决定之外的仓库。</div><div id="disable-agent" class="target-note danger-note">禁用确认示意：后续请求失败关闭，已签发 token 仍按 expiry/inventory 处理。</div></div>
  <div class="card"><h2>credential rotation</h2><p class="muted">轮换后旧 credential 立即失效；新明文只显示一次。</p><div class="row wrap"><a class="btn" href="#rotated">轮换 credential</a><a class="btn danger" href="#revoke-grants">撤销相关 grants</a></div><div id="rotated" class="target-note">轮换确认示意：记录 agent_credential_rotated。</div><div id="revoke-grants" class="target-note danger-note">撤销 grants 确认示意：只影响未兑换/未过期 grant，不伪造已用 token 立即失效。</div></div>
</div>
''')

page(
    "token-grants.html", "Token / Grants", "manual", "Token / Grants", "Manual / Token Inventory", "Token 与 Grant inventory",
    "只显示 hash prefix、状态和过期时间；不显示 parent token、refresh token、scoped token 明文或 grant id 明文。",
    '''
<div class="grid cols2">
  <div class="card"><h2>Scoped token inventory</h2><table class="table"><tr><th>issue</th><th>repo</th><th>hash</th><th>expires</th><th>状态</th></tr><tr><td>tok_a91…</td><td>repo-a</td><td>sha256:71ab…</td><td>11:58</td><td><span class="chip ok">active</span></td></tr><tr><td>tok_c42…</td><td>repo-b</td><td>sha256:0fe1…</td><td>expired</td><td><span class="chip">expired</span></td></tr></table><div class="row" style="margin-top:10px"><a class="btn danger" href="#revoke-token">撤销选中 token</a></div><div id="revoke-token" class="target-note danger-note">revoke 确认示意：真实 GitHub revoke 语义未实测前，界面必须标注不确定结果。</div></div>
  <div class="card"><h2>Grant lifecycle</h2><table class="table"><tr><th>grant hash</th><th>agent</th><th>repo</th><th>status</th><th>用途</th></tr><tr><td>sha256:88aa…</td><td>devin</td><td>repo-a</td><td><span class="chip ok">active</span></td><td>0/1</td></tr><tr><td>sha256:19ff…</td><td>cli</td><td>repo-b</td><td><span class="chip warn">redeemed</span></td><td>1/1</td></tr><tr><td>sha256:52cd…</td><td>research</td><td>repo-c</td><td><span class="chip danger">revoked</span></td><td>0/1</td></tr></table><div class="row wrap" style="margin-top:10px"><a class="btn danger" href="#revoke-grant">撤销 active grant</a><a class="btn" href="audit-manual.html">查看 grant 审计</a></div><div id="revoke-grant" class="target-note danger-note">grant revoke 确认示意：grant 不是 GitHub token，撤销它不会直接 revoke 已签发 token。</div></div>
</div>
''')

page(
    "audit-manual.html", "Manual Audit", "manual", "Audit", "Manual / Audit", "完整审计与排障",
    "人工模式审计页保留在人工模式；支持更完整筛选、导出和关联对象跳转。",
    '''
<div class="card"><h2>筛选</h2><div class="grid cols3"><select><option>全部 actor</option><option>agent</option><option>user</option><option>system</option></select><select><option>全部事件</option><option>token</option><option>grant</option><option>webui_admin_action</option></select><input class="input" value="correlation id / repo / fingerprint prefix"></div></div>
<div class="card" style="margin-top:16px"><table class="table"><tr><th>时间</th><th>actor</th><th>事件</th><th>subject</th><th>outcome</th><th>操作</th></tr><tr><td>10:42</td><td>user</td><td>approval_decision</td><td>application app_01</td><td><span class="chip warn">partial</span></td><td><a href="#detail-1">详情</a></td></tr><tr><td>10:44</td><td>system</td><td>operation_capability_granted</td><td>create_repository_with_secure_baseline</td><td><span class="chip warn">template_only</span></td><td><a href="#detail-1">详情</a></td></tr><tr><td>10:45</td><td>system</td><td>token_scoped_minted</td><td>tok_a91…</td><td><span class="chip ok">success</span></td><td><a href="token-grants.html">inventory</a></td></tr><tr><td>10:47</td><td>agent</td><td>grant_redeemed</td><td>sha256:88aa…</td><td><span class="chip ok">success</span></td><td><a href="token-grants.html">grant</a></td></tr><tr><td>10:51</td><td>user</td><td>webui_admin_action</td><td>agent sha256:9f2a…</td><td><span class="chip danger">disabled</span></td><td><a href="agents-edit.html">agent</a></td></tr></table></div>
<div class="card" id="detail-1" style="margin-top:16px"><h2>审批决定详情</h2><p class="muted">repo-a/repo-c 被授予申请上限内的自定义权限子集；repo-b 被拒绝；operation capability 与仓库 token 授权分开记录。审计 metadata 不包含 token 或 credential。</p><a class="btn" href="#exported">导出脱敏 JSON</a><div id="exported" class="target-note">导出示意：导出内容必须继续脱敏。</div></div>
''')

page(
    "settings-manual.html", "Manual Settings", "manual", "Settings", "Manual / Settings", "人工模式高级设置",
    "高级设置仍不显示秘密；影响安全默认值的变化需要明确确认和审计。",
    '''
<div class="grid cols2"><div class="card"><h2>本地服务</h2><table class="table"><tr><td>discovery bind</td><td><span class="chip ok">127.0.0.1 only</span></td></tr><tr><td>WebUI bind</td><td><select><option>127.0.0.1</option><option>localhost</option></select></td></tr><tr><td>日志级别</td><td><select><option>info</option><option>debug（不脱敏禁止）</option></select></td></tr></table><a class="btn primary" href="#saved-local">保存本地设置</a><div id="saved-local" class="target-note">保存示意：不能配置成 LAN 暴露 discovery。</div></div><div class="card"><h2>安全默认值</h2><table class="table"><tr><td>grant 默认寿命</td><td><select><option>10 分钟</option><option>5 分钟</option></select></td></tr><tr><td>grant 默认次数</td><td><span class="chip">单次</span></td></tr><tr><td>raw token 兼容模式</td><td><span class="chip danger">未批准</span></td></tr></table><a class="btn danger" href="#danger-save">修改高风险默认值</a><div id="danger-save" class="target-note danger-note">高风险设置变更确认示意：真实实现需要单独确认并写审计。</div></div></div>
''')

page(
    "states.html", "状态与危险确认", "agent", "Dashboard", "Safety States", "异常状态与危险确认",
    "集中展示空、错误、reauth、policy denied、secret store 和 revoke 的设计语言。",
    '''
<div class="grid cols2">
  <div class="card"><h2>空状态</h2><div class="empty">暂无待审批申请<br><a class="btn primary" href="authorization-code.html" style="margin-top:10px;display:inline-block">生成授权码</a></div></div>
  <div class="card"><h2>policy denied</h2><div class="banner danger">agent 请求 repo-admin，但批准边界只允许自定义子集。未 mint token。</div><a class="btn" href="audit-agent.html">查看审计</a></div>
  <div class="card"><h2>secret store 错误</h2><div class="banner danger">无法解密 refresh token。不会回退到 plaintext，也不会请求 parent token。</div><a class="btn" href="manual-mode.html">去人工模式排障</a></div>
  <div class="card"><h2>revoke 确认</h2><p class="muted">区分 grant revoke 与 token revoke；grant revoke 不代表已签发 GitHub token 立即失效。</p><a class="btn danger" href="token-grants.html#revoke-token">查看 token revoke 确认</a></div>
</div>
''')

print("generated high fidelity pages")
