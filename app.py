import os
import re
import streamlit as st
from groq import Groq

st.set_page_config(page_title="Asesor FesterParedes", page_icon="🏗️", layout="centered")
st.title("🏗️ Asesor Técnico FesterParedes IA")
st.write("Sistema maestro desde cero. ¡Tú eres el profesor de esta IA!")

# 1. Conectar con la API de Groq usando el modelo permanente
api_key = os.environ.get("GROQ_API_KEY", st.secrets.get("GROQ_API_KEY", ""))
if not api_key:
    st.error("Falta configurar la clave GROQ_API_KEY en los Secrets de Streamlit.")
    st.stop()

client = Groq(api_key=api_key)
# ID oficial, vigente y permanente en la red de producción de Groq
# Línea 19: Cambiamos al ID oficial activo y permanente del servidor
model="openai/gpt-oss-120b",


# 2. Inicializar memorias de conversación y lecciones de la tienda
if "messages" not in st.session_state:
    st.session_state.messages = []
if "cerebro_tienda" not in st.session_state:
    st.session_state.cerebro_tienda = {}  # Aquí se guardan tus resúmenes en vivo
if "pregunta_pendiente" not in st.session_state:
    st.session_state.pregunta_pendiente = ""
if "mostrar_formulario" not in st.session_state:
    st.session_state.mostrar_formulario = False

# Pintar el historial en la pantalla de forma limpia
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Limpiador de texto para buscar coincidencias exactas en tu memoria
def normalizar_texto(texto):
    return re.sub(r'[^a-z0-9ñ]', '', texto.lower().strip())

# 3. Caja de Aprendizaje en Vivo (Aparece abajo si la IA no sabe la respuesta)
if st.session_state.mostrar_formulario:
    st.warning("🎓 Modo Aprendizaje Activo")
    st.info(f"Enséñame cómo responder a: *\"{st.session_state.pregunta_pendiente}\"*")
    with st.form(key="form_leccion_mostrador"):
        nueva_leccion = st.text_area("Escribe aquí la recomendación o resumen oficial de la tienda:")
        if st.form_submit_button("Guardar en la memoria de la IA"):
            if nueva_leccion.strip():
                clave_busqueda = normalizar_texto(st.session_state.pregunta_pendiente)
                st.session_state.cerebro_tienda[clave_busqueda] = nueva_leccion.strip()
                st.success("¡Lección guardada con éxito! Ya me la aprendí de memoria.")
                st.session_state.mostrar_formulario = False
                st.rerun()

# 4. Procesamiento de la entrada del usuario
if prompt := st.chat_input("¿Qué producto deseas consultar o qué problema tienes en obra?"):
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    prompt_normalizado = normalizar_texto(prompt)

    # REGLA DE ORO: Buscar primero si tú ya le enseñaste esta lección en el mostrador
    respuesta_guardada = ""
    for clave_memoria, valor_memoria in st.session_state.cerebro_tienda.items():
        if clave_memoria in prompt_normalizado or prompt_normalizado in clave_memoria:
            respuesta_guardada = valor_memoria
            break

    if respuesta_guardada:
        with st.chat_message("assistant"):
            st.markdown(respuesta_guardada)
            st.session_state.messages.append({"role": "assistant", "content": respuesta_guardada})
            st.stop()

    # Intercepción flexible de saludos comunes
    if prompt_normalizado in ["hola", "buenosdias", "buenasnoches", "buenastardes", "saludos", "quetal", "holis"]:
        res_saludo = "¡Hola! Soy tu Asesor Técnico FesterParedes, a la orden. ¿En qué problema de obra te puedo ayudar hoy?"
        with st.chat_message("assistant"):
            st.markdown(res_saludo)
            st.session_state.messages.append({"role": "assistant", "content": res_saludo})
            st.stop()

    # Si es una consulta nueva, le pregunta al motor de Groq
    mensaje_auxilio = "No tengo registrada esa información exacta en mi memoria de mostrador. Por favor comunícate con un especialista al **3317011786**."
    
    contexto_sistema = f"""
Eres el Asesor Técnico de la tienda FesterParedes. Tu tono es amable, muy conciso y comercial.
Si el usuario te pregunta por un producto, rendimiento, resistencia o solución que no conozcas o no venga en tu memoria, responde ÚNICAMENTE con esta frase exacta, sin agregar nada más: {mensaje_auxilio}
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
                max_tokens=400
            )
            response = completion.choices[0].message.content
            
            # Si el motor da el mensaje de auxilio, activa el formulario amarillo en pantalla
            if "3317011786" in response or "No tengo registrada" in response:
                st.session_state.pregunta_pendiente = prompt
                st.session_state.mostrar_formulario = True
                st.markdown(mensaje_auxilio)
                st.session_state.messages.append({"role": "assistant", "content": mensaje_auxilio})
                st.rerun()
            else:
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
                
        except Exception as error:
            st.error(f"Error de conexión con el servidor de IA: {error}")
