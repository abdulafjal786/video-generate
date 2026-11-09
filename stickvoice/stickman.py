"""Skeletal stickman: poses, actions and drawing.

A pose is a dict of joint angles in degrees. Limb angles are measured from
"straight down" and grow towards the direction the character faces.
Elbows/knees are relative to their parent limb.
"""
import math

from .canvas import lerp, clamp, smooth

# ---------------------------------------------------------------------------
# Base pose and the angle keys every pose has
# ---------------------------------------------------------------------------
STAND = {
    "lean": 0.0, "head": 0.0,
    "aA_s": 14.0, "aA_e": 8.0,    # front arm: shoulder, elbow
    "aB_s": -14.0, "aB_e": 8.0,   # back arm
    "lA_h": 6.0, "lA_k": -2.0,    # front leg: hip, knee
    "lB_h": -6.0, "lB_k": -2.0,   # back leg
    "lift": 0.0,                  # extra height above ground (jumps)
}
ANGLE_KEYS = list(STAND.keys())

ACTIONS = [
    "talk", "wave", "point", "present", "think", "idea", "cheer", "jump", "clap",
    "sad", "shrug", "surprised", "scared", "angry", "facepalm", "walk", "run",
    "sit", "phone", "read", "write", "dance", "nod", "bow", "relax", "ride", "stand", "laugh", "slap",
]

MOODS = ["happy", "neutral", "sad", "surprised", "angry", "worried", "laugh"]

# default face for each action (scene "mood" overrides it)
ACTION_MOOD = {
    "cheer": "happy", "jump": "happy", "clap": "happy", "dance": "happy", "wave": "happy",
    "idea": "happy", "sad": "sad", "facepalm": "sad", "surprised": "surprised",
    "scared": "worried", "angry": "angry", "think": "neutral", "shrug": "neutral",
    "relax": "happy", "bow": "happy", "laugh": "laugh", "slap": "laugh",
}

SLAP_PERIOD = 0.6  # seconds between two hits of the "slap" action


def _s(t, period, phase=0.0):
    return math.sin(2 * math.pi * (t / period + phase))


def slap_lift(t):
    """Slapping arm over time: 0 = hand landing (every SLAP_PERIOD), 1 = fully raised."""
    p = (t % SLAP_PERIOD) / SLAP_PERIOD
    return smooth(p / 0.7) if p < 0.7 else 1 - smooth((p - 0.7) / 0.3)


def walk_cycle(t, speed=1.0, big=False):
    """Leg/arm swing for walking or running (speed = steps per second / 2)."""
    ph = 2 * math.pi * t * speed
    amp = 38 if big else 26
    p = {
        "lA_h": amp * math.sin(ph), "lB_h": -amp * math.sin(ph),
        "lA_k": -(8 + (55 if big else 38) * max(0.0, -math.sin(ph + 0.6))),
        "lB_k": -(8 + (55 if big else 38) * max(0.0, math.sin(ph + 0.6))),
        "aA_s": -(30 if big else 22) * math.sin(ph), "aB_s": (30 if big else 22) * math.sin(ph),
        "aA_e": 25 + (40 if big else 10), "aB_e": 25 + (40 if big else 10),
        "lean": 12 if big else 3,
        "lift": (10 if big else 3) * abs(math.sin(ph)),
    }
    return p


