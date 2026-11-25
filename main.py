#!/usr/bin/env python3
"""news-image-20261124 v3 — draws a one-page newspaper front page summing up
Tuesday 24 November 2026 in a single 1024x1024 PNG.

Pure Python 3.13 stdlib only. No network, no wall clock, no randomness:
every run writes byte-identical output. All drawing is done with a small
5x7 bitmap font and filled rectangles / lines / circles on an RGB canvas,
then encoded as PNG with zlib (filter 0, fixed level) so the bytes are
fully deterministic.
"""

import os
import struct
import zlib

W = 1024
H = 1024

# ---------------------------------------------------------------- palette
PAPER = (247, 242, 231)
INK = (17, 17, 17)
GREY = (90, 86, 78)
RED = (163, 22, 33)
BLUE = (27, 58, 107)
GREEN = (30, 107, 58)
GOLD = (150, 105, 10)
TEAL = (14, 92, 96)
LIGHT = (232, 226, 212)
RULE = (60, 56, 48)

# ------------------------------------------------------- 5x7 bitmap font
# Each glyph is 7 rows of 5 bits ("1" = ink). Space is all zeros.
FONT = {
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "G": ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    "J": ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    "K": ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "M": ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    "N": ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "Q": ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "V": ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    "W": ("10001", "10001", "10001", "10101", "10101", "11011", "10001"),
    "X": ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00110", "01000", "10000", "11111"),
    "3": ("11111", "00010", "00100", "00010", "00001", "10001", "01110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    "6": ("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00010", "01100"),
    "a": ("00000", "00000", "01110", "00001", "01111", "10001", "01111"),
    "b": ("10000", "10000", "11110", "10001", "10001", "10001", "11110"),
    "c": ("00000", "00000", "01110", "10001", "10000", "10001", "01110"),
    "d": ("00001", "00001", "01111", "10001", "10001", "10001", "01111"),
    "e": ("00000", "00000", "01110", "10001", "11111", "10000", "01110"),
    "f": ("00110", "01001", "01000", "11110", "01000", "01000", "01000"),
    "g": ("00000", "01111", "10001", "10001", "01111", "00001", "01110"),
    "h": ("10000", "10000", "11110", "10001", "10001", "10001", "10001"),
    "i": ("00100", "00000", "01100", "00100", "00100", "00100", "01110"),
    "j": ("00010", "00000", "00110", "00010", "00010", "10010", "01100"),
    "k": ("10000", "10000", "10010", "10100", "11000", "10100", "10010"),
    "l": ("01100", "00100", "00100", "00100", "00100", "00100", "01110"),
    "m": ("00000", "00000", "11010", "10101", "10101", "10101", "10101"),
    "n": ("00000", "00000", "11110", "10001", "10001", "10001", "10001"),
    "o": ("00000", "00000", "01110", "10001", "10001", "10001", "01110"),
    "p": ("00000", "00000", "11110", "10001", "11110", "10000", "10000"),
    "q": ("00000", "00000", "01111", "10001", "01111", "00001", "00001"),
    "r": ("00000", "00000", "10110", "11001", "10000", "10000", "10000"),
    "s": ("00000", "00000", "01111", "10000", "01110", "00001", "11110"),
    "t": ("01000", "01000", "11100", "01000", "01000", "01010", "00100"),
    "u": ("00000", "00000", "10001", "10001", "10001", "10011", "01101"),
    "v": ("00000", "00000", "10001", "10001", "10001", "01010", "00100"),
    "w": ("00000", "00000", "10001", "10101", "10101", "10101", "01010"),
    "x": ("00000", "00000", "10001", "01010", "00100", "01010", "10001"),
    "y": ("00000", "00000", "10001", "10001", "01111", "00001", "01110"),
    "z": ("00000", "00000", "11111", "00010", "00100", "01000", "11111"),
    " ": ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    ".": ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ",": ("00000", "00000", "00000", "00000", "01100", "00100", "01000"),
    ":": ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    ";": ("00000", "01100", "01100", "00000", "01100", "00100", "01000"),
    "!": ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    "?": ("01110", "10001", "00001", "00110", "00100", "00000", "00100"),
    "-": ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    "\u2014": ("00000", "00000", "00000", "11111", "00000", "00000", "00000"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    '"': ("01010", "01010", "00000", "00000", "00000", "00000", "00000"),
    "(": ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ")": ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    "%": ("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
    "$": ("00100", "01111", "10100", "01110", "00101", "11110", "00100"),
    "&": ("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
    "/": ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    "+": ("00000", "00100", "00100", "11111", "00100", "00100", "00000"),
    "=": ("00000", "00000", "11111", "00000", "11111", "00000", "00000"),
    "#": ("01010", "01010", "11111", "01010", "11111", "01010", "01010"),
    "@": ("01110", "10001", "10111", "10101", "10110", "10000", "01110"),
    "*": ("00000", "10101", "01110", "11111", "01110", "10101", "00000"),
    "[": ("01110", "01000", "01000", "01000", "01000", "01000", "01110"),
    "]": ("01110", "00010", "00010", "00010", "00010", "00010", "01110"),
    "_": ("00000", "00000", "00000", "00000", "00000", "00000", "11111"),
    "<": ("00010", "00100", "01000", "10000", "01000", "00100", "00010"),
    ">": ("01000", "00100", "00010", "00001", "00010", "00100", "01000"),
    "|": ("00100", "00100", "00100", "00100", "00100", "00100", "00100"),
    "\u00b7": ("00000", "00000", "00100", "01110", "01110", "00100", "00000"),
    "\u00d7": ("00000", "10001", "01010", "00100", "01010", "10001", "00000"),
}

CHAR_W = 5
CHAR_H = 7


def text_width(text, scale):
    """Pixel width of text at the given scale (1px gap between glyphs)."""
    if not text:
        return 0
    return len(text) * (CHAR_W + 1) * scale - scale


def wrap_text(text, max_chars):
    """Greedy word wrap into lines of at most max_chars characters."""
    words = text.split(" ")
    lines = []
    cur = ""
    for word in words:
        if not cur:
            cur = word
        elif len(cur) + 1 + len(word) <= max_chars:
            cur += " " + word
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


class Canvas:
    def __init__(self, w, h, bg):
        self.w = w
        self.h = h
        self.px = bytearray(w * h * 3)
        r, g, b = bg
        for i in range(0, len(self.px), 3):
            self.px[i] = r
            self.px[i + 1] = g
            self.px[i + 2] = b

    def set(self, x, y, color):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i], self.px[i + 1], self.px[i + 2] = color

    def rect(self, x, y, w, h, color):
        x0 = max(0, x)
        y0 = max(0, y)
        x1 = min(self.w, x + w)
        y1 = min(self.h, y + h)
        r, g, b = color
        for yy in range(y0, y1):
            base = (yy * self.w + x0) * 3
            for xx in range(x0, x1):
                i = base + (xx - x0) * 3
                self.px[i] = r
                self.px[i + 1] = g
                self.px[i + 2] = b

    def hline(self, x, y, w, color, thick=1):
        self.rect(x, y, w, thick, color)

    def vline(self, x, y, h, color, thick=1):
        self.rect(x, y, thick, h, color)

    def line(self, x0, y0, x1, y1, color):
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        while True:
            self.set(x0, y0, color)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def circle(self, cx, cy, r, color, filled=True):
        for yy in range(cy - r, cy + r + 1):
            for xx in range(cx - r, cx + r + 1):
                d2 = (xx - cx) ** 2 + (yy - cy) ** 2
                if filled:
                    if d2 <= r * r:
                        self.set(xx, yy, color)
                else:
                    if abs(d2 - r * r) <= r * 2:
                        self.set(xx, yy, color)

    def text(self, x, y, s, scale, color):
        cx = x
        for ch in s:
            glyph = FONT.get(ch, FONT[" "])
            for row in range(CHAR_H):
                bits = glyph[row]
                for col in range(CHAR_W):
                    if bits[col] == "1":
                        self.rect(cx + col * scale, y + row * scale,
                                  scale, scale, color)
            cx += (CHAR_W + 1) * scale
        return cx

    def text_center(self, cx, y, s, scale, color):
        self.text(cx - text_width(s, scale) // 2, y, s, scale, color)

    def para(self, x, y, s, scale, max_chars, color, leading=None):
        """Draw wrapped paragraph; returns y just below the last line."""
        if leading is None:
            leading = CHAR_H * scale + 4
        for line in wrap_text(s, max_chars):
            self.text(x, y, line, scale, color)
            y += leading
        return y


def png_bytes(canvas):
    """Encode the canvas as a deterministic PNG (filter 0, level 6)."""
    raw = bytearray()
    stride = canvas.w * 3
    for y in range(canvas.h):
        raw.append(0)
        start = y * stride
        raw += canvas.px[start:start + stride]
    comp = zlib.compress(bytes(raw), 6)

    def chunk(kind, data):
        out = struct.pack(">I", len(data)) + kind + data
        out += struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
        return out

    ihdr = struct.pack(">IIBBBBB", canvas.w, canvas.h, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", comp) + chunk(b"IEND", b""))

# ------------------------------------------------------------- the stories
# All 14 stories happened on, or were first reported on, Tuesday
# 24 November 2026. Sources were checked against Reuters / AP wire
# reporting of that day (see README for the source list).

LEAD = {
    "kicker": "MARKETS  ·  NEW YORK",
    "headline": "NVIDIA TUMBLES 6% AS AI RALLY FADES",
    "deck": ("A day after soaring 31% on Jensen Huang's return as chief, "
             "the chipmaker gives back $240 billion. Nasdaq falls 1.5%."),
}

SECOND_ROW = [
    {
        "kicker": "WAR  ·  LIBYA",
        "color": RED,
        "headline": "UKRAINE DEFENDS DRONE STRIKE ON RUSSIAN WARSHIP",
        "deck": ("Kyiv says its sea drones sank the corvette Merkury off "
                 "Benghazi. Two Libyan sailors die of wounds."),
    },
    {
        "kicker": "CHINA  ·  BEIJING",
        "color": BLUE,
        "headline": "CHINA PROBES A FOURTH POLITBURO MEMBER FOR GRAFT",
        "deck": ("Shanghai party chief Chen Jining is under investigation "
                 "as the graft drive reaches the top."),
    },
    {
        "kicker": "TRADE  ·  WASHINGTON",
        "color": GOLD,
        "headline": "US PLANS NEW TARIFFS ON CHINA, EU AND OTHERS",
        "deck": ("Washington readies duties on 14 partners over subsidised "
                 "output, steepest rates for China."),
    },
]

# (tag, colour, headline, deck) — each one line + one deck line.
BRIEFS = [
    ("TECH", RED,
     "HUAWEI GUILTY OF STEALING TRADE SECRETS",
     "US jury convicts the telecoms giant."),
    ("SECURITY", BLUE,
     "CIA SYSTEM BREACHED IN CYBERATTACK",
     "An unclassified system is hacked."),
    ("ISRAEL", TEAL,
     "EISENKOT CLINCHES FIRST COALITION PACT",
     "First step to forming a government."),
    ("YEMEN", RED,
     "HOUTHI DRONE HITS RIYADH'S TALLEST TOWER",
     "Coalition calls it a terrorist attack."),
    ("GAZA", GOLD,
     "ISRAELI STRIKES KILL THREE IN GAZA",
     "Deaths as the ceasefire frays."),
    ("COLOMBIA", GREEN,
     "CAR BOMB INJURES 23 IN CENTRAL CITY",
     "Violence spreads to urban areas."),
    ("USA", BLUE,
     "TRUMP PARDONS TURKEYS FREEDOM, FEATHERS",
     "White House keeps the tradition."),
    ("PACIFIC", TEAL,
     "SOLOMON ISLANDS PICKS AUSTRALIA",
     "Treaty pointedly leaves out China."),
    ("BUSINESS", GOLD,
     "SHEIN TO PAY $100M OVER FTC CLAIMS",
     "Settles deceptive-practices claims."),
    ("USA", RED,
     "COURT CLEARS ARMY TO BLAST OLD EXPLOSIVES",
     "Ageing explosives to be detonated."),
]


def draw_masthead(c):
    c.hline(24, 18, 976, INK, 4)
    c.text_center(512, 34, "THE WORLD", 8, INK)
    c.text_center(512, 100, "TUESDAY  24  NOVEMBER  2026", 3, RED)
    c.hline(24, 128, 976, INK, 2)
    c.text_center(512, 140, "THE DAY IN ONE PAGE  -  14 STORIES FROM AROUND THE GLOBE",
                  2, GREY)


def draw_lead(c, y):
    # Red rule + kicker
    c.hline(24, y, 976, RED, 3)
    c.text(24, y + 12, LEAD["kicker"], 2, RED)
    # Headline, two lines, scale 4
    hy = y + 36
    for line in wrap_text(LEAD["headline"], 26):
        c.text(24, hy, line, 4, INK)
        hy += 36
    # Deck under the headline, left column
    dy = c.para(24, hy + 6, LEAD["deck"], 2, 52, INK)
    # Ticker strip of the day's market numbers
    ty = dy + 10
    c.rect(24, ty, 600, 34, LIGHT)
    c.text(36, ty + 10, "NVIDIA -5.9%  NASDAQ -1.5%  S&P -0.5%  DOW +423",
           2, INK)
    # Chart panel on the right: Monday's surge, Tuesday's fall
    px, py, pw, ph = 660, y + 12, 340, 176
    c.rect(px, py, pw, ph, (255, 255, 255))
    c.rect(px, py, pw, ph, INK)  # placeholder border, redrawn below
    c.rect(px + 2, py + 2, pw - 4, ph - 4, (255, 255, 255))
    c.text(px + 16, py + 12, "NVIDIA, % CHANGE", 2, GREY)
    base = py + 132
    c.hline(px + 16, base, pw - 32, GREY, 1)
    # Monday +31.5% green bar, Tuesday -5.9% red bar
    c.text(px + 40, py + 28, "MON +31.5%", 2, GREEN)
    c.rect(px + 40, py + 44, 70, 88, GREEN)
    c.rect(px + 190, base, 70, 24, RED)
    c.text(px + 190, base + 28, "TUE -5.9%", 2, RED)
    return ty + 34 + 8


def draw_second_row(c, y):
    c.hline(24, y, 976, INK, 2)
    col_w = 320
    for i, story in enumerate(SECOND_ROW):
        x = 24 + i * (col_w + 8)
        if i:
            c.vline(x - 8, y + 10, 168, RULE, 1)
        c.text(x, y + 12, story["kicker"], 2, story["color"])
        hy = y + 38
        for line in wrap_text(story["headline"], 17):
            c.text(x, hy, line, 3, INK)
            hy += 26
        c.para(x, hy + 2, story["deck"], 2, 26, GREY)
    return y + 200


def draw_briefs(c, y):
    c.rect(24, y, 976, 34, INK)
    c.text(40, y + 10, "THE WORLD IN BRIEF", 2, PAPER)
    c.text(1000 - text_width("ALL DATED 24 NOVEMBER 2026", 2) - 16, y + 10,
           "ALL DATED 24 NOVEMBER 2026", 2, PAPER)
    y += 46
    cell_w = 484
    cell_h = 64
    for idx, (tag, color, headline, deck) in enumerate(BRIEFS):
        row, col = divmod(idx, 2)
        x = 24 + col * (cell_w + 8)
        cy = y + row * cell_h
        c.rect(x, cy + 4, 10, 10, color)
        c.text(x + 20, cy, tag, 2, color)
        c.text(x + 20, cy + 22, headline, 2, INK)
        c.text(x + 20, cy + 44, deck, 2, GREY)
        if row < 4:
            c.hline(x, cy + cell_h - 6, cell_w, LIGHT, 1)
    return y + 5 * cell_h


def draw_footer(c, y):
    c.hline(24, y, 976, INK, 2)
    c.text_center(512, y + 12,
                  "SOURCES: REUTERS  -  ASSOCIATED PRESS  -  INVESTOPEDIA",
                  2, GREY)


def build():
    c = Canvas(W, H, PAPER)
    draw_masthead(c)
    y = draw_lead(c, 168)
    y = draw_second_row(c, y)
    y = draw_briefs(c, y)
    draw_footer(c, y + 6)
    return c


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR") or "/output"
    os.makedirs(out_dir, exist_ok=True)
    data = png_bytes(build())
    with open(os.path.join(out_dir, "entry.png"), "wb") as f:
        f.write(data)


if __name__ == "__main__":
    main()
