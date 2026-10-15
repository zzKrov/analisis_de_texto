import os
import re
import math
import html
import pandas as pd
import streamlit as st
from textblob import TextBlob
import plotly.graph_objects as go

# -----------------------------------------------------------------------------
# TRADUCCIÓN RESILIENTE Y MOTORES AUXILIARES
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
# CONFIGURACIÓN DEL ESPACIO DE TRABAJO
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="KROV // Analizador Semántico y Emocional",
    page_icon="⚜",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# -----------------------------------------------------------------------------
# IDENTIDAD VISUAL: GÓTICO NOIR & TELEMETRÍA KROV INDUSTRIES
# -----------------------------------------------------------------------------
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Spectral:ital,wght@0,300;0,400;0,600;0,700;1,400&family=JetBrains+Mono:wght@400;500;700&display=swap');

    html, body, [data-testid="stAppViewContainer"] {
        background: radial-gradient(circle at 50% 15%, #0d121f 0%, #06080e 55%, #020306 100%) !important;
        color: #f1f5f9 !important;
        font-family: 'Spectral', Georgia, serif !important;
        overflow-x: hidden;
    }

    [data-testid="stHeader"] {
        background: transparent !important;
    }

    .block-container {
        max-width: 1280px !important;
        padding-top: 1.5rem !important;
        padding-bottom: 4rem !important;
    }

    /* Membrete Oficial Krov Industries */
    .krov-brand-row {
        display: flex;
        align-items: center;
        justify-content: space-between;
        border-bottom: 1px solid rgba(212, 175, 55, 0.2);
        padding-bottom: 0.6rem;
        margin-bottom: 1.2rem;
    }

    .krov-sigil {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.72rem;
        font-weight: 700;
        letter-spacing: 0.22em;
        color: #d4af37;
        text-transform: uppercase;
        display: flex;
        align-items: center;
        gap: 8px;
    }

    .krov-dot {
        width: 6px;
        height: 6px;
        background-color: #00f0ff;
        border-radius: 50%;
        box-shadow: 0 0 8px #00f0ff;
    }

    .krov-hero-title {
        font-family: 'Spectral', serif;
        font-size: 2.7rem;
        font-weight: 700;
        letter-spacing: -0.01em;
        background: linear-gradient(135deg, #ffffff 15%, #d4af37 55%, #f59e0b 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-shadow: 0 0 35px rgba(212, 175, 55, 0.35);
        margin: 0;
        line-height: 1.1;
    }

    .krov-hero-sub {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.8rem;
        letter-spacing: 0.12em;
        color: #94a3b8;
        text-transform: uppercase;
        margin-top: 6px;
        margin-bottom: 1.5rem;
    }

    .glow-card {
        background: rgba(10, 14, 24, 0.78);
        border: 1px solid rgba(212, 175, 55, 0.25);
        border-radius: 12px;
        padding: 22px;
        backdrop-filter: blur(16px);
        box-shadow: 0 14px 40px rgba(0, 0, 0, 0.75), inset 0 0 15px rgba(212, 175, 55, 0.04);
        transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
        margin-bottom: 16px;
    }

    .glow-card:hover {
        border-color: #d4af37;
        box-shadow: 0 18px 50px rgba(0, 0, 0, 0.9), 0 0 25px rgba(212, 175, 55, 0.2);
        transform: translateY(-2px);
    }

    .kpi-tile {
        background: rgba(8, 11, 18, 0.92);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-top: 3px solid #d4af37;
        border-radius: 8px;
        padding: 16px;
        text-align: center;
        transition: all 0.25s ease;
    }

    .kpi-tile:hover {
        border-color: #00f0ff;
        box-shadow: 0 0 20px rgba(0, 240, 255, 0.25);
        transform: translateY(-2px);
    }

    .kpi-val {
        font-family: 'Spectral', serif;
        font-size: 2.1rem;
        font-weight: 700;
        color: #ffffff;
    }

    .kpi-lbl {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.7rem;
        letter-spacing: 0.14em;
        color: #94a3b8;
        text-transform: uppercase;
        margin-top: 4px;
    }

    .stButton > button {
        background: linear-gradient(135deg, rgba(16, 21, 33, 0.95), rgba(8, 11, 18, 0.98)) !important;
        border: 1px solid rgba(212, 175, 55, 0.35) !important;
        border-radius: 8px !important;
        color: #f1f5f9 !important;
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 0.8rem !important;
        padding: 9px 16px !important;
        transition: all 0.25s ease !important;
        width: 100%;
    }

    .stButton > button:hover {
        border-color: #d4af37 !important;
        box-shadow: 0 0 20px rgba(212, 175, 55, 0.45) !important;
        transform: translateY(-2px);
        color: #d4af37 !important;
    }

    .stTextArea textarea {
        background: rgba(6, 9, 15, 0.95) !important;
        border: 1px solid rgba(212, 175, 55, 0.3) !important;
        border-radius: 8px !important;
        color: #f8fafc !important;
        font-family: 'Spectral', serif !important;
        font-size: 1.05rem !important;
        padding: 14px 18px !important;
        box-shadow: inset 0 0 20px rgba(0, 0, 0, 0.85) !important;
    }

    .stTextArea textarea:focus {
        border-color: #00f0ff !important;
        box-shadow: 0 0 20px rgba(0, 240, 255, 0.35) !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# -----------------------------------------------------------------------------
# LIENZO REACTIVO: CONSTELACIÓN DINÁMICA KROV
# -----------------------------------------------------------------------------
st.components.v1.html(
    """
    <script>
    (function() {
        const doc = window.parent.document;
        let canvas = doc.getElementById('krov-constellation-canvas');
        if (!canvas) {
            canvas = doc.createElement('canvas');
            canvas.id = 'krov-constellation-canvas';
            canvas.style.cssText = 'position:fixed;top:0;left:0;width:100vw;height:100vh;pointer-events:none;z-index:0;opacity:0.45;';
            doc.body.prepend(canvas);
        }
        const ctx = canvas.getContext('2d');
        let w = canvas.width = window.parent.innerWidth;
        let h = canvas.height = window.parent.innerHeight;

        window.parent.addEventListener('resize', () => {
            w = canvas.width = window.parent.innerWidth;
            h = canvas.height = window.parent.innerHeight;
        });

        const particles = [];
        let mouse = { x: -1000, y: -1000 };

        window.parent.addEventListener('mousemove', (e) => {
            mouse.x = e.clientX;
            mouse.y = e.clientY;
        });

        for (let i = 0; i < 48; i++) {
            particles.push({
                x: Math.random() * w,
                y: Math.random() * h,
                vx: (Math.random() - 0.5) * 0.35,
                vy: (Math.random() - 0.5) * 0.35,
                r: Math.random() * 1.6 + 0.8
            });
        }

        function loop() {
            ctx.clearRect(0, 0, w, h);
            for (let i = 0; i < particles.length; i++) {
                const p = particles[i];
                p.x += p.vx; p.y += p.vy;
                if (p.x < 0) p.x = w; if (p.x > w) p.x = 0;
                if (p.y < 0) p.y = h; if (p.y > h) p.y = 0;

                ctx.beginPath();
                ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
                ctx.fillStyle = '#d4af37';
                ctx.shadowBlur = 6;
                ctx.shadowColor = '#d4af37';
                ctx.fill();

                const dMouse = Math.hypot(p.x - mouse.x, p.y - mouse.y);
                if (dMouse < 130) {
                    ctx.beginPath();
                    ctx.moveTo(p.x, p.y);
                    ctx.lineTo(mouse.x, mouse.y);
                    ctx.strokeStyle = `rgba(0, 240, 255, ${1 - dMouse / 130})`;
                    ctx.lineWidth = 0.75;
                    ctx.stroke();
                }

                for (let j = i + 1; j < particles.length; j++) {
                    const p2 = particles[j];
                    const dist = Math.hypot(p.x - p2.x, p.y - p2.y);
                    if (dist < 95) {
                        ctx.beginPath();
                        ctx.moveTo(p.x, p.y);
                        ctx.lineTo(p2.x, p2.y);
                        ctx.strokeStyle = `rgba(212, 175, 55, ${(1 - dist / 95) * 0.2})`;
                        ctx.lineWidth = 0.5;
                        ctx.stroke();
                    }
                }
            }
            window.requestAnimationFrame(loop);
        }
        loop();
    })();
    </script>
    """,
    height=0,
    width=0
)

# -----------------------------------------------------------------------------
# MOTOR DE INFERENCIA SEMÁNTICA
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
        tono_nombre = "Inspirador y Persuasivo"
        tono_color = "#ffd700"
        tono_desc = "Tono marcadamente positivo con alta carga emocional. Idóneo para arengas, pitches y liderazgo motivacional."
    elif polaridad >= 0.1 and subjetividad < 0.4:
        tono_nombre = "Profesional y Constructivo"
        tono_color = "#00f0ff"
        tono_desc = "Perspectiva equilibrada y asertiva, fundamentada en hechos con balance formal de comunicación ejecutiva."
    elif polaridad <= -0.25 and subjetividad >= 0.45:
        tono_nombre = "Reclamo Severo / Frustración"
        tono_color = "#f43f5e"
        tono_desc = "Carga emocional crítica y contundente. Denota discrepancia frontal, inconformidad o apremio."
    elif polaridad <= -0.1 and subjetividad < 0.45:
        tono_nombre = "Observación Crítica Formal"
        tono_color = "#f59e0b"
        tono_desc = "Evaluación severa pero expuesta mediante parámetros técnicos y sobriedad argumentativa."
    elif subjetividad < 0.25:
        tono_nombre = "Reporte Técnico Objetivo"
        tono_color = "#94a3b8"
        tono_desc = "Alineación neutra y puramente descriptiva. Exento de sesgos u opiniones individuales."
    else:
        tono_nombre = "Discurso Coloquial Equilibrado"
        tono_color = "#c084fc"
        tono_desc = "Intercambio fluido de impresiones personales y hechos concretos de forma mesurada."

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


def plot_speedometer(valor, titulo, rango, color_linea):
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=valor,
        number={"font": {"family": "Spectral", "size": 32, "color": "#ffffff"}},
        title={"text": titulo, "font": {"family": "JetBrains Mono", "size": 11, "color": color_linea}},
        gauge={
            "axis": {"range": rango, "tickwidth": 1, "tickcolor": "rgba(255,255,255,0.25)"},
            "bar": {"color": color_linea, "thickness": 0.24},
            "bgcolor": "rgba(0,0,0,0.45)",
            "borderwidth": 1,
            "bordercolor": "rgba(255,255,255,0.08)",
        }
    ))
    fig.update_layout(
        height=210,
        margin=dict(l=20, r=20, t=35, b=20),
        paper_bgcolor="rgba(0,0,0,0)",
        font={"color": "#e2e8f0"}
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
        line=dict(color="#00f0ff", width=2.5, shape="spline"),
        marker=dict(size=7, color="#d4af37", line=dict(width=1.5, color="#05060a")),
        hovertemplate="<b>Frase %{x}</b><br>Polaridad: %{y:.2f}<extra></extra>"
    ))
    fig.add_hline(y=0, line_dash="dash", line_color="rgba(255,255,255,0.25)")
    fig.update_layout(
        title="<b>Evolución Secuencial del Tono</b>",
        title_font=dict(family="Spectral", size=13, color="#d4af37"),
        xaxis_title="Secuencia de Oraciones",
        yaxis_title="Índice Emocional (-1 a +1)",
        height=250,
        margin=dict(l=35, r=20, t=40, b=35),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(10, 14, 24, 0.7)",
        font=dict(family="JetBrains Mono", color="#94a3b8", size=9),
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

    categorias = ["Positividad", "Objetividad", "Riqueza Léxica", "Estabilidad", "Intensidad"]
    valores = [pos_score, obj_score, lex_score, claridad_score, impacto_score]
    valores += valores[:1]
    categorias += categorias[:1]

    fig = go.Figure(go.Scatterpolar(
        r=valores,
        theta=categorias,
        fill="toself",
        fillcolor="rgba(212, 175, 55, 0.18)",
        line=dict(color="#d4af37", width=1.8),
        marker=dict(size=5, color="#00f0ff"),
    ))
    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 100], gridcolor="rgba(255,255,255,0.06)"),
            angularaxis=dict(gridcolor="rgba(255,255,255,0.06)"),
            bgcolor="rgba(0,0,0,0)"
        ),
        title="<b>Equilibrio Estructural del Discurso</b>",
        title_font=dict(family="Spectral", size=13, color="#d4af37"),
        height=250,
        margin=dict(l=35, r=35, t=40, b=30),
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="JetBrains Mono", color="#94a3b8", size=9)
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
        marker=dict(
            color=conteos,
            colorscale=[[0, "#00f0ff"], [1, "#d4af37"]],
            line=dict(color="#ffffff", width=0.8)
        ),
        hovertemplate="Término: <b>%{y}</b><br>Ocurrencias: %{x}<extra></extra>"
    ))
    fig.update_layout(
        title="<b>Términos Clave Recurrentes</b>",
        title_font=dict(family="Spectral", size=13, color="#d4af37"),
        height=250,
        margin=dict(l=40, r=20, t=40, b=20),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="JetBrains Mono", color="#94a3b8", size=9),
        xaxis=dict(gridcolor="rgba(255,255,255,0.05)"),
        yaxis=dict(gridcolor="rgba(255,255,255,0.0)")
    )
    return fig


