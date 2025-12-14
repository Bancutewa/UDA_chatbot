from langchain.tools import tool
import os
import uuid
import google.generativeai as genai
from ..core.logger import logger
from ..core.config import config

# Configure GenAI with API Key
if config.GEMINI_API_KEY:
    genai.configure(api_key=config.GEMINI_API_KEY)

@tool
def generate_image_tool(prompt: str) -> str:
    """
    Generate an image based on a text prompt using Google's Imagen 3 model via REST API.
    The image is saved locally and the file path is returned.
    
    Args:
        prompt: Description of the image to generate.
        
    Returns:
        Path to the generated image file.
    """
    logger.info(f"Generating image for prompt: {prompt}")
    
    try:
        if not config.GEMINI_API_KEY:
             return "Error: GEMINI_API_KEY is missing. Cannot generate image."

        # Imagen 4.0 REST API endpoint (Vertex AI/Gemini API)
        # Note: Using the generativelanguage.googleapis.com endpoint
        url = f"https://generativelanguage.googleapis.com/v1beta/models/imagen-4.0-generate-001:predict?key={config.GEMINI_API_KEY}"
        
        headers = {
            "Content-Type": "application/json"
        }
        
        payload = {
            "instances": [
                {
                    "prompt": prompt
                }
            ],
            "parameters": {
                "sampleCount": 1,
                "aspectRatio": "1:1"
            }
        }
        
        import requests
        import base64
        
        response = requests.post(url, headers=headers, json=payload)
        
        if response.status_code != 200:
            logger.error(f"Imagen API Error: {response.text}")
            return f"Error from API: {response.status_code} - {response.text}"
            
        result = response.json()
        
        # Parse response
        # Structure should be predictions[0].bytesBase64Encoded or similar
        # Actual structure for Imagen on Gemini API:
        # { "predictions": [ { "bytesBase64Encoded": "..." } ] }
        
        if "predictions" not in result or not result["predictions"]:
            return "Error: No image data in response."
            
        b64_image = result["predictions"][0].get("bytesBase64Encoded")
        
        if not b64_image:
             # Try alternate structure if specific to different serving
             return f"Error: Unexpected response format: {result.keys()}"

        # Create directory if it doesn't exist
        output_dir = "data/generated_images"
        os.makedirs(output_dir, exist_ok=True)
        
        # Save image
        image_id = str(uuid.uuid4())
        file_path = f"{output_dir}/{image_id}.png"
        
        with open(file_path, "wb") as f:
            f.write(base64.b64decode(b64_image))
            
        logger.info(f"Image saved to {file_path}")
        
        return f"Image generated successfully: {file_path}"
        
    except Exception as e:
        logger.error(f"Image generation failed: {e}")
        return f"Error creating image: {str(e)}"
