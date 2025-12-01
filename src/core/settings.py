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

# Default values
DEFAULT_VOICE_ID = AUDIO_VOICE_OPTIONS["Nguyễn Ngân (Female, Vietnamese)"]
DEFAULT_AUDIO_MODEL = "eleven_turbo_v2_5"

# --- CHATBOT SETTINGS ---

# Understanding Layer
PRICE_RANGE_TOLERANCE = 0.05  # For "tầm X tỷ" queries
NLU_CONFIDENCE_THRESHOLD = 0.7  # Threshold for ASK_REPHRASE

# Decision Layer
MIN_SEARCH_CRITERIA = 1  # Minimum criteria to allow search

# Response Layer
MAX_SEARCH_RESULTS = 5  # Max apartments to return
MAX_CONTEXT_MESSAGES = 5  # Context history size

# Slot Validation
MIN_VALID_PRICE = 100_000_000  # 100 million VND
MAX_VALID_PRICE = 100_000_000_000  # 100 billion VND
MIN_BEDROOMS = 0
MAX_BEDROOMS = 10
MIN_AREA = 10  # m²
MAX_AREA = 10000  # m²

# Preprocessing Patterns
LOCATION_SHORTCUTS = {
    # No longer needed as we removed khu_vuc, but keeping for reference or future use
}

PROJECT_NAME_MAPPING = {
    "q7 riverside": "Q7Riverside",
    "riverside quận 7": "Q7Riverside",
    "q7": "Q7Riverside",
    "riverside": "Q7Riverside",
    "river panorama": "RiverPanorama",
    "panorama": "RiverPanorama",
    "river": "RiverPanorama",
}

TOWER_SHORTCUTS = {
    "tòa m1": "M1",
    "toa m1": "M1",
    "tower m1": "M1",
    "tòa rp1": "RP1",
    "toa rp1": "RP1",
    "tower rp1": "RP1",
}

DIRECTION_SHORTCUTS = {
    "đn": "Đông Nam", "đông nam": "Đông Nam",
    "tb": "Tây Bắc", "tây bắc": "Tây Bắc",
    "đb": "Đông Bắc", "đông bắc": "Đông Bắc",
    "tn": "Tây Nam", "tây nam": "Tây Nam",
    "đ": "Đông", "đông": "Đông",
    "t": "Tây", "tây": "Tây",
    "n": "Nam", "nam": "Nam",
    "b": "Bắc", "bắc": "Bắc",
}

FURNITURE_MAPPING = {
    "full": "Full", "đầy đủ": "Full", "có nội thất": "Full",
    "cơ bản": "Cơ Bản", "nhà trống": "Trống", "không nội thất": "Trống"
}

PRICE_PATTERNS = {
    "tỷ": 1_000_000_000,
    "ty": 1_000_000_000,
    "triệu": 1_000_000,
    "tr": 1_000_000,
    "nghìn": 1_000,
    "k": 1_000,
}
