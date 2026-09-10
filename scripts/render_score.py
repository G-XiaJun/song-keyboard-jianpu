#!/usr/bin/env python3
"""
通用「一字一音」键盘简谱渲染器
用法:  python render_score.py score.json -o out.png [--width 760] [--cell-max 48]
依赖:  pip install Pillow
"""
import argparse
import json
import math
import os
import random
import sys

from PIL import Image, ImageDraw, ImageFont

# ------------------------------------------------------------------ Fonts
FONT_CANDIDATES = {
    "cn":       ["C:/Windows/Fonts/msyh.ttc", "/System/Library/Fonts/PingFang.ttc",
                 "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"],
    "cn_bold":  ["C:/Windows/Fonts/msyhbd.ttc", "/System/Library/Fonts/PingFang.ttc",
                 "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"],
    "num":      ["C:/Windows/Fonts/consolab.ttf", "/System/Library/Fonts/Courier New Bold.ttf",
                 "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"],
    "mono":     ["C:/Windows/Fonts/consolab.ttf", "/System/Library/Fonts/Courier New Bold.ttf",
                 "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"],
}


def load_font(kind, size):
    for path in FONT_CANDIDATES[kind]:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    return ImageFont.load_default()


# ------------------------------------------------------------------ Colors
GRAD_TOP = (200, 228, 240)
GRAD_MID = (224, 244, 252)
GRAD_LO  = (200, 222, 232)
GRAD_BOT = (118, 158, 178)

COL_TITLE_1 = (58, 122, 184)
COL_TITLE_2 = (42, 90, 138)
COL_WHITE   = (255, 255, 255)
COL_TEXT    = (26, 77, 122)
COL_SUBTLE  = (96, 148, 184)

#            fill(浅底)          border(描边)         text(字色)
COLOR_MAP = {
    "org": ((255, 205, 128), (200, 130, 60), (139, 69, 19)),
    "blu": ((178, 219, 236), (74, 143, 199), (26, 58, 90)),
    "grn": ((190, 230, 200), (90, 175, 110), (26, 74, 42)),
    "pur": ((210, 184, 220), (140, 100, 175), (74, 32, 112)),
}

COL_BADGE = (74, 138, 200)
COL_CLOUD = (255, 255, 255, 95)

DEFAULT_KEY_MAP = {1: "Z", 2: "X", 3: "C", 4: "V", 5: "B", 6: "N", 7: "M"}
OCTAVE_STYLE = {"": "org", "up": "blu", "down": "grn"}


# ------------------------------------------------------------------ Parse
def parse_note(tok):
    """'3^' -> ('3','up');  '_3' -> ('3','down');  '3' -> ('3','')"""
    if tok.endswith("^"):
        return tok[:-1], "up"
    if tok.startswith("_"):
        return tok[1:], "down"
    return tok, ""


def build_sections(data):
    """把 JSON 数据解析成带 cells 的结构，同时做强校验。"""
    key_map_src = data.get("key_map")
    key_map = {}
    for d in range(1, 8):
        if key_map_src and str(d) in key_map_src:
            key_map[d] = key_map_src[str(d)]
        else:
            key_map[d] = DEFAULT_KEY_MAP[d]

    sections = []
    total_rows = 0
    for sect in data["sections"]:
        rows = []
        for row in sect["rows"]:
            lyric = row["lyric"]
            toks = row["notes"].split()
            chars = list(lyric)
            if len(chars) != len(toks):
                raise ValueError(
                    f"字数({len(chars)})与音符数({len(toks)})不符: {lyric}\n"
                    f"  -> {row['notes']}")
            cells = []
            for ch, tok in zip(chars, toks):
                digit, octave = parse_note(tok)
                if not digit.isdigit() or not (1 <= int(digit) <= 7):
                    raise ValueError(f"非法音符 {tok!r}（应为 1-7，可加 ^ / _ 表八度）")
                deg = int(digit)
                cells.append({
                    "char": ch,
                    "digit": digit,
                    "octave": octave,
                    "color": OCTAVE_STYLE[octave],
                    "key": key_map[deg],
                })
            rows.append(cells)
            total_rows += 1
        sections.append((sect["name"], rows))
    return sections, total_rows


