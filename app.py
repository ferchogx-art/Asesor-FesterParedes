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
                            "texto": texto_pag,
                        })
        except Exception as error:
            print(f"Error leyendo {nombre_archivo}: {error}")
    return texto_completo

base_conocimiento = extraer_conocimiento_fester()
st.success(f"📟 Sistema en línea: {len(base_conocimiento)} páginas de fichas técnicas cargadas.")

# Pintar historial
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

def guardar_respuesta(respuesta):
    with st.chat_message("assistant"):
        st.markdown(respuesta)
    st.session_state.messages.append({"role": "assistant", "content": respuesta})

# 4. Función de normalización de códigos
def normalizar_termino(texto):
    return re.sub(r'[-.\s®™]', '', texto.lower())

# 5. Buscador Inteligente con Memoria de Hilo de Conversación
def buscar_fichas(consulta, historial):
    consulta_limpia = f"{consulta} {historial}".lower()
    
    # AMARRE DE MEMORIA DE ZONA
    es_charola = any(x in consulta_limpia for x in ["charola", "baño", "regadera", "cl52", "cl-52"])
    es_salitre = any(x in consulta_limpia for x in ["salitre", "cr65", "cr-65"])
    es_asfalto = any(x in consulta_limpia for x in ["chapopote", "asfalto", "vaportite", "desplante", "cimentacion"])
    es_techo = any(x in consulta_limpia for x in ["techo", "losa", "azotea", "acriton", "fester a", "proshield", "gotera", "filtracion"])
    es_cr66 = any(x in consulta_limpia for x in ["cr66", "cr-66", "cisterna", "alberca"])

    palabras = [p for p in re.findall(r"[\wáéíóúüñ-]+", consulta_limpia) if len(p) > 2]

    resultados_tienda = []
    resultados_fabrica = []
    
    for item in base_conocimiento:
        texto_item = item["texto"].lower()
        nombre_item = item["origen"].lower()
        
        # Filtros estrictos de exclusión de zona
        if "tienda" not in nombre_item and "respuestas" not in nombre_item:
            if es_charola and "cl" not in nombre_item: continue
            if es_salitre and "cr65" not in nombre_item: continue
            if es_asfalto and "vaportite" not in nombre_item: continue
            if es_cr66 and "cr66" not in nombre_item: continue
            if es_techo and ("cl" in nombre_item or "cr" in nombre_item or "cf" in nombre_item or "nanotech" in nombre_item):
                continue

        puntos = sum(5 for palabra in palabras if palabra in texto_item)
        puntos += sum(35 for palabra in palabras if palabra in nombre_item)
        
        if puntos > 0:
            if "tienda" in nombre_item or "respuestas" in nombre_item:
                resultados_tienda.append((puntos + 100, item))
            else:
                resultados_fabrica.append((puntos, item))

    contexto_final = ""
    if resultados_tienda:
        resultados_tienda.sort(key=lambda x: x, reverse=True)
        for _, res in resultados_tienda[:1]:
            contexto_final += f"\n[MANUAL DE TIENDA OFICIAL: {res['origen']}]\n{res['texto']}\n"
    else:
        if resultados_fabrica:
            resultados_fabrica.sort(key=lambda x: x, reverse=True)
            for _, res in resultados_fabrica[:1]:
                contexto_final += f"\n[Ficha de Fábrica de Respaldo: {res['origen']}]\n{res['texto']}\n"
                
    return contexto_final

