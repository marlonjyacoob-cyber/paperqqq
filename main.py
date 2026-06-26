import argparse
import os
import json
import re
from pathlib import Path

from pipeline.script_generator import generate_script
from pipeline.voice_generator import generate_voiceovers
from pipeline.image_generator import generate_visuals
from pipeline.assembler import assemble_video
from config import OUTPUT_DIR


def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    return re.sub(r"[\s_-]+", "-", text)[:60]


def run_pipeline(topic: str, duration: int):
    slug = slugify(topic)
    work_dir = os.path.join(OUTPUT_DIR, slug)
    Path(work_dir).mkdir(parents=True, exist_ok=True)

    print(f"\n{'=' * 55}")
    print(f"  Faceless YouTube Video Pipeline")
    print(f"  Topic: {topic}")
    print(f"  Duration: ~{duration}s")
    print(f"{'=' * 55}\n")

    # 1. Script
    script_path = os.path.join(work_dir, "script.json")
    if os.path.exists(script_path):
        print("📄 Loading cached script...")
        with open(script_path) as f:
            segments = json.load(f)
    else:
        print("📝 Generating script...")
        segments = generate_script(topic, duration)
        with open(script_path, "w") as f:
            json.dump(segments, f, indent=2)
    print(f"   {len(segments)} segments generated.\n")

    # 2. Voiceover
    print("🎙️  Generating voiceovers...")
    audio_paths = generate_voiceovers(segments, work_dir)
    print()

    # 3. Visuals
    print("🖼️  Generating images...")
    image_paths = generate_visuals(segments, work_dir)
    print()

    # 4. Assembly
    output_path = os.path.join(work_dir, "final.mp4")
    print("🎬 Assembling video...")
    assemble_video(image_paths, audio_paths, output_path, work_dir)

    print(f"\n✅ Done! Video saved to: {output_path}\n")
    return output_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Faceless YouTube Video Generator")
    parser.add_argument("--topic", required=True, help="Video topic or title")
    parser.add_argument("--duration", type=int, default=60, help="Target duration in seconds")
    args = parser.parse_args()

    run_pipeline(args.topic, args.duration)
