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
st.markdown("Genera prompts e imágenes consistentes para My Kiwi Languages a partir de un brief.")

# Sidebar - Settings
with st.sidebar:
    st.header("Configuración")
    
    # Try to load from env or input
    api_key = st.text_input("Gemini API Key", type="password", value=os.environ.get("GOOGLE_API_KEY", ""))
    
    # Model Configuration
    st.markdown("### Modelos")
    text_model_options = ["gemini-2.5-flash", "gemini-3.0-flash", "gemini-2.5-flash-lite"]
    image_model_options = ["gemini-3.1-flash-image-preview", "gemini-2.5-flash-image", "gemini-3-pro-image-preview"]
    text_model_id = st.selectbox("Modelo de Texto", options=text_model_options, index=0)
    image_model_id = st.selectbox("Modelo de Imagen", options=image_model_options, index=0)
    
    output_dir = st.text_input("Carpeta de Salida", value="output")
    
    if st.button("Limpiar Galería"):
        if 'generated_content' in st.session_state:
            del st.session_state['generated_content']
        st.success("Galería limpiada.")

# Main Interface
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("1. Entrada")
    
    # Load default guidelines
    default_guidelines = ""
    if os.path.exists("brand_guidelines.txt"):
        with open("brand_guidelines.txt", "r", encoding="utf-8") as f:
            default_guidelines = f.read()

    guidelines = st.text_area("Guía de Marca / Estética", value=default_guidelines, height=200)
    
    brief = st.text_area("Brief del Cliente (Email/Mensaje)", height=150, placeholder="Ej: Necesitamos 3 posts para la semana que viene. Uno sobre phrasal verbs, otro un meme de viernes, y otro frase inspiradora.")
    
    generate_btn = st.button("🚀 Generar Contenido", type="primary")

# Initialize Session State
if 'generated_content' not in st.session_state:
    st.session_state.generated_content = None

# Initialize Generator if key is present
generator = None
if api_key:
    try:
        generator = ContentGenerator(api_key, text_model_id, image_model_id)
    except Exception as e:
        st.error(f"Error initializing generator: {e}")

# Logic Execution
if generate_btn and generator and brief:
    # 1. Generate Prompts
    with st.spinner("1/2: Analizando brief y diseñando prompts..."):
        try:
            # We use the provided 'guidelines' from the main UI
            result_json = generator.generate_prompts(brief, guidelines)

            st.session_state.generated_content = result_json
            st.session_state.results_cache = [] # reset image cache
            st.session_state.images_generated = False
            st.session_state.brief_used = brief
            
            # Initialize generated_images_data structure
            st.session_state.generated_images_data = {}
            posts = result_json.get('posts', [])
            for post_idx, post in enumerate(posts):
                st.session_state.generated_images_data[post_idx] = {
                    'id': post['id'],
                    'concept': post['concept'],
                    'description': post['description'],
                    'options': []
                }
                for i, prompt_data in enumerate(post['options']):
                    prompt = prompt_data.get('prompt', str(prompt_data)) if isinstance(prompt_data, dict) else str(prompt_data)
                    st.session_state.generated_images_data[post_idx]['options'].append({
                        'original_prompt': prompt,
                        'current_prompt': prompt,
                        'path': None,
                        'filename': None,
                        'status': 'pending',
                        'message': 'Pendiente - Presiona "Generar Imagen"'
                    })
            
            st.success("✅ Prompts generados exitosamente. Ahora puedes generar las imágenes individualmente.")
            st.rerun()
        except Exception as e:
            st.error(f"Error generando prompts: {e}")
            st.stop()

