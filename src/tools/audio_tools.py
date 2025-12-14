from typing import Optional
from langchain.tools import tool
import requests
import os
from ..core.config import config
from ..core.logger import logger

from ..core.settings import DEFAULT_VOICE_ID

@tool
def generate_audio_tool(text: str, voice_id: Optional[str] = None) -> str:
    """
    Generate audio from text using ElevenLabs API.
    
    Args:
        text: The text content to convert to audio.
        voice_id: Optional voice ID to use. If not provided, uses default from config.
        
    Returns:
        Path to the saved audio file or error message.
    """
    api_key = config.ELEVEN_LABS_API_KEY
    if not api_key:
        return "Error: ElevenLabs API Key is missing."

    # Use default voice from settings if not provided
    voice_id = voice_id or DEFAULT_VOICE_ID
    
    # We need a valid voice_id. 
    # Let's try to fetch from config or use a hardcoded Vietnamese voice if possible, or standard US.
    # Since this is a VN real estate bot, a VN voice is preferred. 
    # But for now, let's keep it simple.
    
    # Note: Text-to-speech endpoint: https://api.elevenlabs.io/v1/text-to-speech/{voice_id}
    
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    
    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": api_key
    }
    
    data = {
        "text": text,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.5
        }
    }
    
    try:
        response = requests.post(url, json=data, headers=headers)
        if response.status_code == 200:
            # Save file
            import uuid
            filename = f"audio_{uuid.uuid4()}.mp3"
            save_dir = config.AUDIO_TARGET_DIR # "data/audio_generations"
            os.makedirs(save_dir, exist_ok=True)
            filepath = os.path.join(save_dir, filename)
            
            with open(filepath, "wb") as f:
                f.write(response.content)
                
            return f"Audio generated successfully: {filepath}"
        else:
            logger.error(f"ElevenLabs API Error: {response.text}")
            return f"Error generating audio: {response.status_code} - {response.text}"
    except Exception as e:
        logger.error(f"Exception in generate_audio_tool: {e}")
        return f"Error: {str(e)}"