PRESETS = {
    "pitch": (
        "Equipo, alcanzamos un rendimiento sobresaliente este trimestre. Superamos holgadamente "
        "las metas iniciales gracias a una disciplina impecable. Esto valida con certeza la solidez de nuestra visión. "
        "Mantengamos esta aceleración decidida para consolidar el liderazgo en el mercado."
    ),
    "crisis": (
        "Reconocemos plenamente la gravedad de la incidencia registrada esta mañana en la infraestructura central. "
        "Asumimos total responsabilidad por el impacto generado y hemos activado los protocolos de mitigación inmediata. "
        "El equipo técnico trabaja sin interrupción para restituir la operatividad con absoluta transparencia."
    ),
    "reclamo": (
        "Manifiesto mi profunda inconformidad ante la reiterada deficiencia del servicio contratado. "
        "Es inaceptable que tras dos semanas de demora continúe sin obtener una resolución fundamentada. "
        "El paquete remitido no cumple con los estándares pactados. Exijo la devolución íntegra de los fondos hoy mismo."
    ),
    "tecnico": (
        "La arquitectura distribuye la carga mediante una cola asíncrona de mensajes desacoplados. "
        "La latencia percentil registrada en los nodos perimetrales se mantiene estable en doce milisegundos. "
        "El consumo de memoria no excede el umbral nominal bajo demanda intensiva del setenta por ciento. "
        "Los respaldos criptográficos se consolidan cada seis horas de manera automatizada."
    )
}

