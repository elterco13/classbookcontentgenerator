"""Estilos estandarizados de My Kiwi Languages.

Cada estilo es una descripción textual fija, escrita a partir de los posts
entregados y aprobados en 2026. No se envían imágenes de referencia: toda la
coherencia viene de estos textos, que se reutilizan idénticos en cada prompt.

Para ajustar un estilo, edita solo este archivo.
"""

from dataclasses import dataclass, field

# Descripción del personaje, compartida por todos los estilos.
KIWI_CHARACTER = (
    "Kiwi, the brand mascot: a chubby, egg-shaped brown kiwi bird covered in soft, "
    "slightly fuzzy brown feathers with darker brown texture strokes; a small round head "
    "that merges into the body; big round glossy dark eyes with a white highlight and a "
    "gentle, friendly expression; a very long, thin, slightly down-curved beak in pale "
    "orange-tan; short sturdy orange-tan legs with three-toed feet; tiny stubby wings that "
    "can gesture or point. It is a bird, not a human: it only wears the accessories "
    "mentioned in the scene. Kiwi appears exactly once, fully visible, as the protagonist."
)

TEXT_RULES = (
    "Render ONLY the text listed below, spelled exactly as written, keeping accents, "
    "punctuation and capitalisation. Every quoted line goes on its own line. Do not add "
    "any other words, letters, labels, translations, prefixes such as 'EN:' or 'ES:', "
    "hashtags, logos or watermarks anywhere in the image. All text must be large, sharp "
    "and easy to read on a phone."
)


@dataclass(frozen=True)
class Style:
    key: str
    name: str
    summary: str  # descripción corta para la interfaz
    visual: str  # bloque de estilo visual
    kiwi_note: str  # matiz del personaje para este estilo
    layout: dict = field(default_factory=dict)  # dónde va cada elemento de texto


STORYBOOK = Style(
    key="storybook",
    name="Storybook acuarela",
    summary="Ilustración de cuento con tinta y acuarela. Título grande arriba, globo bilingüe, "
    "recuadro de vocabulario, cartel māori y pregunta abajo (estilo de junio y julio).",
    visual=(
        "STYLE: a hand-drawn children's-book illustration for a square educational social "
        "media post. Confident dark-brown ink outlines with natural, slightly irregular line "
        "weight; soft watercolor washes and light coloured-pencil texture on warm paper grain; "
        "bright, cheerful daylight. Natural palette of sky blue, leafy greens and warm creams, "
        "with the country's flag colours used only as small accents (a small flag, bunting, "
        "clothing details). Supporting people are diverse, realistic and friendly, drawn in the "
        "same storybook manner. Detailed but uncluttered background, with a calm light area "
        "behind every text element. No photorealism, no 3D render, no emojis."
    ),
    kiwi_note="Kiwi is drawn with the same ink outlines and watercolor shading as the scene.",
    layout={
        "header": "top centre, very large bold rounded sans-serif in deep navy (#1A2B4C), on a light sky area",
        "subtitle": "directly under the header, medium-size bold sans-serif in dark navy",
        "phrases": "inside a white speech bubble with a thin dark outline coming from Kiwi, in the upper-left or centre",
        "vocabulary": "a small cream rounded box with a thin dark outline in the upper-right area, one item per line",
        "maori": "painted in dark lettering on a small wooden signpost standing in the lower-right of the scene",
        "question": "bottom centre, bold dark navy sans-serif over a light band of the image",
        "extra": "in a clear light panel where it fits naturally, without covering Kiwi",
    },
)

