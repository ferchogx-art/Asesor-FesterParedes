import glob
import os
import re

import streamlit as st
from groq import Groq

st.set_page_config(page_title="Asesor Técnico Fester", page_icon="🏗️", layout="centered")
st.title("🏗️ Asesor Técnico FesterParedes IA")
st.write("Sistema experto con consulta directa a fichas técnicas oficiales.")

# 1. Conectar con la API de Groq
api_key = os.environ.get("GROQ_API_KEY", st.secrets.get("GROQ_API_KEY", ""))
if not api_key:
    st.error("Falta configurar la clave GROQ_API_KEY en los Secrets.")
    st.stop()

client = Groq(api_key=api_key)
MODELO_FAVORITO = "openai/gpt-oss-120b"

# 2. Carga inteligente de fichas técnicas en formato PDF
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
                    texto_completo.append(
                        {
                            "origen": nombre_archivo,
                            "referencia": f"Pág. {num_pag + 1}",
                            "texto": texto_pag,
                        }
                    )
        except Exception as e:
            print(f"Error leyendo {nombre_archivo}: {e}")

    return texto_completo


base_conocimiento = extraer_conocimiento_fester()

# Panel visual de diagnóstico
num_bloques = len(base_conocimiento)
if num_bloques == 0:
    st.error("⚠️ ALERTA: No se detectaron PDFs en la raíz de GitHub.")
else:
    st.success(
        f"📊 Base de datos activa: Conectado a las fichas técnicas individuales ({num_bloques} páginas)."
    )

# 3. Historial de chat persistente
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])


def guardar_respuesta(respuesta):
    """Muestra y conserva una respuesta generada sin perder el historial."""
    with st.chat_message("assistant"):
        st.markdown(respuesta)
    st.session_state.messages.append({"role": "assistant", "content": respuesta})


