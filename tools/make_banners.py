#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""用代码生成 StarAsh042 的 README 横幅（纯 SVG，带动画：无位图、无 AI 生图）。

设计方向：
  · 复古液晶屏 —— 全局 6px 点阵网格；标题与数字雨全部由方块拼成（缝＝格子线）
  · 电子故障 —— 标题「逐字母」独立抽动（左右 + 上下），带霓虹辉光与青色色散
  · 显示器塌缩 —— 息屏/亮屏时整幅画面绕中心收成一条亮线 → 一个亮点，再反向展开
  · 流动 —— 数字雨下落（纵向）+ 标题渐变横向流动
输出：assets/banner-header.svg / assets/banner-footer.svg
"""
import pathlib
import random
import xml.etree.ElementTree as ET

BASE = pathlib.Path(__file__).resolve().parent
ASSETS = BASE / "assets"
ASSETS.mkdir(exist_ok=True)

FONT = ("'Segoe UI','Helvetica Neue',Helvetica,Arial,"
        "'PingFang SC','Microsoft YaHei',sans-serif")
MONO = "'Courier New',Consolas,Menlo,monospace"

CYAN, BLUE = "#38d6ff", "#5b8cff"
MAGENTA, ORANGE = "#ff4fd8", "#ffa23c"
WHITE = "#ffffff"
RAIN, RAIN_HEAD = "#25e07f", "#d8ffe9"

BG0, BG1 = "#03080a", "#07140f"
LD_COLOR = "#8dffbe"       # 终端加载条：沿用液晶绿，不用参考图的琥珀色
INFO_TEXT = "CHENGDU · SICHUAN · CHINA"
LD_BW = 72                 # 进度条字符宽度
PX = 6
CELL = PX - 1

GLYPH3 = {
    "0": ["111", "101", "101", "101", "111"],
    "1": ["010", "110", "010", "010", "111"],
}
GLYPH5 = {
    "S": ["01111", "10000", "10000", "01110", "00001", "00001", "11110"],
    "A": ["01110", "10001", "10001", "11111", "10001", "10001", "10001"],
    "C": ["01111", "10000", "10000", "10000", "10000", "10000", "01111"],
    "D": ["11110", "10001", "10001", "10001", "10001", "10001", "11110"],
    "E": ["11111", "10000", "10000", "11110", "10000", "10000", "11111"],
    "G": ["01111", "10000", "10000", "10111", "10001", "10001", "01110"],
    "H": ["10001", "10001", "10001", "11111", "10001", "10001", "10001"],
    "I": ["11111", "00100", "00100", "00100", "00100", "00100", "11111"],
    "N": ["10001", "11001", "10101", "10011", "10001", "10001", "10001"],
    "U": ["10001", "10001", "10001", "10001", "10001", "10001", "01110"],
    "·": ["00000", "00000", "01100", "01100", "00000", "00000", "00000"],
    "t": ["00100", "00100", "11111", "00100", "00100", "00100", "00011"],
    "a": ["00000", "00000", "01110", "00001", "01111", "10001", "01111"],
    "r": ["00000", "00000", "10110", "11001", "10000", "10000", "10000"],
    "s": ["00000", "00000", "01111", "10000", "01110", "00001", "11110"],
    "h": ["10000", "10000", "10110", "11001", "10001", "10001", "10001"],
    "e": ["00000", "00000", "01110", "10001", "11111", "10000", "01110"],
    "b": ["10000", "10000", "10110", "11001", "10001", "10001", "10110"],
    "o": ["00000", "00000", "01110", "10001", "10001", "10001", "01110"],
    "i": ["00100", "00000", "01100", "00100", "00100", "00100", "01110"],
    "l": ["01100", "00100", "00100", "00100", "00100", "00100", "01110"],
    "0": ["01110", "10001", "10001", "10001", "10001", "10001", "01110"],
    "1": ["00100", "01100", "00100", "00100", "00100", "00100", "01110"],
    "2": ["01110", "10001", "00001", "00010", "00100", "01000", "11111"],
    "3": ["01110", "10001", "00001", "00110", "00001", "10001", "01110"],
    "4": ["00010", "00110", "01010", "10010", "11111", "00010", "00010"],
    "5": ["11111", "10000", "10000", "11110", "00001", "00001", "11110"],
    "6": ["01110", "10000", "10000", "11110", "10001", "10001", "01110"],
    "7": ["11111", "00001", "00010", "00100", "01000", "01000", "01000"],
    "8": ["01110", "10001", "10001", "01110", "10001", "10001", "01110"],
    "9": ["01110", "10001", "10001", "01111", "00001", "00001", "01110"],
    ".": ["00000", "00000", "00000", "00000", "00000", "01100", "01100"],
    ",": ["00000", "00000", "00000", "00000", "01100", "01100", "01000"],
    " ": ["00000"] * 7,
}
PLANETS = {
    "purple": ("#8b5cf6", "#4d2694"),
    "orange": ("#ffa23c", "#b05a0c"),
}

BASE_CSS = """@keyframes rainFallH { 0% { transform:translateY(0) } 100% { transform:translateY(680px) } }
    @keyframes rainFallF { 0% { transform:translateY(0) } 100% { transform:translateY(450px) } }
    @keyframes floatY    { 0%,100% { transform:translateY(0) } 50% { transform:translateY(-7px) } }
    /* 撕裂线：闪一下就没 */
    @keyframes tear { 0%,93%,100% { opacity:0 } 94% { opacity:.75 } 95% { opacity:0 }
                     96% { opacity:.45 } 97% { opacity:0 } }
    /* ── 待机 13.85s → 息屏 0.2s → 黑屏 0.5s → 假 DOS 自检 2s → 进度条 3s → 亮屏 0.35s ── */
    /* 整轮 20s。待机（正常显示）占 13.85s，是绝对主体。 */
    @keyframes crt {
      0%,69.25% { transform: scale(1,1) }
      69.75%    { transform: scale(1,.014) }      /* 息屏 0.2s */
      70.25%    { transform: scale(.014,.014) }
      98.25%    { transform: scale(.014,.014) }
      99.13%    { transform: scale(1,.014) }      /* 亮屏 0.35s */
      100%      { transform: scale(1,1) } }
    @keyframes beamFade {
      0%,69.4% { opacity:0 } 69.7% { opacity:1 } 70.7% { opacity:0 }
      98.1% { opacity:0 } 98.5% { opacity:1 } 100% { opacity:0 } }
    @keyframes blackout {
      0%,69.9% { opacity:0 } 70.4% { opacity:1 } 98% { opacity:1 }
      98.7% { opacity:0 } 100% { opacity:0 } }
    @keyframes dosFade {
      0%,72% { opacity:0 } 72.9% { opacity:1 } 82.4% { opacity:1 }
      83.6% { opacity:0 } 100% { opacity:0 } }
    @keyframes loaderFade {
      0%,82.4% { opacity:0 } 83.4% { opacity:1 } 97.5% { opacity:1 }
      98.4% { opacity:0 } 100% { opacity:0 } }
    /* VHS 撕条：和其余故障挤在同一窗口，紧接息屏 */
    @keyframes vhs { 0%,66.2%,100% { opacity:0 } 66.5% { opacity:.55 } 67% { opacity:0 }
                    67.6% { opacity:.42 } 68.1% { opacity:0 } 68.5% { opacity:.30 } 68.8% { opacity:0 } }
    .vhsbar   { animation: vhs 20s steps(1,end) infinite; }
    .vhsbar-b { animation: vhs 20s steps(1,end) infinite; animation-delay:-.06s; }
    .vhsbar-d { animation: vhs 20s steps(1,end) infinite; animation-delay:-.12s; }
    /* 画面撕扯：同样压在 66%–69% 窗口内（13.2s–13.8s），紧接 69.25% 的息屏 */
    @keyframes tbfade { 0%,66%,69.3%,100% { opacity:0 } 66.3% { opacity:1 } 69.1% { opacity:1 } }
    @keyframes ts1 { 0%,66.1%,100% { transform:translateX(0) }
                    66.3% { transform:translateX(-30px) } 66.8% { transform:translateX(20px) }
                    67.3% { transform:translateX(0) } 68.1% { transform:translateX(-16px) }
                    68.5% { transform:translateX(0) } }
    @keyframes ts2 { 0%,66.3%,100% { transform:translateX(0) }
                    66.6% { transform:translateX(24px) } 67% { transform:translateX(-18px) }
                    67.5% { transform:translateX(0) } 68.4% { transform:translateX(13px) }
                    68.8% { transform:translateX(0) } }
    @keyframes ts3 { 0%,66.2%,100% { transform:translateX(0) }
                    66.4% { transform:translateX(-36px) } 66.9% { transform:translateX(26px) }
                    67.4% { transform:translateX(0) } 68.2% { transform:translateX(-20px) }
                    68.7% { transform:translateX(0) } }
    @keyframes ts4 { 0%,66.6%,100% { transform:translateX(0) }
                    66.9% { transform:translateX(17px) } 67.3% { transform:translateX(-25px) }
                    67.8% { transform:translateX(0) } 68.6% { transform:translateX(-18px) }
                    69% { transform:translateX(0) } }
    /* 竖向切片：上下撕扯，与横向切片同窗口 */
    @keyframes vs1 { 0%,66.2%,100% { transform:translateY(0) }
                    66.5% { transform:translateY(-22px) } 67.2% { transform:translateY(14px) }
                    67.9% { transform:translateY(0) } 68.4% { transform:translateY(-12px) }
                    68.9% { transform:translateY(0) } }
    @keyframes vs2 { 0%,66.5%,100% { transform:translateY(0) }
                    66.8% { transform:translateY(18px) } 67.5% { transform:translateY(-16px) }
                    68.2% { transform:translateY(0) } 68.7% { transform:translateY(11px) }
                    69.1% { transform:translateY(0) } }
    @keyframes vs3 { 0%,66.3%,100% { transform:translateY(0) }
                    66.6% { transform:translateY(-26px) } 67.3% { transform:translateY(12px) }
                    68% { transform:translateY(0) } 68.6% { transform:translateY(9px) }
                    69% { transform:translateY(0) } }
    @keyframes jolt { 0%,66.2%,100% { transform:translate(0,0) }
                     66.4% { transform:translate(-10px,-6px) } 66.7% { transform:translate(8px,5px) }
                     67% { transform:translate(-5px,-3px) } 67.4% { transform:translate(0,0) }
                     68.2% { transform:translate(7px,4px) } 68.5% { transform:translate(0,0) } }
    .tbf { animation: tbfade 20s steps(1,end) infinite; }
    .ts1 { animation: ts1 20s steps(1,end) infinite; }
    .ts2 { animation: ts2 20s steps(1,end) infinite; }
    .ts3 { animation: ts3 20s steps(1,end) infinite; }
    .ts4 { animation: ts4 20s steps(1,end) infinite; }
    .vs1 { animation: vs1 20s steps(1,end) infinite; }
    .vs2 { animation: vs2 20s steps(1,end) infinite; }
    .vs3 { animation: vs3 20s steps(1,end) infinite; }
    .jolt { animation: jolt 20s steps(1,end) infinite; }
    /* 底部信息行：明暗闪烁 */
    @keyframes ldflick {
      0%,100% { opacity:1 } 12% { opacity:.22 } 19% { opacity:1 }
      47% { opacity:1 } 53% { opacity:.28 } 60% { opacity:1 }
      78% { opacity:1 } 84% { opacity:.18 } 90% { opacity:1 } }
    @keyframes blink { 0%,100% { opacity:1 } 50% { opacity:.12 } }
    .rainH { animation-name: rainFallH; animation-timing-function: linear; animation-iteration-count: infinite; }
    .rainF { animation-name: rainFallF; animation-timing-function: linear; animation-iteration-count: infinite; }
    .f-a   { animation: floatY 9s ease-in-out infinite; }
    .f-b   { animation: floatY 12s ease-in-out infinite; animation-delay:-3.4s; }
    .tear  { animation: tear 2.2s linear infinite; }
    .tear-b{ animation: tear 3.0s linear infinite; animation-delay:-0.8s; }
    .tear-c{ animation: tear 4.0s linear infinite; animation-delay:-1.9s; }
    .tear-d{ animation: tear 5.4s linear infinite; animation-delay:-3.3s; }
    .collapse { animation: crt 20s linear infinite;
                transform-box: fill-box; transform-origin: center; }
    .beam     { animation: crt 20s linear infinite, beamFade 20s linear infinite;
                transform-box: fill-box; transform-origin: center; }
    .blackout { animation: blackout 20s linear infinite; }
    .dosboot  { animation: dosFade 20s linear infinite; }
    .loader   { animation: loaderFade 20s linear infinite; }
    .ldinfo   { animation: ldflick 1.4s steps(1,end) infinite; }
    .blink    { animation: blink 1.1s steps(1,end) infinite; }"""


def char_css(rng, n):
    """逐字母故障：只有部分字母参与；频率低、幅度小，偶尔色散爆发 + 白闪。"""
    # 只让约 1/3 的字参与跳动（随机挑，不按固定间隔）
    k = max(1, round(n / 3))
    picked = set(rng.sample(range(n), k))
    active = [i in picked for i in range(n)]
    out = []
    for i in range(n):
        if not active[i]:
            continue
        bursts = sorted(round(rng.uniform(10, 88), 1)
                        for _ in range(rng.randint(1, 2)))
        ch = [f"0%,{max(bursts[0] - 1, 0):.1f}% {{ transform:translate(0,0) }}"]
        disp = ["0% { opacity:.26 }"]
        hue = [f"0% {{ opacity:0; fill:{CYAN} }}"]
        for t in bursts:
            ax1 = rng.choice((-1, 1)) * rng.randint(2, 6)
            ay1 = rng.choice((-1, 1)) * rng.randint(1, 3)
            ax2 = rng.choice((-1, 1)) * rng.randint(2, 5)
            ay2 = rng.choice((-1, 1)) * rng.randint(1, 2)
            ch.append(f"{t:.1f}% {{ transform:translate({ax1}px,{ay1}px) }}")
            ch.append(f"{t + 0.6:.1f}% {{ transform:translate({ax2}px,{ay2}px) }}")
            ch.append(f"{t + 1.2:.1f}% {{ transform:translate(0,0) }}")
            disp.append(f"{t:.1f}% {{ opacity:.9 }}")
            disp.append(f"{t + 1.2:.1f}% {{ opacity:.26 }}")
            # 变色故障：青 → 品红 → 白 三连闪，再弹回渐变
            hue.append(f"{t:.1f}% {{ opacity:1; fill:{CYAN} }}")
            hue.append(f"{t + 0.35:.1f}% {{ opacity:1; fill:{MAGENTA} }}")
            hue.append(f"{t + 0.7:.1f}% {{ opacity:1; fill:{WHITE} }}")
            hue.append(f"{t + 1.05:.1f}% {{ opacity:0; fill:{CYAN} }}")
        dur = round(rng.uniform(7.0, 12.0), 1)
        delay = round(rng.uniform(0, dur), 1)
        out.append(f"@keyframes ch{i} {{ " + " ".join(ch)
                   + " 100% { transform:translate(0,0) } }")
        out.append(f"@keyframes disp{i} {{ " + " ".join(disp)
                   + " 100% { opacity:.26 } }")
        out.append(f"@keyframes hue{i} {{ " + " ".join(hue)
                   + f" 100% {{ opacity:0; fill:{CYAN} }} }}")
        out.append(f".ch{i}   {{ animation: ch{i} {dur}s steps(1,end) infinite;"
                   f" animation-delay:-{delay}s; }}")
        out.append(f".disp{i} {{ animation: disp{i} {dur}s steps(1,end) infinite;"
                   f" animation-delay:-{delay}s; }}")
        out.append(f".hue{i}  {{ animation: hue{i} {dur}s steps(1,end) infinite;"
                   f" animation-delay:-{delay}s; }}")
    return "\n    ".join(out), active


LD_CHUNKS = 23             # '#' 填充的分段数
PCT_VALUES = ("00%", "13%", "37%", "58%", "81%", "99%")


DOS_LINES = (
    "StarASH BIOS v4.2.0  (C) 2026 StarDust Systems",
    "Memory Test : 640K Base / 15360K Ext ...... OK",
    "Detecting IDE drives ... Master : STARASH-042",
    "Starting StarDOS 4.2 ...",
    "C:\\STARASH> boot --profile=042 --reboot",
    "C:\\STARASH> loading modules ..............",
)


def dos_css(n=6, t0=73.0, t1=81.5):
    """假 DOS 自检：逐行蹦出（整行闪出，不是打字机）。"""
    out, step = [], (t1 - t0) / max(n - 1, 1)
    for i in range(n):
        t = t0 + i * step
        out.append(f"@keyframes dos{i} {{ 0%,{t:.1f}% {{ opacity:0 }} "
                   f"{min(t + 0.6, 99.2):.1f}%,100% {{ opacity:1 }} }}")
        out.append(f".dos{i} {{ animation: dos{i} 20s linear infinite; }}")
    return "\n    ".join(out)


def dos_markup(w, h, compact=False):
    """黑屏里的假 DOS / BIOS 启动自检画面。"""
    n = 5 if compact else len(DOS_LINES)
    fs = 15.5 if compact else 19.0
    lh = 21.0 if compact else 28.0
    x = w * 0.12
    y0 = h * 0.5 - (n - 1) * lh / 2 + fs * 0.35
    p = ['<g class="dosboot">']
    for i in range(n):
        p.append(f'<text class="dos{i}" x="{x:.1f}" y="{y0 + i * lh:.1f}" '
                 f'font-family="{MONO}" font-size="{fs}" fill="{LD_COLOR}">'
                 f"{DOS_LINES[i]}</text>")
    p.append("</g>")
    return "".join(p)


def loader_css(rng, t0=83.0, t1=97.5):
    """终端加载条：'#' 逐段点亮（节奏不匀：有猛冲、有慢爬、还会卡住）、百分比跳变、转轮循环。"""
    out = []
    weights = [rng.choice((0.22, 0.45, 1.0, 1.0, 2.0, 3.6))
               for _ in range(LD_CHUNKS)]
    total = sum(weights)
    t, times = t0, []
    for wgt in weights:
        times.append(t)
        t += wgt / total * (t1 - t0)
    for i, ti in enumerate(times):
        out.append(f"@keyframes ld{i} {{ 0%,{ti:.1f}% {{ opacity:0 }} "
                   f"{min(ti + 0.5, 99.4):.1f}%,100% {{ opacity:1 }} }}")
        out.append(f".ld{i} {{ animation: ld{i} 20s linear infinite; }}")
    n = len(PCT_VALUES)
    for i in range(n):
        a = t0 + (t1 - t0) * (i / n)
        b = t0 + (t1 - t0) * ((i + 1) / n)
        out.append(f"@keyframes pct{i} {{ 0%,{a:.1f}% {{ opacity:0 }} "
                   f"{min(a + 0.3, 99.2):.1f}%,{b:.1f}% {{ opacity:1 }} "
                   f"{min(b + 0.3, 99.6):.1f}%,100% {{ opacity:0 }} }}")
        out.append(f".pct{i} {{ animation: pct{i} 20s linear infinite; }}")
    for i in range(4):
        a, b = i * 25.0, (i + 1) * 25.0
        out.append(f"@keyframes spn{i} {{ 0%,{a:.1f}% {{ opacity:0 }} "
                   f"{min(a + 0.1, 99.3):.1f}%,{b:.1f}% {{ opacity:1 }} "
                   f"{min(b + 0.1, 99.8):.1f}%,100% {{ opacity:0 }} }}")
        out.append(f".spn{i} {{ animation: spn{i} 0.9s steps(1,end) infinite; }}")
    return "\n    ".join(out)


def loader_markup(w, h, compact=False):
    """黑屏里的琥珀色终端加载条：ASCII 外框 + '#' 填充 + 百分比 + 状态行。"""
    bar_w = 700.0 if compact else w - 220.0
    bar_x = (w - bar_w) / 2
    cw = bar_w / LD_BW
    fs = round(cw / 0.6, 1)
    if compact:
        y_t, y_top, y_bar, y_bot, y_stat, y_info = (
            h * 0.13, h * 0.32, h * 0.45, h * 0.58, h * 0.80, None)
    else:
        y_t, y_top, y_bar, y_bot, y_stat, y_info = (
            h * 0.27, h * 0.40, h * 0.49, h * 0.58, h * 0.72, h * 0.83)

    def txt(x, y, s, size=None, anchor=None, tl=None, cls=None):
        a = (f'x="{x:.1f}" y="{y:.1f}" font-family="{MONO}" '
             f'font-size="{fs if size is None else size}" fill="{LD_COLOR}"')
        if anchor:
            a += f' text-anchor="{anchor}"'
        if tl:
            a += f' textLength="{tl:.1f}" lengthAdjust="spacingAndGlyphs"'
        if cls:
            a += f' class="{cls}"'
        return f"<text {a}>{s}</text>"

    p = ['<g class="loader">']
    p.append(txt(w / 2, y_t, "starash.boot(042);", size=fs * 0.9,
                 anchor="middle"))
    border = "+" + "-" * (LD_BW - 2) + "+"
    p.append(txt(bar_x, y_top, border, tl=bar_w))
    p.append(txt(bar_x, y_bot, border, tl=bar_w))
    p.append(txt(bar_x, y_bar, "|", tl=cw))
    p.append(txt(bar_x + bar_w - cw, y_bar, "|", tl=cw))
    inner = LD_BW - 2
    per = inner // LD_CHUNKS
    sizes = [per] * LD_CHUNKS
    sizes[-1] += inner - per * LD_CHUNKS
    x = bar_x + cw
    for i, k in enumerate(sizes):
        p.append(txt(x, y_bar, "#" * k, cls=f"ld{i}", tl=cw * k))
        x += cw * k
    sx = (w - 31 * cw) / 2
    for i, v in enumerate(PCT_VALUES):
        p.append(txt(sx, y_stat, v, cls=f"pct{i}", tl=cw * 3))
    for i, g in enumerate(("[|]", "[/]", "[-]", "[\\]")):
        p.append(txt(sx + 5 * cw, y_stat, g, cls=f"spn{i}", tl=cw * 3))
    p.append(txt(sx + 10 * cw, y_stat, "WAITING FOR RESPONSE", tl=cw * 21))
    if y_info is not None:
        p.append(txt(w / 2, y_info,
                     "RETRY 0042  /  ACK: --  /  REMAINING: 01%",
                     size=fs * 0.72, anchor="middle", cls="ldinfo"))
    p.append("</g>")
    return "".join(p)


def tear_bands(n=4, vn=3):
    """画面撕扯：横向切片做左右错位，竖向切片做上下错位。
    切片用 clipPath 固定、内部 <use> 做位移 —— 所以切口是硬的，像被撕开。"""
    out = []
    for i in range(n):
        out.append(
            f'<g class="tbf" clip-path="url(#tb{i + 1})">'
            f'<use class="ts{i + 1}" xlink:href="#tearSrc" href="#tearSrc"/></g>')
    for i in range(vn):
        out.append(
            f'<g class="tbf" clip-path="url(#vb{i + 1})">'
            f'<use class="vs{i + 1}" xlink:href="#tearSrc" href="#tearSrc"/></g>')
    return "".join(out)


def pixel_chars(text, px, x0, y0, gap=1):
    """把字符串拆成「每个字符一个方块串」。返回 (每字 rect 列表, 总宽)。"""
    chars, cx = [], x0
    for ch in text:
        g = GLYPH5.get(ch)
        rects = []
        if g:
            for r, line in enumerate(g):
                for c, v in enumerate(line):
                    if v == "1":
                        rects.append(
                            f'<rect x="{cx + c * px}" y="{y0 + r * px}" '
                            f'width="{px - 2}" height="{px - 2}"/>')
        chars.append("".join(rects))
        cx += (5 + gap) * px
    return chars, (len(text) * (5 + gap) - gap) * px


def defs(chars, gx1, gx2, spath, tbands, vbands):
    glyphs3 = "".join(
        f'<g id="g{k}">' + "".join(
            f'<rect x="{c * PX}" y="{r * PX}" width="{CELL}" height="{CELL}"/>'
            for r, line in enumerate(pattern) for c, ch in enumerate(line) if ch == "1"
        ) + "</g>"
        for k, pattern in GLYPH3.items()
    )
    char_defs = "".join(f'<g id="gch{i}">{r}</g>' for i, r in enumerate(chars))
    # 撕扯用的标题原图（只填渐变、不带辉光/故障）——切片错位时像被扯出来的原始数据
    tearsrc = ('<g id="tearSrc" filter="url(#neonGlow)">' + "".join(
        f'<use xlink:href="#gch{i}" href="#gch{i}" fill="url(#titleGrad)"/>'
        for i in range(len(chars))) + "</g>")
    tbclips = "".join(
        f'<clipPath id="tb{i + 1}"><rect x="0" y="{y}" width="1280" '
        f'height="{hh}"/></clipPath>' for i, (y, hh) in enumerate(tbands))
    # 竖向切片：上下撕扯用
    vbclips = "".join(
        f'<clipPath id="vb{i + 1}"><rect x="{x}" y="0" width="{ww}" '
        f'height="512"/></clipPath>' for i, (x, ww) in enumerate(vbands))
    return f"""<defs>
    <linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="{BG0}"/>
      <stop offset="1" stop-color="{BG1}"/>
    </linearGradient>
    <!-- 电子束：中心最亮向外衰减。塌缩时它就是那条亮线 / 那个亮点 -->
    <radialGradient id="beamGrad" cx="0.5" cy="0.5" r="0.5">
      <stop offset="0" stop-color="#ffffff" stop-opacity="1"/>
      <stop offset="0.18" stop-color="#eafff4" stop-opacity="0.9"/>
      <stop offset="0.5" stop-color="#5affa8" stop-opacity="0.35"/>
      <stop offset="1" stop-color="#5affa8" stop-opacity="0"/>
    </radialGradient>
    <!-- userSpaceOnUse：让所有点阵方块共享同一套渐变坐标，标题才整体流动 -->
    <linearGradient id="titleGrad" gradientUnits="userSpaceOnUse"
                    x1="{gx1}" y1="0" x2="{gx2}" y2="0">
      <stop offset="0" stop-color="{CYAN}"/>
      <stop offset="0.32" stop-color="{BLUE}"/>
      <stop offset="0.62" stop-color="{MAGENTA}"/>
      <stop offset="1" stop-color="{ORANGE}"/>
      <animate attributeName="x1" values="{gx1};{gx1 - 420};{gx1}" dur="9s" repeatCount="indefinite"/>
      <animate attributeName="x2" values="{gx2};{gx2 - 420};{gx2}" dur="9s" repeatCount="indefinite"/>
    </linearGradient>
    <pattern id="cells" width="{PX}" height="{PX}" patternUnits="userSpaceOnUse">
      <rect x="0.5" y="0.5" width="{CELL}" height="{CELL}" fill="#5affa8" opacity="0.045"/>
    </pattern>
    <!-- 液晶网格：横线略强于竖线 —— 横线本身就是 CRT 扫描线。
         不要再叠一层同周期图案，两层对齐的暗线会加倍成摩尔纹条带。 -->
    <pattern id="lcd" width="{PX}" height="{PX}" patternUnits="userSpaceOnUse">
      <path d="M0 0 H{PX}" stroke="#000000" stroke-width="1" opacity="0.26"/>
      <path d="M0 0 V{PX}" stroke="#000000" stroke-width="1" opacity="0.15"/>
    </pattern>
    <!-- 整幅画面的故障滤镜链：动态模糊 → 湍流失真 → RGB 通道分离。
         必须合并成一条链、挂在整幅内容上：撕条/切片/标题/数字雨才会一起被处理，
         否则各效果各挂各的，看起来就「浮」在画面上。
         所有参数平时为 0 → 平时完全看不出；只在故障帧（20s 周期的 66%–69%，紧接息屏）拉起来。 -->
    <filter id="picfx" x="-8%" y="-14%" width="116%" height="128%">
      <!-- 1. 动态模糊（水平方向） -->
      <feGaussianBlur in="SourceGraphic" stdDeviation="0 0" result="bl">
        <animate attributeName="stdDeviation" dur="20s" repeatCount="indefinite"
                 calcMode="discrete"
                 keyTimes="0;0.6606;0.6663;0.6711;0.6758;0.6805;0.6853;0.6900;1"
                 values="0 0;7 0;4 0;9 0;5 0;3 0;1.5 0;0 0;0 0"/>
      </feGaussianBlur>
      <!-- 2. 湍流失真 -->
      <feTurbulence type="fractalNoise" baseFrequency="0.006 0.05" numOctaves="1"
                    seed="7" result="nz">
        <animate attributeName="seed" dur="20s" repeatCount="indefinite"
                 calcMode="discrete" keyTimes="0;0.6632;0.6695;0.6758;0.6821;0.6884;1"
                 values="1;4;9;3;12;6;1"/>
      </feTurbulence>
      <feDisplacementMap in="bl" in2="nz" scale="0"
                         xChannelSelector="R" yChannelSelector="G" result="wp">
        <animate attributeName="scale" dur="20s" repeatCount="indefinite"
                 calcMode="discrete"
                 keyTimes="0;0.6606;0.6663;0.6711;0.6758;0.6805;0.6853;0.6900;1"
                 values="0;14;7;18;10;5;2;0;0"/>
      </feDisplacementMap>
      <!-- 3. RGB 通道分离：三通道互不重叠，screen 叠加正好还原原色 -->
      <feOffset in="wp" dx="0" result="sr">
        <animate attributeName="dx" dur="20s" repeatCount="indefinite" calcMode="discrete"
                 keyTimes="0;0.6606;0.6663;0.6711;0.6758;0.6805;0.6853;0.6900;1"
                 values="0;-7;5;-3;6;-4;2;0;0"/>
      </feOffset>
      <feColorMatrix in="sr" type="matrix"
                     values="1 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0 0 0 1 0" result="cr"/>
      <feOffset in="wp" dx="0" result="sg"/>
      <feColorMatrix in="sg" type="matrix"
                     values="0 0 0 0 0  0 1 0 0 0  0 0 0 0 0  0 0 0 1 0" result="cg"/>
      <feOffset in="wp" dx="0" result="sb">
        <animate attributeName="dx" dur="20s" repeatCount="indefinite" calcMode="discrete"
                 keyTimes="0;0.6606;0.6663;0.6711;0.6758;0.6805;0.6853;0.6900;1"
                 values="0;7;-5;3;-6;4;-2;0;0"/>
      </feOffset>
      <feColorMatrix in="sb" type="matrix"
                     values="0 0 0 0 0  0 0 0 0 0  0 0 1 0 0  0 0 0 1 0" result="cb"/>
      <feBlend in="cr" in2="cg" mode="screen" result="m1"/>
      <feBlend in="m1" in2="cb" mode="screen"/>
    </filter>
    <!-- VHS 亮纹：配合 screen 混合 —— 两端用透明黑（screen 黑=无变化），中间加光 -->
    <linearGradient id="vhsGrad" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="#000000" stop-opacity="0"/>
      <stop offset="0.18" stop-color="#38d6ff" stop-opacity="0.62"/>
      <stop offset="0.5" stop-color="#ffffff" stop-opacity="0.55"/>
      <stop offset="0.82" stop-color="#ff4fd8" stop-opacity="0.62"/>
      <stop offset="1" stop-color="#000000" stop-opacity="0"/>
    </linearGradient>
    <!-- VHS 暗纹：配合 multiply 混合 —— 两端用透明白（multiply 白=无变化），中间压暗但不压死 -->
    <linearGradient id="vhsDark" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="#ffffff" stop-opacity="0"/>
      <stop offset="0.14" stop-color="#6a6a6a" stop-opacity="1"/>
      <stop offset="0.5" stop-color="#565656" stop-opacity="1"/>
      <stop offset="0.86" stop-color="#6a6a6a" stop-opacity="1"/>
      <stop offset="1" stop-color="#ffffff" stop-opacity="0"/>
    </linearGradient>
    <!-- 玻璃反光：左上角一层柔和高光（克制，只做“隔玻璃”暗示） -->
    <radialGradient id="glass" cx="0.24" cy="0.08" r="0.46">
      <stop offset="0" stop-color="#ffffff" stop-opacity="0.045"/>
      <stop offset="0.55" stop-color="#ffffff" stop-opacity="0.012"/>
      <stop offset="1" stop-color="#ffffff" stop-opacity="0"/>
    </radialGradient>
    <radialGradient id="vig" cx="0.5" cy="0.5" r="0.78">
      <stop offset="0.35" stop-color="#000000" stop-opacity="0"/>
      <stop offset="0.72" stop-color="#000000" stop-opacity="0.28"/>
      <stop offset="1" stop-color="#000000" stop-opacity="0.72"/>
    </radialGradient>
    <filter id="neonGlow" x="-20%" y="-20%" width="140%" height="140%">
      <feGaussianBlur in="SourceAlpha" stdDeviation="5" result="b1"/>
      <feFlood flood-color="{MAGENTA}" flood-opacity="0.85" result="c1"/>
      <feComposite in="c1" in2="b1" operator="in" result="g1"/>
      <feGaussianBlur in="SourceAlpha" stdDeviation="2.2" result="b2"/>
      <feFlood flood-color="{CYAN}" flood-opacity="0.65" result="c2"/>
      <feComposite in="c2" in2="b2" operator="in" result="g2"/>
      <feMerge>
        <feMergeNode in="g1"/><feMergeNode in="g2"/><feMergeNode in="SourceGraphic"/>
      </feMerge>
    </filter>
    <clipPath id="screen"><path d="{spath}"/></clipPath>
    {glyphs3}
    {char_defs}
    {tearsrc}
    {tbclips}
    {vbclips}
  </defs>"""


def screen_path(w, h, m=10, k=34, r=28):
    """CRT 屏轮廓：圆角 + 四边向外鼓的桶形，于是中间显得“顶出来”。"""
    x0, y0, x1, y1 = m, m, w - m, h - m
    dx, dy = x1 - x0 - 2 * r, y1 - y0 - 2 * r
    return (
        f'M {x0 + r},{y0} '
        f'C {x0 + r + dx / 3},{y0 - k} {x1 - r - dx / 3},{y0 - k} {x1 - r},{y0} '
        f'Q {x1},{y0} {x1},{y0 + r} '
        f'C {x1 + k},{y0 + r + dy / 3} {x1 + k},{y1 - r - dy / 3} {x1},{y1 - r} '
        f'Q {x1},{y1} {x1 - r},{y1} '
        f'C {x1 - r - dx / 3},{y1 + k} {x0 + r + dx / 3},{y1 + k} {x0 + r},{y1} '
        f'Q {x0},{y1} {x0},{y1 - r} '
        f'C {x0 - k},{y1 - r - dy / 3} {x0 - k},{y0 + r + dy / 3} {x0},{y0 + r} '
        f'Q {x0},{y0} {x0 + r},{y0} Z'
    )


def rain_base(j, rows):
    """列内第 j 行的基准亮度。用线性梯度：非线性（^2）会把尾部压到几乎看不见，雨会变稀。"""
    return 0.10 + 0.70 * (j / (rows - 1))


def rain_css(rows, period=3.2):
    """数字雨「流光」：按行做相位偏移 —— 亮度沿列向下传播，而不是随机闪烁。

    关键：第 0 行延迟最负（相位最超前）→ 峰值最先出现；越靠下的行越滞后，
    于是亮光顺着数字列往下流。同时把每行的基准亮度写进关键帧，
    这样「头部亮、尾部暗」的彗星梯度不会被动画抹平。摆幅刻意收窄，避免把梯度冲平。
    """
    out = []
    for j in range(rows):
        base = rain_base(j, rows)
        if j == rows - 1:                    # 头部是整列的锚点，摆动幅度更窄
            lo, hi = 0.80, 1.0
        else:
            lo = round(base * 0.62, 2)
            hi = round(min(0.98, base * 1.38 + 0.05), 2)
        out.append(f"@keyframes rw{j} {{ 0%,100% {{ opacity:{lo} }} "
                   f"50% {{ opacity:{hi} }} }}")
        delay = round(-(rows - 1 - j) * period / rows, 2)
        out.append(f".rw{j} {{ animation: rw{j} {period}s ease-in-out infinite; "
                   f"animation-delay:{delay}s; }}")
    return "\n    ".join(out)


def use_glyph(kind, x, y, fill, opacity, cls=None):
    c = f' class="{cls}"' if cls else ""
    return (f'<use{c} xlink:href="#g{kind}" href="#g{kind}" x="{x:.1f}" y="{y:.1f}" '
            f'fill="{fill}" opacity="{opacity:.2f}"/>')


def rain(rng, w, rows, pitch, cls):
    col_w, col_h = 30.0, rows * pitch
    cols = int((w - 24) // col_w)
    out = []
    for i in range(cols):
        x = 12 + i * col_w + rng.uniform(-2, 2)
        dur = rng.uniform(3.4, 8.6)
        delay = -rng.uniform(0, dur)
        parts = []
        for j in range(rows):
            head = j == rows - 1
            parts.append(use_glyph(
                rng.choice("01"), x, -col_h + j * pitch,
                RAIN_HEAD if head else RAIN,
                1.0 if head else rain_base(j, rows),
                cls=f"rw{j}",
            ))
        out.append(f'<g class="{cls}" style="animation-duration:{dur:.1f}s;'
                   f'animation-delay:{delay:.1f}s">{"".join(parts)}</g>')
    return "".join(out)


def pixel_disc(cx_cell, cy_cell, r_cells, base, dark):
    rects = []
    for gy in range(-r_cells, r_cells + 1):
        for gx in range(-r_cells, r_cells + 1):
            if gx * gx + gy * gy <= r_cells * r_cells:
                rects.append(
                    f'<rect x="{(cx_cell + gx) * PX}" y="{(cy_cell + gy) * PX}" '
                    f'width="{CELL}" height="{CELL}" '
                    f'fill="{dark if gy > 0 else base}"/>')
    return "".join(rects)


def glitch_title(n, active):
    """逐字母故障：仅部分字母参与（位移/色散/变色），整串共用一个霓虹辉光 + RGB 分离。"""
    out = ['<g filter="url(#neonGlow)">']
    for i in range(n):
        c = f' class="ch{i}"' if active[i] else ""
        d = f' class="disp{i}"' if active[i] else ""
        h = f' class="hue{i}"' if active[i] else ""
        out.append(
            f'<g{c}>'
            f'<use{d} xlink:href="#gch{i}" href="#gch{i}" '
            f'fill="{CYAN}" opacity="0.26" transform="translate(-2.5,2)"/>'
            f'<use{d} xlink:href="#gch{i}" href="#gch{i}" '
            f'fill="{MAGENTA}" opacity="0.26" transform="translate(2.5,-2)"/>'
            f'<use xlink:href="#gch{i}" href="#gch{i}" fill="url(#titleGrad)"/>'
            f'<use{h} xlink:href="#gch{i}" href="#gch{i}" '
            f'fill="{CYAN}" opacity="0"/>'
            f'</g>')
    out.append("</g>")
    return "".join(out)


def vhs_bars(rng, w, h, n=14):
    """VHS 随机撕条：亮纹（青→白→品红）与暗纹（压暗带）混合，只在几帧内闪出。
    约 45% 是暗纹，其中一半通栏 —— 亮暗交替才像真的信号损坏。"""
    out = ['<g class="vhs">']
    for i in range(n):
        y = rng.uniform(h * 0.05, h * 0.90)
        bh = rng.choice((2, 3, 4, 6, 9, 12))
        dark = rng.random() < 0.45
        if dark and rng.random() < 0.5:
            x, bw = 0.0, float(w)
        else:
            bw = rng.uniform(w * 0.12, w * 0.52)
            x = rng.uniform(0, w - bw)
        fill = "url(#vhsDark)" if dark else "url(#vhsGrad)"
        blend = "mix-blend-mode:multiply" if dark else "mix-blend-mode:screen"
        cls = ("vhsbar-d" if dark
               else ("vhsbar" if i % 3 else "vhsbar-b"))
        out.append(f'<rect class="{cls}" x="{x:.0f}" y="{y:.0f}" '
                   f'width="{bw:.0f}" height="{bh}" fill="{fill}" '
                   f'style="{blend}" opacity="0"/>')
    out.append("</g>")
    return "".join(out)


def svg(w, h, css, body, label):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" '
            f'xmlns:xlink="http://www.w3.org/1999/xlink" '
            f'viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img" '
            f'aria-label="{label}"><style>{css}</style>{body}</svg>')


def build_header():
    w, h = 1280, 320
    rng = random.Random(42)
    text = "StarAsh042"
    chars, tw = pixel_chars(text, 12, 0, 0)
    x0 = (w - tw) / 2
    chars, _ = pixel_chars(text, 12, x0, 108)
    _, iw = pixel_chars(INFO_TEXT, 4, 0, 0)
    info_rects = "".join(pixel_chars(INFO_TEXT, 4, (w - iw) / 2, 214)[0])
    ccss, active = char_css(rng, len(text))
    css = (BASE_CSS + "\n    " + rain_css(11) + "\n    " + ccss
           + "\n    " + dos_css() + "\n    " + loader_css(rng))
    pb, pd = PLANETS["purple"]
    ob, od = PLANETS["orange"]
    body = [
        f'<rect width="{w}" height="{h}" fill="#000000"/>',
        '<g clip-path="url(#screen)">',
        f'<rect width="{w}" height="{h}" fill="#000000"/>',
        '<g class="jolt" filter="url(#picfx)"><g class="collapse">',
        f'<rect width="{w}" height="{h}" fill="url(#bg)"/>',
        f'<rect width="{w}" height="{h}" fill="url(#cells)"/>',
        rain(rng, w, rows=11, pitch=32, cls="rainH"),
        f'<g class="f-a">{pixel_disc(16, 38, 4, pb, pd)}</g>',
        f'<g class="f-b">{pixel_disc(203, 14, 3, ob, od)}</g>',
        glitch_title(len(text), active),
        f'<g fill="#eafff6" opacity="0.92">{info_rects}</g>',
        vhs_bars(rng, w, h, 14),
        tear_bands(),
        f'<rect class="tear" x="0" y="120" width="{w}" height="3" fill="#c9ffe4" opacity="0"/>',
        f'<rect class="tear-b" x="0" y="168" width="{w}" height="2" fill="#ffd9f4" opacity="0"/>',
        f'<rect class="tear-c" x="0" y="214" width="{w}" height="3" fill="#c9ffe4" opacity="0"/>',
        f'<rect class="tear-d" x="0" y="268" width="{w}" height="2" fill="#ffd9f4" opacity="0"/>',
        f'<rect width="{w}" height="{h}" fill="url(#lcd)"/>',
        '</g></g>',
        f'<rect width="{w}" height="{h}" fill="url(#vig)"/>',
        f'<rect width="{w}" height="{h}" fill="url(#glass)"/>',
        f'<rect class="beam" x="0" y="0" width="{w}" height="{h}" fill="url(#beamGrad)"/>',
        f'<rect class="blackout" x="0" y="0" width="{w}" height="{h}" fill="#000000" opacity="0"/>',
        dos_markup(w, h),
        loader_markup(w, h),
        '</g>',
    ]
    tbands = [(96, 24), (142, 18), (188, 16), (238, 20)]
    vbands = [(330, 26), (560, 34), (800, 22)]
    return svg(w, h, css, defs(chars, x0, x0 + tw,
                               screen_path(w, h, 10, 34, 28), tbands, vbands)
               + "".join(body), "StarAsh042")


def build_footer():
    w, h = 1280, 180
    rng = random.Random(7)
    text = "42 reboots, still StarAsh."
    _, tw = pixel_chars(text, 6, 0, 0)
    x0 = (w - tw) / 2
    chars, _ = pixel_chars(text, 6, x0, 69)
    _, iw = pixel_chars(INFO_TEXT, 3, 0, 0)
    info_rects = "".join(pixel_chars(INFO_TEXT, 3, (w - iw) / 2, 124)[0])
    ccss, active = char_css(rng, len(text))
    css = (BASE_CSS + "\n    " + rain_css(8) + "\n    " + ccss
           + "\n    " + dos_css() + "\n    " + loader_css(rng))
    pb, pd = PLANETS["purple"]
    ob, od = PLANETS["orange"]
    body = [
        f'<rect width="{w}" height="{h}" fill="#000000"/>',
        '<g clip-path="url(#screen)">',
        f'<rect width="{w}" height="{h}" fill="#000000"/>',
        '<g class="jolt" filter="url(#picfx)"><g class="collapse">',
        f'<rect width="{w}" height="{h}" fill="url(#bg)"/>',
        f'<rect width="{w}" height="{h}" fill="url(#cells)"/>',
        rain(rng, w, rows=8, pitch=32, cls="rainF"),
        f'<g class="f-a">{pixel_disc(14, 20, 3, pb, pd)}</g>',
        f'<g class="f-b">{pixel_disc(204, 9, 2, ob, od)}</g>',
        glitch_title(len(text), active),
        f'<g fill="#eafff6" opacity="0.92">{info_rects}</g>',
        vhs_bars(rng, w, h, 10),
        tear_bands(),
        f'<rect class="tear" x="0" y="76" width="{w}" height="2" fill="#c9ffe4" opacity="0"/>',
        f'<rect class="tear-b" x="0" y="118" width="{w}" height="2" fill="#ffd9f4" opacity="0"/>',
        f'<rect class="tear-c" x="0" y="146" width="{w}" height="2" fill="#c9ffe4" opacity="0"/>',
        f'<rect width="{w}" height="{h}" fill="url(#lcd)"/>',
        '</g></g>',
        f'<rect width="{w}" height="{h}" fill="url(#vig)"/>',
        f'<rect width="{w}" height="{h}" fill="url(#glass)"/>',
        f'<rect class="beam" x="0" y="0" width="{w}" height="{h}" fill="url(#beamGrad)"/>',
        f'<rect class="blackout" x="0" y="0" width="{w}" height="{h}" fill="#000000" opacity="0"/>',
        dos_markup(w, h, compact=True),
        loader_markup(w, h, compact=True),
        '</g>',
    ]
    tbands = [(58, 16), (86, 14), (118, 12), (142, 14)]
    vbands = [(400, 24), (620, 30), (860, 20)]
    return svg(w, h, css, defs(chars, x0, x0 + tw,
                               screen_path(w, h, 10, 26, 22), tbands, vbands)
               + "".join(body), "42 reboots, still StarAsh.")


if __name__ == "__main__":
    for name, content in (("banner-header.svg", build_header()),
                          ("banner-footer.svg", build_footer())):
        path = ASSETS / name
        path.write_text(content, encoding="utf-8")
        ET.fromstring(content)
        print(f"OK  {path}  ({len(content)} bytes)")
