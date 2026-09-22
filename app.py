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
        "charola": "cl52 cl-52",
        "salitre": "cr65 cr66",
    }
    consulta = consulta.lower()
    consulta_busqueda = f"{consulta} {historial.lower()}"
    for termino, reemplazo in equivalencias.items():
        if termino in consulta_busqueda:
            consulta_busqueda += f" {reemplazo}"

    # Detectamos la zona de forma estricta para bloquear archivos cruzados
    es_charola_baño = any(x in consulta_busqueda for x in ["charola", "baño", "regadera", "cl52", "cl-52"])
    es_techo_azotea = any(x in consulta_busqueda for x in ["techo", "losa", "azotea", "lluvia", "acriton", "proshield"])

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
        
        # 🛡️ FILTROS DE EXCLUSIÓN TOTALMENTE LIMPIOS Y CORREGIDOS:
        if es_charola_baño and ("vaportite" in nombre or "mip" in nombre or "cr6" in nombre):
            continue  
        if es_techo_azotea and ("cl52" in nombre or "cr65" in nombre or "cf" in nombre):
            continue  

        puntos = sum(5 for palabra in palabras if palabra in texto)
        puntos += sum(35 for palabra in palabras if palabra in nombre)
        if puntos:
            resultados.append((puntos, item))

    if resultados:
        resultados.sort(key=lambda x: x[0], reverse=True)
    
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
    es_azotea = any(palabra in texto for palabra in ("azotea", "techo", "losa", "impermeabilizar mi azote"))
    ya_respondio = any(
        palabra in historial.lower()
        for palabra in ("¿ya cuenta con filtraciones", "preventivo", "superficie", "encharcamientos")
    )
    return pide_recomendacion and es_azotea and not ya_respondio


if prompt := st.chat_input("¿Qué problema tienes en obra o qué producto deseas validar?"):
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    prompt_lower = prompt.lower().strip()
    historial_texto = " ".join(
        message["content"] for message in st.session_state.messages[-4:]
    ).lower()

    if re.search(r"\b(hola|buen[oa]s?|saludos|qué tal)\b", prompt_lower):
        guardar_respuesta(
            "¡Hola! Soy tu amigo Asesor FesterParedes, a la orden. ¿En qué te puedo apoyar hoy?"
        )
        st.stop()

    if es_sondeo_inicial_azotea(prompt_lower, historial_texto):
        guardar_respuesta(
            "Con gusto te ayudo a elegir el sistema para tu azotea. Antes de recomendarte un producto, "
            "¿ya cuenta con filtraciones o es un trabajo preventivo? También indícame: ¿qué superficie "
            "tiene (concreto, impermeabilizante anterior, cerámica u otra)?, ¿tiene humedad o encharcamientos?, "
            "¿qué durabilidad buscas y prefieres una solución acrílica o asfáltica?"
        )
        st.stop()

    contexto_manuales = buscar_fichas(prompt, historial_texto)
    mensaje_no_info = (
        "Lo siento, esa información técnica no viene completa en esta ficha. "
        "Por favor comunícate al **3317011786** para atenderte con mucho gusto."
    )

    contexto_sistema = f"""
Eres el Asesor Técnico Senior de Fester México y atiendes en español. Tu tono es amable, claro, práctico y profesional. Responde de forma ejecutiva en un máximo de 2 o 3 párrafos cortos.

REGLAS TÉCNICAS CRÍTICAS:
1. CHAROLAS DE BAÑO Y REGADERAS: El único producto oficial para interiores y zonas húmedas bajo recubrimiento cerámico es FESTER CL-52 (Acrílico base agua). Está estrictamente PROHIBIDO recomendar Vaportite o sistemas base solvente en baños.
2. Cada rendimiento o consumo que des debe mencionar el nombre del producto, la unidad de medida (L/m² o kg/m²) y estar basado estrictamente en el texto oficial de abajo.
3. Si el usuario te aduce metros cuadrados (m²), realiza el cálculo matemático multiplicando esa área por el rendimiento que marca la ficha técnica del CL-52 para decirle cuántos litros o botes requiere comprar.
4. Para CR66, indica que es cementoso elástico de dos componentes para terrazas o albercas; si el área supera 25 m², advierte sobre la necesidad de ejecutar juntas de dilatación para evitar que el sistema falle.
5. Si un dato técnico exacto no viene en el texto de abajo, di exactamente el mensaje: {mensaje_no_info}

TEXTO REAL EXTRAÍDO DE TU FICHA TÉCNICA:
{contexto_manuales if contexto_manuales else 'Vacio'}
"""

    with st.chat_message("assistant"):
        try:
            completion = client.chat.completions.create(
                model=MODELO_FAVORITO,
                messages=[
                    {"role": "system", "content": contexto_sistema},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.0,
                max_tokens=600,
            )
            response = completion.choices.message.content
            st.session_state.messages.append({"role": "assistant", "content": response})
            st.markdown(response)
        except Exception as error:
            st.error(f"Error en motor IA: {error}")


