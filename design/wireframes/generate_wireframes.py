#!/usr/bin/env python3
"""Generate low-fidelity SVG wireframes for review.

The generated artifacts are intentionally grayscale and structural. They are not
visual design proposals.
"""

from __future__ import annotations

from html import escape
from pathlib import Path

OUT = Path(__file__).parent
WIDTH = 1280
HEIGHT = 820
FONT = "Microsoft YaHei, Segoe UI, Arial, sans-serif"

APPROVAL_NAV = [
    ("dashboard", "Dashboard"),
    ("approvals", "Approvals"),
    ("audit", "Audit"),
    ("settings", "Settings"),
]

MANUAL_NAV = [
    ("dashboard", "Dashboard"),
    ("apps", "GitHub Apps"),
    ("agents", "Agents"),
    ("tokens", "Token / Grants"),
    ("audit", "Audit"),
    ("settings", "Settings"),
]


class Canvas:
    def __init__(self, width: int = WIDTH, height: int = HEIGHT):
        self.width = width
        self.height = height
        self.parts: list[str] = []

    def rect(self, x, y, w, h, fill="#ffffff", stroke="#555", sw=2, rx=0, dash=False):
        dash_attr = ' stroke-dasharray="7 5"' if dash else ""
        self.parts.append(
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"{dash_attr}/>'
        )

    def line(self, x1, y1, x2, y2, stroke="#555", sw=2, dash=False):
        dash_attr = ' stroke-dasharray="7 5"' if dash else ""
        self.parts.append(
            f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{stroke}" stroke-width="{sw}"{dash_attr}/>'
        )

    def text(self, x, y, value, size=16, weight="400", fill="#222", anchor="start"):
        self.parts.append(
            f'<text x="{x}" y="{y}" font-family="{FONT}" font-size="{size}" font-weight="{weight}" fill="{fill}" text-anchor="{anchor}">{escape(value)}</text>'
        )

    def text_block(self, x, y, lines, size=15, line_height=23, fill="#333", weight="400"):
        for i, line in enumerate(lines):
            self.text(x, y + i * line_height, line, size=size, weight=weight, fill=fill)

    def save(self, name: str):
        body = "\n".join(self.parts)
        svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{self.width}" height="{self.height}" viewBox="0 0 {self.width} {self.height}">
