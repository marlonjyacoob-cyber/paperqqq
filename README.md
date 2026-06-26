# Faceless YouTube Video Generator

Fully automated pipeline for faceless YouTube videos (news/facts format).  
**No paid API keys required** — uses free TTS and free image generation.

## Pipeline

| Step | Tool | What happens |
|------|------|-------------|
| Script | Claude API (`anthropic`) | Generates segmented narration + image prompts |
| Voiceover | `edge-tts` (Microsoft Neural, free) | Converts each segment to MP3 |
| Images | Pollinations.ai (free, no key) | Generates cinematic 1920×1080 images |
| Assembly | FFmpeg | Stitches everything into a final MP4 with Ken Burns zoom |

## Setup

```bash
pip install -r requirements.txt
# FFmpeg must be installed:
sudo apt install ffmpeg   # Linux
brew install ffmpeg       # Mac
```

Only needed for script generation (optional if you write scripts manually):
```bash
cp .env.example .env  # add ANTHROPIC_API_KEY
```

## Usage

**One command — full pipeline:**
```bash
python main.py run --topic "10 mind-blowing facts about black holes" --duration 90
```

**Or step by step:**
```bash
python main.py script  --topic "..." --duration 90
python main.py assets  --work-dir output/<slug>/
python main.py assemble --work-dir output/<slug>/
```

Output: `output/<slug>/final.mp4` — ready to upload to YouTube.
