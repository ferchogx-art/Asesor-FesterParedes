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
    st.success(f"📊 Base de datos activa: {num_bloques} páginas de fichas técnicas listas.")

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
    consulta_limpia = f"{consulta} {historial}".lower()
    
    # ENRUTAMIENTO ESTRICTO DE INGENIERÍA: Detectamos la zona real de la obra
    es_charola_zona = any(x in consulta_limpia for x in ["charola", "baño", "regadera", "cl52", "cl-52"])
    es_salitre_zona = any(x in consulta_limpia for x in ["salitre", "cr65", "cr-65"])
    es_asfalto_zona = any(x in consulta_limpia for x in ["chapopote", "asfalto", "vaportite", "cimentacion", "desplante"])
    es_techo_zona = any(x in consulta_limpia for x in ["techo", "losa", "azotea", "acriton", "fester a", "proshield"])

    equivalencias = {
        "chapopote": "vaportite asfalto impermeabilizante desplantes",
        "asfalto": "vaportite impermeabilizante asfaltico",
        "acrilico": "acriton fester a",
        "techo": "azotea",
        "losa": "azotea",
        "terraza": "cr66",
        "vitropiso": "cr66",
    }
    
    consulta_busqueda = consulta_limpia
    for termino, reemplazo in equivalencias.items():
        if termino in consulta_busqueda:
            consulta_busqueda += f" {reemplazo}"

    palabras = [
        palabra for palabra in re.findall(r"[\wáéíóúüñ-]+", consulta_busqueda)
        if len(palabra) > 2 and palabra not in {
            "qué", "que", "cuál", "cual", "cómo", "como", "para", "por",
            "con", "del", "una", "uno", "los", "las", "quiero", "necesito",
        }
    ]

    resultados = []
    for item in base_conocimiento:
        texto = item["texto"].lower()
        nombre = item["origen"].lower()
        
        # APLICACIÓN DE CANDADOS DE EXCLUSIÓN COMPLETA SIN ERRORES DE SINTAXIS
        if es_charola_zona and "cl" not in nombre and "cl52" not in texto:
            continue  
        if es_salitre_zona and "cr65" not in nombre and "cr-65" not in texto:
            continue
        if es_asfalto_zona and "vaportite" not in nombre:
            continue
        if es_techo_zona and ("cl" in nombre or "cr" in nombre or "cf" in nombre):
            continue

        puntos = sum(5 for palabra in palabras if palabra in texto)
        puntos += sum(25 for palabra in palabras if palabra in nombre)
        if puntos > 0:
            resultados.append((puntos, item))

    # ORDENAMIENTO PERFECTO
    resultados.sort(key=lambda x: x[0], reverse=True)
    
    # Traemos las 2 páginas con mayor coincidencia exacta para no saturar los tokens de Groq
    return "".join(
        f"\n[Ficha oficial: {item['origen']} - {item['referencia']}]\n{item['texto']}\n"
        for _, item in resultados[:2]
    )


def es_sondeo_inicial_azotea(texto, historial):
    texto = f"{historial} {texto}".lower()
    pide_recomendacion = any(frase in texto for frase in ("qué me recomiendas", "cual me recomiendas", "cuál me recomiendas", "recomienda"))
    es_azotea = any(palabra in texto for palabra in ("azotea", "techo", "losa"))
    ya_respondio = any(palabra in historial.lower() for palabra in ("filtraciones", "preventivo", "superficie"))
    return pide_recomendacion and es_azotea and not ya_respondio


if prompt := st.chat_input("¿Qué problema tienes en obra o qué producto deseas validar?"):
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    prompt_lower = prompt.lower().strip()
    historial_texto = " ".join(message["content"] for message in st.session_state.messages[-4:]).lower()

    # DETECTOR FLEXIBLE DE SALUDOS: Captura hola, holis, que tal, buen dia, etc.
    if re.search(r"\b(hola|holis|buen[oa]s?|saludos|qu[eé]\s+tal|buenas\s+tardes|buenos\s+dias)\b", prompt_lower):
        guardar_respuesta("¡Hola! Soy tu amigo Asesor FesterParedes, a la orden. ¿En qué te puedo apoyar hoy?")
        st.stop()

    if es_sondeo_inicial_azotea(prompt_lower, historial_texto):
        guardar_respuesta(
            "Con gusto te ayudo a elegir el sistema para tu azotea. Antes de recomendarte un producto, "
            "¿ya cuenta con filtraciones o es un trabajo preventivo? También indícame: ¿qué superficie "
            "tiene (concreto, impermeabilizante anterior)?, ¿tiene humedad o encharcamientos? y ¿qué durabilidad buscas?"
        )
        st.stop()

    contexto_manuales = buscar_fichas(prompt, historial_texto)
    
    # MENSAJE DE CONTENCIÓN AMIGABLE
    mensaje_no_info = "No comprendo del todo tu solicitud o la información exacta no viene en las fichas. Por favor escribe nuevamente de forma detallada o comunícate con un especialista al **3317011786**."

    contexto_sistema = f"""
Eres el Asesor Técnico Senior de Fester México y respondes bajo la perspectiva de un ingeniero experto. Responde siempre en un tono amable, claro, ultra conciso y profesional. Máximo 2 párrafos cortos.

REGLAS CRÍTICAS:
1. Si el cliente pregunta por una CHAROLA DE BAÑO o REGADERA, el producto oficial e inalterable es FESTER CL-52 (Acrílico base agua). Está ESTRICTAMENTE PROHIBIDO recomendar Vaportite 550 o sitemas asfálticos para interiores de baños.
2. Si los datos recuperados abajo vienen vacíos o no contienen la respuesta exacta del producto consultado, debes responder de manera atenta textualmente: {mensaje_no_info}
3. Entrega siempre los rendimientos de forma clara mencionando unidades basándote en el texto inferior. Si te preguntan cantidad de material para una cantidad exacta de metros cuadrados (m²), calcula la cantidad de litros basándote en el rendimiento oficial.

TEXTO OFICIAL DE LA FICHA SELECCIONADA:
{contexto_manuales if contexto_manuales else ''}
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
            # CORRECCIÓN DEFINITIVA DE EXTRACCIÓN CON EL ÍNDICE 0 COMPATIBLE CON EL FORMATO DE LISTAS DE GROQ
            if hasattr(completion, 'choices') and completion.choices:
                response = completion.choices[0].message.content
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
            else:
                st.markdown(mensaje_no_info)
        except Exception as error:
            st.error(f"Error en motor IA: {error}")