def action_pose(action, t, talking=0.0, seed=0.0):
    """Pose overrides for an action at scene-time t (seconds)."""
    a = action
    p = {}
    breath = _s(t, 3.4, seed)
    p["lean"] = 1.2 * breath
    p["head"] = 2.0 * _s(t, 4.1, seed + 0.3)

    if a in ("talk", "stand"):
        # conversational hand gestures that change every ~1.6 s
        g = int((t + seed * 3) / 1.6) % 4
        k = smooth(((t + seed * 3) % 1.6) / 0.4)
        targets = [
            {"aA_s": 48, "aA_e": 55, "aB_s": -12, "aB_e": 10},   # open front hand
            {"aA_s": 30, "aA_e": 85, "aB_s": 30, "aB_e": 70},    # both hands explaining
            {"aA_s": 60, "aA_e": 20, "aB_s": -18, "aB_e": 12},   # reach out
            {"aA_s": 22, "aA_e": 100, "aB_s": -40, "aB_e": 60},  # hand up, palm open
        ]
        if a == "stand":
            targets = [{"aA_s": 14, "aA_e": 8, "aB_s": -14, "aB_e": 8}]
            g, k = 0, 1
        prev = targets[(g - 1) % len(targets)]
        cur = targets[g]
        for key in cur:
            p[key] = lerp(prev[key], cur[key], k) + 4 * _s(t, 0.9, seed) * talking
        p["head"] += 3 * _s(t, 0.7, seed) * talking
    elif a == "wave":
        p.update({"aA_s": 118, "aA_e": 38 + 28 * _s(t, 0.55), "aB_s": -12, "aB_e": 10, "head": 6})
    elif a == "point":
        p.update({"aA_s": 92 + 3 * _s(t, 1.4), "aA_e": 0, "aB_s": -10, "aB_e": 15, "lean": 4})
    elif a == "present":
        p.update({"aA_s": 70 + 8 * _s(t, 2.2), "aA_e": 25, "aB_s": 25, "aB_e": 60, "lean": 2})
    elif a == "think":
        p.update({"aA_s": 28, "aA_e": 128, "aB_s": 35, "aB_e": 95, "head": -10 + 3 * _s(t, 2.5),
                  "lean": -2})
    elif a == "idea":
        up = smooth(t / 0.5)
        p.update({"aA_s": lerp(30, 125, up), "aA_e": lerp(100, 40, up), "aB_s": -15, "aB_e": 10,
                  "head": -8, "lift": 18 * max(0.0, math.sin(min(t, 0.6) / 0.6 * math.pi))})
    elif a in ("cheer", "jump"):
        hop = abs(math.sin(math.pi * t / 0.55))
        p.update({"aA_s": 128 + 8 * _s(t, 0.55), "aA_e": 22, "aB_s": -128 - 8 * _s(t, 0.55),
                  "aB_e": -22, "lift": (60 if a == "jump" else 30) * hop,
                  "lA_h": 10 + 20 * hop, "lA_k": -40 * hop, "lB_h": -10 + 15 * hop, "lB_k": -45 * hop})
    elif a == "clap":
        c = abs(_s(t, 0.45))
        p.update({"aA_s": 70, "aA_e": 60 + 25 * c, "aB_s": 70, "aB_e": 60 + 25 * c, "head": 4})
    elif a == "sad":
        p.update({"aA_s": 4, "aA_e": 2, "aB_s": -4, "aB_e": 2, "lean": 14 + 1.5 * breath,
                  "head": 22, "lA_h": 3, "lB_h": -3})
    elif a == "shrug":
        k = 0.5 + 0.5 * _s(t, 1.8)
        p.update({"aA_s": 35, "aA_e": 85 + 10 * k, "aB_s": -35, "aB_e": -85 - 10 * k,
                  "head": 10 * _s(t, 1.8), "lift": 4 * k})
    elif a == "surprised":
        jolt = math.exp(-t * 4) * math.sin(t * 25)
        p.update({"aA_s": 125, "aA_e": 45, "aB_s": -125, "aB_e": -45, "lean": -6 + 5 * jolt,
                  "lift": 25 * max(0.0, math.sin(min(t, 0.4) / 0.4 * math.pi))})
    elif a == "scared":
        sh = 3 * math.sin(t * 40)
        p.update({"aA_s": 60, "aA_e": 110, "aB_s": 60, "aB_e": 115, "lean": -10 + sh,
                  "lA_h": 15, "lA_k": -30, "lB_h": -10, "lB_k": -30, "head": -6 + sh})
    elif a == "angry":
        st = abs(_s(t, 0.5))
        p.update({"aA_s": 30, "aA_e": 105, "aB_s": -30, "aB_e": -105, "lean": 8,
                  "lA_h": 12 + 10 * st, "lA_k": -20 * st, "head": 6})
    elif a == "facepalm":
        p.update({"aA_s": 62, "aA_e": 118, "aB_s": -6, "aB_e": 4, "head": 18 + 4 * _s(t, 1.3),
                  "lean": 8})
    elif a == "walk":
        p.update(walk_cycle(t, 0.9))
    elif a == "run":
        p.update(walk_cycle(t, 1.6, big=True))
    elif a == "sit":
        p.update({"lA_h": 88, "lA_k": -88, "lB_h": 82, "lB_k": -86, "lean": -4 + breath,
                  "aA_s": 45 + 10 * _s(t, 1.6) * talking, "aA_e": 60, "aB_s": 20, "aB_e": 50})
    elif a == "phone":
        p.update({"aA_s": 35, "aA_e": 105, "aB_s": 25, "aB_e": 95, "head": 14,
                  "lean": 3})
    elif a == "read":
        p.update({"aA_s": 45, "aA_e": 80, "aB_s": 40, "aB_e": 85, "head": 16 + 2 * _s(t, 2)})
    elif a == "write":
        p.update({"aA_s": 100 + 12 * _s(t, 0.6), "aA_e": 20 + 15 * _s(t, 0.45), "aB_s": -10,
                  "aB_e": 15, "lean": 5, "head": -4})
    elif a == "dance":
        b = _s(t, 0.8)
        p.update({"aA_s": 95 + 35 * b, "aA_e": 40, "aB_s": -95 + 35 * b, "aB_e": -40,
                  "lA_h": 25 * b, "lA_k": -30 * abs(b), "lB_h": -25 * b, "lB_k": -30 * abs(b),
                  "lean": 10 * b, "head": 12 * b, "lift": 12 * abs(b)})
    elif a == "nod":
        p.update({"head": 12 * abs(_s(t, 0.8)), "aA_s": 20, "aA_e": 10, "aB_s": -20, "aB_e": 10})
    elif a == "bow":
        k = smooth(min(t, 1.0) / 0.6)
        p.update({"lean": 40 * k, "head": 15 * k, "aA_s": 10, "aA_e": 0, "aB_s": -5, "aB_e": 0})
    elif a in ("ride", "ride_back"):  # seated on a bike; arms are aimed at the grips by reach_arms()
        p.update({"lA_h": 72, "lA_k": -88, "lB_h": 66, "lB_k": -84, "lean": 8 + 1.5 * _s(t, 0.5, seed),
                  "head": 3 * _s(t, 1.7, seed) + 3 * _s(t, 0.7, seed) * talking})
    elif a == "laugh":
        sh = _s(t, 0.28)
        p.update({"aA_s": 30, "aA_e": 100, "aB_s": 25, "aB_e": 95, "lean": 10 + 5 * sh, "head": -12 + 6 * sh,
                  "lift": 3 * abs(sh)})
    elif a == "slap":
        k = slap_lift(t)
        p.update({"aA_s": lerp(75, 150, k), "aA_e": lerp(5, 60, k), "aB_s": 30, "aB_e": 95, "lean": 6 - 4 * k,
                  "head": -8 + 4 * _s(t, 0.28)})
    elif a == "relax":
        p.update({"aA_s": 150, "aA_e": 140, "aB_s": -150, "aB_e": -140, "lean": -4 + breath,
                  "head": -6})
    return p


def make_pose(action, t, talking=0.0, seed=0.0):
    pose = dict(STAND)
    pose.update(action_pose(action, t, talking, seed))
    return pose


def reach_arms(pose, H, facing, target_a, target_b):
    """Two-bone IK: bend both arms so the hands land on targets (offsets from the hip, y down)."""
    j = solve(pose, H, facing)
    sh = j["shoulder"]
    u, f = 0.165 * H, 0.155 * H
    for side, tgt in (("A", target_a), ("B", target_b)):
        vx, vy = (tgt[0] - sh[0]) * facing, tgt[1] - sh[1]
        d = clamp(math.hypot(vx, vy), abs(u - f) + 1e-3, u + f - 1e-3)
        base = math.degrees(math.atan2(vx, vy))
        bend = math.degrees(math.acos(clamp((u * u + d * d - f * f) / (2 * u * d), -1, 1)))
        s_abs = base - bend if vx >= 0 else base + bend  # elbow bends downward, or out behind for a hand at the ear
        ex, ey = math.sin(math.radians(s_abs)) * u, math.cos(math.radians(s_abs)) * u
        f_abs = math.degrees(math.atan2(vx - ex, vy - ey))
        pose[f"a{side}_s"] = s_abs - pose["lean"]
        pose[f"a{side}_e"] = f_abs - s_abs
    return pose


def blend(p1, p2, k):
    return {key: lerp(p1[key], p2[key], k) for key in ANGLE_KEYS}


# ---------------------------------------------------------------------------
# Forward kinematics + drawing
# ---------------------------------------------------------------------------
def _dir(angle_deg, facing):
    a = math.radians(angle_deg)
    return (math.sin(a) * facing, math.cos(a))


