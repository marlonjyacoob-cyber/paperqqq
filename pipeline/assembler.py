import os
import subprocess
from pathlib import Path
import imageio_ffmpeg

FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()


def get_audio_duration(audio_path: str) -> float:
    """Returns duration of an audio file in seconds using ffmpeg stderr output."""
    result = subprocess.run(
        [FFMPEG, "-i", audio_path],
        capture_output=True,
        text=True,
    )
    # ffmpeg prints "Duration: HH:MM:SS.xx" to stderr even on error
    for line in result.stderr.splitlines():
        if "Duration:" in line:
            dur_str = line.split("Duration:")[1].split(",")[0].strip()
            h, m, s = dur_str.split(":")
            return int(h) * 3600 + int(m) * 60 + float(s)
    return 5.0  # fallback


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
                FFMPEG, "-y",
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
            FFMPEG, "-y",
            "-f", "concat", "-safe", "0",
            "-i", concat_list,
            "-c", "copy",
            output_path,
        ],
        check=True,
        capture_output=True,
    )
    return output_path
