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
model_id = "openai/gpt-oss-20b"  # El modelo de tu código original (Activo en Groq)

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
        material_total = volumen_litros * factor_rendimiento
    else:
        area_m2 = st.number_input("Área total a tratar (m²):", min_value=1, value=10, step=1)
        material_total = area_m2 * factor_rendimiento
        
    st.markdown("---")
    st.subheader(f"Total mínimo: {material_total:.2f} {tipo_unidad}")
    
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

    if prompt_normalizado in ["hola", "buenosdias", "buenasnoches", "buenastardes", "saludos", "quetal", "holis"]:
        res_saludo = "¡Hola! Soy tu Asesor Técnico FesterParedes, a la orden. ¿En qué problema de obra te puedo ayudar hoy?"
        with st.chat_message("assistant"):
            st.markdown(res_saludo)
            st.session_state.messages.append({"role": "assistant", "content": res_saludo})
            st.stop()

    mensaje_auxilio = "Con la información que tengo no puedo darte una respuesta 100% precisa sobre esto. Te recomiendo comunicarte directamente con Fester Paredes al 3317011786 para que un especialista te asesore. ¡Con gusto te seguimos ayudando con cualquier otra duda!"

    # === INSTRUCCIONES OPTIMIZADAS CONTRA BUCLES Y SATURACIÓN ===
    contexto_sistema = f"""
    
Eres 'Fester Paredes', asesor técnico experto en impermeabilización en Zapopan, Jalisco. Respondes en español, de forma amable, cercana y profesional.
REGLA DE ORO: Recomienda basándote SOLO en la base de conocimientos adjunta. Si no sabes la respuesta o es un caso fuera del catálogo, di textualmente: '{mensaje_auxilio}'.

=== PROTOCOLO DE SONDEO NATURAL (EVITAR BUCLES) ===
- Si el usuario te da una respuesta corta o parcial (por ejemplo: 'es de ladrillo' o 'es una azotea'), NO le vuelvas a repetir toda la lista completa de preguntas de sondeo. 
- Toma el dato que ya te dio (ej. superficie de ladrillo) y haz una sola pregunta de seguimiento amigable para avanzar en la conversación (ej. '¡Perfecto! Al ser de ladrillo de azotea, ¿tienes goteras activas o solo buscas proteger por prevención?').
- Avanza con el diagnóstico usando máximo 1 o 2 preguntas breves por mensaje. Nunca inundes al usuario con el mismo cuestionario de forma robótica.
- Una vez que tengas una idea clara de la superficie y la necesidad, ofrece la solución técnica ideal explicando brevemente los pasos (Limpieza -> Sellador/Primario -> Impermeabilizante) y sus rendimientos oficiales.



PRODUCTOS, RENDIMIENTOS Y RESTRICCIONES CRÍTICAS:
1. ACRIFLEX: Malla de poliéster tejido para puntos críticos o refuerzo integral acrílico/asfáltico. Rollo 1.10x100m (~100m²). NO usar en sistemas asfálticos en caliente.
2. ACRITON GREEN-SHIELD 10 AÑOS: Acrílico ecológico reflectivo para techos sin tránsito peatonal ni vehicular. RENDIMIENTO: 1.0 Litro/m² a 2 capas (sin malla). REGLA: Requiere Acriton Sellador previo. NO diluir con agua, NO aplicar sobre superficies mojadas ni donde haya encharcamientos constantes.
3. ACRITON RESANADOR: Pasta lista para usar para sellar fisuras hasta 5mm en concreto previo al impermeabilizante. REGLA: Requiere imprimación con Acriton Sellador en la grieta. NO diluir, NO usar en juntas estructurales con movimiento severo.
4. ACRITON PROSHIELD MAX (4, 6 y 8 años): Acrílico de secado rápido (2 capas en una mañana). RENDIMIENTO: 1.0 Litro/m² a 2 capas en losa normal; 0.65 L/m² para mantenimiento. REGLA: Requiere Acriton Sellador previo. NO diluir con agua, NO usar en inmersión continua ni tráfico vehicular.
5. ACRITON SELLADOR: Primario acrílico. RENDIMIENTO: Fijar en 5 m² por Litro (0.20 L/m²). REGLA: Aplicar SIN DILUIR en techos; diluido 1:1 con agua limpia únicamente si se usa en muros o fachadas exteriores.
6. FESTER A (A3, A5, A5 Fibratado, A7): Acrílicos tradicionales. RENDIMIENTO: 1.0 Litro/m² a 2 capas en superficie normal; 1.5 Litros/m² si se instala con malla de refuerzo integral. REGLA: Requiere sellador previo. NO aplicar a menos de 5°C ni sobre charcos.
7. CF-890: Anclaje químico de poliéster (300mL) para varillas y pernos. REGLA: Mezclado automático con su boquilla. NO requiere primario. NO aplicar en perforaciones húmedas ni bajo el sol directo durante la inyección.
8. CF-1000: Anclaje químico epóxico estructural (585mL). REGLA: Mezclado automático por boquilla. SÍ tiene alta adherencia en concreto húmedo o seco. NO diluir ni alterar la mezcla.
9. FESTER CL-52: Membrana impermeable elástica monocomponente de secado extra rápido. SUGERENCIA DE APLICACIÓN: Diseñado específicamente para interiores ANTES de colocar azulejos o acabados cerámicos en charolas de baño, regaderas, cocinas, cuartos de lavado, saunas, zonas húmedas y terrazas/balcones pequeños (máx. 25 m² con malla Acriflex). RENDIMIENTO: Primario diluido 1:2 con agua = 4 a 5 m²/L; capas puras = 0.5 L/m² por capa (1.0 L/m² total a 2 capas); en zonas muy agrietadas con malla integral rinde de 1.3 a 1.5 L/m² total. REGLA: Se aplica directo. NO dejar expuesto permanentemente a la intemperie, NO usar en losas de azotea exteriores ni techos de lámina expuestos.
10. CM-200: Mortero cementoso para resanes cosméticos no estructurales (0.5 a 10cm de espeso). RENDIMIENTO: Saco de 25kg + 4L de agua rinde 14L de mezcla (Factor: 1.80 kg por litro de relleno). SÍ resiste inmersión. NO requiere primario.
11. CM-201: Mortero estructural de reparación vertical/horizontal de ALTA resistencia. RENDIMIENTO: Saco de 25kg + 4L de agua rinde 14L de mezcla. REGLA: Fraguado rápido, transitable en 1 hora. NO mezclar con cemento o arena; usar solo agua limpia.
12. CM-202: Mortero FLUIDO estructural de alta resistencia para colar en cimbras/encofrados angostas. RENDIMIENTO: Saco de 25kg + 4L de agua rinde 14L de mezcla. REGLA: Autonivelante, transitable en 1 hora. NO usar como aplanado vertical debido a su alta fluidez.
13. CR-65: Cementoso rígido contra SALITRE y humedad ascendente en muros de block o tabique (aplicar directo al muro sin aplanado). RENDIMIENTO: Humedad subsuelo 3 kg/m² (2 capas); agua de lluvia 4 kg/m² (2 capas); cisternas/tanques 5 kg/m² (3 capas). REGLA: Saco de 25kg con 6 a 6.5L de agua limpia. NO aplicar en losas de techo ni sobre grietas dinámicas.
14. FESTER CR-66 FIBRE FORCE: Cementoso flexible de 2 componentes (Polvo A + Líquido B) para cisternas, albercas, charolas de baño o terrazas que llevarán piso encima. Puentea grietas de hasta 4mm. RENDIMIENTO: Cimentación y baños 2.0 kg/m² (2 capas); terrazas o depósitos de agua 2.5 a 3.0 kg/m² (2 a 3 capas). REGLA DE ORO PARA TERRAZAS: Se puede aplicar de forma continua en áreas menores a 25 m²; si la terraza es MAYOR a 25 m², es obligatorio generar juntas de dilatación/movimiento perimetrales e intermedias y sellarlas con Fester Superseal P o Fester FT-201. NO agregar agua bajo ninguna circunstancia, NO dejar expuesto a la intemperie sin acabado pétreo (piso) encima.
15. CR-NANOTECH 99+: Cementoso por cristalización para concreto existente bajo presiones hidrostáticas severas (cisternas subterráneas). RENDIMIENTO: 0.75 kg por capa (1.5 kg/m² total a 2 capas). REGLA: Mezclar solo con agua limpia. NO aplicar en losas de techo, ladrillos o mampostería (solo funciona en concreto puro).
16. CR-NANOTECH ADMIX: Aditivo en polvo que se integra DIRECTO en la olla/revolvedora durante el mezclado del concreto nuevo para impermeabilizarlo desde su fabricación. DOSIFICACIÓN: 2% sobre el peso del cemento (1 kg por cada bulto de cemento de 50 kg). NO usar en concretos ya endurecidos.
17. CX-01: Mortero cementoso de fraguado instantáneo (1 minuto) para taponar fugas francas, chorros y filtraciones activas de agua a presión. RENDIMIENTO: 1 kg llena 680 cm³ de grieta profunda. REGLA: Mezclar cantidades pequeñas solo con las manos (usar guantes) y agua limpia. APLICAR INMEDIATAMENTE presionando firmemente.
18. EPOXINE 200: Adhesivo epóxico de 2 componentes (A+B) para unir concreto nuevo a viejo en juntas de colado estructurales. RENDIMIENTO: 3 a 3.5 m² por Litro de mezcla. REGLA: Mezclar componentes A y B completos. NO es un impermeabilizante para filtraciones, NO aplicar si el concreto viejo tiene polvo o grasa.
19. EPOXINE 800 GROUT: Mortero epóxico industrial de 3 componentes (A+B+C) para anclaje de maquinaria pesada (>100L). RENDIMIENTO: La unidad de 112 kg llena exactamente 52 Litros de volumen (Factor: 2.15 kg por litro de relleno). NO mezclar con agua.
20. FESTERBOND: Adhesivo acrílico multiusos. RENDIMIENTO como sellador poroso: 4 a 5 m²/L (diluido 1:1 con agua). REGLA: Úsalo como fortificador en morteros (reemplazando parte del agua de mezcla) o como lechada adherente. NO tiene propiedades estructurales para trabes o columnas.
21. FESTERFLEX: Membrana de refuerzo no tejida de filamentos sintéticos. REGLA: Específica para sistemas impermeables ASFÁLTICOS aplicados en frío. NO usar en sistemas acrílicos ni en caliente.
22. FESTEGRAL: Aditivo integral en polvo para reducir la permeabilidad y absorción de agua en mezclas de concreto y mortero tradicional. DOSIFICACIÓN: 2% sobre el peso del cemento (1 kg por bulto de 50 kg). REGLA: Mezclar en seco con el cemento y la arena antes de agregar el agua.
23. FESTER VAPORTITE 550: Impermeabilizante asfáltico base solvente de consistencia pastosa para sistemas multicapa en frío (barrera de vapor extrema). RENDIMIENTO: 1.0 Litro/m² por capa sola en losa; 2.0 Litros/m² en sistema multicapa con malla de refuerzo. REGLA: Altamente inflamable y tóxico en espacios cerrados. NO diluir con agua ni solventes, NO aplicar sobre superficies húmedas o mojadas. Requiere primario asfáltico previo (Fester Hidroprimer).
24. FESTER HIDROPRIMER: Primario asfáltico base solvente de baja viscosidad diseñado para sellar la porosidad del concreto antes de aplicar sistemas asfálticos (Vaportite 550 o mantos prefabricados). RENDIMIENTO: 3 a 5 m² por Litro dependiendo de la porosidad (0.20 a 0.33 L/m²). REGLA: Aplicar SIN DILUIR. Altamente inflamable. NO aplicar sobre concreto mojado.
25. FESTERMIP (Sistemas Prefabricados APP / SBS): Mantos impermeables prefabricados en rollo (acabado Liso o Gravilla roja/blanca, espesores de 3.5mm o 4.0mm). REGLA: Se aplican por termofusión utilizando soplete de gas. RENDIMIENTO: Un rollo estándar de 1m x 10m cubre exactamente 9.0 m² netos debido al traslape obligatorio de 10 cm entre rollos. Requiere Fester Hidroprimer previo en toda la losa. 
26. FESTERGROUT NM (NM 400 / NM 600 / NM 800): Grouts cementosos de alta resistencia, sin contracción ni expansión (estabilidad volumétrica estructural). RENDIMIENTO: Un saco de 30 kg mezclado correctamente llena exactamente 15.6 Litros de volumen (Factor de consumo: se requieren 1.92 kg de polvo por cada Litro a rellenar). REGLA: Mezclar estrictamente con la cantidad de agua limpia indicada en el saco. NO añadir cemento, NO añadir arena, NO remezclar con más agua una vez iniciado el fraguado.
27. FESTER SUPERSEAL P: Sellador de poliuretano de alto desempeño, elástico y de un solo componente, diseñado para el sellado de juntas de dilatación horizontales y verticales en concreto, pisos industriales y fachadas. REGLA: Ideal para usar en juntas de terrazas grandes impermeabilizadas con CR-66. Excelente resistencia a la intemperie y al agua constante.
28. FESTER FT-201: Sellador y adhesivo elástico multipropósito a base de polímero híbrido avanzado. Diseñado para sellar juntas de movimiento con altas exigencias y pegar diversos materiales de construcción incluso bajo condiciones húmedas. REGLA: No genera burbujas durante el curado y puede ser pintado una vez seco. Ideal para juntas en terrazas transitables.


COMPRAS Y TIENDA FÍSICA:
Fester Paredes es distribuidor autorizado. Opciones de venta:
- Directo por WhatsApp al 3317011786.
- Tienda física: Av. Juan Gil Preciado #2001 Int. 8, Plaza Aleira, Zapopan.
- Redes: @festerparedes en Facebook/Instagram.
Siempre que remitas a contacto usa: 'te recomiendo comunicarte directamente con Fester Paredes al 3317011786'.
"""
    with st.chat_message("assistant"):
        try:
            # Estructura e historial de tu código original intactos
            historial_completo = [{"role": "system", "content": contexto_sistema}] + st.session_state.messages

            completion = client.chat.completions.create(
                model=model_id, # Conserva tu modelo openai/gpt-oss-20b original
                messages=historial_completo,
                temperature=0.0,
                max_tokens=1000
            )
            
            # Extracción segura de la respuesta de tu código original
            if hasattr(completion, 'choices') and len(completion.choices) > 0:
                choice_obj = completion.choices[0]
                
                if hasattr(choice_obj, 'message') and hasattr(choice_obj.message, 'content'):
                    response = choice_obj.message.content
                elif isinstance(choice_obj, dict) and 'message' in choice_obj:
                    response = choice_obj['message']['content']
                elif hasattr(choice_obj, '__dict__') and 'message' in choice_obj.__dict__:
                    response = choice_obj.__dict__['message'].content
                else:
                    response = str(choice_obj)
            else:
                response = str(completion)

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
