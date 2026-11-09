"""Still thumbnails of each style, for the style gallery in the web app."""
import os

import numpy as np
from PIL import Image

from . import renderer as R
from .canvas import Canvas
from .scenes import draw_background
from .themes import get_theme

DEMO = {
    "a1-light": ("idea", "plain", ["bulb"]), "a1-dark": ("surprised", "plain", ["warning"]),
    "a2-tech": ("present", "plain", ["laptop"]), "a2-story": ("cheer", "park", ["trophy"]),
    "a3-cave": ("think", "city", ["fire"]), "a4-cozy": ("phone", "room", ["mail"]),
    "a5-edo": ("bow", "city", []), "a5-egypt": ("point", "plain", ["star"]), "a5-rome": ("talk", "city", []),
    "a6-amber": ("walk", "city", ["question"]), "b1-notebook": ("talk", "plain", ["chart"]),
    "b2-paper": ("read", "room", ["book"]), "c1-toon": ("surprised", "park", []),
}


def style_preview(style_id, folder):
    th = get_theme(style_id)
    path = os.path.join(folder, th["id"] + ".png")
    if os.path.exists(path):
        return path
    os.makedirs(folder, exist_ok=True)
    W, H = 1280, 720
    action, setting, props = DEMO.get(th["id"], ("talk", "plain", []))
    friend = {"action": "wave", "mood": "happy"} if th["id"] in ("a5-edo", "a5-rome", "a3-cave", "c1-toon") else None
    sc = {"narration": th["code"] + " " + th["label"].split(" ", 1)[1], "action": action, "mood": "happy",
          "setting": setting, "props": props, "headline": th["code"], "enter": "none", "camera": "static", "friend": friend}
    L = R._layout(W, H, bool(props), bool(friend))
    words = sc["narration"].split()
    times = R._word_times(words, 1.0, start=0.0)
    s = {"fps": 30, "env": np.zeros(10), "lead": 0.0, "dur": 3, "words": words, "times": times,
         "chunks": R._chunks(words, times, 9), "prop_t": [0.0, 0.2]}
    img = draw_background(setting, W, H, L["ground"], th)
    R._draw_scene(Canvas(img), s, sc, L, th, 1.2, 36, W, H, None, 0)
    frame = img.resize((W, H), Image.LANCZOS)
    R._draw_caption(frame, s, 1.5, L, th, W)
    frame.resize((480, 270), Image.LANCZOS).save(path)
    return path
