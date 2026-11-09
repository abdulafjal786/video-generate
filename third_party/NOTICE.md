# Third-party notices

## stickman-video-director (MIT)
https://github.com/kaomei/stickman-video-director

StickVoice re-implements its visual styles (A1 Classic, A2 Modern Pop, A4 Cozy story,
B1 Minimal hand-drawn, B2 Colourful paper) as a procedural renderer, and bundles from it:

- `assets/fonts/Caveat.ttf`, `assets/fonts/NotoSans.ttf` — SIL Open Font License
  (see `assets/fonts/OFL-*.txt`)
- `assets/props/*.png` — original hand-drawn B1 prop drawings, MIT
  (see `stickman-video-director-LICENSE.txt`; some derive from Lucide icons, see `LUCIDE-LICENSE.txt`)

## VoiceStudio (AGPL-3.0)
https://github.com/debpalash/voicestudio

VoiceStudio is **not bundled**. StickVoice talks to the VoiceStudio app you install
yourself, over its local OpenAI-compatible HTTP API (`POST /v1/audio/speech`,
`GET /v1/audio/voices`). No VoiceStudio source code is copied into this project.
