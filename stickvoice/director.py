"""Director Mode export: a director's treatment + one standalone ~10-second video
prompt per scene, for Kling, Google Flow (Veo), Runway, Luma and similar tools.

Character anchors and negative constraints follow the stickman-video-director
style catalog (A1-A6). Each prompt repeats the full style + character anchor so
every clip can be generated independently with a consistent look.
"""
from .themes import get_theme

STYLE_ANCHORS = {
    "a1-light": ("Minimalist two-dimensional black line animation on a flat, uniform, digitally pure-white canvas "
                 "(no texture, gradient, shadow or 3D depth).",
                 "The same consistent stick figure with a hollow circular head, occasional simple line expressions, no detailed "
                 "facial features, no hair, no clothing, stable proportions, connected line limbs and uniform medium line weight. "
                 "Exactly two arms and two legs; each limb appears only in its current pose. The figure stays black; up to three "
                 "saturated accent colors (vivid red, electric blue, warm gold) appear only on props and graphic effects."),
    "a1-dark": ("Minimalist two-dimensional white line animation on a flat, uniform, pitch-black canvas.",
                "The same consistent stick figure with a hollow circular head, occasional simple line expressions, no detailed "
                "facial features, no hair, no clothing, stable proportions, connected line limbs and uniform medium line weight. "
                "Exactly two arms and two legs; each limb appears only in its current pose. The figure stays white; up to three "
                "saturated accent colors (vivid red, electric blue, warm gold) appear only on props and graphic effects."),
    "a2-tech": ("Smooth 2D animation in a modern bright white studio space with subtle light-gray perspective grid lines on the "
                "floor plane. High-key studio lighting, clean white negative space, sleek glowing cyan and electric blue glass "
                "holographic UI elements.",
                "A minimalist 2D animated stick figure wearing a bright red beanie (smooth rounded knit, no pom-pom) and a yellow "
                "t-shirt, with simple black stick limbs and shorts. Simple black lines, vibrant colors, minimal dot eyes."),
    "a2-story": ("Smooth 2D vector animation in a rich full-color cinematic environment. Cinematic volumetric lighting, soft depth "
                 "of field, atmospheric narrative mood.",
                 "A minimalist 2D animated stick figure wearing a bright red beanie (smooth rounded knit, no pom-pom) and a yellow "
                 "t-shirt, with simple black stick limbs and shorts. Simple black lines, vibrant colors, minimal dot eyes."),
    "a3-cave": ("Crude hand-drawn 2D animation with black irregular outlines, subtle paper texture, earthy ochre and brown "
                "prehistoric scenery and small warm fire accents.",
                "A caveman with a white filled round head, expressive simple cartoon eyes, brows and mouth, wild dark spiky hair, "
                "thin black stick limbs, a ragged one-shoulder tan animal-hide tunic with brown spots, carrying a wooden club."),
    "a4-cozy": ("Full-color 2D cartoon storytelling with gentle atmospheric light, fully illustrated everyday environments and "
                "varied cinematic shots (wide establishing, close reactions, tracking).",
                "A minimalist character with a solid white round head, slim white-filled torso, fine dark stick limbs and a "
                "simple expressive face with natural expressions."),
    "a5-edo": ("Full-color painterly historical cartoon with clean cel shading: Edo-period Japan, wooden machiya houses with tiled "
               "roofs, indigo noren curtains, red paper lanterns, Mount Fuji in the distance.",
               "A samurai with a round white head and a short white neck growing from the kimono collar, two solid black vertical "
               "oval eyes, a short black topknot, an indigo kimono with a cream collar and a mustard sash, a katana at the hip, "
               "thin black exposed limbs and compact solid black mitten-shaped palms with one small thumb lobe."),
    "a5-egypt": ("Full-color painterly historical cartoon with clean cel shading: Ancient Egypt, sandstone temples with painted "
                 "columns, pyramids, palms and the Nile.",
                 "An Egyptian man with a round white head and a short white neck, two solid black vertical oval eyes, a blue and "
                 "gold striped nemes headdress, a teal broad collar, a white linen kilt with a gold belt, thin black exposed limbs "
                 "and compact solid black mitten-shaped palms with one small thumb lobe."),
    "a5-rome": ("Full-color painterly historical cartoon with clean cel shading: Ancient Rome, marble temples and forums, legion "
                "camps with palisades; palette of Roman red, bronze gold, steel grey, grass green, sky blue and earthy tan.",
                "A Roman legionary with a round white head and a short white neck, two solid black vertical oval eyes, a bronze "
                "helmet with a red crest and cheek guards, a red tunic under a bronze breastplate, a spear, thin black exposed "
                "limbs and compact solid black mitten-shaped palms with one small thumb lobe."),
    "a6-amber": ("Cinematic 2D illustration with angular contours, restrained cel shading, warm amber illumination and deep plum "
                 "shadows in layered full-color city settings; restrained camera movement.",
                 "A character with a compact matte-black round head, a connected short black neck, small cream-white eye marks and "
                 "a compact line mouth, wearing an orange hoodie with the hood down, simplified black hands and limbs with a "
                 "readable silhouette. A silent, non-speaking actor."),
    "b1-notebook": ("Hand-drawn 2D animation on near-white paper with a barely visible grid, black hand-drawn lines and a few "
                    "colorful crayon props.",
                    "An expressive stick figure with a white round head, simple black line limbs and expressive cartoon face."),
    "b2-paper": ("Colourful hand-drawn 2D animation on warm paper with fine, irregular ink lines and muted colors.",
                 "A simple stick figure with an ivory round head, fine ink limbs and a terracotta shirt."),
    "c1-toon": ("Bold flat 2D cartoon animation with thick dark outlines, flat cel colors and soft highlights, dusky "
                "teal-green scenery (rounded tree clumps, bushes, a grey road) and a slightly comedic meme-short feel.",
                "A young man drawn as a full cartoon character: big round peach-skin head, thick black curly hair, large white "
                "eyes with black pupils, expressive brows, a yellow T-shirt, blue jeans and grey sneakers, thick dark outlines "
                "and stable proportions."),
}

