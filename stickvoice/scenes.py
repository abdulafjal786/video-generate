"""Scene backgrounds. Drawn once per scene and cached."""
import math
import random

from .canvas import Canvas, new_image, mix

SETTINGS = ["plain", "park", "city", "night", "room", "office", "classroom", "space", "beach", "stage"]


def _faint(th, k=0.75):
    """Ink colour faded toward the background (for line-art scenery)."""
    return mix(th["ink"], th["bg"], k)


def _vgrad(cv, W, y0, y1, c0, c1, steps=48):
    for i in range(steps):
        a = y0 + (y1 - y0) * i / steps
        b = y0 + (y1 - y0) * (i + 1) / steps + 1
        cv.rect((0, a, W, b), fill=mix(c0, c1, i / (steps - 1)))


def draw_background(setting, W, H, ground, th, seed=0):
    rnd = random.Random(sum(map(ord, setting)) * 31 + seed)
    world = th.get("world", th["mode"])
    img = new_image(W, H, th["bg"])
    cv = Canvas(img)
    if world == "line":
        _line_scene(cv, setting, W, H, ground, th, rnd)
    elif world in WORLDS:
        WORLDS[world](cv, setting, W, H, ground, th, rnd)
    else:
        _color_scene(cv, setting, W, H, ground, th, rnd, soft=(world == "color_soft"))
    if th.get("texture"):
        _paper_texture(cv, W, H, rnd)
    return img


# ---------------------------------------------------------------------------
def _grid(cv, W, H, th):
    g = th.get("grid")
    if not g:
        return
    if th.get("perspective_grid"):
        hy = H * 0.55
        for i in range(-12, 13):
            cv.line([(W / 2 + i * W * 0.03, hy), (W / 2 + i * W * 0.22, H)], g, 1)
        y, step = hy, 6
        while y < H:
            cv.line([(0, y), (W, y)], g, 1)
            step *= 1.35
            y += step
        return
    step = 64
    x = 32
    while x < W:
        cv.line([(x, 0), (x, H)], g, 1)
        x += step
    y = 16
    while y < H:
        cv.line([(0, y), (W, y)], g, 1)
        y += step


def _line_scene(cv, s, W, H, ground, th, rnd):
    _grid(cv, W, H, th)
    f = _faint(th, 0.72)
    lw = max(2, H * 0.004)
    if s == "plain":
        cv.line([(W * 0.06, ground), (W * 0.94, ground)], _faint(th, 0.55), lw)
        return
    cv.line([(0, ground), (W, ground)], _faint(th, 0.5), lw)
    if s == "park":
        for x in (0.08, 0.9):
            tx, ty = W * x, ground
            cv.line([(tx, ty), (tx, ty - H * 0.18)], f, lw * 1.5)
            cv.circle((tx, ty - H * 0.25), H * 0.09, outline=f, width=lw)
        cv.circle((W * 0.8, H * 0.14), H * 0.05, outline=f, width=lw)
        for i in range(10):
            gx = rnd.uniform(0, W)
            cv.line([(gx, ground), (gx + 4, ground - 10), (gx + 8, ground)], f, lw * 0.7)
    elif s == "city":
        x = 0
        while x < W:
            bw, bh = rnd.uniform(70, 130), rnd.uniform(H * 0.15, H * 0.42)
            cv.rect((x, ground - bh, x + bw, ground), outline=f, width=lw)
            for wy in range(int(ground - bh + 18), int(ground - 20), 30):
                for wx in range(int(x + 14), int(x + bw - 18), 26):
                    cv.rect((wx, wy, wx + 10, wy + 12), outline=f, width=lw * 0.6)
            x += bw + rnd.uniform(15, 50)
    elif s == "night":
        cv.circle((W * 0.85, H * 0.15), H * 0.05, outline=f, width=lw)
        for _ in range(25):
            sx, sy = rnd.uniform(0, W), rnd.uniform(0, ground * 0.6)
            cv.line([(sx - 4, sy), (sx + 4, sy)], f, lw * 0.6)
            cv.line([(sx, sy - 4), (sx, sy + 4)], f, lw * 0.6)
    elif s in ("room", "office"):
        cv.rect((W * 0.06, H * 0.12, W * 0.24, H * 0.38), outline=f, width=lw)
        cv.line([(W * 0.15, H * 0.12), (W * 0.15, H * 0.38)], f, lw * 0.7)
        cv.line([(W * 0.06, H * 0.25), (W * 0.24, H * 0.25)], f, lw * 0.7)
        if s == "office":
            cv.rect((W * 0.76, ground - H * 0.16, W * 0.96, ground - H * 0.14), outline=f, width=lw)
            cv.line([(W * 0.78, ground - H * 0.14), (W * 0.78, ground)], f, lw)
            cv.line([(W * 0.94, ground - H * 0.14), (W * 0.94, ground)], f, lw)
            cv.rect((W * 0.82, ground - H * 0.27, W * 0.9, ground - H * 0.17), outline=f, width=lw)
        else:
            cv.rect((W * 0.78, ground - H * 0.25, W * 0.95, ground), outline=f, width=lw)
            for k in range(3):
                y = ground - H * 0.25 + (k + 1) * H * 0.0625
                cv.line([(W * 0.78, y), (W * 0.95, y)], f, lw * 0.7)
    elif s == "classroom":
        cv.rect((W * 0.55, H * 0.1, W * 0.95, H * 0.42), outline=f, width=lw * 1.4)
        cv.line([(W * 0.55, H * 0.44), (W * 0.95, H * 0.44)], f, lw)
    elif s == "space":
        for _ in range(40):
            sx, sy = rnd.uniform(0, W), rnd.uniform(0, H * 0.85)
            cv.circle((sx, sy), rnd.uniform(1, 2.5), fill=f)
        cv.circle((W * 0.85, H * 0.2), H * 0.08, outline=f, width=lw)
        cv.ellipse((W * 0.85 - H * 0.14, H * 0.2 - H * 0.025, W * 0.85 + H * 0.14, H * 0.2 + H * 0.025), outline=f, width=lw * 0.7)
    elif s == "beach":
        cv.circle((W * 0.82, H * 0.15), H * 0.05, outline=f, width=lw)
        for i in range(3):
            y = ground - H * 0.08 - i * H * 0.03
            pts = [(x, y + 5 * math.sin(x / 40)) for x in range(0, int(W) + 40, 40)]
            cv.line(pts, f, lw * 0.7)
    elif s == "stage":
        cv.line([(W * 0.02, 0), (W * 0.12, H * 0.5), (W * 0.06, ground)], f, lw)
        cv.line([(W * 0.98, 0), (W * 0.88, H * 0.5), (W * 0.94, ground)], f, lw)
        cv.ellipse((W * 0.25, ground - H * 0.03, W * 0.75, ground + H * 0.03), outline=f, width=lw)


