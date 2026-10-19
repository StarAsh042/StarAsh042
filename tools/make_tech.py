#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成 assets/tech.svg —— 技术栈面板（纯 SVG 点阵，不依赖 shields / 任何图标库）。

为什么要自建：
  shields 的图标来自 simple-icons，而 Photoshop / 3ds Max / ZBrush / Substance /
  Marmoset / ComfyUI / Stable Diffusion 这些**根本没有图标**（实测全部返回 434B 空图标）。
  混着用就会出现「有的有图标、有的没有」的参差感 —— 那正是这一版要解决的问题。

设计：
  · 全局 6px 点阵网格，与横幅同一套语言（那 1px 缝就是液晶格子线）
  · 版式是「规格表」：左侧固定一列分组名，右侧排条目 —— 左对齐，行宽天然不齐也不乱
  · 每个条目 = 一个方框，**全称直接写在框里**（不再用 2 字母缩写 + 下方名称：
    缩写和全称重复，既占地方又显得信息量低）
  · 配色不是 18 种品牌色，而是**按分组取横幅的四个霓虹色**：
      ENGINE 橙 / 3D·DCC 青 / CODE 绿 / AI 品红 —— 一眼能看出分区
  · 不做 logo：38px 里画不出可辨认的官方图标，硬画只会糊成一团；
    统一成「全称方框」至少保证 18 个视觉重量一致、排序配色完全可控

省体积：
  每个字模只定义一次（<defs> 里一条 path，同一行连续的格子合并成一个子路径），
  正文全部用 <use> 引用 —— 比逐格 <rect> 小一个数量级。