FRIENDS = {
    "a3-cave": "a cavewoman with a white round head, dark hair tied in a bun with a bone pin, a brown hide tunic with cream spots and a bone necklace",
    "a5-edo": "a woman with a round white head and short white neck, solid black oval eyes, a black hair bun with a red pin and a red kimono with a gold sash",
    "a5-egypt": "a woman with a round white head and short white neck, solid black oval eyes, a black bob wig, a long white linen dress and a gold collar",
    "a5-rome": "a Roman senator with a round white head and short white neck, solid black oval eyes, a green laurel wreath and a white toga with a purple band",
    "a6-amber": "a second character with a matte-black round head, cream eye marks and a teal jacket",
    "c1-toon": "a friend in the same cartoon style with dark curly hair, round glasses, an olive-green T-shirt, grey jeans and red sneakers",
    "a2-tech": "a friend stick figure with black hair and a cyan t-shirt",
    "a2-story": "a friend stick figure with black hair and a blue t-shirt",
}

NEGATIVES = {
    "a2-tech": "strictly minimalist studio aesthetic, no circuit board textures, no sci-fi wall panels, no spaceship corridors, no cracked concrete, no grunge textures",
    "a5": "no blood or gore, no photorealistic faces, no 3D CGI, no extra limbs, no fused or duplicate heads, no costume changes, no individual fingers, no white hands or gloves, no floating head",
    "a6-amber": "no glossy 3D characters, no photorealism, no talking presenter, no lip-sync",
    "c1-toon": "no stick figures, no 3D render, no photorealism, no anime style, no outfit changes",
}
COMMON_NEG = ("no speech bubbles, no dialogue boxes, no captions or subtitles, no visible text, letters or numbers, "
              "no watermarks, no extra characters, no abstract liquid morphing")

