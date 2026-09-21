import streamlit as st
import os
import glob
import re
from groq import Groq

st.set_page_config(page_title="Asesor Técnico Fester", page_icon="🏗️", layout="centered")
st.title("🏗️ Asesor Técnico FesterParedes IA")

# 1. Conectar con la API de Groq
api_key = os.environ.get("GROQ_API_KEY", st.secrets.get("GROQ_API_KEY", ""))
if not api_key:
    st.error("Falta configurar la clave GROQ_API_KEY en los Secrets.")
    st.stop()

client = Groq(api_key=api_key)

# 2. Carga optimizada y limpieza profunda de textos en PDFs
@st.cache_resource
def extraer_conocimiento_fester():
    texto_completo = []
    archivos_validos = glob.glob("*.pdf") + glob.glob("*.txt")
    
    for ruta in archivos_validos:
        nombre_archivo = os.path.basename(ruta)
        try:
            if ruta.endswith(".pdf"):
                import fitz  # PyMuPDF
                doc = fitz.open(ruta)
                for num_pag, pagina in enumerate(doc):
                    texto_pag = pagina.get_text()
                    if texto_pag.strip():
                        # Limpiamos caracteres especiales del PDF para facilitar la búsqueda futura
                        texto_limpio = texto_pag.replace("®", "").replace("™", "").replace("©", "")
                        fragmentos = [texto_limpio[i:i+1200] for i in range(0, len(texto_limpio), 1200)]
                        for idx, frag in enumerate(fragmentos):
                            texto_completo.append({
                                "origen": nombre_archivo,
                                "referencia": f"Pág. {num_pag + 1}",
                                "texto": frag
                            })
        except Exception as e:
            print(f"Error leyendo {nombre_archivo}: {e}")
    return texto_completo

with st.spinner("Sincronizando manuales y catálogos Fester..."):
    base_conocimiento = extraer_conocimiento_fester()

# Panel visual de diagnóstico
num_bloques = len(base_conocimiento)
if num_bloques == 0:
    st.error("⚠️ ALERTA: La IA no pudo extraer texto de tus archivos.")
else:
    st.success(f"📚 Base de datos activa: {num_bloques} bloques de conocimiento vinculados.")

# 3. Buscador Flexible e Inteligente (Resistente a símbolos y términos cortos)
def buscar_contexto(pregunta, base, k=4):
    # Limpiamos la pregunta del usuario quitando acentos y caracteres especiales
    pregunta_limpia = pregunta.lower().replace("®", "").replace("™", "")
    # Separamos en palabras ignorando conectores comunes vacíos, pero PERMITIENDO la letra "a"
    palabras = [p for p in re.findall(r'\b\w+\b', pregunta_limpia) if p not in ['con', 'para', 'del', 'los', 'las', 'que', 'una']]
    
    if not palabras:
        return ""
    
    puntuaciones = []
    for item in base:
        texto_inferior = item["texto"].lower()
        puntos = 0
        for palabra in palabras:
            # Si la palabra exacta aparece en el fragmento, sumamos puntos
            if palabra in texto_inferior:
                puntos += 5
            # Coincidencia parcial por si las palabras vienen pegadas en el PDF
            if len(palabra) > 2 and palabra[:4] in texto_inferior:
                puntos += 2
                
        if puntos > 0:
            puntuaciones.append((puntos, item))
            
    puntuaciones.sort(key=lambda x: x[0], reverse=True)
    
    contexto_formateado = ""
    # Tomamos los fragmentos con mayor puntaje de coincidencia
    for puntos, res in puntuaciones[:k]:
        contexto_formateado += f"\n[Fuente: {res['origen']} - {res['referencia']}]\n{res['texto']}\n"
    return contexto_formateado

# 4. Historial de conversación
if "messages" not in st.session_state:
    st.session_state.messages = []

if len(st.session_state.messages) > 6:
    st.session_state.messages = st.session_state.messages[-6:]

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 5. Entrada del chat
if prompt := st.chat_input("¿Qué situacion de humedad tienes el dia de hoy? (preguntame)"):
    with st.chat_message("user"):
        st.markdown(prompt)
    
    contexto_manuales = buscar_contexto(prompt, base_conocimiento)

    contexto_system = (
        "Eres el Asesor oficial de Fester Paredes. Tu cliente es un ingeniero o arquitecto en obra, o cualquier persona que pregunte sobre asesoria y productos fester.\n"
        "REGLA DE CONTEXTO CLAVE:\n"
        "- Si el usuario menciona 'Proshield' o 'Acriton 4 años', se refiere al producto oficial 'Fester Acriton Proshield 4 años' documentado ampliamente en las páginas 15, 16 y 17 del manual.\n"
        "- Si el usuario menciona 'Fester A', 'A3' o 'A5', se refiere a la línea de impermeabilizantes acrílicos económicos descritos en la página 43 del manual.\n\n"
        "Reglas estrictas de comportamiento:\n"
        "1. Responde de forma técnica, clara, directa y completa. Nunca dejes frases a medias.\n"
        "2. Usa estrictamente la información de los manuales provistos abajo.\n"
        "3. Al final de tu respuesta, menciona brevemente de qué archivo y página provienen los datos.\n\n"
        f"TEXTO OFICIAL EXTRAÍDO DE TUS MANUALES:\n{contexto_manuales}"
    )

    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("assistant"):
        try:
            historial_completo = [{"role": "system", "content": contexto_system}]
            for msg in st.session_state.messages:
                historial_completo.append({"role": msg["role"], "content": msg["content"]})

            completion = client.chat.completions.create(
                model="openai/gpt-oss-120b",
                messages=historial_completo,
                temperature=0.1,
                max_tokens=650,
            )
            response = completion.choices[0].message.content
            st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})
        except Exception as e:
            st.error(f"Hubo un error con el motor de IA: {e}")
