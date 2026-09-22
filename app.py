import glob
import os
import re
import streamlit as st
from groq import Groq

st.set_page_config(page_title="Asesor Técnico FesterParedes", page_icon="🏗️", layout="centered")
st.title("🏗️ Asesor Técnico FesterParedes IA")
st.write("Sistema experto con base de datos tolerante a errores de escritura y aprendizaje activo.")

# 1. Conectar con la API de Groq usando tu modelo preferido FIJO
api_key = os.environ.get("GROQ_API_KEY", st.secrets.get("GROQ_API_KEY", ""))
if not api_key:
    st.error("Falta configurar la clave GROQ_API_KEY en los Secrets.")
    st.stop()

client = Groq(api_key=api_key)
MODELO_FAVORITO = "openai/gpt-oss-120b"

# Función auxiliar para limpiar y normalizar texto (Elimina guiones y une códigos ej. cm-202 -> cm202)
def normalizar_cadena(texto):
    texto = texto.lower()
    # Quitamos acentos comunes
    texto = re.sub(r'[áäàâ]', 'a', texto)
    texto = re.sub(r'[éëèê]', 'e', texto)
    texto = re.sub(r'[íïìî]', 'i', texto)
    texto = re.sub(r'[óöòô]', 'o', texto)
    texto = re.sub(r'[úüùû]', 'u', texto)
    # Creamos una versión sin guiones ni espacios para comprar códigos como cm202 o cl52
    sin_simbolos = re.sub(r'[^a-z0-9ñ]', '', texto)
    return texto, sin_simbolos

# 2. Carga inteligente de fichas técnicas y archivos de texto de conocimiento humano
@st.cache_resource
def extraer_conocimiento_fester():
    texto_completo = []
    # Cargamos PDFs sueltos
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
                            "tipo": "pdf",
                            "referencia": f"Pág. {num_pag + 1}",
                            "texto": texto_pag
                        })
        except Exception as error:
            print(f"Error leyendo PDF {nombre_archivo}: {error}")
            
    # Cargamos archivo de preguntas frecuentes hechas en tienda (.txt) si existe
    for ruta in glob.glob("*.txt"):
        nombre_archivo = os.path.basename(ruta)
        if "preguntas" in nombre_archivo.lower() or "experto" in nombre_archivo.lower():
            try:
                with open(ruta, "r", encoding="utf-8", errors="ignore") as f:
                    contenido = f.read()
                    bloques = contenido.split("PREGUNTA:")
                    for idx, b in enumerate(bloques):
                        if b.strip():
                            texto_completo.append({
                                "origen": "Manual de Experiencia FesterParedes",
                                "tipo": "txt_experto",
                                "referencia": f"Caso de Tienda {idx + 1}",
                                "texto": "PREGUNTA: " + b.strip()
                            })
            except Exception as error:
                print(f"Error leyendo TXT {nombre_archivo}: {error}")
                
    return texto_completo

base_conocimiento = extraer_conocimiento_fester()
num_bloques = len(base_conocimiento)

# Inicializar Base de Datos de Aprendizaje Local en la memoria del Servidor
if "base_aprendizaje" not in st.session_state:
    st.session_state.base_aprendizaje = {}

if num_bloques == 0:
    st.error("⚠️ ALERTA: No se detectaron PDFs ni TXT en la raíz de GitHub.")
else:
    st.success(f"📊 Sistema Activo: {num_bloques} bloques indexados (PDFs + Experiencia de Tienda).")

# 3. Historial de chat persistente
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

def guardar_respuesta(respuesta):
    with st.chat_message("assistant"):
        st.markdown(respuesta)
    st.session_state.messages.append({"role": "assistant", "content": respuesta})

