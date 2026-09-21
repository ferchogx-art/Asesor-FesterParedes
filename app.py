import streamlit as st
import os
import glob
from groq import Groq

st.set_page_config(page_title="Asesor FesterParedes", page_icon="🏗️", layout="centered")
st.title("🏗️ Asesor Técnico FesterParedes IA - Productos Fester")

# 1. Conectar con la API de Groq
api_key = os.environ.get("GROQ_API_KEY", st.secrets.get("GROQ_API_KEY", ""))
if not api_key:
    st.error("Falta configurar la clave GROQ_API_KEY en los Secrets.")
    st.stop()

client = Groq(api_key=api_key)

# 2. Carga y diagnóstico de archivos PDF y TXT sueltos
@st.cache_resource
def extraer_conocimiento_fester():
    texto_completo = []
    # Busca archivos .pdf o .txt sueltos en la raíz de tu GitHub
    archivos_validos = glob.glob("*.pdf") + glob.glob("*.txt")
    
    for ruta in archivos_validos:
        nombre_archivo = os.path.basename(ruta)
        try:
            if ruta.endswith(".pdf"):
                import fitz  # PyMuPDF
                doc = fitz.open(ruta)
                # Extraemos el texto de cada página para tener una mejor referencia
                for num_pag, pagina in enumerate(doc):
                    texto_pag = pagina.get_text()
                    if texto_pag.strip():
                        # Cortamos en fragmentos pequeños para la memoria del chat
                        fragmentos = [texto_pag[i:i+800] for i in range(0, len(texto_pag), 800)]
                        for idx, frag in enumerate(fragmentos):
                            texto_completo.append({
                                "origen": nombre_archivo,
                                "referencia": f"Pág. {num_pag + 1}",
                                "texto": frag
                            })
            elif ruta.endswith(".txt"):
                with open(ruta, "r", encoding="utf-8", errors="ignore") as f:
                    texto = f.read()
                    if texto.strip():
                        fragmentos = [texto[i:i+800] for i in range(0, len(texto), 800)]
                        for idx, frag in enumerate(fragmentos):
                            texto_completo.append({
                                "origen": nombre_archivo,
                                "referencia": f"Bloque {idx + 1}",
                                "texto": frag
                            })
        except Exception as e:
            print(f"Error leyendo {nombre_archivo}: {e}")
    return texto_completo

with st.spinner("Analizando manuales y catálogos Fester... Esto solo toma unos segundos la primera vez."):
    base_conocimiento = extraer_conocimiento_fester()

# Panel visual de diagnóstico
num_bloques = len(base_conocimiento)
if num_bloques == 0:
    st.error("⚠️ ALERTA: La IA no pudo extraer texto de tus archivos. Verifica que no estén protegidos contra lectura.")
else:
    st.success(f"📚 Base de datos activa: Cargados exitosamente {num_bloques} bloques de conocimiento desde tus PDFs.")

# 3. Buscador simple por coincidencia de palabras clave
def buscar_contexto(pregunta, base, k=2):
    palabras = [p.lower() for p in pregunta.split() if len(p) > 3]
    if not palabras:
        return ""
    puntuaciones = []
    for item in base:
        puntos = sum(2 if palabra in item["texto"].lower() else 0 for palabra in palabras)
        if puntos > 0:
            puntuaciones.append((puntos, item))
    puntuaciones.sort(key=lambda x: x[0], reverse=True)
    
    contexto_formateado = ""
    for puntos, res in puntuaciones[:k]:
        contexto_formateado += f"\n[Fuente: {res['origen']} - {res['referencia']}]\n{res['texto']}\n"
    return contexto_formateado

# 4. Historial de chat en pantalla
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 5. Entrada del usuario y respuesta ejecutiva de la IA
if prompt := st.chat_input("¿Qué rendimiento o producto deseas validar? o que situacion de humedad tienes?"):
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Buscar en los PDFs reales que subiste
    contexto_manuales = buscar_contexto(prompt, base_conocimiento)

    contexto_sistema = (
        "Eres el Asesor Técnico oficial de FesterParedes. Tu cliente es un ingeniero, arquitecto en obra o cualquier persona que tenga dudas con productos fester.\n"
        "Reglas estrictas de comportamiento:\n"
        "1. Responde de forma muy breve, directa y al grano (máximo 2 párrafos cortos o viñetas).\n"
        "2. Usa ÚNICAMENTE los datos oficiales provistos abajo. Si el dato exacto no viene ahí, di textualmente: 'No encontré ese dato específico en los manuales cargados, favor de comunicarse al 3317011786'.\n"
        "3. Está estrictamente PROHIBIDO inventar nombres de productos, marcas o rendimientos que no existan en el texto provisto.\n"
        "4. Si encuentras la información, menciona brevemente de qué archivo y página proviene para darle certeza al ingeniero.\n\n"
        f"TEXTO OFICIAL EXTRAÍDO DE TUS MANUALES:\n{contexto_manuales if contexto_manuales else 'No hay información en los documentos para esta consulta.'}"
    )

    with st.chat_message("assistant"):
        try:
            # Usamos el modelo ultra rápido, gratuito y 100% vigente de Groq
            completion = client.chat.completions.create(
                model="llama3-8b-8192",
                messages=[
                    {"role": "system", "content": contexto_sistema},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.0,  # Cero creatividad para evitar que invente marcas falsas
                max_tokens=300,
            )
            response = completion.choices[0].message.content
            st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})
        except Exception as e:
            st.error(f"Hubo un error con el motor de IA: {e}")

