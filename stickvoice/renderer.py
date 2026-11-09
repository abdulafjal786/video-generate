"""Plan + voice -> finished MP4 (video, voice, sound effects, captions)."""
import json
import math
import os
import re
import subprocess
import time

import numpy as np
from PIL import Image, ImageDraw

from . import audio, voice
from .canvas import SS, Canvas, font, smooth, mix, clamp, lerp
from .assemble import append_clip, end_clip_spec
from .planner import RULES, pitch_str
from .props import draw_prop
from .scenes import draw_background, draw_call_rooms, draw_curtain_stage, draw_standup_stage, standup_floor
from .stickman import ACTION_MOOD, ACTIONS, MOODS, SLAP_PERIOD, blend, draw_stickman, make_pose, slap_lift, walk_cycle, STAND
from .themes import CHARACTERS, get_theme

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RATIOS = {"16:9": (1280, 720), "9:16": (720, 1280), "1:1": (1080, 1080)}
LEAD, TAIL, FADE = 0.3, 0.5, 0.3
ENTER_TIME = 1.1


# ---------------------------------------------------------------------------
def _layout(W, H, has_props, has_friend, position=None):
    portrait = H > W * 1.15
    m = min(W, H)
    L = {"portrait": portrait, "ground": H * (0.70 if portrait else 0.80)}
    if portrait:
        L.update(char_h=H * 0.25, char_x=W * (0.32 if has_friend else 0.5), friend_x=W * 0.7,
                 props=(W * 0.5, H * 0.30), prop_s=W * 0.34, headline=(W * 0.5, H * 0.075))
    else:
        L.update(char_h=H * (0.38 if has_friend else 0.42), headline_y=H * 0.1)
        if has_friend:
            L.update(char_x=W * 0.28, friend_x=W * 0.74, props=(W * 0.51, H * 0.36), prop_s=H * 0.22,
                     headline=(W * 0.5, H * 0.09))
        elif has_props:
            L.update(char_x=W * 0.28, props=(W * 0.67, H * 0.46), prop_s=H * 0.30, headline=(W * 0.67, H * 0.12))
        else:
            L.update(char_x=W * 0.5, props=(W * 0.5, H * 0.4), prop_s=H * 0.3, headline=(W * 0.5, H * 0.12))
    if position in ("left", "center", "right") and not has_friend:
        L["char_x"] = W * {"left": 0.25, "center": 0.5, "right": 0.75}[position]
        if has_props and not portrait:
            L["props"] = (W * (0.7 if position != "right" else 0.3), L["props"][1])
            L["headline"] = (L["props"][0], L["headline"][1])
    L["headline_size"] = m * (0.075 if not portrait else 0.08)
    L["caption_size"] = m * (0.046 if not portrait else 0.052)
    L["caption_y"] = H * (0.905 if not portrait else 0.84)
    return L


def _prop_positions(n, center, s):
    cx, cy = center
    if n <= 1:
        return [(cx, cy)]
    if n == 2:
        return [(cx - s * 0.62, cy), (cx + s * 0.62, cy)]
    return [(cx - s * 0.7, cy + s * 0.3), (cx + s * 0.7, cy + s * 0.3), (cx, cy - s * 0.45)][:n]


def _word_times(words, speech_dur, start=LEAD):
    weights = []
    for w in words:
        wt = len(w) + 2.0
        if re.search(r"[,;:]$", w):
            wt += 3
        if re.search(r"[.!?।]$", w):
            wt += 5
        weights.append(wt)
    total = sum(weights) or 1
    t, out = start, []
    for w, wt in zip(words, weights):
        d = speech_dur * wt / total
        out.append((t, t + d))
        t += d
    return out


def _chunks(words, times, max_words=7):
    chunks, cur = [], []
    for i, w in enumerate(words):
        cur.append(i)
        if len(cur) >= max_words or re.search(r"[.!?,;:।]$", w):
            chunks.append(cur)
            cur = []
    if cur:
        chunks.append(cur)
    return [(c, times[c[0]][0], times[c[-1]][1]) for c in chunks]


def _prop_time(prop, words, times, idx, n):
    pats = [p for p, h in RULES if prop in h.get("props", [])]
    for i, w in enumerate(words):
        lw = w.lower()
        if any(re.search(p, lw) for p in pats):
            return max(0.2, times[i][0] - 0.15)
    return 0.45 + idx * 0.7


def _scene_entry(sc, speech, dur, words, times, lead, fps, W, H):
    return {"fps": fps, "sc": sc, "speech": speech, "speech_dur": len(speech) / audio.SR, "dur": dur,
            "words": words, "times": times, "lead": lead,
            "chunks": _chunks(words, times, 5 if H > W else 7), "env": audio.envelope(speech, fps)}


LINE_GAP = 0.3  # pause between two dialogue lines


VOICE_KEYS = ("pitch", "speed", "edge_voice", "voice", "sapi_voice", "instructions")


def voice_for(who, plan, vcfg, sc=None, ln=None):
    """Voice settings for a speaker, later layers win:
    base voice -> plan["voices"][who] -> scene["voices"][who] -> the line's own pitch/speed/voice.

    The friend gets a different voice automatically (higher pitch, a bit faster) unless the plan sets one.
    """
    v = dict(vcfg)
    own = (plan.get("voices") or {}).get(who)
    if own:
        v.update(own)
    elif who == "friend":
        v["pitch"] = "+22Hz"
        v["speed"] = float(v.get("speed") or 1.0) * 1.06
    v.update(((sc or {}).get("voices") or {}).get(who) or {})
    v.update({k: ln[k] for k in VOICE_KEYS if (ln or {}).get(k) not in (None, "")})
    if v.get("pitch") not in (None, ""):
        v["pitch"] = pitch_str(v["pitch"]) or "+0Hz"
    return v


def _scenes_from_tts(plan, fps, W, H, vcfg, cache, job):
    """One voice clip per dialogue line. Each character's mouth follows only their own lines."""
    scenes, used = [], set()
    n = len(plan["scenes"])
    for i, sc in enumerate(plan["scenes"]):
        job.progress(2 + 28 * i / n, f"Voice {i + 1}/{n}")
        lines = sc.get("lines") or [{"who": sc.get("speaker", "main"), "text": sc["narration"]}]
        parts, spans, words, times, chunks, chunk_who = [], [], [], [], [], []
        pos = 0.0
        for ln in lines:
            clip, backend = voice.synthesize(ln["text"], cache, voice_for(ln["who"], plan, vcfg, sc, ln), log=job.log)
            used.add(backend)
            if ln.get("gain"):
                clip = np.clip(clip * float(ln["gain"]), -1.0, 1.0)
            if parts:
                gap = ln.get("pause", LINE_GAP)  # longer before a punchline
                parts.append(np.zeros(int(gap * audio.SR), dtype=np.float32))
                pos += gap
            d = len(clip) / audio.SR
            spans.append({**ln, "t0": LEAD + pos, "t1": LEAD + pos + d, "a": len(np.concatenate(parts)) if parts else 0, "n": len(clip)})
            parts.append(clip)
            lw = ln["text"].split()
            lt = _word_times(lw, d, start=LEAD + pos)
            for idxs, c0, c1 in _chunks(lw, lt, 5 if H > W else 7):
                chunks.append(([k + len(words) for k in idxs], c0, c1))
                chunk_who.append(ln["who"])
            words += lw
            times += lt
            pos += d
            if ln.get("crowd"):  # he waits for the laugh
                parts.append(np.zeros(int(audio.CROWD_LAUGH * audio.SR), dtype=np.float32))
                pos += audio.CROWD_LAUGH
        speech = np.concatenate(parts)
        dur = max(LEAD + pos + TAIL, 2.2, float(sc.get("duration") or 0))
        if sc.get("call_end"):
            dur += 1.6  # time for the hang-up
        if sc.get("enter") in ("left", "right"):
            dur = max(dur, ENTER_TIME + 1.5)
        e = _scene_entry(sc, speech, dur, words, times, LEAD, fps, W, H)
        e["chunks"], e["chunk_who"], e["lines"] = chunks, chunk_who, spans
        if sc.get("call_end"):
            e["call_end_t"] = LEAD + pos + 0.15
        for who in ("main", "friend"):  # separate lip-sync tracks
            mine = np.zeros_like(speech)
            for sp in spans:
                if sp["who"] == who:
                    mine[sp["a"]: sp["a"] + sp["n"]] = speech[sp["a"]: sp["a"] + sp["n"]]
            e["env" if who == "main" else "env_friend"] = audio.envelope(mine, fps)
        scenes.append(e)
    return scenes, used