输出：assets/tech.svg（880 宽，1:1 显示，不缩放）
"""
import pathlib
import xml.etree.ElementTree as ET

BASE = pathlib.Path(__file__).resolve().parent
OUT = BASE.parent / "assets" / "tech.svg"

W = 880
PAD = 18
LBLW = 80                  # 左侧分组名列宽
CHIP_H = 28                # 条目方框高度
CHIP_PAD = 8               # 方框内左右留白
SLOT_GAP = 8               # 条目间距
NAME_PX = 2                # 文字点阵（1 字 = 10×14）
CELL = 0.7                 # 字模内每格边长（1-0.7=0.3 的缝就是液晶格线）

BG, BORDER = "#060b09", "#16241f"
TILE_BG, TILE_EDGE = "#0e1c18", "#22362e"
NAME_COL = "#a6c0b6"

GROUPS = (
    ("ENGINE", "#ffa23c", ("UNREAL ENGINE",)),
    ("3D·DCC", "#38d6ff", ("BLENDER", "MAYA", "3DS MAX", "ZBRUSH",
                           "SUBSTANCE", "MARMOSET", "PHOTOSHOP")),
    ("CODE", "#25e07f", ("PYTHON", "C++", "C#", "RUST", "JAVASCRIPT",
                         "GIT", "GITHUB")),
    ("AI", "#ff4fd8", ("COMFYUI", "STABLE DIFFUSION", "DEEPSEEK")),
)

FONT = {
    "A": ["01110", "10001", "10001", "11111", "10001", "10001", "10001"],
    "B": ["11110", "10001", "10001", "11110", "10001", "10001", "11110"],
    "C": ["01111", "10000", "10000", "10000", "10000", "10000", "01111"],
    "D": ["11110", "10001", "10001", "10001", "10001", "10001", "11110"],
    "E": ["11111", "10000", "10000", "11110", "10000", "10000", "11111"],
    "F": ["11111", "10000", "10000", "11110", "10000", "10000", "10000"],
    "G": ["01111", "10000", "10000", "10111", "10001", "10001", "01110"],
    "H": ["10001", "10001", "10001", "11111", "10001", "10001", "10001"],
    "I": ["11111", "00100", "00100", "00100", "00100", "00100", "11111"],
    "J": ["00111", "00010", "00010", "00010", "00010", "10010", "01100"],
    "K": ["10001", "10010", "10100", "11000", "10100", "10010", "10001"],
    "L": ["10000", "10000", "10000", "10000", "10000", "10000", "11111"],
    "M": ["10001", "11011", "10101", "10101", "10001", "10001", "10001"],
    "N": ["10001", "11001", "10101", "10011", "10001", "10001", "10001"],
    "O": ["01110", "10001", "10001", "10001", "10001", "10001", "01110"],
    "P": ["11110", "10001", "10001", "11110", "10000", "10000", "10000"],
    "Q": ["01110", "10001", "10001", "10001", "10101", "10010", "01101"],
    "R": ["11110", "10001", "10001", "11110", "10100", "10010", "10001"],
    "S": ["01111", "10000", "10000", "01110", "00001", "00001", "11110"],
    "T": ["11111", "00100", "00100", "00100", "00100", "00100", "00100"],
    "U": ["10001", "10001", "10001", "10001", "10001", "10001", "01110"],
    "V": ["10001", "10001", "10001", "10001", "10001", "01010", "00100"],
    "W": ["10001", "10001", "10001", "10101", "10101", "11011", "10001"],
    "X": ["10001", "10001", "01010", "00100", "01010", "10001", "10001"],
    "Y": ["10001", "10001", "01010", "00100", "00100", "00100", "00100"],
    "Z": ["11111", "00001", "00010", "00100", "01000", "10000", "11111"],
    "0": ["01110", "10001", "10011", "10101", "11001", "10001", "01110"],
    "1": ["00100", "01100", "00100", "00100", "00100", "00100", "01110"],
    "2": ["01110", "10001", "00001", "00010", "00100", "01000", "11111"],
    "3": ["01110", "10001", "00001", "00110", "00001", "10001", "01110"],
    "4": ["00010", "00110", "01010", "10010", "11111", "00010", "00010"],
    "5": ["11111", "10000", "10000", "11110", "00001", "00001", "11110"],
    "6": ["01110", "10000", "10000", "11110", "10001", "10001", "01110"],
    "7": ["11111", "00001", "00010", "00100", "01000", "01000", "01000"],
    "8": ["01110", "10001", "10001", "01110", "10001", "10001", "01110"],
    "9": ["01110", "10001", "10001", "01111", "00001", "00001", "01110"],
    "+": ["00000", "00100", "00100", "11111", "00100", "00100", "00000"],
    "#": ["01010", "01010", "11111", "01010", "11111", "01010", "01010"],
    "·": ["00000", "00000", "01100", "01100", "00000", "00000", "00000"],
    " ": ["00000"] * 7,
}


def gid(ch):
    """字模 id：用码点，避免 A/B 之类与别的 id 撞名。"""
    return f"c{ord(ch):x}"


def glyph_path(pattern):
    """一个字的 path。同一行里连续的格子合并成一条子路径（体积能省掉一大半）。"""
    d = []
    for r, line in enumerate(pattern):
        c = 0
        while c < len(line):
            if line[c] != "1":
                c += 1
                continue
            start = c
            while c < len(line) and line[c] == "1":
                c += 1
            d.append(f"M{start} {r}h{c - start}v1h-{c - start}z")
    return "".join(d)


def tw(text, px):
    """文本宽度：每字 5 格 + 1 格字距（末字不加字距）。"""
    return (len(text) * 6 - 1) * px


def text_run(text, x, y, px):
    """一段文字：外层 <g> 负责平移+缩放，内部每个字只是一个 <use>。"""
    uses = "".join(f'<use xlink:href="#{gid(ch)}" href="#{gid(ch)}" x="{i * 6}"/>'
                   for i, ch in enumerate(text.upper()))
    return f'<g transform="translate({x:.1f} {y:.1f}) scale({px})">{uses}</g>'


def build():
    defs = "".join(f'<path id="{gid(ch)}" d="{glyph_path(p)}"/>'
                   for ch, p in FONT.items())
    rows, y = [], PAD
    for gname, accent, items in GROUPS:
        # 左侧分组名，与方框垂直居中
        rows.append(f'<g fill="{accent}" opacity="0.72">'
                    f'{text_run(gname, PAD, y + (CHIP_H - 7 * NAME_PX) / 2, NAME_PX)}</g>')
        x = PAD + LBLW
        for label in items:
            w = tw(label, NAME_PX) + CHIP_PAD * 2
            rows.append(
                f'<rect x="{x:.1f}" y="{y}" width="{w:.1f}" height="{CHIP_H}" rx="1" '
                f'fill="{TILE_BG}" stroke="{TILE_EDGE}" stroke-width="1"/>'
                # 左侧 2px 强调条：颜色只在这里出现，文字保持统一浅色，18 个框才不花
                f'<rect x="{x + 1:.1f}" y="{y + 1}" width="2" height="{CHIP_H - 2}" '
                f'fill="{accent}" opacity="0.85"/>'
                f'<g fill="{NAME_COL}">'
                f'{text_run(label, x + CHIP_PAD + 3, y + (CHIP_H - 7 * NAME_PX) / 2, NAME_PX)}</g>')
            x += w + SLOT_GAP
        assert x - SLOT_GAP <= W - PAD, f"{gname} 行超宽：{x:.0f} > {W - PAD}"
        y += CHIP_H + 12
    h = int(y - 12 + PAD)
    body = (f'<rect width="{W}" height="{h}" fill="{BG}"/>'
            f'<rect width="{W}" height="{h}" fill="url(#grid)"/>'
            f'<rect x="0.5" y="0.5" width="{W - 1}" height="{h - 1}" fill="none" '
            f'stroke="{BORDER}" stroke-width="1"/>' + "".join(rows))
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" '
           f'xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 0 {W} {h}" '
           f'width="{W}" height="{h}" role="img" aria-label="Tech stack — '
           f'Unreal Engine, Blender, Maya, 3ds Max, ZBrush, Substance, Marmoset, '
           f'Photoshop, Python, C++, C#, Rust, JavaScript, Git, GitHub, ComfyUI, '
           f'Stable Diffusion, DeepSeek">'
           f'<defs>{defs}'
           f'<pattern id="grid" width="6" height="6" patternUnits="userSpaceOnUse">'
           f'<path d="M0 0 H6" stroke="#000" stroke-width="1" opacity="0.22"/>'
           f'<path d="M0 0 V6" stroke="#000" stroke-width="1" opacity="0.12"/>'
           f'</pattern></defs>{body}</svg>')
    return svg, h


if __name__ == "__main__":
    content, h = build()
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(content, encoding="utf-8")
    ET.fromstring(content)                       # XML 合法性自检
    print(f"OK  {OUT}  {W}×{h}  ({len(content)} bytes)")
