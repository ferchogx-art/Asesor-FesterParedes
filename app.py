import streamlit as st
import os
import glob
import re
from groq import Groq

st.set_page_config(page_title="Asesor Técnico Fester", page_icon="🏗️", layout="centered")
st.title("🏗️ Asesor Técnico FesterParedes IA")
st.write("Sistema experto con sondeo de obra y diagnóstico de ingeniería.")

# 1. Conectar con la API de Groq usando tu modelo preferido fijo
api_key = os.environ.get("GROQ_API_KEY", st.secrets.get("GROQ_API_KEY", ""))
if not api_key:
    st.error("Falta configurar la clave GROQ_API_KEY en los Secrets.")
    st.stop()

client = Groq(api_key=api_key)

# 2. Carga inteligente de la base de conocimientos
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
                        texto_limpio = texto_pag.replace("®", "").replace("™", "")
                        texto_completo.append({
                            "origen": nombre_archivo,
                            "tipo": "pdf",
                            "referencia": f"Pág. {num_pag + 1}",
                            "texto": texto_limpio
                        })
            elif ruta.endswith(".txt") and "preguntas_frecuentes" in nombre_archivo:
                with open(ruta, "r", encoding="utf-8", errors="ignore") as f:
                    contenido = f.read()
                    bloques = contenido.split("PREGUNTA:")
                    for idx, b in enumerate(bloques):
                        if b.strip():
                            texto_completo.append({
                                "origen": "Manual de Respuestas Rápidas",
                                "tipo": "expert_txt",
                                "referencia": f"Bloque Experto {idx}",
                                "texto": "PREGUNTA: " + b.strip()
                            })
        except Exception as e:
            print(f"Error leyendo {nombre_archivo}: {e}")
    return texto_completo

base_conocimiento = extraer_conocimiento_fester()

# Panel visual de diagnóstico
num_bloques = len(base_conocimiento)
if num_bloques == 0:
    st.error("⚠️ ALERTA: No se detectaron archivos de soporte técnico en GitHub.")
else:
    st.success(f"📊 Base de datos activa: Conectado a las fichas técnicas individuales ({num_bloques} páginas).")

# 3. Buscador Avanzado con segmentación estricta por zona de obra
def buscar_contexto(pregunta, base, k=3):
    pregunta_limpia = pregunta.lower()
    
    # Determinar zona geográfica o elemento de la estructura
    es_techo = any(x in pregunta_limpia for x in ["techo", "losa", "azotea", "lluvia", "pluvial"])
    es_muro = any(x in pregunta_limpia for x in ["muro", "pared", "salitre", "fachada", "sótano"])
    es_hidrico = any(x in pregunta_limpia for x in ["alberca", "cisterna", "charola", "baño", "terraza", "espejo de agua"])
    
    palabras = [p for p in re.findall(r'\b\w+\b', pregunta_limpia) if p not in ['con', 'para', 'del', 'los', 'las', 'que', 'una', 'problema', 'tengo']]
    
    puntuaciones = []
    for item in base:
        texto_inferior = item["texto"].lower()
        
        # FILTROS DE SEGURIDAD EXCLUSIVOS PARA EVITAR CRUCES ERMÁNEOS:
        if es_techo and any(x in texto_inferior for x in ["cr-65", "cr-66", "cx-01", "salitre"]):
            continue  # No metas cementosos de muros si están preguntando explícitamente por techos/lluvia
        if es_muro and any(x in texto_inferior for x in ["acriton", "fester a", "proshield"]) and not "salitre" in texto_inferior:
            continue
            
        puntos = 0
        for palabra in palabras:
            if palabra in texto_inferior:
                if item["tipo"] == "expert_txt":
                    puntos += 35
                else:
                    puntos += 5
        if puntos > 0:
            puntuaciones.append((puntos, item))
            
    puntuaciones.sort(key=lambda x: x[0], reverse=True)
    
    contexto_formateado = ""
    for puntos, res in puntuaciones[:k]:
        contexto_formateado += f"\n[Fuente Oficial: {res['origen']} - {res['referencia']}]\n{res['texto']}\n"
    return contexto_formateado