def _scenes_from_audio(plan, fps, W, H, job):
    """Cut the uploaded recording into scenes using the transcript timestamps."""
    path = plan["audio"]["path"]
    if not os.path.exists(path):
        raise FileNotFoundError("Audio file not found: " + path)
    job.progress(5, "Loading your audio")
    full = audio.load(path)
    length = len(full) / audio.SR
    scs = plan["scenes"]
    starts = [0.0] + [float(sc.get("start", 0)) for sc in scs[1:]]
    for i in range(1, len(starts)):  # keep the cuts in order
        starts[i] = max(starts[i], starts[i - 1] + 0.5)
    ends = starts[1:] + [max(length, float(scs[-1].get("end") or 0)) + TAIL]
    scenes = []
    for sc, st, en in zip(scs, starts, ends):
        speech = full[int(st * audio.SR): int(en * audio.SR)]
        ws = sc.get("words") or []
        if ws and len(ws) == len(sc["narration"].split()):
            words = [w[0] for w in ws]
            times = [(max(0.0, w[1] - st), max(0.0, w[2] - st)) for w in ws]
        else:  # narration edited or no word timings: spread words over the spoken part
            words = sc["narration"].split()
            a = max(0.0, float(sc.get("start", st)) - st)
            b = max(a + 0.5, float(sc.get("end", en)) - st)
            times = _word_times(words, b - a, start=a)
        e = _scene_entry(sc, speech, en - st, words, times, 0.0, fps, W, H)
        e["from_recording"] = True
        scenes.append(e)
    scenes[0]["full_track"] = full
    return scenes, {"your recording"}


# ---------------------------------------------------------------------------
class Job:
    def __init__(self, log=print, progress=None):
        self.log = log
        self.progress = progress or (lambda p, msg="": None)


def render(plan, cfg, out_dir, job=None, preview_seconds=None):
    job = job or Job()
    t0 = time.time()
    os.makedirs(out_dir, exist_ok=True)
    th = get_theme(plan.get("style"))
    W, H = RATIOS.get(plan.get("ratio"), RATIOS["16:9"])
    fps = int(cfg.get("video", {}).get("fps", 30))
    vcfg = dict(cfg.get("voice", {}))
    vcfg.update(plan.get("voice") or {})
    cache = os.path.join(os.path.dirname(os.path.abspath(out_dir)), "_voice_cache")
    with open(os.path.join(out_dir, "plan.json"), "w", encoding="utf-8") as f:
        json.dump(plan, f, indent=2, ensure_ascii=False)
    try:
        from .director import treatment, clip_jobs
        with open(os.path.join(out_dir, "director_prompts.md"), "w", encoding="utf-8") as f:
            f.write(treatment(plan))
        with open(os.path.join(out_dir, "clips.json"), "w", encoding="utf-8") as f:
            json.dump(clip_jobs(plan), f, indent=2, ensure_ascii=False)
    except Exception as e:  # never block a render
        job.log(f"Director prompts skipped: {e}")

    # 1) sound per scene: your own recording, or a TTS voice ------------------
    if (plan.get("audio") or {}).get("path"):
        scenes, used = _scenes_from_audio(plan, fps, W, H, job)
    else:
        scenes, used = _scenes_from_tts(plan, fps, W, H, vcfg, cache, job)
    job.log("Voice: " + ", ".join(sorted(used)))

    if preview_seconds:
        keep, acc = [], 0
        for s in scenes:
            keep.append(s)
            acc += s["dur"]
            if acc >= preview_seconds:
                break
        scenes = keep

    # 2) timeline + audio mix ---------------------------------------------------
    starts, acc = [], 0.0
    for s in scenes:
        starts.append(acc)
        acc += s["dur"]
    total = acc
    with open(os.path.join(out_dir, "timeline.json"), "w", encoding="utf-8") as f:  # used by --assemble
        json.dump({"ratio": plan.get("ratio", "16:9"), "size": [W, H], "total": total,
                   "scenes": [{"start": st, "dur": s["dur"]} for s, st in zip(scenes, starts)]}, f, indent=2)
    mixbuf =np.zeros(int(total * audio.SR) + audio.SR, dtype=np.float32)
    sfx_gain = float(cfg.get("video", {}).get("sfx_volume", 0.6))
    if scenes and scenes[0].get("full_track") is not None:
        audio.add(mixbuf, scenes[0]["full_track"][: int(total * audio.SR)], 0.0)
    for i, (s, st) in enumerate(zip(scenes, starts)):
        if s.get("full_track") is None and not s.get("from_recording"):
            audio.add(mixbuf, s["speech"], st + s["lead"])
        sc = s["sc"]
        if sfx_gain <= 0:
            continue
        if i > 0 and sc.get("layout") not in ("call", "standup", "trio"):
            audio.add(mixbuf, audio.sfx("whoosh"), st - 0.1, 0.25 * sfx_gain)
        if s.get("call_end_t"):
            audio.add(mixbuf, audio.sfx("hangup"), st + s["call_end_t"] + 0.2, 0.5 * sfx_gain)
        for k, p in enumerate(sc.get("props", [])):
            s.setdefault("prop_t", []).append(_prop_time(p, s["words"], s["times"], k, len(sc["props"])))
            audio.add(mixbuf, audio.sfx("pop"), st + s["prop_t"][-1], 0.35 * sfx_gain)
        a0 = (ENTER_TIME if sc.get("enter") in ("left", "right") else 0) + 0.25
        fx = {"idea": "ding", "cheer": "jingle", "jump": "boing", "sad": "sad", "surprised": "boing", "clap": "jingle"}.get(sc["action"])
        if fx:
            audio.add(mixbuf, audio.sfx(fx), st + a0, 0.3 * sfx_gain)
        beat = sc.get("beat")
        if beat == "ring":
            for k in range(int(s["dur"] / 1.3) + 1):
                audio.add(mixbuf, audio.sfx("ring"), st + k * 1.3, 0.8 * sfx_gain)
        elif beat == "grab":
            audio.add(mixbuf, audio.sfx("tap"), st + 0.1, 1.0 * sfx_gain)
        if beat in ("grab", "struggle"):
            for k in range(int(s["dur"] / 0.9)):
                audio.add(mixbuf, audio.sfx("muffled"), st + 0.25 + k * 0.9, 1.0 * sfx_gain)
        elif beat == "bite":
            audio.add(mixbuf, audio.sfx("slap"), st + _bite_time(s), 0.8 * sfx_gain)
        for ln in s.get("lines") or []:
            if ln.get("crowd"):
                audio.add(mixbuf, audio.sfx("laugh"), st + ln["t1"] + 0.05, 1.5 * sfx_gain)
            if ln.get("crowd") == "clap":
                audio.add(mixbuf, audio.sfx("clap"), st + ln["t1"] + 0.15, 1.2 * sfx_gain)
        for hit in _slap_hits(s, sc, fps):
            audio.add(mixbuf, audio.sfx("slap"), st + hit, 0.5 * sfx_gain)
    for s in scenes:
        s.setdefault("prop_t", [_prop_time(p, s["words"], s["times"], k, 0) for k, p in enumerate(s["sc"].get("props", []))])
    music = plan.get("music") or cfg.get("video", {}).get("music")
    if music and os.path.exists(music):
        mixbuf += audio.loop_music(music, len(mixbuf), float(cfg.get("video", {}).get("music_volume", 0.08)))
    peak = np.max(np.abs(mixbuf)) or 1
    mixbuf = mixbuf * min(1.0, 0.95 / peak)
    wav_path = os.path.join(out_dir, "audio.wav")
    audio.write_wav(wav_path, mixbuf[: int(total * audio.SR)])

    # 3) captions file ---------------------------------------------------------
    _write_srt(os.path.join(out_dir, "captions.srt"), scenes, starts)

    # 4) frames -> ffmpeg -------------------------------------------------------
    out_mp4 = os.path.join(out_dir, "video.mp4" if not preview_seconds else "preview.mp4")
    vcodec = cfg.get("video", {})
    cmd = [audio.ffmpeg_exe(), "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
           "-r", str(fps), "-i", "-", "-i", wav_path, "-c:v", "libx264", "-preset", vcodec.get("preset", "veryfast"),
           "-crf", str(vcodec.get("crf", 20)), "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
           "-shortest", "-movflags", "+faststart", out_mp4]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    total_frames = int(total * fps)
    done = 0
    prev_pose, prev_frame = None, None
    show_captions = cfg.get("video", {}).get("captions", True) and plan.get("captions", True) is not False
    try:
        for i, (s, st) in enumerate(zip(scenes, starts)):
            sc = s["sc"]
            has_friend = bool(sc.get("friend"))
            L = _layout(W, H, bool(sc.get("props")), has_friend, sc.get("position"))
            call = sc.get("layout") == "call"
            standup = sc.get("layout") == "standup"
            if call or standup:
                L["caption_y"] = H * 0.93
            if sc.get("layout") == "trio":
                L["ground"], L["caption_y"] = H * (0.78 if L["portrait"] else 0.88), H * (0.9 if L["portrait"] else 0.95)
            bg = (draw_call_rooms(W, H, th) if call else _standup_bg(sc, W, H, th) if standup else
                  _trio_bg(W, H, L, th) if sc.get("layout") == "trio" else
                  draw_background(sc.get("setting", "plain"), W, H, L["ground"], th, seed=i))
            s["bg"] = bg
            strip = _ride_strip(bg) if sc.get("action") == "ride" else None
            nf = int(round((st + s["dur"]) * fps)) - int(round(st * fps))
            last_pose = None
            for f in range(nf):
                t = f / fps
                img = _scroll(strip, t, W) if strip else bg.copy()
                cv = Canvas(img)
                pose = _draw_scene(cv, s, sc, L, th, t, f, W, H, prev_pose, i)
                last_pose = pose
                frame = _camera(img, sc.get("camera", "static"), t, s["dur"], W, H)
                if show_captions:
                    _draw_caption(frame, s, t, L, th, W)
                if prev_frame is not None and t < FADE:
                    frame = Image.blend(prev_frame, frame, smooth(t / FADE))
                proc.stdin.write(frame.tobytes())
                done += 1
                if done % 15 == 0:
                    job.progress(30 + 68 * done / max(1, total_frames), f"Frame {done}/{total_frames}")
                if i == 0 and abs(t - min(1.6, s["dur"] / 2)) < 0.5 / fps:
                    frame.save(os.path.join(out_dir, "thumbnail.png"))
            prev_pose = last_pose
            prev_frame = frame
        proc.stdin.close()
        err = proc.stderr.read().decode(errors="ignore")
        if proc.wait() != 0:
            raise RuntimeError("ffmpeg failed: " + err[-800:])
    except BrokenPipeError:
        err = proc.stderr.read().decode(errors="ignore")
        raise RuntimeError("ffmpeg stopped: " + err[-800:])
    spec = end_clip_spec(plan, ROOT)
    if spec and not preview_seconds:  # meme / outro clip after the last scene
        job.progress(99, "Adding end clip")
        try:
            total += append_clip(out_mp4, spec, W, H, fps, log=job.log) or 0
        except RuntimeError as e:  # never lose the finished video over the extra clip
            job.log(f"End clip skipped: {str(e)[-300:]}")
    job.progress(100, "Done")
    job.log(f"Rendered {total:.1f}s video ({total_frames} frames) in {time.time() - t0:.0f}s -> {out_mp4}")
    return {"video": out_mp4, "duration": total, "voice_backends": sorted(used),
            "srt": os.path.join(out_dir, "captions.srt"), "thumbnail": os.path.join(out_dir, "thumbnail.png")}


