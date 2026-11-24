import math
import random
import sys
import time
import tkinter as tk
import tkinter.font as tkfont
from pathlib import Path

W, H = 1280, 720
FPS_MS = 33
HERE = Path(__file__).resolve().parent

BOARD = (30, 62, 47)
CHALK = (242, 242, 232)
WOOD = (120, 76, 40)
WOOD_DARK = (78, 46, 22)
WOOD_LIGHT = (160, 110, 64)
TOP, BOTTOM, SIDE = 22, 662, 22
TRAY = 680

TITLE_START = 4.1
PORTRAIT_START, PORTRAIT_SCAN = 7.6, 3.0
MORPH, MORPH_LEN = 11.0, 2.0
QUOTE_START = 11.2
PLANES_START = 17.2


def hexc(rgb):
    return "#%02x%02x%02x" % rgb


def mix(a, b, t):
    t = max(0.0, min(1.0, t))
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def pick_font(*names):
    have = set(tkfont.families())
    return next((n for n in names if n in have), "Arial")


def draw_board(cv):
    cv.create_rectangle(0, 0, W, H, fill=hexc(WOOD), outline="")
    cv.create_rectangle(6, 6, W - 6, H - 6, outline=hexc(WOOD_LIGHT), width=2)
    cv.create_rectangle(SIDE - 3, TOP - 3, W - SIDE + 3, BOTTOM + 3, fill=hexc(WOOD_DARK), outline="")
    cv.create_rectangle(SIDE, TOP, W - SIDE, BOTTOM, fill=hexc(BOARD), outline="")
    for _ in range(16):
        x, y = random.uniform(SIDE, W - SIDE), random.uniform(TOP, BOTTOM)
        rx, ry = random.uniform(80, 260), random.uniform(30, 90)
        cv.create_oval(max(SIDE, x - rx), max(TOP, y - ry), min(W - SIDE, x + rx), min(BOTTOM, y + ry),
                       fill=hexc(mix(BOARD, CHALK, random.uniform(0.02, 0.04))), outline="")
    cv.create_rectangle(8, BOTTOM, W - 8, TRAY, fill=hexc(WOOD_LIGHT), outline="")
    cv.create_line(8, BOTTOM + 1, W - 8, BOTTOM + 1, fill=hexc(mix(WOOD_LIGHT, CHALK, 0.4)), width=2)
    cv.create_rectangle(8, TRAY, W - 8, TRAY + 4, fill=hexc(WOOD_DARK), outline="")
    for x, col in ((300, (250, 236, 150)), (338, (246, 178, 196)), (372, (170, 210, 245))):
        cv.create_rectangle(x, BOTTOM - 7, x + 28, BOTTOM, fill=hexc(col), outline="")
    for _ in range(40):
        x = random.uniform(200, 600)
        cv.create_oval(x, BOTTOM + 4, x + 2, BOTTOM + 6, fill=hexc(mix(WOOD_LIGHT, CHALK, 0.6)), outline="")
    ax, ay = 1222, BOTTOM - 17
    cv.create_oval(ax - 18, ay - 16, ax + 2, ay + 17, fill="#c8202a", outline="")
    cv.create_oval(ax - 2, ay - 16, ax + 18, ay + 17, fill="#c8202a", outline="")
    cv.create_oval(ax - 11, ay - 9, ax - 5, ay - 1, fill="#f07a7f", outline="")
    cv.create_line(ax, ay - 14, ax + 3, ay - 26, fill="#5a3a1a", width=3)
    cv.create_polygon(ax + 3, ay - 22, ax + 18, ay - 30, ax + 22, ay - 22, ax + 8, ay - 17,
                      fill="#4f9a3a", outline="", smooth=True)


