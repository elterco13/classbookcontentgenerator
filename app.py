"""My Kiwi Studio: pega el brief y obtén las imágenes con el estilo de la marca."""

import os
from concurrent.futures import ThreadPoolExecutor, as_completed

import streamlit as st

from kiwi import config
from kiwi.gemini import GeminiClient, GenerationError, closest_aspect_ratio, prepare_reference
from kiwi.jobs import ImageVersion, Job, PostState, list_jobs, new_job_folder
from kiwi.prompt_builder import build_edit_prompt, build_post_prompt
from kiwi.schemas import Phrase, VocabItem
from kiwi.styles import DEFAULT_STYLE, STYLES

st.set_page_config(page_title="My Kiwi Studio", page_icon="🥝", layout="wide")

MODEL_NAMES = {v: k for k, v in config.IMAGE_MODELS.items()}
STYLE_KEYS = list(STYLES)


# ---------------------------------------------------------------- utilidades
@st.cache_resource(show_spinner=False)
def get_client(api_key: str) -> GeminiClient:
    return GeminiClient(api_key)


def secret_api_key() -> str:
    """API key desde .env / variables de entorno o, en Streamlit Cloud, desde st.secrets."""
    key = config.get_api_key()
    if key:
        return key
    try:
        return st.secrets.get("GOOGLE_API_KEY", "") or st.secrets.get("GEMINI_API_KEY", "")
    except Exception:  # no hay secrets.toml
        return ""


def flash(msg: str) -> None:
    st.session_state.setdefault("flash", []).append(msg)


def phrases_to_text(phrases: list[Phrase]) -> str:
    return "\n".join(f"{p.text} | {p.translation}" if p.translation else p.text for p in phrases)


def text_to_phrases(text: str) -> list[Phrase]:
    out = []
    for line in text.splitlines():
        if line.strip():
            original, _, translation = line.partition("|")
            out.append(Phrase(text=original.strip(), translation=translation.strip()))
    return out


def vocab_to_text(items: list[VocabItem]) -> str:
    return "\n".join(f"{v.term} = {v.translation}" if v.translation else v.term for v in items)


def text_to_vocab(text: str) -> list[VocabItem]:
    out = []
    for line in text.splitlines():
        if line.strip():
            term, _, translation = line.partition("=")
            out.append(VocabItem(term=term.strip(), translation=translation.strip()))
    return out


def lines(text: str) -> list[str]:
    return [x.strip() for x in text.splitlines() if x.strip()]


def prompt_for(post: PostState) -> str:
    return post.prompt_override.strip() or build_post_prompt(post.spec, post.style, post.is_reference)


def make_version(kind: str, prompt: str, instruction: str = "") -> ImageVersion:
    model_id = config.IMAGE_MODELS[st.session_state.model_name]
    size = st.session_state.size
    return ImageVersion(
        file="",
        kind=kind,
        model=model_id,
        size=size,
        prompt=prompt,
        instruction=instruction,
        cost=config.estimate_cost(model_id, size),
    )


def generate_many(job: Job, client: GeminiClient, indices: list[int]) -> None:
    """Genera varias imágenes en paralelo y las guarda como nuevas versiones."""
    model_id = config.IMAGE_MODELS[st.session_state.model_name]
    size = st.session_state.size
    progress = st.progress(0.0, text=f"Generando {len(indices)} imagen(es)...")
    errors_found = []
    with ThreadPoolExecutor(max_workers=config.MAX_PARALLEL_IMAGES) as pool:
        futures = {}
        for i in indices:
            post = job.posts[i]
            prompt = prompt_for(post)
            fut = pool.submit(
                client.generate_image, prompt, model_id, post.spec.aspect_ratio, size, job.read_reference(i)
            )
            futures[fut] = (i, prompt)
        for done, fut in enumerate(as_completed(futures), 1):
            i, prompt = futures[fut]
            try:
                job.add_version(i, fut.result(), make_version("generate", prompt))
            except GenerationError as e:
                errors_found.append(f"Post {job.posts[i].spec.number}: {e}")
            progress.progress(done / len(indices), text=f"{done}/{len(indices)} listas")
    progress.empty()
    for err in errors_found:
        st.error(err)
    if not errors_found:
        flash(f"✅ {len(indices)} imagen(es) generada(s).")
        st.rerun()


