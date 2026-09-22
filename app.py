import glob
import os
import re
import streamlit as st
from groq import Groq

st.set_page_config(page_title="Asesor Técnico Fester", page_icon="🏗️", layout="centered")
st.title("🏗️ Asesor Técnico FesterParedes IA")
st.write("Sistema experto con consulta prioritaria a tu manual de mostrador.")

# 1. Conectar con la API de Groq usando el modelo oficial estable
api_key = os.environ.get("GROQ_API_KEY", st.secrets.get("GROQ_API_KEY", ""))
if not api_key:
    st.error("Falta configurar la clave GROQ_API_KEY en los Secrets.")
    st.stop()

client = Groq(api_key=api_key)
MODELO_FAVORITO = "llama3-70b-8192"

# 2. Inicializar memorias en el servidor
if "messages" not in st.session_state:
    st.session_state.messages = []
if "memoria_aprendizaje" not in st.session_state:
    st.session_state.memoria_aprendizaje = {}

# Carga inteligente de PDFs
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
                        texto_completo.append({
                            "origen": nombre_archivo,
                            "texto": texto_pag,
                        })
        except Exception as error:
            print(f"Error leyendo {nombre_archivo}: {error}")
    return texto_completo

base_conocimiento = extraer_conocimiento_fester()

# Pintar historial en pantalla
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

def guardar_respuesta(respuesta):
    with st.chat_message("assistant"):
        st.markdown(respuesta)
    st.session_state.messages.append({"role": "assistant", "content": respuesta})

# 3. Buscador Inteligente con Filtros de Exclusión Tecnológica Estrictos
def buscar_fichas(consulta, historial):
    consulta_limpia = f"{consulta} {historial}".lower()
    
    es_charola = any(x in consulta_limpia for x in ["charola", "baño", "regadera", "cl52", "cl-52"])
    es_salitre = any(x in consulta_limpia for x in ["salitre", "cr65", "cr-65"])
    es_asfalto = any(x in consulta_limpia for x in ["chapopote", "asfalto", "vaportite", "desplante", "cimentacion"])
    es_techo = any(x in consulta_limpia for x in ["techo", "losa", "azotea", "lluvia", "acriton", "fester a", "proshield", "gotera", "filtracion", "filtraciones"])
    es_cr66 = any(x in consulta_limpia for x in ["cr66", "cr-66", "cisterna", "alberca", "terraza"])

    palabras = [p for p in re.findall(r"[\wáéíóúüñ-]+", consulta_limpia) if len(p) > 2]

    resultados_tienda = []
    resultados_fabrica = []
    
    for item in base_conocimiento:
        texto = item["texto"].lower()
        nombre = item["origen"].lower()
        
        # Candados radicales de exclusión técnica en azoteas
        if es_techo and ("cl" in nombre or "cr" in nombre or "cf" in nombre or "nanotech" in nombre or "cx" in nombre):
            continue
        if es_charola and "cl" not in nombre and "tienda" not in nombre:
            continue
        if es_salitre and "cr65" not in nombre and "tienda" not in nombre:
            continue
        if es_asfalto and "vaportite" not in nombre and "tienda" not in nombre:
            continue
        if es_cr66 and "cr66" not in nombre and "tienda" not in nombre:
            continue

        puntos = sum(5 for palabra in palabras if palabra in texto)
        puntos += sum(35 for palabra in palabras if palabra in nombre)
        
        if puntos > 0:
            if "tienda" in nombre or "respuestas" in nombre:
                resultados_tienda.append((puntos + 150, item))
            else:
                resultados_fabrica.append((puntos, item))

    contexto_final = ""
    if resultados_tienda:
        resultados_tienda.sort(key=lambda x: x, reverse=True)
        for _, res in resultados_tienda[:2]:
            contexto_final += f"\n[MANUAL DE TIENDA OFICIAL: {res['origen']}]\n{res['texto']}\n"
    else:
        if resultados_fabrica:
            resultados_fabrica.sort(key=lambda x: x, reverse=True)
            for _, res in resultados_fabrica[:1]:
                contexto_final += f"\n[Ficha de Fábrica de Respaldo: {res['origen']}]\n{res['texto']}\n"
                
    return contexto_final