class Chalk:
    REST = (430, BOTTOM - 4)

    def __init__(self, cv):
        self.cv = cv
        self.x, self.y = self.REST
        self.want = None
        self.writing = False
        self.t = 0.0
        self.shadow = cv.create_polygon(0, 0, 0, 0, fill=hexc(mix(BOARD, (0, 0, 0), 0.35)), outline="")
        self.body = cv.create_polygon(0, 0, 0, 0, fill=hexc(CHALK), outline="")
        self.tip = cv.create_polygon(0, 0, 0, 0, fill="#d8d8cc", outline="")
        self.dust = []
        for _ in range(60):
            item = cv.create_oval(0, 0, 0, 0, fill=hexc(CHALK), outline="", state="hidden")
            self.dust.append([0, 0, 0, 0, 0, item])
        self.next_dust = 0

    def go(self, x, y, writing=True):
        self.want = (x, y)
        self.writing = writing

    def update(self, t, dt):
        self.t = t
        tx, ty = self.want if self.want else self.REST
        k = 1 - math.exp(-dt * (30 if self.writing and self.want else 7))
        self.x += (tx - self.x) * k
        self.y += (ty - self.y) * k
        writing = self.writing and self.want and math.hypot(tx - self.x, ty - self.y) < 40
        bob = math.sin(t * 38) * 1.5 if writing else 0
        x, y = self.x, self.y + bob
        ang = math.radians(-35)
        dx, dy = math.cos(ang), math.sin(ang)
        nx, ny = -dy, dx
        L, w = 46, 5.5
        bx, by = x + dx * L, y + dy * L

        def quad(x0, y0, x1, y1, ww):
            return (x0 + nx * ww, y0 + ny * ww, x1 + nx * ww, y1 + ny * ww,
                    x1 - nx * ww, y1 - ny * ww, x0 - nx * ww, y0 - ny * ww)

        self.cv.coords(self.shadow, *quad(x + 6, y + 6, bx + 6, by + 6, w))
        self.cv.coords(self.body, *quad(x + dx * 6, y + dy * 6, bx, by, w))
        self.cv.coords(self.tip, *quad(x, y, x + dx * 6, y + dy * 6, w * 0.8))
        for item in (self.shadow, self.body, self.tip):
            self.cv.tag_raise(item)

        if writing:
            for _ in range(2):
                p = self.dust[self.next_dust]
                self.next_dust = (self.next_dust + 1) % len(self.dust)
                p[:5] = [x, y, random.uniform(-15, 15), random.uniform(-10, 20), random.uniform(0.6, 1.3)]
                self.cv.itemconfigure(p[5], state="normal")
        for p in self.dust:
            if p[4] <= 0:
                continue
            p[4] -= dt
            p[3] += 90 * dt
            p[0] += p[2] * dt
            p[1] += p[3] * dt
            if p[4] <= 0 or p[1] > BOTTOM:
                p[4] = 0
                self.cv.itemconfigure(p[5], state="hidden")
                continue
            self.cv.coords(p[5], p[0], p[1], p[0] + 2, p[1] + 2)
            self.cv.itemconfigure(p[5], fill=hexc(mix(BOARD, CHALK, min(1, p[4]))))
            self.cv.tag_raise(p[5])
        self.want = None


