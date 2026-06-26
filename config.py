import os
from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")  # for DALL-E image fallback

IMAGE_WIDTH = 1920
IMAGE_HEIGHT = 1080
FPS = 24
FONT_SIZE = 48

OUTPUT_DIR = "output"
