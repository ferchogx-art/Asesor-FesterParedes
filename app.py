import streamlit as st
import os
import glob
import re
from groq import Groq

st.set_page_config(page_title="Asesor Técnico Fester", page_icon="🏗️", layout="centered")
st.title("🏗️ Asesor Técnico FesterParedes IA")
st.write("Respuestas ejecutivas inmediatas para ingenieros en obra basadas en tu criterio comercial.")

# 1. Conectar con la API de Groq
api_key = os.environ.get("GROQ_API_KEY", st.secrets.get("GROQ_API_KEY", ""))
if not api_key:
    st.error("Falta configurar la clave GROQ_API_KEY en los Secrets.")
    st.stop()

client = Groq(api_key=api_key)

# =========================================================================
# 2. TU DICCIONARIO MAESTRO (INTEGRADO DE FORMA INALTERABLE)
# =========================================================================
TU_CONOCIMIENTO = [
    {
        "claves": ["charola", "baño", "zona humeda", "cl52", "cl-52"],
        "respuesta": (
            "Para impermeabilizar una **charola de baño o zonas húmedas**, el producto recomendado es **Fester CL-52**. "
            "Es un impermeabilizante cementoso elástico de rápida aplicación que evita filtraciones entre pisos. "
            "El rendimiento exacto se extrae directamente de la ficha técnica según las condiciones de la superficie."
        )
    },
    {
        "claves": ["salitre", "humedad", "pared", "muro", "cr65", "cr66", "cr-65", "cr-66"],
        "respuesta": (
            "Para problemas de **humedad y salitre en muros o paredes**, la solución definitiva es la línea cementosa **Fester CR**. "
            "La elección depende de la urgencia de la obra:\n"
            "- **Fester CR-65:** Opción económica estándar, pero requiere un proceso obligatorio de curado con agua durante 2 días seguidos.\n"
            "- **Fester CR-66:** Opción premium y rápida. Es bicomponente, elástico y NO necesita curado con agua, lo que permite avanzar de inmediato con los acabados."
        )
    },
    {
        "claves": ["usos multiples", "fortificar", "mezcla", "concreto", "mortero", "festerbond"],
        "respuesta": (
            "Si necesitas un sellador de **usos múltiples o un aditivo para fortificar mezclas**, el producto ideal es **Festerbond**.\n"
            "- **Uso:** Funciona como unión de concreto nuevo a viejo, fortificador de morteros, lechadas y sellador de porocidad.\n"
            "- **Rendimiento:** Se saca de la ficha técnica ya que varía según la dilución de agua requerida para la mezcla."
        )
    },
    {
        "claves": ["anclaje", "quimico", "varilla", "perno", "carga", "cf890", "cf1000", "cf-890", "cf-1000"],
        "respuesta": (
            "Para un **anclaje químico de varillas o pernos**, la recomendación se define mediante el sondeo del tipo de carga:\n"
            "- **Fester CF-890:** Diseñado para fijaciones y anclajes de **carga ligera o mediana** en condiciones normales.\n"
            "- **Fester CF-1000:** Diseñado para **carga pesada**, altas demandas estructurales y tiene la gran ventaja de que funciona perfectamente **bajo el agua** o en perforaciones inundadas."
        )
    },
    {
        "claves": ["economico", "barato", "presupuesto", "inversion", "linea a", "a3", "a5", "a7", "fibratado"],
        "respuesta": (
            "Si buscas impermeabilizar con un **presupuesto limitado (poca inversión económica)** y de forma preventiva, la recomendación oficial es la **Línea Fester A**.\n"
            "- Viene en presentaciones de **3, 5 y 7 años** de durabilidad.\n"
            "- Destaca el **Fester A 5 Años Fibratado**, que por llevar fibras integradas facilita la aplicación.\n"
            "- **Rendimiento:** El rendimiento real de la línea acrílica en losa es de **1 a 1.5 Litros por m² a dos capas** (el conocido 1 a 1)."
        )
    },
    {
        "claves": ["muchos años", "premium", "alta calidad", "duradero", "acriton", "4 años", "6 años", "8 años", "12 años"],
        "respuesta": (
            "Si el cliente busca una protección que **dure muchos años** con máxima calidad, se debe recomendar la línea premium: **Fester Acriton**.\n"
            "- Son impermeabilizantes acrílicos con tecnología avanzada de poliuretano.\n"
            "- Disponibles en garantías extremas de **4, 6, 8 y hasta 12 años**, ofreciendo excelente resistencia al movimiento de las losas."
        )
    },
    {
        "claves": ["medio ambiente", "ecologico", "sustentable", "green shield", "green-shield"],
        "respuesta": (
            "Para proyectos que requieran un producto **amigable con el medio ambiente**, la solución es **Fester Acriton Green Shield**.\n"
            "- Ofrece una durabilidad garantizada de **10 años**.\n"
            "- Es un sistema ecológico sustentable que ayuda a reducir la absorción de calor en las edificaciones."
        )
    }
]