# 6. Entrada del usuario
if prompt := st.chat_input("¿Qué problema tienes en obra o qué producto deseas validar?"):
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    prompt_lower = prompt.lower().strip()
    prompt_normalizado = normalizar_termino(prompt_lower)
    historial_texto = " ".join(m["content"] for m in st.session_state.messages[-5:]).lower()

    # Saludos directos locales
    if re.search(r"\b(hola|holis|buen[oa]s?|saludos|qu[eé]\s+tal)\b", prompt_lower):
        guardar_respuesta("¡Hola! Soy tu amigo Asesor FesterParedes, a la orden. ¿En qué te puedo apoyar hoy?")
        st.stop()

    # Buscar en memoria de aprendizaje local
    if prompt_normalizado in st.session_state.memoria_aprendizaje:
        guardar_respuesta(st.session_state.memoria_aprendizaje[prompt_normalizado])
        st.stop()

    # INTERCEPCIÓN FIEL A LA FICHA TÉCNICA - SIN MENTIRAS DE POLIURETANO
    respuesta_directa = ""
    if any(g in prompt_lower for g in ["gotera", "filtracion", "tiene goteras", "tengo filtraciones", "ya tiene"]):
        if "azotea" in historial_texto or "techo" in historial_texto or "losa" in historial_texto:
            respuesta_directa = (
                "Para una azotea con goteras activas la solución oficial es **FESTER ACRITON PRO SHIELD MAX** "
                "(Premium), disponible en duraciones de 4, 6 y 8 años. El proceso es:<br/><br/>"
                "1. Limpieza completa de la superficie.<br/>"
                "2. Aplicar una mano de Sellador Acriton.<br/>"
                "3. Resanar fisuras menores (≤ 4 mm) con Resanador Acriton (si superan 4 mm usar Superseal P).<br/>"
                "4. Refuerzo en puntos críticos (bajantes, chaflanes) con malla Acriflex o Revoflex.<br/>"
                "5. Aplicar dos capas de ACRITON PRO SHIELD MAX, cubriendo uniformemente ≈ 1 L/m² total a dos capas.<br/><br/>"
                "Este sistema **elastomérico 100% acrílico base agua de última generación** brinda una altísima resistencia a la abrasión "
                "por tránsito peatonal, excelente elasticidad ante movimientos estructurales de las losas y secado extra rápido, garantizando la eliminación de filtraciones."
            )
    elif "preventivo" in prompt_lower or "mera prevencion" in prompt_lower or "prevenir" in prompt_lower:
        if "azotea" in historial_texto or "techo" in historial_texto or "losa" in historial_texto:
            respuesta_directa = (
                "Excelente, al ser un trabajo preventivo (mantenimiento regular sin goteras activas), la recomendación ideal "
                "por presupuesto y desempeño es la **Línea Profesional Fester A** (disponible en presentaciones de 3, 5 y 7 años). "
                "Lleva el mismo proceso de preparación con Sellador Acriton y malla Revoflex en puntos críticos, rindiendo **1 Litro por m² a dos capas**."
            )

    if respuesta_directa:
        guardar_respuesta(respuesta_directa)
        st.stop()

    # Ejecutar el buscador
    contexto_manuales = buscar_fichas(prompt, historial_texto)
    mensaje_no_info = "No tengo esa información exacta en las fichas cargadas. Por favor comunícate con un especialista al **3317011786**."

    contexto_sistema = f"""
Eres el Asesor Técnico Senior de Fester México. Tu tono es profesional, claro, atento y muy conciso. Máximo 2 párrafos cortos.

REGLAS CRÍTICAS DE INGENIERÍA:
1. Recuerda que Fester Acritón Pro Shield Max es un sistema ELASTOMÉRICO 100% ACRÍLICO BASE AGUA. Está prohibido decir que contiene poliuretano o solventes.
2. Si los datos del texto oficial inferior vienen vacíos o no corresponden al área platicada, responde textualmente: {mensaje_no_info}

TEXTO REAL EXTRAÍDO PARA RESPONDER:
{contexto_manuales if contexto_manuales else ''}
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
            
            # FORMATO DE EXTRACCIÓN SEGURO Y COMPATIBLE PARA EL MODELO FIJO
            response = completion.choices.message.content
            
            if mensaje_no_info in response or "3317011786" in response:
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
                
                st.warning("💡 MODO APRENDIZAJE: Agrega la solución correcta para enseñarle a la IA:")
                with st.form(key=f"form_aprendizaje_{prompt_normalizado}"):
                    nueva_respuesta_experta = st.text_area("Escribe la recomendación de mostrador aquí:")
                    if st.form_submit_button("Guardar en el cerebro de la IA") and nueva_respuesta_experta.strip():
                        st.session_state.memoria_aprendizaje[prompt_normalizado] = nueva_respuesta_experta.strip()
                        st.success("¡Guardado! He aprendido la lección de mostrador.")
            else:
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
