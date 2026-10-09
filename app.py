import streamlit as st
import os
import pandas as pd
from logic import ContentGenerator
from datetime import datetime

# Page Config
st.set_page_config(
    page_title="Nano Banana Automator",
    page_icon="🍌",
    layout="wide"
)

# Application Title
st.title("🍌 Nano Banana Content Automator")
st.markdown("Genera prompts e imágenes consistentes para **My Kiwi Languages** a partir de un brief.")

# Sidebar - Settings
with st.sidebar:
    st.header("Configuración")
    
    # API Key Input
    api_key = st.text_input("Gemini API Key", type="password", value=os.environ.get("GOOGLE_API_KEY", ""))
    
    # Model Configuration
    st.markdown("### Modelos")
    text_model_options = [
        "gemini-2.5-flash",
        "gemini-3.5-flash-lite",
        "gemini-3.0-flash",
        "gemini-2.5-pro"
    ]
    image_model_options = [
        "gemini-3.1-flash-image-preview",
        "gemini-3-pro-image-preview",
        "imagen-3.0-generate-002",
        "gemini-2.5-flash-image"
    ]
    
    text_model_id = st.selectbox(
        "Modelo de Texto",
        options=text_model_options,
        index=0,
        help="Recomendado: gemini-2.5-flash para rapidez o gemini-3.5-flash-lite"
    )
    image_model_id = st.selectbox(
        "Modelo de Imagen",
        options=image_model_options,
        index=0,
        help="Recomendado: gemini-3.1-flash-image-preview o gemini-3-pro-image-preview (Nano Banana Pro)"
    )
    
    output_dir = st.text_input("Carpeta de Salida", value="output")
    
    if st.button("🗑️ Limpiar Galería"):
        if 'generated_content' in st.session_state:
            del st.session_state['generated_content']
        if 'generated_images_data' in st.session_state:
            del st.session_state['generated_images_data']
        st.success("Galería limpiada.")
        st.rerun()

# Main Interface: Input Section
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("1. Entrada Brief & Marca")
    
    # Load default guidelines from file or session state
    if 'guidelines_text' not in st.session_state:
        default_guidelines = ""
        if os.path.exists("brand_guidelines.txt"):
            with open("brand_guidelines.txt", "r", encoding="utf-8") as f:
                default_guidelines = f.read()
        st.session_state.guidelines_text = default_guidelines

    guidelines = st.text_area("Guía de Marca / Estética", value=st.session_state.guidelines_text, height=200)

    if st.button("💾 Guardar Guía de Marca", help="Guarda este texto en el archivo para que se cargue automáticamente siempre."):
        with open("brand_guidelines.txt", "w", encoding="utf-8") as f:
            f.write(guidelines)
        st.session_state.guidelines_text = guidelines
        st.success("✅ Guía de marca guardada en el archivo. Se cargará automáticamente cada vez que inicies la app.")
    
    brief = st.text_area(
        "Brief del Cliente (Email/Mensaje)",
        height=150,
        placeholder="Ej: Necesitamos 3 posts para la semana que viene. Uno sobre phrasal verbs, otro un meme de viernes, y otro frase inspiradora."
    )
    
    generate_btn = st.button("🚀 Generar Prompts de Contenido", type="primary")

# Initialize Session State
if 'generated_content' not in st.session_state:
    st.session_state.generated_content = None

# Initialize Generator if key is present
generator = None
if api_key:
    try:
        generator = ContentGenerator(api_key, text_model_id, image_model_id)
    except Exception as e:
        st.error(f"Error al inicializar el generador: {e}")

# Helper for logging generation
def log_generation(post_id, concept, option_num, prompt, file_path):
    log_data = [{
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "brief_snippet": st.session_state.get('brief_used', '')[:30],
        "post_id": post_id,
        "concept": concept,
        "option_num": option_num,
        "prompt": prompt,
        "file_path": file_path
    }]
    log_file = os.path.join(output_dir, "generation_log.csv")
    df_new = pd.DataFrame(log_data)
    if os.path.exists(log_file):
        df_old = pd.read_csv(log_file)
        df_final = pd.concat([df_old, df_new], ignore_index=True)
    else:
        df_final = df_new
    df_final.to_csv(log_file, index=False)

