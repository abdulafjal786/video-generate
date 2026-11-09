"""Prompt -> scene plan.

A plan is plain JSON, so you can also write or edit it by hand:

{
  "title": "...", "style": "notebook", "ratio": "16:9",
  "scenes": [
    {"narration": "spoken words", "action": "talk", "mood": "happy",
     "setting": "park", "props": ["bulb"], "headline": "BIG IDEA",
     "enter": "left", "camera": "zoom_in", "friend": {"action": "clap"}}
  ]
}
"""
import json
import os
import re

from .props import all_prop_names
from .scenes import SETTINGS
from .stickman import ACTIONS, MOODS
from .themes import CHARACTERS

CAMERAS = ["zoom_in", "zoom_out", "pan_left", "pan_right", "static", "punch"]

# keyword -> hints. First matching rules win for action/setting; props accumulate.
RULES = [
    (r"\b(bike|motorbike|motorcycle|scooter|scooty|riding|ride)", {"action": "ride", "setting": "park"}),  # first: a ride beats other actions
    (r"\b(idea|realiz|discover|solution|eureka|invent)", {"action": "idea", "props": ["bulb"], "mood": "happy"}),
    (r"\b(think|wonder|why|how|what if|question|curious|\?)", {"action": "think", "props": ["question"]}),
    (r"\b(money|rich|cash|salary|pay|price|cost|dollar|rupee|budget|invest|earn)", {"props": ["money"]}),
    (r"\b(coin|save|saving)", {"props": ["coin"]}),
    (r"\b(time|clock|hour|minute|late|deadline|wait)", {"props": ["clock"]}),
    (r"\b(day|week|month|year|calendar|schedule|habit)", {"props": ["calendar"]}),
    (r"\b(phone|mobile|social media|instagram|scroll|app|notification)", {"action": "phone", "props": ["phone"]}),
    (r"\b(computer|laptop|code|coding|software|internet|online|website|ai\b|program)", {"props": ["laptop"], "setting": "office"}),
    (r"\b(grow|growth|increase|rise|profit|success|better|improv)", {"props": ["arrow_up", "chart"]}),
    (r"\b(fall|drop|decrease|lose|loss|worse|decline|crash)", {"props": ["arrow_down"], "mood": "worried"}),
    (r"\b(data|chart|statistic|percent|number|graph|market)", {"props": ["chart"], "action": "present"}),
    (r"\b(world|global|earth|country|countries|planet)", {"props": ["globe"]}),
    (r"\b(launch|start|startup|rocket|fast|speed|boost)", {"props": ["rocket"]}),
    (r"\b(rain|storm|weather|cloud)", {"props": ["rain"]}),
    (r"\b(sun|summer|hot|morning|bright)", {"props": ["sun"]}),
    (r"\b(night|sleep|dream|tired|moon|dark)", {"props": ["moon"], "setting": "night"}),
    (r"\b(tree|nature|forest|environment|green)", {"props": ["tree"], "setting": "park"}),
    (r"\b(home|house|family|room)", {"props": ["house"], "setting": "room"}),
    (r"\b(work|job|office|boss|career|business|company|meeting)", {"setting": "office"}),
    (r"\b(school|learn|study|student|teacher|class|exam|education)", {"props": ["graduation", "book"], "setting": "classroom"}),
    (r"\b(book|read|story)", {"props": ["book"], "action": "read"}),
    (r"\b(write|note|plan|list)", {"action": "write"}),
    (r"\b(process|system|machine|engine|work[s]? how|mechanism)", {"props": ["gear"]}),
    (r"\b(win|winner|champion|award|achieve|victory|best)", {"action": "cheer", "props": ["trophy"], "mood": "happy"}),
    (r"\b(brain|mind|psycholog|memory|focus|smart|intelligen)", {"props": ["brain"]}),
    (r"\b(goal|target|aim|focus on|purpose)", {"props": ["target"]}),
    (r"\b(yes|correct|right way|true|done|complete)", {"props": ["check"]}),
    (r"\b(no\b|wrong|mistake|myth|false|never|don't|stop)", {"props": ["cross"], "action": "shrug"}),
    (r"\b(danger|warning|careful|risk|problem|trouble)", {"props": ["warning"], "mood": "worried"}),
    (r"\b(energy|battery|power|tired)", {"props": ["battery"]}),
    (r"\b(search|find|look|research|investigat)", {"props": ["magnifier"]}),
    (r"\b(gift|present|reward|bonus|free)", {"props": ["gift"]}),
    (r"\b(music|song|sing|dance)", {"props": ["music"], "action": "dance"}),
    (r"\b(fire|burn|hot|passion)", {"props": ["fire"]}),
    (r"\b(water|drink|ocean|sea|beach)", {"props": ["drop"], "setting": "beach"}),
    (r"\b(electric|shock|sudden|lightning)", {"props": ["lightning"]}),
    (r"\b(car|drive|travel|road|trip)", {"props": ["car"], "setting": "city"}),
    (r"\b(city|street|town|traffic)", {"setting": "city"}),
    (r"\b(email|message|letter|mail)", {"props": ["mail"]}),
    (r"\b(secret|lock|security|password|privacy|safe)", {"props": ["lock"]}),
    (r"\b(key|unlock|secret to)", {"props": ["key"]}),
    (r"\b(people|team|friends|community|everyone|together|crowd)", {"props": ["people"]}),
    (r"\b(health|food|eat|diet|apple|fruit)", {"props": ["apple"]}),
    (r"\b(pizza|hungry|lunch|dinner)", {"props": ["pizza"]}),
    (r"\b(love|heart|care|kind|relationship)", {"props": ["heart"], "mood": "happy"}),
    (r"\b(star|famous|amazing|awesome)", {"props": ["star"]}),
    (r"\b(mountain|climb|challenge|journey|hard)", {"props": ["mountain"]}),
    (r"\b(space|universe|galaxy|astronaut|nasa)", {"setting": "space", "props": ["rocket"]}),
    (r"\b(video|camera|youtube|film|record)", {"props": ["camera"]}),
    (r"\b(plant|seed|small step|patience)", {"props": ["plant"]}),
    (r"\b(explode|boom|bomb|shock)", {"props": ["bomb"], "action": "surprised"}),
    (r"\b(happy|great|good news|excit|celebrat|yay)", {"action": "cheer", "mood": "happy"}),
    (r"\b(sad|unhappy|fail|lonely|depress|cry)", {"action": "sad", "mood": "sad"}),
    (r"\b(angry|mad|annoy|hate|frustrat)", {"action": "angry", "mood": "angry"}),
    (r"\b(scared|afraid|fear|anxious|anxiety|panic)", {"action": "scared", "mood": "worried"}),
    (r"\b(surpris|shock|wow|unbelievable|incredible)", {"action": "surprised", "mood": "surprised"}),
    (r"\b(walk|walking|journey|wander)", {"action": "walk"}),
    (r"\b(run|hurry|rush|race)", {"action": "run"}),
    (r"\b(relax|calm|rest|chill|peace)", {"action": "relax", "mood": "happy"}),
    (r"\b(hello|hi\b|welcome|hey)", {"action": "wave", "mood": "happy"}),
    (r"\b(thank|subscribe|follow|bye|goodbye)", {"action": "wave", "mood": "happy"}),
    (r"\b(oops|facepalm|silly|stupid|forgot)", {"action": "facepalm", "mood": "sad"}),
]

