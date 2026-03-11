# TheVoice: Experimental Autonomous Streamer Bot (Local Prototype)

This project is a **local-only** prototype for an autonomous “streamer bot” performance loop.  
It intentionally excludes Twitch/YouTube/OBS/RTMP integration for now.

## What it does

Per cycle, the bot can:
1. Generate a short surreal monologue with an LLM abstraction.
2. Convert text to speech (local `pyttsx3`, chorus-style `collective` voice using gTTS/ElevenLabs, with robust tone fallback).
3. Render cellular automata visuals (Conway's Game of Life GIF).
4. Generate Strudel pattern code and attempt browser control via Playwright.
5. Slow an existing audio file by 100x (high-quality path with `librosa`, fallback via `pydub`).
6. Save artifacts and summaries into timestamped folders.

## Project structure

```text
app/
  __init__.py
  main.py
  config.py
  orchestrator.py
  llm.py
  tts.py
  visuals.py
  strudel_client.py
  slow_audio.py
  utils.py
assets/
  audio/
  output/
tests/
requirements.txt
.env.example
README.md
```

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
# optional but recommended for strudel automation:
playwright install chromium
```

Copy environment template:

```bash
cp .env.example .env
```

Export variables manually or with your preferred dotenv workflow.

## Environment variables

| Variable | Purpose | Default |
|---|---|---|
| `BOT_OUTPUT_ROOT` | output directory | `assets/output` |
| `BOT_LOOP_INTERVAL_SECONDS` | pause between cycles | `12` |
| `BOT_CYCLES` | number of cycles to run | `1` |
| `BOT_ENABLE_LLM_SPEECH` | enable monologue + TTS | `true` |
| `BOT_ENABLE_VISUALS` | enable automata GIF output | `true` |
| `BOT_ENABLE_STRUDEL` | enable Strudel browser automation | `true` |
| `BOT_ENABLE_SLOW_AUDIO` | enable slow audio module | `true` |
| `BOT_PERSONA_PROMPT` | persona/system style prompt | uncanny host prompt |
| `BOT_LLM_PROVIDER` | `openai` or fallback template | `openai` |
| `OPENAI_API_KEY` | OpenAI key | unset |
| `BOT_OPENAI_MODEL` | OpenAI model name | `gpt-4o-mini` |
| `BOT_TTS_PROVIDER` | `pyttsx3`, `collective`, or fallback | `pyttsx3` |
| `BOT_TTS_COLLECTIVE_BASE_PROVIDER` | base layer provider (`gtts`/`elevenlabs`) | `gtts` |
| `BOT_TTS_COLLECTIVE_BASE_GTTS_TLD` | gTTS accent domain for base layer | `co.uk` |
| `BOT_TTS_COLLECTIVE_ELEVENLABS_VOICE_ID` | optional base ElevenLabs voice id | unset |
| `BOT_TTS_COLLECTIVE_ELEVENLABS_MODEL_ID` | optional base ElevenLabs model | `eleven_multilingual_v2` |
| `BOT_TTS_VOICE` | optional local voice id | unset |
| `BOT_TTS_RATE` | TTS speed | `165` |
| `BOT_AUTOMATA_WIDTH` | grid width | `128` |
| `BOT_AUTOMATA_HEIGHT` | grid height | `96` |
| `BOT_AUTOMATA_CELL_SIZE` | render scale | `6` |
| `BOT_AUTOMATA_STEPS` | generations per cycle | `36` |
| `BOT_AUTOMATA_SEED_DENSITY` | initial alive density | `0.22` |
| `BOT_AUTOMATA_FPS` | GIF frame rate | `12` |
| `BOT_STRUDEL_URL` | Strudel URL | `https://strudel.cc` |
| `BOT_STRUDEL_HEADLESS` | browser mode | `true` |
| `BOT_SLOW_AUDIO_SOURCE` | source WAV/MP3 path | `assets/audio/source.wav` |
| `BOT_SLOW_AUDIO_FACTOR` | slow amount | `100` |

## Run the demo

```bash
python -m app.main
```

Expected behavior:
- Initializes modules.
- Runs configured cycles.
- Produces monologue text + TTS audio.
- Exports automata GIF and metadata.
- Produces a Strudel pattern and attempts to inject/play it.
- Processes slowed audio if source file exists.
- Writes per-cycle `summary.json`, plus `latest_session_summary.json` and `.html`.

## Testing

```bash
pytest -q
```

## Known limitations

- **No website streaming integration** is implemented by design.
- Strudel audio capture is not directly implemented (automation focuses on opening page, setting pattern, and triggering play). Browser/system capture can be added later as a separate backend.
- `pyttsx3` output quality depends on local OS voices.
- `collective` voice mode depends on `ffmpeg` for `pydub` decoding/encoding, and network access for gTTS/ElevenLabs.
- 100x slow audio via fallback changes pitch; `librosa` path may still have artifacts at extreme stretch factors.

## Future work

- Pluggable audio mixer for speech + music buses.
- Higher-quality TTS backends (coqui/edge/piper adapters).
- More automata rules and shader-style color pipelines.
- Reliable Strudel recording backend (virtual loopback device + ffmpeg capture worker).
- Runtime control UI (still local-only).

## Scope reminder

This repository currently focuses on **local generation, orchestration, and preview artifacts**, not live-stream delivery.
