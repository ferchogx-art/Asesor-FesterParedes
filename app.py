import os
import re
import streamlit as st
from groq import Groq

st.set_page_config(page_title="Asesor FesterParedes", page_icon="🏗️", layout="centered")
st.title("🏗️ Asesor Técnico FesterParedes IA")
st.write("Sistema experto desde cero. ¡Tú eres el profesor de esta IA!")

# 1. Conectar con la API de Groq usando el modelo vigente definitivo
api_key = os.environ.get("GROQ_API_KEY", st.secrets.get("GROQ_API_KEY", ""))
if not api_key:
    st.error("Falta configurar la clave GROQ_API_KEY en los Secrets de Streamlit.")
    st.stop()

client = Groq(api_key=api_key)
# Modelo insignia actual, activo y permanente en los servidores
# Línea 18: Cambiamos al modelo base oficial y permanente de producción
MODELO_FAVORITO = "llama-3.1-8b-instant"


# 2. Inicializar memorias de conversación y aprendizaje
if "messages" not in st.session_state:
    st.session_state.messages = []
if "cerebro_tienda" not in st.session_state:
    st.session_state.cerebro_tienda = {}  # Aquí se guardan tus lecciones en vivo
if "pregunta_sin_responder" not in st.session_state:
    st.session_state.pregunta_sin_responder = ""
if "mostrar_formulario" not in st.session_state:
    st.session_state.mostrar_formulario = False

# Pintar el historial en la pantalla
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Limpiador de texto para buscar en la memoria
def limpiar_texto(texto):
    return re.sub(r'[^a-z0-9ñ]', '', texto.lower().strip())

# 3. Formulario de Aprendizaje Activo (Aparece si la IA no sabe la respuesta)
if st.session_state.mostrar_formulario:
    st.warning(f"🎓 Modo Aprendizaje Activo")
    st.info(f"Enséñame cómo responder a: *\"{st.session_state.pregunta_sin_responder}\"*")
    with st.form(key="form_leccion_mostrador"):
        leccion = st.text_area("Escribe aquí la recomendación oficial de la tienda:")
        if st.form_submit_button("Guardar en la memoria de la IA"):
            if leccion.strip():
                clave = limpiar_texto(st.session_state.pregunta_sin_responder)
                st.session_state.cerebro_tienda[clave] = leccion.strip()
                st.success("¡Lección guardada con éxito! Ya me la aprendí de memoria.")
                st.session_state.mostrar_formulario = False
                st.rerun()

# 4. Procesamiento de la entrada del usuario
if prompt := st.chat_input("¿Qué producto deseas consultar o qué problema tienes en obra?"):
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    prompt_limpio = limpiar_texto(prompt)

    # Buscar primero si tú ya le enseñaste esta respuesta en el mostrador
    respuesta_maestra = ""
    for clave_guardada, valor_guardado in st.session_state.cerebro_tienda.items():
        if clave_guardada in prompt_limpio or prompt_limpio in clave_guardada:
            respuesta_maestra = valor_guardado
            break

    if respuesta_maestra:
        with st.chat_message("assistant"):
            st.markdown(respuesta_maestra)
            st.session_state.messages.append({"role": "assistant", "content": respuesta_maestra})
            st.stop()

    # Intercepción flexible de saludos comunes
    if prompt_limpio in ["hola", "buenosdias", "buenasnoches", "buenastardes", "saludos", "quetal"]:
        res_saludo = "¡Hola! Soy tu Asesor Técnico FesterParedes, a la orden. ¿En qué problema de obra te puedo ayudar hoy?"
        with st.chat_message("assistant"):
            st.markdown(res_saludo)
            st.session_state.messages.append({"role": "assistant", "content": res_saludo})
            st.stop()

    # Si no está en tu memoria, le pregunta al nuevo motor de Groq
    mensaje_auxilio = "No tengo registrada esa información exacta en mi memoria de mostrador. Por favor comunícate con un especialista al **3317011786**."
    
    contexto_sistema = f"""
Eres el Asesor Técnico de la tienda FesterParedes. Tu tono es amable, muy conciso y comercial.
Si el usuario te pregunta por un producto o solución que no conozcas o de la cual no tengas datos seguros, responde ÚNICAMENTE con esta frase exacta: {mensaje_auxilio}
"""

    with st.chat_message("assistant"):
        try:
            completion = client.chat.completions.create(
                model=MODELO_VIGENTE,
                messages=[
                    {"role": "system", "content": contexto_sistema},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.0,
                max_tokens=400
            )
            response = completion.choices[0].message.content
            
            # Si el motor da el mensaje de auxilio, activa el Modo Aprendizaje en pantalla
            if "3317011786" in response or "No tengo registrada" in response:
                st.session_state.pregunta_sin_responder = prompt
                st.session_state.mostrar_formulario = True
                st.markdown(mensaje_auxilio)
                st.session_state.messages.append({"role": "assistant", "content": mensaje_auxilio})
                st.rerun()
            else:
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
                
        except Exception as error:
            st.error(f"Error de conexión con el servidor de IA: {error}")


