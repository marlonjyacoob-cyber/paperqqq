"""
Offline TTS using espeak-ng (no network required).
Outputs MP3 via ffmpeg WAV→MP3 conversion.
"""

import os
import subprocess
from pathlib import Path
import imageio_ffmpeg

FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()

# en-us with a slightly slower speed and lower pitch = authoritative narrator feel
ESPEAK_VOICE = "en-us"
ESPEAK_SPEED = 145   # words per minute (default 175 is too fast)
ESPEAK_PITCH = 32    # 0-99, lower = deeper voice


def text_to_speech(text: str, output_path: str) -> str:
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    wav_path = output_path.replace(".mp3", ".wav")

    subprocess.run(
        [
            "espeak-ng",
            "-v", ESPEAK_VOICE,
            "-s", str(ESPEAK_SPEED),
            "-p", str(ESPEAK_PITCH),
            "-g", "8",           # gap between words (ms)
            text,
            "-w", wav_path,
        ],
        check=True,
        capture_output=True,
    )

    # Convert WAV → MP3 with ffmpeg
    subprocess.run(
        [FFMPEG, "-y", "-i", wav_path, "-b:a", "192k", output_path],
        check=True,
        capture_output=True,
    )
    os.remove(wav_path)
    return output_path


def generate_voiceovers(segments: list[dict], work_dir: str) -> list[str]:
    audio_paths = []
    for i, seg in enumerate(segments):
        path = os.path.join(work_dir, "audio", f"segment_{i:03d}.mp3")
        print(f"  🎙️  Voiceover {i + 1}/{len(segments)}...")
        text_to_speech(seg["text"], path)
        audio_paths.append(path)
    return audio_paths
