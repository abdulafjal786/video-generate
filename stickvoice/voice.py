"""Text-to-speech backends.

Order for backend "auto":
  1. VoiceStudio  - local app (github.com/debpalash/voicestudio), OpenAI-compatible
                    endpoint POST {url}/v1/audio/speech. Best quality, offline, cloning.
  2. edge-tts     - free Microsoft neural voices (needs internet), pip install edge-tts
  3. pyttsx3      - Windows built-in SAPI voices, fully offline
  4. silent       - placeholder silence so the animation still renders
"""
import asyncio
import hashlib
import json
import os
import wave

import numpy as np

from . import audio


class VoiceError(RuntimeError):
    pass


def _cache_name(text, vcfg, backend):
    key = json.dumps([text, backend, vcfg.get("voice"), vcfg.get("edge_voice"), vcfg.get("model"),
                      vcfg.get("language"), vcfg.get("speed"), vcfg.get("instructions"), vcfg.get("pitch"),
                      vcfg.get("sapi_voice")], sort_keys=True)
    return hashlib.sha1(key.encode("utf-8")).hexdigest()[:16]


# ---------------------------------------------------------------------------
def voicestudio_url(vcfg):
    return (vcfg.get("voicestudio_url") or os.environ.get("VOICESTUDIO_URL") or "http://127.0.0.1:3900").rstrip("/")


def voicestudio_available(vcfg, timeout=2.0):
    import requests
    try:
        r = requests.get(voicestudio_url(vcfg) + "/v1/models", timeout=timeout, headers=_vs_headers(vcfg))
        return r.status_code == 200
    except Exception:
        return False


def _vs_headers(vcfg):
    key = vcfg.get("voicestudio_api_key") or os.environ.get("OMNIVOICE_API_KEY")
    return {"Authorization": f"Bearer {key}"} if key else {}


def voicestudio_voices(vcfg):
    import requests
    try:
        r = requests.get(voicestudio_url(vcfg) + "/v1/audio/voices", timeout=4, headers=_vs_headers(vcfg))
        r.raise_for_status()
        data = r.json()
        items = data.get("voices", data.get("data", data)) if isinstance(data, dict) else data
        out = []
        for v in items or []:
            if isinstance(v, dict):
                out.append({"id": v.get("voice_id") or v.get("id"), "name": v.get("name") or v.get("voice_id")})
        return out
    except Exception:
        return []


def _voicestudio(text, path, vcfg):
    import requests
    body = {
        "model": vcfg.get("model") or "omnivoice",
        "input": text,
        "voice": vcfg.get("voice") or "alloy",
        "response_format": "wav",
        "speed": float(vcfg.get("speed") or 1.0),
    }
    if vcfg.get("language"):
        body["language"] = vcfg["language"]
    if vcfg.get("instructions"):
        body["instructions"] = vcfg["instructions"]
    r = requests.post(voicestudio_url(vcfg) + "/v1/audio/speech", json=body,
                      headers=_vs_headers(vcfg), timeout=float(vcfg.get("timeout") or 900))
    if r.status_code != 200:
        raise VoiceError(f"VoiceStudio HTTP {r.status_code}: {r.text[:300]}")
    with open(path, "wb") as f:
        f.write(r.content)


def _edge(text, path, vcfg):
    try:
        import edge_tts
    except ImportError as e:
        raise VoiceError("edge-tts not installed (pip install edge-tts)") from e
    voice = vcfg.get("edge_voice") or "en-US-GuyNeural"
    speed = float(vcfg.get("speed") or 1.0)
    rate = f"{int(round((speed - 1) * 100)):+d}%"
    pitch = vcfg.get("pitch") or "+0Hz"  # e.g. "+20Hz": the same voice sounds like a different person

    async def go():
        await edge_tts.Communicate(text, voice, rate=rate, pitch=pitch).save(path)
    asyncio.run(go())


def _sapi(text, path, vcfg):
    try:
        import pyttsx3
    except ImportError as e:
        raise VoiceError("pyttsx3 not installed (pip install pyttsx3)") from e
    eng = pyttsx3.init()
    eng.setProperty("rate", int(175 * float(vcfg.get("speed") or 1.0)))
    want = (vcfg.get("sapi_voice") or "").lower()
    if want:
        for v in eng.getProperty("voices"):
            if want in (v.name or "").lower():
                eng.setProperty("voice", v.id)
                break
    eng.save_to_file(text, path)
    eng.runAndWait()
    if not os.path.exists(path) or os.path.getsize(path) < 100:
        raise VoiceError("pyttsx3 produced no audio")


def _silent(text, path, vcfg):
    secs = max(1.5, len(text.split()) / 2.6)
    audio.write_wav(path, np.zeros(int(secs * audio.SR), dtype=np.float32))


BACKENDS = {"voicestudio": _voicestudio, "edge": _edge, "sapi": _sapi, "silent": _silent}
EXT = {"voicestudio": ".wav", "edge": ".mp3", "sapi": ".wav", "silent": ".wav"}


def synthesize(text, cache_dir, vcfg, log=print):
    """Return (audio_array, backend_used). Results are cached by text+settings."""
    os.makedirs(cache_dir, exist_ok=True)
    backend = (vcfg.get("backend") or "auto").lower()
    order = [backend] if backend != "auto" else ["voicestudio", "edge", "sapi", "silent"]
    errors = []
    for b in order:
        if b not in BACKENDS:
            errors.append(f"{b}: unknown backend")
            continue
        if b == "voicestudio" and backend == "auto" and not voicestudio_available(vcfg):
            errors.append("voicestudio: not running at " + voicestudio_url(vcfg))
            continue
        path = os.path.join(cache_dir, _cache_name(text, vcfg, b) + EXT[b])
        try:
            if not os.path.exists(path) or os.path.getsize(path) < 100:
                BACKENDS[b](text, path, vcfg)
            x = audio.load(path)
            if len(x) < audio.SR * 0.2:
                raise VoiceError("audio too short")
            if b == "silent" and backend == "auto":
                log("WARNING: no voice engine worked, using silence. " + " | ".join(errors))
            return audio.trim_silence(x) if b != "silent" else x, b
        except Exception as e:  # try the next backend
            errors.append(f"{b}: {e}")
            try:
                if os.path.exists(path):
                    os.remove(path)
            except OSError:
                pass
    raise VoiceError("All voice backends failed: " + " | ".join(errors))


def wav_duration(path):
    with wave.open(path) as w:
        return w.getnframes() / w.getframerate()
