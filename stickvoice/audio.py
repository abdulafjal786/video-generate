"""Audio helpers: decode any file with ffmpeg, synthesize sound effects, mix."""
import shutil
import subprocess
import wave

import numpy as np

SR = 44100


def ffmpeg_exe():
    exe = shutil.which("ffmpeg")
    if exe:
        return exe
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception as e:  # pragma: no cover
        raise RuntimeError("ffmpeg not found. Run setup.bat (installs imageio-ffmpeg) or install ffmpeg.") from e


def load(path):
    """Decode an audio file to mono float32 at SR."""
    cmd = [ffmpeg_exe(), "-v", "error", "-i", str(path), "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"]
    out = subprocess.run(cmd, capture_output=True, check=True).stdout
    return np.frombuffer(out, dtype=np.float32).copy()


def trim_silence(x, thresh=0.012, pad=0.05):
    if len(x) == 0:
        return x
    idx = np.where(np.abs(x) > thresh)[0]
    if len(idx) == 0:
        return x
    a = max(0, idx[0] - int(pad * SR))
    b = min(len(x), idx[-1] + int(pad * SR))
    return x[a:b]


def envelope(x, fps):
    """Per-frame loudness 0..1 (used for mouth movement)."""
    hop = SR / fps
    n = int(np.ceil(len(x) / hop))
    env = np.zeros(n, dtype=np.float32)
    for i in range(n):
        seg = x[int(i * hop): int((i + 1) * hop)]
        if len(seg):
            env[i] = float(np.sqrt(np.mean(seg ** 2)))
    if env.max() > 0:
        env = env / (np.percentile(env[env > 0], 90) + 1e-6)
    return np.clip(env, 0, 1)


def write_wav(path, x):
    x = np.clip(x, -1, 1)
    data = (x * 32767).astype(np.int16)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(data.tobytes())


# --- procedural sound effects ----------------------------------------------
def _t(d):
    return np.arange(int(d * SR)) / SR


CROWD_LAUGH = 1.8  # seconds


