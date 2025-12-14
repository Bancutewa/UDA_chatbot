from langchain.tools import tool
import requests
from ..core.logger import logger

@tool
def generate_image_tool(prompt: str) -> str:
    """
    Generate an image based on a text prompt using Pollinations AI.
    
    Args:
        prompt: Description of the image to generate.
        
    Returns:
        URL of the generated image.
    """
    # Pollinations AI usage: https://image.pollinations.ai/prompt/{encoded_prompt}
    
    logger.info(f"Generating image for prompt: {prompt}")
    
    # Simple URL construction
    # We can encode the prompt to be safe
    import urllib.parse
    encoded_prompt = urllib.parse.quote(prompt)
    image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}"
    
    # We could try to fetch it to ensure it works, or just return the URL directly.
    # Returning the URL is usually enough for the UI to render.
    
    return f"Image generated: {image_url}"