def _color_scene(cv, s, W, H, ground, th, rnd, soft=False):
    def c(rgb):
        return mix(rgb, th["bg"], 0.45) if soft else rgb

    ink = th["ink"]
    lw = max(2, H * 0.004)
    if s == "night" or s == "space":
        _vgrad(cv, W, 0, ground, c((20, 26, 60)), c((60, 50, 110)))
        for _ in range(60 if s == "space" else 35):
            cv.circle((rnd.uniform(0, W), rnd.uniform(0, ground * 0.9)), rnd.uniform(1, 2.6), fill=(255, 250, 220))
        if s == "night":
            cv.circle((W * 0.84, H * 0.16), H * 0.06, fill=(250, 240, 190))
            cv.rect((0, ground, W, H), fill=c((40, 60, 50)))
        else:
            cv.circle((W * 0.82, H * 0.22), H * 0.09, fill=c((230, 150, 90)), outline=ink, width=lw)
            cv.ellipse((W * 0.82 - H * 0.16, H * 0.2, W * 0.82 + H * 0.16, H * 0.245), outline=c((250, 220, 160)), width=lw * 1.5)
            cv.rect((0, ground, W, H), fill=c((90, 90, 110)))
            for _ in range(8):
                x = rnd.uniform(0, W)
                cv.ellipse((x - 30, ground + 10, x + 30, ground + 24), fill=c((70, 70, 90)))
        return
    if s in ("room", "office", "classroom"):
        wall = {"room": (250, 228, 196), "office": (220, 232, 240), "classroom": (235, 240, 215)}[s]
        cv.rect((0, 0, W, ground), fill=c(wall))
        cv.rect((0, ground, W, H), fill=c((196, 150, 110) if s != "office" else (150, 156, 170)))
        cv.line([(0, ground), (W, ground)], ink, lw)
        if s == "classroom":
            cv.rect((W * 0.55, H * 0.1, W * 0.95, H * 0.42), fill=c((40, 85, 60)), outline=c((150, 100, 60)), width=lw * 3)
        else:
            cv.rect((W * 0.06, H * 0.12, W * 0.24, H * 0.38), fill=c((170, 215, 245)), outline=ink, width=lw)
            cv.line([(W * 0.15, H * 0.12), (W * 0.15, H * 0.38)], ink, lw * 0.7)
            cv.circle((W * 0.2, H * 0.17), H * 0.025, fill=c((250, 210, 80)))
            if s == "room":
                cv.rect((W * 0.78, ground - H * 0.25, W * 0.95, ground), fill=c((170, 115, 80)), outline=ink, width=lw)
                for k in range(3):
                    y = ground - H * 0.25 + (k + 1) * H * 0.0625
                    cv.line([(W * 0.78, y), (W * 0.95, y)], ink, lw * 0.7)
                    for b in range(5):
                        bx = W * 0.79 + b * W * 0.03
                        cv.rect((bx, y - H * 0.05, bx + W * 0.02, y), fill=c(th["accents"][b % 3]))
            else:
                cv.rect((W * 0.76, ground - H * 0.16, W * 0.96, ground - H * 0.14), fill=c((240, 240, 245)), outline=ink, width=lw)
                cv.rect((W * 0.82, ground - H * 0.27, W * 0.9, ground - H * 0.17), fill=c((50, 55, 65)), outline=ink, width=lw)
                cv.line([(W * 0.78, ground - H * 0.14), (W * 0.78, ground)], ink, lw)
                cv.line([(W * 0.94, ground - H * 0.14), (W * 0.94, ground)], ink, lw)
        return
    # outdoor daytime: sky + ground
    sky_top, sky_bot = (120, 190, 240), (205, 235, 252)
    if s == "beach":
        sky_top, sky_bot = (110, 195, 245), (220, 240, 250)
    if s == "stage":
        _vgrad(cv, W, 0, ground, c((60, 20, 40)), c((120, 40, 60)))
        cv.rect((0, ground, W, H), fill=c((110, 70, 45)))
        cv.poly([(W * 0.5 - W * 0.08, 0), (W * 0.5 + W * 0.08, 0), (W * 0.5 + W * 0.25, ground), (W * 0.5 - W * 0.25, ground)], fill=(255, 245, 200, 50))
        cv.rect((0, 0, W * 0.1, ground), fill=c((170, 30, 50)))
        cv.rect((W * 0.9, 0, W, ground), fill=c((170, 30, 50)))
        return
    _vgrad(cv, W, 0, ground, c(sky_top), c(sky_bot))
    cv.circle((W * 0.85, H * 0.14), H * 0.055, fill=c((255, 215, 80)))
    for _ in range(3):
        x, y = rnd.uniform(0.05, 0.7) * W, rnd.uniform(0.06, 0.25) * H
        for dx, r in ((-30, 22), (0, 30), (30, 22)):
            cv.circle((x + dx, y), r, fill=(255, 255, 255))
    if s == "city":
        x = 0
        while x < W:
            bw, bh = rnd.uniform(70, 140), rnd.uniform(H * 0.18, H * 0.45)
            col = c(rnd.choice([(150, 160, 185), (175, 180, 200), (130, 140, 170), (190, 170, 160)]))
            cv.rect((x, ground - bh, x + bw, ground), fill=col, outline=ink, width=lw * 0.6)
            for wy in range(int(ground - bh + 16), int(ground - 18), 28):
                for wx in range(int(x + 12), int(x + bw - 16), 24):
                    cv.rect((wx, wy, wx + 10, wy + 12), fill=c((250, 240, 190)))
            x += bw + rnd.uniform(4, 20)
        cv.rect((0, ground, W, H), fill=c((110, 110, 118)))
        for x in range(0, int(W), 90):
            cv.rect((x, ground + (H - ground) * 0.45, x + 45, ground + (H - ground) * 0.5), fill=(240, 240, 240))
    elif s == "beach":
        cv.rect((0, ground - H * 0.12, W, ground), fill=c((60, 150, 210)))
        for i in range(3):
            y = ground - H * 0.1 + i * H * 0.03
            pts = [(x, y + 4 * math.sin(x / 35 + i)) for x in range(0, int(W) + 35, 35)]
            cv.line(pts, (230, 245, 255), lw * 0.7)
        cv.rect((0, ground, W, H), fill=c((240, 215, 160)))
    else:  # park / plain outdoor
        cv.poly([(0, ground - H * 0.08), (W * 0.3, ground - H * 0.16), (W * 0.6, ground - H * 0.06), (W, ground - H * 0.14), (W, ground), (0, ground)],
                fill=c((150, 200, 120)))
        cv.rect((0, ground, W, H), fill=c((110, 175, 90)))
        if s == "park":
            for x in (0.07, 0.92):
                tx = W * x
                cv.rect((tx - 10, ground - H * 0.2, tx + 10, ground), fill=c((140, 95, 60)), outline=ink, width=lw)
                cv.circle((tx, ground - H * 0.26), H * 0.1, fill=c((90, 165, 80)), outline=ink, width=lw)
            for _ in range(14):
                fx, fy = rnd.uniform(0, W), rnd.uniform(ground + 8, H - 8)
                cv.circle((fx, fy), 4, fill=c(rnd.choice(th["accents"])))
    cv.line([(0, ground), (W, ground)], mix(ink, th["bg"], 0.4), lw)


