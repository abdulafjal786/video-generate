"""Animated vector props. Each prop is drawn centred at (cx, cy) inside a box
of size s (design pixels); t = seconds since the prop appeared."""
import math
import os

from PIL import Image

from .canvas import ASSETS, SS, polar, smooth, mix

RED, BLUE, GOLD = 0, 1, 2


def _acc(th, i):
    return th["accents"][i % len(th["accents"])]


def _lw(s):
    return max(2.0, s * 0.035)


def bulb(cv, cx, cy, s, t, th):
    ink, lw = th["ink"], _lw(s)
    glow = 0.5 + 0.5 * math.sin(t * 5)
    gold = _acc(th, GOLD)
    for i in range(8):  # rays
        a = -90 + (i - 3.5) * 26
        p1, p2 = polar(cx, cy - s * 0.1, s * 0.36, a), polar(cx, cy - s * 0.1, s * (0.44 + 0.05 * glow), a)
        cv.line([p1, p2], gold, lw)
    cv.circle((cx, cy - s * 0.1), s * 0.24, fill=mix(gold, (255, 255, 255), 0.3 * glow), outline=ink, width=lw)
    cv.rect((cx - s * 0.11, cy + s * 0.12, cx + s * 0.11, cy + s * 0.3), fill=(170, 170, 175), outline=ink, width=lw, radius=s * 0.03)
    cv.line([(cx - s * 0.11, cy + s * 0.18), (cx + s * 0.11, cy + s * 0.18)], ink, lw * 0.6)
    cv.line([(cx - s * 0.11, cy + s * 0.24), (cx + s * 0.11, cy + s * 0.24)], ink, lw * 0.6)
    cv.line([(cx - s * 0.06, cy + s * 0.04), (cx, cy - s * 0.06), (cx + s * 0.06, cy + s * 0.04)], ink, lw * 0.6)


def question(cv, cx, cy, s, t, th):
    from .canvas import font
    wob = 6 * math.sin(t * 3)
    f = font("Caveat.ttf", s * 0.9)
    cv.text((cx + wob * 0.3, cy), "?", f, _acc(th, BLUE), anchor="mm", stroke=s * 0.012, stroke_fill=th["ink"])


def exclamation(cv, cx, cy, s, t, th):
    from .canvas import font
    f = font("Caveat.ttf", s * 0.9)
    k = 1 + 0.08 * math.sin(t * 8)
    cv.text((cx, cy), "!", font("Caveat.ttf", s * 0.9 * k), _acc(th, RED), anchor="mm", stroke=s * 0.012, stroke_fill=th["ink"])


def heart(cv, cx, cy, s, t, th):
    k = s * 0.36 * (1 + 0.08 * abs(math.sin(t * 4)))
    pts = []
    for i in range(60):
        a = 2 * math.pi * i / 60
        x = 16 * math.sin(a) ** 3
        y = -(13 * math.cos(a) - 5 * math.cos(2 * a) - 2 * math.cos(3 * a) - math.cos(4 * a))
        pts.append((cx + x * k / 16, cy + y * k / 16))
    cv.poly(pts, fill=_acc(th, RED), outline=th["ink"], width=_lw(s))


def star(cv, cx, cy, s, t, th):
    rot = t * 30
    pts = [polar(cx, cy, s * (0.42 if i % 2 == 0 else 0.18), -90 + rot + i * 36) for i in range(10)]
    cv.poly(pts, fill=_acc(th, GOLD), outline=th["ink"], width=_lw(s))


def coin(cv, cx, cy, s, t, th):
    from .canvas import font
    sq = abs(math.cos(t * 3))
    rw = s * 0.32 * max(0.15, sq)
    cv.ellipse((cx - rw, cy - s * 0.32, cx + rw, cy + s * 0.32), fill=_acc(th, GOLD), outline=th["ink"], width=_lw(s))
    if sq > 0.5:
        cv.text((cx, cy), "$", font("NotoSans.ttf", s * 0.36), th["ink"], anchor="mm")


def money(cv, cx, cy, s, t, th):
    green = (90, 170, 90)
    for i in range(3):
        y = cy + s * 0.15 - i * s * 0.12
        cv.rect((cx - s * 0.38, y - s * 0.1, cx + s * 0.38, y + s * 0.1), fill=green, outline=th["ink"], width=_lw(s))
        cv.circle((cx, y), s * 0.06, fill=None, outline=th["ink"], width=_lw(s) * 0.6)
    # falling coins
    for i in range(3):
        ph = (t * 0.9 + i / 3) % 1
        coin(cv, cx - s * 0.25 + i * s * 0.25, cy - s * 0.55 + ph * s * 0.5, s * 0.35, t + i, th)


def clock(cv, cx, cy, s, t, th):
    ink, lw = th["ink"], _lw(s)
    r = s * 0.38
    cv.circle((cx, cy), r, fill=(255, 255, 255), outline=ink, width=lw * 1.2)
    for i in range(12):
        p1, p2 = polar(cx, cy, r * 0.82, i * 30), polar(cx, cy, r * 0.92, i * 30)
        cv.line([p1, p2], ink, lw * 0.6)
    cv.line([(cx, cy), polar(cx, cy, r * 0.5, -90 + t * 40)], ink, lw)
    cv.line([(cx, cy), polar(cx, cy, r * 0.75, -90 + t * 240)], _acc(th, RED), lw * 0.8)
    cv.circle((cx, cy), lw, fill=ink)


def book(cv, cx, cy, s, t, th):
    ink, lw = th["ink"], _lw(s)
    flap = 0.15 * math.sin(t * 2)
    cv.poly([(cx, cy - s * 0.2), (cx - s * 0.42, cy - s * (0.28 + flap)), (cx - s * 0.42, cy + s * 0.22), (cx, cy + s * 0.3)],
            fill=(255, 255, 255), outline=ink, width=lw)
    cv.poly([(cx, cy - s * 0.2), (cx + s * 0.42, cy - s * 0.28), (cx + s * 0.42, cy + s * 0.22), (cx, cy + s * 0.3)],
            fill=(255, 255, 255), outline=ink, width=lw)
    for i in range(3):
        y = cy - s * 0.12 + i * s * 0.1
        cv.line([(cx + s * 0.07, y), (cx + s * 0.34, y - s * 0.03)], _acc(th, BLUE), lw * 0.6)
        cv.line([(cx - s * 0.07, y), (cx - s * 0.34, y - s * 0.03)], _acc(th, BLUE), lw * 0.6)


