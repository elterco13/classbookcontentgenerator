# 🍌 Nano Banana Content Automator

Herramienta de automatización para generar contenido de redes sociales (prompts e imágenes) para **My Kiwi Languages** usando Gemini AI.

## 🚀 Características

- **Generación automática de prompts** usando Gemini 2.5 Flash Lite
- **Generación de imágenes** con Gemini 3 Pro Image Preview (Nano Banana)
- **Regeneración individual** con instrucciones de corrección personalizadas
- **Registro completo** de todas las generaciones en CSV
- **Interfaz simple** con Streamlit

## 📋 Requisitos

- Python 3.8+
- API Key de Google Gemini ([Obtener aquí](https://aistudio.google.com/apikey))

## 🛠️ Instalación Local

1. Clona el repositorio:
```bash
git clone https://github.com/elterco13/classbookcontentgenerator.git
cd classbookcontentgenerator
```

2. Instala las dependencias:
```bash
pip install -r requirements.txt
```

3. Configura tu API Key:
   - Crea un archivo `.env` en la raíz del proyecto
   - Agrega: `GOOGLE_API_KEY=tu_api_key_aqui`

4. Ejecuta la aplicación:
```bash
streamlit run app.py
```

## ☁️ Deployment en Streamlit Cloud

1. Haz fork de este repositorio
2. Ve a [share.streamlit.io](https://share.streamlit.io)
3. Conecta tu repositorio de GitHub
4. En **Advanced settings** → **Secrets**, agrega:
```toml
GOOGLE_API_KEY = "tu_api_key_aqui"
```
5. ¡Deploy!

## 📖 Uso

1. **Ingresa tu API Key** en la barra lateral (o configúrala en `.env`)
2. **Revisa/edita las guías de marca** en el área de texto
3. **Pega el brief del cliente** en el campo correspondiente
4. **Haz clic en "🚀 Generar Contenido"**
5. **Espera** mientras se generan los prompts e imágenes
6. **Regenera imágenes individuales** si necesitas correcciones

## 📁 Estructura del Proyecto

```
content_automation_tool/
├── app.py                    # Interfaz Streamlit
├── logic.py                  # Lógica de generación (Gemini API)
├── requirements.txt          # Dependencias Python
├── brand_guidelines.txt      # Guías de marca predeterminadas
├── .env                      # Variables de entorno (no incluido en repo)
└── output/                   # Carpeta de salida (generada automáticamente)
    ├── *.png                 # Imágenes generadas
    └── generation_log.csv    # Registro de generaciones
```

## 🎨 Modelos Utilizados

- **Texto**: `gemini-2.5-flash-lite` (generación de prompts)
- **Imagen**: `gemini-3-pro-image-preview` (Nano Banana Pro)
  - Resolución: 1024x1024 (1:1)
  - Mejor renderizado de texto
  - Proceso de "pensamiento" para mejor calidad

## 📝 Licencia

MIT License - Siéntete libre de usar y modificar este proyecto.

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Por favor abre un issue primero para discutir cambios mayores.