# Hindi keywords -> same hints (plain substring match)
HI_RULES = [
    ("बाइक|मोटरसाइकिल|स्कूटर|स्कूटी|सवारी", {"action": "ride", "setting": "park"}),  # first: a ride beats other actions
    ("विचार|आइडिया|तरकीब|उपाय|समाधान", {"action": "idea", "props": ["bulb"], "mood": "happy"}),
    ("क्यों|कैसे|क्या आप|सवाल|सोच", {"action": "think", "props": ["question"]}),
    ("पैसा|पैसे|रुपय|कमाई|कमा|सैलरी|बचत|निवेश|खर्च", {"props": ["money"]}),
    ("समय|घंटे|मिनट|देर|वक्त|वक़्त", {"props": ["clock"]}),
    ("दिन|हफ्ते|महीने|साल|रोज़|रोज", {"props": ["calendar"]}),
    ("फोन|फ़ोन|मोबाइल|सोशल मीडिया|ऐप", {"action": "phone", "props": ["phone"]}),
    ("कंप्यूटर|लैपटॉप|इंटरनेट|ऑनलाइन|एआई|कोड", {"props": ["laptop"], "setting": "office"}),
    ("बढ़|तरक्की|सफल|कामयाब|बेहतर|मुनाफ", {"props": ["arrow_up", "chart"]}),
    ("गिर|घट|नुकसान|असफल|हार", {"props": ["arrow_down"], "mood": "worried"}),
    ("दुनिया|देश|धरती|पृथ्वी", {"props": ["globe"]}),
    ("शुरू|शुरुआत|तेज़|रफ्तार", {"props": ["rocket"]}),
    ("बारिश|बादल|मौसम", {"props": ["rain"]}),
    ("सूरज|धूप|सुबह|गर्मी", {"props": ["sun"]}),
    ("रात|नींद|सपना|चाँद|चांद|थक", {"props": ["moon"], "setting": "night"}),
    ("पेड़|जंगल|प्रकृति|पौध|बीज", {"props": ["plant"], "setting": "park"}),
    ("घर|परिवार|कमरा", {"props": ["house"], "setting": "room"}),
    ("नौकरी|ऑफिस|दफ्तर|बॉस|व्यापार|बिज़नेस|कंपनी", {"setting": "office"}),
    ("स्कूल|पढ़ाई|पढ़|सीख|छात्र|टीचर|परीक्षा|कक्षा", {"props": ["book", "graduation"], "setting": "classroom"}),
    ("किताब|कहानी", {"props": ["book"], "action": "read"}),
    ("लिख|नोट|योजना|प्लान", {"action": "write"}),
    ("जीत|इनाम|चैंपियन|सबसे अच्छ", {"action": "cheer", "props": ["trophy"], "mood": "happy"}),
    ("दिमाग|दिमाग़|याद|ध्यान|स्मार्ट", {"props": ["brain"]}),
    ("लक्ष्य|मकसद|निशाना", {"props": ["target"]}),
    ("बिल्कुल सही|पूरा हो", {"props": ["check"]}),
    ("गलत|ग़लत|गलती|मिथक", {"props": ["cross"], "action": "shrug"}),
    ("खतरा|ख़तरा|सावधान|जोखिम|समस्या|परेशानी", {"props": ["warning"], "mood": "worried"}),
    ("ऊर्जा|बैटरी|ताकत|ताक़त", {"props": ["battery"]}),
    ("खोज|ढूंढ|ढूँढ|रिसर्च", {"props": ["magnifier"]}),
    ("तोहफा|तोहफ़ा|गिफ्ट|मुफ्त|मुफ़्त", {"props": ["gift"]}),
    ("गाना|संगीत|नाच|डांस", {"props": ["music"], "action": "dance"}),
    ("आग|जुनून", {"props": ["fire"]}),
    ("पानी|समुद्र|नदी|प्यास", {"props": ["drop"]}),
    ("गाड़ी|कार|सफर|सफ़र|यात्रा|सड़क", {"props": ["car"], "setting": "city"}),
    ("शहर|बाज़ार|बाजार", {"setting": "city"}),
    ("संदेश|मैसेज|ईमेल|चिट्ठी", {"props": ["mail"]}),
    ("राज़|राज|सुरक्षा|पासवर्ड|ताला", {"props": ["lock"]}),
    ("लोग|दोस्त|टीम|सब मिलकर|समाज", {"props": ["people"]}),
    ("सेहत|स्वास्थ्य|खाना|फल|सेब", {"props": ["apple"]}),
    ("प्यार|दिल|परवाह", {"props": ["heart"], "mood": "happy"}),
    ("पहाड़|चुनौती|मुश्किल|कठिन", {"props": ["mountain"]}),
    ("अंतरिक्ष|ब्रह्मांड|ग्रह", {"setting": "space", "props": ["rocket"]}),
    ("वीडियो|कैमरा|यूट्यूब", {"props": ["camera"]}),
    ("खुश|बढ़िया|शानदार|मज़ा|मजा|बधाई", {"action": "cheer", "mood": "happy"}),
    ("दुखी|उदास|अकेल|रोना|रोने|रोया", {"action": "sad", "mood": "sad"}),
    ("गुस्सा|गुस्से|नाराज़|नाराज", {"action": "angry", "mood": "angry"}),
    ("डर|घबरा|चिंता|तनाव", {"action": "scared", "mood": "worried"}),
    ("हैरान|चौंक|अरे|वाह|कमाल", {"action": "surprised", "mood": "surprised"}),
    ("चलते हैं|चलना|टहल", {"action": "walk"}),
    ("दौड़|भागना|भागो|जल्दी", {"action": "run"}),
    ("आराम|शांत|सुकून", {"action": "relax", "mood": "happy"}),
    ("नमस्ते|नमस्कार|स्वागत|हेलो|हैलो", {"action": "wave", "mood": "happy"}),
    ("धन्यवाद|शुक्रिया|सब्सक्राइब|फॉलो|अलविदा", {"action": "wave", "mood": "happy"}),
]

