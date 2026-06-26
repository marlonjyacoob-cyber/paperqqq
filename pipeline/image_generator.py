import os
import requests
from pathlib import Path
from openai import OpenAI
from config import OPENAI_API_KEY, IMAGE_WIDTH, IMAGE_HEIGHT

client = OpenAI(api_key=OPENAI_API_KEY)


def generate_image(prompt: str, output_path: str) -> str:
    """Generates a 1792x1024 image via DALL-E 3 and saves it. Returns output_path."""
    enhanced = (
        f"Cinematic, photorealistic, high-detail YouTube thumbnail style: {prompt}. "
        "16:9 aspect ratio, dramatic lighting, no text."
    )
    response = client.images.generate(
        model="dall-e-3",
        prompt=enhanced,
        size="1792x1024",
        quality="standard",
        n=1,
    )
    image_url = response.data[0].url
    img_data = requests.get(image_url).content

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "wb") as f:
        f.write(img_data)
    return output_path


def generate_visuals(segments: list[dict], work_dir: str) -> list[str]:
    """Generates one image per segment. Returns list of image file paths."""
    image_paths = []
    for i, seg in enumerate(segments):
        path = os.path.join(work_dir, "images", f"segment_{i:03d}.png")
        print(f"  🖼️  Generating image for segment {i + 1}/{len(segments)}...")
        generate_image(seg["image_prompt"], path)
        image_paths.append(path)
    return image_paths