# Main Processor
if st.session_state.generated_content and generator:
    posts = st.session_state.generated_content.get('posts', [])

    # DISPLAY PHASE (Persistent)
    st.divider()
    st.subheader("Resultados - Generación Manual de Imágenes")
    st.info("💡 Haz clic en '🎨 Generar Imagen' para crear solo las imágenes que necesites, ahorrando tokens.")

    # Use the data stored in session_state for display
    if 'generated_images_data' in st.session_state:
        for post_idx, post_data in st.session_state.generated_images_data.items():
            st.markdown(f"### Post {post_data['id']}: {post_data['concept']}")
            st.write(post_data['description'])

            cols = st.columns(3) # Display 3 options side by side

            for i, option_data in enumerate(post_data['options']):
                with cols[i]:
                    st.caption(f"Opción {i+1}")
                    st.code(option_data['current_prompt'], language="text")

                    # Button to generate image on-demand
                    if option_data['status'] == 'pending' or option_data['status'] == 'error':
                        if st.button("🎨 Generar Imagen", key=f"gen_{post_data['id']}_{i+1}", type="primary"):
                            with st.spinner("Generando imagen..."):
                                img_filename = f"post_{post_data['id']}_opt_{i+1}_{datetime.now().strftime('%Y%m%d%H%M%S')}.png"
                                img_path = os.path.join(output_dir, img_filename)
                                
                                # Ensure output directory exists
                                os.makedirs(output_dir, exist_ok=True)
                                
                                success, msg = generator.generate_image(option_data['current_prompt'], img_path)
                                
                                if success:
                                    st.session_state.generated_images_data[post_idx]['options'][i].update({
                                        'path': img_path,
                                        'filename': img_filename,
                                        'status': 'generated',
                                        'message': 'Generado'
                                    })
                                    
                                    # Log generation
                                    log_data = [{
                                        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                        "brief_snippet": st.session_state.get('brief_used', '')[:30],
                                        "post_id": post_data['id'],
                                        "concept": post_data['concept'],
                                        "option_num": i+1,
                                        "prompt": option_data['current_prompt'],
                                        "file_path": img_path
                                    }]
                                    log_file = os.path.join(output_dir, "generation_log.csv")
                                    df_new = pd.DataFrame(log_data)
                                    if os.path.exists(log_file):
                                        df_old = pd.read_csv(log_file)
                                        df_final = pd.concat([df_old, df_new], ignore_index=True)
                                    else:
                                        df_final = df_new
                                    df_final.to_csv(log_file, index=False)
                                    
                                    st.toast(f"✅ Imagen generada para Post {post_data['id']}, Opción {i+1}")
                                    st.rerun()
                                else:
                                    st.session_state.generated_images_data[post_idx]['options'][i].update({
                                        'status': 'error',
                                        'message': msg
                                    })
                                    st.error(f"Error al generar: {msg}")
                                    st.rerun()
                    
                    if option_data['status'] == 'generated' and option_data['path'] and os.path.exists(option_data['path']):
                        st.image(option_data['path'], caption=f"Opción {i+1}", use_container_width=True)
                        st.success(option_data['message'])

                        # Individual Download Button
                        with open(option_data['path'], "rb") as file:
                            st.download_button(
                                label="⬇️ Descargar",
                                data=file,
                                file_name=option_data['filename'],
                                mime="image/png",
                                key=f"dl_{post_data['id']}_{i+1}"
                            )

                        # Regeneration UI
                        regen_key = f"regen_{post_data['id']}_{i+1}"
                        correction_prompt = st.text_input(
                            "Corrección (opcional)",
                            key=f"input_{regen_key}",
                            placeholder="Ej: Cambia el fondo a azul, agrega más texto..."
                        )

                        if st.button("🔄 Regenerar", key=f"btn_{regen_key}"):
                            if correction_prompt:
                                full_correction = f"{option_data['original_prompt']}\n\nCORRECTIONS: {correction_prompt}"

                                with st.spinner("Regenerando imagen..."):
                                    new_filename = f"post_{post_data['id']}_opt_{i+1}_v2_{datetime.now().strftime('%Y%m%d%H%M%S')}.png"
                                    new_path = os.path.join(output_dir, new_filename)

                                    regen_success, regen_msg = generator.generate_image(full_correction, new_path)

                                    if regen_success:
                                        # Update session state for the regenerated image
                                        st.session_state.generated_images_data[post_idx]['options'][i].update({
                                            'current_prompt': full_correction,
                                            'path': new_path,
                                            'filename': new_filename,
                                            'status': 'generated', # Reset status to generated so it shows up
                                            'message': 'Imagen regenerada'
                                        })

                                        # Log regeneration
                                        log_file = os.path.join(output_dir, "generation_log.csv")
                                        log_entry = {
                                            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                            "brief_snippet": st.session_state.get('brief_used', '')[:30],
                                            "post_id": post_data['id'],
                                            "concept": post_data['concept'],
                                            "option_num": f"{i+1}_v2",
                                            "prompt": full_correction,
                                            "file_path": new_path
                                        }
                                        df_new = pd.DataFrame([log_entry])
                                        if os.path.exists(log_file):
                                            df_old = pd.read_csv(log_file)
                                            df_final = pd.concat([df_old, df_new], ignore_index=True)
                                        else:
                                            df_final = df_new
                                        df_final.to_csv(log_file, index=False)

                                        st.toast("✅ Imagen regenerada y registrada.")
                                        st.rerun() # Rerun to display the new image
                                    else:
                                        st.error(f"Error al regenerar: {regen_msg}")
                            else:
                                st.warning("Ingresa instrucciones de corrección para regenerar.")
                    elif option_data['status'] == 'error':
                        st.error(option_data['message'])
                    elif option_data['status'] == 'pending':
                        st.info("⏳ Presiona '🎨 Generar Imagen'")

    st.divider()

    # Download ZIP button (visible when images have been generated)
    generated_count = sum(
        1 for post_data in st.session_state.generated_images_data.values() 
        for opt in post_data['options'] 
        if opt['status'] == 'generated'
    )
    
    if generated_count > 0:
        st.info(f"📊 {generated_count} imagen(es) generada(s)")
        
        # Create ZIP file
        zip_path = "output_files.zip"
        if os.path.exists(output_dir):
            import shutil
            shutil.make_archive("output_files", 'zip', output_dir)
        
        if os.path.exists(zip_path):
            with open(zip_path, "rb") as fp:
                st.download_button(
                    label="📦 DESCARGAR TODO (ZIP)",
                    data=fp,
                    file_name="nano_banana_output.zip",
                    mime="application/zip",
                    type="primary",
                    help="Descarga todas las imágenes generadas y el registro en un solo archivo."
                )

else:
    # Initial State or no content
    if not generate_btn:
        st.info("👆 Ingresa el brief y presiona 'Generar Ideas e Imágenes' para comenzar.")

# Results Display (Historical/Persisted if needed, or unnecessary if we show during gen)
# Removed the old interactive column to keep it simple as requested: "input -> generate all -> done"