<rect width="100%" height="100%" fill="#f4f4f4"/>
{body}
</svg>
'''
        (OUT / name).write_text(svg, encoding="utf-8", newline="\n")


def label(c: Canvas, x, y, value, fill="#eeeeee", stroke="#555", width=None):
    width = width or max(76, len(value) * 13 + 20)
    c.rect(x, y, width, 28, fill=fill, stroke=stroke, sw=1, rx=14)
    c.text(x + width / 2, y + 19, value, size=13, weight="600", anchor="middle")


def box(c: Canvas, x, y, w, h, title, lines=None, fill="#ffffff", dash=False):
    c.rect(x, y, w, h, fill=fill, stroke="#555", sw=2, rx=4, dash=dash)
    c.text(x + 16, y + 28, title, size=17, weight="700")
    if lines:
        c.text_block(x + 16, y + 56, lines, size=14, line_height=22)


def shell(c: Canvas, title: str, active: str, mode="manual", status="broker: running"):
    nav = APPROVAL_NAV if mode == "approval" else MANUAL_NAV
    c.rect(0, 0, 210, HEIGHT, fill="#e8e8e8", stroke="#555", sw=2)
    c.text(24, 42, "GH Token Broker", size=20, weight="700")
    c.text(24, 68, "localhost WebUI", size=13, fill="#555")
    c.text(24, 96, "审批模式" if mode == "approval" else "人工模式", size=13, weight="700", fill="#555")
    y = 128
    for key, name in nav:
        selected = key == active
        c.rect(14, y - 24, 182, 38, fill="#d4d4d4" if selected else "#e8e8e8", stroke="#777" if selected else "#aaa", sw=1, rx=4)
        c.text(30, y, name, size=15, weight="700" if selected else "400")
        y += 52
    c.rect(14, 704, 182, 88, fill="#f7f7f7", stroke="#777", sw=1, rx=4)
    c.text(28, 730, "本地状态", size=13, weight="700")
    c.text(28, 754, status, size=13)
    c.text(28, 776, "127.0.0.1 only", size=13)

    c.rect(210, 0, WIDTH - 210, 72, fill="#eeeeee", stroke="#555", sw=2)
    c.text(238, 44, title, size=24, weight="700")
    c.rect(850, 18, 190, 36, fill="#d4d4d4" if mode == "approval" else "#f7f7f7", stroke="#555", sw=1, rx=18)
    c.text(945, 41, "Agent 审批模式", size=13, weight="700" if mode == "approval" else "400", anchor="middle")
    c.rect(1050, 18, 150, 36, fill="#d4d4d4" if mode == "manual" else "#f7f7f7", stroke="#555", sw=1, rx=18)
    c.text(1125, 41, "人工模式", size=13, weight="700" if mode == "manual" else "400", anchor="middle")


def page_frame(name: str, title: str, active: str, mode="manual"):
    c = Canvas()
    shell(c, title, active, mode=mode)
    return c


def generate_overview():
    c = Canvas()
    c.text(40, 52, "审批优先的 WebUI 低保真流程总览", size=28, weight="700")
    c.text(40, 82, "用户新方向：少配置；agent 主动读取协议并提交权限申请，用户只生成授权码并审批。原人工模式保留为高级模式。", size=15, fill="#555")

    steps = [
        ("1. 生成授权码", ["用户在 Broker 登录", "生成一次性/短寿命 code", "把 code 交给 agent"]),
        ("2. agent 发现协议", ["读取 localhost public node", "well-known/discovery", "了解申请格式和能力"]),
        ("3. agent 提交申请", ["项目/仓库/权限 profile", "min_ttl / 用途说明", "authorization code 认证"]),
        ("4. 用户审批", ["全部批准", "部分批准/降权", "拒绝并写原因"]),
        ("5. Broker 生效", ["创建/更新 agent policy", "发放 credential/grant", "后续按 approval  mint token"]),
        ("6. 审计与撤销", ["approval inbox", "agent/token inventory", "revoke + audit"]),
    ]
    x = 40
    for idx, (title, lines) in enumerate(steps):
        box(c, x, 125, 180, 165, title, lines)
        if idx < len(steps) - 1:
            c.line(x + 180, 205, x + 205, 205)
            c.text(x + 183, 194, "→", size=24, weight="700")
        x += 205

    box(c, 40, 330, 560, 260, "审批模式（默认）", [
        "用户不需要手工编写 repo pattern/profile 组合",
        "agent 根据项目上下文主动声明需要的 GitHub 权限",
        "用户在 Approval Inbox 中按仓库批准/拒绝/降权申请",
        "批准后自动生成 agent credential、policy 和后续 grant/token 边界",
        "授权码一次性/短寿命；审批前不等于已获得 GitHub 访问能力",
    ])
    box(c, 640, 330, 560, 260, "人工模式（高级保留）", [
        "保留原 GitHub Apps / Agents / Token / Grants / Settings 管理能力",
        "用于手工修正策略、rotate/disable credential、处理异常和高级排障",
        "不作为普通用户接入 agent 的默认路径",
        "高风险操作仍需二次确认；秘密永不完整回显",
    ])
    box(c, 40, 630, 1160, 120, "待用户确认的审批模式问题", [
        "已确认：授权码默认一次性/短寿命；失败或泄露则撤销并重新生成。",
        "已确认：第一版可按仓库批准/拒绝，也可把 permission profile 降权；不开放原子权限操作。",
        "已确认：agent discovery public node 严格仅限 127.0.0.1；public 不是公网公开。",
    ], dash=True)
    c.save("00-overview-flow.svg")

def generate_dashboard():
    c = page_frame("dashboard", "Dashboard — 审批模式首页", "dashboard", mode="approval")
    label(c, 240, 96, "reauth required", fill="#dddddd", width=150)
    box(c, 240, 136, 480, 118, "需要用户行动", [
        "GitHub App `example-app`：refresh token 失效或权限变化",
        "操作：查看详情 / 显式重新授权（不会自动 device flow）",
    ], fill="#f1f1f1")
    box(c, 740, 136, 470, 118, "Broker 状态", [
        "daemon running · SQLite available · secret store available",
        "最近 refresh：成功 / 失败 / pending",
    ])

    box(c, 240, 278, 300, 170, "GitHub 授权", [
        "authorized: 1",
        "refresh_required: 0",
        "reauth_required: 1",
        " revoked/unknown: 0",
    ])
    box(c, 560, 278, 300, 170, "Agent 访问", [
        "enabled agents: n",
        "policy denied today: n",
        "high-risk profiles: disabled",
    ])
    box(c, 880, 278, 330, 170, "Token / Grant", [
        "active child tokens: n",
        "active grants: n",
        "expiring < 2h: n",
    ])

    box(c, 240, 478, 620, 250, "最近事件摘要", [
        "table: time · actor · event · result · correlation id",
        "示例事件类型：refresh_failed / policy_denied / token_revoked",
        "点击行 → Audit 页并带入 correlation filter",
        "不显示 token、secret、authorization header",
    ])
    box(c, 890, 478, 320, 250, "快速操作", [
        "查看 GitHub Apps",
        "创建 agent credential",
        "查看 active grants",
        "打开 Audit",
        "所有危险操作仍需确认",
    ])
    c.save("01-dashboard.svg")


def generate_onboarding():
    c = page_frame("onboarding", "首次配置与显式授权流程", "apps")
    box(c, 240, 108, 300, 570, "1. 空状态", [
        "尚未配置 GitHub App",
        "说明：broker 需要 App client id 才能开始授权",
        "按钮：添加 GitHub App",
        "辅助链接：如何创建测试 App",
        "",
        "错误状态：",
        "· secret store unavailable",
        "· config invalid",
    ])
    box(c, 570, 108, 300, 570, "2. App 表单", [
        "name / host / client id",
        "client secret：write-only",
        "保存后不显示完整秘密",
        "",
        "校验错误：",
        "· client id 缺失",
        "· host 不被允许",
        "· secret 格式明显错误",
    ])
    box(c, 900, 108, 300, 570, "3. Device flow", [
        "用户点击“开始授权”才启动",
        "显示 verification URI + user code",
        "pending：等待用户在 GitHub 确认",
        "success：账号/过期时间/范围摘要",
        "error：expired / access_denied / network",
        "",
        "不会在普通 token 请求中自动弹出",
    ])
    c.line(540, 390, 570, 390)
    c.line(870, 390, 900, 390)
    c.save("02-onboarding-device-flow.svg")


def generate_apps():
    c = page_frame("apps", "GitHub Apps — 授权与安装范围", "apps")
    box(c, 240, 104, 690, 250, "App / Account 列表", [
        "table columns: name · host · user · auth status · parent expiry · refresh expiry",
        "row actions: view / reauth / refresh now / mark untrusted",
        "status badges: valid / refreshing / reauth_required / revoked / unknown_error",
        "empty: 尚未配置 GitHub App → 进入 onboarding",
    ])
    box(c, 950, 104, 260, 250, "添加 App", [
        "name / host / client id",
        "client secret write-only",
        "保存后只显示 fingerprint",
    ])

    box(c, 240, 382, 590, 310, "详情 drawer（右侧或下方）", [
        "GitHub App metadata：client id、host、installations",
        "授权状态机：valid → refreshing → valid / reauth_required",
        "最近错误：machine code + human message + correlation id",
        " Installation/repository coverage 警告",
    ])
    box(c, 860, 382, 350, 310, "显式 reauth 确认", [
        "说明为何需要重新授权",
        "确认按钮：开始 device flow",
        "取消：保持 reauth_required",
        "高风险提示：旧 token 可能失效",
    ], dash=True)
    c.save("03-github-apps.svg")


def generate_agents():
    c = page_frame("agents", "Agents — credential 与访问策略", "agents")
    box(c, 240, 104, 420, 590, "Agent 列表", [
        "table: name · enabled · created · last used · credential fingerprint",
        "actions: create / rotate / disable / enable",
        "credential 只在创建时显示一次；之后不可查看",
        "empty: 引导创建第一个 agent credential",
    ])
    box(c, 690, 104, 520, 280, "策略编辑", [
        "host / owner / repo pattern / permission profile / min_ttl / rate limit",
        "profile examples: read-only · pr-write · high-risk disabled",
        "保存前校验：repo pattern、profile、min_ttl、host allowlist",
    ])
    box(c, 690, 414, 520, 280, "高风险权限确认", [
        "workflow write / administration / secrets 默认禁用",
        "启用时显示显著警告和二次确认",
        "建议确认文案说明可造成的 GitHub 影响",
        "是否要求输入仓库名：待低保真评审确认",
    ], dash=True)
    c.save("04-agents-policies.svg")


def generate_tokens():
    c = page_frame("tokens", "Token Issues 与 Grants", "tokens")
    box(c, 240, 104, 970, 300, "Token Issues inventory", [
        "table: issue id · agent · repo · profile · fingerprint/last-eight · expires · status",
        "filters: active / expired / revoked / agent / repo",
        "actions: check validity / revoke / view audit",
        "不显示完整 token；撤销操作需要确认",
    ])
    box(c, 240, 432, 560, 260, "Grants", [
        "table: grant id prefix · agent · repo/profile · expires · uses · status",
        "states: active / redeemed / expired / revoked",
        "grant id 不是 GitHub token；默认单次使用",
    ])
    box(c, 830, 432, 380, 260, "Revoke 确认 modal", [
        "显示 issue metadata 和 fingerprint/last-eight",
        "说明撤销后使用该 token 的 git/gh 操作会失败",
        "按钮：确认撤销 / 取消",
        "pending / success / failure 都在原页反馈",
    ], dash=True)
    c.save("05-token-issues-grants.svg")


def generate_audit():
    c = page_frame("audit", "Audit — 授权、发放、撤销追踪", "audit")
    box(c, 240, 104, 970, 120, "Filters", [
        "time range · actor/agent · event type · repo · result · correlation id",
        "quick filters: failures only · reauth · high-risk admin actions",
    ])
    box(c, 240, 254, 650, 440, "事件列表", [
        "table: timestamp · actor · event · repo/profile · result · error code",
        "分页或无限滚动；加载时 skeleton rows",
        "empty: 当前筛选无审计事件",
        "error: audit store unavailable / corrupted query",
    ])
    box(c, 920, 254, 290, 440, "详情 drawer", [
        "完整 event metadata",
        "correlation id 可复制",
        "secret fingerprint / last-eight only",
        "details_json 脱敏展示",
        "链接：相关 token issue / grant / agent",
    ])
    c.save("06-audit.svg")


def generate_settings():
    c = page_frame("settings", "Settings — 安全与本地运行", "settings")
    box(c, 240, 104, 450, 285, "本地服务", [
        "bind: 127.0.0.1",
        "port / startup mode",
        "single instance status",
        "SQLite path（非秘密）",
    ])
    box(c, 720, 104, 490, 285, "Secret store", [
        "backend: encrypted SQLite + WCM master key",
        "status: available / unavailable / key version",
        "操作：test access / rotate master key（未来）",
        "不显示 master key 或任何秘密",
    ])
    box(c, 240, 420, 450, 275, "Token 策略默认值", [
        "default min_ttl: 2h",
        "safety margin",
        "raw token output: disabled",
        "若启用 raw token：高级模式 + 明显警告 + 审计",
    ])
    box(c, 720, 420, 490, 275, "备份与恢复", [
        "备份说明：SQLite 密文/元数据可以备份；master key 不随备份",
        "恢复状态预览：missing key → reauth_required",
        "日志级别 / 日志脱敏状态",
    ])
    c.save("07-settings-security.svg")


def generate_states():
    c = Canvas()
    c.text(40, 52, "状态与错误低保真集合", size=28, weight="700")
    c.text(40, 82, "每个页面复用这些状态骨架；错误包含 code + message + correlation id，不包含秘密。", size=15, fill="#555")

    items = [
        ("Empty", ["插画占位：空框", "标题：还没有数据", "下一步按钮/说明"]),
        ("Loading", ["skeleton table rows", "按钮 disabled", "防止重复点击"]),
        ("Network error", ["code: github_unreachable", "message + retry", "correlation id"]),
        ("Reauth required", ["code: reauth_required", "显式 reauth 按钮", "不自动 device flow"]),
        ("Policy denied", ["code: policy_denied", "说明哪个 profile/repo 被拒", "不泄露 credential"]),
        ("Secret store error", ["code: secret_store_unavailable", "恢复建议", "不显示 key/material"]),
        ("Host/Origin rejected", ["localhost 安全错误页", "无 CORS/拒绝跨站", "说明如何正确访问"]),
        ("High-risk confirm", ["危险操作标题", "后果说明", "确认/取消 + pending"]),
    ]
    positions = [(40, 120), (360, 120), (680, 120), (1000, 120), (40, 440), (360, 440), (680, 440), (1000, 440)]
    for (title, lines), (x, y) in zip(items, positions):
        box(c, x, y, 280, 260, title, lines, dash=title in {"High-risk confirm", "Reauth required"})
    c.save("08-states-errors.svg")


def generate_approval_inbox():
    c = page_frame("approvals", "Approvals — agent 权限申请审批", "approvals", mode="approval")
    label(c, 240, 96, "审批模式 · 默认", fill="#dddddd", width=150)
    box(c, 240, 136, 300, 250, "生成 agent 授权码", [
        "按钮：生成授权码",
        "展示：一次性 code + 过期时间",
        "code 只显示一次；可 revoke/regenerate",
        "可选备注：给哪个 agent/项目使用",
        "边界：code 泄露可重新撤销；审批前无 GitHub 权限",
    ])
    box(c, 560, 136, 650, 250, "待审批申请列表", [
        "table: agent/project · repo · requested profile · min_ttl · reason · expires",
        "status: pending / partially approved / approved / rejected / expired",
        "empty: 当前没有待审批申请",
        "点击行 → 右侧审批详情",
    ])

    box(c, 240, 416, 570, 310, "申请详情", [
        "agent 自称：name/version/project path（需显示为未验证声明）",
        "请求范围：host / owner / repo / permission profile / min_ttl",
        "用途说明：例如 read issues、create PR、push branch",
        "风险提示：requested profile 是否包含 write/high-risk；多仓库高权限批量申请需突出警告",
        "broker 校验结果：repo 存在性、App installation coverage、policy冲突",
    ])
    box(c, 840, 416, 370, 310, "审批操作", [
        "Approve all：接受全部申请",
        "Partial approve：按仓库勾选/取消，也可降权 profile；不编辑原子权限",
        "Reject：填写可选原因并通知 agent",
        "确认页显示最终生效差异，不显示完整 credential",
        "所有结果写 audit；pending 防重复点击",
    ])
    c.save("09-approval-inbox.svg")


def generate_agent_code_flow():
    c = Canvas()
    c.text(40, 52, "Agent 授权码与协议发现流程", size=28, weight="700")
    c.text(40, 82, "这是 agent-facing 流程，不是复杂人工配置页。public node 指无需凭证可读的 localhost 协议元数据，不是公网服务。", size=15, fill="#555")
    lanes=[("用户 / Owner",40),("Agent",460),("GH Token Broker",880)]
    for title,x in lanes:
        c.rect(x,120,360,620,fill="#f8f8f8",stroke="#555",sw=2,rx=4)
        c.text(x+180,150,title,size=18,weight="700",anchor="middle")
    def step(x,y,w,text):
        c.rect(x,y,w,58,fill="#ffffff",stroke="#777",sw=1,rx=4)
        c.text_block(x+12,y+22,text,size=13,line_height=18)
    step(60,190,320,["1. 登录本地 Broker","生成一次性授权码"])
    step(480,220,320,["2. 用户把授权码交给 agent","例如粘贴到 agent 配置/命令"])
    step(480,310,320,["3. 读取 discovery","GET /.well-known/gh-token-broker"])
    step(900,310,280,["返回公开协议元数据","api version/endpoints/capabilities"])
    step(480,410,320,["4. 用授权码提交申请","项目、仓库、profile、min_ttl、原因"])
    step(900,430,280,["校验授权码","创建 pending approval"])
    step(60,520,320,["5. 用户审批","全部 / 部分 / 拒绝"])
    step(900,590,280,["批准后生效","创建 credential/policy/grant 边界"])
    step(480,650,320,["6. agent 后续按协议请求 token","不再要求用户手工配置 policy"])
    for x1,y1,x2,y2 in [(380,220,480,240),(640,280,640,310),(800,340,900,340),(800,440,900,460),(900,610,380,550),(900,650,800,680)]:
        c.line(x1,y1,x2,y2)
    c.save("10-agent-code-flow.svg")


def generate_partial_approval():
    c = page_frame("approvals", "Partial Approval — 部分批准与降权", "approvals", mode="approval")
    box(c, 240, 108, 440, 570, "agent 原始申请", [
        "project: repo-maintainer",
        "repositories:",
        "· owner/repo-a — pr-write — reason: create fix PR",
        "· owner/repo-b — read-only — reason: inspect issues",
        "· owner/repo-c — admin — reason: manage settings",
        "min_ttl: 2h",
        "agent 声明用途文本（不可作为安全证明）",
    ])
    box(c, 710, 108, 500, 570, "用户可调整的批准结果", [
        "[x] owner/repo-a · pr-write · 批准",
        "[x] owner/repo-b · read-only · 批准",
        "[ ] owner/repo-c · admin · 拒绝",
        "",
        "可选降权：pr-write → read-only / issue-read",
        "可按仓库逐项决定批准、降权或拒绝",
        "不开放 GitHub 原子权限勾选；高风险仓库默认不勾选",
        "",
        "最终确认：显示批准/拒绝差异",
        "结果写 audit；agent 收到机器可读结果",
    ])
    c.line(680,390,710,390)
    c.text(684,378,"→",size=24,weight="700")
    c.save("11-partial-approval.svg")


def generate_index():
    pages = [
        ("00-overview-flow.svg", "页面与核心流程总览"),
        ("01-dashboard.svg", "Dashboard"),
        ("02-onboarding-device-flow.svg", "首次配置与 Device Flow"),
        ("03-github-apps.svg", "GitHub Apps"),
        ("04-agents-policies.svg", "Agents 与策略"),
        ("05-token-issues-grants.svg", "Token Issues 与 Grants"),
        ("06-audit.svg", "Audit"),
        ("07-settings-security.svg", "Settings / Security"),
        ("08-states-errors.svg", "状态与错误集合"),
        ("09-approval-inbox.svg", "Approvals：agent 权限申请审批"),
        ("10-agent-code-flow.svg", "Agent 授权码与协议发现流程"),
        ("11-partial-approval.svg", "Partial Approval：部分批准与降权"),
    ]
    cards = []
    for href, title in pages:
        cards.append(f'''      <section class="card">
        <h2>{escape(title)}</h2>
        <a href="{href}"><img src="{href}" alt="{escape(title)}"></a>
        <p><a href="{href}">打开 SVG</a></p>
      </section>''')
    html = f'''<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>GH Token Broker WebUI 低保真 Wireframes</title>
  <style>
    body {{ margin: 0; padding: 32px; font-family: "Microsoft YaHei", "Segoe UI", sans-serif; background: #f5f5f5; color: #222; }}
    header {{ max-width: 1100px; margin: 0 auto 28px; }}
    h1 {{ margin: 0 0 8px; }}
    .note {{ background: #fff; border: 1px solid #999; padding: 16px; max-width: 1100px; margin: 0 auto 24px; }}
    main {{ max-width: 1100px; margin: 0 auto; }}
    .card {{ background: #fff; border: 1px solid #999; margin: 0 0 28px; padding: 16px; }}
    .card h2 {{ margin: 0 0 12px; font-size: 20px; }}
    img {{ display: block; width: 100%; height: auto; border: 1px solid #aaa; background: #eee; }}
  </style>
</head>
<body>
  <header>
    <h1>GH Token Broker WebUI 低保真 Wireframes</h1>
    <p>版本：draft 0.1 · 2026-11-27 · 仅用于功能、页面、流程和状态评审</p>
  </header>
  <div class="note">
    <strong>评审说明：</strong>这些图刻意使用灰度、粗边框和占位内容，不代表最终视觉设计。请重点确认页面是否完整、入口是否可达、流程是否闭环、空/加载/错误/危险确认状态是否覆盖。
    <p><strong>不理解页面或后端 POC 时，请先打开：</strong><a href="walkthrough.html">低保真与后端 POC 决策讲解 Demo</a>。它逐项解释页面区域、设计理由、边界情况和接受/拒绝 POC 的差异。</p>
  </div>
  <main>
{chr(10).join(cards)}
  </main>
</body>
</html>
'''
    (OUT / "index.html").write_text(html, encoding="utf-8", newline="\n")


def main():
    generate_overview()
    generate_dashboard()
    generate_onboarding()
    generate_apps()
    generate_agents()
    generate_tokens()
    generate_audit()
    generate_settings()
    generate_states()
    generate_approval_inbox()
    generate_agent_code_flow()
    generate_partial_approval()
    generate_index()
    print(f"generated wireframes in {OUT}")


if __name__ == "__main__":
    main()