# 4. Buscador tolerante a abreviaciones y códigos pegados
def buscar_fichas(consulta, historial):
    consulta_limpia, consulta_codigo = normalizar_cadena(f"{consulta} {historial}")
    
    # Equivalencias comerciales avanzadas
    equivalencias = {
        "chapopote": "vaportite asfalto desplantes cimentacion",
        "asfalto": "vaportite",
        "acrilico": "acriton fester a proshield",
        "techo": "losa azotea",
        "losa": "azotea",
        "terraza": "cr66",
        "vitropiso": "cr66",
        "salitre": "cr65 cr66",
    }
    
    for termino, reemplazo in equivalencias.items():
        if termino in consulta_limpia:
            consulta_limpia += f" {reemplazo}"
            consulta_codigo += re.sub(r'[^a-z0-9ñ]', '', reemplazo)

    palabras_consulta = [p for p in re.findall(r"[\wñ-]+", consulta_limpia) if len(p) > 2]
    
    resultados = []
    for item in base_conocimiento:
        texto_norm, texto_codigo = normalizar_cadena(item["texto"])
        nombre_norm, nombre_codigo = normalizar_cadena(item["origen"])
        
        puntos = 0
        # Validación estricta de códigos pegados (ej: busca cm202 en texto que tiene cm-202)
        for palabra in palabras_consulta:
            if palabra in texto_norm:
                puntos += 5
            if palabra in nombre_norm:
                puntos += 30  # Súper bono si la palabra coincide con el nombre del PDF
        
        # Validación por coincidencia de códigos compactos sin guiones
        if any(p in nombre_codigo for p in palabras_consulta) or (len(consulta_codigo) > 3 and consulta_codigo in texto_codigo):
            puntos += 50
            
        # Darle máxima prioridad a los textos redactados por ti en el mostrador
        if item["tipo"] == "txt_experto" and any(p in texto_norm for p in palabras_consulta):
            puntos += 80

        if puntos > 0:
            resultados.append((puntos, item))

    if resultados:
        resultados.sort(key=lambda x: x, reverse=True)
    
    return "".join(
        f"\n[Ficha/Manual: {item['origen']} - {item['referencia']}]\n{item['texto']}\n"
        for _, item in resultados[:2]
    )

def es_sondeo_inicial_azotea(texto, historial):
    texto = f"{historial} {texto}".lower()
    pide_rec = any(f in texto for f in ("que me recomiendas", "cual me recomiendas", "recomienda", "que aplico"))
    es_zona = any(p in texto for p in ("azotea", "techo", "losa", "terraza"))
    ya_respondio = any(p in historial.lower() for p in ("filtraciones", "preventivo", "superficie"))
    return pide_rec and es_zona and not ya_respondio

# 5. Ejecución del Chat
if prompt := st.chat_input("¿Qué problema tienes en obra o qué producto deseas validar?"):
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    prompt_lower = prompt.lower().strip()
    prompt_norm, prompt_cod = normalizar_cadena(prompt_lower)
    historial_texto = " ".join(message["content"] for message in st.session_state.messages[-4:]).lower()

    # Intercepción inmediata de saludos
    if re.search(r"\b(hola|holis|buen[oa]s?|saludos|qu[eé]\s+tal)\b", prompt_lower):
        guardar_respuesta("¡Hola! Soy tu amigo Asesor FesterParedes, a la orden. ¿En qué te puedo apoyar hoy?")
        st.stop()

    # REGLA DE APRENDIZAJE ACTIVO EN TIEMPO REAL: Verificar si ya guardaste la respuesta a esta duda exacta antes
    if prompt_cod in st.session_state.base_aprendizaje:
        guardar_respuesta(st.session_state.base_aprendizaje[prompt_cod])
        st.stop()

    if es_sondeo_inicial_azotea(prompt_lower, historial_texto):
        guardar_respuesta(
            "Con gusto te ayudo a elegir el sistema ideal. Antes de sugerirte un producto específico, "
            "compárteme: ¿ya cuentas con filtraciones activas o es un trabajo preventivo? También indícame: "
            "¿qué tipo de superficie tienes (concreto, impermeabilizante anterior)? y ¿qué durabilidad buscas?"
        )
        st.stop()

    if prompt_lower in ["acriton", "quiero acriton", "necesito acriton"]:
        guardar_respuesta(
            "Manejo tanto el **Fester Acriton Sellador** (primario acrílico para preparar la superficie) como la línea de "
            "**Impermeabilizantes Premium Fester Acriton Pro Shield Max** (con durabilidades de 4, 6, 8 y 12 años). ¿Cuál te interesa?"
        )
        st.stop()

    # Ejecución normal del buscador tolerante a códigos
    contexto_manuales = buscar_fichas(prompt, historial_texto)
    
    # Texto clave que indica que no hay información certera
    mensaje_no_info = "Lo siento, esa información exacta no viene completa en las fichas cargadas. Por favor comunícate con un especialista al **3317011786**."

    contexto_sistema = f"""
Eres el Asesor Técnico Senior de Fester México. Responde siempre de forma muy breve, clara y profesional (máximo 2 párrafos cortos).

REGLAS CRÍTICAS DE INGENIERÍA:
1. Si te consultan por CHAROLAS DE BAÑO o REGADERAS, el producto único e inalterable es FESTER CL-52 (Acrílico base agua). Queda estrictamente PROHIBIDO recomendar sistemas asfálticos solventes como Vaportite en interiores.
2. Si los datos del texto oficial de abajo vienen vacíos o no tienen relación directa con la duda o marcas consultadas, debes responder exactamente esta frase: {mensaje_no_info}
3. Entrega cálculos de botes o litros exactos basados únicamente en los consumos numéricos que exponga el texto de abajo.

TEXTO DE RESPALDO DE LAS FICHAS TÉCNICAS:
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
