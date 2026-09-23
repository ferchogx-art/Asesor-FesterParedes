import glob
import os
import re
import streamlit as st
from groq import Groq

st.set_page_config(page_title="Asesor Técnico Fester", page_icon="🏗️", layout="centered")
st.title("🏗️ Asesor Técnico FesterParedes IA")
st.write("Sistema experto con buscador flexible y aprendizaje en vivo.")

# 1. Conectar con la API de Groq
api_key = os.environ.get("GROQ_API_KEY", st.secrets.get("GROQ_API_KEY", ""))
if not api_key:
    st.error("Falta configurar la clave GROQ_API_KEY en los Secrets.")
    st.stop()

client = Groq(api_key=api_key)
MODELO_FAVORITO = "openai/gpt-oss-120b"

# 2. Inicializar memorias persistentes en el servidor
if "messages" not in st.session_state:
    st.session_state.messages = []
if "memoria_aprendizaje" not in st.session_state:
    st.session_state.memoria_aprendizaje = {}  # Guarda tus lecciones en vivo
if "mostrar_caja_retro" not in st.session_state:
    st.session_state.mostrar_caja_retro = False
if "pregunta_pendiente" not in st.session_state:
    st.session_state.pregunta_pendiente = ""

# 3. Carga inteligente de PDFs
@st.cache_resource
def extraer_conocimiento_fester():
    texto_completo = []
    for ruta in glob.glob("*.pdf"):
        nombre_archivo = os.path.basename(ruta)
        try:
            import fitz
            with fitz.open(ruta) as doc:
                for num_pag, pagina in enumerate(doc):
                    texto_pag = pagina.get_text()
                    if texto_pag.strip():
                        texto_completo.append({
                            "origen": nombre_archivo,
                            "referencia": f"Pág. {num_pag + 1}",
                            "texto": texto_pag,
                        })
        except Exception as error:
            print(f"Error leyendo {nombre_archivo}: {error}")
    return texto_completo

base_conocimiento = extraer_conocimiento_fester()

# Diagnóstico limpio en pantalla
num_bloques = len(base_conocimiento)
st.success(f"📊 Base de datos activa: {num_bloques} páginas indexadas de fichas técnicas.")

# 4. Función de normalización (ej: "cm202" encuentra "cm-202")
def normalizar_termino(texto):
    return re.sub(r'[-.\s®™]', '', texto.lower())

def buscar_fichas(consulta, historial):
    consulta_limpia = f"{consulta} {historial}".lower()
    
    # Enrutamiento por zona real de obra
    es_charola_zona = any(x in consulta_limpia for x in ["charola", "baño", "regadera", "cl"])
    es_salitre_zona = any(x in consulta_limpia for x in ["salitre", "cr65"])
    es_asfalto_zona = any(x in consulta_limpia for x in ["chapopote", "asfalto", "vaportite", "cimentacion"])
    es_techo_zona = any(x in consulta_limpia for x in ["techo", "losa", "azotea", "acriton", "fester a"])

    equivalencias = {
        "chapopote": "vaportite asfalto",
        "asfalto": "vaportite",
        "acrilico": "acriton fester a",
        "techo": "azotea",
        "losa": "azotea",
        "terraza": "cr66",
        "vitropiso": "cr66",
    }
    
    consulta_busqueda = consulta_limpia
    for termino, reemplazo in equivalencias.items():
        if termino in consulta_busqueda:
            consulta_busqueda += f" {reemplazo}"

    palabras = [p for p in re.findall(r"[\wáéíóúüñ-]+", consulta_busqueda) if len(p) > 2]
    palabras_normalizadas = [normalizar_termino(p) for p in palabras]

    resultados = []
    for item in base_conocimiento:
        texto_base = item["texto"].lower()
        texto_normalizado = normalizar_termino(item["texto"])
        nombre_normalizado = normalizar_termino(item["origen"])
        
        # Candados de exclusión por zona
        if es_charola_zona and "cl" not in nombre_normalizado and "cl52" not in texto_normalizado:
            continue  
        if es_salitre_zona and "cr65" not in nombre_normalizado and "cr65" not in texto_normalizado:
            continue
        if es_asfalto_zona and "vaportite" not in nombre_normalizado:
            continue
        if es_techo_zona and ("cl" in nombre_normalizado or "cr" in nombre_normalizado or "cf" in nombre_normalizado):
            continue

        puntos = 0
        for p, p_norm in zip(palabras, palabras_normalizadas):
            if p in texto_base or p_norm in texto_normalizado:
                puntos += 5
            if p_norm in nombre_normalizado:
                puntos += 40  # Bono por coincidir con el nombre de la ficha técnica
                
        if "tienda" in nombre_normalizado or "respuestas" in nombre_normalizado:
            puntos *= 2

        if puntos > 0:
            resultados.append((puntos, item))

    if resultados:
        resultados.sort(key=lambda x: x[0], reverse=True)
    return "".join(f"\n[Ficha: {item['origen']}]\n{item['texto']}\n" for _, item in resultados[:2])