def phone(cv, cx, cy, s, t, th):
    ink, lw = th["ink"], _lw(s)
    cv.rect((cx - s * 0.2, cy - s * 0.38, cx + s * 0.2, cy + s * 0.38), fill=(40, 40, 46), outline=ink, width=lw, radius=s * 0.06)
    cv.rect((cx - s * 0.16, cy - s * 0.3, cx + s * 0.16, cy + s * 0.28), fill=mix(_acc(th, BLUE), (255, 255, 255), 0.5), radius=s * 0.02)
    n = int(t * 2) % 4  # notifications popping
    for i in range(n):
        cv.rect((cx - s * 0.13, cy - s * 0.25 + i * s * 0.12, cx + s * 0.13, cy - s * 0.17 + i * s * 0.12), fill=(255, 255, 255), radius=s * 0.02)


def laptop(cv, cx, cy, s, t, th):
    ink, lw = th["ink"], _lw(s)
    cv.rect((cx - s * 0.38, cy - s * 0.3, cx + s * 0.38, cy + s * 0.15), fill=(45, 48, 56), outline=ink, width=lw, radius=s * 0.03)
    cv.rect((cx - s * 0.33, cy - s * 0.25, cx + s * 0.33, cy + s * 0.1), fill=mix(_acc(th, BLUE), (255, 255, 255), 0.55))
    for i in range(3):
        L = 0.15 + 0.4 * ((t * 0.7 + i * 0.3) % 1)
        cv.line([(cx - s * 0.28, cy - s * 0.17 + i * s * 0.09), (cx - s * 0.28 + s * L, cy - s * 0.17 + i * s * 0.09)], ink, lw * 0.6)
    cv.poly([(cx - s * 0.42, cy + s * 0.15), (cx + s * 0.42, cy + s * 0.15), (cx + s * 0.48, cy + s * 0.24), (cx - s * 0.48, cy + s * 0.24)],
            fill=(180, 182, 190), outline=ink, width=lw)


def chart(cv, cx, cy, s, t, th):
    ink, lw = th["ink"], _lw(s)
    x0, y0 = cx - s * 0.42, cy + s * 0.35
    cv.line([(x0, cy - s * 0.42), (x0, y0), (cx + s * 0.45, y0)], ink, lw)
    hs = [0.25, 0.4, 0.55, 0.75]
    for i, h in enumerate(hs):
        g = smooth((t - i * 0.15) / 0.5)
        bx = x0 + s * 0.08 + i * s * 0.2
        cv.rect((bx, y0 - s * h * g, bx + s * 0.13, y0), fill=_acc(th, i % 3), outline=ink, width=lw * 0.7)
    g = smooth((t - 0.6) / 0.6)
    if g > 0:
        cv.line([(x0 + s * 0.1, y0 - s * 0.3), (x0 + s * 0.1 + s * 0.7 * g, y0 - s * 0.3 - s * 0.5 * g)], _acc(th, RED), lw * 1.2)


def _arrow(cv, cx, cy, s, t, th, up=True):
    ink, lw = th["ink"], _lw(s)
    g = smooth(t / 0.6)
    col = (60, 170, 90) if up else _acc(th, RED)
    sgn = -1 if up else 1
    x1, y1 = cx - s * 0.38, cy - sgn * s * 0.3
    x2, y2 = cx - s * 0.38 + s * 0.76 * g, cy - sgn * s * 0.3 + sgn * s * 0.6 * g
    mid = ((x1 + x2) / 2, (y1 + y2) / 2 + sgn * s * 0.08)
    cv.line([(x1, y1), mid, (x2, y2)], col, lw * 2.2)
    ang = math.degrees(math.atan2(y2 - mid[1], x2 - mid[0]))
    cv.poly([polar(x2, y2, s * 0.14, ang), polar(x2, y2, s * 0.12, ang + 140), polar(x2, y2, s * 0.12, ang - 140)], fill=col)


def arrow_up(cv, cx, cy, s, t, th):
    _arrow(cv, cx, cy, s, t, th, True)


def arrow_down(cv, cx, cy, s, t, th):
    _arrow(cv, cx, cy, s, t, th, False)


def globe(cv, cx, cy, s, t, th):
    ink, lw = th["ink"], _lw(s)
    r = s * 0.38
    cv.circle((cx, cy), r, fill=mix(_acc(th, BLUE), (255, 255, 255), 0.35), outline=ink, width=lw)
    off = (t * 0.25) % 1
    for k in range(3):
        x = cx - r + ((off + k / 3) % 1) * 2 * r
        wdt = r * 0.3 * math.sin(math.pi * (x - cx + r) / (2 * r))
        if wdt > 2:
            cv.ellipse((x - wdt, cy - r * 0.45, x + wdt * 0.6, cy + r * 0.1), fill=(110, 180, 100))
    cv.ellipse((cx - r * 0.45, cy - r, cx + r * 0.45, cy + r), outline=ink, width=lw * 0.5)
    cv.line([(cx - r, cy), (cx + r, cy)], ink, lw * 0.5)


def rocket(cv, cx, cy, s, t, th):
    ink, lw = th["ink"], _lw(s)
    y = cy - s * 0.2 * smooth((t - 0.8) / 1.5) - 2 * math.sin(t * 20)
    for i in range(4):  # flame
        fl = s * (0.12 + 0.08 * abs(math.sin(t * 15 + i)))
        cv.circle((cx + (i - 1.5) * s * 0.03, y + s * 0.38 + fl * 0.5), fl * 0.6, fill=_acc(th, GOLD if i % 2 else RED))
    cv.poly([(cx, y - s * 0.45), (cx + s * 0.15, y - s * 0.2), (cx + s * 0.15, y + s * 0.32), (cx - s * 0.15, y + s * 0.32), (cx - s * 0.15, y - s * 0.2)],
            fill=(245, 245, 248), outline=ink, width=lw)
    cv.poly([(cx - s * 0.15, y + s * 0.1), (cx - s * 0.3, y + s * 0.36), (cx - s * 0.15, y + s * 0.32)], fill=_acc(th, RED), outline=ink, width=lw)
    cv.poly([(cx + s * 0.15, y + s * 0.1), (cx + s * 0.3, y + s * 0.36), (cx + s * 0.15, y + s * 0.32)], fill=_acc(th, RED), outline=ink, width=lw)
    cv.circle((cx, y - s * 0.08), s * 0.07, fill=_acc(th, BLUE), outline=ink, width=lw * 0.7)