STOP = set("""a an the and or but if then so to of in on at for with from by is are was were be been it its this that these
those you your we our they their i me my he she his her as not no do does did can could will would should just very
really about into than more most some any all each every here there what why how when who which while also only own""".split())


def split_sentences(text):
    text = re.sub(r"\s+", " ", text.strip())
    parts = re.split(r"(?<=[.!?।])\s+", text)
    return [p.strip() for p in parts if p.strip()]


def headline_for(sentence):
    words = [w for w in re.findall(r"[A-Za-z][A-Za-z'\-]+", sentence) if w.lower() not in STOP and len(w) > 2]
    if not words:
        # non-Latin text (e.g. Hindi): the two longest words, in spoken order
        toks = [t.strip(".,!?;:\u0964\"'") for t in sentence.split()]
        toks = [t for t in toks if len(t) > 2]
        top = sorted(toks, key=len, reverse=True)[:2]
        return " ".join(t for t in dict.fromkeys(toks) if t in top)[:24]
    words.sort(key=len, reverse=True)
    keep = [w for w in re.findall(r"[A-Za-z][A-Za-z'\-]+", sentence) if w in words[:2]]
    return " ".join(dict.fromkeys(keep)).upper()[:24]


def hints_for(sentence):
    low = sentence.lower()
    out = {"props": []}
    matches = [h for pat, h in RULES if re.search(pat, low)]
    matches += [h for pat, h in HI_RULES if re.search(pat, sentence)]
    for h in matches:
        if True:
            for k, v in h.items():
                if k == "props":
                    out["props"] += [p for p in v if p not in out["props"]]
                elif k not in out:
                    out[k] = v
    out["props"] = out["props"][:2]
    return out