# ------------------------------------------------------------------ Render
def render(data, out_path, W=760, cell_max=48, with_footer=True):
    sections, total_rows = build_sections(data)

    SECTION_H, ROW_H, ROW_GAP = 46, 104, 8
    HEADER = 250
    FOOTER = 400 if with_footer else 60

    content_h = len(sections) * SECTION_H + total_rows * (ROW_H + ROW_GAP)
    H = HEADER + content_h + FOOTER

    img = Image.new("RGB", (W, H), GRAD_MID)
    draw = ImageDraw.Draw(img, "RGBA")

    # ---- 背景渐变：四段显式插值，别写成 A*(1-t)+常数（会泛红）
    for y in range(H):
        if y < H * 0.30:
            t = y / (H * 0.30)
            a, b = GRAD_TOP, GRAD_MID
        elif y < H * 0.40:
            t = (y - H * 0.30) / (H * 0.10)
            a, b = GRAD_MID, GRAD_LO
        else:
            t = min(1.0, (y - H * 0.40) / (H * 0.45))
            a, b = GRAD_LO, GRAD_BOT
        draw.line([(0, y), (W, y)],
                  fill=(int(a[0] * (1 - t) + b[0] * t),
                        int(a[1] * (1 - t) + b[1] * t),
                        int(a[2] * (1 - t) + b[2] * t)))

    # ---- helpers
    def rr(xy, r, fill=None, outline=None, width=2):
        draw.rounded_rectangle(xy, radius=r, fill=fill, outline=outline, width=width)

    def tw(text, font):
        bb = draw.textbbox((0, 0), text, font=font)
        return bb[2] - bb[0], bb[3] - bb[1]

    def cloud(x, y2, s=1.0):
        draw.ellipse([x - 30 * s, y2 - 12 * s, x + 30 * s, y2 + 12 * s], fill=COL_CLOUD)
        draw.ellipse([x - 15 * s, y2 - 22 * s, x + 15 * s, y2 - 2 * s], fill=COL_CLOUD)
        draw.ellipse([x - 45 * s, y2 - 8 * s, x - 15 * s, y2 + 10 * s], fill=COL_CLOUD)
        draw.ellipse([x + 15 * s, y2 - 8 * s, x + 45 * s, y2 + 10 * s], fill=COL_CLOUD)

    def pavilion(cx, cy, s=1.0):
        draw.polygon([(cx - 40 * s, cy + 15 * s), (cx + 40 * s, cy + 15 * s),
                      (cx + 35 * s, cy + 5 * s), (cx - 35 * s, cy + 5 * s)],
                     fill=(120, 90, 70), outline=(80, 60, 50))
        for px in (-25, 0, 25):
            draw.rectangle([cx + px * s - 3 * s, cy, cx + px * s + 3 * s, cy + 5 * s],
                           fill=(120, 90, 70), outline=(80, 60, 50))
        draw.polygon([(cx - 45 * s, cy), (cx + 45 * s, cy),
                      (cx + 38 * s, cy - 12 * s), (cx - 38 * s, cy - 12 * s)],
                     fill=(170, 90, 70), outline=(120, 60, 50))
        draw.polygon([(cx - 50 * s, cy - 12 * s), (cx + 50 * s, cy - 12 * s),
                      (cx + 30 * s, cy - 25 * s), (cx - 30 * s, cy - 25 * s)],
                     fill=(190, 100, 80), outline=(130, 70, 55))
        draw.polygon([(cx - 30 * s, cy - 25 * s), (cx + 30 * s, cy - 25 * s),
                      (cx + 15 * s, cy - 38 * s), (cx - 15 * s, cy - 38 * s)],
                     fill=(210, 110, 90), outline=(140, 75, 60))
        draw.line([(cx, cy - 38 * s), (cx, cy - 48 * s)], fill=(80, 50, 40), width=3)
        draw.ellipse([cx - 4 * s, cy - 52 * s, cx + 4 * s, cy - 44 * s], fill=(80, 50, 40))

    def flower(cx, cy, s=1.0):
        for ang in range(0, 360, 72):
            rad = math.radians(ang)
            px, py = cx + 18 * s * math.cos(rad), cy + 18 * s * math.sin(rad)
            draw.ellipse([px - 12 * s, py - 12 * s, px + 12 * s, py + 12 * s],
                         fill=(220, 230, 245), outline=(80, 110, 140))
        draw.ellipse([cx - 9 * s, cy - 9 * s, cx + 9 * s, cy + 9 * s],
                     fill=(255, 220, 180), outline=(180, 130, 70))

    def foliage(cx, cy, angles):
        for ang_deg, l in angles:
            rad = math.radians(ang_deg)
            x2, y2 = cx + l * math.cos(rad), cy + l * math.sin(rad)
            for w in range(3):
                draw.line([(cx, cy), (x2, y2)], fill=(90, 130, 90), width=4 - w)

    random.seed(7)

    def mountains(y_base, color, peak_h, peaks=9):
        pts = [(0, H), (0, y_base)]
        for i in range(peaks + 1):
            x = i / peaks
            bell = max(0.0, 1.0 - abs(x - 0.5) * 2.0)
            sub1 = max(0.0, 1.0 - abs(x - 0.25) * 5.0) * 0.7
            sub2 = max(0.0, 1.0 - abs(x - 0.75) * 5.0) * 0.7
            h = max(0, (bell + sub1 + sub2) * peak_h
                    + random.uniform(-peak_h * 0.08, peak_h * 0.08))
            pts.append((i * W / peaks, y_base - h))
        pts += [(W, y_base), (W, H)]
        draw.polygon(pts, fill=color)

    # ---- 顶部装饰
    cloud(int(W * 0.158), 62, 0.85)
    cloud(int(W * 0.849), 92, 0.9)
    cloud(int(W * 0.553), 48, 0.6)
    pavilion(W - 78, 112, 0.55)
    foliage(50, 50, [(10, 35), (40, 28), (70, 32), (350, 30), (320, 25)])
    flower(80, 80, 0.55)
    foliage(W - 50, 50, [(170, 35), (140, 28), (110, 32), (190, 30), (220, 25)])
    flower(W - 80, 80, 0.55)

    # ---- 标题
    f_cn = load_font("cn", 30)
    f_sub = load_font("cn", 15)
    f_legend = load_font("cn", 16)
    title_y, title_h = 58, 58
    rr((24, title_y, W - 24, title_y + title_h), 22,
       fill=COL_TITLE_1, outline=COL_TITLE_2, width=2)
    draw.rounded_rectangle((28, title_y + 3, W - 28, title_y + title_h // 2), 18,
                           fill=(90, 150, 200, 80))
    t = data.get("title", "键盘谱")
    w, h = tw(t, f_cn)
    draw.text(((W - w) / 2, title_y + (title_h - h) / 2 - 4), t, font=f_cn, fill=COL_WHITE)
    s = data.get("subtitle", "")
    if s:
        w, h = tw(s, f_sub)
        draw.text(((W - w) / 2, title_y + title_h + 10), s, font=f_sub, fill=COL_SUBTLE)

    # ---- 图例
    legend = data.get("legend", [
        ("右键 = 高音", "blu"), ("左键 = 低音", "grn"),
        ("中键 = 半音", "pur"), ("不按鼠标 = 中音", "org")])
    legend_y = title_y + title_h + 38
    chip_w, chip_h = (W - 48 - 12) / 2, 36
    for idx, (label, cls) in enumerate(legend):
        r, c = divmod(idx, 2)
        x0 = 24 + c * (chip_w + 12)
        y0 = legend_y + r * (chip_h + 8)
        fill, brd, txt = COLOR_MAP[cls]
        rr((x0, y0, x0 + chip_w, y0 + chip_h), 18, fill=fill, outline=brd, width=2)
        lw, lh = tw(label, f_legend)
        draw.text((x0 + (chip_w - lw) / 2, y0 + (chip_h - lh) / 2 - 3), label,
                  font=f_legend, fill=txt)

    # ---- 谱面字体
    f_note = load_font("num", 26)
    f_lyric = load_font("cn", 19)
    f_kbd = load_font("mono", 22)
    f_badge = load_font("cn_bold", 15)
    f_sect = load_font("cn_bold", 19)

    y = HEADER
    row_no = 0
    N_X0, N_X1 = 86, W - 38
    AVAIL = N_X1 - N_X0

    for sect_name, rows in sections:
        sw, sh = tw(sect_name, f_sect)
        sx = 30
        draw.ellipse([sx - 4, y + sh / 2 - 3, sx + 4, y + sh / 2 + 5], fill=COL_SUBTLE)
        draw.text((sx + 12, y), sect_name, font=f_sect, fill=COL_SUBTLE)
        draw.line([(sx + 12 + sw + 14, y + sh / 2 + 1), (W - 30, y + sh / 2 + 1)],
                  fill=(150, 190, 215), width=2)
        y += SECTION_H

        for cells in rows:
            row_no += 1
            rr((24, y, W - 24, y + ROW_H), 24,
               fill=(255, 255, 255, 112), outline=(58, 122, 184, 112), width=2)
            bcx, bcy = 52, y + ROW_H / 2
            draw.ellipse([bcx - 18, bcy - 18, bcx + 18, bcy + 18],
                         fill=COL_BADGE, outline=COL_TITLE_2, width=2)
            bt = f"{row_no}."
            bw, bh = tw(bt, f_badge)
            draw.text((bcx - bw / 2 - 1, bcy - bh / 2 - 4), bt,
                      font=f_badge, fill=COL_WHITE)

            n = len(cells)
            cell_w = min(cell_max, AVAIL / n)
            start_x = N_X0 + max(0, (AVAIL - n * cell_w) / 2)
            box_w = max(30, min(36, cell_w - 6))
            box_h = 30
            box_top = y + ROW_H - box_h - 6

            for i, cell in enumerate(cells):
                cx = start_x + i * cell_w + cell_w / 2

                # 数字 + 八度圆点
                nw, nh = tw(cell["digit"], f_note)
                ny = y + 10
                draw.text((cx - nw / 2, ny), cell["digit"], font=f_note, fill=COL_TEXT)
                if cell["octave"] == "up":
                    draw.ellipse([cx - 4, ny - 10, cx + 4, ny - 2], fill=COL_TEXT)
                elif cell["octave"] == "down":
                    draw.ellipse([cx - 4, ny + nh + 2, cx + 4, ny + nh + 10], fill=COL_TEXT)

                # 歌词 chip
                cw, ch = tw(cell["char"], f_lyric)
                chip_top = y + 40
                fill, brd, txt = COLOR_MAP[cell["color"]]
                rr((cx - cw / 2 - 10, chip_top, cx + cw / 2 + 10, chip_top + ch + 12),
                   11, fill=fill, outline=brd, width=2)
                draw.text((cx - cw / 2, chip_top + 5), cell["char"],
                          font=f_lyric, fill=txt)

                # 键盘字母：彩色方框 + 大写粗体
                fill, brd, txt = COLOR_MAP[cell["color"]]
                rr((cx - box_w / 2, box_top, cx + box_w / 2, box_top + box_h),
                   8, fill=fill, outline=brd, width=3)
                kw, kh = tw(cell["key"], f_kbd)
                draw.text((cx - kw / 2, box_top + (box_h - kh) / 2 - 3), cell["key"],
                          font=f_kbd, fill=txt)

            y += ROW_H + ROW_GAP

    # ---- 底部装饰
    foot = y + 30
    if with_footer:
        mountains(foot + 30, (172, 208, 220), 70, 7)
        mountains(foot + 80, (148, 188, 204), 60, 8)
        mountains(foot + 130, (122, 168, 186), 50, 10)
        cloud(120, foot + 60, 0.9)
        cloud(640, foot + 80, 0.7)
        cloud(380, foot + 200, 0.6)
        mountains(foot + 220, (90, 134, 162), 80, 8)
        pavilion(640, foot + 150, 0.5)
        draw.rectangle([460, foot + 175, 660, foot + 195], fill=(95, 130, 150))
        draw.ellipse([460, foot + 195, 660, foot + 235], outline=(95, 130, 150), width=3)
    foliage(60, H - 70, [(10, 35), (40, 28), (70, 32), (350, 30), (320, 25)])
    flower(90, H - 40, 0.55)
    foliage(W - 60, H - 70, [(170, 35), (140, 28), (110, 32), (190, 30), (220, 25)])
    flower(W - 90, H - 40, 0.55)

    os.makedirs(os.path.dirname(os.path.abspath(out_path)) or ".", exist_ok=True)
    img.save(out_path, "PNG", optimize=True)
    print(f"OK  rows={total_rows}  size={W}x{H}")
    print(f"Saved: {out_path}")


# ------------------------------------------------------------------ CLI
def main():
    ap = argparse.ArgumentParser(description="渲染一字一音键盘简谱 PNG")
    ap.add_argument("json_path", help="谱面 JSON 文件")
    ap.add_argument("-o", "--output", required=True, help="输出 PNG 路径")
    ap.add_argument("--width", type=int, default=760, help="画布宽度，默认 760")
    ap.add_argument("--cell-max", type=int, default=48, help="单字最大列宽，默认 48")
    ap.add_argument("--no-footer", action="store_true", help="去掉底部山水装饰")
    args = ap.parse_args()

    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    with open(args.json_path, encoding="utf-8") as f:
        data = json.load(f)

    render(data, args.output, W=args.width,
           cell_max=args.cell_max, with_footer=not args.no_footer)


if __name__ == "__main__":
    main()