def reference_form(form_key: str, output_dir: str) -> None:
    """Formulario para crear un post a partir de una imagen de referencia.

    Si no hay trabajo abierto, crea uno nuevo con ese post.
    """
    with st.form(form_key, clear_on_submit=True):
        uploaded = st.file_uploader("Imagen de referencia", type=["png", "jpg", "jpeg", "webp"])
        instructions = st.text_area(
            "Qué cambiar respecto a la referencia",
            height=120,
            placeholder="Mismo estilo que la referencia, pero para Canadá: sustituye los símbolos de "
            "EE. UU. y Australia del cuerpo del Kiwi y del globo por símbolos de Canadá (hoja de arce, "
            "bandera, alce, Rocosas) y de Nueva Zelanda.",
        )
        texts = st.text_area(
            "Texto exacto de la imagen (opcional, una línea por elemento, en orden de importancia)",
            height=80,
            placeholder="MY KIWI ENGLISH\nLearn Canadian English",
        )
        st.caption("Si dejas el texto vacío, se conserva el de la referencia salvo lo que pidas cambiar.")
        submitted = st.form_submit_button("Añadir post", icon=":material/add_photo_alternate:")
    if not submitted:
        return
    if not uploaded or not instructions.strip():
        st.warning("Sube una imagen y escribe qué cambiar.")
        return
    reference = prepare_reference(uploaded.getvalue())
    aspect = closest_aspect_ratio(reference, config.ASPECT_RATIOS)
    job = st.session_state.get("job")
    if job is None:
        job_id, folder = new_job_folder(output_dir)
        job = Job(id=job_id, folder=folder, brief=instructions, style=DEFAULT_STYLE, posts=[])
        st.session_state.job = job
    idx = job.add_reference_post(reference, instructions, lines(texts), aspect)
    flash(f"Post {job.posts[idx].spec.number} añadido desde la referencia ({aspect}).")
    st.rerun()


# ---------------------------------------------------------------- barra lateral
with st.sidebar:
    st.title("🥝 My Kiwi Studio")

    api_key = secret_api_key()
    if not api_key:
        api_key = st.text_input("API key de Gemini", type="password", help="Mejor guárdala en el archivo .env")
    else:
        st.caption("🔑 API key configurada")

    st.segmented_control(
        "Modelo de imagen",
        list(config.IMAGE_MODELS),
        default=config.DEFAULT_IMAGE_MODEL,
        required=True,
        key="model_name",
        help="Nano Banana 2.1 para el día a día. Cambia a Pro si el texto o la composición no salen bien.",
    )
    st.segmented_control(
        "Resolución",
        config.IMAGE_SIZES,
        default=config.IMAGE_SIZES[0],
        required=True,
        key="size",
        help="1K = 1024 px, suficiente para Instagram.",
    )
    model_id = config.IMAGE_MODELS[st.session_state.model_name]
    st.caption(f"≈ US${config.estimate_cost(model_id, st.session_state.size):.3f} por imagen")

    output_dir = st.text_input("Carpeta de trabajos", value=config.OUTPUT_DIR)

    st.divider()
    st.subheader("Trabajos anteriores")
    past = list_jobs(output_dir)
    if past:
        chosen = st.selectbox("Trabajo", past, format_func=os.path.basename, label_visibility="collapsed")
        if st.button("Abrir trabajo", icon=":material/folder_open:", width="stretch"):
            st.session_state.job = Job.load(chosen)
            st.rerun()
    else:
        st.caption("Todavía no hay trabajos guardados.")

    if st.session_state.get("job") and st.button("Nuevo trabajo", icon=":material/add:", width="stretch"):
        del st.session_state["job"]
        st.rerun()

