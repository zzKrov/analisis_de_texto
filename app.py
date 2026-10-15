import os
import re
import math
import pandas as pd
import streamlit as st
from textblob import TextBlob
import plotly.graph_objects as go

# -----------------------------------------------------------------------------
# TRADUCCIÓN RESILIENTE
# -----------------------------------------------------------------------------
try:
    from deep_translator import GoogleTranslator
    HAS_DEEP = True
except Exception:
    HAS_DEEP = False

try:
    from googletrans import Translator as GTrans
    HAS_GTRANS = True
except Exception:
    HAS_GTRANS = False


def traducir_a_ingles(texto: str) -> str:
    """Traduce a inglés para el motor de análisis de TextBlob."""
    if not texto or not texto.strip():
        return ""
    if HAS_DEEP:
        try:
            return GoogleTranslator(source="auto", target="en").translate(texto)
        except Exception:
            pass
    if HAS_GTRANS:
        try:
            return GTrans().translate(texto, src="auto", dest="en").text
        except Exception:
            pass
    return texto


def traducir_a_idioma(texto: str, target: str) -> str:
    if not texto or not texto.strip() or target == "es":
        return texto
    if HAS_DEEP:
        try:
            return GoogleTranslator(source="auto", target=target).translate(texto)
        except Exception:
            pass
    if HAS_GTRANS:
        try:
            return GTrans().translate(texto, src="auto", dest=target).text
        except Exception:
            pass
    return texto


# -----------------------------------------------------------------------------
# PALABRAS COMUNES / STOPWORDS
# -----------------------------------------------------------------------------
STOP_WORDS = set([
    "a", "al", "algo", "algunas", "algunos", "ante", "antes", "como", "con", "contra",
    "cual", "cuando", "de", "del", "desde", "donde", "durante", "e", "el", "ella",
    "ellas", "ellos", "en", "entre", "era", "eras", "es", "esa", "esas", "ese",
    "eso", "esos", "esta", "estas", "este", "esto", "estos", "ha", "había", "han",
    "has", "hasta", "he", "la", "las", "le", "les", "lo", "los", "me", "mi", "mía",
    "mías", "mío", "míos", "mis", "mucho", "muchos", "muy", "nada", "ni", "no", "nos",
    "nosotras", "nosotros", "nuestra", "nuestras", "nuestro", "nuestros", "o", "os",
    "otra", "otras", "otro", "otros", "para", "pero", "poco", "por", "porque", "que",
    "quien", "quienes", "qué", "se", "sea", "sean", "según", "si", "sido", "sin",
    "sobre", "sois", "somos", "son", "soy", "su", "sus", "suya", "suyas", "suyo",
    "suyos", "también", "tanto", "te", "tenéis", "tenemos", "tener", "tengo", "ti",
    "tiene", "tienen", "todo", "todos", "tu", "tus", "tuya", "tuyas", "tuyo", "tuyos",
    "tú", "un", "una", "uno", "unos", "vosotras", "vosotros", "vuestra", "vuestras",
    "vuestro", "vuestros", "y", "ya", "yo",
    "about", "above", "after", "again", "against", "all", "am", "an", "and",
    "any", "are", "as", "at", "be", "because", "been", "before", "being",
    "below", "between", "both", "but", "by", "could", "did", "do", "does",
    "doing", "down", "during", "each", "few", "for", "from", "further", "had",
    "has", "have", "having", "he", "her", "here", "hers", "herself", "him",
    "himself", "his", "how", "i", "if", "in", "into", "is", "it", "its",
    "itself", "just", "me", "more", "most", "my", "myself", "no", "nor", "not",
    "of", "off", "on", "once", "only", "or", "other", "our", "ours", "ourselves",
    "out", "over", "own", "same", "she", "should", "so", "some", "such", "than",
    "that", "the", "their", "theirs", "them", "themselves", "then", "there",
    "these", "they", "this", "those", "through", "to", "too", "under", "until",
    "up", "very", "was", "we", "were", "what", "when", "where", "which", "while",
    "who", "whom", "why", "with", "would", "you", "your", "yours", "yourself"
])


