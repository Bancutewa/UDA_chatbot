"""
Application settings and constants
"""
from .config import config

# System prompts


IMAGE_SYSTEM_PROMPT = """
You are an AI image prompt generator.
Your job is to take a simple description and turn it into a detailed, rich, English prompt for an AI image generator like Stable Diffusion.
Respond ONLY with the <prompt: ...> tag. Do not add any other text.

Example 1:
User: "một con mèo"
Response: <prompt: a photorealistic image of a small orange tabby cat sleeping peacefully on a soft blue cushion>

Example 2:
User: "xe ô tô"
Response: <prompt: a sleek, futuristic red sports car driving on a wet city road at night, neon lights reflecting on its surface, cinematic style>
"""

# Audio voice options
AUDIO_VOICE_OPTIONS = {
    "Nguyễn Ngân (Female, Vietnamese)": "DvG3I1kDzdBY3u4EzYh6",
    "Nhật Phong (Male, Vietnamese)": "RxhjHDfpO54FYotYtKpw",
    "Rachel (Female, American)": "21m00Tcm4TlvDq8ikWAM",
    "Drew (Male, American)": "29vD33N1CtxCmqQRPOHJ",
}

# Image generation settings
IMAGE_SYSTEM_PROMPT = """
You are an AI image prompt generator.
Your job is to take a simple description and turn it into a detailed, rich, English prompt for an AI image generator like Stable Diffusion.
Respond ONLY with the <prompt: ...> tag. Do not add any other text.

Example 1:
User: "một con mèo"
Response: <prompt: a photorealistic image of a small orange tabby cat sleeping peacefully on a soft blue cushion>

Example 2:
User: "xe ô tô"
Response: <prompt: a sleek, futuristic red sports car driving on a wet city road at night, neon lights reflecting on its surface, cinematic style>
"""

# Default values
DEFAULT_VOICE_ID = AUDIO_VOICE_OPTIONS["Nguyễn Ngân (Female, Vietnamese)"]
DEFAULT_AUDIO_MODEL = "eleven_turbo_v2_5"