# ---------------------------------------------------------------------------
# Era / mood worlds for the Director styles (A3, A5, A6)
# ---------------------------------------------------------------------------
def _paper_texture(cv, W, H, rnd):
    for _ in range(int(W * H / 900)):
        x, y = rnd.uniform(0, W), rnd.uniform(0, H)
        v = rnd.choice([(0, 0, 0, 10), (255, 255, 255, 14)])
        cv.circle((x, y), rnd.uniform(0.6, 1.8), fill=v)


def _hills(cv, W, ground, h, color, rnd, n=5):
    pts = [(0, ground)]
    for i in range(n + 1):
        pts.append((W * i / n, ground - h * rnd.uniform(0.4, 1.0)))
    pts.append((W, ground))
    cv.poly(pts, fill=color)


def _ground(cv, W, H, ground, color, ink, lw):
    cv.rect((0, ground, W, H), fill=color)
    cv.line([(0, ground), (W, ground)], ink, lw)


def _cave(cv, s, W, H, ground, th, rnd):
    ink = th["ink"]
    lw = max(2, H * 0.004)
    ochre, brown, dark = (214, 176, 120), (150, 104, 62), (92, 62, 40)
    if s in ("plain", "room", "office", "classroom", "stage"):   # cave interior
        _vgrad(cv, W, 0, ground, (110, 76, 48), (170, 124, 78))
        # cave mouth showing daylight
        cx = W * (0.82 if s != "stage" else 0.5)
        cv.ellipse((cx - W * 0.13, H * 0.12, cx + W * 0.13, ground + H * 0.08), fill=(250, 214, 150))
        cv.ellipse((cx - W * 0.13, H * 0.12, cx + W * 0.13, ground + H * 0.08), outline=dark, width=lw * 2)
        _hills(cv, W, H * 0.05, -H * 0.05, (90, 60, 38), rnd, 9)
        # wall paintings
        f = (170, 70, 40)
        for k in range(3):
            x0, y0 = W * (0.08 + k * 0.14), H * (0.2 + 0.05 * (k % 2))
            cv.line([(x0, y0), (x0 + 40, y0)], f, lw)                       # animal body
            for lx in (x0 + 6, x0 + 34):
                cv.line([(lx, y0), (lx - 3, y0 + 18)], f, lw * 0.8)
            cv.line([(x0 + 40, y0), (x0 + 50, y0 - 10)], f, lw)
            cv.circle((x0 + 70, y0 + 4), 4, fill=f)
            cv.line([(x0 + 70, y0 + 8), (x0 + 70, y0 + 22)], f, lw * 0.8)
        for k in range(4):  # stalactites
            x = W * rnd.uniform(0.05, 0.65)
            cv.poly([(x - 18, 0), (x + 18, 0), (x, H * rnd.uniform(0.08, 0.16))], fill=(90, 60, 38))
        _ground(cv, W, H, ground, brown, mix(ink, brown, 0.4), lw)
        for _ in range(9):
            x = rnd.uniform(0, W)
            cv.ellipse((x - 26, ground + 6, x + 26, ground + 22), fill=dark)
        if s == "stage":
            for x in (0.18, 0.32, 0.68, 0.82):
                cv.rect((W * x - 22, ground - H * 0.28, W * x + 22, ground), fill=(130, 120, 110), outline=ink, width=lw, radius=10)
    elif s in ("night", "space"):                                  # campfire night
        _vgrad(cv, W, 0, ground, (24, 22, 48), (70, 50, 70))
        for _ in range(45):
            cv.circle((rnd.uniform(0, W), rnd.uniform(0, ground * 0.8)), rnd.uniform(1, 2.4), fill=(255, 240, 210))
        cv.circle((W * 0.82, H * 0.16), H * 0.07, fill=(250, 236, 190))
        _hills(cv, W, ground, H * 0.12, (40, 32, 44), rnd, 6)
        _ground(cv, W, H, ground, (70, 50, 40), ink, lw)
        fx = W * 0.62
        cv.ellipse((fx - 160, ground - 60, fx + 160, ground + 40), fill=(255, 150, 60, 50))
        for k in range(4):
            cv.line([(fx - 40 + k * 26, ground + 4), (fx + 40 - k * 26, ground - 10)], (110, 70, 40), lw * 2.2)
        cv.poly([(fx - 30, ground - 4), (fx, ground - 70), (fx + 30, ground - 4)], fill=(240, 110, 40))
        cv.poly([(fx - 16, ground - 4), (fx + 2, ground - 44), (fx + 16, ground - 4)], fill=(255, 210, 80))
    else:                                                          # savanna / village
        _vgrad(cv, W, 0, ground, (250, 196, 120), (252, 228, 176))
        cv.circle((W * 0.84, H * 0.15), H * 0.06, fill=(255, 240, 200))
        # volcano + far hills
        cv.poly([(W * 0.55, ground - H * 0.05), (W * 0.66, ground - H * 0.33), (W * 0.72, ground - H * 0.33), (W * 0.84, ground - H * 0.05)],
                fill=(150, 104, 80))
        for k in range(3):
            cv.circle((W * 0.69 + k * 14, ground - H * (0.38 + k * 0.05)), 12 + k * 6, fill=(200, 190, 180))
        _hills(cv, W, ground, H * 0.08, (200, 150, 90), rnd, 7)
        _ground(cv, W, H, ground, (196, 150, 86), mix(ink, ochre, 0.4), lw)
        if s == "city":                                            # village of hide huts
            for x in (0.08, 0.2, 0.86):
                hx = W * x
                cv.poly([(hx - 60, ground), (hx, ground - H * 0.24), (hx + 60, ground)], fill=(176, 126, 80), outline=ink, width=lw)
                cv.poly([(hx - 14, ground), (hx, ground - H * 0.09), (hx + 14, ground)], fill=(70, 46, 30))
                cv.line([(hx - 8, ground - H * 0.27), (hx, ground - H * 0.22), (hx + 10, ground - H * 0.28)], (110, 70, 40), lw)
        else:
            for x in (0.07, 0.93):                                 # ferns / palms
                tx = W * x
                cv.line([(tx, ground), (tx + 10, ground - H * 0.24)], (110, 74, 44), lw * 3)
                for a in range(-70, 71, 35):
                    cv.line([(tx + 10, ground - H * 0.24), (tx + 10 + 70 * math.sin(math.radians(a)), ground - H * 0.24 + 30 * abs(math.sin(math.radians(a))) - 10)],
                            (90, 140, 70), lw * 2)
        for _ in range(16):
            gx = rnd.uniform(0, W)
            cv.line([(gx, ground + 2), (gx + 4, ground - 12), (gx + 8, ground + 2)], (140, 120, 60), lw * 0.8)


