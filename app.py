import streamlit as st
import os
import glob
from groq import Groq

st.set_page_config(page_title="Asesor Técnico FesterParedes", page_icon="🏗️", layout="centered")
st.title("🏗️ Asesor Fester Paredes IA - Productos Fester")
st.write("Filtro técnico avanzado para evitar mezclas de productos acrílicos, asfálticos y cementosos.")

# 1. Conectar con la API de Groq
api_key = os.environ.get("GROQ_API_KEY", st.secrets.get("GROQ_API_KEY", ""))
if not api_key:
    st.error("Falta configurar la clave GROQ_API_KEY en los Secrets.")
    st.stop()

client = Groq(api_key=api_key)

# 2. Carga inteligente manteniendo el contexto estricto de la página
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

with st.spinner("Sincronizando manuales con validación de sistemas..."):
    base_conocimiento = extraer_conocimiento_fester()

num_bloques = len(base_conocimiento)
if num_bloques == 0:
    st.error("⚠️ ALERTA: No se cargaron PDFs.")
else:
    st.success(f"📚 Base de datos activa: Cargadas {num_bloques} páginas oficiales.")

# 3. BUSCADOR CON FILTRADO EXCLUSIVO POR FAMILIA DE PRODUCTO
def buscar_contexto(pregunta, base, k=3):
    pregunta_lower = pregunta.lower()
    
    # Detectar qué familia está buscando el usuario realmente
    es_acrilico = any(x in pregunta_lower for x in ["acriton", "fester a", "a3", "a5", "a7", "proshield", "elastomero"])
    es_asfaltico = any(x in pregunta_lower for x in ["vaportite", "hidroprimer", "microfest", "asfaltico", "solvent"])
    es_cementoso = any(x in pregunta_lower for x in ["cr-65", "cr-66", "cx-01", "cisterna", "cementoso"])
    
    palabras = [p for p in pregunta_lower.split() if len(p) > 2]
    puntuaciones = []
    
    for item in base:
        texto_manual = item["texto"].lower()
        puntos = 0
        
        # Penalizar fragmentos que mezclan tecnologías incompatibles con la pregunta
        if es_acrilico and any(x in texto_manual for x in ["vaportite", "hidroprimer", "asfáltico"]):
            continue  # Salta esta página si es asfáltica y el usuario busca acrílicos
        if es_asfaltico and "acriton" in texto_manual:
            continue
            
        for palabra in palabras:
            if palabra in texto_manual:
                puntos += 2
                if palabra in ["rendimiento", "aplicación", "capa", "litros", "m²"]:
                    puntos += 1
                    
        if puntos > 0:
            puntuaciones.append((puntos, item))
            
    puntuaciones.sort(key=lambda x: x[0], reverse=True)
    
    contexto_formateado = ""
    for puntos, res in puntuaciones[:k]:
        contexto_formateado += f"\n[PÁGINA OFICIAL: {res['origen']} - {res['referencia']}]\n{res['texto']}\n"
    return contexto_formateado

# 4. Historial
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 5. Ejecución con Prompt de Restricción Extrema
if prompt := st.chat_input("¿Qué duda técnica deseas validar?"):
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    contexto_manuales = buscar_contexto(prompt, base_conocimiento)

    contexto_sistema = (
        "Eres el Ingeniero de Soporte Técnico Senior de Fester Paredes. Tu misión es dar instrucciones de obra IMPECABLES y SIN ERRORES.\n"
        "REGLAS DE SEGURIDAD CONTRA CONFUSIONES:\n"
        "1. Los sistemas ACRÍLICOS (Fester Acriton, Fester A3/A5/A7) se imprimen EXCLUSIVAMENTE con 'Fester Acriton Sellador' (Rendimiento 5 m²/L) y se aplican a razón de 1 a 1.5 Litros por m² en total (NUNCA 8 o 9 m² por litro).\n"
        "2. El 'Fester Hidroprimer' y 'Vaportite 550' pertenecen al sistema ASFÁLTICO. NUNCA los mezcles ni los recomiendes en un proceso acrílico.\n"
        "3. El 'Fester CX-01' es un taponero cementoso para fugas de agua con presión. NUNCA lo listes como un reparador de grietas común para losas antes de acrílicos.\n"
        "4. Si los documentos provistos abajo no mencionan explícitamente un dato para el producto consultado, di que no cuentas con el registro exacto en lugar de cruzar información de otras páginas.\n\n"
        f"TEXTO ESTRICTO DE LAS PÁGINAS SELECCIONADAS:\n{contexto_manuales}"
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
                max_tokens=700,
            )
            response = completion.choices[0].message.content
            st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})
        except Exception as e:
            st.error(f"Error: {e}")