if "texto_activo" not in st.session_state:
    st.session_state.texto_activo = PRESETS["pitch"]

def cargar_preset(key):
    st.session_state.texto_activo = PRESETS[key]


# -----------------------------------------------------------------------------
# CABECERA Y CONTROLADORES
# -----------------------------------------------------------------------------
render_clean_html(
    """
    <div>
        <div class="krov-brand-row">
            <span class="krov-sigil"><span class="krov-dot"></span> KROV INDUSTRIES // COGNITIVE LABS</span>
            <span style="font-family:'JetBrains Mono'; font-size:0.72rem; color:#94a3b8;">SYS.REF: SEMANTIC-V5</span>
        </div>
        <h1 class="krov-hero-title">Analizador Semántico // Actitud, Tono y Claridad</h1>
        <div class="krov-hero-sub">Diagnóstico formal de la tonalidad, estabilidad emocional y riqueza discursiva</div>
    </div>
    """
)

st.markdown("<p style='font-size:0.8rem; color:#94a3b8; margin-bottom:6px;'>Casos de evaluación inmediata:</p>", unsafe_allow_html=True)
c_p1, c_p2, c_p3, c_p4 = st.columns(4)
with c_p1:
    if st.button("🚀 Motivación / Pitch", use_container_width=True):
        cargar_preset("pitch")
        st.rerun()