# Logic Execution: Generate Prompts
if generate_btn and generator and brief:
    with st.spinner("Analizando brief y diseñando prompts estructurados..."):
        try:
            result_json = generator.generate_prompts(brief, guidelines)
            st.session_state.generated_content = result_json
            st.session_state.brief_used = brief
            
            # Initialize generated_images_data structure
            st.session_state.generated_images_data = {}
            posts = result_json.get('posts', [])
            for post_idx, post in enumerate(posts):
                st.session_state.generated_images_data[post_idx] = {
                    'id': post.get('id', post_idx + 1),
                    'concept': post.get('concept', f"Post {post_idx+1}"),
                    'description': post.get('description', ''),
                    'options': []
                }
                for i, prompt_data in enumerate(post.get('options', [])):
                    prompt = prompt_data.get('prompt', str(prompt_data)) if isinstance(prompt_data, dict) else str(prompt_data)
                    style_label = "Pop Educational" if i == 0 else ("Storybook" if i == 1 else "Creative Fusion")
                    st.session_state.generated_images_data[post_idx]['options'].append({
                        'style_name': style_label,
                        'original_prompt': prompt,
                        'current_prompt': prompt,
                        'path': None,
                        'filename': None,
                        'status': 'pending',
                        'message': 'Pendiente'
                    })
            
            st.success("✅ Prompts generados exitosamente. Selecciona qué imágenes deseas generar a continuación.")
            st.rerun()
        except Exception as e:
            st.error(f"Error generando prompts: {e}")
            st.stop()

