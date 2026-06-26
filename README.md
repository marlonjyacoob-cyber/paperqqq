# Faceless YouTube Video Generator

AI-powered pipeline for faceless YouTube videos (news/facts format).

## Pipeline

| Step | Who does it | What happens |
|------|-------------|-------------|
| 1. Script | Python (Claude API) | Generates segmented narration + image prompts |
| 2. Assets | Claude + Higgs | Generates voiceover MP3s and cinematic images per segment |
| 3. Assembly | Python (FFmpeg) | Stitches audio + images into final MP4 with Ken Burns effect |

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env   # add ANTHROPIC_API_KEY
```

FFmpeg must be installed: `sudo apt install ffmpeg`

## Usage

**Step 1 — generate script**
```bash
python main.py script --topic "10 mind-blowing facts about black holes" --duration 90
```
Writes `output/<slug>/script.json`

**Step 2 — generate assets**  
Tell Claude in your session:
> "generate assets for output/10-mind-blowing-facts-about-black-holes/script.json"

Claude calls Higgs (ElevenLabs TTS + Cinematic Studio images) and saves files to `output/<slug>/audio/` and `output/<slug>/images/`.

**Step 3 — assemble**
```bash
python main.py assemble --work-dir output/10-mind-blowing-facts-about-black-holes/
```
Outputs `output/<slug>/final.mp4`

## Models used (via Higgs)

- **Audio**: `text2speech_v2_seed_speech` — clean, stable long-form narration
- **Images**: `cinematic_studio_2_5` — cinematic 16:9 stills up to 4K
