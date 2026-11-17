"""Construye el prompt de imagen de forma determinista.

El modelo de texto solo aporta la descripción de la escena; el estilo, el
personaje y la colocación del texto salen siempre de plantillas fijas. Así cada
imagen sigue la misma receta y el texto del brief se copia sin cambios.
"""

from .schemas import PostSpec
from .styles import KIWI_CHARACTER, TEXT_RULES, get_style

ASPECT_LABEL = {
    "1:1": "square 1:1",
    "4:5": "vertical 4:5",
    "9:16": "vertical 9:16 story",
    "16:9": "horizontal 16:9",
}


def _q(text: str) -> str:
    return f'"{text.strip()}"'


def text_block(post: PostSpec, layout: dict) -> list[str]:
    """Lista numerada con cada elemento de texto y dónde colocarlo."""
    items: list[str] = []

    if post.brand_title.strip():
        items.append(f"Header ({layout['header']}): {_q(post.brand_title)}")
    if post.subtitle.strip():
        items.append(f"Subtitle ({layout['subtitle']}): {_q(post.subtitle)}")

    phrases = [p for p in post.phrases if p.text.strip()]
    if phrases:
        lines = []
        for p in phrases:
            lines.append(f"    {_q(p.text)} (bold)")
            if p.translation.strip():
                lines.append(f"    {_q(p.translation)} (italic, slightly smaller, directly below)")
        items.append(f"Main phrases ({layout['phrases']}):\n" + "\n".join(lines))

    vocab = [v for v in post.vocabulary if v.term.strip()]
    if vocab:
        lines = [f"    {_q(post.vocabulary_label)} (bold)"] if post.vocabulary_label.strip() else []
        for v in vocab:
            entry = f"{v.term.strip()} = {v.translation.strip()}" if v.translation.strip() else v.term.strip()
            lines.append(f"    {_q(entry)}")
        items.append(f"Vocabulary box ({layout['vocabulary']}):\n" + "\n".join(lines))

    if post.maori_word.strip():
        items.append(f"Māori word ({layout['maori']}): {_q(post.maori_word)}")
    if post.question.strip():
        items.append(f"Bottom question ({layout['question']}): {_q(post.question)}")

    extra = [e for e in post.extra_text if e.strip()]
    if extra:
        lines = "\n".join(f"    {_q(e)}" for e in extra)
        items.append(f"Additional text ({layout['extra']}):\n{lines}")

    return [f"{i}. {item}" for i, item in enumerate(items, 1)]


def build_prompt(post: PostSpec, style_key: str) -> str:
    style = get_style(style_key)
    parts = [
        style.visual,
        f"MAIN CHARACTER: {KIWI_CHARACTER} {style.kiwi_note}",
        f"SCENE: {post.scene.strip()}",
    ]
    texts = text_block(post, style.layout)
    if texts:
        parts.append("TEXT IN THE IMAGE: " + TEXT_RULES + "\n" + "\n".join(texts))
    else:
        parts.append("TEXT IN THE IMAGE: none. The image must contain no text, letters or logos at all.")
    parts.append(
        f"FORMAT: {ASPECT_LABEL.get(post.aspect_ratio, 'square 1:1')} composition, balanced and "
        "uncluttered, with nothing important cut off at the edges."
    )
    return "\n\n".join(parts)


def build_reference_prompt(post: PostSpec) -> str:
    """Prompt para crear una imagen nueva a partir de una imagen de referencia adjunta."""
    parts = [
        "The attached image is a reference design from the same brand. Create a NEW image "
        "that keeps exactly the same art style, technique, textures, colour treatment, "
        "composition, layout and typography style as the reference, adapted as follows:",
        post.scene.strip(),
    ]
    texts = [t for t in post.extra_text if t.strip()]
    if texts:
        lines = "\n".join(f'{i}. "{t.strip()}"' for i, t in enumerate(texts, 1))
        parts.append(
            "TEXT IN THE IMAGE: replace all of the reference's text with ONLY these lines, in "
            "the same positions, sizes and type styles as the reference text (first line = main "
            "title). Spell them exactly as written, keeping accents and punctuation; add no "
            "other words:\n" + lines
        )
    else:
        parts.append(
            "TEXT IN THE IMAGE: keep the reference's text layout, changing only the words the "
            "instructions above ask to change. Add no other words."
        )
    parts.append(
        f"Elements of the reference that conflict with the instructions must be replaced, not "
        f"kept. FORMAT: {ASPECT_LABEL.get(post.aspect_ratio, 'square 1:1')}."
    )
    return "\n\n".join(parts)


def build_post_prompt(post: PostSpec, style_key: str, is_reference: bool) -> str:
    return build_reference_prompt(post) if is_reference else build_prompt(post, style_key)


def build_edit_prompt(instruction: str) -> str:
    return (
        "Edit the attached image. Apply ONLY this change: "
        f"{instruction.strip()}\n\n"
        "Keep everything else identical: the same illustration style, the same Kiwi character, "
        "the same composition, and every piece of text exactly as it is unless the change asks "
        "to modify it. Do not add any new text."
    )
