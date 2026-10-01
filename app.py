import os
import re
import math
import streamlit as st
from groq import Groq

# Configuración inicial de la página
st.set_page_config(page_title="Asesor FesterParedes", page_icon="🏗️", layout="wide")
st.title("🏗️ Asesor Técnico FesterParedes IA")
st.write("Sistema unificado. ¡Base de datos y calculadora en un solo lugar!")

# 1. Conectar con la API de Groq
api_key = os.environ.get("GROQ_API_KEY", st.secrets.get("GROQ_API_KEY", ""))
if not api_key:
    st.error("Falta configurar la clave GROQ_API_KEY en los Secrets de Streamlit.")
    st.stop()

client = Groq(api_key=api_key)
model_id = "llama-3.1-8b-instant"


# 2. Inicializar memorias de conversación
if "messages" not in st.session_state:
    st.session_state.messages = []
if "cerebro_tienda" not in st.session_state:
    st.session_state.cerebro_tienda = {}  
if "pregunta_pendiente" not in st.session_state:
    st.session_state.pregunta_pendiente = ""
if "mostrar_formulario" not in st.session_state:
    st.session_state.mostrar_formulario = False

def normalizar_texto(texto):
    return re.sub(r'[^a-z0-9ñ]', '', texto.lower().strip())

# =========================================================================
# 🧮 CALCULADORA - PRIMERA MITAD DE PRODUCTOS
# =========================================================================
with st.sidebar:
    st.header("🧮 Calculadora de Materiales")
    st.write("Cálculos exactos basados en fichas técnicas.")
    
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