# 3. Carga inteligente de fichas técnicas en formato PDF (Sueltas en GitHub)
@st.cache_resource
def extraer_conocimiento_fester():
    texto_completo = []
    archivos_validos = glob.glob("*.pdf")
    for ruta in archivos_validos:
        nombre_archivo = os.path.basename(ruta)
        try:
            import fitz  # PyMuPDF
            doc = fitz.open(ruta)
            for num_pag, pagina in enumerate(doc):
                texto_pag = pagina.get_text()
                if texto_pag.strip():
                    texto_completo.append({
                        "origen": nombre_archivo,
                        "referencia": f"Pág. {num_pag + 1}",
                        "texto": texto_pag
                    })
        except Exception as e:
            print(f"Error leyendo {nombre_archivo}: {e}")
    return texto_completo

base_conocimiento = extraer_conocimiento_fester()

# Panel visual de diagnóstico
num_bloques = len(base_conocimiento)
if num_bloques == 0:
    st.error("⚠️ ALERTA: No se detectaron PDFs en la raíz de GitHub.")
else:
    st.success(f"📚 Base de datos activa: Conectado a las fichas técnicas individuales ({num_bloques} páginas).")

# 4. Historial
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 5. Lógica del Asesor de Obra Ejecutivo
if prompt := st.chat_input("¿Qué problema tienes en obra o qué producto deseas validar?"):
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    prompt_lower = prompt.lower()
    solucion_maestra = ""

    # BUSQUEDA INMEDIATA EN TU CONOCIMIENTO COMERCIAL TRATADO
    for item in TU_CONOCIMIENTO:
        if any(clave in prompt_lower for clave in item["claves"]):
            solucion_maestra = item["respuesta"]
            break

    with st.chat_message("assistant"):
        if solucion_maestra:
            # Si coincide con tus reglas comerciales, responde al grano con tus palabras fijas
            st.markdown(solucion_maestra)
            st.session_state.messages.append({"role": "assistant", "content": solucion_maestra})
        else:
            # Si pregunta algo técnico avanzado, busca estrictamente en las fichas individuales
            contexto_manuales = ""
            palabras = [p for p in prompt_lower.split() if len(p) > 2]
            puntuaciones = []
            
            for item_doc in base_conocimiento:
                texto_manual = item_doc["texto"].lower()
                puntos = sum(3 for p in palabras if p in texto_manual)
                if puntos > 0:
                    puntuaciones.append((puntos, item_doc))
            
            if puntuaciones:
                puntuaciones.sort(key=lambda x: x[0], reverse=True)
            
            for puntos, res in puntuaciones[:2]:
                contexto_manuales += f"\n[Ficha Técnica: {res['origen']} - {res['referencia']}]\n{res['texto']}\n"

            contexto_sistema = (
                "Eres el Asesor Técnico Ejecutivo de Fester México.\n"
                "REGLAS OBLIGATORIAS DE REDACCIÓN:\n"
                "1. Responde de forma resumida en máximo 1 o 2 párrafos cortos. Ve directo al grano.\n"
                "2. Usa exclusivamente los datos técnicos de la ficha provista abajo para evitar mezclar líneas.\n"
                "3. Si la ficha técnica no contiene el dato, di: 'No dispongo del rendimiento exacto en esta ficha, favor de validar catálogo físico.'\n\n"
                f"TEXTO OFICIAL DE LA FICHA INDIVIDUAL:\n{contexto_manuales}"
            )

            try:
                completion = client.chat.completions.create(
                    model="openai/gpt-oss-120b",
                    messages=[
                        {"role": "system", "content": contexto_sistema},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.0,
                    max_tokens=300,
                )
                response = completion.choices[0].message.content
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
            except Exception as e:
                st.error(f"Error en motor IA: {e}")