class Writer:
    def __init__(self, cv, chalk, font_name):
        self.cv, self.chalk, self.font_name = cv, chalk, font_name
        self.jobs = []

    def text(self, start, s, x, y, size, cps=14, anchor="center", color=CHALK):
        font = (self.font_name, -size)
        width = tkfont.Font(font=font).measure(s)
        left = x - width / 2 if anchor == "center" else x - width if anchor == "e" else x
        ghost = self.cv.create_text(left + 1.5, y + 1, text="", anchor="w", font=font,
                                    fill=hexc(mix(BOARD, color, 0.45)))
        main = self.cv.create_text(left, y, text="", anchor="w", font=font, fill=hexc(color))
        dur = len(s) / cps
        self.jobs.append({"kind": "text", "start": start, "end": start + dur, "s": s, "items": (ghost, main),
                          "shown": 0, "right": left, "y": y, "size": size})
        return start + dur

    def stroke(self, start, pts, dur, width=4, color=CHALK):
        cum = [0.0]
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            cum.append(cum[-1] + math.hypot(x1 - x0, y1 - y0))
        item = self.cv.create_line(0, 0, 0, 0, fill=hexc(color), width=width,
                                   capstyle="round", joinstyle="round", state="hidden")
        self.jobs.append({"kind": "stroke", "start": start, "end": start + dur, "pts": pts, "cum": cum,
                          "item": item, "width": width, "done": False})
        return start + dur

    def update(self, t, dt):
        for job in self.jobs:
            if t < job["start"] or job.get("finished"):
                continue
            p = min(1.0, (t - job["start"]) / (job["end"] - job["start"]))
            if job["kind"] == "text":
                n = int(round(p * len(job["s"])))
                if n > job["shown"]:
                    for item in job["items"]:
                        self.cv.itemconfigure(item, text=job["s"][:n])
                    job["right"] = self.cv.bbox(job["items"][1])[2]
                    job["shown"] = n
                x, y = job["right"], job["y"] + job["size"] * 0.25
            else:
                pts, cum = job["pts"], job["cum"]
                target = p * cum[-1]
                part = [pts[0]]
                for i in range(1, len(pts)):
                    if cum[i] <= target:
                        part.append(pts[i])
                    else:
                        f = (target - cum[i - 1]) / (cum[i] - cum[i - 1])
                        part.append((pts[i - 1][0] + (pts[i][0] - pts[i - 1][0]) * f,
                                     pts[i - 1][1] + (pts[i][1] - pts[i - 1][1]) * f))
                        break
                if len(part) < 2:
                    part.append(part[0])
                self.cv.coords(job["item"], *[c for pt in part for c in pt])
                self.cv.itemconfigure(job["item"], state="normal")
                x, y = part[-1]
            if p < 1:
                self.chalk.go(x, y)
            else:
                job["finished"] = True


def star_pts(cx, cy, r):
    pts = []
    for k in range(6):
        ang = -math.pi / 2 + k * 4 * math.pi / 5
        pts.append((cx + r * math.cos(ang), cy + r * math.sin(ang)))
    return pts


def heart_pts(cx, cy, s):
    pts = []
    for i in range(41):
        a = i / 40 * math.tau
        x = 16 * math.sin(a) ** 3
        y = 13 * math.cos(a) - 5 * math.cos(2 * a) - 2 * math.cos(3 * a) - math.cos(4 * a)
        pts.append((cx + x * s, cy - y * s))
    return pts


def wavy(x0, x1, y, amp=4, n=40):
    return [(x0 + (x1 - x0) * i / n, y + amp * math.sin(i / n * 9)) for i in range(n + 1)]