with c_p2:
    if st.button("⚠️ Manejo de Crisis", use_container_width=True):
        cargar_preset("crisis")
        st.rerun()
with c_p3:
    if st.button("🛑 Reclamo Severo", use_container_width=True):
        cargar_preset("reclamo")
        st.rerun()
with c_p4:
    if st.button("📋 Reporte Técnico", use_container_width=True):
        cargar_preset("tecnico")
        st.rerun()

st.write("")
col_in, col_opts = st.columns([3.2, 1], gap="medium")

with col_in:
    texto_usuario = st.text_area(
        label="Texto a someter a evaluación:",
        value=st.session_state.texto_activo,
        height=160,
        placeholder="Redacta o inserta aquí el comunicado, memorando o documento..."
    )

with col_opts:
    st.markdown('<div class="glow-card" style="padding: 16px;">', unsafe_allow_html=True)
    st.markdown("<p style='font-size:0.72rem; color:#d4af37; margin:0 0 6px 0; font-family:JetBrains Mono;'>ORIGEN DE DATOS</p>", unsafe_allow_html=True)
    modo_subida = st.radio("Fuente:", ["Edición manual", "Subir archivo"], horizontal=True, label_visibility="collapsed")
    archivo_subido = None
    if modo_subida == "Subir archivo":
        archivo_subido = st.file_uploader("Documento (.txt, .md, .csv)", type=["txt", "md", "csv"])

    target_lang = st.selectbox(
        label="Traducir oraciones a:",
        options=["en", "es", "fr", "ja", "de", "it", "pt"],
        format_func=lambda c: {"en": "Inglés", "es": "Español", "fr": "Francés", "ja": "Japonés", "de": "Alemán", "it": "Italiano", "pt": "Portugués"}.get(c, c),
        index=0
    )
    st.markdown("</div>", unsafe_allow_html=True)

