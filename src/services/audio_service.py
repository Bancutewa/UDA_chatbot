"""
Audio Service - Handles Speech-to-Text configuration and processing
"""
import google.generativeai as genai
from ..core.config import config
from ..core.logger import logger

class AudioService:
    """Service for handling audio transcription using Google Gemini"""
    
    def __init__(self):
        self._setup_genai()
        
    def _setup_genai(self):
        """Configure Google Generative AI"""
        if config.GEMINI_API_KEY:
            genai.configure(api_key=config.GEMINI_API_KEY)
        else:
            logger.warning("GEMINI_API_KEY not found. Audio transcription will not work.")

    def transcribe(self, audio_data) -> str:
        """
        Transcribe audio data to text (Speech-to-Text)
        
        Args:
            audio_data: The audio bytes or file-like object
            
        Returns:
            str: Transcribed text
        """
        try:
            model = genai.GenerativeModel("gemini-2.5-flash")
            
            prompt = """
            Listen to this audio and write down what is said. 
            The audio is primarily in Vietnamese.
            Output ONLY the transcribed text. Do not add any description or extra words.
            """
            
            # Read bytes if it's a file-like object from Streamlit
            if hasattr(audio_data, 'read'):
                audio_bytes = audio_data.read()
            else:
                audio_bytes = audio_data

            response = model.generate_content([
                prompt,
                {
                    "mime_type": "audio/mp3",
                    "data": audio_bytes
                }
            ])
            
            return response.text.strip()
            
        except Exception as e:
            logger.error(f"Error transcribing audio: {e}")
            return ""

# Singleton instance
audio_service = AudioService()