def topic_script(topic):
    """Offline fallback when the prompt is only a short topic and no LLM is set up.
    It gives a generic outline; paste a full script (or enable an LLM) for real content."""
    t = topic.strip().rstrip(".?!")
    is_q = bool(re.match(r"(?i)(how|why|what|when|where|who|which|can|do|does|is|are|should|will)\b", t)) or topic.strip().endswith("?")
    if is_q:
        q = t[0].upper() + t[1:] + "?"
        return [
            f"{q} Let's find out.",
            "Most people think the answer is complicated. But it is simpler than you think.",
            "Here is the secret. It all comes down to a few small steps that work together.",
            "Each step builds on the last one, and that is how the whole thing works.",
            "Now you know the answer. Which part surprised you the most? Tell me in the comments!",
        ]
    T = t[0].upper() + t[1:]
    return [
        f"Have you ever wondered about {t}?",
        f"Most people think {t} is complicated. But the idea is simpler than you think.",
        f"Here is the secret. {T} starts with one small step, repeated every day.",
        "Each step builds on the last one, and slowly the results grow.",
        "So start small, stay patient, and watch what happens. Tell me what you think in the comments!",
    ]


def builtin_plan(prompt, style, ratio):
    sents = split_sentences(prompt)
    words = len(prompt.split())
    if len(sents) < 2 and words < 25:
        sents = topic_script(prompt)
        title = prompt.strip()[:60]
    else:
        title = sents[0][:60]
    # merge very short sentences so each scene has ~6-30 words
    merged = []
    for s in sents:
        if merged and len(merged[-1].split()) < 6:
            merged[-1] += " " + s
        else:
            merged.append(s)
    scenes = []
    last_setting = "plain"
    for i, s in enumerate(merged):
        h = hints_for(s)
        setting = h.get("setting") or last_setting
        last_setting = setting
        action = h.get("action") or ("wave" if i == 0 and len(merged) > 2 else "talk")
        if not h.get("action") and h["props"] and i % 2 == 1:
            action = "present"
        scenes.append({
            "narration": s,
            "action": action,
            "mood": h.get("mood") or ("happy" if i in (0, len(merged) - 1) else "neutral"),
            "setting": setting,
            "props": h["props"],
            "headline": headline_for(s),
            "enter": "left" if i == 0 else "none",
            "camera": ["zoom_in", "static", "zoom_out", "pan_right"][i % 4],
            "friend": None,
        })
    if scenes:
        scenes[-1]["action"] = scenes[-1]["action"] if scenes[-1]["action"] != "talk" else "wave"
    return {"title": title, "style": style, "ratio": ratio, "scenes": scenes}


