"""
Faceless YouTube Video Generator

Usage
-----
Step 1 — generate script (Python):
    python main.py script --topic "10 mind-blowing space facts" --duration 60

Step 2 — generate audio + images (Claude via Higgs):
    Tell Claude: "generate assets for output/<slug>/script.json"

Step 3 — assemble final video (Python):
    python main.py assemble --work-dir output/<slug>/
"""

import argparse
import json
import os
import re
from pathlib import Path

from pipeline.script_generator import generate_script
from pipeline.assembler import assemble_video
from config import OUTPUT_DIR


def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    return re.sub(r"[\s_-]+", "-", text)[:60]


def cmd_script(args):
    slug = slugify(args.topic)
    work_dir = os.path.join(OUTPUT_DIR, slug)
    Path(work_dir).mkdir(parents=True, exist_ok=True)

    script_path = os.path.join(work_dir, "script.json")
    if os.path.exists(script_path) and not args.force:
        print(f"Script already exists: {script_path}  (use --force to regenerate)")
        with open(script_path) as f:
            segments = json.load(f)
    else:
        print(f"Generating script for: {args.topic}")
        segments = generate_script(args.topic, args.duration)
        with open(script_path, "w") as f:
            json.dump(segments, f, indent=2)

    print(f"\n✅ Script saved: {script_path}")
    print(f"   {len(segments)} segments | ~{sum(s['duration'] for s in segments):.0f}s total")
    print(f"\nNext: tell Claude → \"generate assets for {script_path}\"")


def cmd_assemble(args):
    work_dir = args.work_dir.rstrip("/")
    audio_dir = os.path.join(work_dir, "audio")
    image_dir = os.path.join(work_dir, "images")

    audio_files = sorted(Path(audio_dir).glob("segment_*.mp3")) if os.path.isdir(audio_dir) else []
    image_files = sorted(Path(image_dir).glob("segment_*.png")) if os.path.isdir(image_dir) else []

    if not audio_files or not image_files:
        print("Error: audio/ or images/ folder is empty.")
        print("Run asset generation with Claude first (Step 2).")
        return

    if len(audio_files) != len(image_files):
        print(f"Warning: {len(audio_files)} audio files vs {len(image_files)} images — counts differ.")

    output_path = os.path.join(work_dir, "final.mp4")
    print(f"Assembling {len(audio_files)} segments...")
    assemble_video(
        [str(p) for p in image_files],
        [str(p) for p in audio_files],
        output_path,
        work_dir,
    )
    print(f"\n✅ Video ready: {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Faceless YouTube Video Generator")
    sub = parser.add_subparsers(dest="command", required=True)

    p_script = sub.add_parser("script", help="Generate narration script")
    p_script.add_argument("--topic", required=True)
    p_script.add_argument("--duration", type=int, default=60)
    p_script.add_argument("--force", action="store_true")
    p_script.set_defaults(func=cmd_script)

    p_assemble = sub.add_parser("assemble", help="Assemble audio + images into MP4")
    p_assemble.add_argument("--work-dir", required=True)
    p_assemble.set_defaults(func=cmd_assemble)

    args = parser.parse_args()
    args.func(args)
