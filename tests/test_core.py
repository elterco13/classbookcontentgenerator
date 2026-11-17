import io
from datetime import datetime

import pytest
from google.genai import types
from PIL import Image

from kiwi.gemini import GenerationError, _extract_image
from kiwi.jobs import ImageVersion, Job, PostState, list_jobs, new_job_folder
from kiwi.prompt_builder import build_prompt
from kiwi.schemas import BriefSpec, Phrase, PostSpec, VocabItem
from kiwi.styles import STYLES


def sample_post(**kw) -> PostSpec:
    base = dict(
        number=1,
        brand_title="My Kiwi English",
        subtitle="English for Families",
        country="Argentina",
        phrases=[Phrase(text="Is your child in this class too?", translation="¿Tu hijo también viene a esta clase?")],
        vocabulary=[VocabItem(term="Class", translation="Clase"), VocabItem(term="Teacher", translation="Profesor")],
        maori_word="Haere Mai – Welcome",
        question="How many children do you have?",
        scene="A primary school entrance in Buenos Aires with parents chatting.",
    )
    base.update(kw)
    return PostSpec(**base)


def png_bytes(color="red") -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (8, 8), color).save(buf, format="PNG")
    return buf.getvalue()


# ------------------------------------------------------------- prompts
@pytest.mark.parametrize("style", list(STYLES))
def test_prompt_contains_exact_text_and_style(style):
    prompt = build_prompt(sample_post(), style)
    assert STYLES[style].visual in prompt
    for text in [
        '"My Kiwi English"',
        '"English for Families"',
        '"Is your child in this class too?"',
        '"¿Tu hijo también viene a esta clase?"',
        '"Class = Clase"',
        '"Haere Mai – Welcome"',
        '"How many children do you have?"',
        '"Vocabulary:"',
    ]:
        assert text in prompt


def test_prompt_omits_empty_sections():
    post = sample_post(subtitle="", vocabulary=[], maori_word="", question="")
    prompt = build_prompt(post, "storybook")
    assert "Subtitle" not in prompt
    assert "Vocabulary box" not in prompt
    assert "Māori word (" not in prompt
    assert "Bottom question" not in prompt


def test_prompt_without_text_forbids_text():
    post = sample_post(brand_title="", subtitle="", phrases=[], vocabulary=[], maori_word="", question="")
    assert "must contain no text" in build_prompt(post, "editorial")


def test_phrase_without_translation_has_no_italic_line():
    post = sample_post(phrases=[Phrase(text="¿Hasta dónde puedes llegar?")])
    assert "italic" not in build_prompt(post, "editorial")


def test_unknown_style_falls_back_to_default():
    assert STYLES["storybook"].visual in build_prompt(sample_post(), "nope")


def test_brief_schema_roundtrip():
    spec = BriefSpec(suggested_style="storybook", posts=[sample_post()])
    assert BriefSpec.model_validate_json(spec.model_dump_json()) == spec


# ------------------------------------------------------------- trabajos
def make_job(tmp_path) -> Job:
    job_id, folder = new_job_folder(str(tmp_path), datetime(2026, 11, 17))
    return Job(id=job_id, folder=folder, brief="b", style="storybook", posts=[PostState(spec=sample_post(), style="storybook")])


def test_job_folder_naming(tmp_path):
    job_id, folder = new_job_folder(str(tmp_path), datetime(2026, 11, 7))
    assert job_id == "07-11-26"
    (tmp_path / job_id).mkdir()
    assert new_job_folder(str(tmp_path), datetime(2026, 11, 7))[0] == "07-11-26_2"


def test_versions_selection_and_zip(tmp_path):
    job = make_job(tmp_path)
    v = lambda: ImageVersion(file="", kind="generate", model="m", size="1K", prompt="p", cost=0.03)
    job.add_version(0, png_bytes("red"), v())
    job.add_version(0, png_bytes("blue"), v())
    assert job.posts[0].selected == 1
    assert (tmp_path / job.id / "01.png").read_bytes() == png_bytes("blue")

    job.select(0, 0)
    assert (tmp_path / job.id / "01.png").read_bytes() == png_bytes("red")
    assert job.total_cost() == pytest.approx(0.06)

    import zipfile

    with zipfile.ZipFile(io.BytesIO(job.zip_bytes())) as z:
        assert z.namelist() == ["01.png"]
        assert z.read("01.png") == png_bytes("red")

    reloaded = Job.load(job.folder)
    assert reloaded.posts[0].selected == 0 and len(reloaded.posts[0].versions) == 2
    assert list_jobs(str(tmp_path)) == [job.folder]


