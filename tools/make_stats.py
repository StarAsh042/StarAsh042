#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成 CRT 风格的自建统计卡 assets/stats.svg —— 不依赖任何第三方图床。

数据来自 GitHub REST API：
  · /users/{u}                      → 仓库数 / 关注者
  · /users/{u}/repos                → 星标 / fork / 语言分布
  · /search/commits?q=author:{u}    → 提交总数
  · /search/issues?q=type:pr+author:{u} → PR 总数
  · /repos/{u}/{u}/traffic/views    → 近 14 天访问（需要 repo 权限）

GITHUB_TOKEN 由 Actions 注入；本地运行则回退到 `gh auth token`。
复用 make_banners.py 里的点阵字库、CRT 轮廓与数字雨，保证和横幅是同一套视觉语言。
"""
import json
import os
import pathlib
import random
import shutil
import subprocess
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from collections import Counter

import make_banners as B

OWNER = "StarAsh042"
PROFILE_REPO = "StarAsh042"
ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "assets" / "stats.svg"

# 860：GitHub Profile 内容区实测宽度 —— 按原生尺寸出图，浏览器就不再缩放 6px 点阵
W, H = 860, 280
NV_PX = 5                  # 指标数字的点阵边长（六列并排，比四列时要更克制）
# 雨的三层结构借自横幅（远暗近亮、远快近慢），但整组增益压低一档：
# 横幅里雨和大标题抢画面，这里满屏都是数据，雨必须退到背景层，
# 否则「410」「109」这种多位数字会被雨的数字打断，读不出来。
RAIN_LAYERS = (
    ("far",  0.30, 1.60, 30, 9, 66, 10),
    ("mid",  0.42, 1.05, 36, 8, 60, 40),
    ("near", 0.54, 0.72, 42, 6, 92, 64),
)


def token():
    t = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if t:
        return t.strip()
    exe = shutil.which("gh")
    if exe:
        return subprocess.run([exe, "auth", "token"],
                              capture_output=True, text=True).stdout.strip()
    raise SystemExit("没有 GITHUB_TOKEN，也找不到 gh CLI")


TOKEN = token()


def api(path, accept="application/vnd.github+json"):
    r = urllib.request.Request("https://api.github.com" + path)
    r.add_header("Authorization", "Bearer " + TOKEN)
    r.add_header("Accept", accept)
    r.add_header("User-Agent", "workbuddy-ai")
    with urllib.request.urlopen(r, timeout=60) as resp:
        return json.loads(resp.read().decode("utf-8"))


def collect():
    u = api(f"/users/{OWNER}")
    repos = api(f"/users/{OWNER}/repos?per_page=100&sort=updated")
    stars = sum(r["stargazers_count"] for r in repos)
    forks = sum(r["forks_count"] for r in repos)
    langs = Counter(r["language"] for r in repos if r.get("language"))
    try:
        views = api(f"/repos/{OWNER}/{PROFILE_REPO}/traffic/views")["count"]
    except Exception:
        views = None
    try:
        commits = api(f"/search/commits?q=author:{OWNER}",
                      accept="application/vnd.github.cloak-preview+json")["total_count"]
    except Exception:
        commits = None
    try:
        q = urllib.parse.quote(f"type:pr author:{OWNER}")
        prs = api(f"/search/issues?q={q}")["total_count"]
    except Exception:
        prs = None
    return {
        "repos": u["public_repos"], "followers": u["followers"],
        "stars": stars, "forks": forks, "views": views, "commits": commits,
        "prs": prs,
        "langs": langs.most_common(),
    }


# ── 绘图小工具 ─────────────────────────────────────────────────────
def px_text(text, px, cx, baseline):
    """点阵数字，水平居中。"""
    _, tw = B.pixel_chars(text, px, 0, 0)
    rects = "".join(B.pixel_chars(text, px, cx - tw / 2, baseline - 7 * px)[0])
    return f'<g fill="url(#num)">{rects}</g>'


def mono(x, y, s, size, anchor="start", fill=None, ls=0):
    f = fill or B.LD_COLOR
    a = f' text-anchor="{anchor}"' if anchor != "start" else ""
    l = f' letter-spacing="{ls}"' if ls else ""
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-family="{B.MONO}" '
            f'font-size="{size}" fill="{f}"{a}{l}>{s}</text>')


def build(d):
    rng = random.Random(42)
    # 六项指标：(标签, 数值)。列距由宽度反推，加指标时不用手调坐标。
    metrics = [
        ("REPOS", d["repos"]), ("STARS", d["stars"]), ("COMMITS", d["commits"]),
        ("PRS", d["prs"]), ("FOLLOWERS", d["followers"]),
        ("VIEWS / 14D", d["views"]),
    ]
    langs = d["langs"] or [("Python", 1)]
    ltotal = sum(n for _, n in langs) or 1
    MX = 80.0                      # 左右安全边

    body = [
        f'<rect width="{W}" height="{H}" fill="#000000"/>',
        '<g clip-path="url(#screen)">',
        f'<rect width="{W}" height="{H}" fill="url(#bg)"/>',
        f'<rect width="{W}" height="{H}" fill="url(#cells)"/>',
        B.rain(rng, W, H, RAIN_LAYERS),
        mono(W / 2, 40, f"{OWNER}  &#183;  SYSTEM STATUS", 15,
             anchor="middle", ls=4),
    ]
    # 指标：首尾各留 MX，其余等分
    pitch = (W - 2 * MX) / (len(metrics) - 1)
    for i, (label, val) in enumerate(metrics):
        cx = MX + i * pitch
        txt = "&#8212;" if val is None else str(val)
        body.append(px_text(txt, NV_PX, cx, 132))
        body.append(mono(cx, 164, label, 12, anchor="middle", ls=1.5))
    # 分隔线
    body.append(f'<rect x="{MX:.0f}" y="184" width="{W - 2 * MX:.0f}" height="2" '
                f'fill="url(#edge)"/>')
    # 语言条：宽度一窄就放不下右侧图例了，图例改到条形正下方居中
    body.append(mono(MX, 214, "LANGUAGES", 12, ls=1.5))
    bx, bw = 200.0, 580.0
    body.append(f'<rect x="{bx:.0f}" y="202" width="{bw:.0f}" height="16" '
                f'fill="#0b1a12" stroke="#2a4a38" stroke-width="1"/>')
    used = 0.0
    for k, (name, cnt) in enumerate(langs[:3]):
        frac = cnt / ltotal
        body.append(f'<rect x="{bx + used * bw:.1f}" y="203" width="{frac * bw:.1f}" '
                    f'height="14" fill="{B.RAIN}" opacity="{0.74 - k * 0.24:.2f}"/>')
        used += frac
    legend = "   ".join(f"{n.upper()} {round(c / ltotal * 100)}%" for n, c in langs[:3])
    body.append(mono(W / 2, 246, legend, 12, anchor="middle"))
    body.append(f'<rect width="{W}" height="{H}" fill="url(#lcd)"/>')
    body.append(f'<rect width="{W}" height="{H}" fill="url(#vig)"/>')
    body.append("</g>")

    pair = "".join(B.glyph_group(gid, cells)
                   for gid, cells in zip(("gc", "gA", "gB"), B.glyph_split()))
    css = B.RAIN_CSS + "\n" + B.rain_css(RAIN_LAYERS, H)
    return f"""<svg xmlns="http://www.w3.org/2000/svg"
     xmlns:xlink="http://www.w3.org/1999/xlink"
     viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img"
     aria-label="{OWNER} stats">
  <style>{css}</style>
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="{B.BG0}"/><stop offset="1" stop-color="{B.BG1}"/>
    </linearGradient>
    <linearGradient id="num" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="{B.CYAN}"/><stop offset="0.45" stop-color="{B.BLUE}"/>
      <stop offset="0.72" stop-color="{B.MAGENTA}"/><stop offset="1" stop-color="{B.ORANGE}"/>
    </linearGradient>
    <linearGradient id="edge" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="{B.CYAN}" stop-opacity="0"/>
      <stop offset="0.5" stop-color="{B.MAGENTA}" stop-opacity="0.75"/>
      <stop offset="1" stop-color="{B.ORANGE}" stop-opacity="0"/>
    </linearGradient>
    <pattern id="cells" width="{B.PX}" height="{B.PX}" patternUnits="userSpaceOnUse">
      <rect x="0.5" y="0.5" width="{B.CELL}" height="{B.CELL}" fill="#5affa8" opacity="0.045"/>
    </pattern>
    <pattern id="lcd" width="{B.PX}" height="{B.PX}" patternUnits="userSpaceOnUse">
      <path d="M0 0 H{B.PX}" stroke="#000000" stroke-width="1" opacity="0.26"/>
      <path d="M0 0 V{B.PX}" stroke="#000000" stroke-width="1" opacity="0.15"/>
    </pattern>
    <radialGradient id="vig" cx="0.5" cy="0.5" r="0.78">
      <stop offset="0.35" stop-color="#000000" stop-opacity="0"/>
      <stop offset="0.72" stop-color="#000000" stop-opacity="0.28"/>
      <stop offset="1" stop-color="#000000" stop-opacity="0.72"/>
    </radialGradient>
    <clipPath id="screen"><path d="{B.screen_path(W, H, 10, 30, 24)}"/></clipPath>
    {B.rain_well(W, H, W / 2, 145, 350, 122)}
    {pair}
  </defs>
  {"".join(body)}
</svg>
"""


if __name__ == "__main__":
    data = collect()
    print("数据:", {k: v for k, v in data.items() if k != "langs"}, data["langs"])
    svg = build(data)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    # newline="\n"：仓库里存的是 LF，Windows 上默认会写成 CRLF，整份 diff 就变噪声
    OUT.write_text(svg, encoding="utf-8", newline="\n")
    ET.fromstring(svg)
    print(f"OK  {OUT}  ({len(svg)} bytes)")