class Calendar:
    CW, CHT = 300, 330
    BIND = 40
    PAPER = (250, 247, 238)
    BACK = (222, 218, 204)
    RED = (200, 24, 34)
    INK = (40, 36, 34)

    DROP = (0.2, 0.9)
    PEEL = (1.5, 2.4)
    LIFT = (3.4, 3.95)

    def __init__(self, cv, cx=W / 2, top=165):
        self.cv = cv
        x0, y0 = cx - self.CW / 2, top
        x1, y1 = x0 + self.CW, y0 + self.CHT
        self.x0, self.x1 = x0, x1
        self.pt, self.pb = y0 + self.BIND, y1
        tag = ("cal",)
        bold, plain = "Segoe UI Black", "Segoe UI"

        nx, ny = cx, y0 - 46
        cv.create_line(nx, ny, x0 + 60, y0 + 4, fill="#cfc7b0", width=2, tags=tag)
        cv.create_line(nx, ny, x1 - 60, y0 + 4, fill="#cfc7b0", width=2, tags=tag)
        cv.create_oval(nx - 6, ny - 6, nx + 6, ny + 6, fill="#9a9a9a", outline="#555555", tags=tag)
        cv.create_rectangle(x0 + 8, y0 + 8, x1 + 8, y1 + 10, fill=hexc(mix(BOARD, (0, 0, 0), 0.35)),
                            outline="", tags=tag)
        for k in (6, 4, 2):
            cv.create_rectangle(x0 + k / 2, y0 + 20, x1 - k / 2, y1 + k,
                                fill=hexc(mix(self.PAPER, (0, 0, 0), 0.03 * k)),
                                outline=hexc(mix(self.PAPER, (0, 0, 0), 0.2)), tags=tag)

        cv.create_rectangle(x0, self.pt, x1, y1, fill=hexc(self.PAPER), outline="", tags=tag)
        cv.create_text(cx, self.pt + 32, text="KASIM 2026", font=(bold, -26), fill=hexc(self.RED), tags=tag)
        self.big24 = cv.create_text(cx, self.pt + 132, text="24", font=(bold, -130), fill=hexc(self.RED), tags=tag)
        cv.create_text(cx, self.pt + 222, text="Salı", font=(plain, -26), fill=hexc(self.INK), tags=tag)
        cv.create_text(cx, self.pt + 262, text="Öğretmenler Günü", font=("Segoe UI Semibold", -21),
                       fill=hexc(self.RED), tags=tag)

        self.front = cv.create_rectangle(x0, self.pt, x1, y1, fill=hexc(self.PAPER), outline="", tags=tag)
        self.texts = [
            cv.create_text(cx, self.pt + 32, text="KASIM 2026", font=(bold, -26), fill=hexc(self.RED), tags=tag),
            cv.create_text(cx, self.pt + 132, text="23", font=(bold, -130), fill=hexc(self.INK), tags=tag),
            cv.create_text(cx, self.pt + 222, text="Pazartesi", font=(plain, -26), fill=hexc(self.INK), tags=tag),
        ]

        cv.create_rectangle(x0 - 4, y0, x1 + 4, self.pt, fill="#8e1a22", outline="", tags=tag)
        cv.create_line(x0 - 4, self.pt - 3, x1 + 4, self.pt - 3, fill="#6a1016", width=3, tags=tag)
        for rx in (x0 + 60, cx, x1 - 60):
            cv.create_rectangle(rx - 5, y0 - 8, rx + 5, y0 + 16, fill="#c8c8c8", outline="#777777", tags=tag)

        self.fold_shadow = cv.create_line(0, 0, 0, 0, fill="#8a8678", width=3, state="hidden", tags=tag)
        self.flap = cv.create_polygon(0, 0, 0, 0, fill=hexc(self.BACK), outline="#b9b4a2", state="hidden")
        self.flap_pts = None
        self.fall = None

        self.offset = self._offset(0.0)
        cv.move("cal", 0, self.offset)
        self.done = False

    def _offset(self, t):
        far = -(self.pb + 80)
        a, b = self.DROP
        if t < a:
            return far
        if t < b:
            p = (t - a) / (b - a) - 1
            return far * -(p * p * (2.7 * p + 1.7))
        a, b = self.LIFT
        if t < a:
            return 0.0
        p = min(1.0, (t - a) / (b - a))
        return far * p * p

    def update(self, t, dt):
        if self.done:
            return
        cv = self.cv
        off = self._offset(t)
        if off != self.offset:
            cv.move("cal", 0, off - self.offset)
            self.offset = off

        a, b = self.PEEL
        if a <= t and self.fall is None:
            p = min(1.0, (t - a) / (b - a))
            p = p * p * (3 - 2 * p)
            pt, pb, x0, x1 = self.pt, self.pb, self.x0, self.x1
            yf = pb - p * (pb - pt)
            L = pb - yf
            c = 14 * math.sin(p * math.pi)
            cv.coords(self.front, x0, pt, x1, max(pt, yf))
            for item in self.texts:
                box = cv.bbox(item)
                if box and box[3] > yf:
                    cv.itemconfigure(item, state="hidden")
            pts = [x0, yf, x1, yf, x1 - c, yf - L, x0 + c, yf - L]
            cv.coords(self.flap, *pts)
            cv.coords(self.fold_shadow, x0, yf + 1, x1, yf + 1)
            cv.itemconfigure(self.flap, state="normal")
            cv.itemconfigure(self.fold_shadow, state="normal" if p < 1 else "hidden")
            cv.tag_raise(self.flap)
            self.flap_pts = [(pts[i], pts[i + 1]) for i in range(0, 8, 2)]
            if p >= 1:
                cv.itemconfigure(self.front, state="hidden")
                cx = sum(q[0] for q in self.flap_pts) / 4
                cy = sum(q[1] for q in self.flap_pts) / 4
                self.fall = {"t0": t, "cx": cx, "cy": cy,
                             "rel": [(x - cx, y - cy) for x, y in self.flap_pts]}

        if self.fall:
            f = self.fall
            s = t - f["t0"]
            fy = f["cy"] - 60 * s + 900 * s * s
            if fy > H + 300:
                cv.itemconfigure(self.flap, state="hidden")
            else:
                ang = 2.4 * s + 0.4 * math.sin(s * 5)
                ca, sa = math.cos(ang), math.sin(ang)
                fx = f["cx"] + 460 * s + 30 * math.sin(s * 6)
                sq = 0.55 + 0.45 * math.cos(s * 7)
                cv.coords(self.flap, *[c for rx, ry in f["rel"]
                                       for c in (fx + rx * sq * ca - ry * sa, fy + rx * sq * sa + ry * ca)])
                cv.tag_raise(self.flap)
            pulse = math.sin(min(1.0, s / 0.6) * math.pi)
            cv.itemconfigure(self.big24, font=("Segoe UI Black", -int(130 + 24 * pulse)))
            if t > self.LIFT[1] and s > 2.0:
                cv.delete("cal")
                cv.delete(self.flap)
                self.done = True


