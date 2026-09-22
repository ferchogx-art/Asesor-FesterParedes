import glob
import os
import re
import streamlit as st
from groq import Groq

st.set_page_config(page_title="Asesor Técnico Fester", page_icon="🏗️", layout="centered")
st.title("🏗️ Asesor Técnico FesterParedes IA")
st.write("Sistema experto con consulta directa a fichas técnicas oficiales.")

api_key = os.environ.get("GROQ_API_KEY", st.secrets.get("GROQ_API_KEY", ""))
if not api_key:
    st.error("Falta configurar la clave GROQ_API_KEY en los Secrets.")
    st.stop()

client = Groq(api_key=api_key)
MODELO_FAVORITO = "openai/gpt-oss-120b"


@st.cache_resource
def extraer_conocimiento_fester():
    texto_completo = []
    for ruta in glob.glob("*.pdf"):
        nombre_archivo = os.path.basename(ruta)
        try:
            import fitz

            with fitz.open(ruta) as doc:
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
        except Exception as error:
            print(f"Error leyendo {nombre_archivo}: {error}")
    return texto_completo


base_conocimiento = extraer_conocimiento_fester()
num_bloques = len(base_conocimiento)
if num_bloques == 0:
    st.error("⚠️ ALERTA: No se detectaron PDFs en la raíz de GitHub.")
else:
    st.success(f"📊 Base de datos activa: {num_bloques} páginas de fichas técnicas.")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])


def guardar_respuesta(respuesta):
    with st.chat_message("assistant"):
        st.markdown(respuesta)
    st.session_state.messages.append({"role": "assistant", "content": respuesta})


def buscar_fichas(consulta, historial):
    equivalencias = {
        "chapopote": "vaportite asfalto impermeabilizante desplantes",
        "asfalto": "vaportite impermeabilizante asfaltico",
        "impermeabilizante asfaltico": "vaportite",
        "acrilico": "acriton fester a",
        "acrílico": "acriton fester a",
        "techo": "azotea",
        "losa": "azotea",
        "terraza": "cr66 impermeabilizante cementoso",
        "ceramica": "cr66",
        "vitropiso": "cr66",
        "charola": "cl52",
        "salitre": "cr65 cr66",
    }
    consulta = consulta.lower()
    consulta_busqueda = f"{consulta} {historial.lower()}"
    for termino, reemplazo in equivalencias.items():
        if termino in consulta_busqueda:
            consulta_busqueda += f" {reemplazo}"

    palabras = [
        palabra
        for palabra in re.findall(r"[\wáéíóúüñ-]+", consulta_busqueda)
        if len(palabra) > 2
        and palabra not in {
            "qué", "que", "cuál", "cual", "cómo", "como", "para", "por",
            "con", "del", "una", "uno", "los", "las", "quiero", "necesito",
            "tiene", "cuenta", "puede", "donde", "desde", "sobre",
        }
    ]

    resultados = []
    for item in base_conocimiento:
        texto = item["texto"].lower()
        nombre = item["origen"].lower()
        puntos = sum(5 for palabra in palabras if palabra in texto)
        puntos += sum(25 for palabra in palabras if palabra in nombre)
        if puntos:
            resultados.append((puntos, item))

    resultados.sort(key=lambda resultado: resultado[0], reverse=True)
    
    # CONTROL DE TOKENS EXTRICTO: Bajamos de 8 a los 2 fragmentos más exactos para no saturar los 8,000 tokens de Groq
    return "".join(
        f"\n[Ficha oficial: {item['origen']} - {item['referencia']}]\n{item['texto']}\n"
        for _, item in resultados[:2]
    )