def llm_system_prompt(seconds, language):
    n = max(3, round(seconds / 7))
    return f"""You are a director of short animated stickman explainer videos.
Turn the user's prompt into a JSON plan for a video of about {seconds} seconds
({n} scenes, 12-25 spoken words per scene). Narration language: {language}.
Use a strong hook in scene 1, clear simple sentences, and a memorable ending.
Return ONLY JSON with this shape:
{{"title": str,
  "scenes": [{{"narration": str, "action": one of {ACTIONS},
              "mood": one of {MOODS}, "setting": one of {SETTINGS},
              "props": up to 2 of {sorted(all_prop_names())},
              "headline": "2-4 WORD KEY PHRASE (in caps, may be empty)",
              "enter": "left"|"right"|"none", "camera": one of {CAMERAS},
              "friend": null or {{"action": one of {ACTIONS}, "mood": one of {MOODS}}} }}]}}
Pick actions/props that visually show what the narration says. Vary settings and cameras.
Use a "friend" only when a second character helps the story."""


SPEAKERS = ("main", "friend", "narrator")


def pitch_str(p):
    """-6 / "-6" / "-6Hz" / "-6 hz" -> "-6Hz"; "" or None -> None."""
    if p in (None, ""):
        return None
    m = re.match(r"^\s*([+-]?\d+(?:\.\d+)?)\s*(hz)?\s*$", str(p), re.I)
    return f"{int(round(float(m.group(1)))):+d}Hz" if m else None


def _clean_voice(d):
    """Voice overrides: pitch ("-6Hz"), speed (0.5-2), edge_voice / voice / sapi_voice names."""
    out = {}
    if pitch_str(d.get("pitch")):
        out["pitch"] = pitch_str(d.get("pitch"))
    try:
        if d.get("speed") not in (None, ""):
            out["speed"] = min(2.0, max(0.5, float(d["speed"])))
    except (TypeError, ValueError):
        pass
    out.update({k: str(d[k]).strip() for k in ("edge_voice", "voice", "sapi_voice") if str(d.get(k) or "").strip()})
    return out


def _clean_voices(vs):
    """Per-scene voices: {"main": {...}, "friend": {...}, "narrator": {...}}."""
    if not isinstance(vs, dict):
        return {}
    return {w: c for w in SPEAKERS if isinstance(vs.get(w), dict) and (c := _clean_voice(vs[w]))}