class ChalkPortrait:
    CW = 5
    BLOCK = 24
    HEAD = (0.50, 0.30, 0.34, 0.35)
    BODY_TOP, NECK = 0.55, 0.19

    @classmethod
    def brightness(cls, img, cols, rows):
        iw, ih = img.width(), img.height()
        lum = [[0.0] * cols for _ in range(rows)]
        for r in range(rows):
            for c in range(cols):
                acc = 0.0
                for fx in (0.25, 0.75):
                    for fy in (0.25, 0.75):
                        px = int((c + fx) / cols * iw)
                        py = int((r + fy) / rows * ih)
                        rgb = img.get(min(px, iw - 1), min(py, ih - 1))
                        acc += 0.299 * rgb[0] + 0.587 * rgb[1] + 0.114 * rgb[2]
                lum[r][c] = acc / 4 / 255
        sharp = [[0.0] * cols for _ in range(rows)]
        for r in range(rows):
            for c in range(cols):
                nb = [lum[rr][cc] for rr in range(max(0, r - 1), min(rows, r + 2))
                      for cc in range(max(0, c - 1), min(cols, c + 2))]
                sharp[r][c] = lum[r][c] + 1.2 * (lum[r][c] - sum(nb) / len(nb))
        hx, hy, hrx, hry = cls.HEAD
        out = {}
        for r in range(rows):
            for c in range(cols):
                u, v = (c + 0.5) / cols, (r + 0.5) / rows
                head = ((u - hx) / hrx) ** 2 + ((v - hy) / hry) ** 2
                body = abs(u - 0.5) - (cls.NECK + (v - cls.BODY_TOP) * 2.5) if v > cls.BODY_TOP else 1
                person = max(0.0, min(1.0, max((1.0 - head) / 0.2, -body / 0.04)))
                out[r, c] = (sharp[r][c], person)
        tones = sorted(l for l, p in out.values() if p > 0.5)
        n = len(tones)
        for key, (l, p) in out.items():
            lo, hi = 0, n
            while lo < hi:
                mid = (lo + hi) // 2
                if tones[mid] < l:
                    lo = mid + 1
                else:
                    hi = mid
            out[key] = (lo / n, p)
        return out

    def __init__(self, cv, chalk, path, cx, top):
        self.cv, self.chalk = cv, chalk
        self.photo = tk.PhotoImage(file=str(path))
        pw, ph = self.photo.width(), self.photo.height()
        self.x0, self.y0 = cx - pw / 2, top
        self.pw, self.ph = pw, ph
        cols, rows = pw // self.CW, ph // self.CW
        self.cols, self.rows = cols, rows
        grid = self.brightness(self.photo, cols, rows)

        x0, y0 = self.x0, self.y0
        self.paper = cv.create_rectangle(x0 - 9, y0 - 9, x0 + pw + 9, y0 + ph + 9,
                                         fill="#f4f1e8", outline="", state="hidden")
        self.tapes = []
        for tx, ty, a in ((x0 + 6, y0 - 4, -0.6), (x0 + pw - 6, y0 - 4, 0.6)):
            dx, dy = math.cos(a) * 30, math.sin(a) * 30
            nx, ny = -math.sin(a) * 10, math.cos(a) * 10
            self.tapes.append(cv.create_polygon(tx - dx - nx, ty - dy - ny, tx + dx - nx, ty + dy - ny,
                                                tx + dx + nx, ty + dy + ny, tx - dx + nx, ty - dy + ny,
                                                fill="#e2d6a8", outline="", state="hidden"))

        bs = self.BLOCK
        self.blocks = {}
        fx, fy = cx, y0 + 0.30 * ph
        far = math.hypot(pw, ph)
        for by in range(0, ph, bs):
            for bx in range(0, pw, bs):
                d = math.hypot(x0 + bx + bs / 2 - fx, y0 + by + bs / 2 - fy) / far
                when = MORPH + d * (MORPH_LEN - 0.5) * 1.5 + random.uniform(0, 0.5)
                self.blocks[by // bs, bx // bs] = [when, bx, by, []]
        self.dots = []
        for (r, c), (b, person) in grid.items():
            b *= person
            if b < 0.07:
                continue
            x = x0 + c * self.CW + self.CW / 2 + random.uniform(-1.2, 1.2)
            y = y0 + r * self.CW + self.CW / 2 + random.uniform(-1.2, 1.2)
            s = 0.5 + 2.1 * b
            col = hexc(mix(BOARD, CHALK, 0.25 + 0.75 * b))
            item = cv.create_oval(x - s, y - s, x + s, y + s, fill=col, outline="", state="hidden")
            when = PORTRAIT_START + r / rows * PORTRAIT_SCAN + random.uniform(0, 0.2)
            self.dots.append((when, item))
            key = (min(int((y - y0) // bs), (ph - 1) // bs), min(int((x - x0) // bs), (pw - 1) // bs))
            self.blocks[max(0, key[0]), max(0, key[1])][3].append(item)
        self.dots.sort()
        self.shown = 0
        self.morph = sorted(self.blocks.values(), key=lambda blk: blk[0])
        self.flashed = 0
        self.opened = 0
        self.flashes = []
        self.tiles = []
        self.framed = False

    def update(self, t, dt):
        cv = self.cv
        dots = self.dots
        while self.shown < len(dots) and dots[self.shown][0] <= t:
            cv.itemconfigure(dots[self.shown][1], state="normal")
            self.shown += 1
        if PORTRAIT_START <= t < PORTRAIT_START + PORTRAIT_SCAN:
            p = (t - PORTRAIT_START) / PORTRAIT_SCAN
            self.chalk.go(self.x0 + self.pw * (0.5 + 0.42 * math.sin(t * 11)), self.y0 + p * self.ph)

        morph = self.morph
        while self.flashed < len(morph) and morph[self.flashed][0] <= t:
            when, bx, by, items = morph[self.flashed]
            for item in items:
                cv.delete(item)
            x1, y1 = self.x0 + bx, self.y0 + by
            x2, y2 = self.x0 + min(self.pw, bx + self.BLOCK), self.y0 + min(self.ph, by + self.BLOCK)
            self.flashes.append(cv.create_rectangle(x1, y1, x2, y2, outline="",
                                                    fill=random.choice((hexc(CHALK), "#ffffff", "#e8e4c8"))))
            self.flashed += 1
        while self.opened < self.flashed and morph[self.opened][0] + 0.09 <= t:
            when, bx, by, items = morph[self.opened]
            bx2, by2 = min(self.pw, bx + self.BLOCK), min(self.ph, by + self.BLOCK)
            tile = tk.PhotoImage(width=bx2 - bx, height=by2 - by)
            tile.tk.call(tile, "copy", self.photo, "-from", bx, by, bx2, by2, "-to", 0, 0)
            self.tiles.append(tile)
            cv.create_image(self.x0 + bx, self.y0 + by, image=tile, anchor="nw")
            cv.delete(self.flashes[self.opened])
            self.opened += 1
        if self.opened == len(morph) and not self.framed:
            self.framed = True
            cv.itemconfigure(self.paper, state="normal")
            for tape in self.tapes:
                cv.itemconfigure(tape, state="normal")
                cv.tag_raise(tape)


class PaperPlanes:
    PAPER = [(252, 252, 246), (250, 238, 170), (248, 200, 214), (190, 222, 248), (204, 238, 196)]

    def __init__(self, cv, n=6):
        self.cv = cv
        self.planes = []
        for i in range(n):
            col = self.PAPER[i % len(self.PAPER)]
            p = {
                "top": cv.create_polygon(0, 0, 0, 0, fill=hexc(col), outline="", state="hidden"),
                "bot": cv.create_polygon(0, 0, 0, 0, fill=hexc(mix(col, (0, 0, 0), 0.2)), outline="", state="hidden"),
                "fold": cv.create_line(0, 0, 0, 0, fill=hexc(mix(col, (0, 0, 0), 0.35)), state="hidden"),
                "trail": [cv.create_oval(0, 0, 0, 0, fill=hexc(BOARD), outline="", state="hidden") for _ in range(14)],
                "hist": [],
            }
            self._spawn(p, delay=i * 0.55)
            self.planes.append(p)

    @staticmethod
    def _spawn(p, delay=0.0):
        p["x"], p["y"] = random.uniform(470, 820), H + 40
        p["vx"], p["vy"] = random.uniform(150, 260), -random.uniform(330, 420)
        p["wait"] = delay
        p["age"] = random.uniform(0, 10)
        p["hist"] = []

    def update(self, t, dt):
        if t < PLANES_START:
            return
        cv = self.cv
        for p in self.planes:
            if p["wait"] > 0:
                p["wait"] -= dt
                continue
            p["age"] += dt
            p["vy"] += 75 * dt
            p["vy"] += 40 * math.sin(p["age"] * 3) * dt
            p["x"] += p["vx"] * dt
            p["y"] += p["vy"] * dt
            if p["x"] > W + 90 or p["y"] < -90 or p["y"] > H + 60:
                self._spawn(p, delay=random.uniform(0.2, 1.2))
                continue
            x, y = p["x"], p["y"]
            ang = math.atan2(p["vy"], p["vx"])
            roll = 0.35 + 0.65 * abs(math.cos(p["age"] * 2.2))

            def pt(px, py):
                py *= roll
                ca, sa = math.cos(ang), math.sin(ang)
                return x + px * ca - py * sa, y + px * sa + py * ca

            nose, back, tail_l, tail_r = pt(30, 0), pt(-10, 0), pt(-18, -15), pt(-18, 15)
            cv.coords(p["top"], *nose, *tail_l, *back)
            cv.coords(p["bot"], *nose, *back, *tail_r)
            cv.coords(p["fold"], *nose, *back)
            p["hist"].insert(0, back)
            del p["hist"][len(p["trail"]) * 3:]
            for i, item in enumerate(p["trail"]):
                k = i * 3 + 3
                if k < len(p["hist"]) and SIDE < p["hist"][k][0] < W - SIDE:
                    hx, hy = p["hist"][k]
                    s = 2.2 - i * 0.12
                    cv.coords(item, hx - s, hy - s, hx + s, hy + s)
                    cv.itemconfigure(item, state="normal",
                                     fill=hexc(mix(BOARD, CHALK, 0.55 * (1 - i / len(p["trail"])))))
                else:
                    cv.itemconfigure(item, state="hidden")
            for key in ("bot", "top", "fold"):
                cv.itemconfigure(p[key], state="normal")
                cv.tag_raise(p[key])


def main():
    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass
    root = tk.Tk()
    root.title("24 Kasım Öğretmenler Günü")
    root.resizable(False, False)
    cv = tk.Canvas(root, width=W, height=H, bg=hexc(WOOD), highlightthickness=0)
    cv.pack()

    hand = pick_font("Segoe Print", "Ink Free", "Comic Sans MS")
    draw_board(cv)
    calendar = Calendar(cv)
    chalk = Chalk(cv)
    writer = Writer(cv, chalk, hand)

    portrait_path = HERE / "ataturk.png"
    layers = [calendar]
    if portrait_path.exists():
        cx = 845
        layers.append(ChalkPortrait(cv, chalk, portrait_path, 250, 52))
    else:
        cx = W / 2

    t = writer.text(TITLE_START, "24 Kasım", cx, 120, 104, cps=7)
    t = writer.text(t + 0.15, "Öğretmenler Günü", cx, 245, 66, cps=13)
    t = writer.text(t + 0.1, "Kutlu Olsun!", cx, 335, 66, cps=12)
    writer.stroke(t + 0.05, wavy(cx - 250, cx + 250, 392), 0.5, width=4)

    t = writer.text(QUOTE_START, "“Öğretmenler! Yeni nesil", cx, 462, 34, cps=17)
    t = writer.text(t + 0.05, "sizin eseriniz olacaktır.”", cx, 512, 34, cps=17)
    t = writer.text(t + 0.1, "— Mustafa Kemal Atatürk", cx + 250, 566, 24, cps=20, anchor="e",
                    color=mix(BOARD, CHALK, 0.78))

    if portrait_path.exists():
        t = writer.text(t + 0.2, "Başöğretmen", 250, 560, 40, cps=10)
        t = writer.text(t + 0.05, "Mustafa Kemal Atatürk", 250, 606, 26, cps=18,
                        color=mix(BOARD, CHALK, 0.8))

    t = writer.stroke(t + 0.15, star_pts(cx - 320, 112, 26), 0.45, width=3, color=(250, 236, 150))
    t = writer.stroke(t + 0.05, star_pts(cx + 320, 112, 26), 0.45, width=3, color=(250, 236, 150))
    t = writer.stroke(t + 0.05, heart_pts(cx - 330, 600, 1.6), 0.5, width=3, color=(246, 178, 196))
    writer.stroke(t + 0.05, heart_pts(cx + 330, 600, 1.6), 0.5, width=3, color=(246, 178, 196))

    layers += [writer, PaperPlanes(cv), chalk]
    state = {"paused": False, "last": time.perf_counter(), "t": 0.0}

    def tick():
        start = time.perf_counter()
        dt = min(0.1, start - state["last"])
        state["last"] = start
        if not state["paused"]:
            state["t"] += dt
            for layer in layers:
                layer.update(state["t"], dt)
        spent = int((time.perf_counter() - start) * 1000)
        if "--test" in sys.argv:
            print(f"{state['t']:.2f} {spent}ms", flush=True)
        root.after(max(1, FPS_MS - spent), tick)

    root.bind("<space>", lambda e: state.update(paused=not state["paused"]))
    root.bind("<Escape>", lambda e: root.destroy())

    if "--test" in sys.argv:
        root.attributes("-topmost", True)
        root.geometry("+0+0")
        root.after(300, lambda: print("ROOT", cv.winfo_rootx(), cv.winfo_rooty(), flush=True))
        root.after(24000, root.destroy)

    def start():
        state["last"] = time.perf_counter()
        tick()

    root.after(150, start)
    root.mainloop()


if __name__ == "__main__":
    main()
