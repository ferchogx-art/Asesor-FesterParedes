import glob
import os
import re
import streamlit as st
from groq import Groq

st.set_page_config(page_title="Asesor Técnico Fester", page_icon="🏗️", layout="centered")
st.title("🏗️ Asesor Técnico FesterParedes IA")
st.write("Sistema experto con consulta prioritaria a tu manual de mostrador.")

# 1. Conectar con la API de Groq usando tu modelo preferido FIJO
api_key = os.environ.get("GROQ_API_KEY", st.secrets.get("GROQ_API_KEY", ""))
if not api_key:
    st.error("Falta configurar la clave GROQ_API_KEY en los Secrets.")
    st.stop()

client = Groq(api_key=api_key)
MODELO_FAVORITO = "openai/gpt-oss-120b"

# 2. Carga inteligente de PDFs y Manuales de Tienda
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
num_bloques = len(base_conocimiento)
st.success(f"📊 Sistema en línea: {num_bloques} páginas de fichas técnicas cargadas.")

# Historial de Chat
if "messages" not in st.session_state:
    st.session_state.messages = []
if "memoria_aprendizaje" not in st.session_state:
    st.session_state.memoria_aprendizaje = {}
if "mostrar_caja_retro" not in st.session_state:
    st.session_state.mostrar_caja_retro = False
if "pregunta_pendiente" not in st.session_state:
    st.session_state.pregunta_pendiente = ""

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

def guardar_respuesta(respuesta):
    with st.chat_message("assistant"):
        st.markdown(respuesta)
    st.session_state.messages.append({"role": "assistant", "content": respuesta})

# 3. Buscador Inteligente con Filtrado y Filtro de Prioridad Absoluta de Tienda
def buscar_fichas(consulta, historial):
    consulta_limpia = f"{consulta} {historial}".lower()
    
    # Segmentación por zona de la obra
    es_charola = any(x in consulta_limpia for x in ["charola", "baño", "regadera", "cl52", "cl-52"])
    es_salitre = any(x in consulta_limpia for x in ["salitre", "cr65", "cr-65"])
    es_asfalto = any(x in consulta_limpia for x in ["chapopote", "asfalto", "vaportite", "desplante"])
    es_techo = any(x in consulta_limpia for x in ["techo", "losa", "azotea", "acriton", "fester a", "proshield"])
    es_cr66 = any(x in consulta_limpia for x in ["cr66", "cr-66", "cisterna", "alberca"])

    palabras = [p for p in re.findall(r"[\wáéíóúüñ-]+", consulta_limpia) if len(p) > 2]

    # SEPARACIÓN DE BLOQUES: Buscaremos primero si tu manual de respuestas de la tienda tiene la información
    resultados_tienda = []
    resultados_fabrica = []
    
    for item in base_conocimiento:
        texto = item["texto"].lower()
        nombre = item["origen"].lower()
        
        # Filtros de exclusión drásticos para los PDFs de fábrica
        if "tienda" not in nombre and "respuestas" not in nombre:
            if es_charola and "cl" not in nombre:
                continue
            if es_salitre and "cr65" not in nombre:
                continue
            if es_asfalto and "vaportite" not in nombre:
                continue
            if es_techo and ("cl" in nombre or "cr" in nombre or "cf" in nombre):
                continue
            if es_cr66 and "cr66" not in nombre:
                continue

        puntos = sum(5 for palabra in palabras if palabra in texto)
        puntos += sum(35 for palabra in palabras if palabra in nombre)
        
        if puntos > 0:
            if "tienda" in nombre or "respuestas" in nombre:
                resultados_tienda.append((puntos + 100, item)) # Súper bono para tu manual de mostrador
            else:
                resultados_fabrica.append((puntos, item))

    # REGLA DE ORO: Si tu manual de tienda tiene coincidencia, ignora los PDFs de fábrica por completo
    contexto_final = ""
    if resultados_tienda:
        resultados_tienda.sort(key=lambda x: x, reverse=True)
        for _, res in resultados_tienda[:1]:
            contexto_final += f"\n[MANUAL DE TIENDA OFICIAL: {res['origen']}]\n{res['texto']}\n"
    else:
        if resultados_fabrica:
            resultados_fabrica.sort(key=lambda x: x, reverse=True)
            for _, res in resultados_fabrica[:1]:
                contexto_final += f"\n[Ficha de Fábrica de Respaldo: {res['origen']}]\n{res['texto']}\n"
                
    return contexto_final

# 4. Procesamiento del chat
if prompt := st.chat_input("¿Qué problema tienes en obra o qué producto deseas validar?"):
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    prompt_lower = prompt.lower().strip()
    historial_texto = " ".join(m["content"] for m in st.session_state.messages[-4:]).lower()

    if re.search(r"\b(hola|holis|buen[oa]s?|saludos|qu[eé]\s+tal)\b", prompt_lower):
        guardar_respuesta("¡Hola! Soy tu amigo Asesor FesterParedes, a la orden. ¿En qué te puedo apoyar hoy?")
        st.stop()

    # Verificar aprendizaje local en vivo
    prompt_limpio_cod = re.sub(r'[^a-z0-9ñ]', '', prompt_lower)
    if prompt_limpio_cod in st.session_state.memoria_aprendizaje:
        guardar_respuesta(st.session_state.memoria_aprendizaje[prompt_limpio_cod])
        st.stop()

    contexto_manuales = buscar_fichas(prompt, historial_texto)
    mensaje_no_info = "No tengo esa información exacta en las fichas cargadas. Por favor comunícate con un especialista al **3317011786**."

    contexto_sistema = f"""
Eres el Asesor Técnico Senior de Fester México. Tu tono es amable, ultra conciso, práctico y profesional. Máximo 2 párrafos cortos.

REGLAS CRÍTICAS:
1. Usa con absoluta prioridad la información que diga 'MANUAL DE TIENDA OFICIAL'. Si el texto de abajo contiene las respuestas de mostrador redactadas por el dueño de FesterParedes, copia y apega textualmente sus rendimientos, condiciones y pasos.
2. Si te preguntan qué recomiendas para una azotea o techo, ejecuta estrictamente el sistema de sondeo que viene redactado en tu manual: pregunta si es preventivo o si ya hay filtraciones, tipo de superficie, humedad, durabilidad, etc.
3. Si el texto inferior viene vacío o no tiene relación directa con la duda, responde textualmente con el mensaje de asistencia técnica telefónica: {mensaje_no_info}

TEXTO OFICIAL EXTRAÍDO PARA RESPONDER HOY:
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
                max_tokens=500,
            )
            # CORRECCIÓN DE EXTRACCIÓN MAESTRA CON EL ÍNDICE EXTRA PARA TU MODELO
            response = completion.choices.message.content
            
            if mensaje_no_info in response or "3317011786" in response:
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
                
                st.warning("💡 MODO APRENDIZAJE ACTIVO: Agrega la respuesta oficial para enseñarle a la IA:")
                with st.form(key=f"form_retro_{prompt_limpio_cod}"):
                    solucion_tienda = st.text_area("Escribe la recomendación de mostrador aquí:")
                    if st.form_submit_button("Guardar en el cerebro de la IA") and solucion_tienda.strip():
                        st.session_state.memoria_aprendizaje[prompt_limpio_cod] = solucion_tienda.strip()
                        st.success("¡Guardado! He aprendido la lección para la próxima vez.")
            else:
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
        except Exception as error:
            st.error(f"Error en motor IA: {error}")


