"""Visual styles, following the stickman-video-director style gallery.

A · Director styles: A1.1, A1.2, A2.1, A2.2, A3, A4, A5 (Edo / Egypt / Rome), A6
B · Autopilot styles: B1, B2
C · Cartoon styles: C1

Each theme sets the canvas, palette, the narrator's and friend's costume, the
world used for backgrounds ("line", "color", "color_soft", "cave", "edo",
"egypt", "rome", "amber", "toon") and how titles and captions look.
"""

INK = (20, 20, 22)
WHITE = (255, 255, 255)

THEMES = {
    # ---------------------------------------------------------------- A1 Classic
    "a1-light": {
        "code": "A1.1", "group": "A", "label": "A1.1 Classic · black on white",
        "about": "Pure white canvas, black line figures, up to three accent colours. Clear explainers.",
        "bg": (255, 255, 255), "grid": None, "ink": (15, 15, 15), "head": (255, 255, 255),
        "accents": [(220, 40, 50), (30, 110, 230), (245, 170, 20)], "world": "line",
        "caption_ink": (15, 15, 15), "caption_box": None, "hand_font": "Caveat.ttf",
        "outfit": {}, "friend": {"headwear": "hair", "hair": (15, 15, 15)},
    },
    "a1-dark": {
        "code": "A1.2", "group": "A", "label": "A1.2 Classic · white on black",
        "about": "Pure black canvas, white line figures. Stronger contrast for suspense, conflict and emotion.",
        "bg": (10, 10, 12), "grid": None, "ink": (245, 245, 240), "head": (10, 10, 12),
        "accents": [(255, 80, 80), (80, 170, 255), (255, 200, 60)], "world": "line",
        "caption_ink": (250, 250, 250), "caption_box": None, "hand_font": "Caveat.ttf",
        "outfit": {}, "friend": {"headwear": "hair", "hair": (245, 245, 240)},
    },
    # ---------------------------------------------------------------- A2 Modern Pop
    "a2-tech": {
        "code": "A2.1", "group": "A", "label": "A2.1 Modern Pop · Minimal Tech",
        "about": "Red beanie + yellow T-shirt in a white studio with a faint grid and cyan glow. Tools and tutorials.",
        "bg": (250, 251, 253), "grid": (222, 230, 240), "perspective_grid": True, "ink": (20, 22, 28),
        "head": WHITE, "accents": [(0, 180, 220), (40, 110, 240), (255, 196, 0)], "world": "line",
        "caption_ink": (20, 22, 28), "caption_box": None, "hand_font": "NotoSans.ttf",
        "outfit": {"headwear": "beanie", "headwear_color": (214, 40, 40), "shirt": (255, 205, 30), "shorts": (40, 60, 110)},
        "friend": {"headwear": "hair", "hair": (20, 22, 28), "shirt": (0, 170, 210)},
    },
    "a2-story": {
        "code": "A2.2", "group": "A", "label": "A2.2 Modern Pop · Colorful Story",
        "about": "The same red-beanie character in rich, colourful scenes with cinematic light. Personal growth stories.",
        "bg": (190, 228, 250), "grid": None, "ink": (30, 30, 36), "head": WHITE,
        "accents": [(235, 80, 70), (60, 130, 230), (250, 190, 40)], "world": "color",
        "caption_ink": WHITE, "caption_box": (20, 20, 28), "hand_font": "Caveat.ttf",
        "outfit": {"headwear": "beanie", "headwear_color": (214, 40, 40), "shirt": (255, 205, 30), "shorts": (40, 60, 110)},
        "friend": {"headwear": "hair", "hair": (30, 30, 36), "shirt": (60, 130, 230)},
    },
    # ---------------------------------------------------------------- A3 Prehistoric Cave
    "a3-cave": {
        "code": "A3", "group": "A", "label": "A3 Prehistoric Cave",
        "about": "Caves, animal skins, campfires and exaggerated faces. Workplace satire and fables with a twist.",
        "bg": (214, 176, 120), "grid": None, "ink": (34, 24, 18), "head": (255, 252, 244),
        "accents": [(214, 84, 40), (70, 120, 150), (238, 172, 52)], "world": "cave", "texture": True,
        "caption_ink": (255, 244, 220), "caption_box": (52, 34, 22), "hand_font": "Caveat.ttf",
        "title_color": (60, 36, 20), "title_halo": (240, 220, 180),
        "outfit": {"tunic": {"color": (196, 140, 80), "spots": (120, 76, 40)}, "headwear": "wild", "headwear_color": (52, 34, 22),
                   "weapon": "club"},
        "friend": {"tunic": {"color": (160, 110, 70), "spots": (230, 210, 170)}, "headwear": "bun", "headwear_color": (90, 55, 30),
                   "pin": (240, 230, 210), "necklace": (240, 230, 210)},
    },
    # ---------------------------------------------------------------- A4 Cozy Storytelling
    "a4-cozy": {
        "code": "A4", "group": "A", "label": "A4 Cozy Storytelling",
        "about": "White round heads and slim white bodies in colourful everyday places. Relatable small moments.",
        "bg": (190, 228, 250), "grid": None, "ink": (30, 30, 36), "head": WHITE,
        "accents": [(235, 80, 70), (60, 130, 230), (250, 190, 40)], "world": "color",
        "caption_ink": WHITE, "caption_box": (20, 20, 28), "hand_font": "Caveat.ttf",
        "outfit": {"shirt": WHITE}, "friend": {"shirt": WHITE, "headwear": "hair", "hair": (60, 40, 30)},
    },
    # ---------------------------------------------------------------- A5 Historical Cartoon
    "a5-edo": {
        "code": "A5", "group": "A", "label": "A5 Historical · Edo Japan",
        "about": "Samurai on Edo streets: kimono, topknot, lanterns, cel-shaded colour. History you can picture.",
        "bg": (236, 222, 196), "grid": None, "ink": (24, 22, 26), "head": WHITE,
        "accents": [(200, 50, 45), (40, 70, 130), (226, 170, 60)], "world": "edo",
        "caption_ink": (30, 26, 24), "caption_box": (250, 244, 228), "hand_font": "georgiab.ttf",
        "title_color": (40, 30, 26), "title_halo": (250, 242, 225),
        "outfit": {"neck": True, "eyes": "oval", "hands": "mitten", "headwear": "topknot", "headwear_color": (24, 22, 26),
                   "robe": {"color": (52, 74, 128), "trim": (236, 228, 210), "sash": (196, 160, 90), "length": 1.5}, "weapon": "katana"},
        "friend": {"neck": True, "eyes": "oval", "hands": "mitten", "headwear": "bun", "headwear_color": (24, 22, 26),
                   "robe": {"color": (196, 70, 80), "trim": (250, 236, 210), "sash": (240, 200, 90), "length": 1.75, "bottom": 0.12}},
    },
    "a5-egypt": {
        "code": "A5", "group": "A", "label": "A5 Historical · Ancient Egypt",
        "about": "Temples, pyramids, the Nile, nemes headdresses and gold collars.",
        "bg": (240, 214, 160), "grid": None, "ink": (28, 22, 18), "head": WHITE,
        "accents": [(40, 110, 170), (210, 160, 50), (190, 70, 50)], "world": "egypt",
        "caption_ink": (30, 26, 24), "caption_box": (252, 242, 220), "hand_font": "georgiab.ttf",
        "title_color": (60, 40, 20), "title_halo": (252, 240, 210),
        "outfit": {"neck": True, "eyes": "oval", "hands": "mitten", "headwear": "nemes", "headwear_color": (40, 90, 160),
                   "headwear_stripe": (226, 182, 70), "kilt": (250, 246, 236), "belt": (226, 182, 70), "collar": (40, 140, 150)},
        "friend": {"neck": True, "eyes": "oval", "hands": "mitten", "headwear": "bob", "headwear_color": (24, 22, 26),
                   "robe": {"color": (250, 246, 236), "length": 1.85, "top": 0.06, "bottom": 0.1}, "collar": (226, 182, 70)},
    },
    "a5-rome": {
        "code": "A5", "group": "A", "label": "A5 Historical · Ancient Rome",
        "about": "Roman red, bronze gold and steel: forums, legion camps and villas.",
        "bg": (214, 228, 236), "grid": None, "ink": (26, 24, 26), "head": WHITE,
        "accents": [(178, 40, 40), (200, 156, 60), (110, 140, 90)], "world": "rome",
        "caption_ink": (30, 26, 24), "caption_box": (248, 244, 234), "hand_font": "georgiab.ttf",
        "title_color": (60, 24, 24), "title_halo": (250, 246, 236),
        "outfit": {"neck": True, "eyes": "oval", "hands": "mitten", "headwear": "helmet", "headwear_color": (200, 156, 60),
                   "crest": (178, 40, 40), "robe": {"color": (178, 40, 40), "length": 1.3}, "breastplate": (200, 156, 60),
                   "weapon": "spear"},
        "friend": {"neck": True, "eyes": "oval", "hands": "mitten", "headwear": "laurel",
                   "robe": {"color": (250, 248, 240), "trim": (120, 50, 120), "length": 1.75, "bottom": 0.14}},
    },
    # ---------------------------------------------------------------- A6 Amber Noir
    "a6-amber": {
        "code": "A6", "group": "A", "label": "A6 Amber Noir",
        "about": "Black round-headed character in an orange hoodie, warm amber light and deep plum shadows. Cinematic 'what if' stories.",
        "bg": (52, 30, 56), "grid": None, "ink": (14, 10, 16), "head": (18, 14, 20),
        "accents": [(255, 150, 40), (120, 200, 220), (255, 206, 110)], "world": "amber",
        "caption_ink": WHITE, "caption_box": None, "caption_upper": True, "caption_hi": (255, 176, 60),
        "hand_font": "NotoSans.ttf", "title_upper": True, "title_color": WHITE, "title_halo": (20, 12, 24),
        "outfit": {"neck": True, "eyes": "noir", "face_color": (250, 238, 214), "hood": (232, 112, 30),
                   "shirt": (240, 124, 36), "sleeves": (240, 124, 36), "shorts": (34, 30, 44)},
        "friend": {"neck": True, "eyes": "noir", "face_color": (250, 238, 214), "shirt": (70, 120, 140),
                   "sleeves": (70, 120, 140), "headwear": "hair", "hair": (14, 10, 16)},
    },
    # ---------------------------------------------------------------- B Autopilot
    "b1-notebook": {
        "code": "B1", "group": "B", "label": "B1 Minimal Hand-Drawn",
        "about": "Near-white paper with a faint grid, black hand-drawn lines and a few colourful props.",
        "bg": (253, 253, 252), "grid": (226, 230, 234), "ink": (25, 25, 22), "head": WHITE,
        "accents": [(226, 62, 72), (38, 120, 214), (240, 168, 32)], "world": "line",
        "caption_ink": (25, 25, 22), "caption_box": None, "hand_font": "Caveat.ttf",
        "outfit": {}, "friend": {"headwear": "hair", "hair": (25, 25, 22)},
    },
    "b2-paper": {
        "code": "B2", "group": "B", "label": "B2 Colorful Hand-Drawn",
        "about": "Warm paper, muted colourful scenes, dark captions on ivory labels.",
        "bg": (244, 240, 229), "grid": None, "ink": (48, 40, 34), "head": (255, 252, 244),
        "accents": [(214, 92, 64), (70, 128, 170), (226, 170, 60)], "world": "color_soft",
        "caption_ink": (40, 34, 30), "caption_box": (252, 247, 232), "hand_font": "Caveat.ttf",
        "outfit": {"shirt": (214, 92, 64)}, "friend": {"shirt": (70, 128, 170), "headwear": "hair", "hair": (48, 40, 34)},
    },
    # ---------------------------------------------------------------- C Cartoon
    "c1-toon": {
        "code": "C1", "group": "C", "label": "C1 Bold Cartoon",
        "about": "Full cartoon characters with curly hair, big eyes, T-shirts, jeans and sneakers, thick outlines, "
                 "dusky teal scenes and white titles on maroon labels. Relatable meme shorts.",
        "bg": (32, 78, 86), "grid": None, "ink": (30, 22, 24), "head": (247, 208, 176),
        "accents": [(255, 200, 40), (236, 96, 40), (70, 150, 230)], "world": "toon",
        "caption_ink": WHITE, "caption_box": (112, 22, 36), "caption_hi": (255, 210, 60), "hand_font": "segoeuib.ttf",
        "title_color": WHITE, "title_box": (112, 22, 36), "bike": (236, 186, 52),
        "outfit": {"body": "toon", "hair": (34, 26, 28), "shirt": (252, 196, 40), "pants": (66, 108, 170),
                   "shoes": (86, 96, 120)},
        "friend": {"body": "toon", "skin": (240, 196, 160), "hair": (44, 32, 30), "glasses": True,
                   "shirt": (156, 168, 112), "pants": (62, 64, 74), "shoes": (178, 44, 44)},
        "girl": {"body": "toon", "hairstyle": "long", "skin": (246, 204, 176), "hair": (52, 30, 34),
                 "shirt": (232, 84, 128), "pants": (70, 62, 120), "shoes": (240, 236, 230)},
    },
}

