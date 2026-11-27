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
  <a class="card linkcard" href="partial-approval.html"><h2>细粒度部分批准</h2><p class="muted">在申请权限组上限内逐项降低 GitHub 原子权限。</p><span class="chip warn">重点评审</span></a>
  <a class="card linkcard" href="states.html"><h2>异常与危险确认</h2><p class="muted">reauth、policy denied、secret store、revoke 等安全状态。</p><span class="chip danger">安全状态</span></a>
</div>
<div class="card" style="margin-top:16px"><h2>本轮修正的完整性要求</h2><div class="grid cols3 small"><div>✓ Dashboard 可点击</div><div>✓ 生成授权码有独立页面</div><div>✓ 审计/重新授权有目标页面</div><div>✓ Settings 不再缺失</div><div>✓ GitHub Apps / Agents / Token / Grants / Audit 均有页面</div><div>✓ 人工模式侧栏不再跳回 Agent 模式</div></div></div>
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
<div class="card" style="margin-top:16px"><div class="between"><h2>最近事件</h2><a class="btn ghost" href="audit-agent.html">查看全部审计</a></div><table class="table"><tr><th>时间</th><th>事件</th><th>对象</th><th>结果</th></tr><tr><td>10:42</td><td>permission application</td><td>devin / repo-a</td><td><span class="chip warn">pending</span></td></tr><tr><td>10:17</td><td>grant redeemed</td><td>repo-b</td><td><span class="chip ok">success</span></td></tr><tr><td>09:58</td><td>refresh failed</td><td>github.com/octo</td><td><a class="chip danger" href="reauth.html">需要重新授权</a></td></tr></table></div>
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
    <a class="item sel" href="#detail"><div class="between"><b>Devin Coding Agent</b><span class="chip danger">批量高风险</span></div><div class="muted small">3 repos · repo-admin · 2h</div></a>
    <a class="item" href="partial-approval.html"><div class="between"><b>Local CLI Agent</b><span class="chip warn">部分降权建议</span></div><div class="muted small">1 repo · pr-write · 1h</div></a>
    <a class="item" href="#detail"><div class="between"><b>Research Bot</b><span class="chip ok">低权限</span></div><div class="muted small">1 repo · read-only · 30m</div></a>
  </div>
  <div class="card" id="detail"><div class="between"><h2>Devin Coding Agent</h2><span class="chip danger">repo-admin</span></div><div class="banner danger">一次申请 3 个仓库的 repo-admin。高风险权限默认未勾选，必须逐仓库确认或降级。</div><table class="table"><tr><th>仓库</th><th>申请 profile</th><th>min_ttl</th><th>建议</th></tr><tr><td>octo/repo-a</td><td>repo-admin</td><td>2h</td><td><a href="partial-approval.html" class="chip warn">细粒度调整</a></td></tr><tr><td>octo/repo-b</td><td>repo-admin</td><td>2h</td><td><span class="chip danger">默认拒绝</span></td></tr><tr><td>octo/repo-c</td><td>repo-admin</td><td>2h</td><td><span class="chip warn">需确认</span></td></tr></table><h3>agent 自述用途（未验证）</h3><p class="muted">“需要创建分支、推送提交并打开 PR。”该说法不是安全事实。</p><div class="row wrap"><a class="btn primary" href="partial-approval.html">进入部分批准/降权</a><a class="btn" href="#approved">全部批准</a><a class="btn danger" href="#rejected">拒绝申请</a></div><div id="approved" class="target-note danger-note">全部批准确认示意：真实 UI 会要求再次确认高风险权限。</div><div id="rejected" class="target-note danger-note">拒绝确认示意：拒绝会返回机器可读结果并写审计。</div></div>
</div>
''')

page(
    "partial-approval.html", "部分批准与细粒度授权", "agent", "Approvals", "Partial Approval", "部分批准与细粒度授权",
    "用户可以在 agent 申请的权限组上限内逐项降低权限；不能扩展到申请之外的权限。",
    '''
<div class="banner danger">申请 profile：repo-admin。页面展示该 profile 覆盖的权限上限；你只能在这个上限内降低或关闭权限，不能新增 repo-admin 未包含的权限。</div>
<div class="grid cols2" style="margin-top:16px">
  <div class="card"><h2>仓库决定</h2><table class="table"><tr><th>仓库</th><th>决定</th><th>最终范围</th></tr><tr><td>octo/repo-a</td><td><select><option>批准后细粒度调整</option><option>拒绝</option></select></td><td>自定义子集</td></tr><tr><td>octo/repo-b</td><td><select><option>拒绝</option><option>批准并调整</option></select></td><td>无权限</td></tr><tr><td>octo/repo-c</td><td><select><option>批准后细粒度调整</option><option>拒绝</option></select></td><td>自定义子集</td></tr></table></div>
  <div class="card emph"><h2>权限上限内的细粒度调整</h2><p class="muted small">勾选状态可点击，用于评审交互；静态稿不会保存。</p><div class="permgrid"><div class="permhead">GitHub 权限</div><div class="permhead">申请上限</div><div class="permhead">最终授予</div><div>Contents</div><div>write</div><select><option selected>write</option><option>read</option><option>none</option></select><div>Pull requests</div><div>write</div><select><option selected>write</option><option>read</option><option>none</option></select><div>Issues</div><div>write</div><select><option selected>write</option><option>read</option><option>none</option></select><div>Actions</div><div>write</div><select><option>write</option><option>read</option><option selected>none</option></select><div>Administration</div><div>write</div><select><option>write</option><option>read</option><option selected>none（高风险默认关闭）</option></select><div>Environments</div><div class="muted">不在申请组内</div><select disabled><option>不可选择</option></select></div>
  <div class="diff" style="margin-top:14px"><div class="item"><b>申请</b><div class="muted small">repo-admin 全量</div></div><div class="arrow">→</div><div class="item"><b>最终</b><div class="muted small">contents/pr/issues write；actions/administration none</div></div></div></div>