# 4. Procesamiento de la consulta
if prompt := st.chat_input("¿Qué problema tienes en obra o qué producto deseas validar?"):
    with st.chat_message("user"):
        st.markdown(prompt)

    st.session_state.messages.append({"role": "user", "content": prompt})
    prompt_lower = prompt.lower().strip()
    historial_texto = " ".join(
        message["content"] for message in st.session_state.messages[-6:]
    ).lower()

    # Respuestas deterministas para las intenciones más frecuentes.
    es_saludo = bool(
        re.search(
            r"\b(hola|buen[oa]s?(?: días?| tardes?| noches?)?|saludos|qué tal)\b",
            prompt_lower,
        )
    )
    menciona_impermeabilizante = any(
        termino in prompt_lower
        for termino in ("impermeabilizante", "impermeabilizar", "impermeabilizacion")
    )
    pide_lista = any(
        termino in prompt_lower
        for termino in ("qué existen", "cuales existen", "cuáles hay", "opciones", "tipos")
    )

    if es_saludo:
        guardar_respuesta(
            "¡Hola! Soy tu amigo Asesor FesterParedes, a la orden. ¿En qué te puedo apoyar?"
        )

    elif menciona_impermeabilizante and pide_lista:
        guardar_respuesta(
            "En Fester contamos principalmente con dos opciones de impermeabilizantes: "
            "la **línea Fester A**, de tecnología acrílica, y la **línea Premium**, "
            "con diferentes soluciones y durabilidades. También existen soluciones "
            "asfálticas para necesidades específicas. ¿Buscas impermeabilizar una azotea, "
            "una cimentación, un baño u otra área?"
        )

    else:
        # Búsqueda en las fichas reales. Se agregan equivalencias para entender el lenguaje
        # cotidiano del cliente (por ejemplo, chapopote = producto Vaportite).
        consulta_busqueda = prompt_lower
        equivalencias = {
            "chapopote": "vaportite asfalto impermeabilizante",
            "asfalto": "vaportite impermeabilizante asfaltico",
            "impermeabilizante asfaltico": "vaportite",
            "impermeabilizante asfáltico": "vaportite",
            "acrilico": "fester a",
            "acrílico": "fester a",
            "techo": "azotea",
            "losa": "azotea",
        }
        for termino, reemplazo in equivalencias.items():
            if termino in consulta_busqueda:
                consulta_busqueda += f" {reemplazo}"

        palabras = [
            palabra
            for palabra in re.findall(r"[\wáéíóúüñ-]+", consulta_busqueda)
            if len(palabra) > 2
            and palabra
            not in {
                "qué",
                "que",
                "cuál",
                "cual",
                "cómo",
                "como",
                "para",
                "por",
                "con",
                "del",
                "una",
                "uno",
                "los",
                "las",
                "quiero",
                "necesito",
            }
        ]

        es_charola = any(
            x in historial_texto
            for x in ("charola", "baño", "regadera", "cl52", "cl-52", "muros de mi baño")
        )
        es_salitre = any(
            x in historial_texto for x in ("salitre", "cr65", "cr66", "cr-65", "cr-66")
        )
        es_techo = any(
            x in historial_texto
            for x in ("techo", "losa", "azotea", "lluvia", "proshield", "fester a", "azoteas")
        )

        puntuaciones = []
        for item_doc in base_conocimiento:
            texto_manual = item_doc["texto"].lower()
            nombre_archivo = item_doc["origen"].lower()

            if es_charola and "cl" not in nombre_archivo and "cl52" not in texto_manual:
                continue
            if es_salitre and "cr" not in nombre_archivo:
                continue
            if es_techo and ("cr" in nombre_archivo or "cl" in nombre_archivo or "cf" in nombre_archivo):
                continue

            puntos = sum(5 for palabra in palabras if palabra in texto_manual)
            if any(palabra in nombre_archivo for palabra in palabras):
                puntos += 25
            if puntos > 0:
                puntuaciones.append((puntos, item_doc))

        contexto_manuales = ""
        if puntuaciones:
            puntuaciones.sort(key=lambda resultado: resultado[0], reverse=True)
            for _, resultado in puntuaciones[:5]:
                contexto_manuales += (
                    f"\n[Ficha Oficial: {resultado['origen']} - {resultado['referencia']}]\n"
                    f"{resultado['texto']}\n"
                )

        mensaje_no_info = (
            "Lo siento, esa información te la puede dar un compañero. "
            "Comunícate al **3317011786**."
        )

        contexto_sistema = (
            "Eres el Asesor Técnico Senior de Fester México y atiendes en español.\n"
            "Tu tono es amable, claro, práctico y profesional; eres el amigo Asesor "
            "FesterParedes. Responde en máximo 1 o 2 párrafos cortos.\n\n"
            "REGLAS OBLIGATORIAS:\n"
            "1. Para rendimientos, consumos, tiempos, preparación y aplicación, usa "
            "exclusivamente los datos de las fichas oficiales incluidas abajo. Di que el "
            "rendimiento está basado en la ficha técnica y menciona el producto y la unidad. "
            "Nunca inventes números.\n"
            "2. Si el cliente dice chapopote o impermeabilizante asfáltico, verifica si se "
            "refiere a Vaportite y pregunta o aclara antes de asumir otro producto.\n"
            "3. Si pide una recomendación (por ejemplo, para una azotea), NO recomiendes "
            "todavía: primero haz preguntas breves para conocer el área y la necesidad. "
            "Como mínimo pregunta si prefiere una solución acrílica o asfáltica, el tipo de "
            "superficie, si tiene humedad o impermeabilizante anterior y la durabilidad buscada. "
            "Después de recibir esas respuestas, recomienda solo con base en las fichas.\n"
            "4. Si no queda claro qué producto busca, sondea con una pregunta concreta. "
            "Puedes mencionar Fester A (acrílica), la línea Premium y Vaportite (asfáltico) "
            "para ayudarle a identificarlo.\n"
            "5. Si la ficha no contiene la respuesta o no sabes algo, responde exactamente: "
            f"{mensaje_no_info}\n"
            "6. Está estrictamente prohibido dar números de asistencia o teléfonos distintos "
            "de 3317011786.\n\n"
            f"TEXTO OFICIAL DE LAS FICHAS INDIVIDUALES:\n"
            f"{contexto_manuales if contexto_manuales else 'Vacio'}"
        )

        with st.chat_message("assistant"):
            try:
                mensajes_ia = [{"role": "system", "content": contexto_sistema}]
                mensajes_ia.extend(st.session_state.messages[-6:])

                completion = client.chat.completions.create(
                    model=MODELO_FAVORITO,
                    messages=mensajes_ia,
                    temperature=0.0,
                    max_tokens=450,
                )
                response = completion.choices[0].message.content
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
            except Exception as e:
                st.error(f"Error en motor IA: {e}")
