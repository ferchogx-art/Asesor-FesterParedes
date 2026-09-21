import streamlit as st
import os
import glob
from groq import Groq

st.set_page_config(page_title="Asesor Técnico Fester", page_icon="🏗️", layout="centered")
st.title("🏗️ Asesor Técnico FesterParedes IA")
st.write("Respuestas ejecutivas inmediatas para ingenieros en obra.")

# 1. Conectar con la API de Groq
api_key = os.environ.get("GROQ_API_KEY", st.secrets.get("GROQ_API_KEY", ""))
if not api_key:
    st.error("Falta configurar la clave GROQ_API_KEY en los Secrets.")
    st.stop()

client = Groq(api_key=api_key)

# =========================================================================
# 2. TU DICCIONARIO PERSONALIZADO (ALIMENTACIÓN DIRECTA REDACTADA POR TI)
# =========================================================================
# Aquí puedes editar, quitar o agregar las preguntas básicas que más te hacen.
# Si el usuario escribe algo similar, la IA usará esta base de datos exacta.
DICCIONARIO_EXPERTOS = {
    "economico": (
        "Para un presupuesto limitado y prevención de filtraciones sin goteras activas, la opción ideal es la línea **Fester A**. "
        "Se recomienda aplicar **Fester A3** (protección por 3 años) o **Fester A5** (protección por 5 años). "
        "Son impermeabilizantes acrílicos económicos de fácil aplicación que no requieren mano de obra especializada.\n\n"
        "**Procedimiento rápido:**\n"
        "1. Limpiar la superficie de polvo y falsas adherencias.\n"
        "2. Aplicar una capa de Fester Acriton Sellador diluido en agua para sellar poros.\n"
        "3. Aplicar dos capas directas de Fester A (Rendimiento total aproximado de 1 a 1.5 Litros por m² a dos capas)."
    ),
    "vaportite": (
        "**Fester Vaportite 550** es un impermeabilizante asfáltico base solvente de consistencia pastosa. "
        "Es ideal para aplicarse en cimentaciones, muros de contención, jardineras y zonas bajo tierra.\n"
        "- **Rendimiento:** 1 Litro por m² por capa (se recomiendan dos capas).\n"
        "- **Primario obligatorio:** Requiere la aplicación previa de **Fester Hidroprimer** para asegurar el anclaje."
    ),
    "festerbond": (
        "**Festerbond** es un adherente de consistencia lechosa base resinas acrílicas.\n"
        "- **Uso principal:** Funciona como unión de concreto nuevo a viejo, fortificador de morteros y sellador de superficies porosas.\n"
        "- **Rendimiento como sellador:** Rinde aproximadamente 5 m² por litro diluido 1 a 1 con agua."
    )
}

# 3. Carga inteligente de PDFs de fondo para consultas avanzadas
@st.cache_resource
def extraer_conocimiento_fester():
    texto_completo = []
    archivos_validos = glob.glob("*.pdf")
    for ruta in archivos_validos:
        nombre_archivo = os.path.basename(ruta)
        try:
            import fitz  # PyMuPDF
            doc = fitz.open(ruta)
            for num_pag, pagina in enumerate(doc):
                texto_pag = pagina.get_text()
                if texto_pag.strip():
                    texto_completo.append({
                        "origen": nombre_archivo,
                        "referencia": f"Pág. {num_pag + 1}",
                        "texto": texto_pag
                    })
        except Exception as e:
            print(f"Error leyendo {nombre_archivo}: {e}")
    return texto_completo

base_conocimiento = extraer_conocimiento_fester()

# 4. Historial de visualización
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 5. Lógica del Chat Ejecutivo
if prompt := st.chat_input("¿Qué rendimiento o producto deseas validar de forma directa?"):
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    prompt_lower = prompt.lower()
    respuesta_directa = ""

    # REVISIÓN AUTOMÁTICA EN TU DICCIONARIO REDACTADO
    if any(x in prompt_lower for x in ["barato", "economico", "económica", "bajo costo", "presupuesto", "inversion"]):
        respuesta_directa = DICCIONARIO_EXPERTOS["economico"]
    elif "vaportite" in prompt_lower:
        respuesta_directa = DICCIONARIO_EXPERTOS["vaportite"]
    elif "festerbond" in prompt_lower:
        respuesta_directa = DICCIONARIO_EXPERTOS["festerbond"]

    with st.chat_message("assistant"):
        if respuesta_directa:
            # Si la pregunta coincide con tu diccionario, responde de inmediato SIN usar PDFs revueltos
            st.markdown(respuesta_directa)
            st.session_state.messages.append({"role": "assistant", "content": respuesta_directa})
        else:
            # Si es una pregunta diferente, la IA busca de forma estricta en los textos pero obligada a ser ULTRA BREVE
            contexto_manuales = ""
            palabras = [p for p in prompt_lower.split() if len(p) > 2]
            puntuaciones = []
            for item in base_knowledge := base_conocimiento:
                texto_manual = item["texto"].lower()
                puntos = sum(2 for p in palabras if p in texto_manual)
                if puntos > 0:
                    puntuaciones.append((puntos, item))
            puntuaciones.sort(key=lambda x: x, reverse=True)
            for puntos, res in puntuaciones[:2]:
                contexto_manuales += f"\n[{res['origen']} - {res['referencia']}]\n{res['texto']}\n"

            contexto_sistema = (
                "Eres el Asesor Técnico Ejecutivo de Fester México.\n"
                "REGLAS OBLIGATORIAS DE REDACCIÓN:\n"
                "1. Prohibido dar respuestas largas, explicaciones teóricas o generar tablas gigantes.\n"
                "2. Responde en un máximo de 1 o 2 párrafos muy cortos. Ve directo al grano.\n"
                "3. Si te preguntan por impermeabilizantes acrílicos económicos, responde puntualmente recomendando la línea Fester A3 o A5.\n"
                "4. Si la información provista abajo no responde con exactitud milimétrica la pregunta, di: 'No dispongo del dato exacto en la ficha técnica, por favor valida con catálogo físico.'\n\n"
                f"TEXTO BASE:\n{contexto_manuales}"
            )

            try:
                completion = client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=[
                        {"role": "system", "content": contexto_sistema},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.0,
                    max_tokens=250, # Límite muy corto para obligarla a no rellenar con texto basura
                )
                response = completion.choices.message.content
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
            except Exception as e:
                st.error(f"Error: {e}")