</div>
<div class="card" style="margin-top:16px"><h2>确认最终授权</h2><p class="muted">确认前必须展示最终差异。真实实现可要求输入授权仓库数量或勾选高风险确认。</p><div class="row wrap"><a class="btn primary" href="#confirmed">确认 2 个仓库的自定义授权</a><a class="btn" href="approval-inbox.html">返回 inbox</a><a class="btn danger" href="#reject-all">全部拒绝</a></div><div id="confirmed" class="target-note">确认示意：最终授权只包含上限内被勾选的权限，决定会写审计。</div><div id="reject-all" class="target-note danger-note">全部拒绝示意：不会创建 agent credential 或 grant。</div></div>
''')

page(
    "audit-agent.html", "Audit", "agent", "Audit", "Audit Log", "审计记录",
    "默认模式只展示与审批、安全状态和 grant/token 生命周期相关的审计，不显示秘密。",
    '''
<div class="row wrap" style="margin-bottom:14px"><a class="btn" href="#filters">筛选</a><a class="btn" href="reauth.html">处理重新授权</a><a class="btn ghost" href="dashboard.html">返回 Dashboard</a></div>
<div class="card" id="filters"><h2>筛选条件</h2><div class="grid cols3"><select><option>全部事件</option><option>grant</option><option>reauth</option></select><select><option>全部结果</option><option>success</option><option>denied</option></select><input class="input" value="octo/repo-a"></div></div>
<div class="card" style="margin-top:16px"><h2>事件列表</h2><table class="table"><tr><th>时间</th><th>事件</th><th>对象</th><th>结果</th><th>操作</th></tr><tr><td>10:42</td><td>permission application</td><td>devin / 3 repos</td><td><span class="chip warn">pending</span></td><td><a href="approval-inbox.html">去审批</a></td></tr><tr><td>09:58</td><td>refresh failed</td><td>github.com/octo</td><td><span class="chip danger">reauth_required</span></td><td><a href="reauth.html">重新授权</a></td></tr><tr><td>09:12</td><td>policy denied</td><td>repo-c / repo-admin</td><td><span class="chip danger">denied</span></td><td><a href="#denied-detail">查看原因</a></td></tr><tr><td>08:46</td><td>token_scoped_minted</td><td>repo-a</td><td><span class="chip ok">success</span></td><td><a href="#token-detail">查看元数据</a></td></tr></table></div>
<div class="grid cols2" style="margin-top:16px"><div class="card" id="denied-detail"><h2>policy denied 详情</h2><p class="muted">repo-admin 超出该 agent 已批准 profile；未返回 token。</p></div><div class="card" id="token-detail"><h2>token issue 元数据</h2><p class="muted">只显示 issue id、hash prefix、expires_at 和权限摘要；不显示 token。</p></div></div>
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
  <div class="card"><h2>Devin Coding Agent</h2><table class="table"><tr><td>fingerprint</td><td><span class="code inline">sha256:9f2a…</span></td></tr><tr><td>状态</td><td><select><option>enabled</option><option>disabled</option></select></td></tr><tr><td>host</td><td>github.com</td></tr><tr><td>允许仓库</td><td>octo/repo-a</td></tr><tr><td>profile</td><td>custom subset</td></tr><tr><td>min_ttl</td><td>2h</td></tr></table><div class="row wrap" style="margin-top:12px"><a class="btn primary" href="#saved">保存策略</a><a class="btn" href="audit-manual.html">查看审计</a><a class="btn danger" href="#disable-agent">禁用</a></div><div id="saved" class="target-note">保存示意：不允许扩大到审批决定之外的仓库。</div><div id="disable-agent" class="target-note danger-note">禁用确认示意：后续请求失败关闭，已签发 token 仍按 expiry/inventory 处理。</div></div>
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
<div class="card" style="margin-top:16px"><table class="table"><tr><th>时间</th><th>actor</th><th>事件</th><th>subject</th><th>outcome</th><th>操作</th></tr><tr><td>10:42</td><td>user</td><td>approval_decision</td><td>application app_01</td><td><span class="chip warn">partial</span></td><td><a href="#detail-1">详情</a></td></tr><tr><td>10:45</td><td>system</td><td>token_scoped_minted</td><td>tok_a91…</td><td><span class="chip ok">success</span></td><td><a href="token-grants.html">inventory</a></td></tr><tr><td>10:47</td><td>agent</td><td>grant_redeemed</td><td>sha256:88aa…</td><td><span class="chip ok">success</span></td><td><a href="token-grants.html">grant</a></td></tr><tr><td>10:51</td><td>user</td><td>webui_admin_action</td><td>agent sha256:9f2a…</td><td><span class="chip danger">disabled</span></td><td><a href="agents-edit.html">agent</a></td></tr></table></div>
<div class="card" id="detail-1" style="margin-top:16px"><h2>审批决定详情</h2><p class="muted">repo-a/repo-c 被授予申请上限内的自定义权限子集；repo-b 被拒绝。审计 metadata 不包含 token 或 credential。</p><a class="btn" href="#exported">导出脱敏 JSON</a><div id="exported" class="target-note">导出示意：导出内容必须继续脱敏。</div></div>
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
