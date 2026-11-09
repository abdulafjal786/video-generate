"""Join AI video clips (from the Colab notebook) into one video with StickVoice's voice and captions.

Each clip_NN.mp4 is fitted to scene NN's length from timeline.json: scaled and cropped
to the video size, slowed down a little if it is short, then looped. A scene with no
clip uses that part of StickVoice's own animation (video.mp4) instead.
"""
import json
import os
import re
import subprocess
import tempfile
import wave
import zipfile

from .audio import ffmpeg_exe

MAX_SLOW = 1.6  # stretch a clip up to this much before looping it


def _run(cmd, cwd=None):
    p = subprocess.run(cmd, capture_output=True, cwd=cwd)
    if p.returncode != 0:
        raise RuntimeError("ffmpeg failed: " + p.stderr.decode(errors="ignore")[-800:])


def _duration(path):
    p = subprocess.run([ffmpeg_exe(), "-i", path], capture_output=True)
    m = re.search(r"Duration: (\d+):(\d+):([\d.]+)", p.stderr.decode(errors="ignore"))
    return int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3)) if m else 0.0


def _secs(ts):
    h, m, s = ts.strip().replace(",", ".").split(":")
    return int(h) * 3600 + int(m) * 60 + float(s)


def _in_ranges(cue, ranges):
    """True if the middle of an SRT cue falls inside one of the (start, end) ranges."""
    m = re.search(r"([\d:,]+)\s*-->\s*([\d:,]+)", cue)
    if not m:
        return False
    mid = (_secs(m.group(1)) + _secs(m.group(2))) / 2
    return any(a <= mid < b for a, b in ranges)


def end_clip_spec(plan, root=None):
    """plan["end_clip"] as {"path", "volume", "seconds"}; a plain string is just the path. None if not set."""
    ec = plan.get("end_clip")
    if not ec:
        return None
    spec = {"path": ec} if isinstance(ec, str) else dict(ec)
    p = os.path.expanduser(str(spec.get("path") or ""))
    if p and not os.path.isabs(p) and not os.path.exists(p) and root:
        p = os.path.join(root, p)  # relative paths may also be relative to the project folder
    spec["path"] = p
    return spec


def _overlay_clip(video, spec, clip, dur, has_audio, W, H, fps, log):
    """Merge a clip over the last part of `video` at low opacity; both end together."""
    ff = ffmpeg_exe()
    vdur = _duration(video)
    dur = min(dur, vdur)
    start = max(0.0, vdur - dur)
    opacity = min(1.0, max(0.05, float(spec.get("opacity", 0.3))))
    size = f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H}" if spec.get("fit") == "fill"         else f"scale={W}:{H}:force_original_aspect_ratio=decrease"
    graph = (f"[1:v]trim=duration={dur:.3f},setpts=PTS-STARTPTS+{start:.3f}/TB,{size},fps={fps},format=rgba,"
             f"colorchannelmixer=aa={opacity:.3f}[ov];"
             f"[0:v][ov]overlay=(W-w)/2:(H-h)/2:eof_action=pass,format=yuv420p[v]")
    amap = "0:a"
    if has_audio:  # the video's own audio stays at full level
        ms = int(start * 1000)
        graph += (f";[1:a]atrim=duration={dur:.3f},asetpts=PTS-STARTPTS,aresample=44100,"
                  f"aformat=sample_fmts=fltp:channel_layouts=stereo,volume={float(spec.get('volume', 0.3))},adelay={ms}|{ms}[m];"
                  f"[0:a]aresample=44100,aformat=sample_fmts=fltp:channel_layouts=stereo[a0];"
                  f"[a0][m]amix=inputs=2:duration=first:normalize=0[a]")
        amap = "[a]"
    tmp = video + ".tmp.mp4"
    _run([ff, "-y", "-v", "error", "-i", video, "-i", clip, "-filter_complex", graph, "-map", "[v]", "-map", amap,
          "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-c:a", "aac", "-b:a", "192k",
          "-movflags", "+faststart", tmp])
    os.replace(tmp, video)
    log(f"Clip merged over the last {dur:.1f}s at {opacity:.0%} opacity: {os.path.basename(clip)}")
    return 0.0  # the video keeps its length