# Main Processor Display Phase
if st.session_state.generated_content and generator and 'generated_images_data' in st.session_state:
    st.divider()
    st.subheader("Resultados y Generación de Imágenes")
    
    # Global & Style Batch Generation Action Bar
    st.markdown("### ⚡ Acciones de Generación Masiva")
    b_col1, b_col2, b_col3, b_col4 = st.columns(4)
    
    def process_batch(option_filter=None):
        """
        Processes batch image generation.
        option_filter: None for ALL pending images, or int (0, 1, 2) for specific style index.
        """
        os.makedirs(output_dir, exist_ok=True)
        pending_targets = []
        
        for post_idx, post_data in st.session_state.generated_images_data.items():
            for i, opt in enumerate(post_data['options']):
                if option_filter is not None and i != option_filter:
                    continue
                if opt['status'] != 'generated':
                    pending_targets.append((post_idx, i))
                    
        if not pending_targets:
            st.info("No hay imágenes pendientes en la selección elegida.")
            return

        progress_bar = st.progress(0)
        status_text = st.empty()
        total = len(pending_targets)
        
        for idx, (post_idx, i) in enumerate(pending_targets):
            post_data = st.session_state.generated_images_data[post_idx]
            opt = post_data['options'][i]
            
            status_text.text(f"Generando Post {post_data['id']} (Opción {i+1}: {opt['style_name']})... [{idx+1}/{total}]")
            
            img_filename = f"post_{post_data['id']}_opt_{i+1}_{datetime.now().strftime('%Y%m%d%H%M%S')}.png"
            img_path = os.path.join(output_dir, img_filename)
            
            success, msg = generator.generate_image(opt['current_prompt'], img_path)
            
            if success:
                st.session_state.generated_images_data[post_idx]['options'][i].update({
                    'path': img_path,
                    'filename': img_filename,
                    'status': 'generated',
                    'message': 'Generado'
                })
                log_generation(post_data['id'], post_data['concept'], i+1, opt['current_prompt'], img_path)
            else:
                st.session_state.generated_images_data[post_idx]['options'][i].update({
                    'status': 'error',
                    'message': msg
                })
            
            progress_bar.progress((idx + 1) / total)
            
        status_text.empty()
        progress_bar.empty()
        st.toast(f"✅ Procesamiento completado para {total} imagen(es).")
        st.rerun()

    with b_col1:
        if st.button("🚀 Generar TODAS las Imágenes", type="primary", use_container_width=True):
            process_batch(option_filter=None)
            
    with b_col2:
        if st.button("🎨 Generar TODAS (Opción 1: Pop)", use_container_width=True):
            process_batch(option_filter=0)
            
    with b_col3:
        if st.button("🖌️ Generar TODAS (Opción 2: Storybook)", use_container_width=True):
            process_batch(option_filter=1)
            
    with b_col4:
        if st.button("✨ Generar TODAS (Opción 3: Creative)", use_container_width=True):
            process_batch(option_filter=2)

    st.divider()

    # Display Individual Posts Cards
    for post_idx, post_data in st.session_state.generated_images_data.items():
        st.markdown(f"### Post {post_data['id']}: {post_data['concept']}")
        st.caption(post_data['description'])

        cols = st.columns(3) # 3 options side by side

        for i, option_data in enumerate(post_data['options']):
            with cols[i]:
                st.markdown(f"**Opción {i+1}: {option_data['style_name']}**")
                st.code(option_data['current_prompt'], language="text")

                # Single generate button if pending or error
                if option_data['status'] in ['pending', 'error']:
                    if st.button("🎨 Generar Imagen", key=f"gen_{post_data['id']}_{i+1}", type="secondary"):
                        with st.spinner("Generando imagen..."):
                            os.makedirs(output_dir, exist_ok=True)
                            img_filename = f"post_{post_data['id']}_opt_{i+1}_{datetime.now().strftime('%Y%m%d%H%M%S')}.png"
                            img_path = os.path.join(output_dir, img_filename)
                            
                            success, msg = generator.generate_image(option_data['current_prompt'], img_path)
                            
                            if success:
                                st.session_state.generated_images_data[post_idx]['options'][i].update({
                                    'path': img_path,
                                    'filename': img_filename,
                                    'status': 'generated',
                                    'message': 'Generado'
                                })
                                log_generation(post_data['id'], post_data['concept'], i+1, option_data['current_prompt'], img_path)
                                st.toast(f"✅ Imagen generada: Post {post_data['id']}, Opción {i+1}")
                                st.rerun()
                            else:
                                st.session_state.generated_images_data[post_idx]['options'][i].update({
                                    'status': 'error',
                                    'message': msg
                                })
                                st.error(f"Error: {msg}")
                                st.rerun()
                
                # If generated, display image & options
                if option_data['status'] == 'generated' and option_data['path'] and os.path.exists(option_data['path']):
                    st.image(option_data['path'], caption=f"Opción {i+1} ({option_data['style_name']})", use_container_width=True)
                    st.success(option_data['message'])

                    # Download button
                    with open(option_data['path'], "rb") as file:
                        st.download_button(
                            label="⬇️ Descargar PNG",
                            data=file,
                            file_name=option_data['filename'],
                            mime="image/png",
                            key=f"dl_{post_data['id']}_{i+1}"
                        )

                    # Individual Regeneration
                    regen_key = f"regen_{post_data['id']}_{i+1}"
                    correction_prompt = st.text_input(
                        "Instrucciones de corrección",
                        key=f"input_{regen_key}",
                        placeholder="Ej: Cambia el fondo a azul, haz el texto más grande..."
                    )

                    if st.button("🔄 Regenerar", key=f"btn_{regen_key}"):
                        if correction_prompt:
                            full_correction = f"{option_data['original_prompt']}\n\nCORRECTIONS: {correction_prompt}"

                            with st.spinner("Regenerando imagen..."):
                                new_filename = f"post_{post_data['id']}_opt_{i+1}_v2_{datetime.now().strftime('%Y%m%d%H%M%S')}.png"
                                new_path = os.path.join(output_dir, new_filename)

                                regen_success, regen_msg = generator.generate_image(full_correction, new_path)

                                if regen_success:
                                    st.session_state.generated_images_data[post_idx]['options'][i].update({
                                        'current_prompt': full_correction,
                                        'path': new_path,
                                        'filename': new_filename,
                                        'status': 'generated',
                                        'message': 'Imagen regenerada'
                                    })
                                    log_generation(post_data['id'], post_data['concept'], f"{i+1}_v2", full_correction, new_path)
                                    st.toast("✅ Imagen regenerada correctamente.")
                                    st.rerun()
                                else:
                                    st.error(f"Error al regenerar: {regen_msg}")
                        else:
                            st.warning("Ingresa instrucciones de corrección para regenerar.")
                            
                elif option_data['status'] == 'error':
                    st.error(option_data['message'])
                elif option_data['status'] == 'pending':
                    st.info("⏳ Pendiente de generación")

    st.divider()

    # Zip Download section
    generated_count = sum(
        1 for post_data in st.session_state.generated_images_data.values() 
        for opt in post_data['options'] 
        if opt['status'] == 'generated'
    )
    
    if generated_count > 0:
        st.info(f"📊 {generated_count} imagen(es) generada(s) hasta ahora")
        
        zip_path = "output_files.zip"
        if os.path.exists(output_dir):
            import shutil
            shutil.make_archive("output_files", 'zip', output_dir)
        
        if os.path.exists(zip_path):
            with open(zip_path, "rb") as fp:
                st.download_button(
                    label="📦 DESCARGAR TODO EN ZIP",
                    data=fp,
                    file_name="nano_banana_output.zip",
                    mime="application/zip",
                    type="primary",
                    help="Descarga todas las imágenes generadas y el registro CSV en un archivo ZIP."
                )
