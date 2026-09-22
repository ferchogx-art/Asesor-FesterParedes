import glob
import os
import re
import streamlit as st
from groq import Groq

st.set_page_config(page_title="Asesor Técnico Fester", page_icon="🏗️", layout="centered")
st.title("🏗️ Asesor Técnico FesterParedes IA")
st.write("Sistema experto con consulta prioritaria a tu manual de mostrador.")

# 1. Conectar con la API de Groq
api_key = os.environ.get("GROQ_API_KEY", st.secrets.get("GROQ_API_KEY", ""))
if not api_key:
    st.error("Falta configurar la clave GROQ_API_KEY en los Secrets.")
    st.stop()

client = Groq(api_key=api_key)
MODELO_FAVORITO = "openai/gpt-oss-120b"

# 2. Inicializar memorias en el servidor
if "messages" not in st.session_state:
    st.session_state.messages = []
if "memoria_aprendizaje" not in st.session_state:
    st.session_state.memoria_aprendizaje = {}
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
st.success(f"📟 Sistema en línea: {len(base_conocimiento)} páginas de fichas técnicas cargadas.")

# 4. Función de normalización de códigos
def normalizar_termino(texto):
    return re.sub(r'[-.\s®™]', '', texto.lower())

def buscar_fichas(consulta, historial):
    consulta_limpia = f"{consulta} {historial}".lower()
    consulta_norm = normalizar_termino(consulta_limpia)
    
    # ENRUTAMIENTO ESTRICTO POR CÓDIGO DE PRODUCTO
    es_cr66 = "cr66" in consulta_norm
    es_cl52 = "cl52" in consulta_norm or "charola" in consulta_norm or "baño" in consulta_norm
    es_cr65 = "cr65" in consulta_norm or "salitre" in consulta_norm
    es_vaportite = "vaportite" in consulta_norm or "chapopote" in consulta_norm or "asfalto" in consulta_norm
    es_acriton = "acriton" in consulta_norm or "proshield" in consulta_norm or "techo" in consulta_norm or "losa" in consulta_norm

    resultados = []
    for item in base_conocimiento:
        texto_norm = normalizar_termino(item["texto"])
        nombre_norm = normalizar_termino(item["origen"])
        
        # APLICACIÓN DE CANDADOS RADICALES DE EXCLUSIÓN
        if es_cr66 and "cr66" not in nombre_norm and "tienda" not in nombre_norm:
            continue
        if es_cl52 and "cl52" not in nombre_norm and "cl-52" not in nombre_norm and "tienda" not in nombre_norm:
            continue
        if es_cr65 and "cr65" not in nombre_norm and "tienda" not in nombre_norm:
            continue
        if es_vaportite and "vaportite" not in nombre_norm and "tienda" not in nombre_norm:
            continue
        if es_acriton and ("cl" in nombre_norm or "cr" in nombre_norm or "vaportite" in nombre_norm) and "tienda" not in nombre_norm:
            continue

        puntos = 0
        if "tienda" in nombre_norm or "respuestas" in nombre_norm:
            puntos += 100  # Máxima prioridad absoluta a tu PDF de la tienda
        
        if "cr66" in consulta_norm and "cr66" in nombre_norm: puntos += 50
        if "cl52" in consulta_norm and "cl52" in nombre_norm: puntos += 50
        if "festerbond" in consulta_norm and "festerbond" in nombre_norm: puntos += 50

        # Coincidencias de texto básico
        palabras = [p for p in re.findall(r"[\wáéíóúüñ-]+", consulta_limpia) if len(p) > 2]
        for p in palabras:
            if p in item["texto"].lower(): puntos += 5

        if puntos > 0:
            resultados.append((puntos, item))

    if resultados:
        resultados.sort(key=lambda x: x[0], reverse=True) # Arreglado el ordenamiento numérico por índice de puntos
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
                st.success("¡Entendido! He aprendido la lección de mostrador.")
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

    # Intercepción flexible de saludos
    if re.search(r"\b(hola|holis|buen[oa]s?|saludos|qu[eé]\s+tal|buenas\s+tardes|buenos\s+dias)\b", prompt_lower):
        with st.chat_message("assistant"):
            res = "¡Hola! Soy tu amigo Asesor FesterParedes, a la orden. ¿En qué te puedo apoyar hoy?"
            st.markdown(res)
            st.session_state.messages.append({"role": "assistant", "content": res})
            st.stop()

    # Buscar en memoria de aprendizaje manual
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

    # Ejecutar el buscador blindado por código de producto
    contexto_manuales = buscar_fichas(prompt, historial_texto)
    mensaje_no_info = "No comprendo del todo tu solicitud o la información exacta no viene en las fichas. Por favor comunícate con un especialista al **3317011786**."

    contexto_sistema = f"""
Eres el Asesor Técnico Senior de Fester México. Tu tono es profesional, claro y ultra conciso. Responde en un máximo de 1 o 2 párrafos cortos.

REGLAS CRÍTICAS DE INGENIERÍA:
1. UNIDADES DE MEDIDA DE CONSUMO: Entrega rendimientos basándote estrictamente en el texto de abajo. Si hablas de Fester CR-66, el rendimiento oficial es en KILOGRAMOS (kg/m²) o por JUEGO COMPLETO, nunca en litros.
2. Si te preguntan por una AZOTEA o LOSA, antes de recomendar, sondea obligatoriamente de forma amable si ya cuentan con filtraciones activas o si es mera prevención para dar la opción idónea según tu manual.
3. Si los datos del texto oficial inferior vienen vacíos o no tienen relación, di exactamente: {mensaje_no_info}

TEXTO REAL EXTRAÍDO DE LAS FICHAS TÉCNICAS SELECCIONADAS:
{contexto_manuales if contexto_manuales else 'Vacio'}
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
            
            # NUEVA SINTAXIS SEGURA SELECCIONANDO EL CONTENIDO DE LA RESPUESTA DE GROQ DIRECTAMENTE
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