# ------------------------------------------------------------- respuesta de la API
def response_with(parts, finish="STOP"):
    return types.GenerateContentResponse(
        candidates=[types.Candidate(content=types.Content(role="model", parts=parts), finish_reason=finish)]
    )


def test_extract_image_skips_thoughts():
    jpeg = io.BytesIO()
    Image.new("RGB", (8, 8), "green").save(jpeg, format="JPEG")
    resp = response_with(
        [
            types.Part(inline_data=types.Blob(data=png_bytes("red"), mime_type="image/png"), thought=True),
            types.Part(inline_data=types.Blob(data=jpeg.getvalue(), mime_type="image/jpeg")),
        ]
    )
    out = _extract_image(resp)
    assert out.startswith(b"\x89PNG")
    assert Image.open(io.BytesIO(out)).getpixel((4, 4))[1] > 100  # verde, no la imagen "thought"


def test_extract_image_without_image_raises():
    with pytest.raises(GenerationError, match="no devolvió"):
        _extract_image(response_with([types.Part(text="Sorry")], finish="SAFETY"))


# ------------------------------------------------------------- imagen de referencia
from kiwi.gemini import GeminiClient, closest_aspect_ratio, prepare_reference
from kiwi.prompt_builder import build_post_prompt, build_reference_prompt


def test_reference_prompt_with_and_without_text():
    post = sample_post(scene="Same style but for Canada.", extra_text=["MY KIWI ENGLISH", "Learn Canadian English"])
    prompt = build_reference_prompt(post)
    assert "attached image is a reference" in prompt
    assert "Same style but for Canada." in prompt
    assert '1. "MY KIWI ENGLISH"' in prompt and '2. "Learn Canadian English"' in prompt
    assert "keep the reference's text layout" in build_reference_prompt(sample_post(extra_text=[]))
    # build_post_prompt elige la plantilla correcta
    assert build_post_prompt(post, "storybook", True) == prompt
    assert build_post_prompt(post, "storybook", False) == build_prompt(post, "storybook")


def test_closest_aspect_ratio_and_prepare_reference():
    def img(w, h, mode="RGB"):
        buf = io.BytesIO()
        Image.new(mode, (w, h)).save(buf, format="PNG")
        return buf.getvalue()

    opts = ["1:1", "4:5", "9:16", "16:9"]
    assert closest_aspect_ratio(img(400, 450), opts) == "4:5"
    assert closest_aspect_ratio(img(1080, 1920), opts) == "9:16"
    assert closest_aspect_ratio(img(500, 500), opts) == "1:1"
    out = Image.open(io.BytesIO(prepare_reference(img(3000, 2000, "P"))))
    assert max(out.size) == 1024 and out.format == "PNG"


def test_add_reference_post(tmp_path):
    job = make_job(tmp_path)
    idx = job.add_reference_post(png_bytes("blue"), "Para Canadá", ["MY KIWI ENGLISH", " "], "4:5")
    post = job.posts[idx]
    assert post.is_reference and post.spec.number == 2 and post.spec.extra_text == ["MY KIWI ENGLISH"]
    assert job.read_reference(idx) == png_bytes("blue")
    assert Job.load(job.folder).posts[idx].reference_file == post.reference_file


def test_generate_image_sends_reference_first():
    sent = {}

    class FakeModels:
        def generate_content(self, model, contents, config):
            sent["contents"] = contents
            return response_with([types.Part(inline_data=types.Blob(data=png_bytes(), mime_type="image/png"))])

    client = GeminiClient.__new__(GeminiClient)
    client.client = type("C", (), {"models": FakeModels()})()
    client.generate_image("prompt", "m", reference_png=png_bytes("blue"))
    assert isinstance(sent["contents"], list) and sent["contents"][1] == "prompt"
    assert sent["contents"][0].inline_data.data == png_bytes("blue")
    client.generate_image("solo prompt", "m")
    assert sent["contents"] == "solo prompt"
