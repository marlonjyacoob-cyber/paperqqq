# Faceless YouTube Video Generator

Automated pipeline for creating AI-powered faceless YouTube videos (news/facts format).

## Pipeline

1. **Script** — Claude generates a structured narration script from a topic
2. **Voiceover** — TTS converts the script to audio
3. **Visuals** — AI-generated images synced to script segments
4. **Assembly** — FFmpeg stitches audio + images into a final MP4

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env  # fill in your API keys
```

## Usage

```bash
python main.py --topic "10 mind-blowing space facts" --duration 60
```

## Output

`output/<topic-slug>/final.mp4` — ready to upload to YouTube
