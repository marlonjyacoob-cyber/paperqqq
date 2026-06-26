import os
import requests
from pathlib import Path
from config import ELEVENLABS_API_KEY

VOICE_ID = "21m00Tcm4TlvDq8ikWAM"  # Rachel — clear, neutral narrator voice
TTS_URL = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"


def text_to_speech(text: str, output_path: str) -> str:
    """Converts text to an MP3 file via ElevenLabs. Returns output_path."""
    headers = {
        "xi-api-key": ELEVENLABS_API_KEY,
        "Content-Type": "application/json",
    }
    payload = {
        "text": text,
        "model_id": "eleven_monolingual_v1",
        "voice_settings": {"stability": 0.5, "similarity_boost": 0.75},
    }
    response = requests.post(TTS_URL, json=payload, headers=headers)
    response.raise_for_status()

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "wb") as f:
        f.write(response.content)
    return output_path


def generate_voiceovers(segments: list[dict], work_dir: str) -> list[str]:
    """Generates one MP3 per segment. Returns list of audio file paths."""
    audio_paths = []
    for i, seg in enumerate(segments):
        path = os.path.join(work_dir, "audio", f"segment_{i:03d}.mp3")
        print(f"  🎙️  Generating audio for segment {i + 1}/{len(segments)}...")
        text_to_speech(seg["text"], path)
        audio_paths.append(path)
    return audio_paths
