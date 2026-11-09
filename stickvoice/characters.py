"""Character sheet: every named character from themes.CHARACTERS, drawn with the real renderer."""
import os

from PIL import Image, ImageDraw

from .canvas import Canvas, font, new_image
from .renderer import _draw_ride, _draw_standup, _layout, _standup_bg
from .scenes import draw_background
from .stickman import draw_stickman, make_pose, reach_arms, solve
from .themes import CHARACTERS, get_theme

W, H = 540, 960


def _act(action, mood):
    return {"action": action, "mood": mood, "since": 0.0, "prev": action}


def _standup_panel(th, sc, action, mood):
    img = _standup_bg(sc, W, H, th).copy()
    _draw_standup(Canvas(img), {"lines": []}, sc, th, 2.0, W, H, _act(action, mood), 0.0, 0)
    return img


def _ride_panel(th):
    sc = {"setting": "night", "vehicle": "scooter", "character": "rider_yellow",
          "friend": {"character": "rider_green"}}
    L = _layout(W, H, False, True)
    img = draw_background("night", W, H, L["ground"], th, seed=2)
    L.update(char_h=H * 0.42, ground=H * 0.76)
    _draw_ride(Canvas(img), sc, L, th, 1.0, 0, W, "worried", 0.0, _act("nod", "surprised"))
    return img


def _huddle_panel(th):
    """Three friends leaning in over one phone."""
    ground, ch = H * 0.86, H * 0.47
    img = draw_background("room", W, H, ground, th, seed=1)
    cv = Canvas(img)
    phone = (W * 0.5, H * 0.6)
    cast = (("friend_blue", W * 0.5, 1, "happy"), ("friend_orange", W * 0.2, 1, "surprised"), ("friend_yellow", W * 0.8, -1, "laugh"))  # blue stands behind
    for name, x, f, mood in cast:
        outfit = dict(CHARACTERS[name])
        pose = make_pose("stand", 1.0, 0.0, x)
        pose["lean"] += 13 if x != W * 0.5 else 4
        pose["head"] += 12
        j = solve(pose, ch, f)
        oy = ground - max(j["footA"][1], j["footB"][1]) - pose["lift"] - ch * 0.035
        hand = (phone[0] - x + (0 if x == W * 0.5 else -f * ch * 0.03), phone[1] - oy + ch * 0.03)
        reach_arms(pose, ch, f, hand, (hand[0] - f * ch * 0.04, hand[1] + ch * 0.05))
        draw_stickman(cv, x, ground, ch, pose, f, th, {"mood": mood, "mouth_open": 0.0, "blink": False}, outfit)
    pw, ph = ch * 0.055, ch * 0.1
    cv.rect((phone[0] - pw, phone[1] - ph, phone[0] + pw, phone[1] + ph), fill=(36, 38, 46), outline=th["ink"], width=3, radius=6)
    cv.rect((phone[0] - pw * 0.74, phone[1] - ph * 0.84, phone[0] + pw * 0.74, phone[1] + ph * 0.84), fill=(120, 200, 240))
    return img


def character_sheet(out_dir):
    th = get_theme("c1-toon")
    panels = [("Tunic Comic", _standup_panel(th, {"character": "tunic_comic", "backdrop": "curtain", "mic": "stand", "audience": False}, "talk", "happy")),
              ("Tunic Comic, unimpressed", _standup_panel(th, {"character": "tunic_comic", "audience": False}, "shrug", "worried")),
              ("Bald Boy", _standup_panel(th, {"character": "bald_boy", "backdrop": "outdoor", "mic": "stand", "audience": False}, "wave", "happy")),
              ("Three Friends", _huddle_panel(th)),
              ("Riders on the scooter", _ride_panel(th))]
    os.makedirs(out_dir, exist_ok=True)
    label_h, gap = 56, 12
    sheet = Image.new("RGB", (len(panels) * (W + gap) + gap, H + label_h + gap * 2), (24, 22, 26))
    draw = ImageDraw.Draw(sheet)
    for i, (label, img) in enumerate(panels):
        small = img.resize((W, H), Image.LANCZOS)
        name = label.lower().replace(",", "").replace(" ", "-")
        small.save(os.path.join(out_dir, f"{name}.png"))
        x = gap + i * (W + gap)
        sheet.paste(small, (x, gap))
        fnt = font(th["hand_font"], 26)
        draw.text((x + W / 2, gap + H + label_h / 2), label, font=fnt, fill=(245, 242, 234), anchor="mm")
    path = os.path.join(out_dir, "character-sheet.png")
    sheet.save(path)
    return path
