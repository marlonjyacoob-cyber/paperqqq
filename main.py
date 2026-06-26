"""
Faceless YouTube Video Generator

Usage
-----
Full pipeline (script + assets + assembly):
    python main.py run --topic "10 mind-blowing space facts" --duration 60

Or step by step:
    python main.py script   --topic "..." --duration 60
    python main.py assets   --work-dir output/<slug>/
    python main.py assemble --work-dir output/<slug>/
"""

import argparse
import json
import os
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


def load_or_generate_script(topic, duration, work_dir, force=False):
    script_path = os.path.join(work_dir, "script.json")
    if os.path.exists(script_path) and not force:
        print("📄 Loading existing script...")
        with open(script_path) as f:
            return json.load(f)
    print("📝 Generating script...")
    segments = generate_script(topic, duration)
    with open(script_path, "w") as f:
        json.dump(segments, f, indent=2)
    return segments


def cmd_script(args):
    slug = slugify(args.topic)
    work_dir = os.path.join(OUTPUT_DIR, slug)
    Path(work_dir).mkdir(parents=True, exist_ok=True)
    segments = load_or_generate_script(args.topic, args.duration, work_dir, args.force)
    print(f"\n✅ Script: {work_dir}/script.json")
    print(f"   {len(segments)} segments | ~{sum(s['duration'] for s in segments):.0f}s")


def cmd_assets(args):
    work_dir = args.work_dir.rstrip("/")
    script_path = os.path.join(work_dir, "script.json")
    with open(script_path) as f:
        segments = json.load(f)
    print(f"🎙️  Generating voiceovers ({len(segments)} segments)...")
    generate_voiceovers(segments, work_dir)
    print(f"\n🖼️  Generating images ({len(segments)} segments)...")
    generate_visuals(segments, work_dir)
    print("\n✅ Assets ready.")


def cmd_assemble(args):
    work_dir = args.work_dir.rstrip("/")
    audio_files = sorted(Path(work_dir, "audio").glob("segment_*.mp3"))
    image_files = sorted(Path(work_dir, "images").glob("segment_*.png"))

    if not audio_files or not image_files:
        print("Error: audio/ or images/ folder is empty. Run assets step first.")
        return

    output_path = os.path.join(work_dir, "final.mp4")
    print(f"🎬 Assembling {len(audio_files)} clips...")
    assemble_video([str(p) for p in image_files], [str(p) for p in audio_files], output_path, work_dir)
    print(f"\n✅ Video ready: {output_path}")


def cmd_run(args):
    slug = slugify(args.topic)
    work_dir = os.path.join(OUTPUT_DIR, slug)
    Path(work_dir).mkdir(parents=True, exist_ok=True)

    print(f"\n{'=' * 55}")
    print(f"  Faceless YouTube Video Pipeline")
    print(f"  Topic : {args.topic}")
    print(f"  Target: ~{args.duration}s")
    print(f"{'=' * 55}\n")

    segments = load_or_generate_script(args.topic, args.duration, work_dir)
    print(f"   {len(segments)} segments\n")

    print("🎙️  Generating voiceovers...")
    generate_voiceovers(segments, work_dir)

    print("\n🖼️  Generating images...")
    generate_visuals(segments, work_dir)

    output_path = os.path.join(work_dir, "final.mp4")
    print(f"\n🎬 Assembling video...")
    assemble_video(
        sorted(str(p) for p in Path(work_dir, "images").glob("segment_*.png")),
        sorted(str(p) for p in Path(work_dir, "audio").glob("segment_*.mp3")),
        output_path,
        work_dir,
    )
    print(f"\n✅ Done! → {output_path}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Faceless YouTube Video Generator")
    sub = parser.add_subparsers(dest="command", required=True)

    p_run = sub.add_parser("run", help="Full pipeline end-to-end")
    p_run.add_argument("--topic", required=True)
    p_run.add_argument("--duration", type=int, default=60)
    p_run.set_defaults(func=cmd_run)

    p_script = sub.add_parser("script", help="Generate script only")
    p_script.add_argument("--topic", required=True)
    p_script.add_argument("--duration", type=int, default=60)
    p_script.add_argument("--force", action="store_true")
    p_script.set_defaults(func=cmd_script)

    p_assets = sub.add_parser("assets", help="Generate voiceovers + images from script")
    p_assets.add_argument("--work-dir", required=True)
    p_assets.set_defaults(func=cmd_assets)

    p_assemble = sub.add_parser("assemble", help="Assemble assets into MP4")
    p_assemble.add_argument("--work-dir", required=True)
    p_assemble.set_defaults(func=cmd_assemble)

    args = parser.parse_args()
    args.func(args)
