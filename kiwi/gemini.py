"""Llamadas a la API de Gemini: interpretar el brief, generar y editar imágenes."""

import io
import time

from google import genai
from google.genai import errors, types
from PIL import Image

from .brief_parser import PARSER_INSTRUCTIONS
from .prompt_builder import build_edit_prompt
from .schemas import BriefSpec

RETRY_CODES = {429, 500, 502, 503, 504}


class GenerationError(Exception):
    """Error legible para mostrar en la interfaz."""


def _with_retries(fn, attempts: int = 3):
    delay = 4.0
    for attempt in range(1, attempts + 1):
        try:
            return fn()
        except errors.APIError as e:
            if e.code in RETRY_CODES and attempt < attempts:
                time.sleep(delay)
                delay *= 2
                continue
            raise GenerationError(f"Error de la API ({e.code}): {e.message}") from e


def _to_png(data: bytes) -> bytes:
    with Image.open(io.BytesIO(data)) as im:
        out = io.BytesIO()
        im.save(out, format="PNG")
        return out.getvalue()


def prepare_reference(data: bytes, max_side: int = 1024) -> bytes:
    """Convierte una imagen subida a PNG de como máximo 1024 px (menos tokens de entrada)."""
    with Image.open(io.BytesIO(data)) as im:
        if im.mode not in ("RGB", "RGBA"):
            im = im.convert("RGBA")
        im.thumbnail((max_side, max_side))
        out = io.BytesIO()
        im.save(out, format="PNG")
        return out.getvalue()


def closest_aspect_ratio(data: bytes, options: list[str]) -> str:
    """Formato admitido más parecido a las proporciones de la imagen."""
    import math

    with Image.open(io.BytesIO(data)) as im:
        ratio = im.width / im.height

    def distance(opt: str) -> float:
        w, h = (int(x) for x in opt.split(":"))
        return abs(math.log(ratio / (w / h)))

    return min(options, key=distance)


def _extract_image(response: types.GenerateContentResponse) -> bytes:
    candidates = response.candidates or []
    for cand in candidates:
        for part in (cand.content.parts if cand.content else None) or []:
            if getattr(part, "thought", False):
                continue  # imágenes intermedias del razonamiento
            if part.inline_data and part.inline_data.data:
                return _to_png(part.inline_data.data)
    reason = candidates[0].finish_reason if candidates else None
    feedback = getattr(response, "prompt_feedback", None)
    detail = response.text if candidates and response.text else ""
    raise GenerationError(
        "La API no devolvió ninguna imagen"
        + (f" (motivo: {reason})" if reason else "")
        + (f" (bloqueo: {feedback.block_reason})" if feedback and feedback.block_reason else "")
        + (f": {detail[:300]}" if detail else ".")
    )


class GeminiClient:
    def __init__(self, api_key: str):
        if not api_key:
            raise GenerationError("Falta la API key de Gemini.")
        self.client = genai.Client(api_key=api_key)

    def parse_brief(self, brief: str, model: str) -> BriefSpec:
        def call():
            return self.client.models.generate_content(
                model=model,
                contents=f"CLIENT BRIEF:\n\n{brief.strip()}",
                config=types.GenerateContentConfig(
                    system_instruction=PARSER_INSTRUCTIONS,
                    response_mime_type="application/json",
                    response_schema=BriefSpec,
                    temperature=0.2,
                ),
            )

        response = _with_retries(call)
        if isinstance(response.parsed, BriefSpec):
            spec = response.parsed
        else:
            try:
                spec = BriefSpec.model_validate_json(response.text or "")
            except Exception as e:
                raise GenerationError(f"No se pudo interpretar la respuesta del modelo: {e}") from e
        if not spec.posts:
            raise GenerationError("No se encontró ningún post en el brief.")
        return spec

    def _image_call(self, contents, model: str, aspect_ratio: str, size: str) -> bytes:
        def call():
            return self.client.models.generate_content(
                model=model,
                contents=contents,
                config=types.GenerateContentConfig(
                    response_modalities=["IMAGE"],
                    image_config=types.ImageConfig(aspect_ratio=aspect_ratio, image_size=size),
                ),
            )

        return _extract_image(_with_retries(call))

    def generate_image(
        self,
        prompt: str,
        model: str,
        aspect_ratio: str = "1:1",
        size: str = "1K",
        reference_png: bytes | None = None,
    ) -> bytes:
        contents = prompt
        if reference_png:
            contents = [types.Part.from_bytes(data=reference_png, mime_type="image/png"), prompt]
        return self._image_call(contents, model, aspect_ratio, size)

    def edit_image(self, image_png: bytes, instruction: str, model: str, aspect_ratio: str = "1:1", size: str = "1K") -> bytes:
        contents = [
            types.Part.from_bytes(data=image_png, mime_type="image/png"),
            build_edit_prompt(instruction),
        ]
        return self._image_call(contents, model, aspect_ratio, size)