def _edo(cv, s, W, H, ground, th, rnd):
    ink = th["ink"]
    lw = max(2, H * 0.004)
    if s in ("room", "office", "classroom"):                       # tatami room with shoji
        cv.rect((0, 0, W, ground), fill=(232, 214, 176))
        for x in range(0, int(W) + 1, int(W / 6)):
            cv.rect((x + 6, H * 0.06, x + W / 6 - 6, ground - H * 0.04), fill=(248, 242, 226), outline=(140, 100, 60), width=lw * 1.4)
            for k in range(1, 4):
                cv.line([(x + 6, H * 0.06 + k * (ground - H * 0.1) / 4), (x + W / 6 - 6, H * 0.06 + k * (ground - H * 0.1) / 4)], (170, 130, 90), lw * 0.6)
            cv.line([(x + W / 12, H * 0.06), (x + W / 12, ground - H * 0.04)], (170, 130, 90), lw * 0.6)
        cv.rect((W * 0.44, H * 0.08, W * 0.56, H * 0.45), fill=(244, 236, 214), outline=(120, 90, 60), width=lw)   # hanging scroll
        cv.line([(W * 0.47, H * 0.14), (W * 0.48, H * 0.36)], ink, lw * 2)
        cv.line([(W * 0.52, H * 0.16), (W * 0.51, H * 0.3)], ink, lw * 1.5)
        cv.rect((0, ground, W, H), fill=(196, 186, 120))
        for x in range(0, int(W) + 1, int(W / 5)):
            cv.line([(x, ground), (x, H)], (150, 140, 80), lw)
        cv.line([(0, ground), (W, ground)], (120, 90, 60), lw * 1.5)
        return
    night = s in ("night", "space")
    sky = ((30, 34, 70), (80, 70, 110)) if night else ((246, 214, 170), (250, 236, 210))
    _vgrad(cv, W, 0, ground, *sky)
    # Mount Fuji
    fuji = (80, 90, 130) if not night else (50, 50, 80)
    cv.poly([(W * 0.45, ground - H * 0.08), (W * 0.62, ground - H * 0.42), (W * 0.68, ground - H * 0.42), (W * 0.86, ground - H * 0.08)], fill=fuji)
    cv.poly([(W * 0.6, ground - H * 0.37), (W * 0.62, ground - H * 0.42), (W * 0.68, ground - H * 0.42), (W * 0.7, ground - H * 0.37), (W * 0.665, ground - H * 0.35), (W * 0.645, ground - H * 0.38)], fill=(250, 250, 250))
    if night:
        cv.circle((W * 0.18, H * 0.15), H * 0.06, fill=(250, 240, 200))
    else:
        cv.circle((W * 0.16, H * 0.16), H * 0.07, fill=(220, 70, 50))
    if s in ("park", "beach"):                                     # garden: sakura + red bridge
        cv.rect((0, ground, W, H), fill=(120, 170, 100))
        cv.ellipse((W * 0.55, ground - H * 0.02, W * 0.98, ground + (H - ground) * 0.35), fill=(110, 160, 200))
        cv.arc((W * 0.765, ground + H * 0.1), W * 0.12, 205, 335, (200, 50, 45), lw * 3)
        for x in (0.08, 0.92):
            tx = W * x
            cv.line([(tx, ground), (tx + 12, ground - H * 0.2), (tx - 10, ground - H * 0.3)], (90, 60, 50), lw * 3)
            for _ in range(14):
                cv.circle((tx + rnd.uniform(-80, 80), ground - H * rnd.uniform(0.22, 0.42)), rnd.uniform(14, 26), fill=(246, 182, 200))
        cv.line([(0, ground), (W, ground)], mix(ink, (120, 170, 100), 0.5), lw)
        return
    if s == "stage":                                                # torii gate
        _ground(cv, W, H, ground, (176, 150, 110), ink, lw)
        gx = W * 0.5
        for dx in (-0.16, 0.16):
            cv.rect((gx + W * dx - 12, ground - H * 0.42, gx + W * dx + 12, ground), fill=(200, 50, 45), outline=ink, width=lw)
        cv.rect((gx - W * 0.22, ground - H * 0.46, gx + W * 0.22, ground - H * 0.42), fill=(40, 30, 30))
        cv.rect((gx - W * 0.19, ground - H * 0.37, gx + W * 0.19, ground - H * 0.345), fill=(200, 50, 45), outline=ink, width=lw)
        return
    # Edo street: wooden houses, tiled roofs, noren and lanterns
    x = -20
    while x < W:
        bw = rnd.uniform(150, 220)
        if not (W * 0.2 < x + bw / 2 < W * 0.4):  # keep space around the actor
            top = ground - H * rnd.uniform(0.3, 0.38)
            cv.rect((x, top, x + bw, ground), fill=(150, 104, 66) if not night else (70, 50, 46), outline=ink, width=lw)
            cv.poly([(x - 16, top + 6), (x + bw / 2, top - H * 0.07), (x + bw + 16, top + 6)], fill=(70, 72, 84), outline=ink, width=lw)
            cv.rect((x + bw * 0.2, top + H * 0.08, x + bw * 0.8, top + H * 0.15), fill=(40, 60, 110))
            for k in range(3):
                cv.line([(x + bw * (0.2 + 0.2 * (k + 1)), top + H * 0.08), (x + bw * (0.2 + 0.2 * (k + 1)), top + H * 0.15)], (230, 230, 230), lw * 0.6)
            lx = x + bw * 0.12
            cv.line([(lx, top + 8), (lx, top + 20)], ink, lw)
            lc = (255, 200, 90) if night else (210, 60, 50)
            if night:
                cv.circle((lx, top + 38), 40, fill=(255, 190, 80, 40))
            cv.ellipse((lx - 13, top + 20, lx + 13, top + 54), fill=lc, outline=ink, width=lw * 0.7)
        x += bw + rnd.uniform(10, 40)
    _ground(cv, W, H, ground, (196, 170, 120) if not night else (80, 70, 70), ink, lw)