# 5. Pintar historial en pantalla
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 6. Caja de Aprendizaje en Vivo (Retroalimentación)
if st.session_state.mostrar_caja_retro:
    with st.expander("🎓 ¡Profesor FesterParedes! Enséñale la respuesta correcta a la IA", expanded=True):
        st.info(f"Escribe cómo responder a: *\"{st.session_state.pregunta_pendiente}\"*")
        nueva_respuesta = st.text_area("Escribe la solución oficial de la tienda aquí:")
        if st.button("Guardar lección en la memoria de la IA"):
            if nueva_respuesta.strip():
                clave_memoria = normalizar_termino(st.session_state.pregunta_pendiente)
                st.session_state.memoria_aprendizaje[clave_memoria] = nueva_respuesta.strip()
                st.success("¡Entendido! He aprendido la lección.")
                st.session_state.mostrar_caja_retro = False
                st.rerun()

# 7. Entrada del usuario
if prompt := st.chat_input("¿Qué problema tienes en obra o qué producto deseas validar?"):
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    prompt_lower = prompt.lower().strip()
    prompt_normalizado = normalizar_termino(prompt_lower)
    historial_texto = " ".join(m["content"] for m in st.session_state.messages[-4:]).lower()

    # Saludos
    if re.search(r"\b(hola|holis|buen[oa]s?|saludos|qu[eé]\s+tal|buenas\s+tardes|buenos\s+dias)\b", prompt_lower):
        with st.chat_message("assistant"):
            res = "¡Hola! Soy tu amigo Asesor FesterParedes, a la orden. ¿En qué te puedo apoyar hoy?"
            st.markdown(res)
            st.session_state.messages.append({"role": "assistant", "content": res})
            st.stop()

    # Buscar en memoria de aprendizaje
    respuesta_aprendida = ""
    for clave, valor in st.session_state.memoria_aprendizaje.items():
        if clave in prompt_normalizado or prompt_normalizado in clave:
            respuesta_aprendida = valor
            break

    if respuesta_aprendida:
        with st.chat_message("assistant"):
            st.markdown(respuesta_aprendida)
            st.session_state.messages.append({"role": "assistant", "content": respuesta_aprendida})
            st.stop()

    # Búsqueda en PDFs
    contexto_manuales = buscar_fichas(prompt, historial_texto)
    mensaje_no_info = "No comprendo del todo tu solicitud o la información exacta no viene en las fichas. Por favor comunícate con un especialista al **3317011786**."

    if not contexto_manuales.strip():
        with st.chat_message("assistant"):
            st.markdown(mensaje_no_info)
            st.session_state.messages.append({"role": "assistant", "content": mensaje_no_info})
            st.session_state.pregunta_pendiente = prompt
            st.session_state.mostrar_caja_retro = True
            st.rerun()

    contexto_sistema = f"""
Eres el Asesor Técnico Senior de Fester México. Responde siempre en un tono amable, claro, ultra conciso y profesional. Máximo 2 párrafos cortos.

REGLAS CRÍTICAS:
1. Si el cliente pregunta por una CHAROLA DE BAÑO o REGADERA, el producto oficial es FESTER CL-52. Prohibido recomendar Vaportite en baños.
2. Si los datos recuperados abajo no contienen la respuesta exacta del producto consultado, di textualmente: {mensaje_no_info}
3. Si te dan m², calcula el consumo basado en la ficha técnica inferior.

TEXTO OFICIAL DE LA FICHA SELECCIONADA:
{contexto_manuales}
"""

    with st.chat_message("assistant"):
        try:
            completion = client.chat.completions.create(
                model=MODELO_FAVORITO,
                messages=[
                    {"role": "system", "content": contexto_sistema},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.0,
                max_tokens=500
            )
            response = completion.choices[0].message.content
            
            if "3317011786" in response or "No comprendo" in response:
                st.session_state.pregunta_pendiente = prompt
                st.session_state.mostrar_caja_retro = True
                
            st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})
            if st.session_state.mostrar_caja_retro:
                st.rerun()
        except Exception as error:
            st.error(f"Error en motor IA: {error}")
