"""Tiny local web app (standard library only): http://127.0.0.1:7860"""
import json
import mimetypes
import os
import threading
import traceback
import uuid
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import unquote, urlparse

from . import audio, pipeline, voice
from .planner import CAMERAS, pitch_str
from .props import all_prop_names
from .scenes import SETTINGS
from .stickman import ACTIONS, MOODS
from .themes import THEMES

STATIC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
JOBS = {}
CFG_PATH = None
EDGE_VOICES = ["en-US-GuyNeural", "en-US-AriaNeural", "en-US-JennyNeural", "en-US-ChristopherNeural",
               "en-GB-RyanNeural", "en-GB-SoniaNeural", "en-IN-PrabhatNeural", "en-IN-NeerjaNeural",
               "hi-IN-MadhurNeural", "hi-IN-SwaraNeural", "bn-IN-BashkarNeural", "ta-IN-ValluvarNeural",
               "te-IN-MohanNeural", "mr-IN-ManoharNeural", "gu-IN-NiranjanNeural", "es-ES-AlvaroNeural",
               "fr-FR-HenriNeural", "de-DE-ConradNeural", "ja-JP-KeitaNeural", "zh-CN-YunxiNeural"]

LAB_VOICES = [("hi-IN-SwaraNeural", "Swara (female, Hindi)"), ("hi-IN-MadhurNeural", "Madhur (male, Hindi)"),
              ("en-US-AvaMultilingualNeural", "Ava (female, reads Hindi)"), ("en-US-EmmaMultilingualNeural", "Emma (female, reads Hindi)"),
              ("en-US-AndrewMultilingualNeural", "Andrew (male, reads Hindi)"), ("en-US-BrianMultilingualNeural", "Brian (male, reads Hindi)")]
LAB_PRESETS = [{"name": "Natural girl", "edge_voice": "hi-IN-SwaraNeural", "pitch": "+0Hz", "speed": 1.0},
               {"name": "Natural boy", "edge_voice": "hi-IN-MadhurNeural", "pitch": "+0Hz", "speed": 1.0},
               {"name": "Soft woman", "edge_voice": "en-US-EmmaMultilingualNeural", "pitch": "+0Hz", "speed": 0.95},
               {"name": "Deep man", "edge_voice": "hi-IN-MadhurNeural", "pitch": "-40Hz", "speed": 0.92},
               {"name": "Cartoon kid", "edge_voice": "hi-IN-SwaraNeural", "pitch": "+50Hz", "speed": 1.1},
               {"name": "Cartoon boy", "edge_voice": "hi-IN-MadhurNeural", "pitch": "+60Hz", "speed": 1.12},
               {"name": "Squeaky cartoon", "edge_voice": "hi-IN-SwaraNeural", "pitch": "+100Hz", "speed": 1.25},
               {"name": "Cartoon villain", "edge_voice": "hi-IN-MadhurNeural", "pitch": "-70Hz", "speed": 0.82}]


def _cfg():
    return pipeline.load_config(CFG_PATH)


