import os
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

def crear_pdf_maestro():
    os.makedirs("generated", exist_ok=True)
    ruta_pdf = "generated/respuestas_maestras_tienda.pdf"
    
    doc = SimpleDocTemplate(
        ruta_pdf,
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40,
        title="Manual de Respuestas Maestras FesterParedes"
    )
    
    styles = getSampleStyleSheet()
    
    estilo_titulo = ParagraphStyle(
        'TituloManual',
        parent=styles['Heading1'],
        fontSize=16,
        leading=20,
        spaceAfter=15,
        textColor='#1A365D'
    )
    
    estilo_pregunta = ParagraphStyle(
        'PreguntaTienda',
        parent=styles['Normal'],
        fontSize=11,
        leading=15,
        bold=True,
        textColor='#2B6CB0',
        spaceBefore=12,
        spaceAfter=5
    )
    
    estilo_respuesta = ParagraphStyle(
        'RespuestaTienda',
        parent=styles['Normal'],
        fontSize=10,
        leading=14,
        textColor='#2D3748',
        spaceAfter=10
    )

    historia_pdf = []
    
    # Encabezado
    historia_pdf.append(Paragraph("MANUAL DE CONOCIMIENTO TÉCNICO COMPLETO - FESTERPAREDES V2", estilo_titulo))
    historia_pdf.append(Spacer(1, 10))
    
    # =========================================================================
    # BLOQUE 1: IMPERMEABILIZANTES ACRÍLICOS (TECHO / LOSA)
    # =========================================================================
    historia_pdf.append(Paragraph("PREGUNTA: ¿Qué producto me recomiendan para impermeabilizar mi casa, techo, losa, azotea o azotera? ¿Qué diferencia hay entre la línea Fester A y el Acriton Pro Shield Max?", estilo_pregunta))
    historia_pdf.append(Paragraph("RESPUESTA: Para recomendar el sistema ideal, el primer paso obligatorio es hacer un sondeo de la obra: <br/>1. <b>Si es por mera prevención (sin goteras activas):</b> Se especifica la línea <b>Fester A</b> (Gama Profesional), disponible en durabilidades de 3, 5 y 7 años. Es ideal para presupuestos estándar o trabajos preventivos comunes.<br/>2. <b>Si la casa ya cuenta con filtraciones activas, goteras o humedad:</b> Se especifica <b>Fester Acriton Pro Shield Max</b> (Gama Premium), disponible en 4, 6 y 8 años. Al ser de tecnología avanzada, ofrece mayores ventajas sobre la Línea A: excelente aguante a la abrasión (desgaste por tránsito), mucha mayor elasticidad ante movimientos de la losa y un secado extra rápido.", estilo_respuesta))
    
    historia_pdf.append(Paragraph("PREGUNTA: ¿Cuánto rinde un impermeabilizante acrílico (Fester A o Acriton Pro Shield Max) y cuántas capas lleva?", estilo_pregunta))
    historia_pdf.append(Paragraph("RESPUESTA: Basado estrictamente en la ficha técnica, tanto la Línea Fester A como el Acriton Pro Shield Max tienen un rendimiento oficial de <b>1 Litro por metro cuadrado (m²) aplicado a dos capas</b> (es decir, el consumo estimado de 1 litro total por cada metro de losa).", estilo_respuesta))
    
    historia_pdf.append(Paragraph("PREGUNTA: ¿Cómo se aplica un impermeabilizante acrílico en azotea? ¿Cómo se tratan las grietas y puntos críticos?", estilo_pregunta))
    historia_pdf.append(Paragraph("RESPUESTA: El proceso técnico correcto en mostrador consta de 5 pasos secuenciales:<br/>• <b>Limpieza:</b> Dejar el área o superficie de la azotea perfectamente limpia, barrida, sin polvo, grasas ni falsas adherencias.<br/>• <b>Primario:</b> Aplicar una capa de <b>Sellador Acriton</b> uniforme en toda la losa para tapar porosidad y asegurar el anclaje.<br/>• <b>Resanado de fisuras:</b> Si la grieta o fisura es menor a 4 mm se repara con el <b>Resanador Acriton</b>. Si la grieta es mayor a 4 mm, se debe rellenar obligatoriamente con el sellador de poliuretano <b>Superseal P</b>.<br/>• <b>Puntos Críticos:</b> Tratar de forma obligatoria las zonas vulnerables (bajantes pluviales, chaflanes, zavaletas y esquinas) colocando una banda de malla de refuerzo <b>Acriflex</b> o <b>Revoflex</b> ahogada entre las capas de impermeabilizante directo.<br/>• <b>Capas finales:</b> Aplicar la primera capa directa sin diluir en un solo sentido. Dejar secar y aplicar la segunda capa en sentido cruzado con respecto a la primera mano.", estilo_respuesta))

    # =========================================================================
    # BLOQUE 2: IMPERMEABILIZANTES ASFÁLTICOS (CIMENTACIÓN / DESPLANTE)
    # =========================================================================
    historia_pdf.append(Paragraph("PREGUNTA: Quiero prevenir humedad en el futuro, apenas estoy en la cimentación o dalas de desplante, ¿qué producto recomiendas? ¿Para qué sirve el chapopote o impermeabilizante asfáltico?", estilo_pregunta))
    historia_pdf.append(Paragraph("RESPUESTA: Cuando el cliente está iniciando obra en la parte de los desplantes y cimentaciones, el producto excelente recomendado es <b>Fester Vaportite 550</b>. Es un impermeabilizante asfáltico base solvente de專 consistencia pastosa (coloquialmente llamado chapopote) diseñado para proteger dalas, cimentaciones y muros de contención bajo tierra, evitando que la humedad suba por capilaridad.", estilo_respuesta))
    
    historia_pdf.append(Paragraph("PREGUNTA: ¿Cómo se aplica el Fester Vaportite 550 en cimentación o dalas de desplante? ¿Cuánto rinde?", estilo_pregunta))
    historia_pdf.append(Paragraph("RESPUESTA: El proceso oficial de aplicación técnica requiere:<br/>1. <b>Preparación:</b> Tener el área de concreto sumamente limpia, cepillada y completamente seca.<br/>2. <b>Primario:</b> Aplicar una mano previa del sellador asfáltico <b>Fester Hidroprimer</b> para abrir anclaje químico.<br/>3. <b>Membrana:</b> Colocar una membrana de refuerzo de fibra de vidrio integrada para dar soporte estructural.<br/>4. <b>Aplicación y Secado:</b> El Fester Vaportite 550 <b>no debe diluirse por ningún motivo</b>. Se aplica la primera capa directa con brocha o llana. Se deja secar perfectamente y <b>72 horas después</b> (tiempo técnico de curado del solvente) se puede aplicar la segunda capa cruzada antes de levantar muros o rellenar con tierra. El rendimiento se valida en la ficha según la rugosidad del block o concreto.", estilo_respuesta))

    # =========================================================================
    # NUEVO BLOQUE 3: REPARADORES ESTRUCTURALES (LÍNEA FESTER CM)
    # =========================================================================
    historia_pdf.append(Paragraph("PREGUNTA: ¿Para qué sirven los reparadores Fester CM? ¿Cuál es la diferencia entre Fester CM-200, CM-201 y CM-202?", estilo_pregunta))
    historia_pdf.append(Paragraph("RESPUESTA: La línea Fester CM está diseñada para reparar estructuras de concreto o mortero dañado según la necesidad específica de la obra:<br/>"
                                  "• <b>Fester CM-200 (Reparador Estructural Rápido):</b> Es un mortero cementoso de fraguado rápido ideal para reparar oquedades, baches, cantos de vigas, postes o secciones de concreto profundas en superficies verticales, horizontales o sobre la cabeza sin necesidad de usar cimbra.<br/>"
                                  "• <b>Fester CM-201 (Grout Estructural Fluido):</b> Es un mortero cementoso de alta resistencia e increíble fluidez, diseñado para rellenar bases de maquinaria, anclaje de columnas estructurales o rellenar cavidades confinadas donde se requiera que el material corra solo y no tenga contracción.<br/>"
                                  "• <b>Fester CM-202 (Reparador Fino y Estético):</b> Es un mortero cementoso diseñado para reparaciones cosméticas y capas delgadas (resanes finos). Sirve para tapar poros, resanar pequeñas imperfecciones en muros de concreto aparente o prefabricados, dejando un acabado liso listo para recibir pintura.", estilo_respuesta))

    historia_pdf.append(Paragraph("PREGUNTA: ¿Cómo se aplican los morteros de reparación Fester CM200, CM201 o CM202?", estilo_pregunta))
    historia_pdf.append(Paragraph("RESPUESTA: Para los tres productos de la línea CM, el proceso básico e inalterable en mostrador es:<br/>"
                                  "1. <b>Preparación:</b> Se debe picar el concreto viejo dañado hasta llegar a superficie sana y firme. Retirar polvo y aceites.<br/>"
                                  "2. <b>Saturación:</b> Humedecer abundantemente el área con agua limpia (saturar la superficie) pero sin dejar encharcamientos antes de colocar la mezcla.<br/>"
                                  "3. <b>Mezclado:</b> Agregar el polvo al agua limpia respetando las relaciones de la ficha técnica. Mezclar mecánicamente por 3 minutos hasta eliminar grumos.<br/>"
                                  "4. <b>Colocación:</b> Aplicar el CM-200 a presión con llana en capas sucesivas si es profundo; vaciar el CM-201 de forma continua por un solo lado para evitar burbujas de aire; o extender el CM-202 con llana metálica para acabados finos estéticos.", estilo_respuesta))

    # =========================================================================
    # NUEVO BLOQUE 4: TECNOLOGÍA CRISTALINA (FESTER NANOTECH)
    # =========================================================================
    historia_pdf.append(Paragraph("PREGUNTA: ¿Qué es la tecnología cristalina Fester Nanotech y cuál es la diferencia entre Nanotech Admix y Nanotech 99?", estilo_pregunta))
    historia_pdf.append(Paragraph("RESPUESTA: Fester Nanotech es un sistema de impermeabilización por cristalización capilar que reacciona con la humedad del concreto para sellar sus poros de forma interna y permanente:<br/>"
