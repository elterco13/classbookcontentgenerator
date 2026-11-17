"""Estructura de datos de un brief interpretado."""

from typing import Literal

from pydantic import BaseModel, Field

StyleKey = Literal["storybook", "editorial", "frame", "cartoon"]


class Phrase(BaseModel):
    text: str = Field(description="Main phrase exactly as written in the brief (shown first, bold).")
    translation: str = Field(
        default="",
        description="Its translation exactly as written in the brief (shown below, italic). Empty if the brief gives none.",
    )


class VocabItem(BaseModel):
    term: str = Field(description="Vocabulary word exactly as written in the brief.")
    translation: str = Field(default="", description="Its translation exactly as written. Empty if none.")


class PostSpec(BaseModel):
    number: int = Field(description="Post number, in the brief's order, starting at 1.")
    brand_title: str = Field(description="Brand header at the top, e.g. 'My Kiwi English'. Empty only if the brief says no title.")
    subtitle: str = Field(default="", description="Series or topic title shown under the header, verbatim.")
    country: str = Field(default="", description="Country or culture of the post, in English.")
    phrases: list[Phrase] = Field(default_factory=list, description="Main learning phrases or headline, in order.")
    vocabulary_label: str = Field(default="Vocabulary:", description="Label for the vocabulary box.")
    vocabulary: list[VocabItem] = Field(default_factory=list)
    maori_word: str = Field(default="", description="Māori word with meaning, verbatim, e.g. 'Mahi – Work'.")
    question: str = Field(default="", description="Secondary discussion question shown at the bottom, verbatim.")
    extra_text: list[str] = Field(
        default_factory=list,
        description="Any other exact text the brief asks to show (CTA, fill-in-the-blank lines, signs, labels).",
    )
    scene: str = Field(description="Visual description of the scene in English (setting, Kiwi's outfit and action, people, cultural and NZ elements, colours). No text instructions.")
    aspect_ratio: Literal["1:1", "4:5", "9:16", "16:9"] = "1:1"


class BriefSpec(BaseModel):
    suggested_style: StyleKey = Field(description="Best matching house style for this brief.")
    posts: list[PostSpec]