def _clean_outfit(o):
    """Costume changes for one scene: colours as [r, g, b], plus the hoodie and ripped jeans of the cartoon body."""
    if not isinstance(o, dict):
        return {}
    out = {k: [int(c) for c in o[k]] for k in ("shirt", "pants", "shoes", "hair")
           if isinstance(o.get(k), list) and len(o[k]) == 3}
    return {**out, **{k: True for k in ("hoodie", "ripped") if o.get(k)}}


def _clean_lines(lines):
    """Dialogue lines: [{"who": main|friend|narrator, "text", "action"?, "mood"?, "other"?: {action, mood}}].

    Also accepts plain strings like "friend: kaha chalna hai?" (no prefix = main).
    """
    out = []
    for ln in lines or []:
        if isinstance(ln, str):
            m = re.match(r"\s*(main|friend|narrator)\s*:\s*(.+)", ln, re.I)
            ln = {"who": m.group(1).lower(), "text": m.group(2)} if m else {"who": "main", "text": ln}
        if not isinstance(ln, dict) or not str(ln.get("text") or "").strip():
            continue
        c = {"who": ln.get("who") if ln.get("who") in SPEAKERS else "main", "text": str(ln["text"]).strip()}
        if ln.get("action") in ACTIONS:
            c["action"] = ln["action"]
        if ln.get("mood") in MOODS:
            c["mood"] = ln["mood"]
        c.update(_clean_voice(ln))
        if isinstance(ln.get("gain"), (int, float)) and ln["gain"] > 0:  # louder for shouting, softer for whispers
            c["gain"] = float(ln["gain"])
        if isinstance(ln.get("pause"), (int, float)) and ln["pause"] >= 0:  # seconds of silence before this line
            c["pause"] = float(ln["pause"])
        if ln.get("hearts"):
            c["hearts"] = True
        if ln.get("crowd"):  # standup: the audience laughs after this line ("clap": laughs and applauds)
            c["crowd"] = "clap" if ln["crowd"] == "clap" else True
        if str(ln.get("name") or "").strip():  # who says it, for the video-AI prompts ("The safari guide")
            c["name"] = str(ln["name"]).strip()
        o = ln.get("other")
        if isinstance(o, dict):
            o = {k: o[k] for k in ("action", "mood") if o.get(k) in (ACTIONS if k == "action" else MOODS)}
            if o:
                c["other"] = o
        out.append(c)
    return out


