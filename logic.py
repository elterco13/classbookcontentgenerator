from google import genai
from google.genai import types
from pydantic import BaseModel, Field
import json
import os
from typing import List, Dict, Any
from PIL import Image

class PostConcept(BaseModel):
    id: int = Field(description="Sequential post number matching brief")
    concept: str = Field(description="Title or theme of post")
    description: str = Field(description="Brief explanation of the visual direction")
    options: List[str] = Field(
        description="A list of exactly 3 distinct image prompt strings corresponding to Option 1 (Pop Educational), Option 2 (Storybook), Option 3 (Creative Fusion / Modern Editorial). Each prompt must strictly adhere to the brief and brand guidelines without inventing text."
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
            print(f"Google GenAI Client initialized: Text={text_model_id}, Image={image_model_id}")
        except Exception as e:
            print(f"Error initializing Google GenAI Client: {e}")
            raise e

    def generate_prompts(self, brief: str, guidelines: str) -> Dict[str, Any]:
        """
        Generates structured image prompts based on the brief and brand guidelines.
        Enforces strict brief adherence, brand title inclusion, and eliminates text hallucination.
        """
        system_instruction = """
You are an expert Creative Director and Visual Prompt Engineer for 'My Kiwi Languages'.
Your mission is to transform client briefs and brand guidelines into precision image generation prompts for social media posts.

*** CORE FIDELITY DIRECTIVES (STRICT COMPLIANCE REQUIRED) ***
1. ZERO TEXT HALLUCINATION / RESPECT BRAND GUIDELINES & BRIEF:
   - You MUST NOT invent, assume, translate, or fabricate any text not requested in the brief or brand guidelines.
   - If the Brand Guidelines or brief specify a brand title (e.g., 'My Kiwi Languages'), always render that exact title clearly in the composition (e.g. at the top margin in clean, high-legibility typography).
   - If the brief specifies a headline or phrase, render ONLY that exact phrase verbatim, preserving original language, accents, and punctuation.
   - DO NOT prepend country names or labels to headlines unless explicitly quoted in the brief.
   - NEVER add English translations, Spanish subtitles, or generic CTAs (like 'Start speaking Spanish today!' or 'Follow us') unless explicitly written in the brief.
   - If no specific headline text is given in the brief, render ONLY the brand title ('My Kiwi Languages') without inventing additional slogans or body text.

2. STRICT ORDER & POST CORRESPONDENCE:
   - Map each post in the brief 1-to-1 in the EXACT requested order. Never reorder, omit, or add posts.

3. ACCURATE VISUAL TRANSLATION:
   - Faithfully translate every requested element from the brief and guidelines (colors, characters, cultural elements, workplace settings, props, backgrounds).
   - The protagonist is 'Kiwi': a stylized, chubby ovoid brown kiwi bird with large expressive glossy black eyes and a slender orange beak. Adapt its attire, accessories, or colleagues exactly as requested in the brief (e.g. cultural fusion between New Zealand and the post's culture).

*** THE THREE MASTER ARTISTIC STYLES ***
- OPTION 1: 'Pop Educational Infographic Card'
  * Visual Style: High-quality 1:1 educational card in a modern 2D digital illustration style with soft watercolor paper texture and clean, friendly line-art outlines. Flat vector shapes with organic shading.
  * Palette: Deep navy blue (#1A2B4C) outlines and text, warm pastel blues and creams, vibrant orange (#FF5722) accents, combined with cultural accents.
  * Composition: Educational layout with clean negative space. Renders the brand title 'My Kiwi Languages' and any exact text from the brief.

- OPTION 2: 'Hand-drawn / Storybook Illustration'
  * Visual Style: Whimsical children's book illustration style. Rough textures, soft brush shading, organic ink outlines. Cozy warm watercolor palette with defined borders.
  * Composition: Heartfelt storybook narrative scene placing the Kiwi and colleagues in the requested setting. Renders 'My Kiwi Languages' and requested text in friendly storybook lettering.

- OPTION 3: 'Creative Fusion / Modern Editorial'
  * Visual Style: Polished modern editorial digital illustration. Clean geometric compositions, sophisticated vector color blocking, dynamic aspirational layout, sleek vector lines with premium depth and subtle lighting.
  * Cultural Fusion: Elegantly blends modern workplace/aspirational motifs with cultural touches requested in the brief (e.g. cultural accents paired with NZ workplace colleagues, silver fern motifs, or clean architectural lines).
  * Graphic Elements: Sophisticated, clean geometric or rounded vector thought bubble / graphic containers displaying the requested icons.
  * Typography & Text: High-end editorial typography. Renders the brand title 'My Kiwi Languages' prominently at the top with pristine legibility. No unrequested text.

*** MANDATORY OUTPUT ***
Return a JSON object conforming to PromptResponseSchema with 'posts', each containing 'id', 'concept', 'description', and 'options' [Option 1, Option 2, Option 3].
Each prompt string MUST be fully self-contained, detailed, and directly executable by image generation models.
"""

        full_prompt = f"""
BRAND GUIDELINES:
{guidelines if guidelines.strip() else "Brand: My Kiwi Languages. Protagonist: Kiwi bird (friendly, chubby, traveler, educator)."}

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
