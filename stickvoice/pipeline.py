"""High-level helpers shared by the CLI and the web UI."""
import copy
import json
import os
import re
import time

from . import planner, renderer

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT = os.path.join(ROOT, "output")


def load_config(path=None):
    path = path or os.path.join(ROOT, "config.json")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def slug(text):
    s = re.sub(r"[^A-Za-z0-9]+", "-", text or "video").strip("-").lower()[:40] or "video"
    return time.strftime("%Y%m%d-%H%M%S-") + s


def make_plan(prompt, cfg, style=None, ratio=None, seconds=None, language=None, log=print):
    v = cfg.get("video", {})
    return planner.make_plan(prompt, cfg, style or v.get("style", "notebook"), ratio or v.get("ratio", "16:9"),
                             int(seconds or v.get("seconds", 45)), language or v.get("language", "English"), log=log)


def render_plan(plan, cfg, out_dir=None, log=print, progress=None, voice_overrides=None, preview_seconds=None):
    cfg = copy.deepcopy(cfg)
    if voice_overrides:
        cfg.setdefault("voice", {}).update({k: v for k, v in voice_overrides.items() if v not in (None, "")})
    plan = planner.sanitize(plan, plan.get("style") or cfg["video"]["style"], plan.get("ratio") or cfg["video"]["ratio"])
    out_dir = out_dir or os.path.join(OUTPUT, slug(plan.get("title")))
    job = renderer.Job(log=log, progress=progress)
    return renderer.render(plan, cfg, out_dir, job, preview_seconds=preview_seconds)


LANG_CODES = {"english": "en", "hindi": "hi", "bengali": "bn", "bangla": "bn", "tamil": "ta", "telugu": "te",
              "marathi": "mr", "gujarati": "gu", "kannada": "kn", "malayalam": "ml", "punjabi": "pa", "urdu": "ur",
              "spanish": "es", "french": "fr", "german": "de", "japanese": "ja", "chinese": "zh", "arabic": "ar",
              "portuguese": "pt", "russian": "ru", "korean": "ko", "italian": "it"}


def lang_code(language):
    """'Hindi' -> 'hi'; 'hi' stays 'hi'; empty/auto -> None (auto-detect)."""
    if not language or language.lower() in ("auto", "detect"):
        return None
    l = language.strip().lower()
    return LANG_CODES.get(l, l if len(l) <= 3 else None)


def plan_from_audio(audio_path, cfg, style=None, ratio=None, language=None, transcript=None, direction="", log=print):
    """Your recording -> transcript (with timings) -> scene plan that plays your audio."""
    from . import transcribe
    v = cfg.get("video", {})
    style, ratio = style or v.get("style", "notebook"), ratio or v.get("ratio", "16:9")
    if transcript and os.path.isfile(transcript):
        with open(transcript, encoding="utf-8") as f:
            transcript = f.read()
    if transcript and transcript.strip():
        tr = transcribe.from_typed_text(audio_path, transcript)
        log("Using your typed transcript (timed to the pauses in the audio)")
    else:
        tr = transcribe.transcribe(audio_path, cfg, lang_code(language), log=log)
        log(f"Transcribed by {tr['backend']}: {len(tr['segments'])} segments, {len(tr['words'])} timed words")
    return planner.plan_from_transcript(tr, audio_path, cfg, style, ratio, direction, log=log)
