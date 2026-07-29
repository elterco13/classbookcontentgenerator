from google import genai
from google.genai import types
from pydantic import BaseModel, Field
import json
import os
from typing import List, Dict, Any
from PIL import Image

class PostConcept(BaseModel):
    id: int = Field(description="Sequential post number")
    concept: str = Field(description="Short title of the post idea")
    description: str = Field(description="Brief explanation of the post content")
    options: List[str] = Field(
        description="A list of exactly 3 distinct image prompt strings corresponding to Option 1 (Pop Educational), Option 2 (Storybook), Option 3 (Creative Fusion)"
    )

class PromptResponseSchema(BaseModel):
    posts: List[PostConcept]

class ContentGenerator:
    def __init__(self, api_key: str, text_model_id: str, image_model_id: str):
        """
        Initializes the Gemini API client.
        """
        self.api_key = api_key
        self.text_model_id = text_model_id
        self.image_model_id = image_model_id
        self.system_instruction = None

        try:
            self.client = genai.Client(api_key=self.api_key)
            print(f"✅ Google GenAI Client initialized: Text={text_model_id}, Image={image_model_id}")
        except Exception as e:
            print(f"❌ Error initializing Google GenAI Client: {e}")
            raise e

    def generate_prompts(self, brief: str, guidelines: str) -> Dict[str, Any]:
        """
        Generates structured image prompts based on the brief and brand guidelines.
        """
        system_instruction = """
You are an expert Social Media Content Strategist and Creative Director for 'My Kiwi Languages'.
Your goal is to translate a client brief into executable image generation prompts for social media posts.

*** MASTER PROMPT & ARTISTIC STYLES ***

1. THE PROTAGONIST: "Kiwi"
   - Stylized, chubby ovoid brown kiwi bird.
   - Large, glossy, highly expressive black eyes, long slender orange beak.
   - Personality: Eternal student, traveler, friendly Spanish teacher.

2. THREE DISTINCT ARTISTIC STYLES:
   - OPTION 1: "Pop Educational Infographic Card"
     * Format/Style: High-quality 1:1 square educational infographic card in a modern 2D digital illustration style with soft, hand-painted watercolor paper texture and clean, friendly line-art outlines. Flat vector shapes combined with gentle, organic shading.
     * Color Palette: Strictly uses a cohesive palette of deep navy blue (#1A2B4C) for outlines and text, warm pastel sky blues and creams for backgrounds, and vibrant orange (#FF5722) for pops of energetic accents.
     * Character & Action: The central character is a single, chubby brown kiwi bird with large glossy expressive black eyes and slender orange beak. The kiwi bird is dressed in pop country/cultural accessories relevant to the brief, actively performing the action requested.
     * Background & Setting: The background depicts a beautifully detailed, stylized, and inviting illustrated scene. Integrated naturally and subtly into the background are iconic cultural references of the target country, avoiding literal flag banners.
     * Text & UI Overlay (Mandatory Layout):
       - At the very top center margin, separate from any bubbles, is a clean, small header: "My Kiwi Spanish" with a smaller subtitle below it indicating the lesson title.
       - Coming from the kiwi bird is a single, large, clean white rounded speech bubble outlined in deep navy blue.
       - Inside the speech bubble, text is stacked vertically on separate lines:
         * Spanish phrase in large, bold, deep navy blue text.
         * English translation in smaller, italic, soft grey text.
       - At the very bottom center margin of the card, completely aligned and separated from the illustration, is a simple, bold navy blue Call to Action text: "Start speaking Spanish today!"
     * No photographic elements, no 3D renders, no emojis, clean negative space, high legibility for mobile devices.

   - OPTION 2: "Hand-drawn / Storybook" (Culture/Kids focus)
     * Children's book illustration style. Rough textures, soft brush shading, organic ink outlines.
     * Soft watercolor palette with defined borders.
     * Includes explicit text rendering instructions if text is required by the brief.

   - OPTION 3: "Creative Fusion / Modern Editorial"
     * Modern vector editorial design mixed with creative concept variations requested in the brief.
     * Clean geometric compositions, rounded corners, dynamic layout.
     * Includes explicit text rendering instructions if text is required by the brief.

3. MANDATORY OUTPUT REQUIREMENTS:
   - Output must contain a list of 'posts'.
   - Each 'post' must have:
     * 'id': sequential number (1, 2, 3...)
     * 'concept': Short title of the post idea.
     * 'description': Brief explanation of post content.
     * 'options': List of 3 distinct string prompts [Option 1 string, Option 2 string, Option 3 string].
   - Each prompt string MUST be fully formed, self-contained, and ready for image generation.
"""

        full_prompt = f"""
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
                    system_instruction=system_instruction,
                    response_mime_type="application/json",
                    response_schema=PromptResponseSchema,
                )
            )
            return json.loads(response.text)
        except Exception as e:
            # Fallback handling
            available = []
            try:
                pager = self.client.models.list()
                for m in pager:
                    available.append(m.name)
            except Exception:
                available = ["Could not list models"]

            if len(available) > 50:
                available = available[:50] + ["... more ..."]

            error_msg = f"Error calling Gemini API (Text): {e}\n\nAVAILABLE MODELS:\n" + "\n".join(available)
            raise Exception(error_msg)

    def generate_image(self, prompt: str, output_path: str, aspect_ratio: str = "1:1"):
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
                        image_size="1K"
                    )
                )
            )

            for part in response.parts:
                if part.inline_data is not None:
                    image = part.as_image()
                    os.makedirs(os.path.dirname(output_path), exist_ok=True)
                    image.save(output_path)
                    return True, "Image generated successfully"

            return False, "No image data in response"

        except Exception as e:
            import traceback
            return False, f"Error generating image: {traceback.format_exc()}"
