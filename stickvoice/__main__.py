"""Command line:

  python -m stickvoice "How does rain form?"                 # prompt -> video
  python -m stickvoice "..." --style pop --ratio 9:16 --seconds 30
  python -m stickvoice --plan output/<job>/plan.json         # re-render an edited plan
  python -m stickvoice "..." --plan-only                     # just write the script
  python -m stickvoice --audio my-voice.mp3                 # your recording -> video
  python -m stickvoice --audio my-voice.mp3 --transcript words.txt --direction "funny, cooking"
  python -m stickvoice "..." --style a5-edo --director     # Director Mode: clip prompts for Kling/Flow
  python -m stickvoice --assemble output/<job>                # join AI clips from the Colab notebook
  python -m stickvoice --web                                 # open the web app
"""
import argparse
import json
import os
import sys

from . import pipeline
from .stickman import ACTIONS
from .themes import THEMES, style_choices
from .props import all_prop_names


def main(argv=None):
    ap = argparse.ArgumentParser(prog="stickvoice", description="Prompt -> narrated stickman animation video")
    ap.add_argument("prompt", nargs="?", help="topic, idea or full script")
    ap.add_argument("--plan", help="render an existing plan.json")
    ap.add_argument("--audio", help="your own voice recording (mp3/wav/m4a...): transcribe it and animate to it")
    ap.add_argument("--transcript", help="(with --audio) the spoken words as text or a .txt file; skips speech-to-text")
    ap.add_argument("--direction", default="", help="(with --audio) extra creative direction for the visuals")
    ap.add_argument("--plan-only", action="store_true", help="only write the scene plan")
    ap.add_argument("--director", action="store_true",
                    help="Director Mode: write a treatment + one ~10 s video prompt per scene (Kling/Flow/Runway), no render")
    ap.add_argument("--assemble", metavar="FOLDER",
                    help="join AI clips (clips.zip from the Colab notebook) with this render's voice and captions")
    ap.add_argument("--clips", help="(with --assemble) clips.zip or folder; default: FOLDER/clips.zip")
    ap.add_argument("--no-captions", action="store_true", help="(with --assemble) leave the captions out")
    ap.add_argument("--style", choices=style_choices(), metavar="STYLE", help="a1-light, a1-dark, a2-tech, a2-story, a3-cave, a4-cozy, a5-edo, a5-egypt, a5-rome, a6-amber, b1-notebook, b2-paper, c1-toon")
    ap.add_argument("--ratio", choices=["16:9", "9:16", "1:1"])
    ap.add_argument("--seconds", type=int)
    ap.add_argument("--language")
    ap.add_argument("--voice-backend", choices=["auto", "voicestudio", "edge", "sapi", "silent"])
    ap.add_argument("--voice", help="VoiceStudio voice/profile id")
    ap.add_argument("--edge-voice", help="edge-tts voice, e.g. en-US-AriaNeural, hi-IN-MadhurNeural")
    ap.add_argument("--no-llm", action="store_true", help="use the built-in planner only")
    ap.add_argument("--out", help="output folder")
    ap.add_argument("--preview", type=float, help="render only the first N seconds")
    ap.add_argument("--config")
    ap.add_argument("--web", action="store_true", help="start the web app")
    ap.add_argument("--list", action="store_true", help="list styles, actions and props")
    ap.add_argument("--characters", action="store_true", help="draw the character sheet to output/characters")
    a = ap.parse_args(argv)

    if a.list:
        for k, t in THEMES.items():
            print(f"{k:12s} {t['label']:34s} {t['about']}")
        print("Actions:", ", ".join(ACTIONS))
        print("Props  :", ", ".join(all_prop_names()))
        return 0
    if a.characters:
        from .characters import character_sheet
        print("Character sheet:", character_sheet(a.out or os.path.join(pipeline.OUTPUT, "characters")))
        return 0
    if a.web:
        from .web import serve
        return serve(a.config)

    if a.assemble:
        from .assemble import assemble
        assemble(a.assemble, a.clips, captions=not a.no_captions)
        return 0

    cfg = pipeline.load_config(a.config)
    if a.no_llm:
        cfg.setdefault("llm", {})["backend"] = "none"
    if a.plan:
        with open(a.plan, encoding="utf-8") as f:
            plan = json.load(f)
        if a.style:
            plan["style"] = a.style
        if a.ratio:
            plan["ratio"] = a.ratio
    elif a.audio:
        plan = pipeline.plan_from_audio(a.audio, cfg, a.style, a.ratio, a.language, a.transcript,
                                        a.direction or (a.prompt or ""))
    elif a.prompt:
        plan = pipeline.make_plan(a.prompt, cfg, a.style, a.ratio, a.seconds, a.language)
    else:
        ap.print_help()
        return 1

    if a.director:
        from .director import treatment
        out = a.out or os.path.join(pipeline.OUTPUT, pipeline.slug(plan.get("title")))
        os.makedirs(out, exist_ok=True)
        path = os.path.join(out, "director_prompts.md")
        with open(path, "w", encoding="utf-8") as f:
            f.write(treatment(plan))
        from .director import clip_jobs
        with open(os.path.join(out, "clips.json"), "w", encoding="utf-8") as f:
            json.dump(clip_jobs(plan), f, indent=2, ensure_ascii=False)
        print("Director prompts written:", path)
        return 0

    if a.plan_only:
        out = a.out or os.path.join(pipeline.OUTPUT, pipeline.slug(plan.get("title")))
        os.makedirs(out, exist_ok=True)
        path = os.path.join(out, "plan.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(plan, f, indent=2, ensure_ascii=False)
        print("Plan written:", path)
        return 0

    overrides = {"backend": a.voice_backend, "voice": a.voice, "edge_voice": a.edge_voice}

    def progress(p, msg=""):
        sys.stdout.write(f"\r[{p:5.1f}%] {msg:<40}")
        sys.stdout.flush()

    res = pipeline.render_plan(plan, cfg, a.out, log=lambda m: print("\n" + m), progress=progress,
                               voice_overrides=overrides, preview_seconds=a.preview)
    print("\nVideo:", res["video"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
