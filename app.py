import os
import re
import math
import streamlit as st
from groq import Groq

# Configuración inicial de la página en formato ancho
st.set_page_config(page_title="Asesor FesterParedes", page_icon="🏗️", layout="wide")
# CAMBIO: Aquí agregas el logotipo desde internet
st.image("https://cdninstagram.com", width=250)
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
    
    # Texto de referencia para alimentar a la IA de forma dinámica
    calculo_actual_str = f"Producto seleccionado: {producto_sel}. Total mínimo calculado en el panel lateral: {material_total:.2f} {tipo_unidad}."

    if tipo_unidad == "L":
        cubetas = math.floor(material_total / 19)
        resto = material_total % 19
        botes = math.ceil(resto / 4)
        if botes >= 5:
            cubetas += 1
            botes = 0
        st.metric("Cubetas de 19 L necesarias:", f"{cubetas} Cubeta(s)")
        st.metric("Botes de 4 L necesarios:", f"{botes} Bote(s)")
        calculo_actual_str += f" ({cubetas} cubeta(s) de 19L y {botes} bote(s) de 4L necesarias)."
        
    elif presentacion == "sacos":
        sacos = math.ceil(material_total / 25)
        st.metric("Sacos de 25 kg necesarios:", f"{sacos} Saco(s)")
        calculo_actual_str += f" ({sacos} saco(s) de 25kg necesarios)."
        
    elif presentacion == "kits_cr66":
        kits = math.ceil(material_total / 35)
        st.metric("Kits de 35 kg necesarios (A+B):", f"{kits} Kit(s)")
        calculo_actual_str += f" ({kits} kit(s) de 35kg necesarios)."
        
    elif presentacion == "sacos_grout":
        sacos = math.ceil(material_total / 30)
        st.metric("Sacos de 30 kg necesarios:", f"{sacos} Saco(s)")
        calculo_actual_str += f" ({sacos} saco(s) de 30kg necesarios)."
        
    elif presentacion == "sacos_cm":
        sacos = math.ceil(material_total / 25)
        st.metric("Sacos de 25 kg necesarios:", f"{sacos} Saco(s)")
        calculo_actual_str += f" ({sacos} saco(s) de 25kg necesarios)."

    st.caption("⚠️ Valores teóricos mínimos de rendimiento. El consumo real variará según la porosidad de la superficie.")