# ---------------------------------------------------------------------------
def _girl_outfit(th):
    return dict(th.get("girl") or th.get("friend") or {})


def _outfit(th, friend=False, sc=None):
    """Costume for the narrator or the friend: the style's own, or a named character from the plan."""
    sc = sc or {}
    who = (sc.get("friend") or {}) if friend else sc
    o = dict(CHARACTERS.get(who.get("character")) or th.get("friend" if friend else "outfit") or {})
    if not friend:
        o.update({k: tuple(v) if isinstance(v, list) else v for k, v in (sc.get("outfit") or {}).items()})
    return o


def _title_colors(th, setting):
    dark_setting = th["mode"] != "line" and setting in ("night", "space", "stage")
    if th.get("title_color") and not (dark_setting and th["world"] in ("color", "color_soft", "edo", "egypt", "rome", "cave")):
        return th["title_color"], th.get("title_halo", th["bg"]), True
    if dark_setting:
        return (255, 255, 255), (20, 20, 30), True
    return th["ink"], th["bg"], th["mode"] != "line"


def _draw_scene(cv, s, sc, L, th, t, f, W, H, prev_pose, idx):
    ground, ch = L["ground"], L["char_h"]
    props = sc.get("props", [])
    target_x = L["char_x"]
    face_dir = 1 if (L["props"][0] >= target_x or sc.get("friend")) else -1
    if not props and not sc.get("friend"):
        face_dir = 1 if idx % 2 == 0 else -1

    # shadow helper
    def shadow(x):
        cv.ellipse((x - ch * 0.17, ground - ch * 0.02, x + ch * 0.17, ground + ch * 0.025), fill=mix(th["ink"], th["bg"], 0.88))

    # headline
    hl = (sc.get("headline") or "").strip()
    if hl:
        k = smooth((t - 0.15) / 0.35)
        if k > 0:
            if th.get("title_upper"):
                hl = hl.upper()
            size = L["headline_size"] * (0.85 if th.get("title_upper") else 1)
            fnt = font(_text_font(hl, th["hand_font"]), size)
            tw = cv.text_size(hl, fnt)[0]
            if tw > W * 0.9:  # long titles shrink to stay on screen
                fnt = font(_text_font(hl, th["hand_font"]), size * W * 0.9 / tw)
            hx, hy = L["headline"]
            col, halo, use_halo = _title_colors(th, sc.get("setting"))
            box = th.get("title_box")
            if box:  # C1: white text on a rounded label
                fnt = font(_text_font(hl, th["hand_font"]), L["headline_size"] * 0.62)
                tw, thh = cv.text_size(hl, fnt)
                pad, by = L["headline_size"] * 0.32, hy + (1 - k) * 18
                cv.rect((hx - tw / 2 - pad * 1.6, by - thh / 2 - pad, hx + tw / 2 + pad * 1.6, by + thh / 2 + pad),
                        fill=box + (int(240 * k),), radius=thh / 2 + pad)
                use_halo = False
            cv.text((hx, hy + (1 - k) * 18), hl, fnt, col + (int(255 * k),), anchor="mm",
                    stroke=L["headline_size"] * 0.06 if use_halo else 0, stroke_fill=halo + (int(255 * k),))
            tw, thh = cv.text_size(hl, fnt)
            u = smooth((t - 0.4) / 0.5)
            if u > 0 and not box:
                y = hy + thh * 0.62
                x0 = hx - tw / 2
                pts = [(x0 + tw * u * j / 8, y + 3 * math.sin(j * 1.7)) for j in range(9)]
                cv.line(pts, th["accents"][0], max(3, L["headline_size"] * 0.08))

    # props
    for k, (p, pos) in enumerate(zip(props, _prop_positions(len(props), L["props"], L["prop_s"]))):
        pt = s["prop_t"][k] if k < len(s.get("prop_t", [])) else 0.5 + k * 0.6
        draw_prop(cv, p, pos[0], pos[1], L["prop_s"] if len(props) == 1 else L["prop_s"] * 0.8, t - pt, th)

    # who does what right now (dialogue lines can change action and mood)
    act = _acting(s, sc, t)
    m, fr_now = act["main"], act["friend"]
    action, mood = m["action"], m["mood"]
    enter = sc.get("enter", "none")
    x = target_x
    sp_f = f - int(s["lead"] * s["fps"])

    def level(key):
        env = s.get(key)
        return float(env[sp_f]) if env is not None and 0 <= sp_f < len(env) else 0.0
    talk, ftalk = level("env"), level("env_friend")
    if sc.get("layout") == "call":
        return _draw_call(cv, s, th, t, W, H, act, talk, ftalk, idx)
    if sc.get("layout") == "standup":
        return _draw_standup(cv, s, sc, th, t, W, H, m, talk, idx)
    if sc.get("layout") == "trio":
        return _draw_trio(cv, s, sc, L, th, t, W, H)
    if sc["action"] == "ride":
        return _draw_ride(cv, sc, L, th, t, idx, W, mood, talk, fr_now, ftalk)
    if enter in ("left", "right") and t < ENTER_TIME:
        k = smooth(t / ENTER_TIME) * 0.6 + 0.4 * (t / ENTER_TIME)
        start = -ch * 0.4 if enter == "left" else W + ch * 0.4
        x = start + (target_x - start) * k
        pose = make_pose("walk", t, 0.0, idx)
        facing = 1 if enter == "left" else -1
    else:
        ta = t - (ENTER_TIME if enter in ("left", "right") else 0)
        pose = _acted_pose(m, ta if m["since"] <= 0 else t, talk, idx * 0.37)
        facing = face_dir
        if action in ("walk", "run"):
            # stroll across the frame during the scene
            span = W * (0.16 if action == "walk" else 0.3)
            x = target_x - span / 2 + span * clamp(ta / max(0.5, s["dur"] - 0.3))
            facing = 1
        src = None
        if enter in ("left", "right"):
            src = make_pose("walk", ENTER_TIME, 0, idx)
        elif prev_pose is not None:
            src = prev_pose
        if src is not None and ta < 0.35:
            pose = blend(src, pose, smooth(ta / 0.35))
    blink = ((t + idx * 1.3) % 3.7) < 0.12
    if action == "sit":
        _chair(cv, x, ground, ch, facing, th)
    shadow(x)
    face = {"mood": mood, "mouth_open": talk * 0.9 if talk > 0.12 else 0.0, "blink": blink}
    hands = draw_stickman(cv, x, ground, ch, pose, facing, th, face, _outfit(th, sc=sc))
    _held_item(cv, action, hands, ch, th, t)
    if action == "think" and t > 0.5 and not props:
        hx, hy = hands["head"]
        r = hands["head_r"]
        for j, (dx, dy, rr) in enumerate([(0.9, -1.1, 0.12), (1.3, -1.7, 0.2)]):
            if t > 0.5 + j * 0.2:
                cv.circle((hx + facing * r * dx * 1.2, hy + r * dy), r * rr * 1.4, fill=(255, 255, 255), outline=th["ink"], width=2)
        draw_prop(cv, "question", hx + facing * r * 2.6, hy - r * 2.6, r * 2.2, t - 0.9, th)

    # friend
    if sc.get("friend"):
        fx = L["friend_x"]
        fpose = _acted_pose(fr_now, t + 0.5 if fr_now["since"] <= 0 else t, ftalk, idx + 2.1)
        shadow(fx)
        fh = draw_stickman(cv, fx, ground, ch * 0.96, fpose, -1, th,
                           {"mood": fr_now["mood"], "mouth_open": ftalk * 0.9 if ftalk > 0.12 else 0.0,
                            "blink": ((t + 2.0) % 4.1) < 0.12}, _outfit(th, True, sc))
        _held_item(cv, fr_now["action"], fh, ch, th, t)
    return pose