SETTING_TEXT = {
    "toon": {"plain": "a road beside a dusky teal forest", "park": "a road beside a dusky teal forest with rounded trees and bushes",
             "night": "a forest road at night under a full moon", "city": "a night city street with lit windows",
             "room": "a cozy room with a window and a bookshelf", "office": "a bright modern office",
             "classroom": "a classroom with a green chalkboard", "space": "deep space with a ringed planet",
             "beach": "a sunny beach with blue sea", "stage": "a theater stage under a warm spotlight"},
    "line": {"plain": "an empty canvas with a simple ground line", "park": "a minimal line-drawn park with two trees",
             "city": "minimal line-drawn city buildings", "night": "a minimal night sky with a moon and stars",
             "room": "a minimal room with a window and a bookshelf", "office": "a minimal office with a desk and monitor",
             "classroom": "a minimal classroom with a blackboard", "space": "minimal outer space with a ringed planet",
             "beach": "a minimal beach with gentle waves", "stage": "a minimal stage with curtains"},
    "color": {"plain": "a sunny meadow under a blue sky", "park": "a green park with trees and flowers",
              "city": "a colorful city street with tall buildings", "night": "a starry night with a glowing moon",
              "room": "a cozy room with warm lamplight, a window and a bookshelf", "office": "a bright modern office",
              "classroom": "a classroom with a green chalkboard", "space": "deep space with a ringed planet",
              "beach": "a sunny beach with blue sea", "stage": "a theater stage under a warm spotlight"},
    "cave": {"plain": "inside a cave with ochre wall paintings and a bright cave mouth", "room": "inside a cave with ochre wall paintings",
             "office": "a cave 'meeting' around flat rocks", "classroom": "a cave wall covered in paintings",
             "park": "an ochre savanna with a smoking volcano", "beach": "a sunny savanna by a river",
             "city": "a tribe village of hide huts", "night": "a campfire under a starry night sky",
             "space": "a campfire under a starry night sky", "stage": "a circle of standing stones"},
    "edo": {"plain": "an Edo street of wooden machiya with lanterns", "city": "a busy Edo street with noren curtains and red lanterns",
            "room": "a tatami room with shoji screens and a hanging scroll", "office": "a merchant's tatami office with shoji screens",
            "classroom": "a terakoya school room with shoji screens", "park": "a garden with cherry blossoms, a pond and a red arched bridge",
            "beach": "a garden pond with cherry blossoms", "night": "an Edo street at night lit by glowing lanterns",
            "space": "a moonlit Edo street", "stage": "a red torii gate before Mount Fuji"},
    "egypt": {"plain": "the desert with pyramids under a bright sun", "city": "the desert near the pyramids of Giza",
              "park": "palm trees before the pyramids", "beach": "the banks of the Nile with reeds and a felucca boat",
              "room": "a temple hall with painted columns and torches", "office": "a scribe's hall with painted columns",
              "classroom": "a temple hall with painted columns", "stage": "a grand temple hall", "night": "the pyramids under a starry night",
              "space": "the pyramids under a starry night"},
    "rome": {"plain": "the Roman forum with a marble temple", "city": "the Roman forum with marble columns and cobblestones",
             "room": "a Roman villa interior with red walls and mosaics", "office": "a villa study with red walls",
             "classroom": "a villa hall with mosaics", "park": "a legion camp with tents and a wooden palisade",
             "beach": "a legion camp on green hills", "night": "a legion camp at night around a fire",
             "space": "a legion camp under the stars", "stage": "the arches of the Colosseum"},
    "amber": {"plain": "a night city street with amber windows and a street lamp", "city": "a night city street with amber windows, wet reflections and a street lamp",
              "night": "a quiet alley at night under one amber street lamp", "room": "a dim room with one warm lamp and a city view",
              "office": "a dim office with one warm lamp and a city view", "classroom": "a dim room with one warm lamp",
              "park": "plum hills under an amber sunset", "beach": "a shore under an amber sunset",
              "space": "a rooftop under a plum night sky", "stage": "an empty street under one amber spotlight"},
}

ACTION_TEXT = {
    "talk": "gestures with open hands as if explaining", "stand": "stands still, then shifts weight",
    "wave": "waves warmly toward the viewer", "point": "points firmly toward the key object",
    "present": "presents the key object with an open palm", "think": "rubs the chin, looking up while thinking",
    "idea": "raises one finger as a lightbulb moment hits", "cheer": "throws both arms up and hops with joy",
    "jump": "jumps high with excitement", "clap": "claps happily", "sad": "slumps, head down, shoulders dropping",
    "shrug": "shrugs with palms up", "surprised": "jolts back in surprise, arms flung up",
    "scared": "recoils and trembles", "angry": "stomps with fists clenched", "facepalm": "slaps a palm to the forehead",
    "walk": "walks across the frame", "run": "sprints across the frame", "sit": "sits on a chair",
    "phone": "stares at a glowing phone", "read": "reads an open book", "write": "writes with a marker",
    "dance": "dances with bouncing steps", "ride": "rides a motorbike along the road in a side-on tracking shot, wheels spinning, the background streaming past with motion blur", "nod": "nods in agreement", "bow": "bows politely", "relax": "leans back and relaxes",
    "laugh": "doubles over laughing, shoulders shaking", "slap": "laughs out loud and playfully smacks the other person on the back",
}