def render_clean_html(html_str: str):
    clean = "".join(line.strip() for line in html_str.splitlines() if line.strip())
    st.markdown(clean, unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# CONFIGURACIÓN DE PÁGINA
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Analizador de Texto // Tono y Sentimiento",
    page_icon="⚜",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# -----------------------------------------------------------------------------
# ESTILOS NOIR GÓTICOS
# -----------------------------------------------------------------------------
NOIR_CSS = r"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Spectral:ital,wght@0,300;0,400;0,600;0,700;1,400&family=JetBrains+Mono:wght@400;500;700&display=swap');

html, body, [data-testid="stAppViewContainer"] {
    background-color: #050608 !important;
    color: #e5e7eb !important;
    font-family: 'Spectral', Georgia, serif !important;
    overflow-x: hidden;
}

[data-testid="stHeader"] {
    background: transparent !important;
}

.block-container {
    max-width: 1200px !important;
    padding-top: 2rem !important;
    padding-bottom: 3.5rem !important;
    margin: 0 auto !important;
}

.main-title {
    font-family: 'Spectral', serif;
    font-size: 2.4rem;
    font-weight: 700;
    letter-spacing: 0.04em;
    color: #ffffff;
    margin-bottom: 2px;
}

.main-sub {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.78rem;
    letter-spacing: 0.15em;
    color: #d4af37;
    text-transform: uppercase;
    margin-bottom: 1.5rem;
}

.noir-card {
    background: #090b10;
    border: 1px solid rgba(212, 175, 55, 0.22);
    border-radius: 6px;
    padding: 20px;
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.7);
    margin-bottom: 14px;
}

.kpi-card {
    background: #090b10;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-top: 2px solid #d4af37;
    border-radius: 4px;
    padding: 14px;
    text-align: center;
}

.kpi-num {
    font-family: 'Spectral', serif;
    font-size: 1.8rem;
    font-weight: 600;
    color: #fafafa;
}

.kpi-label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.68rem;
    letter-spacing: 0.12em;
    color: #9ca3af;
    text-transform: uppercase;
    margin-top: 2px;
}

.stButton > button {
    background: #0f121a !important;
    border: 1px solid rgba(212, 175, 55, 0.35) !important;
    border-radius: 4px !important;
    color: #f3f4f6 !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.8rem !important;
    padding: 8px 16px !important;
    transition: all 0.2s ease !important;
}

.stButton > button:hover {
    border-color: #d4af37 !important;
    color: #d4af37 !important;
    box-shadow: 0 0 15px rgba(212, 175, 55, 0.2) !important;
}

.stTextArea textarea {
    background: #090b10 !important;
    border: 1px solid rgba(212, 175, 55, 0.25) !important;
    border-radius: 4px !important;
    color: #f3f4f6 !important;
    font-family: 'Spectral', serif !important;
    font-size: 1rem !important;
    padding: 14px 16px !important;
}

.stTextArea textarea:focus {
    border-color: #d4af37 !important;
    box-shadow: 0 0 12px rgba(212, 175, 55, 0.2) !important;
}

.stTabs [data-baseweb="tab-list"] {
    gap: 8px;
}

.stTabs [data-baseweb="tab"] {
    background: #090b10 !important;
    border: 1px solid rgba(255, 255, 255, 0.08) !important;
    border-radius: 4px !important;
    color: #9ca3af !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.8rem !important;
}