def sanitize(plan, style, ratio):
    plan = dict(plan or {})
    plan.setdefault("title", "Stickman video")
    from .themes import resolve
    plan["style"] = resolve(plan.get("style") or style)
    plan["ratio"] = plan.get("ratio") or ratio
    props_ok = set(all_prop_names())
    clean = []
    for i, sc in enumerate(plan.get("scenes") or []):
        if isinstance(sc, str):
            sc = {"narration": sc}
        lines = _clean_lines(sc.get("lines"))
        text = " ".join(ln["text"] for ln in lines) if lines else str(sc.get("narration") or "").strip()
        if not text:
            continue
        h = hints_for(text)
        action = sc.get("action") if sc.get("action") in ACTIONS else (h.get("action") or "talk")
        mood = sc.get("mood") if sc.get("mood") in MOODS else (h.get("mood") or "neutral")
        setting = sc.get("setting") if sc.get("setting") in SETTINGS else (h.get("setting") or (clean[-1]["setting"] if clean else "plain"))
        props = [p for p in (sc.get("props") or []) if isinstance(p, str) and (p in props_ok or p.lower().endswith(".png"))][:3]
        if not props and "props" not in sc:
            props = h["props"]
        friend = sc.get("friend")
        if isinstance(friend, dict):
            friend = {"action": friend.get("action") if friend.get("action") in ACTIONS else "nod",
                      "mood": friend.get("mood") if friend.get("mood") in MOODS else "neutral",
                      **({"character": friend["character"]} if friend.get("character") in CHARACTERS else {})}
        else:
            friend = None
        clean.append({
            "narration": text, "action": action, "mood": mood, "setting": setting, "props": props,
            "headline": str(sc.get("headline") if sc.get("headline") is not None else headline_for(text))[:40],
            "enter": sc.get("enter") if sc.get("enter") in ("left", "right", "none") else ("left" if i == 0 else "none"),
            "camera": sc.get("camera") if sc.get("camera") in CAMERAS else "zoom_in",
            "friend": friend,
            **({"position": sc["position"]} if sc.get("position") in ("left", "center", "right") else {}),
            **({"layout": sc["layout"]} if sc.get("layout") in ("call", "standup", "trio") else {}),
            **({"beat": sc["beat"]} if sc.get("beat") in ("ring", "grab", "struggle", "glare", "bite") else {}),
            **({"outfit": o} if (o := _clean_outfit(sc.get("outfit"))) else {}),
            **({"character": sc["character"]} if sc.get("character") in CHARACTERS else {}),
            **({"mic": sc["mic"]} if sc.get("mic") in ("stand", "boom") else {}),
            **({"backdrop": sc["backdrop"]} if sc.get("backdrop") in ("curtain", "outdoor") else {}),
            **({"audience": False} if sc.get("audience") is False else {}),
            **({"vehicle": "scooter"} if sc.get("vehicle") == "scooter" else {}),
            **({"call_end": True} if sc.get("call_end") else {}),
            **({"duration": float(sc["duration"])} if isinstance(sc.get("duration"), (int, float)) else {}),
            **({k: sc[k] for k in ("start", "end", "words", "clip_prompt") if sc.get(k) is not None}),
            **({"lines": lines} if lines else {}),
            **({"voices": v} if (v := _clean_voices(sc.get("voices"))) else {}),
            **({"speaker": sc["speaker"]} if sc.get("speaker") in SPEAKERS else {}),
        })
    if not clean:
        raise ValueError("The plan has no scenes with narration.")
    plan["scenes"] = clean
    return plan


def make_plan(prompt, cfg, style, ratio, seconds=45, language="English", log=print):
    from . import llm
    prompt = prompt.strip()
    if prompt.startswith("{"):
        return sanitize(json.loads(prompt), style, ratio)
    lcfg = cfg.get("llm", {})
    if lcfg.get("backend", "auto") != "none":
        try:
            raw = llm.complete_json(llm_system_prompt(seconds, language), prompt, lcfg, log=log)
            if raw:
                log("Script written by LLM (" + raw.get("_backend", "llm") + ")")
                raw.pop("_backend", None)
                return sanitize(raw, style, ratio)
        except Exception as e:
            log(f"LLM planner failed ({e}); using built-in planner")
    log("Script made by the built-in planner (no LLM). Tip: run Ollama or set an API key for smarter scripts.")
    return sanitize(builtin_plan(prompt, style, ratio), style, ratio)


# ---------------------------------------------------------------------------
# Audio -> scenes
# ---------------------------------------------------------------------------
def _group_segments(tr, min_len=3.0, max_len=8.0):
    """Merge transcript segments into scene-sized chunks with start/end/words."""
    words = tr.get("words") or []
    pieces = []
    for sg in tr["segments"]:
        sw = [w for w in words if sg["start"] - 0.05 <= w["start"] < sg["end"] + 0.05]
        if sg["end"] - sg["start"] > max_len * 1.4 and len(sw) > 6:
            # split a long segment at sentence ends / commas near the middle
            cur = []
            for w in sw:
                cur.append(w)
                long = cur[-1]["end"] - cur[0]["start"]
                if long >= max_len or (long >= min_len and re.search(r"[.!?,\u0964]$", w["word"])):
                    pieces.append({"start": cur[0]["start"], "end": cur[-1]["end"], "text": " ".join(x["word"] for x in cur), "words": cur})
                    cur = []
            if cur:
                pieces.append({"start": cur[0]["start"], "end": cur[-1]["end"], "text": " ".join(x["word"] for x in cur), "words": cur})
        else:
            pieces.append({**sg, "words": sw})
    scenes = []
    for p in pieces:
        if scenes:
            last = scenes[-1]
            short = last["end"] - last["start"] < min_len
            open_sentence = not re.search(r"[.!?\u0964]$", last["text"].strip())
            if (short or (open_sentence and p["end"] - last["start"] <= max_len)) and p["end"] - last["start"] <= max_len * 1.5:
                last["end"] = p["end"]
                last["text"] = (last["text"] + " " + p["text"]).strip()
                last["words"] += p["words"]
                continue
        scenes.append({"start": p["start"], "end": p["end"], "text": p["text"].strip(), "words": list(p["words"])})
    if len(scenes) > 1 and scenes[-1]["end"] - scenes[-1]["start"] < min_len:  # tiny last line
        last = scenes.pop()
        scenes[-1]["end"] = last["end"]
        scenes[-1]["text"] += " " + last["text"]
        scenes[-1]["words"] += last["words"]
    return scenes


