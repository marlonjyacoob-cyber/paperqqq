"""
Asset generation via Higgs (Claude-orchestrated).

This module is NOT called directly by Python — it is used by Claude
during a session to generate audio and images for each script segment
using the Higgs MCP tools, then saves the results to disk.

Workflow:
  1. Run: python main.py script --topic "..." --duration 60
     → writes output/<slug>/script.json

  2. Tell Claude: "generate assets for output/<slug>/script.json"
     → Claude calls Higgs per segment and saves files into
       output/<slug>/audio/segment_NNN.mp3
       output/<slug>/images/segment_NNN.png

  3. Run: python main.py assemble --work-dir output/<slug>/
     → stitches assets into output/<slug>/final.mp4

Models used by Claude:
  Audio : text2speech_v2_seed_speech  (clean long-form narration)
  Images: cinematic_studio_2_5        (cinematic 16:9 stills, up to 4K)
"""

import os
import requests
from pathlib import Path


def save_url_to_file(url: str, dest: str) -> str:
    """Downloads a media URL and saves it to dest. Returns dest."""
    Path(dest).parent.mkdir(parents=True, exist_ok=True)
    response = requests.get(url, timeout=60)
    response.raise_for_status()
    with open(dest, "wb") as f:
        f.write(response.content)
    return dest