PROP_TEXT = {"bulb": "a glowing lightbulb", "question": "a big question mark", "exclamation": "an exclamation mark",
             "money": "a stack of banknotes with falling coins", "coin": "a spinning gold coin", "clock": "a ticking clock",
             "chart": "a bar chart growing upward", "arrow_up": "a rising green arrow", "arrow_down": "a falling red arrow",
             "rocket": "a small rocket lifting off", "rain": "a rain cloud", "phone": "a smartphone with notifications",
             "laptop": "a laptop", "book": "an open book", "globe": "a spinning globe", "trophy": "a golden trophy",
             "brain": "a glowing brain", "heart": "a beating heart", "lock": "a padlock", "key": "a golden key",
             "car": "a small car", "check": "a big green check mark", "cross": "a big red cross", "warning": "a warning sign",
             "calendar": "a calendar flipping pages", "magnifier": "a magnifying glass", "gear": "turning gears",
             "mail": "an envelope", "people": "a small crowd", "fire": "a flickering flame", "flag": "a waving flag",
             "mountain": "a mountain peak", "target": "a target hit by a dart", "star": "a twinkling star"}

CAMERA_TEXT = {"zoom_in": "slow push-in", "zoom_out": "slow pull-back", "pan_left": "lateral tracking left",
               "pan_right": "lateral tracking right", "static": "locked-off wide shot", "punch": "quick punch-in, then hold"}


def _friend_act(sc, friend):
    if sc.get("action") == "ride":
        return "rides pillion behind them with both hands on their shoulders"
    return ACTION_TEXT.get(friend.get("action"), "reacts")


def _world(th):
    w = th["world"]
    return "color" if w in ("color", "color_soft") else w


def scene_prompt(i, sc, th, voice_desc, next_sc=None, seconds=10):
    tid = th["id"]
    style, char = STYLE_ANCHORS.get(tid, STYLE_ANCHORS["b1-notebook"])
    setting = SETTING_TEXT.get(_world(th), SETTING_TEXT["color"]).get(sc.get("setting", "plain"), sc.get("setting", ""))
    act = ACTION_TEXT.get(sc.get("action"), sc.get("action", ""))
    props = [PROP_TEXT.get(p, p.replace("_", " ")) for p in sc.get("props", [])]
    friend = sc.get("friend")
    cast = char
    if friend:
        cast += f" Also visible: {FRIENDS.get(tid, 'a second stick figure friend in the same drawing style')}, who " \
                f"{_friend_act(sc, friend)}."
    enter = {"left": "enters from frame left, ", "right": "enters from frame right, "}.get(sc.get("enter"), "")
    b1 = f"[0-3s] {CAMERA_TEXT.get(sc.get('camera'), 'wide shot')} on {setting}; the character {enter}" \
         f"{'notices ' + props[0] if props else 'looks toward the viewer'}."
    b2 = f"[3-7s] The character {act}" + (f" while {' and '.join(props)} pop{'s' if len(props) == 1 else ''} in beside them" if props else "") + "."
    end = f"turns toward the next moment ({ACTION_TEXT.get(next_sc.get('action'), 'moves on')})" if next_sc else "holds a final expressive pose"
    b3 = f"[7-10s] A clear reaction ({sc.get('mood', 'neutral')} mood), then the character {end}."
    neg = ", ".join(x for x in (NEGATIVES.get(tid), NEGATIVES.get("a5") if tid.startswith("a5") else None, COMMON_NEG) if x)
    narration = sc["narration"].replace('"', "'")
    if sc.get("lines"):
        who = {"main": "The main character", "friend": "The friend", "narrator": "A narrator (off screen)"}
        said = " ".join(f'{ln.get("name") or who[ln["who"]]} says: "{ln["text"]}"' for ln in sc["lines"])
        audio = (f"AUDIO: spoken dialogue in this order, each line lip-synced to the character who says it; the main character "
                 f"and the friend have clearly different voices. {said} ")
    else:
        audio = f"AUDIO: voiceover only. {voice_desc} The narrator says exactly, once, without changes: \"{narration}\" "
    if sc.get("clip_prompt"):  # hand-written shot: use it as is, with the plan's style and continuity notes
        audio = audio.replace("the main character and the friend", "the characters")
        return (f"{sc.get('_clip_style') or style}\nSHOT: {sc['clip_prompt']}\n{audio}"
                f"Strictly no speech bubbles, no dialogue boxes, no subtitles.\n"
                f"NEGATIVE: {sc.get('_clip_negative') or neg}.")
    return (f"{style}\nCHARACTER: {cast}\nSETTING: {setting}.\n{b1}\n{b2}\n{b3}\n"
            f"{audio}"
            f"Strictly no speech bubbles, no dialogue boxes, no subtitles. Gentle background music continues from the previous clip.\n"
            f"NEGATIVE: {neg}.")


CLIP_SIZES = {"16:9": (832, 480), "9:16": (480, 832), "1:1": (624, 624)}  # Wan 2.1 480p sizes