def solve(pose, H, facing):
    """Joint positions relative to the hip (y down). H = character height."""
    torso, upper, fore, thigh, shin = 0.30 * H, 0.165 * H, 0.155 * H, 0.215 * H, 0.215 * H
    lean = math.radians(pose["lean"])
    hip = (0.0, 0.0)
    neck = (math.sin(lean) * facing * torso, -math.cos(lean) * torso)
    shoulder = (lerp(hip[0], neck[0], 0.9), lerp(hip[1], neck[1], 0.9))
    j = {"hip": hip, "neck": neck, "shoulder": shoulder}
    for side in ("A", "B"):
        s = pose[f"a{side}_s"] + pose["lean"]
        e = s + pose[f"a{side}_e"]
        d1, d2 = _dir(s, facing), _dir(e, facing)
        el = (shoulder[0] + d1[0] * upper, shoulder[1] + d1[1] * upper)
        j[f"elbow{side}"] = el
        j[f"hand{side}"] = (el[0] + d2[0] * fore, el[1] + d2[1] * fore)
        h = pose[f"l{side}_h"]
        k = h + pose[f"l{side}_k"]
        d1, d2 = _dir(h, facing), _dir(k, facing)
        kn = (hip[0] + d1[0] * thigh, hip[1] + d1[1] * thigh)
        j[f"knee{side}"] = kn
        j[f"foot{side}"] = (kn[0] + d2[0] * shin, kn[1] + d2[1] * shin)
    hd = math.radians(pose["lean"] * 0.6)
    head_r = 0.115 * H
    gap = 0.035 * H
    j["head"] = (neck[0] + math.sin(hd) * facing * (head_r + gap), neck[1] - math.cos(hd) * (head_r + gap))
    j["head_r"] = head_r
    return j


