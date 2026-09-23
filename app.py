import json
import os
import re
import tempfile
import unicodedata
from pathlib import Path

import streamlit as st
from groq import Groq

st.set_page_config(
    page_title="Asesor Técnico FesterParedes",
    page_icon="🏗️",
    layout="centered",
)

st.title("🏗️ Asesor Técnico FesterParedes IA")
st.caption("Consulta fichas técnicas y enseña al asistente las respuestas oficiales de tu tienda.")

# -----------------------------
# Configuración
# -----------------------------
try:
    api_key = os.environ.get("GROQ_API_KEY") or st.secrets.get("GROQ_API_KEY", "")
except Exception:
    api_key = os.environ.get("GROQ_API_KEY", "")

if not api_key:
    st.error("Falta configurar la clave GROQ_API_KEY en los Secrets de Streamlit.")
    st.stop()

client = Groq(api_key=api_key)
MODELO = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")
MEMORIA_PATH = Path(os.environ.get("FESTER_MEMORY_FILE", "memoria_aprendizaje.json"))
MENSAJE_SIN_RESPUESTA = (
    "No encuentro información oficial suficiente para responder con seguridad. "
    "Por favor comunícate con un especialista al **3317011786**."
)

# -----------------------------
# Memoria persistente de retroalimentación
# -----------------------------
def cargar_memoria():
    try:
        if MEMORIA_PATH.exists():
            datos = json.loads(MEMORIA_PATH.read_text(encoding="utf-8"))
            return datos if isinstance(datos, list) else []
    except (OSError, json.JSONDecodeError) as error:
        st.warning(f"No se pudo leer la memoria de aprendizaje: {error}")
    return []


def guardar_memoria(memoria):
    """Escritura atómica para no dejar el JSON corrupto si la app se reinicia."""
    try:
        MEMORIA_PATH.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=MEMORIA_PATH.parent, delete=False
        ) as archivo:
            json.dump(memoria, archivo, ensure_ascii=False, indent=2)
            temporal = archivo.name
        os.replace(temporal, MEMORIA_PATH)
        return True
    except OSError as error:
        st.error(f"No se pudo guardar la retroalimentación: {error}")
        return False


if "messages" not in st.session_state:
    st.session_state.messages = []
if "memoria_aprendizaje" not in st.session_state:
    st.session_state.memoria_aprendizaje = cargar_memoria()
if "pregunta_pendiente" not in st.session_state:
    st.session_state.pregunta_pendiente = ""
if "mostrar_formulario" not in st.session_state:
    st.session_state.mostrar_formulario = False

# -----------------------------
# Normalización y búsqueda
# -----------------------------
def normalizar(texto):
    texto = unicodedata.normalize("NFKD", texto.lower())
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9ñ]+", " ", texto).strip()


def tokens(texto):
    return {token for token in normalizar(texto).split() if len(token) > 2}


def similitud(a, b):
    """Jaccard con un pequeño bono por coincidencia exacta de producto."""
    ta, tb = tokens(a), tokens(b)
    if not ta or not tb:
        return 0.0
    puntuacion = len(ta & tb) / len(ta | tb)
    productos = re.findall(r"\b(?:cl|cr|cf|cm|c[0-9]{2,3})[- ]?[0-9]{1,3}\b", normalizar(a))
    if productos and any(producto in normalizar(b) for producto in productos):
        puntuacion += 0.25
    return min(puntuacion, 1.0)


def buscar_memoria(pregunta, minimo=0.58):
    mejor = None
    mejor_puntuacion = 0.0
    for leccion in st.session_state.memoria_aprendizaje:
        puntuacion = similitud(pregunta, leccion.get("pregunta", ""))
        if puntuacion > mejor_puntuacion:
            mejor_puntuacion = puntuacion
            mejor = leccion
    return mejor if mejor_puntuacion >= minimo else None


@st.cache_data(show_spinner="Leyendo fichas técnicas...")
def extraer_fichas():
    paginas = []
    try:
        import fitz  # PyMuPDF
    except ImportError:
        return paginas

    for ruta in sorted(Path(".").glob("*.pdf")):
        try:
            with fitz.open(ruta) as documento:
                for numero, pagina in enumerate(documento, start=1):
                    texto = pagina.get_text("text").strip()
                    if texto:
                        paginas.append(
                            {
                                "archivo": ruta.name,
                                "pagina": numero,
                                "texto": texto,
                            }
                        )
        except Exception as error:
            print(f"Error leyendo {ruta.name}: {error}")
    return paginas


def buscar_fichas(pregunta, limite=3):
    consulta = tokens(pregunta)
    resultados = []
    for ficha in extraer_fichas():
        texto = f"{ficha['archivo']} {ficha['texto']}"
        palabras = tokens(texto)
        coincidencias = len(consulta & palabras)
        if coincidencias:
            # El nombre del PDF y los códigos de producto pesan más que palabras genéricas.
            nombre = normalizar(ficha["archivo"])
            bono_producto = sum(3 for codigo in re.findall(r"(?:cl|cr|cf|cm)[ -]?\d+", normalizar(pregunta)) if codigo in nombre)
            puntuacion = coincidencias + bono_producto
            resultados.append((puntuacion, ficha))
    resultados.sort(key=lambda elemento: elemento[0], reverse=True)
    return [ficha for _, ficha in resultados[:limite]]


