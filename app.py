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
    return "".join(
        f"\n[Ficha oficial: {item['origen']} - {item['referencia']}]\n{item['texto']}\n"
        for _, item in resultados[:8]
    )


def es_sondeo_inicial_azotea(texto, historial):
    texto = f"{historial} {texto}".lower()
    pide_recomendacion = any(
        frase in texto
        for frase in ("qué me recomiendas", "cual me recomiendas", "cuál me recomiendas", "recomienda", "que imper")
    )
    es_azotea = any(palabra in texto for palabra in ("azotea", "techo", "losa", "impermeabilizar mi azote"))
    ya_respondio = any(
        palabra in historial.lower()
        for palabra in ("¿ya cuenta con filtraciones", "¿es preventivo", "¿tiene filtraciones")
    )
    return pide_recomendacion and es_azotea and not ya_respondio


if prompt := st.chat_input("¿Qué problema tienes en obra o qué producto deseas validar?"):
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    prompt_lower = prompt.lower().strip()
    historial_texto = " ".join(
        message["content"] for message in st.session_state.messages[-6:]
    ).lower()

    if re.search(r"\b(hola|buen[oa]s?|saludos|qué tal)\b", prompt_lower):
        guardar_respuesta(
            "¡Hola! Soy tu amigo Asesor FesterParedes, a la orden. ¿En qué te puedo apoyar?"
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
        "Lo siento, esa información te la puede dar un compañero. "
        "Comunícate al **3317011786**."
    )

    contexto_sistema = f"""
Eres el Asesor Técnico Senior de Fester México y atiendes en español. Tu tono es amable,
claro, práctico y profesional. Responde en máximo 2 párrafos cortos, salvo que una secuencia
de aplicación requiera una lista breve.

REGLAS CRÍTICAS:
1. Usa exclusivamente las fichas oficiales incluidas al final para beneficios, características,
   rendimientos, consumos, diluciones, tiempos, preparación y aplicación. Si un dato no aparece
en las fichas recuperadas, no lo inventes y responde exactamente: {mensaje_no_info}
2. Cada rendimiento debe mencionar producto, unidad y que está basado en la ficha técnica. Nunca
   mezcles el rendimiento de un producto con el de otro.
3. Cuando el cliente pregunte por una azotea, primero sondea si es preventivo o si ya hay filtraciones,
   tipo de superficie, humedad o impermeabilizante anterior, solución acrílica o asfáltica y durabilidad.
   Después recomienda solamente con la ficha técnica.
4. Si ya existen filtraciones, considera Acriton Pro Shield Max (durabilidades de 4, 6 u 8 años
   únicamente si así aparece en la ficha), la línea Profesional (3, 5 o 7 años) y 5 Fibratado.
   Menciona sus beneficios solo cuando estén escritos en la ficha técnica recuperada.
5. Para azoteas, explica la preparación y el sistema únicamente con respaldo documental: superficie
   limpia, barrida y sin polvo; sellador Acriton y su rendimiento; resanador Acriton para juntas
   menores a 4 mm; Superseal P para juntas mayores; FT201 para juntas de alto movimiento; Revoflex
   o Acriflex en domos, bajantes, zavaletas y chaflanes; primera capa contra el sentido del agua,
   segunda en el sentido del flujo y el tiempo entre capas solo si la ficha lo confirma.
6. Si hay cavidades o estancamientos, evalúa CM200 o un entortado reforzado con Festerbond. Describe
   características, beneficios y rendimiento solo desde sus fichas.
7. "Chapopote" o "impermeabilizante asfáltico" normalmente se refiere a Vaportite, pero acláralo
   antes de asumir. Para desplantes, menciona Vaportite, primario e Hidroprimer solo con sus
   características, beneficios y rendimiento documentados.
8. Para CL52 y CR65, identifica el uso correcto con las fichas. Para CR66, indica que es cementoso
   de dos componentes solo si la ficha recuperada lo confirma; si la terraza supera 25 m², pregunta
   o indica las juntas de dilatación únicamente si ese criterio está respaldado por la ficha.
9. Aplica el mismo criterio a Festerbond, Festegral y cualquier otro producto: no inventes beneficios,
   compatibilidades, rendimientos ni procedimientos.
10. No des ningún teléfono distinto de 3317011786.

HISTORIAL RECIENTE:
{historial_texto}

TEXTO OFICIAL RECUPERADO:
{contexto_manuales if contexto_manuales else "Vacio"}
"""

    try:
        mensajes_ia = [{"role": "system", "content": contexto_sistema}]
        mensajes_ia.extend(st.session_state.messages[-6:])
        completion = client.chat.completions.create(
            model=MODELO_FAVORITO,
            messages=mensajes_ia,
            temperature=0.0,
            max_tokens=2000,
        )
        respuesta = completion.choices[0].message.content
        guardar_respuesta(respuesta)
    except Exception as error:
        with st.chat_message("assistant"):
            st.error(f"Error en motor IA: {error}")
