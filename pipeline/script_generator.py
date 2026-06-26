import anthropic
import json
from config import ANTHROPIC_API_KEY


def generate_script(topic: str, duration_seconds: int = 60) -> list[dict]:
    """
    Returns a list of segments:
    [{"text": "...", "image_prompt": "...", "duration": 5.0}, ...]
    """
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    word_count = int(duration_seconds * 2.5)  # ~150 wpm

    prompt = f"""You are a scriptwriter for a faceless YouTube channel that covers fascinating facts and news.

Topic: {topic}
Target duration: {duration_seconds} seconds (~{word_count} words)

Write a script broken into short segments (5-8 seconds each). Return ONLY valid JSON — an array of objects with these keys:
- "text": the narration text for this segment
- "image_prompt": a vivid image generation prompt that visualizes this segment (for DALL-E/Stable Diffusion)
- "duration": estimated seconds to read this segment aloud (float)

Keep each segment punchy and engaging. Hook the viewer in the first segment. End with a call to action.
Return ONLY the JSON array, no other text."""

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2048,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = message.content[0].text.strip()
    # strip markdown code fences if present
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    segments = json.loads(raw)
    return segments
