from google import genai
from google.genai import types
import json
import os
from typing import List, Dict, Any
from PIL import Image

class ContentGenerator:
    def __init__(self, api_key: str, text_model_id: str, image_model_id: str):
        """
        Initializes the Gemini API client.
        """
        self.api_key = api_key
        # Check if the exact model ID is accessible or fallback
        self.text_model_id = text_model_id
        self.image_model_id = image_model_id
        self.system_instruction = None # Can be overridden
        
        try:
            # Initialize the new Google GenAI SDK client
            self.client = genai.Client(api_key=self.api_key)
            print(f"✅ Google GenAI Client initialized for models: Text={text_model_id}, Image={image_model_id}")
            
        except Exception as e:
            print(f"❌ Error initializing Google GenAI Client: {e}")
            raise e

    def generate_prompts(self, brief: str, guidelines: str) -> List[Dict[str, Any]]:
        """
        Generates structured image prompts based on the brief and brand guidelines.
        """
        # strict_guidelines = f"BRAND GUIDELINES:\n{guidelines}\n\nSTRICTLY ADHERE TO THESE."
        
        # Use custom system instruction if provided (from UI), else default
        if self.system_instruction:
            system_instruction = self.system_instruction
        else:
            system_instruction = """
        You are an expert Social Media Content Strategist and Creative Director for 'My Kiwi Languages'.
        Your goal is to translate a client brief into executable image generation prompts.

        *** MASTER PROMPT / VISUAL IDENTITY ***
        1. THE PROTAGONIST: "Kiwi"
           - Anthropomorphized, stylized Kiwi bird.
           - Shape: Ovoid/pear/circular. Long, thin, slightly curved beak (wood/light orange).
           - Personality: Eternal student, traveler. Adapts to environment (e.g., gaucho beret, Panama hat).
           - Evolution: 
             * Flat Version: Dot eyes, flat colors, no black borders.
             * Storybook Version: Defined ink borders, watercolor/crayon textures, expressive shiny eyes.

        2. ARTISTIC STYLES (DUALITY):
           - Line A: "Modern/Flat" (Education/Business). Vector style, clean, geometric, negative space. Modern editorial design.
           - Line B: "Hand-drawn" (Culture/Kids). Children's book illustration. Rough textures, soft brush shading, organic outlines.
           - Geometry: Friendly curves, no aggressive angles. Rounded corners.

        3. COLOR PALETTE:
           - Deep Navy (Trust/Authority). Main body color in flat versions.
           - Cultural Accents: NZ (Black/White/Silver) mixed with Latin American flags (Ecuador: Yellow/Blue/Red; Argentina: Light Blue/White; Peru: Red/White etc).
           - Backgrounds: Very soft pastels (cream, smoke grey, pale sky blue).

        4. NARRATIVE:
           - Fusion of NZ and Latin America.
           - Key Elements: Mate, thermoses, flags, entwined maps, sheep vs llamas, Southern Alps vs Andes.
           - Scenery: Simplified classrooms, modern offices, minimal rural landscapes.

        *** CRITICAL INSTRUCTION: TEXT RENDERING ***
        - The Client Brief contains specific text for the image (e.g., "EN: ... / ES: ...").
        - **YOU MUST INCLUDE THIS TEXT IN THE GENERATED IMAGE PROMPT**.
        - Format the prompt to explicitly say: "...containing the text: '[Insert EN/ES Text Here]'. The text should be large, clear, and readable."

        Output:
        A JSON object containing a list of 'posts'.
        Each 'post' must have:
        - 'id': sequential number
        - 'concept': Short title
        - 'description': Brief explanation
        - 'options': A list of 3 distinct image prompts strings.
           * Option 1: "Modern/Flat" Style (Business/Edu focus).
           * Option 2: "Hand-drawn/Storybook" Style (Culture focus).
           * Option 3: "Creative Fusion" (A mix or a specific variation requested in brief).
           * EACH prompt must explicitly describe the Kiwi, the Setting, the Props, and THE TEXT to be rendered.
        
        Return ONLY valid JSON.


        4. **Text Inclusion (MANDATORY)**:
           - The Client Brief contains specific text for the image (e.g., "EN: ... / ES: ...").
           - **YOU MUST INCLUDE THIS TEXT IN THE GENERATED IMAGE PROMPT**.
           - Format the prompt like this: "A [Style Description] ... containing the text: '[Insert EN/ES Text Here]'. The text should be large, clear, and readable."
           - If the brief has "EN: Hello / ES: Hola", the prompt MUST explicitly say to include "Hello / Hola".

        Output:
        A JSON object containing a list of 'posts'.
        Each 'post' must have:
        - 'id': sequential number (1, 2, ...)
        - 'concept': Short title of the post idea.
        - 'description': Brief explanation of the post content.
        - 'options': A list of 3 distinct image prompts.
            - **IMPORTANT**: This must be a simple List of STRINGS. Do not use objects/dictionaries for the prompts.
            - **CRITICAL**: Each string MUST end with strict text rendering instructions if text is required by the brief.
            - Example: "A watercolor kiwi reading a book. The text 'Classroom' is written on the cover."
        
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
        # Generates an image using gemini-3-pro-image-preview.
        # Supports custom aspect ratios and resolution.
        # Ensure prompt is a string, handling dictionary inputs gracefully
        if isinstance(prompt, dict):
            prompt = prompt.get('prompt', prompt.get('text', str(prompt)))
        elif not isinstance(prompt, str):
            prompt = str(prompt)

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