def clip_jobs(plan):
    """Visual-only prompts for an open-source text-to-video model (Wan 2.1 in the Colab notebook).

    Same anchors as the Kling prompts, but no timecodes and no audio: the voice and
    captions come from StickVoice's own audio.wav when the clips are assembled.
    """
    th = get_theme(plan.get("style"))
    tid = th["id"]
    style, char = STYLE_ANCHORS.get(tid, STYLE_ANCHORS["b1-notebook"])
    neg = ", ".join(x for x in (NEGATIVES.get(tid), NEGATIVES.get("a5") if tid.startswith("a5") else None, COMMON_NEG) if x)
    neg += ", blurry, low quality, jpeg artifacts, deformed hands, extra limbs, static frame"
    w, h = CLIP_SIZES.get(plan.get("ratio"), CLIP_SIZES["16:9"])
    clips = []
    for i, sc in enumerate(plan["scenes"]):
        setting = SETTING_TEXT.get(_world(th), SETTING_TEXT["color"]).get(sc.get("setting", "plain"), sc.get("setting", ""))
        props = [PROP_TEXT.get(p, p.replace("_", " ")) for p in sc.get("props", []) if "/" not in p and "\\" not in p]
        cast = char
        fr = sc.get("friend")
        if fr:
            cast += f" Next to them, {FRIENDS.get(tid, 'a second character in the same drawing style')}, who " \
                    f"{_friend_act(sc, fr)}."
        act = ACTION_TEXT.get(sc.get("action"), sc.get("action", ""))
        prompt = (f"{style} {cast} Setting: {setting}. {CAMERA_TEXT.get(sc.get('camera'), 'wide shot').capitalize()}. "
                  f"The character {act}" + (f", with {' and '.join(props)} beside them" if props else "") +
                  f", {sc.get('mood', 'neutral')} expression. Smooth, clear motion.")
        if sc.get("clip_prompt"):  # hand-written shot for this scene
            prompt = f"{plan.get('clip_style') or ''} {sc['clip_prompt']}".strip()
        clips.append({"id": f"clip_{i + 1:02d}", "scene": i + 1, "prompt": prompt,
                      "negative": (plan.get("clip_negative") + ", " + neg) if plan.get("clip_negative") else neg,
                      "narration": sc["narration"]})
    return {"title": plan.get("title", "video"), "style": tid, "ratio": plan.get("ratio", "16:9"),
            "width": w, "height": h, "clips": clips}


def treatment(plan, voice_desc="One consistent warm, clear narrator voice for the whole video: same timbre, accent, pace and recording quality in every clip."):
    th = get_theme(plan.get("style"))
    scenes = plan["scenes"]
    words = sum(len(s["narration"].split()) for s in scenes)
    out = [f"# {plan.get('title', 'Stickman video')} — Director's treatment", "",
           f"- **Style:** {th['label']} ({th['code']}) — {th['about']}",
           f"- **Aspect ratio:** {plan.get('ratio', '16:9')}",
           f"- **Clips:** {len(scenes)} × about 10 seconds (~{round(words / 2.5)} s of narration)",
           f"- **Narrator:** {voice_desc}", "",
           "## Cast (repeat in full in every clip)", "", f"- **Main character:** {STYLE_ANCHORS.get(th['id'], STYLE_ANCHORS['b1-notebook'])[1]}"]
    if any(s.get("friend") for s in scenes):
        out.append(f"- **Second character:** {FRIENDS.get(th['id'], 'a second stick figure friend in the same drawing style')}")
    out += ["", "## Scene plan", "", "| # | Narration | Action | Setting | Props | Camera |", "|---|---|---|---|---|---|"]
    for i, s in enumerate(scenes, 1):
        out.append(f"| {i} | {s['narration']} | {s.get('action')} | {s.get('setting')} | {', '.join(s.get('props', []))} | {s.get('camera')} |")
    out += ["", "## Clip prompts", "",
            "Paste each prompt into Kling, Google Flow (Veo), Runway or Luma as a separate ~10 s clip, with the same "
            "aspect ratio. Add captions and final music in CapCut or Premiere.", ""]
    for i, s in enumerate(scenes):
        nxt = scenes[i + 1] if i + 1 < len(scenes) else None
        out += [f"### Clip {i + 1}", "", "```text", scene_prompt(i, {**s, "_clip_style": plan.get("clip_style"), "_clip_negative": plan.get("clip_negative")}, th, voice_desc, nxt), "```", ""]
    out += ["## Sound design", "",
            "- One continuous background score from clip 1; duck it under the narration.",
            "- Soft pops when props appear, a whoosh on each cut, a bright ding on ideas, a short jingle on wins.", ""]
    return "\n".join(out)