# =========================================================================
# CENTRO DE LA PANTALLA: HISTORIAL DEL CHAT CON EL ASESOR
# =========================================================================
for message in st.session_state.messages:
    if message["role"] != "system":
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

    # 1. Comprobar la Base de Datos Local de la Tienda (cerebro_tienda)
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

    # 2. Control de Saludos Manuales de Confianza
    if prompt_normalizado in ["hola", "buenosdias", "buenasnoches", "buenastardes", "saludos", "quetal", "holis"]:
        res_saludo = "¡Hola! Soy tu Asesor Técnico FesterParedes, a la orden. ¿En qué problema de obra te puedo ayudar hoy?"
        with st.chat_message("assistant"):
            st.markdown(res_saludo)
            st.session_state.messages.append({"role": "assistant", "content": res_saludo})
            st.stop()

    mensaje_auxilio = "Con la información que tengo no puedo darte una respuesta 100% precisa sobre esto. Te recomiendo comunicarte directamente con Fester Paredes al 3317011786 para que un especialista te asesore. ¡Con gusto te seguimos ayudando con cualquier otra duda!"

    # === INSTRUCCIONES OPTIMIZADAS CONTRA BUCLES Y SATURACIÓN ===
    contexto_sistema = """
Eres 'Fester Paredes', asesor técnico experto en impermeabilización en Zapopan, Jalisco. Siempre preséntate y responde diciendo: 'Soy tu asesor Fester Paredes a la orden😀, ¿en qué te podemos ayudar?'. Respondes en español, de forma amable, cercana, profesional y humanamente.


=== CONTROL DE IDENTIDAD Y CORTESÍA ===
- NOTA CRÍTICA: SI EL USUARIO SOLO TE ESTÁ SALUDANDO POR PRIMERA VEZ, preséntate diciendo textualmente: 'Soy tu asesor Fester Paredes a la orden, ¿en qué te podemos ayudar😀?'.
- SI LA CONVERSACIÓN YA AVANZÓ (ya es el segundo o tercer mensaje), ¡NO vuelvas a repetir el saludo inicial de presentación ni la pregunta de en qué puedes ayudar! Responde directamente a la consulta del usuario de forma natural como un humano en WhatsApp muy amable como si ya fueran amigos.
- SI EL USUARIO TE AGRADECE, te dice 'gracias', 'perfecto', 'entendido' o se despide, responde de forma sumamente amable e institucional (por ejemplo: '¡Al contrario! Quedo a tus órdenes en Fester Paredes para cuando decidas iniciar tu proyecto.', o '¡Gracias a ti! Éxito en tu obra.'). NO actives el mensaje de auxilio ante palabras de cortesía.

=== REGLA DE ORO ===
Recomienda basándote SOLO en la base de conocimientos adjunta. Si te hacen una pregunta técnica compleja fuera de catálogo o de un caso que no conoces, di textualmente: 'Con la información que tengo no puedo darte una respuesta 100% precisa sobre esto. Te recomiendo comunicarte directamente con Fester Paredes al 3317011786 para que un especialista te asesore. ¡Con gusto te seguimos ayudando con cualquier otra duda!'.

=== PROTOCOLO DE SONDEO NATURAL (EVITAR BUCLES) ===
- Si el usuario te da una respuesta corta o parcial (por ejemplo: 'es de ladrillo' o 'es una azotea'), NO le vuelvas a repetir toda la lista completa de preguntas de sondeo. 
- Toma el dato que ya te dio (ej. superficie de ladrillo) y haz una sola pregunta de seguimiento amigable para avanzar en la conversación (ej. '¡Perfecto! Al ser de ladrillo de azotea, ¿tienes goteras activas o solo buscas proteger por prevención?').
- Avanza con el diagnóstico usando máximo 1 o 2 preguntas breves por mensaje. Nunca inundes al usuario con el mismo cuestionario de forma robótica.
- Una vez que tengas una idea clara de la superficie y la necesidad, ofrece la solución técnica ideal explicando brevemente los pasos (Limpieza -> Sellador/Primario -> Impermeabilizante) y sus rendimientos oficiales.

=== PRODUCTOS, RENDIMIENTOS Y RESTRICCIONES CRÍTICAS ===
1. ACRIFLEX: Malla de poliéster tejido para puntos críticos o refuerzo integral acrílico/asfáltico. Rollo 1.10x100m (~100m²). NO usar en sistemas asfálticos en caliente.
2. ACRITON GREEN-SHIELD 10 AÑOS: Acrílico ecológico reflectivo para techos sin tránsito peatonal ni vehicular. RENDIMIENTO: 1.0 Litro/m² a 2 capas (sin malla). REGLA: Requiere Acriton Sellador previo. NO diluir con agua, NO aplicar sobre superficies mojadas ni donde haya encharcamientos constantes.Si existen encharcamientos. se recomiendan a nivelarlos primero. Secado extra rapido.
3. ACRITON RESANADOR: Pasta lista para usar para sellar fisuras menores a 5mm en azoteas previo al impermeabilizante. REGLA: Requiere imprimación con Acriton Sellador en la fisura. NO diluir, NO usar en juntas estructurales con movimiento severo.Siempre que se resanen las fisuras de azotea se recomienda reforzar con malla revoflex o acriflex e impermeabilizar, nunca se deja expuesto.
4. ACRITON PROSHIELD MAX (4, 6 y 8 años): Acrílico de secado rápido (2 capas en una mañana). RENDIMIENTO: 1.0 Litro/m² a 2 capas en losa normal; 0.65 L/m² para mantenimiento. REGLA: Requiere Acriton Sellador previo y sellar fisuras si llegan a existir. NO diluir con agua, NO usar en inmersión continua ni tráfico vehicular.
5. ACRITON SELLADOR: Primario acrílico. RENDIMIENTO: Fijar en 5 m² por Litro (0.20 L/m²). REGLA: Aplicar SIN DILUIR en techos; diluido 1:1 con agua limpia únicamente si se usa en muros o fachadas exteriores.Es necesario para que el impermeabilizante tenga buena adherencia.
6. FESTER A (A3, A5, A5 Fibratado, A7): Acrílicos Profesionales. RENDIMIENTO: 1.0 Litro/m² a 2 capas en superficie normal; 1.5 Litros/m² si se instala con malla de refuerzo integral. REGLA: Requiere sellador previo. NO aplicar a menos de 5°C ni sobre charcos.Se recomienda sellar fisuras con resanador acriton si son menores a 5mm, de lo contrario usar sellador superseal p o ft201 para juntas de alto movimiento.
7. CF-890: Anclaje químico de poliéster (300mL) para varillas y pernos. REGLA: Mezclado automático con su boquilla. NO requiere primario. NO aplicar en perforaciones húmedas ni bajo el sol directo durante la inyección.No se recomienda instalar bajo el agua. Soporta hasta 1200 kg de extraccion si el sustrato lo soporta.
8. CF-1000: Anclaje químico epóxico estructural (585mL). REGLA: Mezclado automático por boquilla. SÍ tiene alta adherencia en concreto húmedo o seco. NO diluir ni alterar la mezcla.
9. FESTER CL-52: Membrana impermeable elástica monocomponente de secado extra rápido. SUGERENCIA DE APLICACIÓN: Diseñado específicamente para interiores ANTES de colocar azulejos o acabados cerámicos en charolas de baño, regaderas, cocinas, cuartos de lavado, saunas, zonas húmedas y terrazas/balcones pequeños (máx. 25 m² con malla Acriflex). RENDIMIENTO: Primario diluido 1:2 con agua = 4 a 5 m²/L; capas puras sin diluir para la aplicacion despues del primario = 0.5 L/m² por capa (1.0 L/m² total a 2 capas); en zonas muy agrietadas con malla integral rinde de 1.3 a 1.5 L/m² total. REGLA: Se aplica directo. NO dejar expuesto permanentemente a la intemperie, NO usar en losas de azotea exteriores ni techos de lámina expuestos.Se recomienda malla de refuerzo en puntos criticos como esquinas y desagues.
10. CM-200: Mortero cementoso para resanes cosméticos no estructurales (0.5 a 10cm de espesor). RENDIMIENTO: Saco de 25kg + 4L de agua rinde 14L de mezcla (Factor: 1.80 kg por litro de relleno). SÍ resiste inmersión. NO requiere primario.
11. CM-201: Mortero estructural de reparación vertical/horizontal de ALTA resistencia. RENDIMIENTO: Saco de 25kg + 4L de agua rinde 14L de mezcla. REGLA: Fraguado rápido, transitable en 1 hora. NO mezclar con cemento o arena; usar solo agua limpia.
12. CM-202: Mortero FLUIDO estructural de alta resistencia para colar en cimbras/encofrados angostas. RENDIMIENTO: Saco de 25kg + 4L de agua rinde 14L de mezcla. REGLA: Autonivelante, transitable en 1 hora. NO usar como aplanado vertical debido a su alta fluidez.Minimo espesor 2.5mm.
13. CR-65: Cementoso rígido contra SALITRE y humedad ascendente en muros de block o tabique (aplicar directo al muro sin pintura ni enjarre, no se recomienda en desplantes de cimentacion o dalas). RENDIMIENTO: Humedad subsuelo 3 kg/m² (2 capas); agua de lluvia 4 kg/m² (2 capas); cisternas/tanques 5 kg/m² (3 capas). REGLA: Saco de 25kg con 6 a 6.5L de agua limpia. NO aplicar en losas de techo ni sobre grietas dinámicas ni en enjarres.Si el muro  tiene humedad y salitre y ya esta enjarrado y pintado se recomienda retirar el enjarre y la pintura para dejar el ladrillo o block virgen y aplicar cr65 directo, nunca por encima del enjarre. Si existen fisuras se rellenan con reparador cm200 si no es estructural o cm201 si si es estructural.El tecnico realizara la mejor recomendacion para retirar el enjarre, tu no recomiendes como retirar el enjarre.
14. FESTER CR-66 FIBRE FORCE: Cementoso flexible de 2 componentes (Polvo A + Líquido B) para cisternas, albercas, charolas de baño o terrazas que llevarán piso encima. Puentea grietas de hasta 4mm. RENDIMIENTO: Cimentación y baños 2.5 kg/m² (2 capas); terrazas o depósitos de agua 3.0 a 3.5 kg/m² (2 a 3 capas). REGLA DE ORO PARA TERRAZAS: Se puede aplicar de forma continua en áreas menores a 25 m²; si la terraza es MAYOR a 25 m², es obligatorio generar juntas de dilatación/movimiento perimetrales e intermedias y sellarlas con Fester Superseal P o Fester FT-201. NO agregar agua bajo ninguna circunstancia, NO dejar expuesto a la intemperie sin acabado pétreo (piso) encima.
15. CR-NANOTECH 99+: Cementoso por cristalización para concreto existente bajo presiones hidrostáticas severas (cisternas subterráneas). RENDIMIENTO: 0.75 kg por capa (1.5 kg/m² total a 2 capas). REGLA: Mezclar solo con agua limpia. NO aplicar en losas de techo, ladrillos o mampostería (solo funciona en concreto puro).
16. CR-NANOTECH ADMIX: Aditivo en polvo que se integra DIRECTO en la olla/revolvedora durante el mezclado del concreto nuevo para impermeabilizarlo desde su fabricación. DOSIFICACIÓN: 2% sobre el peso del cemento (1 kg por cada bulto de cemento de 50 kg). NO usar en concretos ya endurecidos.
17. CX-01: Mortero cementoso de fraguado instantáneo (1 minuto) para taponar fugas francas, chorros y filtraciones activas de agua a presión. RENDIMIENTO: 1 kg llena 680 cm³ de grieta profunda. REGLA: Mezclar cantidades pequeñas solo con las manos (usar guantes) y agua limpia. APLICAR INMEDIATAMENTE presionando firmemente.
18. EPOXINE 200: Adhesivo epóxico de 2 componentes (A+B) para unir concreto nuevo a viejo en juntas de colado estructurales. RENDIMIENTO: 3 a 3.5 m² por Litro de mezcla. REGLA: Mezclar componentes A y B completos. NO es un impermeabilizante para filtraciones, NO aplicar si el concreto viejo tiene polvo o grasa.
19. EPOXINE 800 GROUT: Mortero epóxico industrial de 3 componentes (A+B+C) para anclaje de maquinaria pesada (>100L). RENDIMIENTO: La unidad de 112 kg llena exactamente 52 Litros de volumen (Factor: 2.15 kg por litro de relleno). NO mezclar con agua.
20. FESTERBOND: Adhesivo acrílico multiusos. RENDIMIENTO como sellador poroso: 4 a 5 m²/L (diluido 1:1 con agua). REGLA: Úsalo como fortificador en morteros dosificacion 2% sobre el peso del mortero, (reemplazando parte del agua de mezcla) o como lechada adherente. NO tiene propiedades estructurales para trabes o columnas.Para unir mortero a concreto viejo no estructural, si es estructural recomendar epoxine 200.
21. FESTERFLEX: Membrana de refuerzo no tejida de filamentos sintéticos. REGLA: Específica para sistemas impermeables ASFÁLTICOS aplicados en frío. NO usar en sistemas acrílicos ni en caliente.
22. FESTEGRAL: Aditivo integral en polvo para reducir la permeabilidad y absorción de agua en mezclas de concreto y mortero tradicional. DOSIFICACIÓN: 2% sobre el peso del cemento (1 kg por bulto de 50 kg). REGLA: Mezclar en seco con el cemento y la arena antes de agregar el agua.
23. FESTER VAPORTITE 550: Impermeabilizante asfáltico base solvente de consistencia pastosa para sistemas multicapa en frío (barrera de vapor extrema). RENDIMIENTO: 1.0 Litro/m² por capa sola en losa; 2.0 Litros/m² en sistema multicapa con malla de refuerzo. REGLA: Altamente inflamable y tóxico.

===DONDE COMPRAR/ CONTACTO COMERCIAL ===
COMPRAS Y TIENDA FÍSICA:
Cuando te pregunten dónde comprar, cómo adquirir un producto, precios, o disponibilidad, o te agradezcan, responde con calidez que Fester Paredes es distribuidor autorizado y ofrece estas opciones:
- Compra directa por WhatsApp al 3317011786 (con gusto se les vende ahí mismo).
- Visitar la tienda física en Av. Juan Gil Preciado #2001 Int. 8, Plaza Aleira, Zapopan.
- Seguirlos en redes sociales como 'festerparedes' en Facebook e Instagram para promociones y novedades.
Ejemplo de respuesta: 'Nosotros somos distribuidores autorizados Fester y con gusto te vendemos directo por WhatsApp al 3317011786, o si prefieres visitar nuestra tienda física, nos encuentras en Av. Juan Gil Preciado #2001 Int. 8, Plaza Aleira, Zapopan. También puedes seguirnos como festerparedes en Facebook e Instagram para ver promociones y novedades.
Siempre que remitas a contacto usa: 'te recomiendo comunicarte directamente con Fester Paredes al 3317011786'.

=== CUANDO NO TIENES LA RESPUESTA ===
Si la pregunta no puede responderse con la información de esta base de conocimiento (por ejemplo, un producto que no está aquí, una situación muy específica de ingeniería estructural, o datos que no aparecen en las fichas técnicas), NUNCA inventes ni especules. Responde con amabilidad, por ejemplo:
'Con la información que tengo no puedo darte una respuesta 100% precisa sobre esto. Te recomiendo comunicarte directamente con Fester Paredes al 3317011786 para que un especialista te asesore. ¡Con gusto te seguimos ayudando con cualquier otra duda!'
Esta misma frase ('te recomiendo comunicarte directamente con Fester Paredes al 3317011786') debes usarla SIEMPRE que remitas a alguien a contacto directo, ya sea porque no tienes la respuesta, porque el caso requiere revisión en sitio de un especialista, o porque quieren comprar.
"""
    mensajes_para_api = [{"role": "system", "content": contexto_sistema}]
    
    for msg in st.session_state.messages:
        if msg["role"] != "system":
            mensajes_para_api.append(msg)
            
    if any(k in prompt_normalizado for k in ["cuanto", "necesito", "calcula", "rendimiento", "material", "cubetas", "sacos"]):
        mensajes_para_api.append({
            "role": "system", 
            "content": f"INFORMACIÓN DINÁMICA DE LA CALCULADORA LATERAL: El usuario está solicitando un cálculo de obra. Usa este dato exacto calculado en tiempo real en la interfaz para responderle: {calculo_actual_str}"
        })

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
            
            st.session_state.messages.append({"role": "assistant", "content": full_response})
            
        except Exception as e:
            st.error(f"Error al conectar con Groq: {e}")