def es_sondeo_inicial_azotea(texto, historial):
    texto_completo = f"{historial} {texto}".lower()
    pide_rec = any(f in texto_completo for f in ("que me recomiendas", "cual me recomiendas", "recomienda", "que aplico", "que impermeabilizante"))
    es_zona = any(p in texto_completo for p in ("azotea", "techo", "losa"))
    ya_respondio_sondeo = any(p in historial for p in ["filtraciones", "preventivo", "tengo filtraciones", "ya tengo", "tiene goteras", "goteras activas"])
    return pide_rec and es_zona and not ya_respondio_sondeo

# 4. Procesamiento del chat
if prompt := st.chat_input("¿Qué problema tienes en obra o qué producto deseas validar?"):
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    prompt_lower = prompt.lower().strip()
    historial_texto = " ".join(m["content"] for m in st.session_state.messages[-6:]).lower()

    if re.search(r"\b(hola|holis|buen[oa]s?|saludos|qu[eé]\s+tal)\b", prompt_lower) and len(prompt_lower) < 10:
        guardar_respuesta("¡Hola! Soy tu amigo Asesor FesterParedes, a la orden. ¿En qué te puedo apoyar hoy?")
        st.stop()

    # Verificar aprendizaje manual
    prompt_limpio_cod = re.sub(r'[^a-z0-9ñ]', '', prompt_lower)
    if prompt_limpio_cod in st.session_state.memoria_aprendizaje:
        guardar_respuesta(st.session_state.memoria_aprendizaje[prompt_limpio_cod])
        st.stop()

    if es_sondeo_inicial_azotea(prompt_lower, historial_texto):
        guardar_respuesta(
            "Con gusto te ayudo a elegir el sistema ideal para tu azotea. Antes de sugerirte el producto específico, "
            "compárteme de favor: ¿tu azotea cuenta actualmente con filtraciones o goteras activas, o es un trabajo netamente preventivo?"
        )
        st.stop()

    contexto_manuales = buscar_fichas(prompt, historial_texto)
    mensaje_no_info = "No tengo esa información exacta en las fichas cargadas. Por favor comunícate con un especialista al **3317011786**."

    contexto_sistema = f"""
Eres el Asesor Técnico Senior de Fester México y respondes con base en tu manual. Tu tono es profesional, claro y ultra conciso. Máximo 2 párrafos cortos.

REGLAS DE ORO DE INGENIERÍA:
1. SIEMPRE QUE TE HABLEN DE TECHOS, LOSAS O AZOTEAS: Fester Acriton es un impermeabilizante 100% elastomérico ACRÍLICO base agua con polímeros avanzados. Está prohibido decir que contiene poliuretano o solventes.
2. Si te preguntan por problemas de HUMEDAD O SALITRE EN EL MURO, la recomendación oficial según tu manual de tienda es el FESTER CR-65 y se explica brevemente su proceso (retirar enjarre, limpiar superficie, resanar con CM-200, dos manos cruzadas y curado obligatorio con agua).
3. Si los datos del texto oficial inferior vienen vacíos o no corresponden, responde exactamente con la frase de asistencia técnica telefónica: {mensaje_no_info}

TEXTO OFICIAL EXTRAÍDO PARA RESPONDER HOY:
{contexto_manuales if contexto_manuales else ''}
"""

    with st.chat_message("assistant"):
        try:
            mensajes_ia = [
                {"role": "system", "content": contexto_sistema},
                {"role": "user", "content": prompt}
            ]

            completion = client.chat.completions.create(
                model=MODELO_FAVORITO,
                messages=mensajes_ia,
                temperature=0.0,
                max_tokens=450,
            )
            
            response = completion.choices.message.content
            st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})
            
        except Exception as error:
            st.error(f"Error en motor IA: {error}")