def cloud(cv, cx, cy, s, t, th, color=(255, 255, 255)):
    ink, lw = th["ink"], _lw(s)
    dx = s * 0.04 * math.sin(t * 1.5)
    bumps = [(-0.22, 0.02, 0.18), (0.0, -0.08, 0.24), (0.22, 0.0, 0.18), (0.05, 0.08, 0.2), (-0.12, 0.1, 0.16)]
    for bx, by, br in bumps:
        cv.circle((cx + dx + bx * s, cy + by * s), br * s + lw / 2, fill=ink)
    for bx, by, br in bumps:
        cv.circle((cx + dx + bx * s, cy + by * s), br * s - lw / 2, fill=color)


def rain(cv, cx, cy, s, t, th):
    for i in range(7):
        ph = (t * 1.6 + i * 0.37) % 1
        x = cx - s * 0.3 + i * s * 0.1
        y = cy + s * 0.05 + ph * s * 0.45
        cv.line([(x, y), (x - s * 0.02, y + s * 0.07)], _acc(th, BLUE), _lw(s) * 0.9)
    cloud(cv, cx, cy - s * 0.18, s * 0.9, t, th, color=(200, 205, 215))


def sun(cv, cx, cy, s, t, th):
    ink, lw = th["ink"], _lw(s)
    gold = _acc(th, GOLD)
    for i in range(10):
        a = i * 36 + t * 25
        cv.line([polar(cx, cy, s * 0.3, a), polar(cx, cy, s * 0.43, a)], gold, lw * 1.2)
    cv.circle((cx, cy), s * 0.24, fill=gold, outline=ink, width=lw)


def moon(cv, cx, cy, s, t, th):
    ink, lw = th["ink"], _lw(s)
    cv.circle((cx, cy), s * 0.3, fill=(250, 235, 160), outline=ink, width=lw)
    cv.circle((cx + s * 0.13, cy - s * 0.08), s * 0.26, fill=th["bg"])
    for i in range(3):
        tw = abs(math.sin(t * 2 + i))
        star(cv, cx - s * 0.3 + i * s * 0.32, cy - s * 0.35 + (i % 2) * s * 0.6, s * 0.18 * (0.7 + 0.3 * tw), 0, th)


def tree(cv, cx, cy, s, t, th):
    ink, lw = th["ink"], _lw(s)
    sway = 3 * math.sin(t * 1.5)
    cv.rect((cx - s * 0.06, cy, cx + s * 0.06, cy + s * 0.42), fill=(140, 95, 60), outline=ink, width=lw)
    cv.circle((cx + sway, cy - s * 0.12), s * 0.3, fill=(100, 175, 90), outline=ink, width=lw)
    cv.circle((cx - s * 0.18 + sway, cy + s * 0.02), s * 0.18, fill=(90, 160, 80), outline=ink, width=lw)
    cv.circle((cx + s * 0.18 + sway, cy + s * 0.02), s * 0.18, fill=(90, 160, 80), outline=ink, width=lw)


def house(cv, cx, cy, s, t, th):
    ink, lw = th["ink"], _lw(s)
    cv.rect((cx - s * 0.32, cy - s * 0.05, cx + s * 0.32, cy + s * 0.4), fill=(250, 240, 220), outline=ink, width=lw)
    cv.poly([(cx - s * 0.42, cy - s * 0.02), (cx, cy - s * 0.4), (cx + s * 0.42, cy - s * 0.02)], fill=_acc(th, RED), outline=ink, width=lw)
    cv.rect((cx - s * 0.08, cy + s * 0.15, cx + s * 0.08, cy + s * 0.4), fill=(150, 100, 70), outline=ink, width=lw)
    win = (255, 225, 120) if int(t * 1.2) % 2 else (200, 225, 245)
    cv.rect((cx + s * 0.13, cy + s * 0.03, cx + s * 0.26, cy + s * 0.15), fill=win, outline=ink, width=lw * 0.7)