def visuals_system_prompt(n, direction):
    extra = f"\nCreative direction from the user: {direction}" if direction else ""
    return f"""You direct animated stickman videos. The narration is already recorded, so do NOT change it.
For each of the {n} numbered narration lines, choose visuals that show what is being said.{extra}
Return ONLY JSON: {{"title": str, "scenes": [{{"action": one of {ACTIONS}, "mood": one of {MOODS},
"setting": one of {SETTINGS}, "props": up to 2 of {sorted(all_prop_names())},
"headline": "2-4 word key phrase in the narration language (may be empty)",
"camera": one of {CAMERAS}, "friend": null or {{"action": one of {ACTIONS}, "mood": one of {MOODS}}} }}]}}
The scenes array must have exactly {n} items, in the same order. Vary settings and cameras."""


def plan_from_transcript(tr, audio_path, cfg, style, ratio, direction="", log=print):
    from . import llm
    groups = _group_segments(tr)
    if not groups:
        raise ValueError("No speech found in the transcript.")
    base = builtin_plan(" ".join(g["text"] for g in groups), style, ratio)  # for the title only
    scenes = []
    for i, g in enumerate(groups):
        h = hints_for(g["text"])
        scenes.append({
            "narration": g["text"], "start": round(g["start"], 3), "end": round(g["end"], 3),
            "words": [[w["word"], round(w["start"], 3), round(w["end"], 3)] for w in g["words"]],
            "action": h.get("action") or ("wave" if i == 0 else ("present" if h["props"] and i % 2 else "talk")),
            "mood": h.get("mood") or ("happy" if i == 0 else "neutral"),
            "setting": h.get("setting") or (scenes[-1]["setting"] if scenes else "plain"),
            "props": h["props"], "headline": headline_for(g["text"]),
            "enter": "left" if i == 0 else "none", "camera": ["zoom_in", "static", "zoom_out", "pan_right"][i % 4],
            "friend": None,
        })
    title = base.get("title") or "My video"
    lcfg = cfg.get("llm", {})
    if lcfg.get("backend", "auto") != "none":
        try:
            lines = "\n".join(f"{i + 1}. {sc['narration']}" for i, sc in enumerate(scenes))
            raw = llm.complete_json(visuals_system_prompt(len(scenes), direction), lines, lcfg, log=log)
            if raw and len(raw.get("scenes") or []) == len(scenes):
                for sc, v in zip(scenes, raw["scenes"]):
                    for k in ("action", "mood", "setting", "props", "headline", "camera", "friend"):
                        if k in v:
                            sc[k] = v[k]
                title = raw.get("title") or title
                log("Visuals chosen by LLM (" + raw.get("_backend", "llm") + ")")
            elif raw:
                log("LLM returned a different number of scenes; using keyword visuals")
        except Exception as e:
            log(f"LLM visuals failed ({e}); using keyword visuals")
    plan = {"title": title, "style": style, "ratio": ratio, "scenes": scenes,
            "audio": {"path": os.path.abspath(audio_path), "transcript_by": tr.get("backend")}}
    return sanitize(plan, style, ratio)