def append_clip(video, spec, W, H, fps=30, log=print):
    """Append a clip (meme, outro...) to `video` in place, fitted inside a blurred copy of itself."""
    clip = spec["path"]
    if not clip or not os.path.exists(clip):
        log(f"End clip not found, skipped: {clip}")
        return False
    ff = ffmpeg_exe()
    probe = subprocess.run([ff, "-i", clip], capture_output=True).stderr.decode(errors="ignore")
    has_audio = "Audio:" in probe
    dur = _duration(clip)
    if spec.get("seconds"):
        dur = min(dur or float(spec["seconds"]), float(spec["seconds"]))
    if dur <= 0:
        log(f"End clip has no length, skipped: {clip}")
        return False
    if spec.get("mode") == "overlay":
        return _overlay_clip(video, spec, clip, dur, has_audio, W, H, fps, log)
    vol = float(spec.get("volume", 1.0))
    fmt = f"fps={fps},setsar=1,format=yuv420p"
    stereo = "aresample=44100,aformat=sample_fmts=fltp:channel_layouts=stereo"
    if spec.get("fit") == "fill":  # crop the middle to fill the frame (clips with bars baked in)
        video_graph = f"[1:v]trim=duration={dur:.3f},setpts=PTS-STARTPTS,scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},{fmt}[v1];"
    else:                          # show the whole clip over a blurred copy of itself
        video_graph = (f"[1:v]trim=duration={dur:.3f},setpts=PTS-STARTPTS,split[a][b];"
                       f"[a]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},boxblur=20:2,eq=brightness=-0.12[bg];"
                       f"[b]scale={W}:{H}:force_original_aspect_ratio=decrease[fg];[bg][fg]overlay=(W-w)/2:(H-h)/2,{fmt}[v1];")
    graph = (video_graph + f"[0:v]{fmt}[v0];[0:a]{stereo}[a0];"
             f"[{1 if has_audio else 2}:a]atrim=duration={dur:.3f},asetpts=PTS-STARTPTS,{stereo},volume={vol}[a1];"
             f"[v0][a0][v1][a1]concat=n=2:v=1:a=1[v][a]")
    tmp = video + ".tmp.mp4"
    cmd = [ff, "-y", "-v", "error", "-i", video, "-i", clip]
    if not has_audio:
        cmd += ["-f", "lavfi", "-t", f"{dur:.3f}", "-i", "anullsrc=r=44100:cl=stereo"]
    cmd += ["-filter_complex", graph, "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-preset", "veryfast",
            "-crf", "20", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", tmp]
    _run(cmd)
    os.replace(tmp, video)
    log(f"End clip added ({dur:.1f}s): {os.path.basename(clip)}")
    return dur


def _timeline(out_dir):
    path = os.path.join(out_dir, "timeline.json")
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    # older renders: split the audio by the number of words in each scene
    with open(os.path.join(out_dir, "plan.json"), encoding="utf-8") as f:
        plan = json.load(f)
    with wave.open(os.path.join(out_dir, "audio.wav")) as w:
        total = w.getnframes() / w.getframerate()
    words = [max(1, len(s["narration"].split())) for s in plan["scenes"]]
    scenes, st = [], 0.0
    for n in words:
        d = total * n / sum(words)
        scenes.append({"start": st, "dur": d})
        st += d
    size = {"16:9": [1280, 720], "9:16": [720, 1280], "1:1": [1080, 1080]}.get(plan.get("ratio"), [1280, 720])
    return {"ratio": plan.get("ratio", "16:9"), "size": size, "total": total, "scenes": scenes}


def _find_clips(out_dir, clips_src, tmp):
    """clip number -> file. clips_src may be a folder or a .zip; default: <out_dir>/clips(.zip)."""
    src = clips_src
    if not src:
        for c in ("clips.zip", "clips"):
            if os.path.exists(os.path.join(out_dir, c)):
                src = os.path.join(out_dir, c)
                break
    if not src or not os.path.exists(src):
        raise FileNotFoundError("No clips found. Put clips.zip (from the Colab notebook) in " + out_dir)
    if src.lower().endswith(".zip"):
        with zipfile.ZipFile(src) as z:
            z.extractall(os.path.join(tmp, "clips"))
        src = os.path.join(tmp, "clips")
    found = {}
    for root, _, files in os.walk(src):
        for name in files:
            m = re.match(r"clip_(\d+)\.mp4$", name, re.I)
            if m:
                found[int(m.group(1))] = os.path.join(root, name)
    return found


def assemble(out_dir, clips_src=None, captions=True, log=print):
    out_dir = os.path.abspath(out_dir)
    try:  # a plan with "captions": false stays caption-free
        with open(os.path.join(out_dir, "plan.json"), encoding="utf-8") as f:
            captions = captions and json.load(f).get("captions", True) is not False
    except OSError:
        pass
    tl = _timeline(out_dir)
    W, H = tl["size"]
    fps = 30
    own = os.path.join(out_dir, "video.mp4")
    ff = ffmpeg_exe()
    with tempfile.TemporaryDirectory() as tmp:
        clips = _find_clips(out_dir, clips_src, tmp)
        log(f"Found {len(clips)} AI clips for {len(tl['scenes'])} scenes")
        fit = f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},fps={fps},setsar=1,format=yuv420p"
        parts = []
        for i, sc in enumerate(tl["scenes"]):
            seg = os.path.join(tmp, f"seg_{i:03d}.mp4")
            dur = sc["dur"]
            clip = clips.get(i + 1)
            if clip:
                k = min(MAX_SLOW, max(1.0, dur / max(0.1, _duration(clip))))
                cmd = [ff, "-y", "-v", "error", "-stream_loop", "-1", "-i", clip,
                       "-vf", f"setpts={k:.3f}*PTS,{fit}", "-t", f"{dur:.3f}"]
                log(f"Scene {i + 1}: AI clip" + (f" (slowed x{k:.2f})" if k > 1.01 else ""))
            elif os.path.exists(own):
                cmd = [ff, "-y", "-v", "error", "-ss", f"{sc['start']:.3f}", "-i", own, "-vf", fit, "-t", f"{dur:.3f}"]
                log(f"Scene {i + 1}: no AI clip, using the StickVoice animation")
            else:
                raise FileNotFoundError(f"clip_{i + 1:02d}.mp4 is missing and there is no video.mp4 to fall back on")
            _run(cmd + ["-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", seg])
            parts.append(seg)
        lst = os.path.join(tmp, "list.txt")
        with open(lst, "w", encoding="utf-8") as f:
            f.writelines(f"file '{p.replace(os.sep, '/')}'\n" for p in parts)
        joined = os.path.join(tmp, "joined.mp4")
        _run([ff, "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", joined])

        out = os.path.join(out_dir, "ai_video.mp4")
        base = [ff, "-y", "-v", "error", "-i", joined, "-i", "audio.wav"]
        enc = ["-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", "ai_video.mp4"]
        srt = os.path.exists(os.path.join(out_dir, "captions.srt"))
        burned = False
        if captions and srt:  # burn captions in (run inside out_dir so the filter path needs no escaping)
            # fallback scenes already show StickVoice's own captions, so only burn the cues of AI-clip scenes
            ai = [(sc["start"], sc["start"] + sc["dur"]) for i, sc in enumerate(tl["scenes"]) if (i + 1) in clips]
            tmp_srt = os.path.join(out_dir, "_captions_ai.srt")
            with open(os.path.join(out_dir, "captions.srt"), encoding="utf-8") as f:
                cues = [c for c in f.read().strip().split("\n\n") if _in_ranges(c, ai)]
            with open(tmp_srt, "w", encoding="utf-8") as f:
                f.write("\n\n".join(cues) + "\n")
            style = "FontName=Segoe UI,Bold=1,FontSize=13,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,BorderStyle=1,Outline=2,MarginV=40"
            try:
                _run(base + ["-vf", f"subtitles=_captions_ai.srt:force_style='{style}'", "-c:v", "libx264", "-preset", "veryfast",
                             "-crf", "20", "-pix_fmt", "yuv420p"] + enc, cwd=out_dir)
                burned = True
            except RuntimeError as e:
                log(f"Could not burn captions ({str(e)[-160:]}); adding them as a subtitle track instead")
            finally:
                os.remove(tmp_srt)
        if not burned:
            extra = ["-i", "captions.srt", "-map", "0:v", "-map", "1:a", "-map", "2:s", "-c:s", "mov_text"] if (captions and srt) else []
            _run(base + extra + ["-c:v", "copy"] + enc, cwd=out_dir)
    plan_path = os.path.join(out_dir, "plan.json")
    if os.path.exists(plan_path):
        with open(plan_path, encoding="utf-8") as f:
            spec = end_clip_spec(json.load(f), os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        if spec:
            append_clip(out, spec, W, H, fps, log=log)
    log("AI video: " + out)
    return out
