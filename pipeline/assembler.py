import os
import subprocess
from pathlib import Path


def get_audio_duration(audio_path: str) -> float:
    """Returns duration of an audio file in seconds using ffprobe."""
    result = subprocess.run(
        [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            audio_path,
        ],
        capture_output=True,
        text=True,
    )
    return float(result.stdout.strip())


def assemble_video(
    image_paths: list[str],
    audio_paths: list[str],
    output_path: str,
    work_dir: str,
) -> str:
    """
    Combines each image+audio pair into a clip, then concatenates all clips
    into a final MP4. Returns output_path.
    """
    clip_paths = []
    clips_dir = os.path.join(work_dir, "clips")
    Path(clips_dir).mkdir(parents=True, exist_ok=True)

    for i, (img, aud) in enumerate(zip(image_paths, audio_paths)):
        duration = get_audio_duration(aud)
        clip_path = os.path.join(clips_dir, f"clip_{i:03d}.mp4")

        # zoom-pan (Ken Burns) effect: slow zoom from 1.0 to 1.05 over the clip
        vf = (
            f"scale=1920:1080:force_original_aspect_ratio=increase,"
            f"crop=1920:1080,"
            f"zoompan=z='min(zoom+0.001,1.05)':d={int(duration * 25)}:s=1920x1080:fps=25"
        )

        subprocess.run(
            [
                "ffmpeg", "-y",
                "-loop", "1", "-i", img,
                "-i", aud,
                "-vf", vf,
                "-c:v", "libx264", "-tune", "stillimage",
                "-c:a", "aac", "-b:a", "192k",
                "-pix_fmt", "yuv420p",
                "-shortest",
                clip_path,
            ],
            check=True,
            capture_output=True,
        )
        clip_paths.append(clip_path)
        print(f"  🎬 Assembled clip {i + 1}/{len(image_paths)}")

    # write concat list
    concat_list = os.path.join(work_dir, "concat.txt")
    with open(concat_list, "w") as f:
        for cp in clip_paths:
            f.write(f"file '{os.path.abspath(cp)}'\n")

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            "ffmpeg", "-y",
            "-f", "concat", "-safe", "0",
            "-i", concat_list,
            "-c", "copy",
            output_path,
        ],
        check=True,
        capture_output=True,
    )
    return output_path
