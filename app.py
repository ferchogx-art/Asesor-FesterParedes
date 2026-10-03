import os
import re
import math
import streamlit as st
from groq import Groq

# Configuración inicial de la página en formato ancho
st.set_page_config(page_title="Asesor FesterParedes", page_icon="🏗️", layout="wide")
st.title("🏗️ Asesor Técnico FesterParedes IA")
st.write("Sistema maestro unificado. ¡Base de datos y calculadora en un solo lugar!")

# 1. Conectar con la API de Groq usando el modelo permanente y estable
api_key = os.environ.get("GROQ_API_KEY", st.secrets.get("GROQ_API_KEY", ""))
if not api_key:
    st.error("Falta configurar la clave GROQ_API_KEY en los Secrets de Streamlit.")
    st.stop()

client = Groq(api_key=api_key)
model_id = "llama-3.1-8b-instant"

# 2. Inicializar memorias de conversación y lecciones de la tienda
if "messages" not in st.session_state:
    st.session_state.messages = []
if "cerebro_tienda" not in st.session_state:
    st.session_state.cerebro_tienda = {}  
if "pregunta_pendiente" not in st.session_state:
    st.session_state.pregunta_pendiente = ""
if "mostrar_formulario" not in st.session_state:
    st.session_state.mostrar_formulario = False

# Limpiador de texto para buscar coincidencias exactas en la memoria manual
def normalizar_texto(texto):
    return re.sub(r'[^a-z0-9ñ]', '', texto.lower().strip())

# =========================================================================
# 🧮 CALCULADORA OFICIAL EN LA BARRA LATERAL IZQUIERDA
# =========================================================================
with st.sidebar:
    st.header("🧮 Calculadora de Materiales")
    st.write("Cálculos exactos basados en fichas técnicas oficiales.")
    
    # Selector de Producto
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
    
    # Lógica de Condiciones y Rendimientos Oficiales por Producto
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

    # Entrada de datos del usuario
    if presentacion in ["sacos_grout", "sacos_cm"]:
        volumen_litros = st.number_input("Volumen total a rellenar (en Litros):", min_value=1, value=15, step=1)
        material_total = volumen_litros * factor_rendimiento
    else:
        area_m2 = st.number_input("Área total a tratar (m²):", min_value=1, value=10, step=1)
        material_total = area_m2 * factor_rendimiento
        
    st.markdown("---")
    st.subheader(f"Total mínimo: {material_total:.2f} {tipo_unidad}")
    
    # Desglose de empaques comerciales
    if tipo_unidad == "L":
        cubetas = math.floor(material_total / 19)
        resto = material_total % 19
        botes = math.ceil(resto / 4)
        if botes >= 5:
            cubetas += 1
            botes = 0
        st.metric("Cubetas de 19 L necesarias:", f"{cubetas} Cubeta(s)")
        st.metric("Botes de 4 L necesarios:", f"{botes} Bote(s)")
        
    elif presentacion == "sacos":
        sacos = math.ceil(material_total / 25)
        st.metric("Sacos de 25 kg necesarios:", f"{sacos} Saco(s)")
        
    elif presentacion == "kits_cr66":
        kits = math.ceil(material_total / 35)
        st.metric("Kits de 35 kg necesarios (A+B):", f"{kits} Kit(s)")
        
    elif presentacion == "sacos_grout":
        sacos = math.ceil(material_total / 30)
        st.metric("Sacos de 30 kg necesarios:", f"{sacos} Saco(s)")
        
    elif presentacion == "sacos_cm":
        sacos = math.ceil(material_total / 25)
        st.metric("Sacos de 25 kg necesarios:", f"{sacos} Saco(s)")

    st.caption("⚠️ Valores teóricos mínimos de rendimiento. El consumo real variará según la porosidad de la superficie.")

