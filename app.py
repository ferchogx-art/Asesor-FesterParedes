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

# Historial de Chat e hilos de conversación persistentes
if "messages" not in st.session_state:
    st.session_state.messages = []
if "memoria_aprendizaje" not in st.session_state:
    st.session_state.memoria_aprendizaje = {}

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

def guardar_respuesta(respuesta):
    with st.chat_message("assistant"):
        st.markdown(respuesta)
    st.session_state.messages.append({"role": "assistant", "content": respuesta})

# 3. Buscador Inteligente Automatizado con Filtros de Exclusión Tecnológica Estrictos
def buscar_fichas(consulta, historial):
    consulta_limpia = f"{consulta} {historial}".lower()
    
    # Segmentación ultra estricta por zona de la obra
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
        
        # CANDADOS RADICALES: Si el tema es el TECHO, prohíbe cementosos (CR, CL, Nanotech, CX) para que no cometa barbaridades
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
                resultados_tienda.append((puntos + 150, item)) # Subimos el bono a 150 para forzar tu PDF de tienda
            else:
                resultados_fabrica.append((puntos, item))

    contexto_final = ""
    if resultados_tienda:
        resultados_tienda.sort(key=lambda x: x[0], reverse=True)
        for _, res in resultados_tienda[:2]:
            contexto_final += f"\n[MANUAL DE TIENDA OFICIAL: {res['origen']}]\n{res['texto']}\n"
    else:
        if resultados_fabrica:
            resultados_fabrica.sort(key=lambda x: x[0], reverse=True)
            for _, res in resultados_fabrica[:1]:
                contexto_final += f"\n[Ficha de Fábrica de Respaldo: {res['origen']}]\n{res['texto']}\n"
                
    return contexto_final

def es_sondeo_inicial_azotea(texto, historial):
    texto_completo = f"{historial} {texto}".lower()
    pide_rec = any(f in texto_completo for f in ("que me recomiendas", "cual me recomiendas", "recomienda", "que aplico", "que impermeabilizante"))
    es_zona = any(p in texto_completo for p in ("azotea", "techo", "losa"))
    
    # Si en el historial ya platicamos de "filtraciones", "preventivo" o "tengo filtraciones", SIGNIFICA QUE EL SONDEO YA PASÓ
    ya_respondio_sondeo = any(p in historial for p in ["filtraciones", "preventivo", "tengo filtraciones", "ya tengo"])
    
    return pide_rec and es_zona and not ya_respondio_sondeo

# 4. Procesamiento del chat
if prompt := st.chat_input("¿Qué problema tienes en obra o qué producto deseas validar?"):
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    prompt_lower = prompt.lower().strip()
    
    # Agarramos un historial de los últimos 6 mensajes para que la IA no pierda la memoria a corto plazo
    historial_texto = " ".join(m["content"] for m in st.session_state.messages[-6:]).lower()

    if re.search(r"\b(hola|holis|buen[oa]s?|saludos|qu[eé]\s+tal)\b", prompt_lower) and len(prompt_lower) < 10:
        guardar_respuesta("¡Hola! Soy tu amigo Asesor FesterParedes, a la orden. ¿En qué te puedo apoyar hoy?")
        st.stop()

    # Verificar aprendizaje manual
    prompt_limpio_cod = re.sub(r'[^a-z0-9ñ]', '', prompt_lower)
    if prompt_limpio_cod in st.session_state.memoria_aprendizaje:
        guardar_respuesta(st.session_state.memoria_aprendizaje[prompt_limpio_cod])
        st.stop()

    # Disparador del sondeo inicial (Solo si el usuario no ha respondido el estatus de sus goteras)
    if es_sondeo_inicial_azotea(prompt_lower, historial_texto):
        guardar_respuesta(
            "Con gusto te ayudo a elegir el sistema ideal para tu azotea. Antes de sugerirte el producto específico, "
            "compárteme de favor: ¿tu azotea cuenta actualmente con filtraciones o goteras activas, o es un trabajo netamente preventivo?"
        )
        st.stop()

    contexto_manuales = buscar_fichas(prompt, historial_texto)
    mensaje_no_info = "No tengo esa información exacta en las fichas cargadas. Por favor comunícate con un especialista al **3317011786**."

    contexto_sistema = f"""
Eres el Asesor Técnico Senior de Fester México y atiendes bajo el criterio de FesterParedes. Tu tono es sumamente profesional, claro y muy conciso. Máximo 2 párrafos cortos.

REGLAS DE ORO DE INGENIERÍA:
1. SIEMPRE QUE TE HABLEN DE TECHOS, LOSAS O AZOTEAS: Queda estrictamente PROHIBIDO recomendar Fester Nanotech 99, CX-01, o productos cementosos rígidos. Para azoteas con filtraciones activas, la recomendación oficial según tu manual de tienda es el FESTER ACRITON PRO SHIELD MAX (Premium) y se explica su proceso (limpieza, sellador acriton, resanador, malla en puntos críticos y dos capas).
2. Si el usuario te responde en el hilo del sondeo (ej: 'ya tengo filtraciones'), no vuelvas a saludar ni repitas la pregunta del sondeo. Pasa directo a dar la solución del Acriton Pro Shield Max según tu manual de tienda.
3. Si los datos del texto oficial inferior vienen vacíos, di textualmente: {mensaje_no_info}

TEXTO OFICIAL EXTRAÍDO PARA RESPONDER HOY:
{contexto_manuales if contexto_manuales else ''}
"""

    with st.chat_message("assistant"):
        try:
            # Enviamos el historial completo de la plática en vivo para amarrar la memoria de la IA
            mensajes_ia = [{"role": "system", "content": contexto_sistema}]
            for msg in st.session_state.messages[-5:]:
                mensajes_ia.append({"role": msg["role"], "content": msg["content"]})

            completion = client.chat.completions.create(
                model=MODELO_FAVORITO,
                messages=mensajes_ia,
                temperature=0.0,
                max_tokens=450,
            )
            response = completion.choices[0].message.content
            
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


