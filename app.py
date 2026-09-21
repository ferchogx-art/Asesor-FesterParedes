import streamlit as st
import os
import glob
import re
from groq import Groq

st.set_page_config(page_title="Asesor Técnico Fester", page_icon="🏗️", layout="centered")
st.title("🏗️ Asesor Técnico FesterParedes IA")
st.write("Sistema experto con sondeo de obra y diagnóstico de ingeniería.")

# 1. Conectar con la API de Groq usando tu modelo preferido
api_key = os.environ.get("GROQ_API_KEY", st.secrets.get("GROQ_API_KEY", ""))
if not api_key:
    st.error("Falta configurar la clave GROQ_API_KEY en los Secrets.")
    st.stop()

client = Groq(api_key=api_key)
MODELO_FAVORITO = "openai/gpt-oss-120b"

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

# 3. Historial de chat en pantalla
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 4. Lógica del Asesor de Obra Ejecutivo con Filtro de Contexto Estricto
if prompt := st.chat_input("¿Qué problema tienes en obra o qué producto deseas validar?"):
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Creamos un bloque de texto que junte los últimos mensajes para mantener la memoria del tema (ej. azotea)
    memoria_conversacion = ""
    if len(st.session_state.messages) > 0:
        memoria_conversacion = " ".join([m["content"] for m in st.session_state.messages[-3:]])
    
    st.session_state.messages.append({"role": "user", "content": prompt})
    prompt_lower = prompt.lower()
    contexto_busqueda = prompt_lower + " " + memoria_conversacion.lower()
    
    # --- FILTROS DE ANÁLISIS DE CONTEXTO MEJORADOS ---
    es_muro_salitre = any(x in contexto_busqueda for x in ["muro", "pared", "salitre", "fachada", "sotano"])
    es_techo_losa = any(x in contexto_busqueda for x in ["techo", "losa", "azotea", "lluvia", "gotera", "duradero", "azotera"])
    es_charola = any(x in contexto_busqueda for x in ["charola", "baño", "zona humeda", "cl52", "cl-52"])
    es_terraza_cisterna = any(x in contexto_busqueda for x in ["terraza", "cisterna", "alberca", "espejo de agua", "cr66", "cr-66"])

    solucion_maestra = ""

    # REGLA DE ORO 1: ¿Dijo Acriton a secas? Forzar sondeo para no asumir producto erróneo
    if prompt_lower.strip() in ["acriton", "quiero acriton", "necesito acriton", "me interesa acriton"]:
        solucion_maestra = (
            "Manejo tanto el **Fester Acriton Sellador** (primario acrílico para preparar la superficie) "
            "como los impermeabilizantes premium **Fester Acriton Proshield Max** (con durabilidades de 4, 6, 8 y 12 años).\n\n"
            "¿Cuál de los dos te interesa validar para tu proyecto?"
        )
    
    # REGLA DE ORO 2: Mensaje unificado e impecable de techos (Económico + Premium combinado)
    elif es_techo_losa:
        solucion_maestra = (
            "Para la humedad en el techo (losa) por lluvias, la recomendación oficial es la **Línea Fester A** "
            "(disponible en 3, 5 y 7 años). Para un rango medio te sugiero **Fester A 5 Años Fibratado**, que rinde entre "
            "1 a 1.5 Litros por m² a dos capas. \n\n"
            "Por otra parte, contamos con los impermeabilizantes **Premium**, que son los **Acritones Proshield Max** "
            "con durabilidad de 4, 6 y 8 años (así como la versión extrema de 12 años), los cuales ofrecen una tecnología avanzada "
            "de poliuretano con excelente resistencia al movimiento estructural de las losas."
        )
    elif es_charola:
        solucion_maestra = (
            "Para impermeabilizar una **charola de baño o zonas húmedas**, el producto oficial recomendado es **Fester CL-52**. "
            "Es un impermeabilizante cementoso elástico de rápida aplicación que evita filtraciones entre pisos."
        )
    elif es_muro_salitre:
        solucion_maestra = (
            "Para problemas de **humedad y salitre en muros o paredes**, la solución definitiva es la línea cementosa **Fester CR**:\n"
            "- **Fester CR-65:** Opción económica estándar, requiere curado con agua durante 2 días seguidos.\n"
            "- **Fester CR-66:** Opción premium elástica, bicomponente y NO necesita curado con agua."
        )
    elif es_terraza_cisterna:
        solucion_maestra = (
            "Para **terrazas, cisternas, albercas o espejos de agua**, el producto ideal es **Fester CR-66**.\n"
            "⚠️ **REGLA DE ORO DE INGENIERÍA EN TERRAZAS:** Si la terraza es mayor a **25 metros cuadrados**, es de carácter OBLIGATORIO realizar **juntas de dilatación** en la superficie. Esto evitará que el producto se fisure y falle debido a los movimientos estructurales."
        )

    with st.chat_message("assistant"):
        if solucion_maestra:
            st.markdown(solucion_maestra)
            st.session_state.messages.append({"role": "assistant", "content": solucion_maestra})
        else:
            # Búsqueda de respaldo en las fichas individuales si es algo muy específico o un saludo genérico
            contexto_manuales = ""
            palabras = [p for p in prompt_lower.split() if len(p) > 2]
            puntuaciones = []
            
            for item_doc in base_conocimiento:
                texto_manual = item_doc["texto"].lower()
                puntos = sum(3 for p in palabras if p in texto_manual)
                if puntos > 0:
                    puntuaciones.append((puntos, item_doc))
            
            if puntuaciones:
                puntuaciones.sort(key=lambda x: x, reverse=True)
            
            for puntos, res in puntuaciones[:2]:
                contexto_manuales += f"\n[Ficha: {res['origen']} - {res['referencia']}]\n{res['texto']}\n"

            # MENSAJE DE RESPALDO CON TU TELÉFONO OFICIAL DE ASISTENCIA
            mensaje_no_info = "No tengo esa información, favor de comunicarse con un técnico especialista por ejemplo al **3317011786**, ellos te terminarán de atender con mucho gusto."

            contexto_sistema = (
                "Eres el Asesor Técnico Ejecutivo de Fester México.\n"
                "Responde de forma resumida en máximo 1 o 2 párrafos cortos. Ve directo al grano.\n"
                "Si te saludan (como un 'hola'), responde de forma amable preguntando en qué producto o problema de obra puedes ayudar hoy.\n"
                f"REGLA CRÍTICA: Si el usuario te pregunta por un producto técnico que no está en las fichas o es de otra marca, responde EXACTAMENTE lo siguiente: '{mensaje_no_info}'\n\n"
                f"TEXTO OFICIAL DE LA FICHA INDIVIDUAL:\n{contexto_manuales}"
            )

            try:
                completion = client.chat.completions.create(
                    model=MODELO_FAVORITO,
                    messages=[
                        {"role": "system", "content": contexto_sistema},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.0,
                    max_tokens=350,
                )
                response = completion.choices.message.content
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
            except Exception as e:
                st.error(f"Error en motor IA ({MODELO_FAVORITO}): {e}")