def _acting(s, sc, t):
    """Action/mood of the main character and the friend at scene time t.

    Dialogue lines may set "action"/"mood" for their speaker and "other": {action, mood} for the
    listener; the change starts exactly when the line starts and lasts until another line changes it.
    A listener whose action is "talk" just stands, so only the speaker gestures.
    """
    fr = sc.get("friend") or {}
    st = {"main": {"action": sc["action"], "mood": sc.get("mood") or ACTION_MOOD.get(sc["action"], "neutral"),
                   "since": 0.0, "prev": sc["action"]},
          "friend": {"action": fr.get("action", "nod"), "mood": fr.get("mood") or ACTION_MOOD.get(fr.get("action"), "neutral"),
                     "since": 0.0, "prev": fr.get("action", "nod")}}
    if st["main"]["mood"] == "neutral" and sc["action"] in ACTION_MOOD:
        st["main"]["mood"] = ACTION_MOOD[sc["action"]]
    speaking = None
    for ln in s.get("lines") or []:
        if t < ln["t0"]:
            break
        who = ln["who"] if ln["who"] in st else None
        other = {"main": "friend", "friend": "main"}.get(who)
        for w, d in ((who, ln), (other, ln.get("other") or {})):
            if not w:
                continue
            allowed = sc["action"] != "ride" or (w == "friend" and d.get("action") in ("laugh", "slap"))  # the rider must steer
            if d.get("action") in ACTIONS and d["action"] != st[w]["action"] and allowed:
                st[w].update(prev=st[w]["action"], action=d["action"], since=ln["t0"])
            if d.get("mood") in MOODS:
                st[w]["mood"] = d["mood"]
        if t <= ln["t1"] + 0.3:
            speaking = who
    for w in st:
        if st[w]["action"] == "talk" and s.get("lines") and len(s["lines"]) > 1 and speaking != w:
            st[w]["action"] = "stand"
    return st


def _acted_pose(a, t, talk, seed):
    """Pose for an _acting() entry; blends from the previous action for 0.3 s after a change."""
    if a["since"] <= 0:
        return make_pose(a["action"], t, talk, seed)
    ta = t - a["since"]
    pose = make_pose(a["action"], ta, talk, seed)
    if ta < 0.3:
        pose = blend(make_pose(a["prev"], t, 0.0, seed), pose, smooth(ta / 0.3))
    return pose


def _since_slap(a, t):
    """Seconds since this character's last hit, or None before the first one."""
    ta = t - a["since"]
    return ta % SLAP_PERIOD if a["action"] == "slap" and ta >= SLAP_PERIOD else None


def _slap_hits(s, sc, fps):
    """Scene times at which the friend's hand lands on the rider."""
    if sc["action"] != "ride" or not sc.get("friend"):
        return []
    hits, last = [], None
    for f in range(int(s["dur"] * fps)):
        t = f / fps
        a = _acting(s, sc, t)["friend"]
        n = (a["since"], int((t - a["since"]) / SLAP_PERIOD)) if _since_slap(a, t) is not None else None
        if n and n != last:
            hits.append(t)
        last = n
    return hits


def _ride_speed(W):
    return W * 0.9  # road speed in design px/s


