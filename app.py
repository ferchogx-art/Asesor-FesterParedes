import os
import re
import math
import streamlit as st
from groq import Groq

# Configuración inicial de la página en formato ancho
st.set_page_config(page_title="Asesor FesterParedes", page_icon="🏗️", layout="wide")

st.image("https://cdninstagram.com", width=250)
st.title("🏗️ Asesor Técnico FesterParedes IA")
st.write("Sistema maestro unificado. ¡Base de datos y calculadora en un solo lugar!")

# 1. Conectar con la API de Groq respetando tu modelo original
api_key = os.environ.get("GROQ_API_KEY", st.secrets.get("GROQ_API_KEY", ""))
if not api_key:
    st.error("Falta configurar la clave GROQ_API_KEY en los Secrets de Streamlit.")
    st.stop()

client = Groq(api_key=api_key)
model_id = "openai/gpt-oss-20b"  # Tu modelo de confianza se queda intacto

# 2. Inicializar memorias de conversación y estados
if "messages" not in st.session_state:
    # Agregamos un prompt de sistema inicial invisible para que la IA actúe como experto
    st.session_state.messages = [
        {"role": "system", "content": "Eres un asesor técnico experto de Fester. Ayudas a ingenieros y arquitectos con especificaciones, dosificaciones y sistemas de impermeabilización. Tus respuestas deben ser profesionales, precisas y concisas. Si te preguntan por consumos, refiérelos a los cálculos exactos de la barra lateral."}
    ]

def normalizar_texto(texto):
    return re.sub(r'[^a-z0-9ñ]', '', texto.lower().strip())