for msg in st.session_state.pop("flash", []):
    st.toast(msg)

client = None
if api_key:
    try:
        client = get_client(api_key)
    except GenerationError as e:
        st.error(str(e))

job: Job | None = st.session_state.get("job")

# ---------------------------------------------------------------- paso 1: nuevo trabajo
if job is None:
    st.header("Nuevo trabajo")
    if not client:
        st.info("Añade tu API key de Gemini para empezar.")

    tab_brief, tab_ref = st.tabs(["Desde el brief", "Desde una imagen de referencia"])
    with tab_brief:
        brief = st.text_area(
            "Pega aquí el brief de la clienta",
            height=320,
            placeholder="Post 1 – Argentina\nTitle: English for Families\nIs your child in this class too?\n"
            "¿Tu hijo también viene a esta clase?\n...",
        )
        style_options = ["auto"] + STYLE_KEYS
        style_choice = st.selectbox(
            "Estilo",
            style_options,
            format_func=lambda k: "Automático (lo sugiere la IA)" if k == "auto" else STYLES[k].name,
        )
        with st.expander("Ver los estilos disponibles"):
            for s in STYLES.values():
                st.markdown(f"**{s.name}**: {s.summary}")

        if st.button(
            "Interpretar brief",
            type="primary",
            icon=":material/auto_awesome:",
            disabled=not (client and brief.strip()),
        ):
            with st.spinner("Leyendo el brief..."):
                try:
                    spec = client.parse_brief(brief, config.TEXT_MODEL)
                except GenerationError as e:
                    st.error(str(e))
                    st.stop()
            style = spec.suggested_style if style_choice == "auto" else style_choice
            job_id, folder = new_job_folder(output_dir)
            job = Job(
                id=job_id,
                folder=folder,
                brief=brief,
                style=style,
                posts=[PostState(spec=p, style=style) for p in spec.posts],
            )
            job.save()
            st.session_state.job = job
            flash(f"Brief interpretado: {len(job.posts)} posts, estilo {STYLES[style].name}.")
            st.rerun()

    with tab_ref:
        st.caption(
            "Para cuando la clienta pide «una imagen como esta, pero para otro país». "
            "La imagen se envía al modelo como referencia de estilo y composición."
        )
        reference_form("ref_new", output_dir)
    st.stop()

# ---------------------------------------------------------------- paso 2: posts e imágenes
st.header(f"Trabajo {job.id}")
st.caption(f"📁 {job.folder}   ·   Gasto estimado: US${job.total_cost():.2f}")

with st.expander("Brief original"):
    st.text(job.brief)

style_posts = [i for i, p in enumerate(job.posts) if not p.is_reference]
pending = [i for i, p in enumerate(job.posts) if not p.versions]
all_posts = list(range(len(job.posts)))
price = config.estimate_cost(model_id, st.session_state.size)

with st.container(horizontal=True, vertical_alignment="bottom"):
    if style_posts:
        new_style = st.selectbox(
            "Estilo para todos los posts",
            STYLE_KEYS,
            index=STYLE_KEYS.index(job.style) if job.style in STYLE_KEYS else STYLE_KEYS.index(DEFAULT_STYLE),
            format_func=lambda k: STYLES[k].name,
            key=f"jobstyle_{job.id}",
            width=260,
        )
        if new_style != job.style:
            job.style = new_style
            for idx in style_posts:
                job.posts[idx].style = new_style
                st.session_state.pop(f"style_{job.id}_{idx}", None)
            job.save()
            flash(f"Estilo cambiado a {STYLES[new_style].name}. Pulsa «Nueva versión de todas» para regenerar.")
            st.rerun()
    gen_pending = st.button(
        f"Generar pendientes ({len(pending)}) · ≈US${price * len(pending):.2f}",
        type="primary",
        icon=":material/palette:",
        disabled=not (client and pending),
    )
    gen_all = st.button(
        f"Nueva versión de todas ({len(all_posts)}) · ≈US${price * len(all_posts):.2f}",
        icon=":material/autorenew:",
        disabled=not (client and all_posts),
        help="Genera otra imagen de cada post con el estilo y el modelo actuales. "
        "Las anteriores se conservan como versiones.",
    )
    if any(p.current for p in job.posts):
        st.download_button(
            "Descargar todas (ZIP)",
            data=job.zip_bytes(),
            file_name=f"my_kiwi_{job.id}.zip",
            mime="application/zip",
            icon=":material/download:",
        )

