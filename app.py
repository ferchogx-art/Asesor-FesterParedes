import streamlit as st
import os
import glob
import fitz  # PyMuPDF
from groq import Groq

st.set_page_config(page_title="Asesor Técnico FesterParedes", page_icon="🏗️", layout="centered")
st.title("🏗️ Asesor FesterParedes IA - Productos Fester")
st.write("Consultas técnicas rápidas y precisas para obra basadas en manuales oficiales.")

# 1. Conectar con la API de Groq
api_key = os.environ.get("GROQ_API_KEY", st.secrets.get("GROQ_API_KEY", ""))
if not api_key:
    st.error("Falta configurar la clave GROQ_API_KEY en los Secrets.")
    st.stop()

client = Groq(api_key=api_key)

# 2. Carga optimizada de texto de los manuales
@st.cache_resource
def extraer_conocimiento_fester():
    texto_completo = []
    archivos_txt = glob.glob("*.txt")
    
    for ruta_txt in archivos_txt:
        nombre_archivo = os.path.basename(ruta_txt)
        try:
            with open(ruta_txt, "r", encoding="utf-8") as f:
                texto = f.read()
                if texto.strip():
                    # Cortamos el texto en bloques pequeños para no saturar la memoria
                    fragmentos = [texto[i:i+800] for i in range(0, len(texto), 800)]
                    for idx, frag in enumerate(fragmentos):
                        texto_completo.append({
                            "origen": nombre_archivo,
                            "bloque": idx + 1,
                            "texto": frag
                        })
        except Exception as e:
            print(f"Error leyendo {nombre_archivo}: {e}")
    return texto_completo

with st.spinner("Cargando base técnica Fester..."):
    base_conocimiento = extraer_conocimiento_fester()

# 3. Buscador ajustado para traer solo lo indispensable (k=2 en lugar de 3)
def buscar_contexto(pregunta, base, k=2):
    palabras = pregunta.lower().split()
    puntuaciones = []
    for item in base:
        puntos = sum(1 for palabra in palabras if palabra in item["texto"].lower())
        if puntos > 0:
            puntuaciones.append((puntos, item))
    puntuaciones.sort(key=lambda x: x[0], reverse=True)
    resultados = [item for puntos, item in puntuaciones[:k]]
    
    contexto_formateado = ""
    for res in resultados:
        contexto_formateado += f"[Fuente: {res['origen']}]\n{res['texto']}\n"
    return contexto_formateado

# 4. Mantener un historial corto para que no se sature el servidor (Máximo 4 mensajes)
if "messages" not in st.session_state:
    st.session_state.messages = []
if len(st.session_state.messages) > 4:
    st.session_state.messages = st.session_state.messages[-4:]

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 5. Respuesta directa, ejecutiva y ultra rápida de la IA
if prompt := st.chat_input("¿Qué rendimiento o producto deseas validar?"):
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    contexto_manuales = buscar_contexto(prompt, base_conocimiento)

    # REGLAS ESTRICTAS PARA QUE LA IA SEA BREVE
    contexto_sistema = (
        "Eres el Asesor Técnico de FesterParedes. Tu cliente es un ingeniero, arquitecto o constructor en obra que necesita respuestas RÁPIDAS, EXTREMADAMENTE BREVES y AL GRANO.\n"
        "Reglas obligatorias de respuesta:\n"
        "1. Responde en máximo 2 o 3 párrafos cortos o viñetas muy directas.\n"
        "2. NUNCA generes tablas largas, cronogramas ni cotizaciones a menos que te lo pidan explícitamente.\n"
        "3. Ve directo al grano: si te preguntan un rendimiento, dilo en la primera línea.\n"
        "4. Usa un tono técnico pero ejecutivo.\n\n"
        f"DATOS OFICIALES DEL MANUAL:\n{contexto_manuales}"
    )

    with st.chat_message("assistant"):
        try:
            # Usamos el mismo modelo estable que ya te conectó, pero con respuestas cortas (max_tokens=400)
            completion = client.chat.completions.create(
                model="openai/gpt-oss-120b",
                messages=[
                    {"role": "system", "content": contexto_sistema},
                    *st.session_state.messages
                ],
                temperature=0.2,
                max_tokens=400, 
            )
            response = completion.choices[0].message.content
            st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})
        except Exception as e:
            st.error(f"Hubo un error: {e}")
