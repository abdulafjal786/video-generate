"""Speech-to-text with timestamps, for "audio -> video" mode.

Order for backend "auto":
  1. VoiceStudio  - local app, POST {url}/v1/audio/transcriptions (verbose_json, word timestamps)
  2. faster-whisper - local Python package (pip install faster-whisper); downloads a model once
  3. OpenAI-compatible API - stt.api_key (OpenAI, Groq, ...) with stt.base_url / stt.model
If all fail, type the words yourself ("transcript") and they are spread over the speech.

Returns {"text", "segments": [{"start","end","text"}], "words": [{"word","start","end"}], "backend"}.
"""
import os

import numpy as np

from . import audio, voice


class TranscribeError(RuntimeError):
    pass


def _norm(data, backend):
    segs = [{"start": float(s.get("start") or 0), "end": float(s.get("end") or 0), "text": (s.get("text") or "").strip()}
            for s in data.get("segments") or [] if (s.get("text") or "").strip()]
    words = [{"word": str(w.get("word") or w.get("text") or "").strip(), "start": float(w["start"]), "end": float(w["end"])}
             for w in data.get("words") or [] if w.get("start") is not None and str(w.get("word") or w.get("text") or "").strip()]
    if not words:  # some engines nest words inside segments
        for s in data.get("segments") or []:
            for w in s.get("words") or []:
                if w.get("start") is not None:
                    words.append({"word": str(w.get("word") or "").strip(), "start": float(w["start"]), "end": float(w["end"])})
    text = (data.get("text") or " ".join(s["text"] for s in segs)).strip()
    if not segs and text:
        segs = [{"start": words[0]["start"] if words else 0.0, "end": words[-1]["end"] if words else 0.0, "text": text}]
    return {"text": text, "segments": segs, "words": [w for w in words if w["word"]], "backend": backend}


def _openai_style(path, url, headers, model, language, timeout):
    import requests
    data = {"model": model, "response_format": "verbose_json"}
    if language:
        data["language"] = language
    fields = list(data.items()) + [("timestamp_granularities[]", "word"), ("timestamp_granularities[]", "segment")]
    with open(path, "rb") as f:
        r = requests.post(url, headers=headers, data=fields, files={"file": (os.path.basename(path), f)}, timeout=timeout)
    if r.status_code != 200:
        raise TranscribeError(f"HTTP {r.status_code}: {r.text[:300]}")
    return r.json()


def _voicestudio(path, cfg, language):
    vcfg = cfg.get("voice", {})
    if not voice.voicestudio_available(vcfg):
        raise TranscribeError("VoiceStudio not running at " + voice.voicestudio_url(vcfg))
    url = voice.voicestudio_url(vcfg) + "/v1/audio/transcriptions"
    return _norm(_openai_style(path, url, voice._vs_headers(vcfg), "whisper-1", language, 1800), "voicestudio")


def _faster_whisper(path, cfg, language):
    try:
        from faster_whisper import WhisperModel
    except ImportError as e:
        raise TranscribeError("faster-whisper not installed (pip install faster-whisper)") from e
    size = cfg.get("stt", {}).get("whisper_model") or "small"
    model = WhisperModel(size, device="auto", compute_type="int8")
    segs, _info = model.transcribe(path, language=language or None, word_timestamps=True, vad_filter=True)
    out = {"segments": [], "words": []}
    for s in segs:
        out["segments"].append({"start": s.start, "end": s.end, "text": s.text})
        for w in s.words or []:
            out["words"].append({"word": w.word, "start": w.start, "end": w.end})
    return _norm(out, "faster-whisper " + size)


def _api(path, cfg, language):
    s = cfg.get("stt", {})
    key = s.get("api_key") or os.environ.get("OPENAI_API_KEY") or os.environ.get("GROQ_API_KEY")
    if not key:
        raise TranscribeError("no stt.api_key set")
    base = (s.get("base_url") or ("https://api.groq.com/openai/v1" if os.environ.get("GROQ_API_KEY") and not s.get("api_key")
                                  else "https://api.openai.com/v1")).rstrip("/")
    model = s.get("model") or ("whisper-large-v3" if "groq" in base else "whisper-1")
    return _norm(_openai_style(path, base + "/audio/transcriptions", {"Authorization": f"Bearer {key}"}, model, language, 900),
                 "api " + model)


BACKENDS = {"voicestudio": _voicestudio, "whisper": _faster_whisper, "api": _api}


def transcribe(path, cfg, language=None, log=print):
    backend = (cfg.get("stt", {}).get("backend") or "auto").lower()
    order = [backend] if backend in BACKENDS else ["voicestudio", "whisper", "api"]
    errors = []
    for b in order:
        try:
            log(f"Transcribing with {b}...")
            res = BACKENDS[b](path, cfg, language)
            if res["text"]:
                return res
            errors.append(f"{b}: empty transcript")
        except Exception as e:
            errors.append(f"{b}: {e}")
    raise TranscribeError("Could not transcribe the audio. Type the words into the transcript box instead. ("
                          + " | ".join(errors) + ")")


def from_typed_text(path, text):
    """Spread a typed transcript over the speech in the file (no speech-to-text needed).
    Sentences are snapped to the longest pauses in the recording."""
    from .planner import split_sentences
    x = audio.load(path)
    length = len(x) / audio.SR
    sents = split_sentences(text) or [text.strip()]
    # loudness per 50 ms to find speech and pauses
    hop = int(audio.SR * 0.05)
    n = max(1, len(x) // hop)
    rms = np.array([np.sqrt(np.mean(x[i * hop:(i + 1) * hop] ** 2)) for i in range(n)])
    thr = max(0.01, np.percentile(rms, 30) * 1.5)
    voiced = np.where(rms > thr)[0]
    a = voiced[0] * 0.05 if len(voiced) else 0.0
    b = (voiced[-1] + 1) * 0.05 if len(voiced) else length
    # candidate pauses: runs of quiet frames inside the speech
    pauses, run = [], 0
    for i in range(n):
        if rms[i] <= thr:
            run += 1
        else:
            if run >= 4 and a < i * 0.05 < b:
                pauses.append(((i - run / 2) * 0.05, run))
            run = 0
    chars = [len(s) for s in sents]
    total = sum(chars) or 1
    cuts, acc = [], 0
    for c in chars[:-1]:
        acc += c
        guess = a + (b - a) * acc / total
        near = [p for p in pauses if abs(p[0] - guess) < (b - a) * 0.12]
        cuts.append(max(near, key=lambda p: p[1])[0] if near else guess)
    bounds = [a] + sorted(cuts) + [b]
    segs = [{"start": bounds[i], "end": bounds[i + 1], "text": s} for i, s in enumerate(sents)]
    return {"text": text.strip(), "segments": segs, "words": [], "backend": "typed transcript"}
