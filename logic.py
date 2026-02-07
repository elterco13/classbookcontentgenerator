from google import genai
from google.genai import types
import json
import os
from typing import List, Dict, Any
from PIL import Image

class ContentGenerator:
    def __init__(self, api_key: str):
        self.api_key = api_key
        # Initialize the new Client with v1alpha for preview models
        self.client = genai.Client(api_key=self.api_key, http_options=types.HttpOptions(api_version='v1alpha'))
        self.text_model_id = 'gemini-2.5-flash-lite'
        self.image_model_id = 'gemini-3-pro-image-preview'

    def generate_prompts(self, brief: str, guidelines: str) -> List[Dict[str, Any]]:
        """
        Generates structured image prompts based on the brief and brand guidelines.
        """
        system_instruction = """
        You are an expert Social Media Content Strategist and Creative Director.
        Your goal is to translate a client brief into executable image generation prompts.

        CRITICAL INSTRUCTION:
        1. **Strictly adhere to BRAND GUIDELINES**:
           - Use the specified color palette, tone, and forbidden elements.
           - If the guidelines say "minimalist", usage of clutter is forbidden.
        
        2. **Interpret the Client Brief**:
           - Extract every distinct post request.
           - For EACH post request, generate 3 COMPLETY DIFFERENT visual approaches (options).
        
        3. **Distinct Options (Strict Styles from Examples)**:
           - Option 1: **"Soft Watercolor Illustration"**. 
             * Description: Soft watercolor texture, paper grain effect, cute and approachable, pastel and warm tones. Focus on the character with a dreamy vibe.
           - Option 2: **"Modern Vector Badge"**. 
             * Description: Flat vector art, clean bold outlines, sticker aesthetic, simplified geometry, isolated on plain background. Looks like a logo or a die-cut sticker.
           - Option 3: **"Storybook Scene"**. 
             * Description: Detailed storybook illustration, narrative scene with full background (e.g., street, room, landscape), hand-drawn quality, whimsical and engaging. High detail.

           - **Crucial**: All 3 options MUST feature the "Kiwi" character (or brand mascot) as the central figure.
           - ALL options must still look like they belong to the same Brand (same colors/fonts/vibe).

        Output:
        A JSON object containing a list of 'posts'.
        Each 'post' must have:
        - 'id': sequential number (1, 2, ...)
        - 'concept': Short title of the post idea.
        - 'description': Brief explanation of the post content.
        - 'options': A list of 3 distinct image prompts.
            - Each prompt must be detailed, descriptive, and explicitly incorporate the brand guidelines (colors, characters, style).
            - The prompts should be ready to copy-paste into an AI image generator.
        
        Return ONLY valid JSON.
        """
        
        full_prompt = f"""
        {system_instruction}
        
        BRAND GUIDELINES:
        {guidelines}
        
        CLIENT BRIEF:
        {brief}
        """
        
        try:
            response = self.client.models.generate_content(
                model=self.text_model_id,
                contents=full_prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json"
                )
            )
            return json.loads(response.text)
        except Exception as e:
            # Fallback to list models if 404
            available = []
            try:
                # Listing models in new SDK
                # It returns an iterator of Model objects
                pager = self.client.models.list()
                for m in pager:
                    available.append(m.name)
            except:
                available = ["Could not list models"]
            
            # If the list is huge, truncate
            if len(available) > 50:
                 available = available[:50] + ["... more ..."]

            error_msg = f"Error calling Gemini API (Text): {e}\n\nAVAILABLE MODELS:\n" + "\n".join(available)
            raise Exception(error_msg)

    def generate_image(self, prompt: str, output_path: str, aspect_ratio: str = "1:1", image_size: str = "1K"):
        """
        Generates an image using gemini-3-pro-image-preview via generate_content.
        Supports custom aspect ratios and resolution (1K, 2K, 4K).
        Default: 1:1 aspect ratio at 1K resolution (1024x1024).
        """
        try:
            response = self.client.models.generate_content(
                model=self.image_model_id,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_modalities=["IMAGE"],
                    image_config=types.ImageConfig(
                        aspect_ratio=aspect_ratio,
                        image_size=image_size
                    )
                )
            )
            
            # The image is returned as inline_data in the response parts
            for part in response.parts:
                if part.inline_data is not None:
                    # Convert to PIL Image and save
                    image = part.as_image()
                    
                    # Ensure directory exists
                    os.makedirs(os.path.dirname(output_path), exist_ok=True)
                    
                    image.save(output_path)
                    return True, "Image generated successfully"
            
            return False, "No image data in response"

        except Exception as e:
            import traceback
            return False, f"Error generating image: {traceback.format_exc()}"