def _ride_strip(bg):
    """Motion-blurred background tiled as bg | mirrored bg | bg, for seamless scrolling."""
    w, h = bg.size
    blurred = bg.resize((max(1, w // 8), h), Image.BILINEAR).resize((w, h), Image.BILINEAR)
    strip = Image.new("RGB", (w * 3, h))
    strip.paste(blurred, (0, 0))
    strip.paste(blurred.transpose(Image.FLIP_LEFT_RIGHT), (w, 0))
    strip.paste(blurred, (w * 2, 0))
    return strip


def _scroll(strip, t, W):
    w = strip.width // 3
    off = int(t * _ride_speed(W) * SS) % (2 * w)
    return strip.crop((off, 0, off + w, strip.height))


def _seat(pose, Hr, facing, seat, th, outfit):
    """ground/x to pass to draw_stickman so the hip sits exactly on `seat`."""
    from .stickman import solve
    j = solve(pose, Hr, facing)
    drop = max(j["footA"][1], j["footB"][1])
    extra = 0.035 * Hr if outfit.get("body") == "toon" else 0.0
    return seat[0], seat[1] + drop + pose["lift"] + extra


def _draw_ride(cv, sc, L, th, t, idx, W, mood, talk, fr, ftalk=0.0):
    """Narrator rides a motorbike to the right (friend on the back); the background scrolls in render()."""
    from .props import draw_bike, draw_scooter
    from .stickman import reach_arms
    ground, ch = L["ground"], L["char_h"]
    friend = sc.get("friend")
    hit = _since_slap(fr, t) if friend else None
    x = W * (0.5 if L["portrait"] else 0.42)
    speed = _ride_speed(W)
    for k in range(6):  # speed lines
        yy = ground - ch * (0.15 + 0.17 * k)
        sx = W - ((t * speed * 1.6 + k * 397) % (W * 1.6))
        cv.line([(sx, yy), (sx + W * 0.12, yy)], (255, 255, 255, 90), max(2, ch * 0.008))
    cv.ellipse((x - ch * 0.7, ground - ch * 0.025, x + ch * 0.7, ground + ch * 0.03), fill=mix(th["ink"], th["bg"], 0.8))
    bike = (draw_scooter if sc.get("vehicle") == "scooter" else draw_bike)(cv, x, ground, ch, t, th, speed)
    Hr = ch * 0.92
    blink = ((t + idx * 1.3) % 3.7) < 0.12

    rider = make_pose("ride", t, talk, idx * 0.37)
    rider["head"] -= 6 * ftalk          # the rider tilts his head back to listen
    if hit is not None:                 # a slap jolts him forward
        rider["lean"] += 7 * math.exp(-hit * 14)
        rider["head"] += 8 * math.exp(-hit * 14)
    rx, rg = _seat(rider, Hr, 1, bike["seat"], th, _outfit(th, sc=sc))
    g = bike["grip"]
    reach_arms(rider, Hr, 1, (g[0] - bike["seat"][0], g[1] - bike["seat"][1]),
               (g[0] - bike["seat"][0] - ch * 0.02, g[1] - bike["seat"][1] + ch * 0.01))
    if friend:
        from .stickman import solve
        sh = solve(rider, Hr, 1)["shoulder"]
        on_rider = (bike["seat"][0] + sh[0] - bike["pillion"][0], bike["seat"][1] + sh[1] - bike["pillion"][1])
        back = make_pose("ride_back", t + 0.3, ftalk, idx + 2.1)
        back["lean"] += 8 * ftalk          # leans forward to talk into the rider's ear
        if fr["mood"] == "laugh":
            shake = math.sin(2 * math.pi * t / 0.28)
            back["lean"] += 3 * shake
            back["head"] += -10 + 5 * shake
        hand = (on_rider[0] - ch * 0.02, on_rider[1])
        if fr["action"] == "slap":          # one hand swings up and lands on the rider's back
            k = slap_lift(t - fr["since"])
            hand = (on_rider[0] - ch * (0.05 + 0.02 * k), on_rider[1] + ch * (0.05 - 0.27 * k))
        reach_arms(back, Hr * 0.97, 1, hand, (on_rider[0] - ch * 0.06, on_rider[1] + ch * 0.03))
        fx, fg = _seat(back, Hr * 0.97, 1, bike["pillion"], th, _outfit(th, True, sc))

        def draw_back():
            draw_stickman(cv, fx, fg, Hr * 0.97, back, 1, th,
                          {"mood": fr["mood"], "mouth_open": ftalk * 0.9 if ftalk > 0.12 else 0.0, "blink": ((t + 2.0) % 4.1) < 0.12},
                          _outfit(th, True, sc))
    slapping = friend and fr["action"] == "slap"  # drawn over the rider, so the swinging hand stays visible
    if friend and not slapping:
        draw_back()
    face = {"mood": mood, "mouth_open": talk * 0.9 if talk > 0.12 else 0.0, "blink": blink}
    draw_stickman(cv, rx, rg, Hr, rider, 1, th, face, _outfit(th, sc=sc))
    if slapping:
        draw_back()
    if hit is not None and hit < 0.1:   # impact star where the hand lands
        cx, cy = bike["pillion"][0] + on_rider[0] - ch * 0.05, bike["pillion"][1] + on_rider[1] + ch * 0.04
        pts = [(cx + math.cos(i * math.pi / 5) * ch * (0.075 if i % 2 else 0.035),
                cy + math.sin(i * math.pi / 5) * ch * (0.075 if i % 2 else 0.035)) for i in range(10)]
        cv.poly(pts, fill=(255, 232, 110), outline=th["ink"], width=2)
    return rider


def _call_person(cv, box, outfit, facing, a, lvl, t, seed, th, hang=0.0):
    """Waist-up character in a call panel with the phone at the ear; hang > 0 lowers it."""
    from .stickman import reach_arms, solve
    x0, y0, x1, y1 = box
    ph = y1 - y0
    Hc = ph * 1.12
    r = 0.15 * Hc
    x, hip_y = (x0 + x1) / 2 - facing * (x1 - x0) * 0.03, y0 + ph * 0.87
    ta = t - a["since"]
    pose = make_pose("stand", t, lvl, seed)
    pose["lean"] += 2 * math.sin(t * 1.4 + seed)
    pose["head"] += 4 * lvl * math.sin(t * 9 + seed)
    gesture = clamp(lvl * 1.6) * (0.65 + 0.35 * math.sin(t * 7 + seed))
    if a["mood"] == "angry":                       # shouting: leans in and jabs with the head and hand
        pose["lean"] += 7 + 5 * lvl * math.sin(t * 16)
        pose["head"] += 8 * lvl * math.sin(t * 13)
        gesture = min(1.0, gesture * 1.5)
    elif a["mood"] == "laugh":
        pose["head"] += -8 + 5 * math.sin(2 * math.pi * t / 0.28)
    if a["action"] == "surprised":                 # jolts back with a hop
        pose["lean"] += -9 + 7 * math.exp(-ta * 4) * math.sin(ta * 25)
        hip_y -= ph * 0.06 * max(0.0, math.sin(min(ta, 0.4) / 0.4 * math.pi))
        gesture = 1.0
    j = solve(pose, Hc, facing)
    n, sh = j["neck"], j["shoulder"]
    ear = (n[0] - facing * r * 1.02, n[1] - r * 0.8)
    low = (n[0] + facing * r * 0.75, n[1] + r * 1.7)
    free = (sh[0] + facing * Hc * 0.16, sh[1] + Hc * (0.3 - 0.4 * gesture))
    reach_arms(pose, Hc, facing, (lerp(ear[0], low[0], hang), lerp(ear[1], low[1], hang)), free)
    gx, gy = _seat(pose, Hc, facing, (x, hip_y), th, outfit)
    hands = draw_stickman(cv, gx, gy, Hc, pose, facing, th,
                          {"mood": a["mood"], "mouth_open": lvl * 0.9 if lvl > 0.12 else 0.0,
                           "blink": ((t + seed) % 3.7) < 0.12}, outfit)
    hx, hy = hands["handA"]                        # phone in the hand, over the hair
    pw, phh = r * 0.27, r * 0.62
    cv.rect((hx - pw, hy - phh, hx + pw, hy + phh), fill=(40, 42, 52), outline=th["ink"], width=max(2, r * 0.03), radius=r * 0.08)
    cv.rect((hx - pw * 0.72, hy - phh * 0.82, hx + pw * 0.72, hy + phh * 0.82),
            fill=mix((40, 42, 52), (235, 64, 64), hang) if hang else (70, 150, 210))
    cv.circle((hx - facing * r * 0.04, hy + phh * 0.5), r * 0.26, fill=outfit.get("skin", th["head"]), outline=th["ink"], width=max(2, r * 0.03))
    return pose, hands


def _draw_call(cv, s, th, t, W, H, act, talk, ftalk, idx):
    """Phone call: each character stays in their own room, with a divider between them."""
    from .scenes import call_panels
    boxes = call_panels(W, H)
    end = s.get("call_end_t")
    hang = smooth((t - end) / 0.35) if end is not None else 0.0
    x0, y0, x1, y1 = boxes[0]
    for ln in s.get("lines") or []:                # hearts float up behind him on a line marked "hearts"
        if ln.get("hearts") and ln["t0"] <= t:
            for k in range(7):
                u = ((t - ln["t0"]) * 0.4 + k / 7) % 1
                hx, hy, hr = x0 + (x1 - x0) * (0.08 + k * 0.14) + 14 * math.sin(t * 2 + k), y1 - (y1 - y0) * u, (x1 - x0) * (0.03 + 0.012 * (k % 3))
                for dx in (-0.5, 0.5):
                    cv.circle((hx + dx * hr, hy - hr * 0.3), hr * 0.58, fill=(232, 44, 78))
                cv.poly([(hx - hr * 1.05, hy - hr * 0.1), (hx + hr * 1.05, hy - hr * 0.1), (hx, hy + hr * 1.15)], fill=(232, 44, 78))
    pose, _ = _call_person(cv, boxes[0], _outfit(th, sc=s["sc"]), 1, act["main"], talk, t, idx * 0.37, th, hang)
    box = tuple(int(v * SS) for v in boxes[1])     # her room covers whatever reached past his panel
    cv.img.paste(s["bg"].crop(box), box[:2])
    _call_person(cv, boxes[1], _girl_outfit(th), -1, act["friend"], ftalk, t, idx + 2.1, th)
    lw = max(6, min(W, H) * 0.012)
    if H > W * 1.15:
        cv.rect((0, boxes[1][1] - lw / 2, W, boxes[1][1] + lw / 2), fill=th["ink"])
    else:
        cv.rect((boxes[1][0] - lw / 2, 0, boxes[1][0] + lw / 2, H), fill=th["ink"])
    k = smooth((t - (end or 0) - 0.3) / 0.25) if end is not None else 0.0
    if k > 0:
        fnt = font(th["hand_font"], min(W, H) * 0.052)
        tw, thh = cv.text_size("Call Ended", fnt)
        cx, cy = (boxes[1][0] + (W / 2 if H > W * 1.15 else 0), boxes[1][1] + (0 if H > W * 1.15 else H / 2))
        cv.rect((cx - tw * 0.72, cy - thh * 1.1, cx + tw * 0.72, cy + thh * 1.1), fill=(200, 40, 50, int(240 * k)), radius=thh)
        cv.text((cx, cy), "Call Ended", fnt, (255, 255, 255, int(255 * k)), anchor="mm")
    return pose


def _standup_bg(sc, W, H, th):
    if sc.get("backdrop") == "curtain":
        return draw_curtain_stage(W, H, th)
    if sc.get("backdrop") == "outdoor":
        return draw_background("park", W, H, standup_floor(H), th, seed=3)
    return draw_standup_stage(W, H, th)


def _free_hand(action, sh, Hc, f, t, lvl):
    """Where the hand without the mic goes for each action (the side away from the mic)."""
    if action == "wave":
        return (sh[0] - f * Hc * (0.27 + 0.03 * math.sin(t * 8)), sh[1] - Hc * 0.1)
    if action == "think":                          # deadpan setup: hand on the hip
        return (sh[0] - f * Hc * 0.17, sh[1] + Hc * 0.27)
    if action == "surprised":
        return (sh[0] - f * Hc * 0.29, sh[1] - Hc * 0.09)
    if action == "shrug":
        return (sh[0] - f * Hc * 0.25, sh[1] - Hc * 0.02)
    if action == "laugh":                          # slaps his thigh
        return (sh[0] - f * Hc * 0.19, sh[1] + Hc * (0.29 + 0.03 * math.sin(t * 14)))
    return (sh[0] - f * Hc * 0.24, sh[1] + Hc * (0.24 - 0.2 * clamp(lvl * 1.6) * (0.65 + 0.35 * math.sin(t * 7))))


def _audience(cv, s, t, W, H):
    """Two rows of dark heads in front of the stage; they rock while a laugh lasts."""
    joy = max([clamp((t - ln["t1"]) / 0.15) * clamp((ln["t1"] + audio.CROWD_LAUGH - t) / 0.4)
               for ln in s.get("lines") or [] if ln.get("crowd")] + [0.0])
    m = min(W, H)
    for row, (y, r, col, rim) in enumerate(((H * 0.875, m * 0.075, (40, 24, 28), (92, 58, 46)),
                                            (H * 0.955, m * 0.105, (16, 10, 13), (58, 36, 32)))):
        step = r * 2.5
        for k in range(int(W / step) + 2):
            x = (k + (0.5 if row else 0.0)) * step - step * 0.25
            ph = k * 2.3 + row
            hy = y + r * 0.1 * math.sin(k * 1.9) - joy * r * (0.14 + 0.2 * abs(math.sin(t * 11 + ph)))
            hx = x + joy * r * 0.1 * math.sin(t * 7 + ph)
            cv.ellipse((hx - r * 1.3, hy + r * 0.72, hx + r * 1.3, hy + r * 3.4), fill=col)
            cv.circle((hx, hy), r + 2, fill=rim)
            cv.circle((hx, hy + 2), r, fill=col)


def _draw_standup(cv, s, sc, th, t, W, H, a, lvl, idx):
    """Standup: a big comedian on stage, mic at the mouth, the audience in front of him."""
    from .stickman import reach_arms, solve
    portrait = H > W * 1.15
    outfit = _outfit(th, sc=sc)
    Hc = H * (0.58 if portrait else 0.66)
    r = 0.15 * Hc * outfit.get("head_scale", 1)
    f = 1 if idx % 2 == 0 else -1
    on_stand, boom = sc.get("mic") == "stand", sc.get("mic") == "boom"
    x = W * 0.5 - f * r * 0.35 + (0 if on_stand or boom else W * 0.02 * math.sin(t * 0.7 + idx))
    ta, seed = t - a["since"], idx * 0.37
    pose = make_pose("stand", t, lvl, seed)
    pose["lean"] += 2 * math.sin(t * 1.3 + seed)
    pose["head"] += 4 * lvl * math.sin(t * 9 + seed)
    if a["action"] == "surprised":                 # jolts back with a hop
        pose["lean"] += -8 + 6 * math.exp(-ta * 4) * math.sin(ta * 25)
        pose["lift"] += Hc * 0.035 * max(0.0, math.sin(min(ta, 0.4) / 0.4 * math.pi))
    elif a["action"] == "laugh":
        pose["lean"] += 5
        pose["head"] += -7 + 5 * math.sin(2 * math.pi * t / 0.28)
    elif a["action"] == "shrug":
        pose["head"] += 8
    j = solve(pose, Hc, f)
    n, sh = j["neck"], j["shoulder"]
    grip = (n[0] + f * r * 1.26, n[1] + r * 0.83)  # the mic stands up from here to just under the mouth
    if boom:                                       # the stand holds the mic: this hand hangs and bobs as he talks
        grip = (sh[0] + f * Hc * 0.19, sh[1] + Hc * (0.26 - 0.06 * clamp(lvl * 1.6) * (0.6 + 0.4 * math.sin(t * 6))))
    free = _free_hand(a["action"], sh, Hc, f, t, lvl)
    if ta < 0.25 and a["prev"] != a["action"]:     # swings over from the last gesture
        was = _free_hand(a["prev"], sh, Hc, f, t, lvl)
        free = (lerp(was[0], free[0], smooth(ta / 0.25)), lerp(was[1], free[1], smooth(ta / 0.25)))
    reach_arms(pose, Hc, f, grip, free)
    floor = standup_floor(H) + Hc * 0.05
    hands = draw_stickman(cv, x, floor, Hc, pose, f, th,
                          {"mood": a["mood"], "mouth_open": lvl * 0.9 if lvl > 0.12 else 0.0,
                           "blink": ((t + seed) % 3.7) < 0.12}, outfit)
    hx, hy = hands["handA"]
    gx, gy = hx - f * r * 0.34, hy - r * 0.85
    ink, lw = th["ink"], max(2, r * 0.03)
    if boom:                                       # stand in front of him, the arm angled up to his mouth
        (cx, cy), hr = hands["head"], hands["head_r"]
        gx, gy = cx + f * hr * 0.72, cy + hr * 0.82
        hx, hy = gx + f * hr * 0.42, gy + hr * 0.42
        pole = x + f * hr * 0.5
        top = (pole, hy + hr * 0.55)
        for col, w in ((ink, r * 0.11), ((92, 94, 102), r * 0.06)):
            cv.line([(pole, floor), top, (hx, hy)], col, w)
        cv.ellipse((pole - r * 0.5, floor - r * 0.09, pole + r * 0.5, floor + r * 0.11), fill=(54, 56, 62), outline=ink, width=lw)
    if on_stand:                                   # the stand goes down from his hand to the boards
        cv.line([(hx, hy), (hx, floor)], ink, r * 0.12)
        cv.line([(hx, hy), (hx, floor)], (176, 180, 188), r * 0.06)
        cv.ellipse((hx - r * 0.55, floor - r * 0.1, hx + r * 0.55, floor + r * 0.1), fill=(70, 72, 80), outline=ink, width=lw)
    d = math.hypot(hx - gx, hy - gy)
    nx, ny = (hy - gy) / d, (gx - hx) / d
    tail = (hx + (hx - gx) * 0.3, hy + (hy - gy) * 0.3)
    cv.poly([(gx + nx * r * 0.13, gy + ny * r * 0.13), (gx - nx * r * 0.13, gy - ny * r * 0.13),
             (tail[0] - nx * r * 0.07, tail[1] - ny * r * 0.07), (tail[0] + nx * r * 0.07, tail[1] + ny * r * 0.07)],
            fill=(34, 34, 40), outline=ink, width=lw)
    cv.circle((gx, gy), r * 0.24, fill=(166, 170, 178), outline=ink, width=lw)
    cv.arc((gx, gy), r * 0.14, 200, 290, (232, 234, 238), lw)
    if not boom:
        cv.circle((hx, hy), r * 0.24, fill=outfit.get("skin", th["head"]), outline=ink, width=lw)
    if sc.get("audience") is not False:
        _audience(cv, s, t, W, H)
    return pose


TRIO_MOODS = {"ring": ("happy", "neutral", "happy"), "grab": ("happy", "surprised", "happy"),  # phone friend, victim, holder
              "struggle": ("laugh", "surprised", "laugh"), "glare": ("laugh", "angry", "laugh"), "bite": ("laugh", "angry", "laugh")}


def _trio_size(H, L):
    Hc = H * (0.46 if L["portrait"] else 0.62)
    return Hc, L["ground"] - Hc * 0.225


def _trio_bg(W, H, L, th):
    """The room with a bed across it; the three friends sit on its edge."""
    img = draw_background("room", W, H, L["ground"], th, seed=0)
    cv = Canvas(img)
    Hc, seat = _trio_size(H, L)
    ink, lw = th["ink"], max(2, Hc * 0.008)
    cv.rect((-20, seat - Hc * 0.3, W + 20, seat), fill=(108, 72, 52), outline=ink, width=lw)                 # headboard
    cv.rect((-20, seat - Hc * 0.05, W + 20, L["ground"] - Hc * 0.03), fill=(74, 104, 170), outline=ink, width=lw)
    cv.rect((-20, seat - Hc * 0.05, W + 20, seat + Hc * 0.04), fill=(236, 232, 222), outline=ink, width=lw)
    for k in range(9):
        x = W * (k + 0.5) / 9
        cv.line([(x, seat + Hc * 0.04), (x, L["ground"] - Hc * 0.03)], (58, 86, 148), Hc * 0.012)
    return img


def _bite_time(s):
    """When the hand gets bitten: as the friend holding him starts to yell."""
    return next((ln["t0"] for ln in s.get("lines") or [] if ln["who"] == "main"), 0.0)


def _trio_phone(cv, c, Hc, th, ringing, voice, t):
    """The phone; rings pulse while it rings, sound waves while she talks on speaker."""
    pw, ph = Hc * 0.05, Hc * 0.095
    for k in range(3):
        if ringing or voice:
            u = (t * (1.6 if ringing else 2.4) + k / 3) % 1
            col = (255, 150, 170) if ringing else (255, 255, 255)
            cv.arc(c, ph * (1.2 + 1.3 * u), 215, 325, col + (int(230 * (1 - u)),), Hc * 0.01)
    cv.rect((c[0] - pw, c[1] - ph, c[0] + pw, c[1] + ph), fill=(34, 36, 44), outline=th["ink"], width=max(2, Hc * 0.007), radius=Hc * 0.014)
    cv.rect((c[0] - pw * 0.74, c[1] - ph * 0.84, c[0] + pw * 0.74, c[1] + ph * 0.84), fill=(240, 92, 130) if ringing else (110, 196, 236))
    if ringing:
        cv.circle((c[0], c[1] + ph * 0.45), pw * 0.34, fill=(70, 200, 110))


def _draw_trio(cv, s, sc, L, th, t, W, H):
    """Three friends on a bed: one has the phone on speaker, one holds the victim's mouth shut."""
    from .stickman import reach_arms, solve
    beat = sc.get("beat", "ring")
    Hc, seat = _trio_size(H, L)
    r = 0.15 * Hc
    joker, victim, holder = (CHARACTERS[k] for k in ("friend_red", "friend_blue", "friend_yellow"))
    moods = list(TRIO_MOODS[beat])
    lines = s.get("lines") or []

    def speaking(who):
        return any(ln["who"] == who and ln["t0"] <= t <= ln["t1"] for ln in lines)

    def face(mood, who, seed, shut=False):
        talk = 0.0 if shut or not speaking(who) else 0.5 + 0.4 * math.sin(t * 23)
        return {"mood": mood, "mouth_open": talk, "blink": ((t + seed) % 3.3) < 0.12}

    tb = _bite_time(s) if beat == "bite" else None
    bit = smooth((t - tb) / 0.18) if tb is not None and t >= tb else 0.0
    hold = 0.0 if beat == "ring" else smooth(t / 0.4) if beat == "grab" else 1.0
    if bit > 0:
        moods[2] = "angry"
    laugh = 2 * math.pi * t / 0.3
    xj, xv, xh = W * 0.17, W * (0.47 - 0.04 * bit), W * (lerp(0.8, 0.72, hold) + 0.12 * bit)
    rest = (-0.17 * Hc, -0.03 * Hc)                # hands on the knees, for f = -1

    pj, pv, ph = make_pose("sit", t, 0.0, 0.3), make_pose("sit", t, 0.0, 1.1), make_pose("sit", t, 0.0, 2.3)
    # the victim first: everyone else aims at him
    if beat == "struggle" or beat == "grab" or (beat == "bite" and bit == 0):
        k = hold if beat == "grab" else 1.0
        pv["lean"] += k * 10 * math.sin(t * 8)
        pv["head"] += k * 22 * math.sin(t * 13)
        pv["lA_k"] += k * 20 * math.sin(t * 12)
        pv["lB_k"] -= k * 20 * math.sin(t * 12 + 1)
    pv["lean"] += 12 * bit
    jv = solve(pv, Hc, -1)
    hd = math.radians(pv["lean"] * 0.6 + pv["head"] * 0.4)
    hc = (xv + jv["neck"][0] - math.sin(hd) * r * 0.95, seat + jv["neck"][1] - math.cos(hd) * r * 0.95)
    mouth = (hc[0] - r * 0.2, hc[1] + r * 0.6)

    for p, mood, ph_ in ((pj, moods[0], 0.0), (ph, moods[2], 1.4)):
        if mood == "laugh":
            p["lean"] += 3 * math.sin(laugh + ph_)
            p["head"] += -8 + 5 * math.sin(laugh + ph_)
    # the friend behind him
    ph["lean"] += 18 * hold - 26 * bit
    jh = solve(ph, Hc, -1)
    target = (lerp(xh + rest[0], mouth[0] - r * 0.05, hold), lerp(seat + rest[1], mouth[1], hold))
    if bit > 0:                                    # shakes the bitten hand
        sore = (xh + jh["shoulder"][0] - Hc * 0.2, seat + jh["shoulder"][1] + Hc * (0.02 + 0.04 * math.sin(t * 30)))
        target = (lerp(target[0], sore[0], bit), lerp(target[1], sore[1], bit))
    reach_arms(ph, Hc, -1, (target[0] - xh, target[1] - seat),
               (xv + jv["shoulder"][0] - xh, seat + jv["shoulder"][1] - seat + Hc * 0.05) if hold else rest)
    # the friend with the phone
    reach = smooth((t - s["dur"] * 0.55) / 0.5) if beat == "ring" else 1.0
    pj["lean"] += 12 * reach if beat == "ring" else 2 - 8 * bit
    jj = solve(pj, Hc, 1)
    bed_spot = (W * 0.33, seat + Hc * 0.0)
    if beat == "ring":
        phone = (lerp(bed_spot[0], xj + jj["shoulder"][0] + Hc * 0.24, smooth((t - s["dur"] * 0.8) / 0.2)),
                 lerp(bed_spot[1], seat + jj["shoulder"][1] + Hc * 0.08, smooth((t - s["dur"] * 0.8) / 0.2)))
    else:                                          # pulled away out of the victim's reach once he is free
        phone = (xj + jj["shoulder"][0] + Hc * lerp(0.24, -0.16, bit), seat + jj["shoulder"][1] + Hc * lerp(0.08, -0.2, bit))
    hand = (lerp(-rest[0], phone[0] - xj, reach), lerp(rest[1], phone[1] - seat, reach))
    reach_arms(pj, Hc, 1, hand, (-rest[0], rest[1]))
    # the victim's arms, now that the hand on his mouth is placed
    if beat == "glare":
        va, vb = rest, (rest[0] * 0.8, rest[1])
    elif beat == "ring":
        va, vb = rest, (rest[0] * 0.8, rest[1])
    else:
        va = (target[0] - xv + Hc * 0.02, target[1] - seat + Hc * 0.1)
        vb = (Hc * 0.1, jv["shoulder"][1] + Hc * (0.27 + 0.03 * math.sin(t * 15)))
    if bit > 0:
        va = (lerp(va[0], phone[0] - xv + Hc * 0.05, bit), lerp(va[1], phone[1] - seat + Hc * 0.03, bit))
    reach_arms(pv, Hc, -1, va, vb)

    ringing = beat == "ring" and t < s["dur"] * 0.8
    for x, p, f, o, mood, who, seed in ((xh, ph, -1, holder, moods[2], "main", 0.7), (xj, pj, 1, joker, moods[0], "narrator", 1.9)):
        gx, gy = _seat(p, Hc, f, (x, seat), th, o)
        draw_stickman(cv, gx, gy, Hc, p, f, th, face(mood, who, seed), o)
    gx, gy = _seat(pv, Hc, -1, (xv, seat), th, victim)
    shut = hold > 0.5 and bit == 0
    draw_stickman(cv, gx, gy, Hc, pv, -1, th, face(moods[1], "none", 3.1, shut), victim)
    if hold > 0 and bit < 0.5:                     # his forearm and hand go over the victim's face
        j = solve(ph, Hc, -1)
        ink = th["ink"]
        ol, w, skin = 0.012 * Hc, 0.056 * Hc, holder["skin"]
        el, hd_ = (xh + j["elbowA"][0], seat + j["elbowA"][1]), (xh + j["handA"][0], seat + j["handA"][1])
        cv.line([el, hd_], ink, w + 2 * ol)
        cv.line([el, hd_], skin, w)
        cv.circle(hd_, 0.062 * Hc + ol, fill=ink)
        cv.circle(hd_, 0.062 * Hc, fill=skin)
        for k in (-1, 0, 1):                       # fingers
            cv.line([(hd_[0] - Hc * 0.015, hd_[1] + k * Hc * 0.024), (hd_[0] - Hc * 0.05, hd_[1] + k * Hc * 0.026)], ink, ol * 0.6)
    if tb is not None and 0 <= t - tb < 0.12:      # impact star on the bite
        pts = [(mouth[0] + math.cos(i * math.pi / 5) * Hc * (0.1 if i % 2 else 0.05),
                mouth[1] + math.sin(i * math.pi / 5) * Hc * (0.1 if i % 2 else 0.05)) for i in range(10)]
        cv.poly(pts, fill=(255, 232, 110), outline=th["ink"], width=2)
    _trio_phone(cv, phone, Hc, th, ringing, speaking("friend"), t)
    if not (beat == "ring" and reach < 1):
        cv.circle((phone[0] - Hc * 0.04, phone[1] + Hc * 0.05), Hc * 0.03, fill=joker["skin"], outline=th["ink"], width=max(2, Hc * 0.007))
    return pj


def _chair(cv, x, ground, ch, facing, th):
    seat_y = ground - ch * 0.215 - ch * 0.01
    ink, lw = th["ink"], max(2, ch * 0.03)
    col = mix(th["ink"], th["bg"], 0.6) if th["mode"] == "line" else (150, 100, 65)
    x0, x1 = x - facing * ch * 0.12, x + facing * ch * 0.16
    cv.line([(x0, seat_y), (x1, seat_y)], col, lw * 1.2)
    cv.line([(x0, seat_y), (x0, ground)], col, lw)
    cv.line([(x1, seat_y), (x1, ground)], col, lw)
    cv.line([(x0, seat_y), (x0 - facing * ch * 0.02, seat_y - ch * 0.3)], col, lw)


def _held_item(cv, action, hands, ch, th, t):
    if action == "phone":
        hx, hy = hands["handA"]
        cv.rect((hx - ch * 0.03, hy - ch * 0.09, hx + ch * 0.03, hy + ch * 0.02), fill=(40, 40, 46), outline=th["ink"], width=2, radius=ch * 0.01)
        glow = 0.6 + 0.4 * abs(math.sin(t * 3))
        cv.rect((hx - ch * 0.022, hy - ch * 0.08, hx + ch * 0.022, hy + ch * 0.008), fill=mix((40, 40, 46), th["accents"][1], glow))
    elif action == "read":
        (ax, ay), (bx, by) = hands["handA"], hands["handB"]
        cx, cy = (ax + bx) / 2, (ay + by) / 2 - ch * 0.03
        cv.poly([(cx, cy - ch * 0.06), (cx - ch * 0.1, cy - ch * 0.08), (cx - ch * 0.1, cy + ch * 0.05), (cx, cy + ch * 0.07)],
                fill=(255, 255, 255), outline=th["ink"], width=2)
        cv.poly([(cx, cy - ch * 0.06), (cx + ch * 0.1, cy - ch * 0.08), (cx + ch * 0.1, cy + ch * 0.05), (cx, cy + ch * 0.07)],
                fill=th["accents"][0], outline=th["ink"], width=2)
    elif action == "write":
        hx, hy = hands["handA"]
        cv.line([(hx, hy), (hx + ch * 0.03, hy - ch * 0.07)], th["accents"][1], max(3, ch * 0.025))


def _camera(img, cam, t, dur, W, H):
    u = smooth(t / max(0.1, dur))
    z, px = 1.0, 0.0
    if cam == "zoom_in":
        z = 1.0 + 0.07 * u
    elif cam == "zoom_out":
        z = 1.07 - 0.07 * u
    elif cam == "pan_left":
        z, px = 1.06, W * 0.025 * (1 - 2 * u)
    elif cam == "pan_right":
        z, px = 1.06, -W * 0.025 * (1 - 2 * u)
    elif cam == "punch":
        z = 1.0 + 0.1 * math.exp(-t * 5)
    cw, chh = W / z, H / z
    cx = W / 2 + px
    cy = H / 2
    box = (max(0, cx - cw / 2) * SS, max(0, cy - chh / 2) * SS, min(W, cx + cw / 2) * SS, min(H, cy + chh / 2) * SS)
    return img.resize((W, H), Image.BICUBIC, box=box, reducing_gap=2.0)


def _text_font(text, default):
    """Pick a font that can show the script used in `text` (Windows system fonts)."""
    if any(0x0900 <= ord(c) <= 0x0DFF for c in text):      # Indic scripts
        return "Nirmala.ttf"
    if any(0x3040 <= ord(c) <= 0x9FFF or 0xAC00 <= ord(c) <= 0xD7AF for c in text):  # CJK / Hangul
        return "msyh.ttc"
    if any(0x0600 <= ord(c) <= 0x06FF for c in text):
        return "segoeui.ttf"
    return default


def _draw_caption(frame, s, t, L, th, W):
    cur, ci = None, 0
    for k, c in enumerate(s["chunks"]):
        if c[1] - 0.05 <= t:
            cur, ci = c, k
    if cur is None or t > s["chunks"][-1][2] + 0.6:
        return
    idxs, c0, c1 = cur
    d = ImageDraw.Draw(frame, "RGBA")
    words = [s["words"][i] for i in idxs]
    if th.get("caption_upper"):
        words = [w.upper() for w in words]
    fname = _text_font(" ".join(words), "NotoSans.ttf")
    fnt = font(fname, L["caption_size"] / SS)
    space = d.textlength(" ", font=fnt)
    widths = [d.textlength(w, font=fnt) for w in words]
    total_w = sum(widths) + space * (len(words) - 1)
    max_w = W * 0.9
    scale = 1.0
    if total_w > max_w:
        scale = max_w / total_w
        fnt = font(fname, L["caption_size"] * scale / SS)
        space = d.textlength(" ", font=fnt)
        widths = [d.textlength(w, font=fnt) for w in words]
        total_w = sum(widths) + space * (len(words) - 1)
    x = W / 2 - total_w / 2
    y = L["caption_y"]
    pad = L["caption_size"] * 0.35
    dark_bg = sum(th["bg"]) < 200
    box = th.get("caption_box")
    if box:
        d.rounded_rectangle((x - pad * 1.4, y - L["caption_size"] * scale * 0.75, x + total_w + pad * 1.4, y + L["caption_size"] * scale * 0.75),
                            radius=pad, fill=box + (225,))
    hi = th.get("caption_hi") or (th["accents"][0] if not box or sum(box) > 400 else th["accents"][2])
    if (s.get("chunk_who") or [None] * (ci + 1))[ci] == "friend":  # the friend's words light up in another colour
        hi = th.get("caption_hi_friend") or ((110, 215, 255) if box and sum(box) < 400 else th["accents"][1])
    for i, w, wd in zip(idxs, words, widths):
        on = s["times"][i][0] <= t
        col = hi if (s["times"][i][0] <= t < s["times"][i][1] + 0.05) else th["caption_ink"]
        if not on:
            col = mix(th["caption_ink"], box or th["bg"], 0.35)
        stroke = 0 if box else max(2, int(L["caption_size"] * (0.12 if th.get("caption_upper") else 0.08)))
        stroke_fill = (0, 0, 0) if dark_bg else (255, 255, 255)
        d.text((x, y), w, font=fnt, fill=col, anchor="lm", stroke_width=stroke, stroke_fill=stroke_fill)
        x += wd + space


def _fmt(t):
    ms = int(round(t * 1000))
    return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"


def _write_srt(path, scenes, starts):
    n = 1
    with open(path, "w", encoding="utf-8") as f:
        for s, st in zip(scenes, starts):
            for idxs, a, b in s["chunks"]:
                f.write(f"{n}\n{_fmt(st + a)} --> {_fmt(st + b)}\n{' '.join(s['words'][i] for i in idxs)}\n\n")
                n += 1
