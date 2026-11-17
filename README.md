# 🥝 My Kiwi Studio

Genera las imágenes de redes sociales de **My Kiwi Languages** a partir del brief de la clienta, siempre con el mismo estilo, personaje y tipografía.

## Cómo funciona

1. **Pegas el brief.** Gemini lo convierte en una ficha por post: título de marca, subtítulo, frases bilingües, vocabulario, palabra māori, pregunta y escena.
2. **Revisas las fichas.** Puedes corregir cualquier texto antes de generar. El texto de la imagen sale de la ficha, copiado tal cual.
3. **Generas las imágenes** con **Nano Banana 2.1** o **Nano Banana Pro**, que eliges en la barra lateral.
4. **Corriges** con una instrucción ("haz el globo más grande"): se edita la imagen existente en vez de empezar de cero. Cada intento queda como versión y puedes volver a cualquiera.
5. **Variedad:** cambia el estilo o el modelo y pulsa «Nueva versión de todas». Las imágenes anteriores siguen disponibles como versiones.
6. **Desde una imagen de referencia:** para los pedidos del tipo «una imagen como esta, pero para Canadá». Subes la imagen, escribes qué cambiar y, si quieres, el texto exacto. La imagen se envía al modelo como referencia. Puedes crear un trabajo solo con eso o añadir el post a un trabajo abierto.
7. **Descargas** cada imagen o todas en un ZIP. Además, todo queda guardado en `trabajos/DD-MM-YY/` (`01.png`, `02.png`… más `versiones/` y `job.json`) y puedes reabrir trabajos anteriores.

## Estilos

Están definidos como texto fijo en [`kiwi/styles.py`](kiwi/styles.py), a partir de los posts entregados en 2026. No se envían imágenes de referencia, así que cada imagen solo paga su propio prompt.

| Estilo | Cuándo |
|---|---|
| Storybook acuarela | Familias, comunidad, salud, escuela, vocabulario y palabra māori |
| Editorial geométrico | Trabajo, destinos, estudiar en NZ, LinkedIn, campañas |
| Marco cultural | Frases de conversación con fuerte identidad del país |
| Cartoon vibrante | Posts simples con una o dos frases |

Para ajustar un estilo o el personaje, edita ese archivo. El prompt final se construye en [`kiwi/prompt_builder.py`](kiwi/prompt_builder.py) y se puede ver (y editar a mano) en la app, en "🧾 Prompt".

## Instalación

Necesitas Python 3.11 o superior y una API key de Gemini con facturación activa. Los modelos de imagen no tienen nivel gratuito.

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Abre `.env` y pega tu clave en `GOOGLE_API_KEY=`. Luego:

```bash
streamlit run app.py
```

## Costes aproximados (noviembre de 2026)

| Modelo | 1K | 2K | 4K |
|---|---|---|---|
| Nano Banana 2.1 | US$0.034 | US$0.050 | US$0.113 |
| Nano Banana Pro | US$0.134 | US$0.134 | US$0.24 |

Una tarea de 6 posts a 1K con Nano Banana 2.1 cuesta unos US$0.20. Interpretar el brief usa `gemini-3.8-flash`, que tiene nivel gratuito. La app muestra el gasto estimado de cada trabajo.

## Publicar en Streamlit Community Cloud

1. Sube la rama a GitHub y, en [share.streamlit.io](https://share.streamlit.io), crea la app con `app.py` como archivo principal y Python 3.11 o superior.
2. En **Advanced settings → Secrets** pega:
   ```toml
   GOOGLE_API_KEY = "tu_clave"
   ```
3. **Haz la app privada** (Settings → Sharing) e invita solo a quien deba usarla. La app usa tu clave, así que cualquiera con el enlace podría gastar créditos.

En la nube los archivos se borran cuando la app se reinicia o se duerme, así que **descarga el ZIP al terminar cada trabajo**. El historial de trabajos solo se conserva en la versión local.

## Tests

```bash
pip install -r requirements-dev.txt
pytest
```
