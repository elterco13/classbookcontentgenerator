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
        generator = ContentGenerator(api_key)
    except Exception as e:
        None # Handle silently or let later calls fail gracefully

# Logic Execution
if generate_btn and generator and brief:
    
    # 1. Generate Prompts
    with st.spinner("1/2: Analizando brief y diseñando prompts..."):
        try:
            result_json = generator.generate_prompts(brief, guidelines)
            st.session_state.generated_content = result_json
        except Exception as e:
            st.error(f"Error generando prompts: {e}")
            st.stop()

    # 2. Bulk Generate Images
    posts = st.session_state.generated_content.get('posts', [])
    total_images = sum(len(p['options']) for p in posts)
    
    if total_images > 0:
        progress_bar = st.progress(0, text="2/2: Generando imágenes (esto tomará unos momentos)...")
        log_data = []
        images_generated_count = 0
        
        st.subheader("Resultados de la Generación")
        
        for post in posts:
            st.markdown(f"### Post {post['id']}: {post['concept']}")
            st.write(post['description'])
            
            cols = st.columns(3) # Display 3 options side by side
            
            for i, prompt in enumerate(post['options']):
                with cols[i]:
                    st.caption(f"Opción {i+1}")
                    st.code(prompt, language="text")
                    # ... existing code ...
                    img_filename = f"post_{post['id']}_opt_{i+1}_{datetime.now().strftime('%Y%m%d%H%M%S')}.png"
                    img_path = os.path.join(output_dir, img_filename)
                    
                    # Generate Image
                    success, msg = generator.generate_image(prompt, img_path)
                    
                    if success:
                        st.image(img_path, caption=f"Opción {i+1}", use_container_width=True)
                        
                        # Individual Download Button
                        with open(img_path, "rb") as file:
                            st.download_button(
                                label="⬇️ Descargar Imagen",
                                data=file,
                                file_name=img_filename,
                                mime="image/png",
                                key=f"dl_{post['id']}_{i+1}"
                            )

                        st.success("Generado")
                        
                        # Regeneration UI
                        regen_key = f"regen_{post['id']}_{i+1}"
                        correction_prompt = st.text_input(
                            "Corrección (opcional)", 
                            key=f"input_{regen_key}",
                            placeholder="Ej: Cambia el fondo a azul, agrega más texto..."
                        )
                        
                        if st.button("🔄 Regenerar", key=f"btn_{regen_key}"):
                            if correction_prompt:
                                full_correction = f"{prompt}\n\nCORRECTIONS: {correction_prompt}"
                                
                                with st.spinner("Regenerando imagen..."):
                                    new_filename = f"post_{post['id']}_opt_{i+1}_v2_{datetime.now().strftime('%Y%m%d%H%M%S')}.png"
                                    new_path = os.path.join(output_dir, new_filename)
                                    
                                    regen_success, regen_msg = generator.generate_image(full_correction, new_path)
                                    
                                    if regen_success:
                                        st.image(new_path, caption=f"Opción {i+1} - Regenerada", use_container_width=True)
                                        st.success("✅ Imagen regenerada")
                                        
                                        log_data.append({
                                            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                            "brief_snippet": brief[:30],
                                            "post_id": post['id'],
                                            "concept": post['concept'],
                                            "option_num": f"{i+1}_v2",
                                            "prompt": full_correction,
                                            "file_path": new_path
                                        })
                                    else:
                                        st.error(f"Error: {regen_msg}")
                            else:
                                st.warning("Ingresa instrucciones de corrección")
                        
                        
                        log_data.append({
                            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "brief_snippet": brief[:30],
                            "post_id": post['id'],
                            "concept": post['concept'],
                            "option_num": i+1,
                            "prompt": prompt,
                            "file_path": img_path
                        })
                    else:
                        st.error(f"Error: {msg}")
                
                images_generated_count += 1
                progress_bar.progress(images_generated_count / total_images)

        # 3. Save Log
        if log_data:
            log_file = os.path.join(output_dir, "generation_log.csv")
            df_new = pd.DataFrame(log_data)
            if os.path.exists(log_file):
                df_old = pd.read_csv(log_file)
                df_final = pd.concat([df_old, df_new], ignore_index=True)
            else:
                df_final = df_new
            
            df_final.to_csv(log_file, index=False)
            st.toast("✅ Registro y archivos guardados correctamente.")
            st.balloons()
            st.success(f"¡Proceso completado! Se han generado {total_images} imágenes.")

            # Create ZIP for download (Critical for Cloud Deployment)
            import shutil
            shutil.make_archive("output_files", 'zip', output_dir)
            
            st.divider()
            with open("output_files.zip", "rb") as fp:
                btn = st.download_button(
                    label="📦 DESCARGAR TODO (ZIP)",
                    data=fp,
                    file_name="nano_banana_output.zip",
                    mime="application/zip",
                    type="primary",
                    help="Descarga todas las imágenes y el registro en un solo archivo."
                )
            st.success("✅ Archivo ZIP listo para descarga.")
    else:
        st.warning("No se encontraron ideas de posts en la respuesta del modelo.")

# Results Display (Historical/Persisted if needed, or unnecessary if we show during gen)
# Removed the old interactive column to keep it simple as requested: "input -> generate all -> done"