def _egypt(cv, s, W, H, ground, th, rnd):
    ink = th["ink"]
    lw = max(2, H * 0.004)
    sand = (232, 196, 128)
    if s in ("room", "office", "classroom", "stage"):              # temple hall
        cv.rect((0, 0, W, ground), fill=(222, 186, 130))
        for x in (0.06, 0.24, 0.76, 0.94) if s != "stage" else (0.1, 0.3, 0.7, 0.9):
            cx = W * x
            cv.rect((cx - 34, H * 0.08, cx + 34, ground), fill=(236, 206, 150), outline=ink, width=lw)
            for k in range(4):
                y = H * 0.14 + k * H * 0.13
                cv.rect((cx - 34, y, cx + 34, y + H * 0.025), fill=th["accents"][k % 3])
            cv.rect((cx - 44, H * 0.04, cx + 44, H * 0.09), fill=(200, 160, 100), outline=ink, width=lw)
        for k in range(5):                                          # hieroglyph strip (abstract marks, no letters)
            y = H * 0.12 + k * 34
            for j in range(3):
                cv.circle((W * 0.47 + j * 26, y), 6, outline=(120, 80, 40), width=lw * 0.7)
        cv.rect((0, 0, W, H * 0.04), fill=(40, 90, 160))
        _ground(cv, W, H, ground, (196, 156, 100), ink, lw)
        for x in (0.15, 0.85):
            cv.line([(W * x, ground - H * 0.25), (W * x, ground)], (110, 80, 50), lw * 2)
            cv.poly([(W * x - 14, ground - H * 0.25), (W * x, ground - H * 0.32), (W * x + 14, ground - H * 0.25)], fill=(250, 150, 50))
        return
    night = s in ("night", "space")
    _vgrad(cv, W, 0, ground, *(((20, 26, 60), (60, 60, 110)) if night else ((120, 190, 235), (246, 226, 180))))
    if night:
        for _ in range(40):
            cv.circle((rnd.uniform(0, W), rnd.uniform(0, ground * 0.7)), rnd.uniform(1, 2.2), fill=(255, 245, 220))
        cv.circle((W * 0.84, H * 0.15), H * 0.05, fill=(250, 240, 200))
    else:
        cv.circle((W * 0.84, H * 0.14), H * 0.06, fill=(255, 220, 90))
    pyr = (214, 170, 100) if not night else (90, 80, 90)
    for px, ph in ((0.62, 0.36), (0.78, 0.26), (0.5, 0.18)):
        cx, top = W * px, ground - H * ph
        cv.poly([(cx - H * ph * 1.1, ground), (cx, top), (cx + H * ph * 1.1, ground)], fill=pyr, outline=mix(ink, pyr, 0.5), width=lw)
        cv.poly([(cx, top), (cx + H * ph * 1.1, ground), (cx + H * ph * 0.3, ground)], fill=mix(pyr, (0, 0, 0), 0.15))
    if s == "beach":                                                 # the Nile
        cv.rect((0, ground - H * 0.06, W, ground + H * 0.04), fill=(60, 130, 170))
        for x in range(0, int(W), 60):
            cv.line([(x, ground - H * 0.06), (x + 6, ground - H * 0.12)], (90, 140, 70), lw)
        bx = W * 0.82
        cv.poly([(bx - 70, ground - H * 0.05), (bx + 70, ground - H * 0.05), (bx + 50, ground - H * 0.01), (bx - 50, ground - H * 0.01)], fill=(140, 90, 50), outline=ink, width=lw)
        cv.poly([(bx, ground - H * 0.05), (bx, ground - H * 0.26), (bx + 55, ground - H * 0.08)], fill=(250, 246, 236), outline=ink, width=lw)
    _ground(cv, W, H, ground, sand if not night else (110, 96, 90), ink, lw)
    for x in (0.06,) if s != "city" else (0.06, 0.94):              # palm
        tx = W * x
        cv.line([(tx, ground), (tx + 14, ground - H * 0.28)], (130, 90, 50), lw * 3)
        for a in (-60, -25, 15, 50, 85):
            cv.line([(tx + 14, ground - H * 0.28), (tx + 14 + 70 * math.cos(math.radians(a - 90)), ground - H * 0.28 + 40 * math.sin(math.radians(abs(a))) - 20)],
                    (70, 140, 70), lw * 2.5)