def sfx(kind):
    rng = np.random.default_rng(7)
    if kind == "pop":
        t = _t(0.12)
        f = 900 - 500 * t / t[-1]
        return 0.5 * np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 35)
    if kind == "whoosh":
        t = _t(0.45)
        n = rng.standard_normal(len(t))
        k = np.ones(40) / 40
        n = np.convolve(n, k, mode="same")
        env = np.sin(np.pi * t / t[-1]) ** 2
        return 0.6 * n * env
    if kind == "ding":
        t = _t(1.0)
        return 0.35 * (np.sin(2 * np.pi * 1320 * t) + 0.5 * np.sin(2 * np.pi * 2640 * t) + 0.25 * np.sin(2 * np.pi * 3960 * t)) * np.exp(-t * 4)
    if kind == "jingle":
        out = np.zeros(int(0.7 * SR))
        for i, f in enumerate((784, 988, 1175, 1568)):
            t = _t(0.3)
            tone = 0.25 * np.sin(2 * np.pi * f * t) * np.exp(-t * 9)
            s = int(i * 0.1 * SR)
            out[s:s + len(tone)] += tone[: len(out) - s]
        return out
    if kind == "boing":
        t = _t(0.4)
        f = 200 + 250 * np.sin(2 * np.pi * 8 * t) * np.exp(-t * 6)
        return 0.4 * np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 6)
    if kind == "sad":
        t = _t(0.9)
        f = 440 * 2 ** (-t / 0.9 * 5 / 12)
        return 0.25 * np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 2.5)
    if kind == "slap":
        t = _t(0.14)
        return 0.7 * rng.standard_normal(len(t)) * np.exp(-t * 70) + 0.4 * np.sin(2 * np.pi * 170 * t) * np.exp(-t * 30)
    if kind == "hangup":                                  # line-dead beeps
        out = np.zeros(int(1.0 * SR))
        t = _t(0.18)
        for i in range(3):
            s = int(i * 0.34 * SR)
            out[s:s + len(t)] += 0.3 * np.sin(2 * np.pi * 425 * t)
        return out
    if kind == "laugh":                                   # a room of people going "ha ha"
        t = _t(CROWD_LAUGH)
        out = np.zeros(len(t))
        for _ in range(26):
            f0, rate = rng.uniform(130, 330), rng.uniform(4.0, 6.5)
            voiced = sum(np.sin(2 * np.pi * h * f0 * t + rng.uniform(0, 6)) * np.exp(-((h * f0 - 850) / 650) ** 2)
                         for h in range(1, 12))
            ha = np.exp(-((t * rate + rng.uniform(0, 1)) % 1) * 4)
            join, leave = rng.uniform(0, 0.35), rng.uniform(0.6, 1.0) * CROWD_LAUGH
            out += voiced * ha * np.clip((t - join) / 0.12, 0, 1) * np.clip((leave - t) / 0.4, 0, 1)
        n = np.convolve(rng.standard_normal(len(t)), np.ones(12) / 12, mode="same")  # breath of the room
        out = out / (np.abs(out).max() + 1e-6) + 0.12 * n * np.sin(np.pi * t / t[-1])
        return 0.6 * out
    if kind == "clap":                                    # applause: many hands, each clap a short noise crack
        t = _t(CROWD_LAUGH)
        out = np.zeros(len(t))
        crack = rng.standard_normal(int(0.03 * SR)) * np.exp(-np.arange(int(0.03 * SR)) / SR * 140)
        crack = np.diff(crack, prepend=0.0)                                         # thinner, brighter
        for _ in range(int(CROWD_LAUGH * 45)):
            s = int(rng.uniform(0, CROWD_LAUGH - 0.04) * SR)
            out[s:s + len(crack)] += crack * rng.uniform(0.4, 1.0)
        out *= np.clip(t / 0.1, 0, 1) * np.clip((CROWD_LAUGH - t) / 0.6, 0, 1)
        return 0.5 * out / (np.abs(out).max() + 1e-6)
    if kind == "ring":                                    # phone ringtone, one phrase
        out = np.zeros(int(1.0 * SR))
        t = _t(0.13)
        for i, f in enumerate((880, 1100, 880, 1100)):
            s = int(i * 0.16 * SR)
            out[s:s + len(t)] += 0.3 * (np.sin(2 * np.pi * f * t) + 0.4 * np.sin(2 * np.pi * 2 * f * t)) * np.sin(np.pi * t / t[-1])
        return out
    if kind == "muffled":                                 # someone shouting into a hand
        t = _t(0.7)
        f0 = 150 + 45 * np.sin(2 * np.pi * 1.7 * t + rng.uniform(0, 6))
        phase = 2 * np.pi * np.cumsum(f0) / SR
        voiced = np.sin(phase) + 0.5 * np.sin(2 * phase) + 0.2 * np.sin(3 * phase)
        return 0.32 * voiced * (0.55 + 0.45 * np.sin(2 * np.pi * 6.5 * t)) * np.sin(np.pi * t / t[-1]) ** 0.5
    if kind == "tap":
        t = _t(0.05)
        return 0.4 * rng.standard_normal(len(t)) * np.exp(-t * 120)
    return np.zeros(1)


def add(buf, clip, start_s, gain=1.0):
    s = int(start_s * SR)
    if s >= len(buf) or s < 0:
        return
    e = min(len(buf), s + len(clip))
    buf[s:e] += clip[: e - s] * gain


def loop_music(path, length, gain=0.08):
    m = load(path)
    if len(m) == 0:
        return np.zeros(length, dtype=np.float32)
    reps = int(np.ceil(length / len(m)))
    m = np.tile(m, reps)[:length]
    fade = int(1.5 * SR)
    m[-fade:] *= np.linspace(1, 0, fade)
    return m * gain