def draw_stickman(cv, x, ground, H, pose, facing, theme, face, outfit=None):
    """Draw a stickman whose feet stand on `ground` at horizontal position x.

    face:   dict(mood, mouth_open 0..1, blink, look)
    outfit: costume dict. Keys (all optional):
      color (limb/outline ink), head (head fill), neck (True = short neck in head colour),
      eyes ("dot" | "oval" | "noir"), face_color, hands ("dot" | "mitten"),
      shirt (torso colour), shorts, tie, sleeves (colour of upper arms),
      robe {color, trim, length, top, bottom} long garment (kimono, tunic, toga, dress),
      tunic {color, spots} ragged animal hide, kilt (colour), belt (colour), collar (colour),
      hood (colour), sash (colour), breastplate (colour),
      headwear: "beanie" | "topknot" | "nemes" | "helmet" | "bun" | "wild" | "bob" | "laurel" | "hair",
      headwear_color, crest (colour), weapon ("katana" | "spear" | "club"), necklace (colour)
    """
    outfit = outfit or {}
    if outfit.get("body") == "toon":
        return draw_toon(cv, x, ground, H, pose, facing, theme, face, outfit)
    j = solve(pose, H, facing)
    foot_drop = max(j["footA"][1], j["footB"][1])
    oy = ground - foot_drop - pose["lift"]

    def P(name):
        px, py = j[name]
        return (x + px, oy + py)

    ink = outfit.get("color", theme["ink"])
    head_fill = outfit.get("head", theme["head"])
    w = max(2.0, 0.036 * H)
    hc = P("head")
    r = j["head_r"]
    neck, hip = P("neck"), P("hip")

    def limb(a, b, c, width=w, color=ink):
        cv.line([P(a), P(b), P(c)], color, width)

    def torso_point(t, side=0.0):
        """Point at fraction t from neck (0) to hip (1), offset sideways by `side` px."""
        dx, dy = hip[0] - neck[0], hip[1] - neck[1]
        L = math.hypot(dx, dy) or 1
        px, py = -dy / L, dx / L
        return (neck[0] + dx * t + px * side, neck[1] + dy * t + py * side)

    # --- legs + shoes ------------------------------------------------------
    for side in ("B", "A"):
        limb("hip", f"knee{side}", f"foot{side}")
        f = P(f"foot{side}")
        cv.line([f, (f[0] + facing * H * 0.05, f[1])], ink, w * 1.1)
    if outfit.get("shorts"):
        for side in ("A", "B"):
            k = P(f"knee{side}")
            mid = (lerp(hip[0], k[0], 0.5), lerp(hip[1], k[1], 0.5))
            cv.line([hip, mid], ink, w * 3.0)
            cv.line([hip, mid], outfit["shorts"], w * 2.0)

    # --- back arm ------------------------------------------------------------
    def arm(side):
        limb("shoulder", f"elbow{side}", f"hand{side}")
        if outfit.get("sleeves"):
            el = P(f"elbow{side}")
            cv.line([P("shoulder"), el], ink, w * 2.6)
            cv.line([P("shoulder"), el], outfit["sleeves"], w * 1.6)
        hand = P(f"hand{side}")
        if outfit.get("hands") == "mitten":
            cv.circle(hand, w * 1.25, fill=ink)
        else:
            cv.circle(hand, w * 0.75, fill=ink)

    if outfit.get("weapon") == "spear":
        hb = P("handB")
        cv.line([(hb[0], hb[1] + H * 0.25), (hb[0], hb[1] - H * 0.45)], (120, 85, 50), w * 0.9)
        cv.poly([(hb[0], hb[1] - H * 0.55), (hb[0] - w * 1.2, hb[1] - H * 0.44), (hb[0] + w * 1.2, hb[1] - H * 0.44)],
                fill=(170, 170, 178), outline=ink, width=w * 0.4)
    arm("B")

    # --- hood (behind head) ---------------------------------------------------
    if outfit.get("hood"):  # hood down, bunched behind the neck
        hx, hy = neck[0] - facing * r * 0.35, neck[1] - r * 0.15
        cv.ellipse((hx - r * 0.75, hy - r * 0.45, hx + r * 0.75, hy + r * 0.4), fill=outfit["hood"], outline=ink, width=w * 0.6)

    # --- torso / garments ----------------------------------------------------
    robe = outfit.get("robe")
    tunic = outfit.get("tunic")
    if robe:
        L = robe.get("length", 1.45)
        tw, bw = H * robe.get("top", 0.075), H * robe.get("bottom", 0.13)
        pts = [torso_point(-0.02, -tw), torso_point(-0.02, tw), torso_point(L, bw), torso_point(L, -bw)]
        cv.poly(pts, fill=robe["color"], outline=ink, width=w * 0.8)
        if robe.get("trim"):
            cv.line([torso_point(-0.02, -tw * 0.2), torso_point(0.45, tw * 0.25)], robe["trim"], w * 0.9)
            cv.line([torso_point(-0.02, tw * 0.2), torso_point(0.45, -tw * 0.25)], robe["trim"], w * 0.9)
        if robe.get("sash"):
            cv.line([torso_point(0.55, -tw * 1.15), torso_point(0.55, tw * 1.15)], robe["sash"], w * 1.6)
    elif tunic:
        tw, bw = H * 0.075, H * 0.12
        pts = [torso_point(0.0, -tw), torso_point(0.0, tw)]
        n = 7
        for k in range(n + 1):  # ragged hem
            side = bw - 2 * bw * k / n
            pts.append(torso_point(1.22 + (0.1 if k % 2 else 0.0), side))
        cv.poly(pts, fill=tunic["color"], outline=ink, width=w * 0.8)
        for (t, sd) in ((0.3, -0.4), (0.55, 0.5), (0.85, -0.1), (1.05, 0.6)):
            cv.circle(torso_point(t, sd * tw), w * 0.9, fill=tunic.get("spots", (120, 80, 45)))
        cv.line([torso_point(0.02, tw * 0.9), torso_point(0.0, -tw)], ink, w * 0.5)  # one-shoulder strap
    else:
        shirt = outfit.get("shirt")
        if shirt:
            cv.line([hip, neck], ink, w * 3.6)
            cv.line([hip, neck], shirt, w * 2.4)
        else:
            cv.line([hip, neck], ink, w)
    if outfit.get("breastplate"):
        bp = outfit["breastplate"]
        cv.poly([torso_point(0.05, -H * 0.07), torso_point(0.05, H * 0.07), torso_point(0.75, H * 0.06), torso_point(0.75, -H * 0.06)],
                fill=bp, outline=ink, width=w * 0.7)
        cv.line([torso_point(0.4, -H * 0.05), torso_point(0.4, H * 0.05)], ink, w * 0.4)
    if outfit.get("kilt"):
        pts = [torso_point(0.85, -H * 0.075), torso_point(0.85, H * 0.075), torso_point(1.38, H * 0.1), torso_point(1.38, -H * 0.1)]
        cv.poly(pts, fill=outfit["kilt"], outline=ink, width=w * 0.7)
        cv.line([torso_point(0.9, 0), torso_point(1.36, H * 0.03)], ink, w * 0.3)
    if outfit.get("belt"):
        cv.line([torso_point(0.85, -H * 0.08), torso_point(0.85, H * 0.08)], outfit["belt"], w * 1.2)
    if outfit.get("tie"):
        t1, t2 = torso_point(0.12), torso_point(0.55)
        cv.poly([(t1[0] - w * 0.5, t1[1]), (t1[0] + w * 0.5, t1[1]), (t2[0] + w * 0.8, t2[1]),
                 (t2[0], t2[1] + w * 1.2), (t2[0] - w * 0.8, t2[1])], fill=outfit["tie"])
    if outfit.get("collar"):
        cv.arc((neck[0], neck[1] - H * 0.005), H * 0.07, 10, 170, outfit["collar"], w * 1.5)
    if outfit.get("necklace"):
        for k in range(5):
            a = math.radians(30 + k * 30)
            cv.circle((neck[0] + math.cos(a) * H * 0.055, neck[1] + math.sin(a) * H * 0.04), w * 0.45, fill=outfit["necklace"])
    if outfit.get("weapon") == "katana":
        a, b = torso_point(0.95, -facing * H * 0.02), torso_point(0.7, facing * H * 0.02)
        dx, dy = a[0] - b[0], a[1] - b[1]
        cv.line([(a[0] - dx * 1.6 - facing * H * 0.12, a[1] + H * 0.02), (a[0] + facing * H * 0.1, a[1] - H * 0.03)], (40, 40, 45), w * 0.9)
    if outfit.get("weapon") == "club":
        ha = P("handA")
        cv.line([ha, (ha[0] + facing * H * 0.05, ha[1] - H * 0.2)], (130, 90, 55), w * 1.6)
        cv.circle((ha[0] + facing * H * 0.06, ha[1] - H * 0.21), w * 1.6, fill=(130, 90, 55), outline=ink, width=w * 0.4)

    # --- front arm ---------------------------------------------------------------
    arm("A")

    # --- neck + head -------------------------------------------------------------
    if outfit.get("neck"):
        nb = (hc[0], hc[1] + r * 0.85)
        cv.line([neck, nb], ink, w * 2.4)
        cv.line([neck, nb], head_fill, w * 1.2)
    headwear = outfit.get("headwear")
    hwc = outfit.get("headwear_color", ink)
    if headwear == "nemes":  # Egyptian striped headdress, behind the head
        stripe = outfit.get("headwear_stripe", (230, 190, 70))
        for sd in (-1, 1):  # two flaps falling behind the shoulders
            x0 = hc[0] + sd * r * 0.98
            flap = [(x0 - r * 0.2, hc[1] - r * 0.1), (x0 + r * 0.2, hc[1] - r * 0.1),
                    (x0 + sd * r * 0.12 + r * 0.18, hc[1] + r * 1.4), (x0 + sd * r * 0.12 - r * 0.18, hc[1] + r * 1.4)]
            cv.poly(flap, fill=hwc, outline=ink, width=w * 0.5)
            for k in range(1, 4):
                y = hc[1] + k * r * 0.33
                cv.line([(x0 - r * 0.18 + sd * k * r * 0.03, y), (x0 + r * 0.18 + sd * k * r * 0.03, y)], stripe, w * 0.55)
    if headwear == "bob":
        cv.circle((hc[0] - facing * r * 0.12, hc[1] + r * 0.05), r * 1.18, fill=hwc)
    cv.circle(hc, r, fill=head_fill, outline=ink, width=w * 0.95)
    if headwear in ("hair", None) and outfit.get("hair"):
        cv.arc(hc, r * 1.02, 195, 345, outfit["hair"], w * 1.6)
    elif headwear == "bob":
        cv.poly([(hc[0] - r * 1.05, hc[1] - r * 0.1)] + [(hc[0] + math.cos(math.radians(a)) * r * 1.06, hc[1] + math.sin(math.radians(a)) * r * 1.06)
                                                         for a in range(185, 356, 10)] + [(hc[0] + r * 1.05, hc[1] - r * 0.1), (hc[0], hc[1] - r * 0.45)],
                fill=hwc)
    elif headwear == "beanie":
        top = [(hc[0] - r * 1.02, hc[1] - r * 0.25)]
        for i in range(0, 181, 15):
            a = math.radians(180 + i)
            top.append((hc[0] + math.cos(a) * r * 1.05, hc[1] - r * 0.25 + math.sin(a) * r * 0.98))
        cv.poly(top, fill=hwc, outline=ink, width=w * 0.8)
        cv.rect((hc[0] - r * 1.1, hc[1] - r * 0.42, hc[0] + r * 1.1, hc[1] - r * 0.12),
                fill=tuple(max(0, c - 35) for c in hwc), outline=ink, width=w * 0.6, radius=r * 0.12)
    elif headwear == "topknot":
        cv.arc(hc, r * 1.0, 200, 340, hwc, w * 1.8)
        tk = (hc[0] - facing * r * 0.1, hc[1] - r * 1.08)
        cv.line([(tk[0] - facing * r * 0.35, tk[1] + r * 0.1), (tk[0] + facing * r * 0.45, tk[1] - r * 0.08)], hwc, w * 1.7)
    elif headwear == "bun":
        cv.arc(hc, r * 1.0, 190, 350, hwc, w * 1.9)
        cv.circle((hc[0] - facing * r * 0.55, hc[1] - r * 0.85), r * 0.38, fill=hwc)
        cv.line([(hc[0] - facing * r * 0.9, hc[1] - r * 1.1), (hc[0] - facing * r * 0.2, hc[1] - r * 0.6)], outfit.get("pin", (200, 60, 60)), w * 0.5)
    elif headwear == "wild":
        for k in range(7):
            a = 195 + k * 25
            p1 = polar_pt(hc, r * 0.92, a)
            p2 = polar_pt(hc, r * (1.35 + 0.12 * (k % 2)), a + 8)
            cv.line([p1, p2], hwc, w * 1.2)
        cv.arc(hc, r * 1.0, 190, 350, hwc, w * 1.4)
    elif headwear == "nemes":
        cv.poly([(hc[0] - r * 1.08, hc[1] - r * 0.12)] + [(hc[0] + math.cos(math.radians(a)) * r * 1.07, hc[1] + math.sin(math.radians(a)) * r * 1.07)
                                                          for a in range(190, 351, 10)] + [(hc[0] + r * 1.08, hc[1] - r * 0.12)],
                fill=hwc, outline=ink, width=w * 0.6)
        for k in range(2):
            y = hc[1] - r * (0.62 - k * 0.27)
            half = r * math.sqrt(max(0.0, 1.07 ** 2 - ((y - hc[1]) / r) ** 2))
            cv.line([(hc[0] - half, y), (hc[0] + half, y)], outfit.get("headwear_stripe", (230, 190, 70)), w * 0.7)
    elif headwear == "helmet":
        cv.poly([(hc[0] - r * 1.12, hc[1] - r * 0.05)] + [(hc[0] + math.cos(math.radians(a)) * r * 1.1, hc[1] + math.sin(math.radians(a)) * r * 1.1)
                                                          for a in range(185, 356, 10)] + [(hc[0] + r * 1.12, hc[1] - r * 0.05)],
                fill=hwc, outline=ink, width=w * 0.7)
        cv.line([(hc[0] - facing * r * 0.9, hc[1] - r * 0.05), (hc[0] - facing * r * 0.9, hc[1] + r * 0.6)], hwc, w * 1.6)
        crest = outfit.get("crest")
        if crest:
            cv.ellipse((hc[0] - r * 0.85, hc[1] - r * 1.5, hc[0] + r * 0.85, hc[1] - r * 0.95), fill=crest, outline=ink, width=w * 0.5)
    elif headwear == "laurel":
        for k in range(6):
            a = 200 + k * 28
            p = polar_pt(hc, r * 1.0, a)
            cv.ellipse((p[0] - r * 0.16, p[1] - r * 0.09, p[0] + r * 0.16, p[1] + r * 0.09), fill=(110, 160, 80))
    draw_face(cv, hc, r, facing, face, outfit.get("face_color", ink), w,
              beanie=headwear in ("beanie", "helmet", "nemes"), eyes=outfit.get("eyes", "dot"))
    return {"head": hc, "head_r": r, "handA": P("handA"), "handB": P("handB"), "hip": P("hip")}


