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
# CAMBIO DE MOTOR DEFINITIVO: Modelo insignia permanente en la red de producción de Groq
MODELO_FAVORITO = "llama-3.1-8b-instant"

# 2. Inicializar memorias en el servidor
if "messages" not in st.session_state:
    st.session_state.messages = []
if "memoria_aprendizaje" not in st.session_state:
    st.session_state.memoria_aprendizaje = {}

# Carga inteligente de PDFs
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

# Pintar historial en pantalla
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

def guardar_respuesta(respuesta):
    with st.chat_message("assistant"):
        st.markdown(respuesta)
    st.session_state.messages.append({"role": "assistant", "content": respuesta})

# 3. Función de normalización de códigos
def normalizar_termino(texto):
    return re.sub(r'[-.\s®™]', '', texto.lower())

# 4. Buscador Inteligente con Prioridad de Tienda y Ordenamiento Numérico Corregido
def buscar_fichas(consulta, historial):
    consulta_limpia = f"{consulta} {historial}".lower()
    
    es_charola = any(x in consulta_limpia for x in ["charola", "baño", "regadera", "cl52", "cl-52"])
    es_salitre = any(x in consulta_limpia for x in ["salitre", "cr65", "cr-65", "muro", "pared", "humedad"])
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
                resultados_tienda.append((puntos + 150, item))
            else:
                resultados_fabrica.append((puntos, item))

    contexto_final = ""
    # ORDENAMIENTO SEGURO USANDO EL ÍNDICE NUMÉRICO DE COINCIDENCIAS (Evita el viejo TypeError)
    if resultados_tienda:
        resultados_tienda.sort(key=lambda x: x[0], reverse=True)
        for _, res in resultados_tienda[:2]:
            contexto_final += f"\n[MANUAL DE TIENDA OFICIAL: {res['origen']}]\n{res['texto']}\n"
    else:
        if resultados_fabrica:
            resultados_fabrica.sort(key=lambda x: x[0], reverse=True)
            for _, res in resultados_fabrica[:1]:
                contexto_final += f"\n[Ficha de Fábrica de Respaldo: {res['origen']}]\n{res['texto']}\n"
                
    return contexto_final

def es_sondeo_inicial_azotea(texto, historial):
    texto_completo = f"{historial} {texto}".lower()
    pide_rec = any(f in texto_completo for f in ("que me recomiendas", "cual me recomiendas", "recomienda", "que aplico", "que impermeabilizante"))
    es_zona = any(p in texto_completo for p in ("azotea", "techo", "losa"))
    ya_respondio_sondeo = any(p in historial for p in ["filtraciones", "preventivo", "tengo filtraciones", "ya tengo", "tiene goteras", "goteras activas"])
    return pide_rec and es_zona and not ya_respondio_sondeo

# 5. Procesamiento del chat
if prompt := st.chat_input("¿Qué problema tienes en obra o qué producto deseas validar?"):
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    prompt_lower = prompt.lower().strip()
    prompt_normalizado = normalizar_termino(prompt_lower)
    historial_texto = " ".join(m["content"] for m in st.session_state.messages[-6:]).lower()

    # Filtro de Saludos Estricto
    if prompt_lower in ["hola", "buenos dias", "buenas tardes", "saludos", "holis", "que tal"] or (re.search(r"\b(hola|holis)\b", prompt_lower) and len(prompt_lower) < 8):
        guardar_respuesta("¡Hola! Soy tu amigo Asesor FesterParedes, a la orden. ¿En qué te puedo apoyar hoy?")
        st.stop()

    # VERIFICACIÓN DE RETROALIMENTACIÓN MANUAL
    if prompt_normalizado in st.session_state.memoria_aprendizaje:
        guardar_respuesta(st.session_state.memoria_aprendizaje[prompt_normalizado])
        st.stop()

    # INTERCEPCIÓN DE ARCHIVO MAESTRO
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
                "Este sistema **elastomérico 100% acrílico base agua de última generación** brinda una altísima resistencia a la abrasión, "
                "excelente elasticidad ante los movimientos de la losa y secado extra rápido."
            )
    elif "preventivo" in prompt_lower or "mera prevencion" in prompt_lower or "prevenir" in prompt_lower:
        if "azotea" in historial_texto or "techo" in historial_texto or "losa" in historial_texto:
            respuesta_directa = (
                "Excelente, al ser un trabajo preventivo (mantenimiento regular sin goteras activas), la recomendación ideal "
                "por presupuesto y desempeño es la **Línea Profesional Fester A** (disponible en presentaciones de 3, 5 y 7 años). "
                "Lleva el mismo proceso de preparación con Sellador Acriton y malla Revoflex in puntos críticos, rindiendo **1 Litro por m² a dos capas**."
            )

    if respuesta_directa:
        guardar_respuesta(respuesta_directa)
        st.stop()

    # Ejecutar el buscador
    contexto_manuales = buscar_fichas(prompt, historial_texto)
    mensaje_no_info = "No tengo esa información exacta en las fichas cargadas. Por favor comunícate con un especialista al **3317011786**."

    contexto_sistema = f"""
Eres el Asesor Técnico Senior de Fester México. Tu tono es profesional, claro, atento y muy conciso. Responde en máximo 2 párrafos cortos.

REGLAS CRÍTICAS DE INGENIERÍA:
1. Recuerda que Fester Acritón Pro Shield Max es un sistema ELASTOMÉRICO 100% ACRÍLICO BASE AGUA. Está prohibido decir que contiene poliuretano o solventes.
2. Si te preguntan por problemas de HUMEDAD O SALITRE EN EL MURO o PARED, la recomendación oficial según tu manual de tienda es el FESTER CR-65 y se explica brevemente su proceso (retirar enjarre, limpiar superficie, resanar con CM-200, dos manos cruzadas y curado obligatorio con agua).
3. Si los datos del texto oficial inferior vienen vacíos o no corresponden al área platicada, responde textualmente: {mensaje_no_info}

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
                max_tokens=450
            )
            response = completion.choices[0].message.content
            
            if mensaje_no_info in response or "3317011786" in response:
                st.markdown(response)
