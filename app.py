import streamlit as st
import os
import glob
from groq import Groq

st.set_page_config(page_title="Asesor Técnico Fester Paredes", page_icon="🏗️", layout="centered")
st.title("🏗️ Asesor Fester Paredes IA - Productos Fester")

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
                        # Bloques un poco más grandes para no perder contexto de aplicación
                        fragmentos = [texto_pag[i:i+1200] for i in range(0, len(texto_pag), 1200)]
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
                        fragmentos = [texto[i:i+1200] for i in range(0, len(texto), 1200)]
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
    st.error("⚠️ ALERTA: La IA no pudo extraer texto de tus archivos.")
else:
    st.success(f"📚 Base de datos activa: Cargados exitosamente {num_bloques} bloques de conocimiento desde tus PDFs.")

# 3. Buscador inteligente que limpia términos (ej. Acriton) y soporta historial
def buscar_contexto(pregunta, historial_corto, base, k=3):
    # Combinamos la pregunta con el último contexto para saber a qué se refiere con "ese" o "él"
    texto_busqueda = pregunta + " " + historial_corto
    
    # Limpieza básica de palabras clave comunes
    palabras = [p.lower().replace("®", "").replace("fester", "") for p in texto_busqueda.split() if len(p) > 3]
    if not palabras:
        return ""
        
    puntuaciones = []
    for item in base:
        texto_limpio = item["texto"].lower().replace("®", "")
        # Damos más peso si encuentra marcas importantes como 'acriton', 'vaportite', 'festerbond'
        puntos = sum(3 if palabra in texto_limpio else 0 for palabra in palabras)
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
if prompt := st.chat_input("¿Qué rendimiento o producto deseas validar? o que situacion de humedad tienes el dia de hoy?"):
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Crear un contexto del último mensaje para que no pierda el hilo de "ese producto"
    ultimo_contexto = ""
    if len(st.session_state.messages) > 0:
        ultimo_contexto = st.session_state.messages[-1]["content"]
        
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Buscar en los PDFs usando la pregunta inteligente
    contexto_manuales = buscar_contexto(prompt, ultimo_contexto, base_conocimiento)

    contexto_sistema = (
        "Eres el Asesor oficial de Fester Paredes. Tu cliente es un ingeniero, arquitecto en obra, o cualquier persona que necesite ayuda con los productos fester.\n"
        "Reglas estrictas de comportamiento:\n"
        "1. Responde de forma clara y estructurada. Puedes usar viñetas o pasos numéricos si te piden aplicaciones.\n"
        "2. IMPORTANTE: Termina siempre tus ideas y oraciones por completo. No te cortes a la mitad.\n"
        "3. Usa ÚNICAMENTE los datos oficiales provistos abajo. Si el dato exacto no viene ahí, indícalo amablemente.\n"
        "4. Menciona siempre de qué archivo y página proviene la información técnica (ej. Catálogo pág. X) para dar certeza.\n\n"
        f"TEXTO OFICIAL EXTRAÍDO DE TUS MANUALES:\n{contexto_manuales if contexto_manuales else 'No hay información directa en los documentos.'}"
    )

    with st.chat_message("assistant"):
        try:
            completion = client.chat.completions.create(
                model="openai/gpt-oss-120b",

                messages=[
                    {"role": "system", "content": contexto_sistema},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,  
                max_tokens=700,  # Ampliado a 700 para que NUNCA deje las oraciones a medias
            )
            response = completion.choices[0].message.content
            st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})
        except Exception as e:
            st.error(f"Hubo un error con el motor de IA: {e}")