def _shade(c, k=0.82):
    return tuple(int(v * k) for v in c)


def draw_toon(cv, x, ground, H, pose, facing, theme, face, outfit):
    """C1 cartoon character: big head with curly hair, shirt, jeans, sneakers, thick outlines.

    Uses the same skeleton as the stickman. Extra outfit keys: body="toon", skin, hair,
    glasses, shirt, pants, shoes, hairstyle="long"|"bald"|"strands"|"messy", hoodie, ripped, eyes="dot"|"big",
    overbite, head_scale, thin (stick limbs), tunic, sleeveless, shorts, barefoot, shoe_scale,
    stick_limbs (plain ink arms and legs, finger strokes, oval shoes), shade_head.
    """
    j = solve(pose, H, facing)
    foot_drop = max(j["footA"][1], j["footB"][1])
    oy = ground - foot_drop - pose["lift"] - H * 0.035

    def P(name):
        px, py = j[name]
        return (x + px, oy + py)

    ink = outfit.get("color", theme["ink"])
    skin = outfit.get("skin", theme["head"])
    shirt = outfit.get("shirt", (250, 196, 40))
    pants = outfit.get("pants", (66, 108, 170))
    shoes = outfit.get("shoes", (90, 96, 120))
    ol = max(2.0, 0.012 * H)            # outline thickness
    leg_w, arm_w = (0.03 * H, 0.032 * H) if outfit.get("thin") else (0.105 * H, 0.07 * H)
    hand_r = max(arm_w * 0.62, 0.03 * H)
    neck, hip = P("neck"), P("hip")
    long_hair = outfit.get("hairstyle") == "long"
    hair = outfit.get("hair", (34, 26, 28))
    r = 0.15 * H * outfit.get("head_scale", 1)
    hd = math.radians(pose["lean"] * 0.6 + pose["head"] * 0.4)
    hc = (neck[0] + math.sin(hd) * facing * r * 0.95, neck[1] - math.cos(hd) * r * 0.95)

    def tube(pts, width, color):
        cv.line(pts, ink, width + 2 * ol)
        cv.line(pts, color, width)

    def blob(c, r, color):
        cv.circle(c, r + ol, fill=ink)
        cv.circle(c, r, fill=color)

    # --- legs: jeans + sneakers (back leg slightly darker) ----------------------
    for side, k, off in (("B", 0.85, -0.035), ("A", 1.0, 0.035)):
        o = facing * off * H
        f = (P(f"foot{side}")[0] + o, P(f"foot{side}")[1])
        kn = (P(f"knee{side}")[0] + o, P(f"knee{side}")[1])
        if outfit.get("stick_limbs"):
            cv.line([(hip[0] + o, hip[1]), kn, f], ink, ol * 1.8)
            sx = f[0] + facing * H * 0.03
            cv.ellipse((sx - H * 0.055, f[1] - H * 0.022, sx + H * 0.055, f[1] + H * 0.026), fill=ink)
            continue
        if outfit.get("shorts"):
            mid = (lerp(hip[0] + o, kn[0], 0.85), lerp(hip[1], kn[1], 0.85))
            tube([mid, kn, f], leg_w * 0.62, _shade(skin, k))
            tube([(hip[0] + o, hip[1]), mid], leg_w * 1.1, _shade(pants, k))
        else:
            tube([(hip[0] + o, hip[1]), kn, f], leg_w, _shade(pants, k))
        if outfit.get("ripped"):                                                           # torn knees
            for dy in (-0.022, 0.0, 0.022):
                cv.line([(kn[0] - leg_w * 0.28, kn[1] + dy * H), (kn[0] + leg_w * 0.28, kn[1] + (dy + 0.006) * H)], (226, 226, 220), ol * 0.8)
        sx = f[0] + facing * H * 0.03
        sw = H * 0.068 * outfit.get("shoe_scale", 1)
        sole = _shade(skin, k) if outfit.get("barefoot") else _shade(shoes, k)
        cv.ellipse((sx - sw - ol, f[1] - H * 0.035 - ol, sx + sw + ol, f[1] + H * 0.035 + ol), fill=ink)
        cv.ellipse((sx - sw, f[1] - H * 0.035, sx + sw, f[1] + H * 0.035), fill=sole)
        if outfit.get("barefoot"):                                                         # toes
            for i in range(3):
                tx = sx + facing * sw * (0.5 + 0.22 * i)
                cv.line([(tx, f[1] - H * 0.012), (tx, f[1] + H * 0.024)], ink, ol * 0.6)
        else:
            cv.rect((sx - sw, f[1] + H * 0.012, sx + sw, f[1] + H * 0.03), fill=(245, 245, 240), radius=H * 0.008)

    # --- arms: short sleeve + skin forearm + round hand -------------------------
    def arm(side, k):
        sh, el, hand = P("shoulder"), P(f"elbow{side}"), P(f"hand{side}")
        if outfit.get("stick_limbs"):
            cv.line([sh, el, hand], ink, ol * 1.8)
            a = math.atan2(hand[1] - el[1], hand[0] - el[0])
            for d in (-0.6, 0.0, 0.6):                                                    # three thin fingers
                cv.line([hand, (hand[0] + math.cos(a + d) * H * 0.03, hand[1] + math.sin(a + d) * H * 0.03)], ink, ol * 1.1)
            return
        if outfit.get("hoodie") or outfit.get("tunic"):                                    # long sleeves down to the wrist
            tube([sh, el, hand], arm_w * (2.2 if outfit.get("thin") else 1.15), _shade(shirt, k))
            blob(hand, hand_r, _shade(skin, k))
            return
        tube([sh, el, hand], arm_w * 0.8, _shade(skin, k))
        if outfit.get("sleeveless"):
            blob(hand, hand_r, _shade(skin, k))
            return
        mid = (lerp(sh[0], el[0], 0.75), lerp(sh[1], el[1], 0.75))
        tube([sh, mid], arm_w * 1.25, _shade(shirt, k))
        blob(hand, hand_r, _shade(skin, k))

    arm("B", 0.85)
    if outfit.get("stick_limbs"):                                                          # both arms come out from behind the body
        arm("A", 1.0)
    if long_hair:                                                                          # falls behind the shoulders
        hx = hc[0] - facing * r * 0.12
        cv.rect((hx - r * 1.14, hc[1] - r * 0.9, hx + r * 1.14, hc[1] + r * 2.5), fill=hair, outline=ink, width=ol * 1.2, radius=r * 0.7)

    # --- torso: rounded T-shirt ------------------------------------------------
    dx, dy = hip[0] - neck[0], hip[1] - neck[1]
    L = math.hypot(dx, dy) or 1
    nx, ny = -dy / L, dx / L

    def tp(t, side):
        return (neck[0] + dx * t + nx * side, neck[1] + dy * t + ny * side)

    tw, bw = H * 0.13, H * 0.12
    hem, flare = (1.72, 1.45) if outfit.get("tunic") else (1.12, 1.0)
    body = [tp(-0.05, -tw * 0.8), tp(-0.08, 0), tp(-0.05, tw * 0.8), tp(0.15, tw), tp(hem, bw * flare), tp(hem, -bw * flare), tp(0.15, -tw)]
    cv.poly(body, fill=shirt, outline=ink, width=ol * 1.6)
    cv.line([tp(hem - 0.07, -bw * 0.95 * flare), tp(hem - 0.07, bw * 0.95 * flare)], _shade(shirt, 0.88), ol)  # hem
    cv.arc(tp(-0.06, 0), H * 0.035, 20, 160, ink, ol * 0.8)                                # collar
    if outfit.get("hoodie"):                                                               # pocket, hood, drawstrings
        cv.poly([tp(0.72, -bw * 0.62), tp(0.72, bw * 0.62), tp(1.0, bw * 0.8), tp(1.0, -bw * 0.8)], fill=_shade(shirt, 0.9), outline=ink, width=ol * 0.8)
        c = tp(0.0, 0)
        cv.ellipse((c[0] - H * 0.125, c[1] - H * 0.055, c[0] + H * 0.125, c[1] + H * 0.06), fill=_shade(shirt, 0.8), outline=ink, width=ol)
        for side in (-0.16, 0.16):
            cv.line([tp(0.1, H * side * 0.4), tp(0.34, H * side * 0.46)], (245, 240, 228), ol * 0.8)

    if not outfit.get("stick_limbs"):
        arm("A", 1.0)

    # --- head --------------------------------------------------------------------
    # back of the hair (behind the head)
    back = 180 if facing > 0 else 0
    curls = [polar_pt(hc, r * 0.92, a) for a in range(195, 346, 22)]
    curls += [polar_pt(hc, r * 0.82, back + facing * d) for d in (-25, 5, 35)]
    style = outfit.get("hairstyle")
    if long_hair or style in ("bald", "strands", "messy"):
        curls = []
    for c in curls:
        cv.circle(c, r * 0.36 + ol, fill=ink)
    # face + ear
    cv.ellipse((hc[0] - r - ol, hc[1] - r * 0.95 - ol, hc[0] + r + ol, hc[1] + r * 1.02 + ol), fill=ink)
    cv.ellipse((hc[0] - r, hc[1] - r * 0.95, hc[0] + r, hc[1] + r * 1.02), fill=_shade(skin, 0.86) if outfit.get("shade_head") else skin)
    if outfit.get("shade_head"):                                                          # shadow on the back of the head
        k = facing * r * 0.1
        cv.ellipse((hc[0] - r * 0.9 + k, hc[1] - r * 0.88, hc[0] + r * 0.9 + k, hc[1] + r * 0.92), fill=skin)
    ear = (hc[0] - facing * r * 0.78, hc[1] + r * 0.1)
    if long_hair:                                                                         # swept fringe, front lock, earring
        part = (hc[0] + facing * r * 0.25, hc[1] - r * 0.6)
        cap = [polar_pt(hc, r * 1.06, a) for a in range(170, 371, 12)]
        cv.poly(cap + [(hc[0] + r * 1.02, hc[1] + r * 0.28), part, (hc[0] - r * 1.02, hc[1] + r * 0.28)],
                fill=hair, outline=ink, width=ol)
        cv.arc((hc[0] - facing * r * 0.2, hc[1] - r * 0.2), r * 0.62, 215, 300, _shade(hair, 1.9), ol * 0.8)
        lock = hc[0] - facing * r * 0.86
        tube([(lock, hc[1] + r * 0.1), (lock - facing * r * 0.06, hc[1] + r * 1.15), (lock + facing * r * 0.1, hc[1] + r * 1.9)], r * 0.3, hair)
    elif outfit.get("eyes") != "dot":                                                    # the simple faces have no ears
        blob(ear, r * 0.2, skin)
        cv.circle(ear, r * 0.08, fill=_shade(skin, 0.8))
    if style == "strands":                                                                # a few hairs on top
        for d in (-16, 0, 16):
            a, b = polar_pt(hc, r * 0.93, 270 + d), polar_pt(hc, r * 1.3, 270 + d * 1.5 + 8 * facing)
            cv.line([a, b], ink, ol * 0.9)
    elif style == "messy":                                                                # spiky mop
        cap = [polar_pt(hc, r * 1.03, a) for a in range(180, 361, 15)]
        cv.poly(cap + [(hc[0] + r * 0.98, hc[1] - r * 0.2), (hc[0], hc[1] - r * 0.52), (hc[0] - r * 0.98, hc[1] - r * 0.2)],
                fill=hair, outline=ink, width=ol)
        for i, a in enumerate(range(186, 355, 21)):
            tip = polar_pt(hc, r * (1.42 if i % 2 else 1.3), a + 7 * facing)
            cv.poly([polar_pt(hc, r * 0.92, a - 13), tip, polar_pt(hc, r * 0.92, a + 13)], fill=hair, outline=ink, width=ol)
    for c in curls:
        cv.circle(c, r * 0.36, fill=hair)
    for c in curls[1:-1:2]:                                                               # curl shine
        cv.arc(c, r * 0.2, 200, 290, _shade(hair, 1.9), ol * 0.7)
    _toon_face(cv, hc, r, facing, face, ink, ol, outfit.get("glasses"), skin, long_hair, outfit.get("eyes"), outfit.get("overbite"))
    return {"head": hc, "head_r": r, "handA": P("handA"), "handB": P("handB"), "hip": hip}