def es_sondeo_inicial_azotea(texto, historial):
    texto = f"{historial} {texto}".lower()
    pide_recomendacion = any(
        frase in texto
        for frase in ("qué me recomiendas", "cual me recomiendas", "cuál me recomiendas", "recomienda", "que imper", "que producto")
    )
    es_azotea = any(palabra in texto for palabra in ("azotea", "techo", "losa", "charola", "baño"))
    ya_respondio = any(
        palabra in historial.lower()
        for palabra in ("¿ya cuenta con filtraciones", "¿es preventivo", "¿tiene filtraciones", "indícame")
    )
    return pide_recomendacion and es_azotea and not ya_respondio


if prompt := st.chat_input("¿Qué problema tienes en obra o qué producto deseas validar?"):
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    prompt_lower = prompt.lower().strip()
    
    # Recortamos el historial de memoria enviado para ahorrar presupuesto de tokens
    historial_texto = " ".join(
        message["content"] for message in st.session_state.messages[-2:]
    ).lower()

    if re.search(r"\b(hola|buen[oa]s?|saludos|qué tal)\b", prompt_lower):
        guardar_respuesta(
            "¡Hola! Soy tu amigo Asesor FesterParedes, a la orden. ¿En qué te puedo apoyar?"
        )
        st.stop()

    if es_sondeo_inicial_azotea(prompt_lower, historial_texto):
        guardar_respuesta(
            "Con gusto te ayudo a elegir el sistema ideal. Antes de recomendarte un producto específico, "
            "compárteme: ¿en qué área se localiza exactamente el problema (losa, muro o charola)?, ¿cuántos metros cuadrados tiene en total?, "
            "¿ya cuenta con filtraciones activas o es un trabajo preventivo? e indícame si buscas una durabilidad específica."
        )
        st.stop()

    contexto_manuales = buscar_fichas(prompt, historial_texto)
    mensaje_no_info = (
        "Lo siento, esa información te la puede dar un compañero. "
        "Comunícate al **3317011786**."
    )

    # PROMPT CORREGIDO Y CERRADO PERFECTAMENTE PARA EVITAR ERRORES DE SINTAXIS
    contexto_sistema = f"""
Eres el Asesor Técnico Senior de Fester México y atiendes en español. Tu tono es amable, claro, práctico y profesional. Responde de forma ejecutiva en máximo 2 párrafos cortos.

REGLAS CRÍTICAS:
1. Usa exclusivamente las fichas oficiales incluidas al final para beneficios, características, rendimientos, consumos, diluciones, tiempos, preparación y aplicación. Si un dato no aparece en las fichas recuperadas, no lo inventes ni aproximes, responde exactamente: {mensaje_no_info}
2. Cada rendimiento debe mencionar producto, unidad y que está basado en la ficha técnica. 
3. Si te preguntan cantidad para charolas de baño usando Fester CL-52, busca el rendimiento por m² en el texto de abajo y realiza el cálculo matemático exacto multiplicando las charolas por sus metros cuadrados.
4. Para azoteas, explica la preparación y el sistema únicamente con respaldo documental: superficie limpia, barrida y sin polvo; sellador Acriton y su rendimiento; resanador Acriton para juntas menores a 4 mm; Superseal P para juntas mayores.
5. Para CR66, indica que es cementoso de dos componentes; si la terraza supera los 25 m², incluye obligatoriamente la advertencia técnica sobre la necesidad de ejecutar juntas de dilatación estructurales para evitar que el sistema falle.

TEXTO OFICIAL EXTRAÍDO DE TU FICHA EN GITHUB:
{contexto_manuales if contexto_manuales else 'Vacio'}
"""

    with st.chat_message("assistant"):
        try:
            # Enviamos solo la interacción actual más el contexto del sistema optimizado
            completion = client.chat.completions.create(
                model=MODELO_FAVORITO,
                messages=[
                    {"role": "system", "content": contexto_sistema},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.0,
                max_tokens=350,
            )
            response = completion.choices.message.content
            st.session_state.messages.append({"role": "assistant", "content": response})
            st.markdown(response)
        except Exception as error:
            st.error(f"Error en motor IA: {error}")