def _run_job(job_id, plan, overrides, preview):
    job = JOBS[job_id]

    def log(m):
        job["log"].append(str(m))

    def progress(p, msg=""):
        job["progress"], job["message"] = round(p, 1), msg

    try:
        res = pipeline.render_plan(plan, _cfg(), log=log, progress=progress, voice_overrides=overrides,
                                   preview_seconds=preview)
        rel = os.path.relpath(res["video"], pipeline.OUTPUT).replace(os.sep, "/")
        res["video_url"] = "/files/" + rel
        res["srt_url"] = "/files/" + os.path.relpath(res["srt"], pipeline.OUTPUT).replace(os.sep, "/")
        res["folder"] = os.path.dirname(res["video"])
        job.update(status="done", result=res, progress=100)
    except Exception as e:
        job["log"].append(traceback.format_exc())
        job.update(status="error", message=str(e))


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass

    def _json(self, obj, code=200):
        data = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _body(self):
        n = int(self.headers.get("Content-Length") or 0)
        return json.loads(self.rfile.read(n).decode("utf-8") or "{}")

    def _file(self, path):
        if not os.path.isfile(path):
            self.send_error(404)
            return
        size = os.path.getsize(path)
        ctype = mimetypes.guess_type(path)[0] or "application/octet-stream"
        rng = self.headers.get("Range")
        start, end = 0, size - 1
        if rng and rng.startswith("bytes="):
            a, _, b = rng[6:].partition("-")
            start = int(a) if a else 0
            end = int(b) if b else size - 1
            self.send_response(206)
            self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
        else:
            self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Content-Length", str(end - start + 1))
        self.end_headers()
        with open(path, "rb") as f:
            f.seek(start)
            left = end - start + 1
            while left > 0:
                chunk = f.read(min(1 << 16, left))
                if not chunk:
                    break
                try:
                    self.wfile.write(chunk)
                except (BrokenPipeError, ConnectionResetError):
                    return
                left -= len(chunk)

    def do_GET(self):
        p = urlparse(self.path).path
        if p in ("/", "/index.html"):
            return self._file(os.path.join(STATIC, "index.html"))
        if p == "/voicelab":
            return self._file(os.path.join(STATIC, "voicelab.html"))
        if p == "/api/voice_lab":
            return self._json({"presets": LAB_PRESETS, "voices": [{"id": k, "label": v} for k, v in LAB_VOICES]})
        if p.startswith("/files/"):
            rel = unquote(p[len("/files/"):])
            full = os.path.abspath(os.path.join(pipeline.OUTPUT, rel))
            if not full.startswith(os.path.abspath(pipeline.OUTPUT)):
                return self.send_error(403)
            return self._file(full)
        if p == "/api/options":
            cfg = _cfg()
            vc = cfg.get("voice", {})
            running = voice.voicestudio_available(vc)
            return self._json({
                "styles": [{"id": k, "label": v["label"], "code": v["code"], "group": v["group"], "about": v["about"]}
                           for k, v in THEMES.items()],
                "actions": ACTIONS, "moods": MOODS, "settings": SETTINGS, "cameras": CAMERAS,
                "props": all_prop_names(), "edge_voices": EDGE_VOICES,
                "voicestudio": {"running": running, "url": voice.voicestudio_url(vc),
                                "voices": voice.voicestudio_voices(vc) if running else []},
                "defaults": {"video": cfg.get("video", {}), "voice": vc},
            })
        if p.startswith("/api/style_preview/"):
            from .preview import style_preview
            sid = p.rsplit("/", 1)[-1].replace(".png", "")
            try:
                return self._file(style_preview(sid, os.path.join(pipeline.OUTPUT, "_style_previews")))
            except Exception:
                return self.send_error(500)
        if p.startswith("/api/job/"):
            job = JOBS.get(p.rsplit("/", 1)[-1])
            return self._json(job or {"status": "missing"}, 200 if job else 404)
        if p == "/api/history":
            items = []
            if os.path.isdir(pipeline.OUTPUT):
                for d in sorted(os.listdir(pipeline.OUTPUT), reverse=True)[:30]:
                    for name in ("video.mp4", "preview.mp4"):
                        if os.path.exists(os.path.join(pipeline.OUTPUT, d, name)):
                            items.append({"name": d, "url": f"/files/{d}/{name}", "plan_url": f"/files/{d}/plan.json"})
                            break
            return self._json(items)
        self.send_error(404)

    def do_POST(self):
        p = urlparse(self.path).path
        if p == "/api/upload":
            name = os.path.basename(unquote(self.headers.get("X-Filename") or "audio.wav")) or "audio.wav"
            name = "".join(c if c.isalnum() or c in "._-" else "_" for c in name)
            n = int(self.headers.get("Content-Length") or 0)
            if n <= 0 or n > 500 * 1024 * 1024:
                return self._json({"error": "File is empty or larger than 500 MB"}, 400)
            folder = os.path.join(pipeline.OUTPUT, "_uploads")
            os.makedirs(folder, exist_ok=True)
            path = os.path.join(folder, uuid.uuid4().hex[:8] + "_" + name)
            with open(path, "wb") as f:
                left = n
                while left > 0:
                    chunk = self.rfile.read(min(1 << 20, left))
                    if not chunk:
                        break
                    f.write(chunk)
                    left -= len(chunk)
            return self._json({"path": path, "name": name,
                               "url": "/files/" + os.path.relpath(path, pipeline.OUTPUT).replace(os.sep, "/")})
        try:
            body = self._body()
        except Exception:
            return self._json({"error": "bad json"}, 400)
        if p == "/api/plan":
            cfg = _cfg()
            if not body.get("use_llm", True):
                cfg.setdefault("llm", {})["backend"] = "none"
            logs = []
            try:
                plan = pipeline.make_plan(body.get("prompt", ""), cfg, body.get("style"), body.get("ratio"),
                                          body.get("seconds"), body.get("language"), log=logs.append)
                return self._json({"plan": plan, "log": logs})
            except Exception as e:
                return self._json({"error": str(e), "log": logs}, 400)
        if p == "/api/director":
            from .director import treatment
            from .planner import sanitize
            try:
                plan = sanitize(body.get("plan") or {}, body.get("plan", {}).get("style") or "b1-notebook", "16:9")
                return self._json({"markdown": treatment(plan)})
            except Exception as e:
                return self._json({"error": str(e)}, 400)
        if p == "/api/plan_audio":
            cfg = _cfg()
            if not body.get("use_llm", True):
                cfg.setdefault("llm", {})["backend"] = "none"
            path = body.get("path") or ""
            if not os.path.abspath(path).startswith(os.path.abspath(pipeline.OUTPUT)) or not os.path.isfile(path):
                return self._json({"error": "Upload an audio file first"}, 400)
            logs = []
            try:
                plan = pipeline.plan_from_audio(path, cfg, body.get("style"), body.get("ratio"), body.get("language"),
                                                body.get("transcript"), body.get("direction") or "", log=logs.append)
                return self._json({"plan": plan, "log": logs})
            except Exception as e:
                return self._json({"error": str(e), "log": logs}, 400)
        if p == "/api/voice_test":
            text = str(body.get("text") or "").strip()[:500]
            name = body.get("edge_voice")
            pitch = pitch_str(body.get("pitch"))
            if not text or name not in dict(LAB_VOICES) or pitch is None:
                return self._json({"error": "Enter a line and choose a voice"}, 400)
            pitch = f"{max(-100, min(100, int(pitch[:-2]))):+d}Hz"  # the voices stop changing past +100Hz
            speed = max(0.5, min(2.0, float(body.get("speed") or 1.0)))
            try:
                vc = {"backend": "edge", "edge_voice": name, "pitch": pitch, "speed": speed}
                clip, _ = voice.synthesize(text, os.path.join(pipeline.OUTPUT, "_voice_cache"), vc)
                folder = os.path.join(pipeline.OUTPUT, "_voice_lab")
                os.makedirs(folder, exist_ok=True)
                file = voice._cache_name(text, vc, "lab") + ".wav"
                audio.write_wav(os.path.join(folder, file), clip)
                return self._json({"url": "/files/_voice_lab/" + file, "settings": vc})
            except Exception as e:
                return self._json({"error": str(e)}, 400)
        if p == "/api/render":
            plan = body.get("plan")
            if not plan or not plan.get("scenes"):
                return self._json({"error": "No scenes to render"}, 400)
            job_id = uuid.uuid4().hex[:10]
            JOBS[job_id] = {"id": job_id, "status": "running", "progress": 0, "message": "Starting", "log": []}
            threading.Thread(target=_run_job, args=(job_id, plan, body.get("voice") or {}, body.get("preview")),
                             daemon=True).start()
            return self._json({"job": job_id})
        self.send_error(404)


def serve(config_path=None):
    global CFG_PATH
    CFG_PATH = config_path
    cfg = _cfg()
    host = cfg.get("web", {}).get("host", "127.0.0.1")
    port = int(cfg.get("web", {}).get("port", 7860))
    srv = ThreadingHTTPServer((host, port), Handler)
    url = f"http://{host}:{port}"
    print(f"StickVoice Studio running at {url}  (Ctrl+C to stop)")
    try:
        webbrowser.open(url)
    except Exception:
        pass
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    return 0