if gen_pending:
    generate_many(job, client, pending)
if gen_all:
    generate_many(job, client, all_posts)

with st.expander("Añadir post desde una imagen de referencia", icon=":material/add_photo_alternate:"):
    reference_form(f"ref_{job.id}", output_dir)

st.divider()

for i, post in enumerate(job.posts):
    spec = post.spec
    k = f"{job.id}_{i}"
    with st.container(border=True):
        left, right = st.columns([1.15, 1])

        # ----- izquierda: ficha editable
        with left:
            st.subheader(f"Post {spec.number}" + (f" · {spec.country}" if spec.country else ""))

            if post.is_reference:
                ref = job.read_reference(i)
                st.caption("Basado en imagen de referencia")
                if ref:
                    st.image(ref, width=220, alt=f"Referencia del post {spec.number}")
                with st.expander("Instrucciones y texto", expanded=not post.versions):
                    with st.form(f"form_{k}"):
                        instructions = st.text_area("Qué cambiar respecto a la referencia", spec.scene, height=120)
                        texts = st.text_area(
                            "Texto exacto (una línea por elemento)", "\n".join(spec.extra_text), height=80
                        )
                        aspect = st.selectbox(
                            "Formato", config.ASPECT_RATIOS, index=config.ASPECT_RATIOS.index(spec.aspect_ratio)
                        )
                        if st.form_submit_button("Guardar cambios", icon=":material/save:"):
                            post.spec = spec.model_copy(
                                update=dict(scene=instructions, extra_text=lines(texts), aspect_ratio=aspect)
                            )
                            job.save()
                            flash(f"Post {spec.number} guardado. Genera una nueva versión para aplicarlo.")
                            st.rerun()
            else:
                style_key = st.selectbox(
                    "Estilo",
                    STYLE_KEYS,
                    index=STYLE_KEYS.index(post.style) if post.style in STYLE_KEYS else 0,
                    format_func=lambda s: STYLES[s].name,
                    key=f"style_{k}",
                )
                if style_key != post.style:
                    post.style = style_key
                    job.save()

                with st.expander("Texto y escena", icon=":material/edit_note:", expanded=not post.versions):
                    with st.form(f"form_{k}"):
                        brand = st.text_input("Título de marca", spec.brand_title)
                        subtitle = st.text_input("Subtítulo", spec.subtitle)
                        phrases = st.text_area(
                            "Frases principales (una por línea: frase | traducción)",
                            phrases_to_text(spec.phrases),
                            height=110,
                        )
                        c1, c2 = st.columns([1, 2])
                        vlabel = c1.text_input("Etiqueta vocabulario", spec.vocabulary_label)
                        vocab = c2.text_area(
                            "Vocabulario (término = traducción)", vocab_to_text(spec.vocabulary), height=90
                        )
                        c3, c4 = st.columns(2)
                        maori = c3.text_input("Palabra māori", spec.maori_word)
                        aspect = c4.selectbox(
                            "Formato", config.ASPECT_RATIOS, index=config.ASPECT_RATIOS.index(spec.aspect_ratio)
                        )
                        question = st.text_input("Pregunta inferior", spec.question)
                        extra = st.text_area("Otro texto (una línea por elemento)", "\n".join(spec.extra_text), height=70)
                        scene = st.text_area("Escena (en inglés)", spec.scene, height=140)
                        if st.form_submit_button("Guardar cambios", icon=":material/save:"):
                            post.spec = spec.model_copy(
                                update=dict(
                                    brand_title=brand,
                                    subtitle=subtitle,
                                    phrases=text_to_phrases(phrases),
                                    vocabulary_label=vlabel,
                                    vocabulary=text_to_vocab(vocab),
                                    maori_word=maori,
                                    aspect_ratio=aspect,
                                    question=question,
                                    extra_text=lines(extra),
                                    scene=scene,
                                )
                            )
                            job.save()
                            flash(f"Post {spec.number} guardado. Genera una nueva versión para aplicarlo.")
                            st.rerun()

            with st.expander("Prompt", icon=":material/receipt_long:"):
                auto = build_post_prompt(post.spec, post.style, post.is_reference)
                custom = st.text_area(
                    "Prompt (puedes editarlo; vacío = automático)",
                    post.prompt_override or auto,
                    height=260,
                    # la clave cambia con el prompt, así el cuadro se refresca al editar la ficha
                    key=f"prompt_{k}_{hash(auto + post.prompt_override)}",
                )
                b1, b2 = st.columns(2)
                if b1.button("Usar este prompt", key=f"useprompt_{k}"):
                    post.prompt_override = "" if custom.strip() == auto.strip() else custom
                    job.save()
                    st.rerun()
                if post.prompt_override and b2.button("Volver al automático", key=f"resetprompt_{k}"):
                    post.prompt_override = ""
                    job.save()
                    st.rerun()
                if post.prompt_override:
                    st.caption("⚠️ Usando prompt manual: los cambios en la ficha no se aplicarán.")

        # ----- derecha: imagen
        with right:
            data = job.read_current(i)
            if data:
                st.image(data, width="stretch", alt=f"Imagen del post {spec.number}")
                cur = post.current
                st.caption(
                    f"v{post.selected + 1} · {MODEL_NAMES.get(cur.model, cur.model)} · {cur.size}"
                    + (f" · corrección: {cur.instruction}" if cur.instruction else "")
                )
                if len(post.versions) > 1:
                    sel = st.selectbox(
                        "Versión",
                        range(len(post.versions)),
                        index=post.selected,
                        format_func=lambda v, p=post: f"v{v + 1}"
                        + (" (corrección)" if p.versions[v].kind == "edit" else ""),
                        key=f"ver_{k}_{len(post.versions)}",
                    )
                    if sel != post.selected:
                        job.select(i, sel)
                        st.rerun()
            else:
                st.info("Sin imagen todavía.")

            a1, a2 = st.columns(2)
            if a1.button(
                "Nueva versión" if data else "Generar",
                icon=":material/autorenew:" if data else ":material/palette:",
                key=f"gen_{k}",
                disabled=not client,
                width="stretch",
            ):
                with st.spinner("Generando..."):
                    try:
                        prompt = prompt_for(post)
                        png = client.generate_image(
                            prompt, model_id, post.spec.aspect_ratio, st.session_state.size, job.read_reference(i)
                        )
                        job.add_version(i, png, make_version("generate", prompt))
                        st.rerun()
                    except GenerationError as e:
                        st.error(str(e))
            if data:
                a2.download_button(
                    "Descargar",
                    data=data,
                    file_name=job.final_name(i),
                    mime="image/png",
                    icon=":material/download:",
                    key=f"dl_{k}",
                    width="stretch",
                )
                with st.form(f"edit_{k}", clear_on_submit=True):
                    instruction = st.text_input(
                        "Corregir esta imagen",
                        placeholder="Ej: haz el globo más grande y cambia el cielo a atardecer",
                    )
                    if (
                        st.form_submit_button("Aplicar corrección", icon=":material/edit:", disabled=not client)
                        and instruction.strip()
                    ):
                        with st.spinner("Corrigiendo..."):
                            try:
                                png = client.edit_image(
                                    data, instruction, model_id, post.spec.aspect_ratio, st.session_state.size
                                )
                                job.add_version(
                                    i, png, make_version("edit", build_edit_prompt(instruction), instruction)
                                )
                                st.rerun()
                            except GenerationError as e:
                                st.error(str(e))
