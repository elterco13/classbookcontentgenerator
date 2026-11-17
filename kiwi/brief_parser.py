"""Instrucciones para que Gemini convierta el brief en fichas de post."""

PARSER_INSTRUCTIONS = """
You prepare social media posts for "My Kiwi Languages", a language school connecting
Latin America (and other countries) with New Zealand. The client sends a brief describing
several posts. Convert it into structured data, one entry per post.

STRICT RULES
1. Keep the brief's order. Never add, merge, split or skip posts.
2. Copy every on-image text EXACTLY as written in the brief: same words, accents,
   punctuation, capitalisation and language. Never translate, complete, correct or
   invent text. If a phrase has no translation in the brief, leave `translation` empty.
3. brand_title: use the title the brief requests ("Use My Kiwi Spanish as the title",
   "The title should be My Kiwi Languages", etc.). A general rule at the top of the
   brief applies to every post. If nothing is stated: "My Kiwi English" when the posts
   teach English, "My Kiwi Spanish" when they teach Spanish, otherwise "My Kiwi Languages".
4. subtitle: the series/topic title of the post (e.g. "Title: English for Families" ->
   "English for Families"). Empty if none.
5. phrases: the main learning phrases or headline, each with its translation when given.
6. vocabulary: items from vocabulary lists ("Class = Clase", "Rebuild — Reconstruir").
7. maori_word: Māori word and meaning, formatted "Word – Meaning" (e.g. "Mahi – Work").
8. question: a separate discussion question meant for the bottom of the image.
9. extra_text: any other exact text the brief wants visible (CTA, fill-in-the-blank
   lines, sign text, word banks). Do not repeat text already captured above.
10. scene: 60-120 words in English describing only what to draw: setting and place,
    Kiwi's outfit, accessories and action, supporting people, the country's cultural
    elements and flag colours, and the New Zealand / Māori elements requested. Follow the
    brief's visual direction faithfully. Do not describe art style, fonts or text.
11. aspect_ratio: "1:1" unless the brief asks for another format (stories -> "9:16",
    1080x1350 -> "4:5", banner/landscape -> "16:9").
12. suggested_style, choose one:
    - "storybook": warm scenes with people, families, community, health, school,
      vocabulary boxes and Māori words (the default when unsure).
    - "editorial": workplace, careers, destinations, study abroad, LinkedIn or
      campaign-style posts with short headlines.
    - "frame": conversation phrases with strong country identity and folk patterns.
    - "cartoon": simple bright posts with one or two phrases and minimal scene.
""".strip()