# =========================================================================
# CENTRO DE LA PANTALLA: HISTORIAL DEL CHAT CON EL ASESOR
# =========================================================================
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Caja de Aprendizaje en Vivo (Aparece si falta información)
if st.session_state.mostrar_formulario:
    st.warning("🎓 Modo Aprendizaje Activo")
    st.info(f"Enséñame cómo responder a: *\"{st.session_state.pregunta_pendiente}\"*")
    with st.form(key="form_leccion_mostrador"):
        nueva_leccion = st.text_area("Escribe aquí la recomendación o resumen oficial de la tienda:")
        if st.form_submit_button("Guardar en la memoria de la IA"):
            if nueva_leccion.strip():
                clave_busqueda = normalizar_texto(st.session_state.pregunta_pendiente)
                st.session_state.cerebro_tienda[clave_busqueda] = nueva_leccion.strip()
                st.success("¡Lección guardada con éxito! Ya me la aprendí de memoria.")
                st.session_state.mostrar_formulario = False
                st.rerun()

# =========================================================================
# CENTRO DE LA PANTALLA: PROCESAMIENTO DE ENTRADA Y CONEXIÓN CON IA
# =========================================================================

if prompt := st.chat_input("¿Qué producto deseas consultar o qué problema tienes en obra?"):
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    prompt_normalizado = normalizar_texto(prompt)

    # 1. Buscar primero en la memoria de lecciones manuales
    respuesta_guardada = ""
    for clave_memoria, valor_memoria in st.session_state.cerebro_tienda.items():
        if clave_memoria in prompt_normalizado or prompt_normalizado in clave_memoria:
            respuesta_guardada = valor_memoria
            break

    if respuesta_guardada:
        with st.chat_message("assistant"):
            st.markdown(respuesta_guardada)
            st.session_state.messages.append({"role": "assistant", "content": respuesta_guardada})
            st.stop()

    # 2. Intercepción de saludos rápidos para ahorrar tokens
    if prompt_normalizado in ["hola", "buenosdias", "buenasnoches", "buenastardes", "saludos", "quetal", "holis"]:
        res_saludo = "¡Hola! Soy tu Asesor Técnico FesterParedes, a la orden. ¿En qué problema de obra te puedo ayudar hoy?"
        with st.chat_message("assistant"):
            st.markdown(res_saludo)
            st.session_state.messages.append({"role": "assistant", "content": res_saludo})
            st.stop()

    mensaje_auxilio = "Con la información que tengo no puedo darte una respuesta 100% precisa sobre esto. Te recomiendo comunicarte directamente con Fester Paredes al 3317011786 para que un especialista te asesore. ¡Con gusto te seguimos ayudando con cualquier otra duda!"

    # 3. Contexto resumido del Sistema (Fichas Técnicas compactadas para optimizar tokens)
    contexto_sistema = f"""
Eres 'Fester Paredes', asesor técnico experto en impermeabilización en Zapopan, Jalisco. Respondes en español, amable y profesional.
REGLA: Recomienda basándote SOLO en la base de conocimientos. Si no sabes, di exactamente: '{mensaje_auxilio}'.
PROTOCOLO: Antes de recomendar un producto, si el usuario es vago, pide detalles: Ubicación, Tipo de superficie (concreto, lámina), Humedad (salitre, gotera, filtración franca), si hay grietas o tránsito.

PRODUCTOS Y RENDIMIENTOS:
1. ACRIFLEX: Malla refuerzo integral/puntos críticos (losas, cisternas, esquinas). Rollo 1.10x100m (~100m²).
2. ACRITON GREEN-SHIELD 10 AÑOS: Acrílico ecológico reflectivo para techos/láminas. Requiere Acriton Sellador previo. No inmersión ni tráfico vehicular.
3. ACRITON RESANADOR: Para fisuras de hasta 5mm en concreto. Aplicar antes del impermeable.
4. ACRITON PROSHIELD MAX (4,6,8 años): Acrílico secado rápido (2 capas en una mañana). Losas/láminas.
5. ACRITON SELLADOR: Primario acrílico. Rendimiento: 5 m²/L directo en techos; diluido 1:1 en muros.
6. FESTER A (A3,A5,A5 Fibratado,A7): Acrílicos de 3, 5 o 7 años. A5 Fibratado rellena fisuras pequeñas.
7. CF-890: Anclaje químico poliéster en cartucho (300mL) para varillas/pernos. Catalizado rápido. Superficie seca.
8. CF-1000: Anclaje químico epóxico estructural de alto desempeño (585mL). Funciona en concreto húmedo.
9. CL-52: Impermeabilizante interno para BAÑOS, cocinas, saunas, antes de pegar azulejo. No usar en techos expuestos. Rendimiento: 1 L/m² a 2 capas.
10. CM-200: Mortero reparador no estructural (0.5 a 10cm). Saco 25kg + 4L agua = 14L mezcla. Resiste inmersión.
11. CM-201: Mortero estructural/no estructural de ALTA resistencia. Fraguado rápido (1 hora). Saco 25kg = 14L mezcla.
12. CM-202: Mortero FLUIDO estructural para encofrados/cimbras angostas. Fraguado en 1 hora. Saco 25kg = 14L mezcla.
13. CR-65: Cementoso para SALITRE y humedad ascendente en muros interiores/cimentaciones. Permite transpirar. No usar en techos. Rendimiento: subsuelo 3kg/m², lluvia 4kg/m², tanques 5kg/m² (a 2-3 capas). Saco 25kg.
14. CR-66 FIBRE FORCE: Cementoso flexible 2 componentes (A+B) para cisternas, albercas, baños o terrazas con piso encima. Puentea grietas 4mm. Rendimiento: cimentación/baños 2kg/m², albercas 3kg/m². Kit de 35kg.
15. CR-NANOTECH 99+: Polvo para concreto existente bajo presiones hidrostáticas severas (cisternas, albercas). No techos. Rendimiento: 1.5 kg/m² total (2 capas). Saco 24kg.
16. CR-NANOTECH ADMIX: Aditivo en polvo para mezclar durante la fabricación del concreto nuevo. Dosificación: 2% sobre el peso del cemento (1kg por bulto de 50kg).
17. CX-01: Mortero fraguado instantáneo (1 min) para taponar fugas y chorros de agua activos bajo presión.
18. EPOXINE 200: Adhesivo epóxico estructural para unir concreto nuevo a viejo. Rendimiento: 3 a 3.5 m²/L.
19. EPOXINE 800 GROUT: Mortero epóxico industrial de 3 componentes para anclaje de maquinaria pesada (>100L).
20. FESTERBOND: Adhesivo acrílico multiusos. Fortificador de morteros, adherente viejo-nuevo y sellador poroso.
21. FESTERFLEX: Malla no tejida de refuerzo para sistemas asfálticos en frío.
22. FESTEGRAL: Aditivo integral en polvo para reducir permeabilidad en concretos.

COMPRAS Y TIENDA FÍSICA:
Fester Paredes es distribuidor autorizado. Opciones de venta:
- Directo por WhatsApp al 3317011786.
- Tienda física: Av. Juan Gil Preciado #2001 Int. 8, Plaza Aleira, Zapopan.
- Redes: @festerparedes en Facebook/Instagram.
Siempre que remitas a contacto usa: 'te recomiendo comunicarte directamente con Fester Paredes al 3317011786'.
"""

    with st.chat_message("assistant"):
        try:
            # Enviamos el contexto del sistema + SOLO los últimos 6 mensajes del chat
            historial_optimizado = (
                [{"role": "system", "content": contexto_sistema}] + 
                st.session_state.messages[-6:]
            )

            # NUEVO MODELO ACTIVO: Cambiado a llama-3.1-8b-instant para solucionar el error 400
            completion = client.chat.completions.create(
                model="llama-3.1-8b-instant",  # Reemplazo oficial vigente en Groq
                messages=historial_optimizado,
                temperature=0.0,
                max_tokens=800
            )
            
            # Extracción segura de la respuesta de texto plano
            if hasattr(completion, 'choices') and len(completion.choices) > 0:
                choice_obj = completion.choices[0] # Se corrigió a [0] para evitar errores de tipo lista
                if hasattr(choice_obj, 'message') and hasattr(choice_obj.message, 'content'):
                    response = choice_obj.message.content
                elif isinstance(choice_obj, dict) and 'message' in choice_obj:
                    response = choice_obj['message']['content']
                else:
                    response = str(choice_obj)
            else:
                response = str(completion)

            # Lógica de detección de auxilio o aprendizaje en mostrador
            if "3317011786" in response or "no puedo darte una respuesta" in response:
                st.session_state.pregunta_pendiente = prompt
                st.session_state.mostrar_formulario = True
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
                st.rerun()
            else:
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
                
        except Exception as error:
            st.error(f"Error de conexión con el servidor de IA: {error}")