if archivo_subido is not None:
    try:
        texto_usuario = archivo_subido.getvalue().decode("utf-8")
    except Exception as e:
        st.error(f"Inconveniente al procesar el archivo: {e}")

if texto_usuario and len(texto_usuario.strip()) > 3:
    with st.spinner("Decodificando armónicos semánticos y volatilidad léxica..."):
        res = analizar_texto_profundo(texto_usuario)

    render_clean_html(
        f"""
        <div class="glow-card" style="border-left: 5px solid {res['tono_color']};">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">
                <span style="font-family:'JetBrains Mono'; font-size:0.75rem; color:{res['tono_color']}; letter-spacing:1px; text-transform:uppercase;">
                    DIAGNÓSTICO ESTRUCTURAL
                </span>
                <span style="font-family:'JetBrains Mono'; font-size:0.75rem; color:#94a3b8; background:rgba(0,0,0,0.6); padding:3px 10px; border-radius:12px; border:1px solid rgba(255,255,255,0.1);">
                    Dispersión volátil: {res['volatilidad']}
                </span>
            </div>
            <h2 style="font-family:'Spectral'; font-size:1.85rem; margin:0 0 6px 0; color:#ffffff;">
                {res['tono_nombre']}
            </h2>
            <p style="color:#cbd5e1; font-size:0.95rem; margin:0; line-height:1.5;">
                {res['tono_desc']}
            </p>
        </div>
        """
    )

    min_l = res["tiempo_lectura_seg"] // 60
    seg_l = res["tiempo_lectura_seg"] % 60
    min_o = res["tiempo_oratoria_seg"] // 60
    seg_o = res["tiempo_oratoria_seg"] % 60

    k_cols = st.columns(5)
    with k_cols[0]:
        st.markdown(f'<div class="kpi-tile"><div class="kpi-val">{res["total_palabras"]}</div><div class="kpi-lbl">Palabras</div></div>', unsafe_allow_html=True)
    with k_cols[1]:
        st.markdown(f'<div class="kpi-tile"><div class="kpi-val">{res["diversidad_lexica"]}%</div><div class="kpi-lbl">Riqueza Léxica</div></div>', unsafe_allow_html=True)
    with k_cols[2]:
        st.markdown(f'<div class="kpi-tile"><div class="kpi-val">{len(res["trayectoria"])}</div><div class="kpi-lbl">Oraciones</div></div>', unsafe_allow_html=True)
    with k_cols[3]:
        st.markdown(f'<div class="kpi-tile"><div class="kpi-val">{min_l}m {seg_l}s</div><div class="kpi-lbl">Lectura</div></div>', unsafe_allow_html=True)
    with k_cols[4]:
        st.markdown(f'<div class="kpi-tile"><div class="kpi-val">{min_o}m {seg_o}s</div><div class="kpi-lbl">Oratoria</div></div>', unsafe_allow_html=True)

    st.write("")
    tab_g, tab_f, tab_s = st.tabs(["Telemetría y Gráficos", "Secuencia Textual y Traducción", "Optimización del Discurso"])

    with tab_g:
        g1, g2 = st.columns(2)
        with g1:
            st.markdown('<div class="glow-card">', unsafe_allow_html=True)
            p_col = "#00f0ff" if res["polaridad"] > 0.05 else ("#f43f5e" if res["polaridad"] < -0.05 else "#d4af37")
            st.plotly_chart(plot_speedometer(res["polaridad"], "Polaridad (-1 negativo a +1 positivo)", [-1, 1], p_col), use_container_width=True, config={"displayModeBar": False})
            st.markdown("</div>", unsafe_allow_html=True)
        with g2:
            st.markdown('<div class="glow-card">', unsafe_allow_html=True)
            s_col = "#c084fc" if res["subjetividad"] > 0.5 else "#d4af37"
            st.plotly_chart(plot_speedometer(res["subjetividad"], "Subjetividad (0 hechos a 1 opinión)", [0, 1], s_col), use_container_width=True, config={"displayModeBar": False})
            st.markdown("</div>", unsafe_allow_html=True)

        st.markdown('<div class="glow-card">', unsafe_allow_html=True)
        fig_t = plot_trayectoria_emocional(res["trayectoria"])
        if fig_t:
            st.plotly_chart(fig_t, use_container_width=True, config={"displayModeBar": False})
        else:
            st.info("Estructura al menos dos oraciones separadas por punto para trazar la curva emocional.")
        st.markdown("</div>", unsafe_allow_html=True)

        r1, r2 = st.columns(2)
        with r1:
            st.markdown('<div class="glow-card">', unsafe_allow_html=True)
            st.plotly_chart(plot_radar_dimensiones(res), use_container_width=True, config={"displayModeBar": False})
            st.markdown("</div>", unsafe_allow_html=True)
        with r2:
            st.markdown('<div class="glow-card">', unsafe_allow_html=True)
            fig_b = plot_barras_frecuencia(res["frecuencia"])
            if fig_b:
                st.plotly_chart(fig_b, use_container_width=True, config={"displayModeBar": False})
            else:
                st.info("No se hallaron suficientes términos filtrados para la frecuencia.")
            st.markdown("</div>", unsafe_allow_html=True)

    with tab_f:
        st.markdown("<p style='font-size:0.85rem; color:#94a3b8;'>Desglose analítico por frase registrada:</p>", unsafe_allow_html=True)
        for item in res["trayectoria"]:
            p = item["polaridad"]
            s = item["subjetividad"]
            b_col = "#00f0ff" if p > 0.05 else ("#f43f5e" if p < -0.05 else "#d4af37")
            b_icon = "Positiva" if p > 0.05 else ("Negativa" if p < -0.05 else "Neutra")
            tr_frase = traducir_a_idioma(item["es"], target_lang) if target_lang != "es" else item["en"]

            safe_es = html.escape(item["es"])
            safe_tr = html.escape(tr_frase)

            render_clean_html(
                f"""
                <div style="background:rgba(10,13,22,0.92); border:1px solid rgba(255,255,255,0.08); border-left:4px solid {b_col}; border-radius:8px; padding:12px 16px; margin-bottom:8px;">
                    <div style="display:flex; justify-content:space-between; font-size:0.75rem; font-family:'JetBrains Mono'; margin-bottom:4px;">
                        <span style="color:#d4af37;">Secuencia #{item['idx']}</span>
                        <span style="color:{b_col}; font-weight:600;">{b_icon} (Tono: {p:+.2f} | Opinión: {s:.2f})</span>
                    </div>
                    <div style="font-size:1rem; color:#ffffff; margin-bottom:4px; font-family:'Spectral';">
                        «{safe_es}»
                    </div>
                    <div style="font-size:0.82rem; color:#94a3b8; font-family:'JetBrains Mono';">
                        🌐 [{target_lang.upper()}]: {safe_tr}
                    </div>
                </div>
                """
            )

    with tab_s:
        st.markdown("### Recomendaciones Semánticas Krov")
        tips = []
        if res["polaridad"] < -0.15:
            tips.append(("Atenuar la reactividad frontal", "El mensaje proyecta fricción o descontento severo. Si el propósito es concertar una solución técnica, prioriza peticiones delimitadas sobre adjetivos punitivos."))
        elif res["polaridad"] > 0.4:
            tips.append(("Canalizar el ímpetu afirmativo", "El discurso emite notable energía favorable. Conviene rematar con una directriz o llamado concreto a la acción para capitalizar el entusiasmo."))

        if res["subjetividad"] > 0.6:
            tips.append(("Respaldar premisas con métricas", f"Aproximadamente el {int(res['subjetividad']*100)}% del texto consiste en apreciaciones subjetivas. Incorporar parámetros cuantificables incrementará el rigor argumentativo."))
        elif res["subjetividad"] < 0.25:
            tips.append(("Aportar calidez interpersonal", "La redacción es distante y aséptica. En comunicaciones generales, añadir un breve marco contextual humanizará el vínculo sin restar claridad."))

        if res["volatilidad"] > 0.4:
            tips.append(("Homogeneizar transiciones", f"Se detectaron oscilaciones abruptas de tono (índice {res['volatilidad']}). Emplea conectores lógicos más fluidos entre párrafos para evitar quiebres de lectura."))

        if res["diversidad_lexica"] < 40:
            tips.append(("Diversificar el léxico técnico", f"El índice léxico se sitúa en {res['diversidad_lexica']}%. Sustituir vocablos redundantes por variantes de alta precisión jerarquizará la redacción."))

        for t_tit, t_desc in tips:
            render_clean_html(
                f"""
                <div style="background:rgba(212,175,55,0.05); border:1px solid rgba(212,175,55,0.22); border-radius:8px; padding:14px; margin-bottom:10px;">
                    <div style="font-family:'Spectral'; font-size:1.05rem; color:#d4af37; font-weight:700; margin-bottom:2px;">
                        {t_tit}
                    </div>
                    <div style="font-size:0.92rem; color:#e2e8f0; line-height:1.5;">
                        {t_desc}
                    </div>
                </div>
                """
            )
else:
    st.info("Ingresa un texto en el área superior o pulsa cualquiera de los casos prácticos para desplegar el diagnóstico semántico.")