# =========================================================================
# 🧮 CALCULADORA OFICIAL CON FACTOR DE SEGURIDAD (BARRA LATERAL)
# =========================================================================
with st.sidebar:
    st.header("🧮 Calculadora de Materiales")
    st.write("Cálculos exactos basados en fichas técnicas oficiales.")
    
    # MEJORA 1: Factor de desperdicio indispensable en ingeniería civil
    desperdicio_sel = st.selectbox(
        "Factor de Desperdicio (Mermas / Porosidad):",
        ["Sin desperdicio (Teórico)", "+5% Margen seguro", "+10% Superficie rugosa/porosa"],
        index=1
    )
    margen_map = {"Sin desperdicio (Teórico)": 1.0, "+5% Margen seguro": 1.05, "+10% Superficie rugosa/porosa": 1.10}
    mult_desperdicio = margen_map[desperdicio_sel]

    producto_sel = st.selectbox(
        "Selecciona el Producto:",
        [
            "Fester Acriton Green-Shield 10 años",
            "Fester Acriton Proshield Max",
            "Fester A (A3 / A5 / A7)",
            "Fester Acriton Sellador",
            "Fester CR-65",
            "Fester CR-66 Fibre Force",
            "Festerbond",
            "Festergrout (NM 400 / 600 / 800)",
            "Fester Vaportite 550",
            "Fester Hidroprimer",
            "Fester CM-200",
            "Fester CM-201",
            "Fester CM-202"
        ]
    )
    
    factor_rendimiento = 1.0
    tipo_unidad = "L"
    presentacion = "cubetas"
    
    if "Green-Shield" in producto_sel:
        cond = st.selectbox("Condición:", ["Sin malla", "Con malla Revoflex", "Con malla Acriflex"])
        rend = {"Sin malla": 1.0, "Con malla Revoflex": 1.2, "Con malla Acriflex": 1.5}
        factor_rendimiento = rend[cond]
        
    elif "Proshield Max" in producto_sel:
        cond = st.selectbox("Condición:", ["Normal o lámina", "Con fisuras sin malla", "Con malla Revoflex", "Con malla Acriflex", "Mantenimiento"])
        rend = {"Normal o lámina": 1.0, "Con fisuras sin malla": 1.5, "Con malla Revoflex": 1.2, "Con malla Acriflex": 1.5, "Mantenimiento": 0.65}
        factor_rendimiento = rend[cond]
        
    elif "Fester A " in producto_sel:
        cond = st.selectbox("Condición:", ["Superficie normal", "Con malla de refuerzo"])
        factor_rendimiento = 1.0 if cond == "Superficie normal" else 1.5
        
    elif "Acriton Sellador" in producto_sel:
        st.info("Rendimiento fijo: 5 m² por litro (1 mano sin diluir)")
        factor_rendimiento = 0.20
        
    elif "CR-65" in producto_sel:
        cond = st.selectbox("Aplicación:", ["Humedad subsuelo (2 capas)", "Agua de lluvia (2 capas)", "Tanques de agua (3 capas)"])
        rend = {"Humedad subsuelo (2 capas)": 3.0, "Agua de lluvia (2 capas)": 4.0, "Tanques de agua (3 capas)": 5.0}
        factor_rendimiento = rend[cond]
        tipo_unidad = "kg"
        presentacion = "sacos"
        
    elif "CR-66" in producto_sel:
        cond = st.selectbox(
            "Aplicación:", 
            [
                "Muros de cimentación (3.5 kg/m²)", 
                "Charolas de baño y cocinas (4 kg/m²)", 
                "Muros de tabique, block o yeso (4 kg/m²)", 
                "Albercas, cisternas y tanques (5 kg/m²)", 
                "Balcones y terrazas (5 kg/m²)"
            ]
        )
        rend = {
            "Muros de cimentación (3.5 kg/m²)": 3.5, 
            "Charolas de baño y cocinas (4 kg/m²)": 4.0, 
            "Muros de tabique, block o yeso (4 kg/m²)": 4.0, 
            "Albercas, cisternas y tanques (5 kg/m²)": 5.0, 
            "Balcones y terrazas (5 kg/m²)": 5.0
        }
        factor_rendimiento = rend[cond]
        tipo_unidad = "kg"
        presentacion = "kits_cr66"
        
    elif "Festerbond" in producto_sel:
        cond = st.selectbox("Uso como adherente:", ["Superficial puro", "Lechada / Fortificador tradicional"])
        factor_rendimiento = 0.18 if cond == "Superficial puro" else 0.20
        
    elif "Festergrout" in producto_sel:
        st.info("Grout cementoso sin contracción estructural.")
        factor_rendimiento = 1.92
        tipo_unidad = "kg"
        presentacion = "sacos_grout"
        
    elif "Vaportite" in producto_sel:
        cond = st.selectbox("Aplicación asfáltica:", ["Capa sola en losa (por capa)", "Sistema multicapa con malla (total)"])
        factor_rendimiento = 1.0 if cond == "Capa sola en losa (por capa)" else 2.0
        
    elif "Hidroprimer" in producto_sel:
        st.info("Primario asfáltico base solvente.")
        factor_rendimiento = 0.20
        
    elif "CM-200" in producto_sel or "CM-201" in producto_sel or "CM-202" in producto_sel:
        st.info("Morteros reparadores volumétricos. Se calcula por litros de mezcla requerida.")
        factor_rendimiento = 1.80
        tipo_unidad = "kg"
        presentacion = "sacos_cm"

    if presentacion in ["sacos_grout", "sacos_cm"]:
        volumen_litros = st.number_input("Volumen total a rellenar (en Litros):", min_value=1, value=15, step=1)
        material_total = volumen_litros * factor_rendimiento * mult_desperdicio
    else:
        area_m2 = st.number_input("Área total a tratar (m²):", min_value=1, value=10, step=1)
        material_total = area_m2 * factor_rendimiento * mult_desperdicio
        
    st.markdown("---")
    st.subheader(f"Total estimado: {material_total:.2f} {tipo_unidad}")
    
    # Almacenamos el resultado en texto para pasárselo a la IA si lo requiere
    calculo_actual_str = f"Cálculo actual en panel lateral: Producto {producto_sel}, Total requerido mínimo: {material_total:.2f} {tipo_unidad}."

    if tipo_unidad == "L":
        cubetas = math.floor(material_total / 19)
        resto = material_total % 19
        botes = math.ceil(resto / 4)
        if botes >= 5:
            cubetas += 1
            botes = 0
        st.metric("Cubetas de 19 L necesarias:", f"{cubetas} Cubeta(s)")
        st.metric("Botes de 4 L necesarios:", f"{botes} Bote(s)")
        calculo_actual_str += f" Equivalente a {cubetas} cubetas de 19L y {botes} botes de 4L."
        
    elif presentacion == "sacos":
        sacos = math.ceil(material_total / 25)
        st.metric("Sacos de 25 kg necesarios:", f"{sacos} Saco(s)")
        calculo_actual_str += f" Equivalente a {sacos} sacos de 25kg."
        
    elif presentacion == "kits_cr66":
        kits = math.ceil(material_total / 35)
        st.metric("Kits de 35 kg necesarios (A+B):", f"{kits} Kit(s)")
        calculo_actual_str += f" Equivalente a {kits} kits de 35kg."
        
    elif presentacion == "sacos_grout":
        sacos = math.ceil(material_total / 30)
        st.metric("Sacos de 30 kg necesarios:", f"{sacos} Saco(s)")
        calculo_actual_str += f" Equivalente a {sacos} sacos de 30kg."
        
    elif presentacion == "sacos_cm":
        sacos = math.ceil(material_total / 25)
        st.metric("Sacos de 25 kg necesarios:", f"{sacos} Saco(s)")
        calculo_actual_str += f" Equivalente a {sacos} sacos de 25kg."