# -----------------------------
# Historial y formulario de aprendizaje
# -----------------------------
for mensaje in st.session_state.messages:
    with st.chat_message(mensaje["role"]):
        st.markdown(mensaje["content"])

if st.session_state.mostrar_formulario:
    st.warning("🎓 Modo aprendizaje activo")
    st.info(f"Enséñame la respuesta oficial para: **{st.session_state.pregunta_pendiente}**")
    with st.form("formulario_retroalimentacion", clear_on_submit=True):
        respuesta = st.text_area(
            "Respuesta oficial de la tienda",
            placeholder="Producto, preparación, rendimiento, aplicación y cualquier advertencia relevante...",
            height=160,
        )
        guardar = st.form_submit_button("Guardar retroalimentación")

    if guardar:
        if not respuesta.strip():
            st.error("Escribe una respuesta antes de guardarla.")
        else:
            pregunta = st.session_state.pregunta_pendiente.strip()
            memoria = st.session_state.memoria_aprendizaje
            existente = next(
                (item for item in memoria if normalizar(item.get("pregunta", "")) == normalizar(pregunta)),
                None,
            )
            if existente:
                existente["respuesta"] = respuesta.strip()
            else:
                memoria.append({"pregunta": pregunta, "respuesta": respuesta.strip()})
            if guardar_memoria(memoria):
                st.session_state.mostrar_formulario = False
                st.success("✅ Retroalimentación guardada. La usaré en consultas similares.")
                st.rerun()

# -----------------------------
# Chat
# -----------------------------
if prompt := st.chat_input("¿Qué producto o problema de obra deseas consultar?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    prompt_normalizado = normalizar(prompt)

    if re.search(r"\b(hola|holis|saludos|buenos? dias|buenas? tardes|buenas? noches)\b", prompt_normalizado):
        respuesta = "¡Hola! Soy tu Asesor Técnico FesterParedes. ¿En qué producto o problema de obra te puedo apoyar?"
        st.session_state.messages.append({"role": "assistant", "content": respuesta})
        with st.chat_message("assistant"):
            st.markdown(respuesta)
        st.stop()

    leccion = buscar_memoria(prompt)
    if leccion:
        respuesta = leccion["respuesta"]
        st.session_state.messages.append({"role": "assistant", "content": respuesta})
        with st.chat_message("assistant"):
            st.markdown(respuesta)
        st.stop()

    fichas = buscar_fichas(prompt)
    contexto = "\n\n".join(
        f"[Ficha: {ficha['archivo']} | Página {ficha['pagina']}]\n{ficha['texto']}"
        for ficha in fichas
    )

    if not contexto:
        respuesta = MENSAJE_SIN_RESPUESTA
        st.session_state.messages.append({"role": "assistant", "content": respuesta})
        st.session_state.pregunta_pendiente = prompt
        st.session_state.mostrar_formulario = True
        with st.chat_message("assistant"):
            st.markdown(respuesta)
        st.rerun()

    sistema = f"""
Eres el Asesor Técnico Senior de Fester México. Responde en español, con tono amable,
profesional y claro. Sé conciso: máximo dos párrafos y usa viñetas solo si ayudan.

REGLAS OBLIGATORIAS:
1. Usa exclusivamente la información de las fichas técnicas incluidas abajo y la pregunta del cliente.
2. Nunca inventes rendimientos, proporciones, compatibilidades, tiempos de secado o usos.
3. Si la ficha no contiene información suficiente para responder exactamente, responde ÚNICAMENTE:
   {MENSAJE_SIN_RESPUESTA}
4. Si el cliente proporciona m², calcula solo con un rendimiento explícito de la ficha y muestra la operación.
5. Si pregunta por seguridad, preparación de superficie o aplicación, menciona las precauciones que aparezcan en la ficha.

FICHAS TÉCNICAS RECUPERADAS:
{contexto}
"""

    with st.chat_message("assistant"):
        try:
            completion = client.chat.completions.create(
                model=MODELO,
                messages=[
                    {"role": "system", "content": sistema},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.0,
                max_tokens=500,
            )
            respuesta = (completion.choices[0].message.content or "").strip()
            if not respuesta or "3317011786" in respuesta or "No encuentro información oficial" in respuesta:
                respuesta = MENSAJE_SIN_RESPUESTA
                st.session_state.pregunta_pendiente = prompt
                st.session_state.mostrar_formulario = True

            st.markdown(respuesta)
            st.session_state.messages.append({"role": "assistant", "content": respuesta})
            if st.session_state.mostrar_formulario:
                st.rerun()
        except Exception as error:
            st.error(f"Error en el motor de IA: {error}")

with st.sidebar:
    st.subheader("Estado")
    st.write(f"📄 Páginas indexadas: **{len(extraer_fichas())}**")
    st.write(f"🎓 Lecciones guardadas: **{len(st.session_state.memoria_aprendizaje)}**")
    st.caption("La memoria se guarda en memoria_aprendizaje.json. En Streamlit Cloud necesitarás una base de datos o almacenamiento persistente para conservarla después de reiniciar la app.")