def gear(cv, cx, cy, s, t, th):
    ink, lw = th["ink"], _lw(s)
    rot = t * 60
    pts = []
    for i in range(16):
        r = s * (0.4 if (i // 2) % 2 == 0 else 0.3)
        pts.append(polar(cx, cy, r, rot + i * 22.5))
    cv.poly(pts, fill=(170, 175, 185), outline=ink, width=lw)
    cv.circle((cx, cy), s * 0.12, fill=th["bg"], outline=ink, width=lw)


def trophy(cv, cx, cy, s, t, th):
    ink, lw = th["ink"], _lw(s)
    gold = _acc(th, GOLD)
    cv.arc((cx - s * 0.24, cy - s * 0.12), s * 0.12, 90, 270, ink, lw)
    cv.arc((cx + s * 0.24, cy - s * 0.12), s * 0.12, 270, 90, ink, lw)
    cv.poly([(cx - s * 0.26, cy - s * 0.32), (cx + s * 0.26, cy - s * 0.32), (cx + s * 0.18, cy + s * 0.02), (cx, cy + s * 0.1), (cx - s * 0.18, cy + s * 0.02)],
            fill=gold, outline=ink, width=lw)
    cv.rect((cx - s * 0.05, cy + s * 0.08, cx + s * 0.05, cy + s * 0.25), fill=gold, outline=ink, width=lw)
    cv.rect((cx - s * 0.2, cy + s * 0.25, cx + s * 0.2, cy + s * 0.36), fill=(120, 80, 50), outline=ink, width=lw)
    tw = abs(math.sin(t * 3))
    star(cv, cx + s * 0.3, cy - s * 0.4, s * 0.2 * tw, 0, th)


def brain(cv, cx, cy, s, t, th):
    ink, lw = th["ink"], _lw(s)
    pink = (240, 160, 180)
    pulse = 1 + 0.04 * math.sin(t * 4)
    for bx, by, br in [(-0.15, -0.08, 0.2), (0.1, -0.12, 0.22), (0.2, 0.06, 0.18), (-0.18, 0.1, 0.17), (0.02, 0.1, 0.2)]:
        cv.circle((cx + bx * s, cy + by * s), br * s * pulse, fill=pink, outline=ink, width=lw)
    cv.line([(cx, cy - s * 0.3), (cx - s * 0.04, cy), (cx + s * 0.02, cy + s * 0.28)], ink, lw * 0.8)
    for i in range(3):  # sparks
        ph = (t * 1.5 + i / 3) % 1
        p = polar(cx, cy, s * (0.35 + 0.15 * ph), -150 + i * 60)
        cv.circle(p, s * 0.03 * (1 - ph), fill=_acc(th, GOLD))


def target(cv, cx, cy, s, t, th):
    ink, lw = th["ink"], _lw(s)
    for i, r in enumerate([0.4, 0.28, 0.16]):
        cv.circle((cx, cy), s * r, fill=_acc(th, RED) if i % 2 == 0 else (255, 255, 255), outline=ink, width=lw)
    g = smooth(t / 0.5)
    ax = cx + s * 0.6 * (1 - g)
    cv.line([(ax, cy - s * 0.0), (ax + s * 0.35, cy - s * 0.18)], ink, lw * 1.2)
    cv.poly([polar(ax, cy, s * 0.08, 0), polar(ax, cy, s * 0.08, 120), polar(ax, cy, s * 0.08, 240)], fill=ink)


def check(cv, cx, cy, s, t, th):
    g = smooth(t / 0.5)
    pts = [(cx - s * 0.3, cy), (cx - s * 0.08, cy + s * 0.25), (cx + s * 0.35, cy - s * 0.3)]
    cv.circle((cx, cy), s * 0.42, fill=(225, 245, 228), outline=(60, 160, 80), width=_lw(s))
    if g < 0.5:
        k = g / 0.5
        cv.line([pts[0], (pts[0][0] + (pts[1][0] - pts[0][0]) * k, pts[0][1] + (pts[1][1] - pts[0][1]) * k)], (60, 160, 80), _lw(s) * 2.5)
    else:
        k = (g - 0.5) / 0.5
        cv.line([pts[0], pts[1], (pts[1][0] + (pts[2][0] - pts[1][0]) * k, pts[1][1] + (pts[2][1] - pts[1][1]) * k)], (60, 160, 80), _lw(s) * 2.5)


def cross(cv, cx, cy, s, t, th):
    red = _acc(th, RED)
    g = smooth(t / 0.4)
    cv.circle((cx, cy), s * 0.42, fill=(252, 228, 228), outline=red, width=_lw(s))
    d = s * 0.2 * g
    cv.line([(cx - d, cy - d), (cx + d, cy + d)], red, _lw(s) * 2.5)
    cv.line([(cx + d, cy - d), (cx - d, cy + d)], red, _lw(s) * 2.5)


def warning(cv, cx, cy, s, t, th):
    from .canvas import font
    blink = 0.6 + 0.4 * abs(math.sin(t * 4))
    cv.poly([(cx, cy - s * 0.38), (cx + s * 0.42, cy + s * 0.34), (cx - s * 0.42, cy + s * 0.34)],
            fill=mix((255, 255, 255), _acc(th, GOLD), blink), outline=th["ink"], width=_lw(s) * 1.3)
    cv.text((cx, cy + s * 0.06), "!", font("NotoSans.ttf", s * 0.42), th["ink"], anchor="mm")


def battery(cv, cx, cy, s, t, th):
    ink, lw = th["ink"], _lw(s)
    lvl = (t * 0.5) % 1
    cv.rect((cx - s * 0.38, cy - s * 0.18, cx + s * 0.32, cy + s * 0.18), fill=(255, 255, 255), outline=ink, width=lw, radius=s * 0.04)
    cv.rect((cx + s * 0.32, cy - s * 0.07, cx + s * 0.4, cy + s * 0.07), fill=ink)
    col = (60, 170, 90) if lvl > 0.3 else _acc(th, RED)
    cv.rect((cx - s * 0.33, cy - s * 0.13, cx - s * 0.33 + s * 0.6 * max(0.05, lvl), cy + s * 0.13), fill=col)


def calendar(cv, cx, cy, s, t, th):
    from .canvas import font
    ink, lw = th["ink"], _lw(s)
    cv.rect((cx - s * 0.36, cy - s * 0.32, cx + s * 0.36, cy + s * 0.36), fill=(255, 255, 255), outline=ink, width=lw, radius=s * 0.04)
    cv.rect((cx - s * 0.36, cy - s * 0.32, cx + s * 0.36, cy - s * 0.14), fill=_acc(th, RED), outline=ink, width=lw, radius=s * 0.04)
    day = 1 + int(t * 2) % 30
    cv.text((cx, cy + s * 0.11), str(day), font("NotoSans.ttf", s * 0.3), ink, anchor="mm")


def magnifier(cv, cx, cy, s, t, th):
    ink, lw = th["ink"], _lw(s)
    dx, dy = s * 0.08 * math.sin(t * 2), s * 0.05 * math.cos(t * 2)
    c = (cx - s * 0.08 + dx, cy - s * 0.08 + dy)
    cv.line([(c[0] + s * 0.18, c[1] + s * 0.18), (c[0] + s * 0.42, c[1] + s * 0.42)], (120, 80, 50), lw * 3)
    cv.circle(c, s * 0.25, fill=mix(_acc(th, BLUE), (255, 255, 255), 0.75), outline=ink, width=lw * 1.4)


def gift(cv, cx, cy, s, t, th):
    ink, lw = th["ink"], _lw(s)
    hop = abs(math.sin(t * 3)) * s * 0.05
    cy -= hop
    cv.rect((cx - s * 0.32, cy - s * 0.1, cx + s * 0.32, cy + s * 0.35), fill=_acc(th, RED), outline=ink, width=lw)
    cv.rect((cx - s * 0.36, cy - s * 0.22, cx + s * 0.36, cy - s * 0.1), fill=_acc(th, RED), outline=ink, width=lw)
    cv.rect((cx - s * 0.05, cy - s * 0.22, cx + s * 0.05, cy + s * 0.35), fill=_acc(th, GOLD))
    cv.ellipse((cx - s * 0.22, cy - s * 0.38, cx, cy - s * 0.22), outline=ink, width=lw)
    cv.ellipse((cx, cy - s * 0.38, cx + s * 0.22, cy - s * 0.22), outline=ink, width=lw)


def music(cv, cx, cy, s, t, th):
    ink, lw = th["ink"], _lw(s)
    for i in range(2):
        ox = cx - s * 0.18 + i * s * 0.3
        oy = cy + s * 0.05 * math.sin(t * 4 + i)
        cv.ellipse((ox - s * 0.12, oy + s * 0.12, ox + s * 0.04, oy + s * 0.26), fill=ink)
        cv.line([(ox + s * 0.03, oy + s * 0.18), (ox + s * 0.03, oy - s * 0.25)], ink, lw)
    cv.line([(cx - s * 0.15 + s * 0.03, cy - s * 0.25), (cx + s * 0.15 + s * 0.03, cy - s * 0.3)], ink, lw * 2)


def fire(cv, cx, cy, s, t, th):
    for k, (col, sc) in enumerate([(_acc(th, RED), 1.0), (_acc(th, GOLD), 0.6)]):
        pts = []
        r = s * 0.3 * sc
        for i in range(40):
            a = 2 * math.pi * i / 40
            wob = 1 + 0.12 * math.sin(t * 10 + i * 0.9) * math.sin(a / 2)
            x = cx + r * math.sin(a) * math.sin(a / 2) * wob
            y = cy + s * 0.38 - r - r * 1.25 * math.cos(a) * (1 if math.cos(a) > 0 else 0.75)
            pts.append((x, y))
        cv.poly(pts, fill=col, outline=th["ink"] if k == 0 else None, width=_lw(s))


def drop(cv, cx, cy, s, t, th):
    ink, lw = th["ink"], _lw(s)
    y = cy + s * 0.04 * math.sin(t * 3)
    pts = [(cx, y - s * 0.38)]
    for i in range(0, 181, 15):
        a = math.radians(i)
        pts.append((cx + math.cos(a) * s * 0.24, y + s * 0.08 + math.sin(a) * s * 0.24))
    cv.poly(pts, fill=_acc(th, BLUE), outline=ink, width=lw)


def lightning(cv, cx, cy, s, t, th):
    flash = int(t * 6) % 3 != 0
    col = _acc(th, GOLD) if flash else (255, 255, 255)
    cv.poly([(cx + s * 0.08, cy - s * 0.42), (cx - s * 0.22, cy + s * 0.04), (cx - s * 0.02, cy + s * 0.04), (cx - s * 0.1, cy + s * 0.42),
             (cx + s * 0.24, cy - s * 0.08), (cx + s * 0.03, cy - s * 0.08)], fill=col, outline=th["ink"], width=_lw(s))


def car(cv, cx, cy, s, t, th):
    ink, lw = th["ink"], _lw(s)
    bump = s * 0.015 * math.sin(t * 20)
    cy += bump
    cv.rect((cx - s * 0.42, cy - s * 0.05, cx + s * 0.42, cy + s * 0.18), fill=_acc(th, RED), outline=ink, width=lw, radius=s * 0.06)
    cv.poly([(cx - s * 0.22, cy - s * 0.05), (cx - s * 0.12, cy - s * 0.25), (cx + s * 0.16, cy - s * 0.25), (cx + s * 0.26, cy - s * 0.05)],
            fill=mix(_acc(th, BLUE), (255, 255, 255), 0.6), outline=ink, width=lw)
    for wx in (-0.24, 0.24):
        c = (cx + wx * s, cy + s * 0.2)
        cv.circle(c, s * 0.1, fill=(50, 50, 55), outline=ink, width=lw)
        cv.line([c, polar(c[0], c[1], s * 0.08, t * 720)], (200, 200, 200), lw * 0.6)


def draw_bike(cv, x, ground, s, t, th, speed):
    """Motorbike facing right, wheels on `ground`, centred on x. s = character height.

    speed: road speed in px/s (spins the wheels). Returns the rider seat, pillion seat and grip points.
    """
    ink = th["ink"]
    lw = max(2.0, s * 0.012)
    line_art = th["mode"] == "line"
    tank = th["bg"] if line_art else th.get("bike", _acc(th, GOLD))
    steel, dark, chrome = (150, 154, 162), (52, 52, 58), (214, 218, 224)
    if line_art:
        steel, dark, chrome = th["bg"], ink, th["bg"]
    r = s * 0.2
    rear, front = (x - s * 0.47, ground - r), (x + s * 0.47, ground - r)
    dy = s * 0.006 * math.sin(t * 31)                                   # engine/road bounce
    seat_y = ground - r * 2.55 + dy

    def wheel(c):
        cv.circle(c, r, fill=(36, 36, 40) if not line_art else th["bg"], outline=ink, width=lw)
        cv.circle(c, r * 0.68, fill=steel, outline=ink, width=lw * 0.7)
        a0 = math.degrees(t * speed / r)
        for k in range(6):
            cv.line([c, polar(c[0], c[1], r * 0.66, a0 + k * 60)], ink, lw * 0.5)
        cv.circle(c, r * 0.16, fill=chrome, outline=ink, width=lw * 0.6)

    wheel(rear)
    wheel(front)
    # frame, swingarm, exhaust, engine
    eng = (x - s * 0.06, ground - r * 1.35 + dy)
    cv.line([rear, eng], dark, lw * 2.2)
    cv.line([(x - s * 0.18, ground - r * 0.75 + dy), (x - s * 0.62, ground - r * 1.05 + dy)], ink, lw * 3.2)
    cv.line([(x - s * 0.18, ground - r * 0.75 + dy), (x - s * 0.62, ground - r * 1.05 + dy)], chrome, lw * 2.0)
    cv.rect((eng[0] - s * 0.15, eng[1] - r * 0.6, eng[0] + s * 0.12, eng[1] + r * 0.55), fill=steel, outline=ink, width=lw, radius=s * 0.03)
    for k in range(4):
        fy = eng[1] - r * 0.4 + k * r * 0.25
        cv.line([(eng[0] - s * 0.12, fy), (eng[0] + s * 0.09, fy)], ink, lw * 0.5)
    # fork + handlebar + headlight
    head = (x + s * 0.36, seat_y - s * 0.06)
    cv.line([front, head], ink, lw * 2.6)
    cv.line([front, head], chrome, lw * 1.4)
    grip = (head[0] - s * 0.08, head[1] - s * 0.1)
    cv.line([head, grip], ink, lw * 1.6)
    if th["bg"] and sum(th["bg"]) < 250 or th.get("world") == "toon":
        cv.poly([(head[0] + s * 0.1, head[1]), (head[0] + s * 0.9, head[1] - s * 0.12), (head[0] + s * 0.9, head[1] + s * 0.22)],
                fill=(255, 240, 160, 70))
    cv.circle((head[0] + s * 0.07, head[1] + s * 0.01), s * 0.045, fill=(255, 246, 200), outline=ink, width=lw)
    # fenders
    cv.arc(rear, r * 1.12, 180, 290, ink, lw * 2.4)
    cv.arc(rear, r * 1.12, 182, 288, tank, lw * 1.2)
    cv.arc(front, r * 1.12, 220, 320, ink, lw * 2.4)
    cv.arc(front, r * 1.12, 222, 318, tank, lw * 1.2)
    # seat + tank + side cover
    cv.poly([(x - s * 0.5, seat_y + s * 0.02), (x - s * 0.46, seat_y - s * 0.04), (x + s * 0.06, seat_y - s * 0.035),
             (x + s * 0.08, seat_y + s * 0.03), (x - s * 0.48, seat_y + s * 0.05)], fill=dark if not line_art else th["bg"], outline=ink, width=lw)
    cv.poly([(x - s * 0.18, seat_y + s * 0.03), (x + s * 0.02, seat_y + s * 0.03), (x - s * 0.04, seat_y + s * 0.12), (x - s * 0.2, seat_y + s * 0.1)],
            fill=steel, outline=ink, width=lw * 0.8)
    cv.poly([(x + s * 0.04, seat_y + s * 0.03), (x + s * 0.06, seat_y - s * 0.07), (x + s * 0.2, seat_y - s * 0.09),
             (x + s * 0.33, seat_y - s * 0.05), (x + s * 0.3, seat_y + s * 0.05), (x + s * 0.1, seat_y + s * 0.07)],
            fill=tank, outline=ink, width=lw)
    cv.arc((x + s * 0.17, seat_y - s * 0.02), s * 0.06, 200, 300, (255, 255, 255), lw * 0.8)  # shine
    return {"seat": (x - s * 0.08, seat_y - s * 0.03), "pillion": (x - s * 0.36, seat_y - s * 0.03), "grip": grip,
            "peg": (x - s * 0.08, ground - r * 0.95 + dy)}


def draw_scooter(cv, x, ground, s, t, th, speed):
    """Red step-through scooter facing right; same arguments and return value as draw_bike."""
    ink = th["ink"]
    lw = max(2.0, s * 0.012)
    red, dark, chrome = (208, 44, 46), (46, 42, 46), (214, 218, 224)
    r = s * 0.14
    rear, front = (x - s * 0.4, ground - r), (x + s * 0.46, ground - r)
    dy = s * 0.006 * math.sin(t * 31)
    seat_y = ground - s * 0.5 + dy
    floor = ground - r * 1.2 + dy

    def wheel(c):
        cv.circle(c, r, fill=(36, 36, 40), outline=ink, width=lw)
        cv.circle(c, r * 0.55, fill=chrome, outline=ink, width=lw * 0.7)
        a0 = math.degrees(t * speed / r)
        for k in range(4):
            cv.line([c, polar(c[0], c[1], r * 0.5, a0 + k * 90)], ink, lw * 0.5)

    wheel(rear)
    wheel(front)
    head = (x + s * 0.36, seat_y - s * 0.1)
    cv.line([front, head], ink, lw * 2.6)
    cv.line([front, head], chrome, lw * 1.4)
    cv.poly([(x - s * 0.58, seat_y + s * 0.04), (x - s * 0.06, seat_y + s * 0.04), (x + s * 0.03, floor - s * 0.03), (x + s * 0.24, floor - s * 0.03),
             (x + s * 0.3, seat_y - s * 0.08), (x + s * 0.39, seat_y - s * 0.08), (x + s * 0.37, floor + s * 0.05), (x - s * 0.08, floor + s * 0.05),
             (x - s * 0.2, ground - r * 0.72), (x - s * 0.55, ground - r * 0.9), (x - s * 0.6, seat_y + s * 0.16)], fill=red, outline=ink, width=lw)
    cv.arc((x + s * 0.34, seat_y + s * 0.1), s * 0.08, 200, 300, (255, 255, 255), lw * 0.8)  # shine
    cv.arc(front, r * 1.14, 200, 340, ink, lw * 2.6)
    cv.arc(front, r * 1.14, 202, 338, red, lw * 1.4)
    grip = (head[0] - s * 0.08, head[1] - s * 0.08)
    cv.line([head, grip], ink, lw * 1.6)
    cv.poly([(head[0] + s * 0.1, head[1]), (head[0] + s * 0.9, head[1] - s * 0.12), (head[0] + s * 0.9, head[1] + s * 0.22)], fill=(255, 240, 160, 70))
    cv.circle((head[0] + s * 0.06, head[1]), s * 0.05, fill=(255, 246, 200), outline=ink, width=lw)
    cv.poly([(x - s * 0.56, seat_y + s * 0.03), (x - s * 0.53, seat_y - s * 0.04), (x - s * 0.04, seat_y - s * 0.035),
             (x - s * 0.02, seat_y + s * 0.03)], fill=dark, outline=ink, width=lw)
    return {"seat": (x - s * 0.08, seat_y - s * 0.03), "pillion": (x - s * 0.36, seat_y - s * 0.03), "grip": grip,
            "peg": (x + s * 0.1, floor)}


def mail(cv, cx, cy, s, t, th):
    ink, lw = th["ink"], _lw(s)
    cv.rect((cx - s * 0.38, cy - s * 0.24, cx + s * 0.38, cy + s * 0.26), fill=(255, 255, 255), outline=ink, width=lw, radius=s * 0.03)
    cv.line([(cx - s * 0.38, cy - s * 0.22), (cx, cy + s * 0.05), (cx + s * 0.38, cy - s * 0.22)], ink, lw)
    cv.circle((cx + s * 0.35, cy - s * 0.25), s * 0.09 * (1 + 0.15 * math.sin(t * 6)), fill=_acc(th, RED))


def lock(cv, cx, cy, s, t, th):
    ink, lw = th["ink"], _lw(s)
    open_k = smooth((t - 1.0) / 0.4) * s * 0.1
    cv.arc((cx, cy - s * 0.08 - open_k), s * 0.18, 180, 360, ink, lw * 1.6)
    cv.line([(cx - s * 0.18, cy - s * 0.08 - open_k), (cx - s * 0.18, cy - open_k * 0)], ink, lw * 1.6)
    cv.line([(cx + s * 0.18, cy - s * 0.08 - open_k), (cx + s * 0.18, cy - s * 0.02)], ink, lw * 1.6)
    cv.rect((cx - s * 0.28, cy - s * 0.04, cx + s * 0.28, cy + s * 0.36), fill=_acc(th, GOLD), outline=ink, width=lw, radius=s * 0.04)
    cv.circle((cx, cy + s * 0.14), s * 0.05, fill=ink)


def key(cv, cx, cy, s, t, th):
    ink, lw = th["ink"], _lw(s)
    rot = 10 * math.sin(t * 2)
    c = polar(cx, cy, s * 0.22, 180 + rot)
    cv.circle(c, s * 0.14, fill=_acc(th, GOLD), outline=ink, width=lw)
    e = polar(cx, cy, s * 0.36, rot)
    cv.line([c, e], ink, lw * 2.2)
    for d in (0.18, 0.28):
        p = polar(cx, cy, s * d, rot)
        cv.line([p, (p[0], p[1] + s * 0.1)], ink, lw * 1.8)


def people(cv, cx, cy, s, t, th):
    from .stickman import make_pose, draw_stickman
    for i in range(3):
        x = cx + (i - 1) * s * 0.3
        pose = make_pose("cheer" if i == 1 else "wave", t + i * 0.3)
        draw_stickman(cv, x, cy + s * 0.42, s * 0.62, pose, 1 if i < 2 else -1, th, {"mood": "happy"})


def plant(cv, cx, cy, s, t, th):
    ink, lw = th["ink"], _lw(s)
    g = smooth(t / 1.2)
    cv.poly([(cx - s * 0.2, cy + s * 0.12), (cx + s * 0.2, cy + s * 0.12), (cx + s * 0.15, cy + s * 0.4), (cx - s * 0.15, cy + s * 0.4)],
            fill=(200, 110, 70), outline=ink, width=lw)
    top = cy + s * 0.12 - s * 0.45 * g
    cv.line([(cx, cy + s * 0.12), (cx, top)], (70, 150, 70), lw * 1.3)
    for i, side in enumerate((-1, 1, -1)):
        k = smooth((g - 0.3 - i * 0.2) / 0.3)
        if k > 0:
            ly = cy + s * 0.05 - i * s * 0.13
            cv.ellipse((cx, ly - s * 0.06 * k, cx + side * s * 0.2 * k, ly + s * 0.04 * k), fill=(100, 180, 90), outline=ink, width=lw * 0.6)


def apple(cv, cx, cy, s, t, th):
    ink, lw = th["ink"], _lw(s)
    cv.circle((cx - s * 0.1, cy + s * 0.05), s * 0.25, fill=_acc(th, RED), outline=ink, width=lw)
    cv.circle((cx + s * 0.1, cy + s * 0.05), s * 0.25, fill=_acc(th, RED), outline=ink, width=lw)
    cv.circle((cx - s * 0.1, cy + s * 0.05), s * 0.25 - lw, fill=_acc(th, RED))
    cv.line([(cx, cy - s * 0.18), (cx + s * 0.03, cy - s * 0.32)], (120, 80, 50), lw * 1.2)
    cv.ellipse((cx + s * 0.03, cy - s * 0.34, cx + s * 0.2, cy - s * 0.24), fill=(90, 170, 80), outline=ink, width=lw * 0.6)


def graduation(cv, cx, cy, s, t, th):
    ink, lw = th["ink"], _lw(s)
    tilt = 3 * math.sin(t * 2)
    cv.poly([(cx - s * 0.42, cy - s * 0.08 + tilt), (cx, cy - s * 0.28), (cx + s * 0.42, cy - s * 0.08 - tilt), (cx, cy + s * 0.1)],
            fill=(40, 42, 50), outline=ink, width=lw)
    cv.poly([(cx - s * 0.22, cy + s * 0.02), (cx + s * 0.22, cy + s * 0.02), (cx + s * 0.2, cy + s * 0.25), (cx - s * 0.2, cy + s * 0.25)], fill=(40, 42, 50), outline=ink, width=lw)
    sw = s * 0.04 * math.sin(t * 3)
    cv.line([(cx, cy - s * 0.1), (cx + s * 0.32, cy - s * 0.02), (cx + s * 0.32 + sw, cy + s * 0.22)], _acc(th, GOLD), lw * 0.9)


def flag(cv, cx, cy, s, t, th):
    ink, lw = th["ink"], _lw(s)
    cv.line([(cx - s * 0.25, cy + s * 0.42), (cx - s * 0.25, cy - s * 0.4)], ink, lw * 1.3)
    pts_top = [(cx - s * 0.25 + i * s * 0.1, cy - s * 0.38 + s * 0.04 * math.sin(t * 5 + i)) for i in range(6)]
    pts_bot = [(x, y + s * 0.3) for x, y in pts_top][::-1]
    cv.poly(pts_top + pts_bot, fill=_acc(th, RED), outline=ink, width=lw)


def mountain(cv, cx, cy, s, t, th):
    ink, lw = th["ink"], _lw(s)
    cv.poly([(cx - s * 0.45, cy + s * 0.35), (cx - s * 0.1, cy - s * 0.35), (cx + s * 0.2, cy + s * 0.05), (cx + s * 0.3, cy - s * 0.1), (cx + s * 0.48, cy + s * 0.35)],
            fill=(150, 160, 175), outline=ink, width=lw)
    cv.poly([(cx - s * 0.1, cy - s * 0.35), (cx - s * 0.2, cy - s * 0.15), (cx - s * 0.1, cy - s * 0.2), (cx, cy - s * 0.15)], fill=(255, 255, 255))
    g = smooth(t / 1.5)
    flag(cv, cx - s * 0.1 + s * 0.04, cy - s * 0.35 - s * 0.1 * g, s * 0.3 * g + 1, t, th)


def camera(cv, cx, cy, s, t, th):
    ink, lw = th["ink"], _lw(s)
    cv.rect((cx - s * 0.38, cy - s * 0.2, cx + s * 0.38, cy + s * 0.28), fill=(60, 62, 70), outline=ink, width=lw, radius=s * 0.05)
    cv.rect((cx - s * 0.15, cy - s * 0.3, cx + s * 0.1, cy - s * 0.2), fill=(60, 62, 70), outline=ink, width=lw)
    cv.circle((cx, cy + s * 0.04), s * 0.15, fill=mix(_acc(th, BLUE), (255, 255, 255), 0.4), outline=(230, 230, 230), width=lw)
    if int(t * 1.5) % 3 == 0:
        cv.circle((cx + s * 0.26, cy - s * 0.1), s * 0.04, fill=_acc(th, RED))


def pizza(cv, cx, cy, s, t, th):
    ink, lw = th["ink"], _lw(s)
    cv.poly([(cx - s * 0.35, cy - s * 0.28), (cx + s * 0.35, cy - s * 0.28), (cx, cy + s * 0.38)], fill=(250, 200, 90), outline=ink, width=lw)
    cv.rect((cx - s * 0.38, cy - s * 0.36, cx + s * 0.38, cy - s * 0.24), fill=(200, 140, 70), outline=ink, width=lw, radius=s * 0.05)
    for px, py in [(-0.12, -0.12), (0.1, -0.1), (0, 0.08)]:
        cv.circle((cx + px * s, cy + py * s), s * 0.05, fill=_acc(th, RED))


def bomb(cv, cx, cy, s, t, th):
    ink, lw = th["ink"], _lw(s)
    cv.circle((cx, cy + s * 0.05), s * 0.3, fill=(40, 40, 45), outline=ink, width=lw)
    cv.line([(cx + s * 0.18, cy - s * 0.2), (cx + s * 0.28, cy - s * 0.34)], (140, 100, 60), lw * 1.2)
    sp = abs(math.sin(t * 12))
    cv.circle((cx + s * 0.3, cy - s * 0.37), s * (0.04 + 0.04 * sp), fill=_acc(th, GOLD))


PROPS = {
    "bulb": bulb, "question": question, "exclamation": exclamation, "heart": heart, "star": star,
    "coin": coin, "money": money, "clock": clock, "book": book, "phone": phone, "laptop": laptop,
    "chart": chart, "arrow_up": arrow_up, "arrow_down": arrow_down, "globe": globe, "rocket": rocket,
    "cloud": cloud, "rain": rain, "sun": sun, "moon": moon, "tree": tree, "house": house, "gear": gear,
    "trophy": trophy, "brain": brain, "target": target, "check": check, "cross": cross,
    "warning": warning, "battery": battery, "calendar": calendar, "magnifier": magnifier,
    "gift": gift, "music": music, "fire": fire, "drop": drop, "lightning": lightning, "car": car,
    "mail": mail, "lock": lock, "key": key, "people": people, "plant": plant, "apple": apple,
    "graduation": graduation, "flag": flag, "mountain": mountain, "camera": camera, "pizza": pizza,
    "bomb": bomb,
}

# hand-drawn PNG props bundled from stickman-video-director (MIT)
PNG_PROPS = {
    "crayon_bulb": "idea-bulb-crayon.png", "crayon_calendar": "calendar-crayon.png",
    "crayon_camera": "camera-handdrawn.png", "crayon_clapper": "clapper-crayon.png",
    "crayon_note": "idea-note-crayon.png", "crayon_script": "script-page-crayon.png",
}

_png_cache = {}


def _png(name, size):
    key = (name, int(size))
    if key not in _png_cache:
        path = name if os.path.isabs(name) else os.path.join(ASSETS, "props", name)
        im = Image.open(path).convert("RGBA")
        k = size * SS / max(im.size)
        _png_cache[key] = im.resize((max(1, int(im.width * k)), max(1, int(im.height * k))), Image.LANCZOS)
    return _png_cache[key]


def all_prop_names():
    return sorted(PROPS) + sorted(PNG_PROPS)


def draw_prop(cv, name, cx, cy, s, t, th):
    """Draw a prop with a pop-in and gentle float. Returns False if unknown."""
    if t < 0:
        return True
    from .canvas import ease_out_back
    k = ease_out_back(min(1.0, t / 0.35))
    float_y = 4 * math.sin(t * 2.2 + cx * 0.01)
    size = s * max(0.01, k)
    if name in PROPS:
        PROPS[name](cv, cx, cy + float_y, size, t, th)
        return True
    file = PNG_PROPS.get(name) or (name if os.path.exists(name) else None)
    if file:
        im = _png(file, size)
        cv.paste(im, (cx - im.width / SS / 2, cy + float_y - im.height / SS / 2))
        return True
    return False