# Procesamiento de la entrada del usuario en el chat central
if prompt := st.chat_input("¿Qué producto deseas consultar o qué problema tienes en obra?"):
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    prompt_normalizado = normalizar_texto(prompt)

    # Buscar primero en la memoria de lecciones manuales
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

    # Intercepción de saludos
    if prompt_normalizado in ["hola", "buenosdias", "buenasnoches", "buenastardes", "saludos", "quetal", "holis"]:
        res_saludo = "¡Hola! Soy tu Asesor Técnico FesterParedes, a la orden. ¿En qué problema de obra te puedo ayudar hoy?"
        with st.chat_message("assistant"):
            st.markdown(res_saludo)
            st.session_state.messages.append({"role": "assistant", "content": res_saludo})
            st.stop()

    mensaje_auxilio = "Con la información que tengo no puedo darte una respuesta 100% precisa sobre esto. Te recomiendo comunicarte directamente con Fester Paredes al 3317011786 para que un especialista te asesore. ¡Con gusto te seguimos ayudando con cualquier otra duda!"

    contexto_sistema = f"""
Eres 'Fester Paredes', el asesor técnico virtual experto de Fester. Respondes en español, con un tono profesional, claro y preventivo.

=== REGLAS DE SEGURIDAD INDUSTRIAL (ESTRICTAS) ===
1. CHAROLAS DE BAÑO Y ÁREAS INTERIORES: Queda ESTRICTAMENTE PROHIBIDO recomendar productos base solvente o asfálticos (como Vaportite 550 o Hidroprimer) para baños, regaderas o cocinas. Para charolas de baño que llevarán azulejo/acabado encima, los ÚNICOS productos certificados son FESTER CL-52 (interiores residenciales) o FESTER CR-66 FIBRE FORCE.
2. GOTERAS Y AZOTEAS EXPUESTAS: NUNCA recomiendes cementosos (CR-65, CR-66, Nanotech) ni CL-52 en techos o azoteas que queden expuestas al sol. Ahí van únicamente acrílicos (Línea Acriton o Fester A).
3. MEZCLAS DE PRODUCTOS: Prohíbe al usuario mezclar impermeabilizantes acrílicos con asfálticos en el mismo sistema.

=== BASE DE CONOCIMIENTO CERTIFICADA (PARTE 1) ===
• FESTER CL-52: Impermeabilizante elástico base agua de aplicación en frío. Diseñado EXCLUSIVAMENTE para interiores (charolas de baño, regaderas, cocinas) ANTES de la colocación de azulejo, porcelanato o recubrimientos cerámicos. No genera gases tóxicos. Rendimiento: 1 a 1.2 L/m² a dos capas.
• FESTER CR-66 FIBRE FORCE: Cementoso super flexible de 2 componentes (Kit 35kg). Ideal para cisternas, albercas y también charolas de baño de uso rudo. Soporta movimiento del subsuelo. Rendimiento: 4 kg/m² en baños y muros de block.
• FESTER CR-65: Cementoso rígido en polvo (Saco 25kg). Específico para contrarrestar SALITRE y humedad ascendente en muros de block, tabique o concreto. Se aplica directo al sustrato原 (retirando todo el aplanado dañado). Rendimiento: 3 a 4 kg/m². NUNCA se usa en techos.
• FESTER ACRITON PROSHIELD MAX: Impermeabilizante acrílico base agua de secado ultra rápido (resiste lluvia 30 min después de aplicado). Solo para azoteas, losas de concreto y techos de lámina expuestos. Rendimiento: 1 L/m² a dos capas sin malla.
=== BASE DE CONOCIMIENTO DE PRODUCTOS (ESTRICTA) ===
1. FESTER CL-52: Impermeabilizante elástico base agua para áreas húmedas interiores ANTES de colocar azulejo (baños, regaderas, cocinas). NUNCA usar en exteriores expuestos al sol, ni combinar con asfálticos. Permite la adhesión directa de pegazulejo.
2. FESTER CR-66 FIBRE FORCE: Cementoso elástico de 2 componentes (Kit 35 kg). Ideal para cisternas, albercas y charolas de baño. Soporta movimiento y presiones de agua constantes.
3. FESTER CR-65: Cementoso rígido para tratamiento de salitre y humedad ascendente en muros de block o tabique. Requiere retirar el aplanado/yeso y aplicar directo a la estructura. NUNCA usar en techos.
4. FESTER ACRITON PROSHIELD MAX / GREEN-SHIELD: Impermeabilizantes acrílicos para azoteas y techos expuestos. Secado rápido. Prohibidos en interiores o bajo inmersión (cisternas/albercas).
5. FESTER VAPORTITE 550 e HIDROPRIMER: Sistema asfáltico base solvente de uso EXTERIOR (cimentaciones, barreras de vapor en muros colindantes). PROHIBIDO su uso en baños o espacios cerrados debido a la alta toxicidad de sus gases y porque impiden la adherencia de acabados cerámicos (el azulejo se caería).
6. FESTERBOND: Adhesivo acrílico multiusos. SÍ se mezcla como fortificador SOLO en mezclas tradicionales hechas en obra (arena, agua, cemento). NUNCA mezclar dentro de morteros reparadores listos (Línea CM) ni Grouts.

=== GUÍA RÁPIDA DE DIAGNÓSTICO POR ESCENARIO ===
- ¿Charola de baño / Regadera interior? -> Sistema Fester CL-52 (2 capas) o CR-66 Fibre Force. Exigir preparación con resanador acrílico si hay grietas estáticas. Prohibir asfálticos.
- ¿Salitre en muros interiores/exteriores? -> Fester CR-65 directo al block desnudo.
- ¿Goteras en azotea o losa expuesta? -> Sistema Acrílico (Sellador + Acriton o Fester A).
- ¿Cisternas o albercas de concreto? -> Fester CX-01 (si hay fuga activa) seguido de Fester CR-66 o CR-Nanotech 99+.
    with st.chat_message("assistant"):
        try:
            # Juntamos el sistema con todo el historial acumulado de forma limpia
            historial_completo = [{"role": "system", "content": contexto_sistema}] + st.session_state.messages

            completion = client.chat.completions.create(
                model="openai/gpt-oss-120b",
                messages=historial_completo,
                temperature=0.0,
                max_tokens=1000
            )
            response = completion.choices.message.content
            
            # Ajuste de seguridad para el extractor de respuestas
            if hasattr(completion, 'choices') and len(completion.choices) > 0:
                choice = completion.choices[0]
                if hasattr(choice, 'message'):
                    response = choice.message.content
                else:
                    response = choice['message']['content'] if 'message' in choice else str(choice)
            else:
                response = completion['choices'][0]['message']['content']

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