# =========================================================================
# 💬 CENTRO DE LA PANTALLA: HISTORIAL DEL CHAT CON INTERACCIÓN REAL
# =========================================================================

# Renderizar el historial de la sesión (ocultando el prompt del sistema)
for message in st.session_state.messages:
    if message["role"] != "system":
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

# Capturar la entrada del usuario
prompt = st.chat_input("Pregúntame sobre fichas técnicas, preparación de superficie o solicita un cálculo...")

if prompt:
    # Mostrar el mensaje del usuario en pantalla
    with st.chat_message("user"):
        st.markdown(prompt)
    
        # Guardamos el mensaje del usuario en el historial
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # REESTRUCTURACIÓN: Forzamos las instrucciones del sistema en cada llamada
    instrucciones_sistema = (
        "Eres el Asesor Técnico Experto Oficial de FesterParedes. Tu propósito es guiar de forma "
        "estricta y profesional a ingenieros, arquitectos y aplicadores utilizando únicamente "
        "especificaciones, dosificaciones y normativas técnicas de los productos Fester. "
        "Bajo ninguna circunstancia debes decir que eres un modelo genérico de OpenAI o Groq; "
        "tú eres un sistema maestro unificado de Fester. Sé preciso, conciso y técnico en tus respuestas."
    )
    
    # Creamos la lista de mensajes combinando la identidad con el historial acumulado
    mensajes_para_api = [{"role": "system", "content": instrucciones_sistema}]
    
    # Añadimos el historial que se lleva en la sesión (limpiando posibles residuos previos)
    for msg in st.session_state.messages:
        if msg["role"] != "system":
            mensajes_para_api.append(msg)
    
    # Inyección dinámica de la calculadora lateral
    texto_busqueda = prompt.lower().strip()
    palabras_clave = ["cuanto", "necesito", "calcula", "rendimiento", "material", "cubetas", "sacos"]
    
    if any(k in texto_busqueda for k in palabras_clave):
        mensajes_para_api.append({
            "role": "system", 
            "content": f"El usuario está solicitando datos volumétricos o rendimientos en obra. Información de referencia exacta de la calculadora lateral activa: {calculo_actual_str}"
        })


    # Llamada a la API de Groq conservando tu modelo original
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        
        try:
            completion = client.chat.completions.create(
                model=model_id,
                messages=mensajes_para_api,
                stream=False
            )
            
            full_response = completion.choices[0].message.content
            message_placeholder.markdown(full_response)
            
            # Guardamos la respuesta del asistente en el historial global
            st.session_state.messages.append({"role": "assistant", "content": full_response})
            
        except Exception as e:
            st.error(f"Error al conectar con Groq: {e}")