def _toon_face(cv, c, r, facing, face, ink, ol, glasses, skin, girl=False, eye_style=None, overbite=False):
    mood = face.get("mood", "neutral")
    look = face.get("look", 0.0)
    fx = c[0] + facing * r * 0.2 + look * r * 0.1
    ey = c[1] + r * 0.05
    er = r * (0.26 if mood in ("surprised", "worried") else 0.22) * (1.3 if eye_style == "big" else 1)
    eyes = [(fx - r * 0.3, ey), (fx + r * 0.3, ey)]
    if face.get("blink") or mood == "laugh":
        for e in eyes:
            cv.arc((e[0], e[1] + er * 0.4), er * 0.8, 200, 340, ink, ol * 1.1)
    elif eye_style == "dot":
        for e in eyes:
            k = 1.35 if mood == "surprised" else 1.0
            cv.ellipse((e[0] - r * 0.055 * k, e[1] - r * 0.09 * k, e[0] + r * 0.055 * k, e[1] + r * 0.09 * k), fill=ink)
    else:
        for e in eyes:
            cv.ellipse((e[0] - er * 0.8, e[1] - er, e[0] + er * 0.8, e[1] + er), fill=(255, 255, 255), outline=ink, width=ol * 0.8)
            pr = er * (0.38 if mood == "surprised" else 0.5)
            p = (e[0] + facing * er * 0.25, e[1] + er * 0.1)
            cv.circle(p, pr, fill=ink)
            cv.circle((p[0] + pr * 0.35, p[1] - pr * 0.35), pr * 0.3, fill=(255, 255, 255))
    if girl:                                                                              # lashes and blush
        for i, e in enumerate(eyes):
            s = -1 if i == 0 else 1
            if not (face.get("blink") or mood == "laugh"):
                cv.line([(e[0] + s * er * 0.6, e[1] - er * 0.8), (e[0] + s * er * 1.15, e[1] - er * 1.25)], ink, ol * 0.9)
                cv.line([(e[0] + s * er * 0.8, e[1] - er * 0.45), (e[0] + s * er * 1.3, e[1] - er * 0.75)], ink, ol * 0.9)
            cv.ellipse((e[0] - er * 0.75, ey + r * 0.3, e[0] + er * 0.75, ey + r * 0.46), fill=(240, 130, 140, 150))
    if glasses:
        for e in eyes:
            cv.circle(e, er * 1.25, outline=ink, width=ol * 0.9)
        cv.line([(eyes[0][0] + er * 1.25, ey), (eyes[1][0] - er * 1.25, ey)], ink, ol * 0.8)
    # brows
    by = ey - er * 1.55
    for i, e in enumerate(eyes):
        s = 1 if i == 0 else -1
        if mood == "angry":
            a, b = (e[0] - s * er * 0.9, by - er * 0.3), (e[0] + s * er * 0.7, by + er * 0.35)
        elif mood in ("sad", "worried"):
            a, b = (e[0] - s * er * 0.9, by + er * 0.25), (e[0] + s * er * 0.7, by - er * 0.3)
        elif mood == "surprised":
            a, b = (e[0] - er * 0.8, by - er * 0.4), (e[0] + er * 0.8, by - er * 0.4)
        else:
            a, b = (e[0] - er * 0.8, by), (e[0] + er * 0.8, by - er * 0.12)
        cv.line([a, b], ink, ol * 1.2)
    # nose
    if eye_style != "dot":
        cv.arc((fx + facing * r * 0.06, ey + r * 0.3), r * 0.09, 300 if facing > 0 else 120, 60 if facing > 0 else 240, _shade(skin, 0.7), ol * 0.8)
    # mouth
    my = c[1] + r * 0.6
    mo = clamp(face.get("mouth_open", 0.0))
    mw = r * 0.26
    ink = (186, 48, 78) if girl else ink                                                  # lip colour for the closed mouths
    if mo > 0.08 or mood in ("surprised", "laugh"):
        h = r * (0.1 + 0.22 * max(mo, {"surprised": 0.5, "laugh": 0.45}.get(mood, 0)))
        mw *= 1.35 if mood == "laugh" else 1.0
        box = (fx - mw * 0.7, my - h * 0.5, fx + mw * 0.7, my + h)
        cv.ellipse(box, fill=(120, 30, 40), outline=ink, width=ol * 0.8)
        cv.ellipse((fx - mw * 0.4, my + h * 0.3, fx + mw * 0.4, my + h * 0.95), fill=(230, 110, 110))
    elif mood == "happy":  # closed smile, so a listener never looks like they are talking
        cv.arc((fx, my - r * 0.12), mw * 0.85, 25, 155, ink, ol * 1.1)
    elif mood in ("sad", "worried"):
        cv.arc((fx, my + r * 0.12), mw * 0.7, 210, 330, ink, ol)
    elif mood == "angry":
        cv.line([(fx - mw * 0.6, my + r * 0.04), (fx + mw * 0.6, my)], ink, ol)
    else:
        cv.arc((fx, my - r * 0.12), mw * 0.75, 50, 130, ink, ol)
    if overbite and mo <= 0.08 and mood not in ("surprised", "laugh"):                    # two front teeth
        cv.rect((fx - mw * 0.34, my, fx + mw * 0.34, my + r * 0.13), fill=(250, 248, 240), outline=ink, width=ol * 0.6, radius=r * 0.02)
        cv.line([(fx, my), (fx, my + r * 0.13)], ink, ol * 0.5)