EDITORIAL = Style(
    key="editorial",
    name="Editorial geométrico",
    summary="Vector plano moderno con bloques de color y tarjeta de esquinas redondeadas. "
    "Ideal para trabajo, destinos, campañas y LinkedIn (estilo de agosto a octubre).",
    visual=(
        "STYLE: a polished modern flat-vector editorial illustration, like a contemporary "
        "travel or design poster. Geometric colour blocking, crisp clean shapes, subtle "
        "gradients and fine grain texture, soft directional light and depth through layered "
        "planes. Base palette of deep navy (#1A2B4C) and warm off-white, with the country's "
        "flag colours as bold blocks and accents. Stylised plants, architecture and landmarks "
        "of the country, combined with subtle New Zealand cues (silver fern, koru or "
        "kowhaiwhai pattern motifs, Auckland skyline) where they fit. The artwork sits inside "
        "a rounded-corner card with a thin margin. No photorealism, no 3D render, no emojis."
    ),
    kiwi_note="Kiwi is rendered in the same flat-vector language, with soft gradients and no heavy outlines.",
    layout={
        "header": "top centre, bold geometric sans-serif in deep navy",
        "subtitle": "under the header, smaller geometric sans-serif",
        "phrases": "large bold geometric sans-serif in a clean white rounded panel or on a solid colour block, in the upper or left area",
        "vocabulary": "a small white rounded tag panel near the main text",
        "maori": "a small rounded label integrated into the scene",
        "question": "bottom area, bold navy sans-serif on a solid colour block",
        "extra": "in a clean rounded panel that matches the layout",
    },
)

CULTURAL_FRAME = Style(
    key="frame",
    name="Marco cultural",
    summary="Escena plana y vibrante rodeada de un marco grueso con patrones textiles o "
    "folclóricos del país (estilo de finales de agosto).",
    visual=(
        "STYLE: a vibrant flat digital illustration with a light hand-made texture, "
        "surrounded on all four sides by a thick decorative border (about 7% of the width) made "
        "of the country's traditional textile, tile or folk-art patterns in the flag's colours. "
        "Inside the border: a lively scene with a recognisable landmark, street or landscape of "
        "the country, warm saturated colours and clean outlines. Subtle New Zealand or Maori "
        "motifs may appear inside the scene. No photorealism, no 3D render, no emojis."
    ),
    kiwi_note="Kiwi is drawn in the same flat, clean-outlined style as the scene.",
    layout={
        "header": "top centre inside the border, bold sans-serif in deep navy",
        "subtitle": "under the header, smaller bold sans-serif",
        "phrases": "inside a white rounded card with a thin dark outline beside Kiwi (or a speech bubble from Kiwi)",
        "vocabulary": "a small white rounded card near the main text, one item per line",
        "maori": "a small wooden sign or label inside the scene",
        "question": "bottom area inside the border, on a white rounded card",
        "extra": "in a white rounded card that matches the main card",
    },
)

CARTOON = Style(
    key="cartoon",
    name="Cartoon vibrante",
    summary="Dibujo digital limpio con contornos suaves y colores saturados; texto grande en "
    "una tarjeta blanca (estilo de septiembre).",
    visual=(
        "STYLE: a bright, clean digital cartoon illustration for a square social media post. "
        "Smooth bold dark outlines, soft cel shading, saturated cheerful colours, simplified "
        "but recognisable landmark, street or landscape of the country in the background, "
        "with the flag colours present in the environment. Clear, uncluttered composition: "
        "Kiwi on one side, text on the other. No photorealism, no 3D render, no emojis."
    ),
    kiwi_note="Kiwi is cute and expressive, drawn with smooth bold outlines and soft cel shading.",
    layout={
        "header": "top centre, very bold rounded sans-serif in deep navy",
        "subtitle": "under the header, smaller bold sans-serif",
        "phrases": "a large white rounded card with soft shadow on the right half",
        "vocabulary": "a small rounded tag panel under the main card",
        "maori": "a small rounded label inside the scene",
        "question": "bottom of the white card, bold navy sans-serif",
        "extra": "inside the white card, below the main phrases",
    },
)

STYLES: dict[str, Style] = {s.key: s for s in (STORYBOOK, EDITORIAL, CULTURAL_FRAME, CARTOON)}
DEFAULT_STYLE = STORYBOOK.key


def get_style(key: str) -> Style:
    return STYLES.get(key, STYLES[DEFAULT_STYLE])
