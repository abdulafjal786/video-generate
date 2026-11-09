# StickVoice Studio

**Type a prompt and get a narrated, animated stickman video (MP4).**

This project combines two open-source projects:

| Part | Comes from | What it does here |
|---|---|---|
| Voice | [debpalash/voicestudio](https://github.com/debpalash/voicestudio) | Local AI voices, voice cloning and 600+ languages, used through its local API on port 3900 |
| Animation | [kaomei/stickman-video-director](https://github.com/kaomei/stickman-video-director) | Stickman styles, hand-drawn fonts and props, rebuilt here as a real animation engine |

```
prompt ──► script writer ──► scenes (narration, action, props, setting, camera)
                                  │
                 VoiceStudio TTS ◄┘  (one voice clip per scene)
                                  │
   skeletal stickman + props + backgrounds animated to the voice timing
   + lip-sync + word-by-word captions + sound effects ──► video.mp4
```

## Quick start (Windows)

1. Install **Python 3.9+** from python.org and tick **Add python.exe to PATH**.
2. Double-click **`setup.bat`**. It installs everything, including ffmpeg.
3. Optional, for the best voices: install and open **VoiceStudio** (`install_voicestudio.bat`
   or the installer from its GitHub releases). Leave the app running.
4. Double-click **`run_web.bat`**. The browser opens at http://127.0.0.1:7860.
5. Type a prompt → **Write script** → edit the scenes if you like → **Render video**.

Videos are saved in `output\<date-title>\` as `video.mp4`, `captions.srt`, `thumbnail.png`,
`plan.json` and `audio.wav`.

No web app? Use `make_video.bat`, or the command line:

```bat
.venv\Scripts\python -m stickvoice "Why do cats purr?" --style story --ratio 9:16
.venv\Scripts\python -m stickvoice --plan examples\saving-money.json
.venv\Scripts\python -m stickvoice "..." --plan-only        :: only write the script
.venv\Scripts\python -m stickvoice "..." --preview 12       :: render a 12-second test
.venv\Scripts\python -m stickvoice --list                   :: styles, actions, props
```

## Dialogue: two characters, two voices, real lip-sync

A scene can be a conversation instead of a narration. In the web app, write one line per speaker in the
scene text:

```text
friend: भाई, कहाँ चलना है?
main: तुम बताओ।
friend: नहीं, तुम बताओ!
```

Each line is voiced separately in that character's voice. Only the speaker's mouth moves (lip-sync from their own
audio), the listener stays quiet, the friend's caption words light up in a second colour, and lines follow each other
with a short natural pause. `narrator:` lines are an off-screen voice.

In `plan.json` a line can also change what the characters do at the moment it starts:

```json
{"who": "main", "text": "घर चलते हैं।", "action": "shrug", "mood": "sad",
 "other": {"action": "facepalm", "mood": "sad"}}
```

On a bike the rider keeps steering, but the friend behind can use `"action": "slap"` (laughing, hand smacking the
rider's back, with a slap sound and the rider jolting) or `"laugh"`. `"mood": "laugh"` gives the laughing face.

For a phone call, set `"layout": "call"` on a scene: each character stays in their own room (split screen), holding
the phone. In C1 the `friend` is drawn as the girl. A line can add `"gain"` (louder shout or softer voice) or `"hearts"`, and
`"call_end": true` on the last scene hangs up after its last line. See [examples/love-on-call.json](examples/love-on-call.json).

For standup, set `"layout": "standup"`: one big comedian with a mic on a brick-wall stage, the audience in front. Line actions
`wave`, `think`, `surprised`, `shrug` and `laugh` move the free hand. A line can add `"pause"` (seconds of silence before it) and
`"crowd": true` (the audience laughs after it, and the comedian waits; `"clap"` adds applause). A scene can set `"outfit"` (`shirt`, `pants`, `shoes`, `hair`
as `[r, g, b]`, plus `hoodie` and `ripped` in C1). See [examples/standup-chintu.json](examples/standup-chintu.json).

Standup scenes can also set `"mic": "stand"` (he holds a stand mic) or `"boom"` (a stand mic in front of him, both hands free), `"backdrop": "curtain"` or `"outdoor"`, and `"audience": false`.

Named characters work in any style: set `"character"` on a scene, or on its `friend`: `tunic_comic`, `tee_comic`, `stick_comic`, `bald_boy`, `friend_orange`,
`friend_blue`, `friend_yellow`, `rider_yellow`, `rider_green`. `"vehicle": "scooter"` swaps the bike in a ride scene for a red scooter.
To see them all: `.venv\Scripts\python -m stickvoice --characters` (writes `output/characters/character-sheet.png`).

For a three-friend prank, set `"layout": "trio"` and a `"beat"` on each scene: `ring`, `grab`, `struggle`, `glare`, `bite`. The boys sit on a
bed; `friend` lines come from the phone, `main` is the friend holding the victim, `narrator` is the friend with the phone, and `bite`
happens on the first `main` line. See [examples/gf-call-prank.json](examples/gf-call-prank.json).

To try voices first, open **Voice Lab** at `http://127.0.0.1:7860/voicelab`: pick a voice, Hz and speed, hear your line, then
copy the settings into your plan. Hz is added to the voice's own pitch, and the sound stops changing above about `+100Hz`.

Voices per character go in `"voices"` (anything from the `voice` settings: `edge_voice`, `pitch`, `speed`,
VoiceStudio `voice`...). Without it, the friend automatically gets a higher, slightly faster version of the main voice.

```json
"voices": {"main":     {"edge_voice": "hi-IN-MadhurNeural", "pitch": "-6Hz"},
           "friend":   {"edge_voice": "hi-IN-MadhurNeural", "pitch": "+24Hz", "speed": 1.08},
           "narrator": {"edge_voice": "hi-IN-SwaraNeural"}}
```

Every scene can override this with its own `"voices"`, and every line with its own `pitch`, `speed` or `edge_voice`
(scene → line wins). In the web app each scene card has **Main / Friend pitch + speed** and **Narrator pitch** fields;
leave them empty to use the video's voice. Pitch accepts `-6Hz`, `-6` or `+3 hz`.

```json
{"action": "ride", "voices": {"main": {"pitch": "-4Hz", "speed": 1.12}, "friend": {"pitch": "+28Hz", "speed": 1.15}},
 "lines": [{"who": "friend", "text": "नहीं, तुम बताओ!", "pitch": "+32Hz"}]}
```

Full example: `examples\kaha-jana-hai.json` (two friends on a bike who can't decide where to go).
With VoiceStudio, give each character its own cloned voice profile for the most natural result.

## End with a meme clip

Add any video (mp4, mov, webm, gif) after the last scene, with its own sound. In the web app use
**End meme clip → Choose video…** under the scenes. In `plan.json`:

```json
"end_clip": {"path": "memes/end.mp4", "volume": 1.0, "seconds": 4}
```

`path` can be absolute or relative to the project folder (a plain string works too), `volume` sets the clip's loudness
and `seconds` cuts it short. A clip in another shape (e.g. a 16:9 meme in a 9:16 short) is shown whole over a blurred
copy of itself; `"fit": "fill"` crops the middle to fill the screen instead (best for memes with bars baked in). It is added to `video.mp4` and to `ai_video.mp4` (`--assemble`), not to quick previews.
Add `"mode": "overlay"` to merge the clip over the last part of the video instead (same length, both end together):
`"opacity": 0.3` keeps the meme faint so your video stays strong, and the video's own audio stays at full level while
`volume` (default 0.3 here) sets the meme's sound. In the web app choose **Merge over video**.

Only use clips you have the right to use.

## Make a video from your own audio

Already have a voice recording (your voice, a podcast clip, a VoiceStudio export)?

1. In the web app, open **1 · Start from → My audio** and drop the file (mp3, wav, m4a, ogg, or even mp4).
2. Optional: paste the exact words, and/or add a creative direction such as *"funny, cooking theme"*.
3. Click **Transcribe & make scenes**. The audio is cut into scenes at the sentence breaks, and each
   scene gets actions, props and a setting that match what is said (Hindi keywords work too).
4. Edit the scenes if you like, then **Render video**. Your original audio is used as-is;
   lip-sync, captions and props follow its real timing.

Or drag the audio file onto **`audio_to_video.bat`**, or use the command line:

```bat
.venv\Scripts\python -m stickvoice --audio my-voice.mp3 --language hi --ratio 9:16
.venv\Scripts\python -m stickvoice --audio my-voice.mp3 --transcript words.txt --direction "kids story"
```

Speech-to-text (`config.json` → `stt.backend`) tries, in order:

| Backend | Needs |
|---|---|
| `voicestudio` | VoiceStudio app running with a speech-recognition model installed (it asks to download one) |
| `whisper` | `pip install faster-whisper` in `.venv`; downloads the `small` model (~460 MB) on first use |
| `api` | `stt.api_key` for OpenAI or Groq (set `stt.base_url` for Groq: `https://api.groq.com/openai/v1`) |

If none of these is available, paste the words yourself in the *What is said* box. StickVoice then
times each sentence to the pauses in your recording, so no speech-to-text is needed.

## Voices

The voice engine is chosen in the web app or in `config.json` → `voice.backend`:

| Backend | Quality | Needs |
|---|---|---|
| `voicestudio` | Best: local neural TTS, cloned voices, 646 languages | VoiceStudio app running (http://127.0.0.1:3900) |
| `edge` | Good, free Microsoft neural voices (incl. Hindi, Bengali, Tamil…) | Internet |
| `sapi` | Basic Windows voices | Nothing (offline) |
| `silent` | No sound, for testing animation | Nothing |
| `auto` (default) | Tries the ones above in that order | — |

**Using a cloned voice:** in VoiceStudio, open *Voice cloning*, add a reference recording and
save it as a voice profile. Restart StickVoice's page and pick the profile from the
*VoiceStudio voice* list. You can also put its id or name in `config.json` → `voice.voice`.

If you set `OMNIVOICE_API_KEY` on VoiceStudio, copy the key to `voice.voicestudio_api_key`.

## Smarter scripts (optional AI writer)

Without an AI writer, the built-in planner turns a **full script** into scenes and picks
actions, props and settings from keywords. A **short topic** only gets a generic outline,
so either paste your own script or turn on one of these:

- **Ollama (free, offline):** install from ollama.com, then run `ollama pull llama3.2`.
  StickVoice finds it automatically.
- **Gemini / OpenAI / any OpenAI-compatible API:** put your key in `config.json` → `llm.api_key`.
  A Gemini key works as-is (`gemini-2.5-flash`). For others, also set `llm.base_url` and `llm.model`.

## Styles (from the Stickman Video Director gallery)

Pick a style from the **Style gallery** in the web app, or use `--style <id>`:

| Code | `--style` id | Look | Best for |
|---|---|---|---|
| A1.1 | `a1-light` | Black line figures on pure white, 3 accent colours | Science, psychology, business explainers |
| A1.2 | `a1-dark` | White line figures on pure black | Suspense, conflict, emotion |
| A2.1 | `a2-tech` | Red beanie + yellow T-shirt, white studio, faint grid, cyan glow | Tools, tutorials, tech |
| A2.2 | `a2-story` | Same character in colourful cinematic scenes | Personal growth, motivation |
| A3 | `a3-cave` | Caves, hide tunics, clubs, campfires, paper texture | Workplace satire, fables, twists |
| A4 | `a4-cozy` | White round heads + slim white bodies in colour scenes | Relatable everyday stories |
| A5 | `a5-edo` | Edo Japan: kimono, topknot, katana, lanterns, Mount Fuji | History shorts |
| A5 | `a5-egypt` | Ancient Egypt: nemes, collars, pyramids, temples, the Nile | History shorts |
| A5 | `a5-rome` | Ancient Rome: legionary armour, togas, forum, camps, Colosseum | History shorts |
| A6 | `a6-amber` | Black-headed character in an orange hoodie, amber light, plum shadows, bold uppercase captions | Cinematic "what if" stories |
| B1 | `b1-notebook` | Near-white paper with faint grid, hand-drawn lettering | Long YouTube explainers |
| B2 | `b2-paper` | Warm paper, muted colour, ivory caption labels | Habits, everyday psychology |
| C1 | `c1-toon` | Full cartoon characters (curly hair, big eyes, T-shirt, jeans, sneakers), thick outlines, teal forest/city, white titles on maroon labels | Relatable meme shorts ("Boys be like…") |

Each style changes the characters' costumes and faces (A5 uses solid oval eyes and mitten hands,
A6 uses cream eye marks on a black head), how the 10 settings look (e.g. *city* = Edo street,
pyramids, the Roman forum or an amber night street), and the title and caption design.
The old names `notebook`, `classic`, `dark`, `pop`, `story` and `paper` still work.

## Director Mode: prompts for Kling, Flow, Runway

Besides rendering the video itself, StickVoice writes a **director's treatment** and one
standalone ~10-second video prompt per scene (`director_prompts.md`, saved with every render).
Each prompt repeats the style's full character anchor, the setting, timed beats
`[0-3s] [3-7s] [7-10s]`, the camera move, the exact narration and the negative constraints,
following the stickman-video-director rules. Paste them into Kling, Google Flow (Veo), Runway or
Luma to generate full-motion clips, then edit them in CapCut or Premiere.

- Web app: **Director prompts** button (copy or download).
- Command line: `.venv\Scripts\python -m stickvoice "your topic" --style a5-edo --director`

## AI video clips for free (open-source Wan 2.1 on Google Colab)

Kling itself is closed and paid. For a free alternative, StickVoice can turn your scenes into real
AI video clips with the open-source **Wan 2.1** model (Apache-2.0) on Google Colab's free GPU.
You don't need a graphics card on your PC.

1. Render a video as usual. Next to `video.mp4` you now also get `clips.json` (one visual prompt per scene)
   and `timeline.json` (scene timings).
2. Open https://colab.research.google.com → **File → Upload notebook** → `colab\wan_clips.ipynb`.
3. **Runtime → Change runtime type → T4 GPU**, then **Runtime → Run all**. Upload `clips.json` when asked.
   Each clip takes about 5–15 minutes. Finished clips are kept in Google Drive, so after a disconnect just run all again.
4. `clips.zip` downloads at the end. Put it in the same `output\<video>\` folder and drag that folder onto
   **`assemble_clips.bat`**, or run:

```bat
.venv\Scripts\python -m stickvoice --assemble output\<video>
```

You get `ai_video.mp4`: the AI clips fitted to each scene's length, with StickVoice's voice, sound effects and
captions (`--no-captions` to leave them out). Any scene without a clip uses the StickVoice animation instead.

## What the animation can do

- **27 actions:** talk, wave, point, present, think, idea, cheer, jump, clap, sad, shrug,
  surprised, scared, angry, facepalm, walk, run, sit, phone, read, write, dance, nod, bow, relax, stand,
  and **ride**: the character rides a motorbike (the friend sits on the back) while the background scrolls past
  with motion blur. Words like *bike, scooter, ride, बाइक, स्कूटर* pick it automatically.
- **56 animated props:** bulb, clock, chart, rocket, rain, money, globe, gear, trophy, brain, heart…
  (`--list` shows all). A prop pops in when its word is spoken.
- **10 settings:** plain, park, city, night, room, office, classroom, space, beach, stage.
- Lip-sync from the voice loudness, blinking, breathing, walk-ins, smooth pose blending,
  a second "friend" character, camera moves (zoom, pan, punch), crossfades, headline with
  hand-drawn underline, karaoke captions, and automatic sound effects.
- Shapes: 16:9 (1280×720), 9:16 (720×1280) and 1:1 (1080×1080). Renders about real time.

## Scene plan format

Every render saves `plan.json`. Edit it and re-render with `--plan`:

```json
{
  "title": "Pay yourself first", "style": "story", "ratio": "16:9",
  "scenes": [
    {"narration": "Spoken words for this scene.",
     "action": "idea", "mood": "happy", "setting": "park",
     "props": ["calendar", "coin"], "headline": "PAY YOURSELF FIRST",
     "enter": "left", "camera": "punch",
     "friend": {"action": "clap", "mood": "happy"},
     "position": "left", "duration": 6}
  ],
  "music": "C:/path/to/licensed-music.mp3"
}
```

`props` also accepts a path to your own PNG. `position`, `duration` and `music` are optional.

## Troubleshooting

- **"VoiceStudio not running"**: open the VoiceStudio app first and let it load a model.
  Check http://127.0.0.1:3900/v1/models in a browser.
- **No sound / silent video**: every voice engine failed. Check the log under the video;
  Edge needs internet, VoiceStudio needs the app open.
- **Hindi / other scripts**: set the narration language (e.g. Hindi) and pick a matching voice
  (VoiceStudio, or Edge `hi-IN-MadhurNeural`). Captions switch to the Windows *Nirmala UI* font
  automatically. If they still look wrong, set `video.captions` to `false` and use the `.srt` file.
- **Port 7860 in use**: change `web.port` in `config.json`.

## Licences

StickVoice code: MIT. Bundled fonts: SIL OFL. Bundled props: MIT (stickman-video-director).
VoiceStudio is AGPL-3.0 and is used as a separate app over HTTP, not bundled.
See `third_party/NOTICE.md`.
"# video-generate" 