# old names keep working
ALIASES = {"classic": "a1-light", "dark": "a1-dark", "pop": "a2-tech", "story": "a4-cozy",
           "notebook": "b1-notebook", "paper": "b2-paper", "cave": "a3-cave", "prehistoric": "a3-cave",
           "edo": "a5-edo", "japan": "a5-edo", "egypt": "a5-egypt", "rome": "a5-rome", "amber": "a6-amber",
           "noir": "a6-amber", "a1": "a1-light", "a2": "a2-tech", "a3": "a3-cave", "a4": "a4-cozy",
           "a5": "a5-edo", "a6": "a6-amber", "b1": "b1-notebook", "b2": "b2-paper",
           "toon": "c1-toon", "cartoon": "c1-toon", "c1": "c1-toon", "a1.1": "a1-light", "a1.2": "a1-dark", "a2.1": "a2-tech", "a2.2": "a2-story"}

DEFAULT_THEME = "b1-notebook"

_BIG = {"body": "toon", "eyes": "big"}
CHARACTERS = {  # use with "character" on a scene, or on its "friend"
    "tunic_comic": {"body": "toon", "label": "Tunic Comic", "thin": True, "head_scale": 1.4, "hairstyle": "bald", "eyes": "dot",
                    "tunic": True, "skin": (250, 226, 200), "shirt": (244, 242, 234), "pants": (44, 40, 44), "shoes": (34, 32, 36)},
    "tee_comic": {"body": "toon", "label": "Tee Comic", "thin": True, "head_scale": 1.4, "hairstyle": "bald", "eyes": "dot",
                  "skin": (250, 226, 200), "shirt": (246, 244, 238), "pants": (34, 32, 36), "shoes": (34, 32, 36)},
    "stick_comic": {"body": "toon", "label": "Stick Comic", "stick_limbs": True, "head_scale": 1.3, "hairstyle": "bald",
                    "eyes": "dot", "shade_head": True, "skin": (222, 160, 104), "shirt": (246, 246, 242)},
    "bald_boy": {**_BIG, "label": "Bald Boy", "head_scale": 1.25, "hairstyle": "strands", "overbite": True, "sleeveless": True,
                 "shorts": True, "skin": (214, 160, 118), "shirt": (214, 44, 48), "pants": (50, 96, 190), "shoes": (118, 72, 40),
                 "shoe_scale": 1.4},
    "friend_orange": {**_BIG, "label": "Friend Orange", "hairstyle": "messy", "barefoot": True, "skin": (226, 172, 128),
                      "shirt": (240, 124, 40), "pants": (72, 84, 110)},
    "friend_red": {**_BIG, "label": "Friend Red", "hairstyle": "messy", "barefoot": True, "skin": (226, 172, 128),
                   "shirt": (214, 52, 52), "pants": (72, 84, 110)},
    "friend_blue": {**_BIG, "label": "Friend Blue", "hairstyle": "messy", "barefoot": True, "skin": (204, 148, 106),
                    "shirt": (54, 120, 210), "pants": (90, 80, 70)},
    "friend_yellow": {**_BIG, "label": "Friend Yellow", "hairstyle": "messy", "barefoot": True, "skin": (236, 188, 146),
                      "shirt": (250, 204, 50), "pants": (60, 110, 100)},
    "rider_yellow": {**_BIG, "label": "Rider Yellow", "skin": (226, 172, 128), "shirt": (250, 204, 50), "pants": (62, 72, 104),
                     "shoes": (70, 56, 50)},
    "rider_green": {**_BIG, "label": "Rider Green", "skin": (204, 148, 106), "shirt": (66, 160, 92), "pants": (84, 74, 66),
                    "shoes": (120, 60, 50)},
}

for _k, _t in THEMES.items():
    _t["id"] = _k
    _t["mode"] = "line" if _t["world"] == "line" else ("color_soft" if _t["world"] == "color_soft" else "color")


def resolve(name):
    n = (name or "").lower().strip()
    return n if n in THEMES else ALIASES.get(n, DEFAULT_THEME)


def get_theme(name):
    return THEMES[resolve(name)]


def style_choices():
    return sorted(set(THEMES) | set(ALIASES))
