import streamlit as st
import os
import glob
import fitz  # PyMuPDF para leer los PDFs de Fester
from groq import Groq

st.set_page_config(page_title="Asesor Técnico Fester", page_icon="🏗️", layout="centered")
st.title("🏗️ Asesor Técnico IA - Productos Fester")
st.write("Consulta la correcta aplicación, rendimientos y restricciones basados en los manuales oficiales.")

# 1. Conectar con la API de Groq
api_key = os.environ.get("GROQ_API_KEY", st.secrets.get("GROQ_API_KEY", ""))
if not api_key:
    st.error("Falta configurar la clave GROQ_API_KEY en los Secrets.")
    st.stop()

client = Groq(api_key=api_key)

# 2. Función optimizada para buscar texto en los PDFs cargados sin saturar el servidor gratuito
@st.cache_resource
def extraer_conocimiento_fester():
    texto_completo = []
    # Busca todos los PDFs dentro de la carpeta fichas_fester
    archivos_pdf = glob.glob("fichas_fester/*.pdf")
    
    for ruta_pdf in archivos_pdf:
        nombre_archivo = os.path.basename(ruta_pdf)
        try:
            doc = fitz.open(ruta_pdf)
            for num_pagina, pagina in enumerate(doc):
                texto = pagina.get_text()
                if texto.strip():
                    # Guardamos el texto junto con el origen para que la IA sepa de qué manual viene
                    texto_completo.append({
                        "origen": nombre_archivo,
                        "pagina": num_pagina + 1,
                        "texto": texto
                    })
        except Exception as e:
            print(f"Error leyendo {nombre_archivo}: {e}")
    return texto_completo

# Cargar los manuales en memoria del servidor
with st.spinner("Analizando manuales y catálogos de Fester... Esto solo toma unos segundos la primera vez."):
    base_conocimiento = extraer_conocimiento_fester()

# 3. Buscador simple por palabras clave en los documentos
def buscar_contexto(pregunta, base, k=3):
    palabras = pregunta.lower().split()
    puntuaciones = []
    
    for item in base:
        puntos = sum(1 for palabra in palabras if palabra in item["texto"].lower())
        if puntos > 0:
            puntuaciones.append((puntos, item))
            
    # Ordenar por relevancia y extraer los fragmentos más importantes
    puntuaciones.sort(key=lambda x: x[0], reverse=True)
    resultados = [item for puntos, item in puntuaciones[:k]]
    
    contexto_formateado = ""
    for res in resultados:
        contexto_formateado += f"\n--- Fragmento de {res['origen']} (Pág. {res['pagina']}) ---\n{res['texto']}\n"
    return contexto_formateado

# 4. Historial de chat
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 5. Entrada del usuario y respuesta de la IA
if prompt := st.chat_input("¿Qué producto Fester deseas consultar o qué problema tienes en obra?"):
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Buscar información relevante en los PDFs que subiste
    contexto_manuales = buscar_contexto(prompt, base_conocimiento)

    contexto_sistema = (
        "Eres un ingeniero asesor experto en el catálogo de productos Fester México. "
        "Tu objetivo es guiar a ingenieros y arquitectos en la correcta aplicación en obra, "
        "rendimientos, preparación de superficies y restricciones de clima utilizando la información "
        "de los manuales oficiales proporcionados.\n\n"
        "INFORMACIÓN OFICIAL EXTRAÍDA DE LOS MANUALES FESTER:\n"
        f"{contexto_manuales if contexto_manuales else 'No se encontraron fragmentos exactos en los PDFs para esta consulta, responde con tu conocimiento general de productos Fester pero advierte al usuario.'}\n\n"
        "Instrucciones de respuesta:\n"
        "- Responde de forma técnica, profesional y muy estructurada.\n"
        "- Si la información proviene de los manuales, menciona brevemente el nombre del archivo fuente para darle confianza al ingeniero."
    )

    with st.chat_message("assistant"):
        try:
            completion = client.chat.completions.create(
              model="openai/gpt-oss-120b",



                messages=[
                    {"role": "system", "content": contexto_sistema},
                    *st.session_state.messages
                ],
                temperature=0.2,
            )
            response = completion.choices.message.content
            st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})
        except Exception as e:
            st.error(f"Hubo un error al conectar con la IA: {e}")