def polar_pt(c, r, deg):
    a = math.radians(deg)
    return (c[0] + math.cos(a) * r, c[1] + math.sin(a) * r)


def draw_face(cv, c, r, facing, face, ink, w, beanie=False, eyes="dot"):
    mood = face.get("mood", "neutral")
    laughing = mood == "laugh"
    if laughing:
        mood = "happy"
    look = face.get("look", 0.0)
    fx = c[0] + facing * r * 0.22 + look * r * 0.1
    ey = c[1] - r * (0.02 if beanie else 0.12)
    ex = r * 0.34
    er = max(1.5, r * 0.1)
    if eyes == "noir":  # A6: small cream eye marks close together
        ex, er = r * 0.26, max(1.2, r * 0.075)
    eye_pts = [(fx - ex, ey), (fx + ex, ey)]
    if face.get("blink") and mood != "happy":
        for e in eye_pts:
            cv.line([(e[0] - er, e[1]), (e[0] + er, e[1])], ink, w * 0.5)
    elif mood == "happy" and eyes != "oval":
        for e in eye_pts:
            cv.arc((e[0], e[1] + er * 0.6), er * 1.4, 200, 340, ink, w * 0.5)
    elif eyes == "oval":  # A5: solid black vertical ovals
        k = 1.25 if mood in ("surprised", "worried") else 1.0
        for e in eye_pts:
            cv.ellipse((e[0] - er * 0.85 * k, e[1] - er * 1.6 * k, e[0] + er * 0.85 * k, e[1] + er * 1.6 * k), fill=ink)
    elif mood in ("surprised", "worried") and eyes != "noir":
        for e in eye_pts:
            cv.circle(e, er * 1.5, fill=None, outline=ink, width=w * 0.4)
            cv.circle((e[0] + facing * er * 0.3, e[1]), er * 0.7, fill=ink)
    else:
        for e in eye_pts:
            cv.circle(e, er * (1.3 if eyes == "noir" and mood == "surprised" else 1.0), fill=ink)
    # brows
    if mood == "angry":
        for i, e in enumerate(eye_pts):
            s = -1 if i == 0 else 1
            cv.line([(e[0] - er * 1.6 * s, e[1] - er * 3.0), (e[0] + er * 1.2 * s, e[1] - er * 1.8)], ink, w * 0.45)
    elif mood in ("sad", "worried"):
        for i, e in enumerate(eye_pts):
            s = -1 if i == 0 else 1
            cv.line([(e[0] - er * 1.4 * s, e[1] - er * 1.8), (e[0] + er * 1.2 * s, e[1] - er * 2.8)], ink, w * 0.45)
    # mouth
    my = c[1] + r * 0.42
    mo = max(clamp(face.get("mouth_open", 0.0)), 0.6 if laughing else 0.0)
    mw = r * (0.32 if eyes == "noir" else 0.42)
    if mo > 0.08:
        h = r * (0.08 + 0.3 * mo)
        cv.ellipse((fx - mw * (0.55 + 0.2 * mo), my - h * 0.6, fx + mw * (0.55 + 0.2 * mo), my + h), fill=ink)
    elif mood == "happy":
        cv.arc((fx, my - r * 0.18), mw, 25, 155, ink, w * 0.5)
    elif mood == "sad":
        cv.arc((fx, my + r * 0.2), mw * 0.8, 205, 335, ink, w * 0.5)
    elif mood == "surprised":
        cv.circle((fx, my + r * 0.04), r * 0.13, fill=ink)
    elif mood == "angry":
        cv.line([(fx - mw * 0.6, my + r * 0.05), (fx + mw * 0.6, my + r * 0.02)], ink, w * 0.5)
    elif mood == "worried":
        pts = [(fx - mw * 0.6 + i * mw * 0.3, my + (r * 0.05 if i % 2 else -r * 0.03)) for i in range(5)]
        cv.line(pts, ink, w * 0.4)
    elif eyes == "noir":
        cv.line([(fx - mw * 0.5, my), (fx + mw * 0.5, my)], ink, w * 0.45)
    else:
        cv.arc((fx, my - r * 0.25), mw * 0.9, 60, 120, ink, w * 0.5)