# 4. Historial
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 5. Entrada del chat con Lógica de Sondeo Técnico Obligatorio
if prompt := st.chat_input("¿Qué problema tienes en obra o qué producto deseas validar?"):
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    prompt_lower = prompt.lower()
    
    # REGLA DE ORO DE SONDEO: ¿El usuario omitió decir dónde está el problema?
    conceptos_vagos = ["humedad", "filtracion", "filtración", "gotera", "impermeabilizar", "recomiendas", "remedio"]
    tiene_zona = any(x in prompt_lower for x in ["techo", "losa", "azotea", "muro", "pared", "salitre", "cisterna", "alberca", "baño", "charola", "terraza", "espejo"])
    
    # Si menciona términos de humedad pero no aclara el sitio, obligamos a la IA a hacer el sondeo comercial
    if any(vago in prompt_lower for vago in conceptos_vagos) and not tiene_zona:
        respuesta_sondeo = (
            "Para poder darte la recomendación exacta de Fester y evitar un error en la especificación, "
            "necesito realizar un breve sondeo de la obra. Por favor, compárteme:\n\n"
            "1. **¿En qué parte se localiza el problema?** (¿Es un techo/losa, un muro/pared con salitre, una cisterna, alberca o una charola de baño?)\n"
            "2. **¿Cuál es el área aproximada en metros cuadrados (m²)?**\n"
            "3. **¿Qué presupuesto o durabilidad estimada estás buscando?**\n\n"
            "Con estos datos te daré el producto oficial exacto, su rendimiento y el método de aplicación de su ficha técnica."
        )
        with st.chat_message("assistant"):
            st.markdown(respuesta_sondeo)
            st.session_state.messages.append({"role": "assistant", "content": respuesta_sondeo})
            
    else:
        # Si ya pasó el filtro o especificó la zona, corre el motor de inferencia normal
        contexto_manuales = buscar_contexto(prompt, base_conocimiento)

        contexto_sistema = (
            "Eres el Ingeniero de Soporte Técnico Senior de Fester Paredes México. Tu objetivo es asesorar con precisión ejecutiva sin mezclar tecnologías.\n"
            "REGLAS TÉCNICAS OBLIGATORIAS DE RECOMENDACIÓN:\n"
            "1. REGLA CR-66: El Fester CR-66 es de base cementosa elástica. Úsalo EXCLUSIVAMENTE para terrazas, cisternas, albercas y espejos de agua. "
            "SI EL USUARIO MENCIONA QUE LA TERRAZA ES MAYOR A 25 METROS CUADRADOS (m²), debes incluir esta ADVERTENCIA OBLIGATORIA: 'Nota técnica: Al ser un área mayor a 25 m², es indispensable ejecutar juntas de dilatación en la terraza para absorber los movimientos estructurales, evitar que el producto se fisure y prevenir fallas en el sistema'.\n"
            "2. REGLA DE TECHOS/LOSAS POR LLUVIA: Para humedad en techos provocada por lluvias, si el cliente busca algo económico, recomienda la Línea Fester A (3, 5, 7 años). Si busca algo premium de alta durabilidad, recomienda la Línea Fester Acriton (4, 6, 8, 12 años). NUNCA recomiendes la línea CR para techos expuestos.\n"
            "3. Estructura corta: Responde en máximo 2 o 3 párrafos concisos o viñetas directas al grano. Al final cita el documento oficial fuente."
        )

        with st.chat_message("assistant"):
            try:
                completion = client.chat.completions.create(
                    model="openai/gpt-oss-120b",
                    messages=[
                        {"role": "system", "content": contexto_sistema},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.0,
                    max_tokens=650,
                )
                response = completion.choices.message.content
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
            except Exception as e:
                st.error(f"Error en el motor: {e}")