def _rome(cv, s, W, H, ground, th, rnd):
    ink = th["ink"]
    lw = max(2, H * 0.004)
    marble = (238, 232, 220)
    if s in ("room", "office", "classroom"):                        # villa interior
        cv.rect((0, 0, W, ground), fill=(170, 50, 46))
        cv.rect((0, ground - H * 0.16, W, ground), fill=(60, 50, 50))
        for x in (0.08, 0.92):
            cv.rect((W * x - 26, H * 0.06, W * x + 26, ground), fill=marble, outline=ink, width=lw)
            for k in range(3):
                cv.line([(W * x - 14 + k * 14, H * 0.1), (W * x - 14 + k * 14, ground - 6)], (200, 194, 180), lw * 0.7)
        cv.rect((W * 0.4, H * 0.12, W * 0.6, H * 0.36), fill=(240, 220, 170), outline=(200, 156, 60), width=lw * 2)
        cv.circle((W * 0.5, H * 0.24), H * 0.06, outline=(200, 156, 60), width=lw)
        _ground(cv, W, H, ground, (220, 200, 170), ink, lw)
        for x in range(0, int(W), 40):                               # mosaic band
            cv.rect((x + 4, ground + 10, x + 34, ground + 24), fill=th["accents"][(x // 40) % 3])
        return
    night = s in ("night", "space")
    _vgrad(cv, W, 0, ground, *(((20, 26, 60), (70, 60, 100)) if night else ((130, 190, 235), (220, 236, 245))))
    if night:
        for _ in range(35):
            cv.circle((rnd.uniform(0, W), rnd.uniform(0, ground * 0.7)), rnd.uniform(1, 2.2), fill=(255, 245, 220))
    if s in ("park", "beach", "night", "space"):                     # legion camp
        _hills(cv, W, ground, H * 0.14, (110, 150, 90) if not night else (40, 50, 50), rnd, 6)
        _ground(cv, W, H, ground, (120, 160, 90) if not night else (50, 60, 50), ink, lw)
        for x in (0.1, 0.84, 0.97):
            tx = W * x
            cv.poly([(tx - 70, ground), (tx, ground - H * 0.18), (tx + 70, ground)], fill=(232, 214, 176), outline=ink, width=lw)
            cv.line([(tx, ground - H * 0.18), (tx, ground)], ink, lw * 0.6)
        for x in range(0, int(W), 22):                               # palisade
            if W * 0.3 < x < W * 0.7:
                continue
            cv.rect((x, ground - H * 0.08, x + 14, ground), fill=(140, 100, 60), outline=ink, width=lw * 0.5)
        if night:
            fx = W * 0.6
            cv.ellipse((fx - 120, ground - 50, fx + 120, ground + 30), fill=(255, 150, 60, 50))
            cv.poly([(fx - 24, ground), (fx, ground - 56), (fx + 24, ground)], fill=(240, 110, 40))
        return
    if s == "stage":                                                 # colosseum
        cv.rect((W * 0.05, ground - H * 0.5, W * 0.95, ground), fill=(214, 190, 150), outline=ink, width=lw)
        for row in range(3):
            y0 = ground - H * 0.5 + row * H * 0.16 + 10
            for x in range(int(W * 0.08), int(W * 0.92), 70):
                cv.rect((x, y0 + 14, x + 40, y0 + H * 0.14), fill=(120, 96, 70), radius=18)
        _ground(cv, W, H, ground, (220, 196, 150), ink, lw)
        return
    # forum: temple with columns
    tx0, tx1 = W * 0.55, W * 0.97
    cv.poly([(tx0 - 20, ground - H * 0.46), ((tx0 + tx1) / 2, ground - H * 0.58), (tx1 + 20, ground - H * 0.46)], fill=marble, outline=ink, width=lw)
    cv.rect((tx0 - 20, ground - H * 0.47, tx1 + 20, ground - H * 0.42), fill=marble, outline=ink, width=lw)
    for k in range(6):
        cx = tx0 + k * (tx1 - tx0) / 5
        cv.rect((cx - 14, ground - H * 0.42, cx + 14, ground - H * 0.03), fill=marble, outline=ink, width=lw)
    cv.rect((tx0 - 30, ground - H * 0.03, tx1 + 30, ground), fill=(210, 204, 192), outline=ink, width=lw)
    for x in (0.06, 0.16):
        cv.rect((W * x - 16, ground - H * 0.3, W * x + 16, ground), fill=marble, outline=ink, width=lw)
    _ground(cv, W, H, ground, (200, 190, 170), ink, lw)
    for _ in range(30):
        x = rnd.uniform(0, W)
        y = rnd.uniform(ground + 8, H - 6)
        cv.rect((x, y, x + 18, y + 8), fill=(180, 170, 150), radius=3)


def _amber(cv, s, W, H, ground, th, rnd):
    ink = (14, 10, 16)
    lw = max(2, H * 0.004)
    plum, deep, amber = (64, 36, 66), (34, 20, 40), (255, 170, 70)
    if s in ("park", "beach"):                                       # amber sunset over plum hills
        _vgrad(cv, W, 0, ground, (110, 50, 80), (255, 160, 80))
        cv.circle((W * 0.7, ground - H * 0.08), H * 0.12, fill=(255, 210, 120))
        _hills(cv, W, ground, H * 0.12, (70, 34, 60), rnd, 5)
        _ground(cv, W, H, ground, (46, 24, 44), ink, lw)
        return
    if s in ("room", "office", "classroom"):                        # dim room, one warm lamp
        cv.rect((0, 0, W, ground), fill=(60, 34, 62))
        cv.rect((W * 0.62, H * 0.12, W * 0.9, H * 0.48), fill=(30, 20, 46), outline=ink, width=lw * 2)
        for k in range(6):                                           # city lights through the window
            x = W * (0.64 + k * 0.042)
            cv.rect((x, H * (0.3 + 0.04 * (k % 3)), x + 14, H * 0.48), fill=(48, 30, 60))
            cv.rect((x + 4, H * (0.33 + 0.04 * (k % 3)), x + 9, H * (0.36 + 0.04 * (k % 3))), fill=amber)
        lx = W * 0.14
        for k, rr in enumerate((260, 190, 120)):
            cv.ellipse((lx - rr * 1.4, ground - rr * 0.25, lx + rr * 1.4, ground + rr * 0.12), fill=(255, 170, 70, 18 + k * 8))
        cv.circle((lx, H * 0.26), 70, fill=(255, 180, 80, 40))
        cv.poly([(lx - 30, H * 0.22), (lx + 30, H * 0.22), (lx + 18, H * 0.3), (lx - 18, H * 0.3)], fill=(240, 140, 50))
        cv.line([(lx, H * 0.3), (lx, ground)], ink, lw * 1.5)
        cv.ellipse((lx - 40, ground - 8, lx + 40, ground + 6), fill=ink)
        _ground(cv, W, H, ground, (40, 22, 40), ink, lw)
        return
    # city street at night (default)
    _vgrad(cv, W, 0, ground, (30, 18, 40), (96, 46, 74))
    for col, hmin, hmax, win in (((70, 38, 72), 0.3, 0.55, 0.25), ((44, 24, 50), 0.18, 0.4, 0.45)):
        x = rnd.uniform(-40, 0)
        while x < W:
            bw = rnd.uniform(80, 150)
            top = ground - H * rnd.uniform(hmin, hmax)
            cv.rect((x, top, x + bw, ground), fill=col)
            for wy in range(int(top + 16), int(ground - 24), 30):
                for wx in range(int(x + 12), int(x + bw - 16), 24):
                    if rnd.random() < win:
                        cv.rect((wx, wy, wx + 10, wy + 14), fill=amber if rnd.random() < 0.8 else (255, 220, 160))
            x += bw + rnd.uniform(2, 14)
    # street lamp with amber glow
    lx = W * 0.82
    cv.poly([(lx - 20, ground - H * 0.42), (lx + 20, ground - H * 0.42), (lx + 170, ground), (lx - 170, ground)], fill=(255, 170, 70, 40))
    cv.line([(lx, ground), (lx, ground - H * 0.45), (lx - 30, ground - H * 0.45)], ink, lw * 2)
    cv.circle((lx - 30, ground - H * 0.43), 12, fill=(255, 200, 110))
    _ground(cv, W, H, ground, (36, 20, 38), ink, lw)
    for k in range(10):                                              # wet street reflections
        x = rnd.uniform(0, W)
        cv.line([(x, ground + 12 + k * 4), (x + rnd.uniform(20, 60), ground + 12 + k * 4)], (255, 170, 70, 70), lw)


def _tree_clump(cv, x, base, w, h, color, ink, lw, rnd):
    """Rounded cartoon tree crown made of overlapping circles, outlined."""
    blobs = []
    for _ in range(7):
        bx = x + rnd.uniform(-w * 0.45, w * 0.45)
        by = base - h * rnd.uniform(0.35, 0.85)
        blobs.append((bx, by, rnd.uniform(w * 0.22, w * 0.34)))
    for bx, by, r in blobs:
        cv.circle((bx, by), r + lw, fill=ink)
    for bx, by, r in blobs:
        cv.circle((bx, by), r, fill=color)
    for bx, by, r in blobs[:3]:
        cv.arc((bx, by), r * 0.65, 200, 280, mix(color, (255, 255, 255), 0.18), lw)


def _toon(cv, s, W, H, ground, th, rnd):
    """C1: dusky teal cartoon world with thick outlines (forest road by default)."""
    if s in ("room", "office", "classroom", "space", "beach", "stage"):
        _color_scene(cv, s, W, H, ground, th, rnd)
        return
    ink = (24, 34, 40)
    lw = max(2, H * 0.005)
    night = s in ("night", "city")
    _vgrad(cv, W, 0, ground, (18, 44, 58) if night else (30, 80, 92), (40, 96, 104) if night else (70, 140, 140))
    if night:
        for _ in range(30):
            cv.circle((rnd.uniform(0, W), rnd.uniform(0, ground * 0.5)), rnd.uniform(1, 2.4), fill=(230, 245, 240))
        cv.circle((W * 0.82, H * 0.14), H * 0.05, fill=(250, 244, 210))
    if s == "city":
        x = rnd.uniform(-40, 0)
        while x < W:
            bw, bh = rnd.uniform(90, 160), rnd.uniform(H * 0.22, H * 0.48)
            col = rnd.choice([(40, 70, 90), (52, 86, 104), (34, 60, 80)])
            cv.rect((x, ground - bh, x + bw, ground), fill=col, outline=ink, width=lw)
            for wy in range(int(ground - bh + 18), int(ground - 30), 34):
                for wx in range(int(x + 14), int(x + bw - 22), 30):
                    if rnd.random() < 0.55:
                        cv.rect((wx, wy, wx + 14, wy + 18), fill=(255, 214, 110), outline=ink, width=lw * 0.5)
            x += bw + rnd.uniform(6, 24)
    else:
        # far trees, trunks, near trees
        for i in range(9):
            _tree_clump(cv, W * (i / 8) + rnd.uniform(-30, 30), ground - H * 0.12, W * 0.16, H * 0.5,
                        (26, 72, 72), mix(ink, (26, 72, 72), 0.4), lw * 0.6, rnd)
        for i in range(6):
            tx = W * (0.04 + i * 0.19) + rnd.uniform(-20, 20)
            cv.rect((tx - W * 0.014, ground - H * 0.42, tx + W * 0.014, ground), fill=(70, 52, 50), outline=ink, width=lw)
            _tree_clump(cv, tx, ground - H * 0.3, W * 0.2, H * 0.42, (40, 104, 92), ink, lw, rnd)
        for i in range(12):                                          # bushes along the road
            bx = W * i / 11 + rnd.uniform(-20, 20)
            r = H * rnd.uniform(0.04, 0.07)
            cv.circle((bx, ground - r * 0.4), r + lw, fill=ink)
            cv.circle((bx, ground - r * 0.4), r, fill=(52, 124, 98))
    # road with a curb and dashed centre line
    cv.rect((0, ground - H * 0.015, W, ground + H * 0.01), fill=(150, 160, 160), outline=ink, width=lw)
    cv.rect((0, ground + H * 0.01, W, H), fill=(58, 66, 78))
    y = ground + (H - ground) * 0.55
    for x in range(0, int(W) + 120, 120):
        cv.rect((x, y, x + 60, y + H * 0.012), fill=(240, 236, 220), radius=3)


def call_panels(W, H):
    """The two rooms of a phone call: stacked on tall videos, side by side otherwise."""
    if H > W * 1.15:
        return [(0, 0, W, H / 2), (0, H / 2, W, H)]
    return [(0, 0, W / 2, H), (W / 2, 0, W, H)]


def _bedroom(cv, box, H, girl):
    """Night-time bedroom with thick outlines, decorated at the sides so the character stays clear."""
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    ink, lw = (24, 34, 40), max(2, H * 0.004)
    wall = (222, 138, 160) if girl else (56, 108, 122)
    cv.rect(box, fill=wall)
    cv.rect((x0, y0, x1, y0 + h * 0.05), fill=mix(wall, (255, 255, 255), 0.18))
    # window with the moon (the same night in both rooms)
    wx0, wy0, wx1, wy1 = x0 + w * 0.05, y0 + h * 0.13, x0 + w * 0.3, y0 + h * 0.56
    cv.rect((wx0, wy0, wx1, wy1), fill=(22, 36, 66), outline=ink, width=lw * 1.4)
    cv.circle((wx0 + (wx1 - wx0) * 0.62, wy0 + (wy1 - wy0) * 0.3), w * 0.04, fill=(250, 240, 200))
    cv.line([((wx0 + wx1) / 2, wy0), ((wx0 + wx1) / 2, wy1)], ink, lw)
    cv.line([(wx0, (wy0 + wy1) / 2), (wx1, (wy0 + wy1) / 2)], ink, lw)
    if girl:
        for a, b in ((wx0 - w * 0.03, wx0 + w * 0.05), (wx1 - w * 0.05, wx1 + w * 0.03)):
            cv.rect((a, wy0 - h * 0.03, b, wy1 + h * 0.05), fill=(250, 226, 150), outline=ink, width=lw, radius=w * 0.015)
    # right side: mirror and heart for her, poster and shelf for him
    px = x0 + w * 0.84
    if girl:
        cv.ellipse((px - w * 0.075, y0 + h * 0.12, px + w * 0.075, y0 + h * 0.44), fill=(190, 226, 232), outline=(214, 170, 70), width=lw * 2)
        cv.line([(px - w * 0.03, y0 + h * 0.3), (px + w * 0.03, y0 + h * 0.2)], (240, 250, 250), lw * 1.5)
        for k in range(9):                                            # string lights
            lx = x0 + w * (0.04 + k * 0.115)
            ly = y0 + h * (0.075 + 0.03 * (k % 2))
            cv.circle((lx, ly), h * 0.012, fill=[(255, 226, 120), (255, 255, 255), (150, 225, 240)][k % 3], outline=ink, width=lw * 0.6)
    else:
        cv.rect((px - w * 0.09, y0 + h * 0.1, px + w * 0.09, y0 + h * 0.4), fill=(236, 96, 40), outline=ink, width=lw * 1.4)
        cv.circle((px, y0 + h * 0.23), w * 0.05, fill=(255, 200, 40), outline=ink, width=lw)
        cv.rect((px - w * 0.12, y0 + h * 0.54, px + w * 0.12, y0 + h * 0.565), fill=(120, 80, 60), outline=ink, width=lw)
        for k, col in enumerate([(235, 80, 70), (250, 190, 40), (70, 150, 230), (240, 236, 220)]):
            bx = px - w * 0.1 + k * w * 0.05
            cv.rect((bx, y0 + h * 0.455, bx + w * 0.042, y0 + h * 0.54), fill=col, outline=ink, width=lw * 0.7)
    # bed along the bottom
    cv.rect((x0 - 20, y0 + h * 0.8, x1 + 20, y1 + 20), fill=(250, 200, 214) if girl else (70, 96, 150), outline=ink, width=lw * 1.5)
    cv.rect((x0 + w * 0.03, y0 + h * 0.69, x0 + w * 0.27, y0 + h * 0.83), fill=(255, 255, 255) if girl else (236, 232, 220), outline=ink, width=lw * 1.2, radius=h * 0.04)


def draw_call_rooms(W, H, th):
    """Background for a phone-call scene: his room first, her room second."""
    img = new_image(W, H, th["bg"])
    cv = Canvas(img)
    for k, box in enumerate(call_panels(W, H)):
        _bedroom(cv, box, H, k == 1)
    return img


def standup_floor(H):
    return H * 0.76


def draw_curtain_stage(W, H, th):
    """Theatre stage for standup: red curtain folds, drapes tied back, a hanging lamp, footlights."""
    img = new_image(W, H, (96, 10, 16))
    cv = Canvas(img)
    floor = standup_floor(H)
    ink = (40, 8, 12)
    n = 14
    for i in range(n):                                                               # folds: bright ridge, dark seams
        x0, w = W * i / n, W / n
        cv.rect((x0, 0, x0 + w, floor), fill=(140, 16, 24))
        cv.rect((x0 + w * 0.22, 0, x0 + w * 0.62, floor), fill=(192, 30, 38))
        cv.rect((x0 + w * 0.34, 0, x0 + w * 0.48, floor), fill=(222, 58, 58))
    cv.poly([(W * 0.43, H * 0.07), (W * 0.57, H * 0.07), (W * 0.9, floor), (W * 0.1, floor)], fill=(255, 222, 110, 60))
    for side in (1, -1):                                                             # side drapes
        def X(v):
            return v if side > 0 else W - v
        pts = [(X(0), 0), (X(W * 0.3), 0), (X(W * 0.2), H * 0.2), (X(W * 0.09), H * 0.42), (X(W * 0.12), H * 0.5),
               (X(W * 0.17), floor), (X(0), floor)]
        cv.poly([(px, py) for px, py in pts], fill=(176, 20, 30), outline=ink, width=3)
        for k in (0.05, 0.12, 0.19):
            cv.line([(X(W * k), 0), (X(W * 0.06), H * 0.43)], (120, 10, 18), 3)
            cv.line([(X(W * 0.07), H * 0.5), (X(W * (k - 0.02)), floor)], (120, 10, 18), 3)
        cv.rect((min(X(W * 0.04), X(W * 0.14)), H * 0.43, max(X(W * 0.04), X(W * 0.14)), H * 0.47), fill=(232, 176, 44), outline=ink, width=2, radius=6)
    cv.rect((0, 0, W, H * 0.035), fill=(110, 10, 18))                                 # valance
    for i in range(9):
        cv.circle((W * (i + 0.5) / 9, H * 0.035), W / 18, fill=(110, 10, 18))
    cv.line([(W * 0.5, 0), (W * 0.5, H * 0.045)], (30, 30, 34), 4)                    # hanging lamp
    cv.poly([(W * 0.46, H * 0.045), (W * 0.54, H * 0.045), (W * 0.6, H * 0.075), (W * 0.4, H * 0.075)], fill=(52, 52, 58), outline=(20, 20, 24), width=2)
    cv.ellipse((W * 0.43, H * 0.066, W * 0.57, H * 0.086), fill=(255, 238, 150))
    cv.rect((0, floor, W, H), fill=(166, 100, 50))
    for i in range(1, 10):
        px = W * i / 10
        cv.line([(W / 2 + (px - W / 2) * 0.8, floor), (W / 2 + (px - W / 2) * 1.5, H)], (124, 72, 34), max(2, H * 0.002))
    cv.ellipse((W * 0.12, floor + H * 0.0, W * 0.88, floor + H * 0.07), fill=(255, 214, 110, 110))
    cv.rect((0, floor - H * 0.003, W, floor + H * 0.003), fill=(80, 40, 20))
    edge = H * 0.805                                                                  # front of the stage with footlights
    cv.rect((0, edge, W, edge + H * 0.03), fill=(70, 34, 18))
    for i in range(6):
        bx = W * (i + 0.5) / 6
        cv.circle((bx, edge + H * 0.015), H * 0.016, fill=(255, 220, 120, 90))
        cv.circle((bx, edge + H * 0.015), H * 0.009, fill=(255, 240, 170))
    return img


def draw_standup_stage(W, H, th):
    """Comedy club: brick wall in one warm spotlight, wooden stage. The audience is drawn per frame."""
    img = new_image(W, H, (26, 16, 18))
    cv = Canvas(img)
    floor = standup_floor(H)
    rng = random.Random(11)
    bh, bw = H * 0.03, H * 0.075
    dark = (28, 16, 20)
    y, row = 0.0, 0
    while y < floor:
        x = -bw * (0.5 if row % 2 else 1.0)
        while x < W:
            cx, cy = (x + bw / 2 - W / 2) / W, (y - H * 0.38) / H
            k = min(1.0, math.hypot(cx * 1.15, cy * 1.5) * 1.75)                     # falls off away from the spot
            col = mix((150, 72, 54), (112, 50, 42), rng.random())
            cv.rect((x + 2, y + 2, x + bw - 2, y + bh - 2), fill=mix(col, dark, 0.2 + 0.72 * k), radius=2)
            x += bw
        y += bh
        row += 1
    cv.poly([(W * 0.42, 0), (W * 0.58, 0), (W * 0.86, floor), (W * 0.14, floor)], fill=(255, 196, 110, 42))
    cv.rect((0, floor, W, H), fill=(58, 36, 28))
    for i in range(1, 7):                                                            # planks run toward the crowd
        px = W * i / 7
        cv.line([(W / 2 + (px - W / 2) * 0.8, floor), (W / 2 + (px - W / 2) * 1.5, H)], (40, 25, 21), max(2, H * 0.002))
    cv.ellipse((W * 0.14, floor + H * 0.005, W * 0.86, floor + H * 0.1), fill=(255, 200, 120, 64))
    cv.rect((0, floor - H * 0.003, W, floor + H * 0.003), fill=(20, 12, 14))
    return img


WORLDS = {"cave": _cave, "edo": _edo, "egypt": _egypt, "rome": _rome, "amber": _amber, "toon": _toon}
