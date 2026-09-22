import os
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

def crear_pdf_maestro():
    # Creamos el directorio generated si no existe
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
    
    # Estilos tipográficos personalizados para la IA
    estilo_titulo = ParagraphStyle(
        'TituloManual',
        parent=styles['Heading1'],
        fontSize=18,
        leading=22,
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
        spaceBefore=10,
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
    
    # Título Principal del documento que leerá el algoritmo
    historia_pdf.append(Paragraph("MANUAL DE CONOCIMIENTO TÉCNICO Y COMERCIAL - FESTERPAREDES", estilo_titulo))
    historia_pdf.append(Spacer(1, 10))
    
    # =========================================================================
    # BLOQUE 1: IMPERMEABILIZANTES ACRÍLICOS (TECHO / LOSA)
    # =========================================================================
    historia_pdf.append(Paragraph(
        "PREGUNTA: ¿Qué producto me recomiendan para impermeabilizar mi casa, techo, losa, azotea o azotera? "
        "¿Qué diferencia hay entre la línea Fester A y el Acriton Pro Shield Max?", 
        estilo_pregunta
    ))
    historia_pdf.append(Paragraph(
        "RESPUESTA: Para recomendar el sistema ideal, el primer paso obligatorio es hacer un sondeo de la obra: <br/>"
        "1. <b>Si es por mera prevención (sin goteras activas):</b> Se especifica la línea <b>Fester A</b> (Gama Profesional), "
        "disponible en durabilidades de 3, 5 y 7 años. Es ideal para presupuestos estándar o trabajos preventivos comunes.<br/>"
        "2. <b>Si la casa ya cuenta con filtraciones activas, goteras o humedad:</b> Se especifica <b>Fester Acriton Pro Shield Max</b> "
        "(Gama Premium), disponible en 4, 6 y 8 años. Al ser de tecnología avanzada, ofrece mayores ventajas sobre la Línea A: "
        "excelente aguante a la abrasión (desgaste por tránsito), mucha mayor elasticidad ante movimientos de la losa y un secado extra rápido.",
        estilo_respuesta
    ))
    
    historia_pdf.append(Paragraph(
        "PREGUNTA: ¿Cuánto rinde un impermeabilizante acrílico (Fester A o Acriton Pro Shield Max) y cuántas capas lleva?", 
        estilo_pregunta
    ))
    historia_pdf.append(Paragraph(
        "RESPUESTA: Basado estrictamente en la ficha técnica, tanto la Línea Fester A como el Acriton Pro Shield Max tienen un rendimiento oficial de "
        "<b>1 Litro por metro cuadrado (m²) aplicado a dos capas</b> (es decir, el consumo estimado de 1 litro total por cada metro de losa).",
        estilo_respuesta
    ))
    
    historia_pdf.append(Paragraph(
        "PREGUNTA: ¿Cómo se aplica un impermeabilizante acrílico en azotea? ¿Cómo se tratan las grietas y puntos críticos?", 
        estilo_pregunta
    ))
    historia_pdf.append(Paragraph(
        "RESPUESTA: El proceso técnico correcto en mostrador consta de 5 pasos secuenciales:<br/>"
        "• <b>Limpieza:</b> Dejar el área o superficie de la azotea perfectamente limpia, barrida, sin polvo, grasas ni falsas adherencias.<br/>"
        "• <b>Primario:</b> Aplicar una capa de <b>Sellador Acriton</b> uniforme en toda la losa para tapar porosidad y asegurar el anclaje.<br/>"
        "• <b>Resanado de fisuras:</b> Si la grieta o fisura es menor a 4 mm se repara con el <b>Resanador Acriton</b>. Si la grieta es mayor a 4 mm, "
        "se debe rellenar obligatoriamente con el sellador de poliuretano <b>Superseal P</b>.<br/>"
        "• <b>Puntos Críticos:</b> Tratar de forma obligatoria las zonas vulnerables (bajantes pluviales, chaflanes, zavaletas y esquinas) "
        "colocando una banda de malla de refuerzo <b>Acriflex</b> o <b>Revoflex</b> ahogada entre las capas de impermeabilizante directo.<br/>"
        "• <b>Capas finales:</b> Aplicar la primera capa directa sin diluir en un solo sentido. Dejar secar y aplicar la segunda capa en sentido cruzado "
        "con respecto a la primera mano.",
        estilo_respuesta
    ))

    # =========================================================================
    # BLOQUE 2: IMPERMEABILIZANTES ASFÁLTICOS (CIMENTACIÓN / DESPLANTE)
    # =========================================================================
    historia_pdf.append(Paragraph(
        "PREGUNTA: Quiero prevenir humedad en el futuro, apenas estoy en la cimentación o dalas de desplante, ¿qué producto recomiendas? "
        "¿Para qué sirve el chapopote o impermeabilizante asfáltico?", 
        estilo_pregunta
    ))
    historia_pdf.append(Paragraph(
        "RESPUESTA: Cuando el cliente está iniciando obra en la parte de los desplantes y cimentaciones, el producto excelente recomendado es "
        "<b>Fester Vaportite 550</b>. Es un impermeabilizante asfáltico base solvente de consistencia pastosa (coloquialmente llamado chapopote) "
        "diseñado para proteger dalas, cimentaciones y muros de contención bajo tierra, evitando que la humedad suba por capilaridad.",
        estilo_respuesta
    ))
    
    historia_pdf.append(Paragraph(
        "PREGUNTA: ¿Cómo se aplica el Fester Vaportite 550 en cimentación o dalas de desplante? ¿Cuánto rinde?", 
        estilo_pregunta
    ))
    historia_pdf.append(Paragraph(
        "RESPUESTA: El proceso oficial de aplicación técnica requiere:<br/>"
        "1. <b>Preparación:</b> Tener el área de concreto sumamente limpia, cepillada y completamente seca.<br/>"
        "2. <b>Primario:</b> Aplicar una mano previa del sellador asfáltico <b>Fester Hidroprimer</b> para abrir anclaje químico.<br/>"
        "3. <b>Membrana:</b> Colocar una membrana de refuerzo de fibra de vidrio integrada para dar soporte estructural.<br/>"
        "4. <b>Aplicación y Secado:</b> El Fester Vaportite 550 <b>no debe diluirse por ningún motivo</b>. Se aplica la primera capa directa con brocha "
        "o llana. Se deja secar perfectamente y <b>72 horas después</b> (tiempo técnico de curado del solvente) se puede aplicar la segunda capa cruzada "
        "antes de levantar muros o rellenar con tierra. El rendimiento se valida en la ficha según la rugosidad del block o concreto.",
        estilo_respuesta
    ))

    doc.build(historia_pdf)

if __name__ == "__main__":
    crear_pdf_maestro()
