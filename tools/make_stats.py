#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成 CRT 风格的自建统计卡 assets/stats.svg —— 不依赖任何第三方图床。

数据来自 GitHub REST API：
  · /users/{u}                      → 仓库数 / 关注者 / 建号时间
  · /users/{u}/repos                → 星标 / fork / 语言分布
  · /search/commits?q=author:{u}    → 提交总数
  · /repos/{u}/{u}/traffic/views    → 近 14 天访问（需要 repo 权限）

GITHUB_TOKEN 由 Actions 注入；本地运行则回退到 `gh auth token`。
复用 make_banners.py 里的点阵字库与 CRT 轮廓，保证风格统一。
"""
import json
import os
import pathlib
import random
import shutil
import subprocess
import urllib.request
import xml.etree.ElementTree as ET
from collections import Counter

import make_banners as B

OWNER = "StarAsh042"
PROFILE_REPO = "StarAsh042"
ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "assets" / "stats.svg"

W, H = 1280, 280


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
    return {
        "repos": u["public_repos"], "followers": u["followers"],
        "stars": stars, "forks": forks, "views": views, "commits": commits,
        "langs": langs.most_common(),
    }


# ── 绘图小工具 ─────────────────────────────────────────────────────
def glyph_defs():
    return "".join(
        f'<g id="g{k}">' + "".join(
            f'<rect x="{c * B.PX}" y="{r * B.PX}" width="{B.CELL}" height="{B.CELL}"/>'
            for r, line in enumerate(pat) for c, ch in enumerate(line) if ch == "1"
        ) + "</g>" for k, pat in B.GLYPH3.items())


def dim_rain(rng, cols=30, rows=11):
    """静态暗数字雨，只作质感，不抢数字。"""
    out = []
    for i in range(cols):
        x = 8 + i * (W - 16) / (cols - 1)
        for j in range(rows):
            out.append(B.use_glyph(rng.choice("01"), x, -24 + j * 27, B.RAIN,
                                   round(0.05 + 0.11 * (j / rows), 3)))
    return "".join(out)


def px_text(text, px, cx, baseline):
    """点阵数字，水平居中。"""
    chars, tw = B.pixel_chars(text, px, 0, 0)
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
    # 五项指标：(标签, 数值)
    metrics = [
        ("REPOS", d["repos"]), ("STARS", d["stars"]), ("COMMITS", d["commits"]),
        ("FOLLOWERS", d["followers"]), ("VIEWS / 14D", d["views"]),
    ]
    langs = d["langs"] or [("Python", 1)]
    ltotal = sum(n for _, n in langs) or 1

    body = [
        f'<rect width="{W}" height="{H}" fill="#000000"/>',
        '<g clip-path="url(#screen)">',
        f'<rect width="{W}" height="{H}" fill="url(#bg)"/>',
        f'<rect width="{W}" height="{H}" fill="url(#cells)"/>',
        dim_rain(rng),
        mono(W / 2, 46, f"{OWNER}  &#183;  SYSTEM STATUS", 17,
             anchor="middle", ls=4),
    ]
    # 指标
    for i, (label, val) in enumerate(metrics):
        cx = 128 + i * 256
        txt = "&#8212;" if val is None else str(val)
        body.append(px_text(txt, 6, cx, 152))
        body.append(mono(cx, 186, label, 14, anchor="middle", ls=1.5))
    # 分隔线
    body.append(f'<rect x="140" y="208" width="{W - 280}" height="2" '
                f'fill="url(#edge)"/>')
    # 语言条
    body.append(mono(140, 252, "LANGUAGES", 14, ls=1.5))
    bx, bw, nblk = 330.0, 620.0, 45
    body.append(f'<rect x="{bx:.0f}" y="238" width="{bw:.0f}" height="18" '
                f'fill="#0b1a12" stroke="#2a4a38" stroke-width="1"/>')
    used = 0.0
    for k, (name, cnt) in enumerate(langs[:3]):
        frac = cnt / ltotal
        body.append(f'<rect x="{bx + used * bw:.1f}" y="239" width="{frac * bw:.1f}" '
                    f'height="16" fill="{B.RAIN}" opacity="{0.9 - k * 0.28:.2f}"/>')
        used += frac
    legend = "   ".join(f"{n.upper()} {round(c / ltotal * 100)}%" for n, c in langs[:3])
    body.append(mono(980, 252, legend, 13))
    body.append(f'<rect width="{W}" height="{H}" fill="url(#lcd)"/>')
    body.append(f'<rect width="{W}" height="{H}" fill="url(#vig)"/>')
    body.append("</g>")

    return f"""<svg xmlns="http://www.w3.org/2000/svg"
     xmlns:xlink="http://www.w3.org/1999/xlink"
     viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img"
     aria-label="{OWNER} stats">
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
    {glyph_defs()}
  </defs>
  {"".join(body)}
</svg>
"""


if __name__ == "__main__":
    data = collect()
    print("数据:", {k: v for k, v in data.items() if k != "langs"}, data["langs"])
    svg = build(data)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(svg, encoding="utf-8")
    ET.fromstring(svg)
    print(f"OK  {OUT}  ({len(svg)} bytes)")
