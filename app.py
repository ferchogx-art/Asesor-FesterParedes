import streamlit as st
import os
import glob
from groq import Groq

st.set_page_config(page_title="Asesor Técnico Fester", page_icon="🏗️", layout="centered")
st.title("🏗️ Asesor Técnico FesterParedes IA")
st.write("Sistema experto con consulta directa a fichas técnicas oficiales.")

# 1. Conectar con la API de Groq usando el modelo libre oficial y vigente en 2026
api_key = os.environ.get("GROQ_API_KEY", st.secrets.get("GROQ_API_KEY", ""))
if not api_key:
    st.error("Falta configurar la clave GROQ_API_KEY en los Secrets.")
    st.stop()

client = Groq(api_key=api_key)
MODELO_FAVORITO = "openai/gpt-oss-120b"
 # Cambiado al modelo estable oficial para evitar bloqueos

# 2. Carga inteligente de fichas técnicas en formato PDF (Sueltas en GitHub)
@st.cache_resource
def extraer_conocimiento_fester():
    texto_completo = []
    archivos_validos = glob.glob("*.pdf")
    for ruta in archivos_validos:
        nombre_archivo = os.path.basename(ruta)
        try:
            import fitz  # PyMuPDF
            doc = fitz.open(ruta)
            for num_pag, pagina in enumerate(doc):
                texto_pag = pagina.get_text()
                if texto_pag.strip():
                    texto_completo.append({
                        "origen": nombre_archivo,
                        "referencia": f"Pág. {num_pag + 1}",
                        "texto": texto_pag
                    })
        except Exception as e:
            print(f"Error leyendo {nombre_archivo}: {e}")
    return texto_completo

base_conocimiento = extraer_conocimiento_fester()

# Panel visual de diagnóstico
num_bloques = len(base_conocimiento)
if num_bloques == 0:
    st.error("⚠️ ALERTA: No se detectaron PDFs en la raíz de GitHub.")
else:
    st.success(f"📊 Base de datos activa: Conectado a las fichas técnicas individuales ({num_bloques} páginas).")

# 3. Historial de chat persistente (Memoria del Servidor)
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 4. Procesamiento de la Consulta
if prompt := st.chat_input("¿Qué problema tienes en obra o qué producto deseas validar?"):
    with st.chat_message("user"):
        st.markdown(prompt)
    
    st.session_state.messages.append({"role": "user", "content": prompt})
    prompt_lower = prompt.lower()

    # Recopilar historial acumulado
    historial_texto = " ".join([m["content"] for m in st.session_state.messages[-3:]]).lower()

    # Filtros manuales forzados para responder sin depender de la IA si el usuario saluda o busca un producto directo
    solucion_forzada = ""
    
    if any(saludo in prompt_lower.strip() for saludo in ["hola", "buen dia", "buenas tardes", "buenos dias", "saludos"]):
        solucion_forzada = "¡Hola! Bienvenido al Asesor Técnico FesterParedes. ¿En qué producto o problema de humedad en obra te puedo ayudar hoy?"
        
    elif prompt_lower.strip() in ["acriton", "quiero acriton", "necesito acriton", "me interesa acriton"]:
        solucion_forzada = (
            "Manejo tanto el **Fester Acriton Sellador** (utilizado como primario para preparar la superficie) como la línea de "
            "**Impermeabilizantes Premium Fester Acriton Pro Shield Max** (con durabilidades de 4, 6, 8 y 12 años). "
            "¿Cuál de estos dos te interesa validar para tu proyecto?"
        )

    if solucion_forzada:
        with st.chat_message("assistant"):
            st.markdown(solucion_forzada)
            st.session_state.messages.append({"role": "assistant", "content": solucion_forzada})
            
    else:
        # BÚSQUEDA FILTRADA EN TUS PDFs REALES
        contexto_manuales = ""
        palabras = [p for p in prompt_lower.split() if len(p) > 2]
        
        es_charola = any(x in historial_texto for x in ["charola", "baño", "regadera", "cl52", "cl-52", "muros de mi baño"])
        es_salitre = any(x in historial_texto for x in ["salitre", "cr65", "cr66", "cr-65", "cr-66"])
        es_techo = any(x in historial_texto for x in ["techo", "losa", "azotea", "lluvia", "proshield", "fester a", "azoteas"])
        
        puntuaciones = []
        for item_doc in base_conocimiento:
            texto_manual = item_doc["texto"].lower()
            nombre_archivo = item_doc["origen"].lower()
            
            if es_charola and "cl" not in nombre_archivo and "cl52" not in texto_manual:
                continue
            if es_salitre and "cr" not in nombre_archivo:
                continue
            if es_techo and ("cr" in nombre_archivo or "cl" in nombre_archivo or "cf" in nombre_archivo):
                continue
                
            puntos = sum(5 for p in palabras if p in texto_manual)
            if any(p in nombre_archivo for p in palabras):
                puntos += 25
                
            if puntos > 0:
                puntuaciones.append((puntos, item_doc))
        
        if puntuaciones:
            puntuaciones.sort(key=lambda x: x[0], reverse=True)
            for puntos, res in puntuaciones[:3]:
                contexto_manuales += f"\n[Ficha Oficial: {res['origen']} - {res['referencia']}]\n{res['texto']}\n"

        # Mensaje definitivo con tu teléfono real
        mensaje_no_info = "No tengo esa información exacta en las fichas cargadas. Por favor, comunícate con un técnico especialista al **3317011786**, ellos te terminarán de atender con mucho gusto."

        contexto_sistema = (
            "Eres el Asesor Técnico Senior de Fester México.\n"
            "Tu misión es responder de forma resumida en máximo 1 o 2 párrafos cortos y directos.\n\n"
            "REGLAS EN OBRA:\n"
            "1. Si te preguntan rendimiento o aplicación, busca los números (L/m², kg/m²) estrictamente en el texto de abajo.\n"
            "2. Si el texto de abajo está vacío o no contiene relación con la pregunta, responde EXACTAMENTE con esta frase y el número provisto: '" + mensaje_no_info + "'\n"
            "3. Está estrictamente PROHIBIDO dar números de asistencia o teléfonos que no sean el 3317011786.\n\n"
            f"TEXTO OFICIAL DE LA FICHA INDIVIDUAL:\n{contexto_manuales if contexto_manuales else 'Vacio'}"
        )

        with st.chat_message("assistant"):
            try:
                mensajes_ia = [{"role": "system", "content": contexto_sistema}]
                for msg in st.session_state.messages[-4:]:
                    mensajes_ia.append({"role": msg["role"], "content": msg["content"]})

                completion = client.chat.completions.create(
                    model=MODELO_FAVORITO,
                    messages=mensajes_ia,
                    temperature=0.0,
                    max_tokens=450,
                )
                response = completion.choices[0].message.content
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
            except Exception as e:
                st.error(f"Error en motor IA: {e}")