.stTabs [aria-selected="true"] {
    border-color: #d4af37 !important;
    color: #d4af37 !important;
    background: rgba(212, 175, 55, 0.08) !important;
}
</style>
"""
render_clean_html(NOIR_CSS)


# -----------------------------------------------------------------------------
# PROCESAMIENTO
# -----------------------------------------------------------------------------
def analizar_texto_profundo(texto_original: str):
    texto_en = traducir_a_ingles(texto_original)
    blob = TextBlob(texto_en)

    polaridad = round(blob.sentiment.polarity, 2)
    subjetividad = round(blob.sentiment.subjectivity, 2)

    palabras_totales = re.findall(r"\b\w+\b", texto_original.lower())
    palabras_filtradas = [
        p for p in palabras_totales if p not in STOP_WORDS and len(p) > 2 and not p.isdigit()
    ]
    conteo_frecuencia = {}
    for p in palabras_filtradas:
        conteo_frecuencia[p] = conteo_frecuencia.get(p, 0) + 1
    frecuencia_ordenada = dict(sorted(conteo_frecuencia.items(), key=lambda x: x[1], reverse=True))

    total_palabras = len(palabras_totales)
    vocabulario_unico = len(set(palabras_totales))
    diversidad_lexica = round((vocabulario_unico / max(1, total_palabras)) * 100, 1)

    tiempo_lectura_seg = round((total_palabras / 200) * 60)
    tiempo_oratoria_seg = round((total_palabras / 130) * 60)

    frases_es = [f.strip() for f in re.split(r"[.!?]+", texto_original) if len(f.strip()) > 3]
    frases_en = [f.strip() for f in re.split(r"[.!?]+", texto_en) if len(f.strip()) > 3]

    trayectoria = []
    min_frases = min(len(frases_es), len(frases_en))
    for i in range(min_frases):
        b_frase = TextBlob(frases_en[i])
        trayectoria.append({
            "idx": i + 1,
            "es": frases_es[i],
            "en": frases_en[i],
            "polaridad": round(b_frase.sentiment.polarity, 2),
            "subjetividad": round(b_frase.sentiment.subjectivity, 2)
        })

    if len(trayectoria) > 1:
        pols = [t["polaridad"] for t in trayectoria]
        media_p = sum(pols) / len(pols)
        volatilidad = round(math.sqrt(sum((p - media_p) ** 2 for p in pols) / len(pols)), 2)
    else:
        volatilidad = 0.0

    if polaridad >= 0.35 and subjetividad >= 0.4:
        tono_nombre = "Motivador y Entusiasta"
        tono_color = "#d4af37"
        tono_desc = "Tono muy positivo con alta carga personal. Útil para animar a un equipo o presentar ideas con energía."
    elif polaridad >= 0.1 and subjetividad < 0.4:
        tono_nombre = "Constructivo y Profesional"
        tono_color = "#38bdf8"
        tono_desc = "Equilibrio claro entre hechos objetivos y una perspectiva favorable."
    elif polaridad <= -0.25 and subjetividad >= 0.45:
        tono_nombre = "Crítico y Contundente"
        tono_color = "#f43f5e"
        tono_desc = "Muestra inconformidad explícita o frustración. Conviene revisar si el objetivo es negociar."
    elif polaridad <= -0.1 and subjetividad < 0.45:
        tono_nombre = "Advertencia Formal"
        tono_color = "#f59e0b"
        tono_desc = "Señala problemas de forma sobria, cuidando las formas sin perder firmeza."
    elif subjetividad < 0.25:
        tono_nombre = "Informativo y Neutral"
        tono_color = "#94a3b8"
        tono_desc = "Totalmente enfocado en datos y hechos sin opiniones personales."
    else:
        tono_nombre = "Conversacional Mixto"
        tono_color = "#a855f7"
        tono_desc = "Combina comentarios personales con datos cotidianos de forma equilibrada."

    return {
        "polaridad": polaridad,
        "subjetividad": subjetividad,
        "tono_nombre": tono_nombre,
        "tono_color": tono_color,
        "tono_desc": tono_desc,
        "total_palabras": total_palabras,
        "vocabulario_unico": vocabulario_unico,
        "diversidad_lexica": diversidad_lexica,
        "tiempo_lectura_seg": tiempo_lectura_seg,
        "tiempo_oratoria_seg": tiempo_oratoria_seg,
        "volatilidad": volatilidad,
        "frecuencia": frecuencia_ordenada,
        "trayectoria": trayectoria,
        "texto_original": texto_original,
        "texto_en": texto_en,
    }


# -----------------------------------------------------------------------------
# GRÁFICOS
# -----------------------------------------------------------------------------
def plot_speedometer(valor, titulo, rango, color_linea):
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=valor,
        number={"font": {"family": "Spectral", "size": 30, "color": "#ffffff"}},
        title={"text": titulo, "font": {"family": "JetBrains Mono", "size": 12, "color": color_linea}},
        gauge={
            "axis": {"range": rango, "tickwidth": 1, "tickcolor": "rgba(255,255,255,0.2)"},
            "bar": {"color": color_linea, "thickness": 0.22},
            "bgcolor": "rgba(0,0,0,0.4)",
            "borderwidth": 1,
            "bordercolor": "rgba(255,255,255,0.08)",
            "steps": [{"range": [rango[0], rango[1]], "color": "rgba(255, 255, 255, 0.03)"}],
        }
    ))
    fig.update_layout(
        height=200,
        margin=dict(l=20, r=20, t=35, b=20),
        paper_bgcolor="rgba(0,0,0,0)",
        font={"color": "#e5e7eb"}
    )
    return fig


def plot_trayectoria_emocional(trayectoria):
    if not trayectoria:
        return None
    df = pd.DataFrame(trayectoria)
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["idx"],
        y=df["polaridad"],
        mode="lines+markers",
        name="Sentimiento",
        line=dict(color="#d4af37", width=2, shape="spline"),
        marker=dict(size=7, color="#d4af37", line=dict(width=1, color="#050608")),
        hovertemplate="<b>Oración %{x}</b><br>Sentimiento: %{y:.2f}<extra></extra>"
    ))
    fig.add_hline(y=0, line_dash="dot", line_color="rgba(255,255,255,0.2)")
    fig.update_layout(
        title="<b>Evolución del tono oración por oración</b>",
        title_font=dict(family="Spectral", size=13, color="#d4af37"),
        xaxis_title="Número de oración",
        yaxis_title="De negativo (-1) a positivo (+1)",
        height=260,
        margin=dict(l=35, r=20, t=40, b=35),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(9, 11, 16, 0.7)",
        font=dict(family="JetBrains Mono", color="#9ca3af", size=10),
        xaxis=dict(gridcolor="rgba(255,255,255,0.05)", tickmode="linear"),
        yaxis=dict(gridcolor="rgba(255,255,255,0.05)", range=[-1.05, 1.05]),
    )
    return fig


def plot_radar_dimensiones(res):
    pos_score = max(0, min(100, int(((res["polaridad"] + 1) / 2) * 100)))
    obj_score = max(0, min(100, int((1 - res["subjetividad"]) * 100)))
    lex_score = max(0, min(100, int(res["diversidad_lexica"])))
    claridad_score = max(0, min(100, int(100 - (res["volatilidad"] * 100))))
    impacto_score = max(0, min(100, int((abs(res["polaridad"]) * 50) + (res["subjetividad"] * 50))))

    categorias = ["Positividad", "Objetividad", "Vocabulario", "Estabilidad", "Fuerza"]
    valores = [pos_score, obj_score, lex_score, claridad_score, impacto_score]
    valores += valores[:1]
    categorias += categorias[:1]

    fig = go.Figure(go.Scatterpolar(
        r=valores,
        theta=categorias,
        fill="toself",
        fillcolor="rgba(212, 175, 55, 0.15)",
        line=dict(color="#d4af37", width=1.8),
        marker=dict(size=5, color="#f59e0b"),
    ))
    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 100], gridcolor="rgba(255,255,255,0.06)", linecolor="rgba(255,255,255,0.06)"),
            angularaxis=dict(gridcolor="rgba(255,255,255,0.06)", linecolor="rgba(255,255,255,0.06)"),
            bgcolor="rgba(0,0,0,0)"
        ),
        title="<b>Equilibrio del mensaje</b>",
        title_font=dict(family="Spectral", size=13, color="#d4af37"),
        height=260,
        margin=dict(l=35, r=35, t=40, b=30),
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="JetBrains Mono", color="#9ca3af", size=9)
    )
    return fig


def plot_barras_frecuencia(frecuencia_dict):
    if not frecuencia_dict:
        return None
    top_items = list(frecuencia_dict.items())[:8]
    palabras = [item[0] for item in reversed(top_items)]
    conteos = [item[1] for item in reversed(top_items)]

    fig = go.Figure(go.Bar(
        x=conteos,
        y=palabras,
        orientation="h",
        marker=dict(color="#c5a059", line=dict(color="#d4af37", width=1)),
        hovertemplate="Palabra: <b>%{y}</b><br>Apariciones: %{x}<extra></extra>"
    ))
    fig.update_layout(
        title="<b>Palabras más repetidas</b>",
        title_font=dict(family="Spectral", size=13, color="#d4af37"),
        height=260,
        margin=dict(l=40, r=20, t=40, b=20),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="JetBrains Mono", color="#9ca3af", size=10),
        xaxis=dict(gridcolor="rgba(255,255,255,0.05)"),
        yaxis=dict(gridcolor="rgba(255,255,255,0.0)")
    )
    return fig


# -----------------------------------------------------------------------------
# EJEMPLOS PREDEFINIDOS
# -----------------------------------------------------------------------------
PRESETS = {
    "pitch": (
        "¡Equipo, logramos un resultado excelente este trimestre! Superamos las metas "
        "gracias al trabajo constante de todos. Esto demuestra que la estrategia elegida fue la correcta. "
        "Sigamos con este mismo impulso para cerrar el año con fuerza."
    ),
    "crisis": (
        "Lamentamos profundamente los fallos del sistema durante la mañana de hoy. "
        "Sabemos los inconvenientes que esto causó y asumimos la responsabilidad. "
        "El equipo técnico ya aplicó una corrección y monitorea la estabilidad del servicio. "
        "Mantendremos informados a todos en tiempo real."
    ),
    "reclamo": (
        "Llevo dos semanas esperando una respuesta y nadie me da una solución clara. "
        "El producto llegó defectuoso y la atención al cliente fue muy deficiente. "
        "Necesito el cambio del producto o la devolución inmediata de mi dinero hoy mismo."
    ),
    "tecnico": (
        "La base de datos procesa las peticiones de forma asíncrona mediante una cola de mensajes. "
        "El tiempo de respuesta promedio es de doce milisegundos en condiciones normales. "
        "El consumo de memoria se mantiene en el setenta por ciento y los respaldos se generan cada seis horas."
    )
}

if "texto_activo" not in st.session_state:
    st.session_state.texto_activo = PRESETS["pitch"]


def cargar_preset(key):
    st.session_state.texto_activo = PRESETS[key]


# -----------------------------------------------------------------------------
# ENCABEZADO
# -----------------------------------------------------------------------------
render_clean_html(
    """
    <div style="margin-bottom: 20px;">
        <div class="main-title">Analizador de Tono y Emociones</div>
        <div class="main-sub">Diagnóstico de actitud, claridad y vocabulario en textos</div>
    </div>
    """
)

st.markdown("<p style='font-size:0.85rem; color:#9ca3af; margin-bottom:8px;'>Prueba con un texto de ejemplo:</p>", unsafe_allow_html=True)

col_p1, col_p2, col_p3, col_p4 = st.columns(4)
with col_p1:
    if st.button("Mensaje de motivación", use_container_width=True):
        cargar_preset("pitch")
        st.rerun()
with col_p2:
    if st.button("Manejo de crisis", use_container_width=True):
        cargar_preset("crisis")
        st.rerun()
with col_p3:
    if st.button("Reclamo directo", use_container_width=True):
        cargar_preset("reclamo")
        st.rerun()
with col_p4:
    if st.button("Reporte técnico", use_container_width=True):
        cargar_preset("tecnico")
        st.rerun()

st.write("")

# -----------------------------------------------------------------------------
# ENTRADA
# -----------------------------------------------------------------------------
col_input_txt, col_opciones = st.columns([3.2, 1], gap="medium")

with col_input_txt:
    texto_usuario = st.text_area(
        label="Escribe o pega aquí el texto a analizar:",
        value=st.session_state.texto_activo,
        height=160,
        placeholder="Escribe tu mensaje, correo o comunicado aquí...",
    )

with col_opciones:
    st.markdown('<div class="noir-card" style="padding: 14px;">', unsafe_allow_html=True)
    st.markdown("<p style='font-size:0.75rem; color:#d4af37; margin:0 0 6px 0; font-family:JetBrains Mono;'>ORIGEN</p>", unsafe_allow_html=True)
    modo_subida = st.radio("Fuente:", ["Escribir texto", "Subir archivo"], horizontal=True, label_visibility="collapsed")

    archivo_subido = None
    if modo_subida == "Subir archivo":
        archivo_subido = st.file_uploader("Archivo (.txt, .md, .csv)", type=["txt", "md", "csv"])

    target_lang = st.selectbox(
        label="Traducir frases a:",
        options=["en", "es", "fr", "ja", "de", "it", "pt"],
        format_func=lambda c: {"en": "Inglés", "es": "Español", "fr": "Francés", "ja": "Japonés", "de": "Alemán", "it": "Italiano", "pt": "Portugués"}.get(c, c),
        index=0
    )
    st.markdown("</div>", unsafe_allow_html=True)

if archivo_subido is not None:
    try:
        texto_usuario = archivo_subido.getvalue().decode("utf-8")
    except Exception as e:
        st.error(f"No se pudo leer el archivo: {e}")

# -----------------------------------------------------------------------------
# RESULTADOS
# -----------------------------------------------------------------------------
if texto_usuario and len(texto_usuario.strip()) > 3:
    with st.spinner("Revisando texto..."):
        res = analizar_texto_profundo(texto_usuario)

    render_clean_html(
        f"""
        <div class="noir-card" style="border-left: 4px solid {res['tono_color']};">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
                <span style="font-family: 'JetBrains Mono'; font-size: 0.72rem; color: {res['tono_color']}; text-transform: uppercase;">
                    Diagnóstico principal
                </span>
                <span style="font-family: 'JetBrains Mono'; font-size: 0.72rem; color: #9ca3af;">
                    Variación de ánimo: {res['volatilidad']}
                </span>
            </div>
            <h2 style="font-family: 'Spectral'; font-size: 1.7rem; margin: 0 0 4px 0; color: #ffffff;">
                {res['tono_nombre']}
            </h2>
            <p style="color: #cbd5e1; font-size: 0.95rem; margin: 0;">
                {res['tono_desc']}
            </p>
        </div>
        """
    )

    min_lectura = res["tiempo_lectura_seg"] // 60
    seg_lectura = res["tiempo_lectura_seg"] % 60
    min_oratoria = res["tiempo_oratoria_seg"] // 60
    seg_oratoria = res["tiempo_oratoria_seg"] % 60

    kpi_cols = st.columns(5)
    with kpi_cols[0]:
        st.markdown(f'<div class="kpi-card"><div class="kpi-num">{res["total_palabras"]}</div><div class="kpi-label">Palabras totales</div></div>', unsafe_allow_html=True)
    with kpi_cols[1]:
        st.markdown(f'<div class="kpi-card"><div class="kpi-num">{res["diversidad_lexica"]}%</div><div class="kpi-label">Variedad de palabras</div></div>', unsafe_allow_html=True)
    with kpi_cols[2]:
        st.markdown(f'<div class="kpi-card"><div class="kpi-num">{len(res["trayectoria"])}</div><div class="kpi-label">Oraciones analizadas</div></div>', unsafe_allow_html=True)
    with kpi_cols[3]:
        st.markdown(f'<div class="kpi-card"><div class="kpi-num">{min_lectura}m {seg_lectura}s</div><div class="kpi-label">Tiempo de lectura</div></div>', unsafe_allow_html=True)
    with kpi_cols[4]:
        st.markdown(f'<div class="kpi-card"><div class="kpi-num">{min_oratoria}m {seg_oratoria}s</div><div class="kpi-label">Tiempo al hablar</div></div>', unsafe_allow_html=True)

    st.write("")

    tab_graficos, tab_oraciones, tab_coaching = st.tabs([
        "Gráficos de resumen",
        "Oración por oración",
        "Sugerencias de redacción"
    ])

    with tab_graficos:
        col_g1, col_g2 = st.columns(2)
        with col_g1:
            st.markdown('<div class="noir-card">', unsafe_allow_html=True)
            pol_color = "#38bdf8" if res["polaridad"] > 0.05 else ("#f43f5e" if res["polaridad"] < -0.05 else "#d4af37")
            fig_pol = plot_speedometer(res["polaridad"], "Sentimiento (-1 negativo, +1 positivo)", [-1, 1], pol_color)
            st.plotly_chart(fig_pol, use_container_width=True, config={"displayModeBar": False})
            st.markdown("</div>", unsafe_allow_html=True)

        with col_g2:
            st.markdown('<div class="noir-card">', unsafe_allow_html=True)
            sub_color = "#a855f7" if res["subjetividad"] > 0.5 else "#d4af37"
            fig_sub = plot_speedometer(res["subjetividad"], "Subjetividad (0 objetivo, 1 opinión)", [0, 1], sub_color)
            st.plotly_chart(fig_sub, use_container_width=True, config={"displayModeBar": False})
            st.markdown("</div>", unsafe_allow_html=True)

        st.markdown('<div class="noir-card">', unsafe_allow_html=True)
        fig_tray = plot_trayectoria_emocional(res["trayectoria"])
        if fig_tray:
            st.plotly_chart(fig_tray, use_container_width=True, config={"displayModeBar": False})
        else:
            st.info("Escribe al menos dos oraciones separadas por punto para ver la curva del tono.")
        st.markdown("</div>", unsafe_allow_html=True)

        col_rad, col_bar = st.columns(2)
        with col_rad:
            st.markdown('<div class="noir-card">', unsafe_allow_html=True)
            fig_radar = plot_radar_dimensiones(res)
            st.plotly_chart(fig_radar, use_container_width=True, config={"displayModeBar": False})
            st.markdown("</div>", unsafe_allow_html=True)

        with col_bar:
            st.markdown('<div class="noir-card">', unsafe_allow_html=True)
            fig_bar = plot_barras_frecuencia(res["frecuencia"])
            if fig_bar:
                st.plotly_chart(fig_bar, use_container_width=True, config={"displayModeBar": False})
            else:
                st.info("No hay suficientes palabras clave para mostrar.")
            st.markdown("</div>", unsafe_allow_html=True)

    with tab_oraciones:
        st.markdown("<p style='font-size:0.85rem; color:#9ca3af;'>Detalle de cada frase detectada en el texto:</p>", unsafe_allow_html=True)
        for item in res["trayectoria"]:
            p = item["polaridad"]
            s = item["subjetividad"]
            badge_color = "#38bdf8" if p > 0.05 else ("#f43f5e" if p < -0.05 else "#d4af37")
            badge_icon = "Positiva" if p > 0.05 else ("Negativa" if p < -0.05 else "Neutra")
            traduccion_frase = traducir_a_idioma(item["es"], target_lang) if target_lang != "es" else item["en"]

            render_clean_html(
                f"""
                <div style="background: #090b10; border: 1px solid rgba(255,255,255,0.06); border-left: 3px solid {badge_color}; border-radius: 4px; padding: 12px; margin-bottom: 8px;">
                    <div style="display: flex; justify-content: space-between; font-size: 0.72rem; font-family: 'JetBrains Mono'; margin-bottom: 4px;">
                        <span style="color: #c5a059;">Oración #{item['idx']}</span>
                        <span style="color: {badge_color};">{badge_icon} (Sentimiento: {p:+.2f} | Opinión: {s:.2f})</span>
                    </div>
                    <div style="font-size: 0.95rem; color: #ffffff; margin-bottom: 4px;">
                        «{item['es']}»
                    </div>
                    <div style="font-size: 0.8rem; color: #9ca3af; font-family: 'JetBrains Mono';">
                        Traducción [{target_lang.upper()}]: {traduccion_frase}
                    </div>
                </div>
                """
            )

    with tab_coaching:
        st.markdown("### Sugerencias prácticas para este texto")
        tips = []
        if res["polaridad"] < -0.15:
            tips.append(("Bajar la hostilidad", "El mensaje tiene una carga negativa alta. Si buscas negociar o resolver un problema, enfócate en pedir soluciones concretas en lugar de solo señalar errores."))
        elif res["polaridad"] > 0.4:
            tips.append(("Aprovechar el buen momento", "El texto transmite mucha energía. Asegúrate de cerrar con una llamada clara a la acción (qué debe hacer el lector ahora)."))

        if res["subjetividad"] > 0.6:
            tips.append(("Agregar datos concretos", f"El {int(res['subjetividad']*100)}% del texto son opiniones o impresiones. Respaldar tus puntos con números o fechas le dará más peso a tu propuesta."))
        elif res["subjetividad"] < 0.25:
            tips.append(("Hacerlo más cercano", "El texto es muy formal y frío. Si vas a hablar con un cliente o equipo, una frase de empatía o contexto personal ayudará a conectar mejor."))

        if res["volatilidad"] > 0.4:
            tips.append(("Suavizar cambios de tono", f"Hay saltos bruscos de emoción entre oraciones ({res['volatilidad']}). Intenta que las transiciones entre tus ideas sean más fluidas."))

        if res["diversidad_lexica"] < 40:
            tips.append(("Cuidar palabras repetidas", f"La variedad de vocabulario es del {res['diversidad_lexica']}%. Usar algunos sinónimos evitará que el texto suene monótono."))

        for titulo_tip, desc_tip in tips:
            render_clean_html(
                f"""
                <div style="background: rgba(212, 175, 55, 0.04); border: 1px solid rgba(212, 175, 55, 0.2); border-radius: 4px; padding: 14px; margin-bottom: 10px;">
                    <div style="font-family: 'Spectral'; font-size: 1rem; color: #d4af37; font-weight: 600; margin-bottom: 2px;">
                        {titulo_tip}
                    </div>
                    <div style="font-size: 0.9rem; color: #e2e8f0; line-height: 1.5;">
                        {desc_tip}
                    </div>
                </div>
                """
            )
else:
    st.info("Escribe algo en el cuadro de texto o elige un ejemplo arriba para ver el análisis.")

with st.sidebar:
    st.markdown("### ¿Cómo se calculan estos datos?")
    st.markdown(
        """
        - **Sentimiento:** Califica de -1 (muy negativo) a +1 (muy positivo).
        - **Subjetividad:** De 0% (datos comprobables) a 100% (opiniones personales).
        - **Variación de ánimo:** Qué tanto cambia el tono de una frase a la siguiente.
        - **Variedad de palabras:** Porcentaje de palabras distintas sobre el total escrito.
        """
    )
