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
# CONFIGURACIÓN
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Analizador de Texto // Tono y Emociones",
    page_icon="⚜",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# -----------------------------------------------------------------------------
# ESTILOS OVER-THE-TOP: GÓTICO NOIR & NEÓN
# -----------------------------------------------------------------------------
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Spectral:ital,wght@0,300;0,400;0,600;0,700;1,400&family=JetBrains+Mono:wght@400;600;700&display=swap');

    html, body, [data-testid="stAppViewContainer"] {
        background: radial-gradient(circle at 50% 20%, #0d111a 0%, #05060a 60%, #020204 100%) !important;
        color: #f1f5f9 !important;
        font-family: 'Spectral', Georgia, serif !important;
        overflow-x: hidden;
    }

    [data-testid="stHeader"] {
        background: transparent !important;
    }

    .block-container {
        max-width: 1240px !important;
        padding-top: 1.8rem !important;
        padding-bottom: 3rem !important;
    }

    /* Título con gradiente dinámico y resplandor */
    .hero-title {
        font-family: 'Spectral', serif;
        font-size: 2.8rem;
        font-weight: 700;
        letter-spacing: -0.02em;
        background: linear-gradient(135deg, #ffffff 10%, #ffd700 50%, #ff8800 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-shadow: 0 0 30px rgba(255, 215, 0, 0.4);
        margin: 0;
        line-height: 1.1;
    }

    .hero-sub {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.8rem;
        letter-spacing: 0.15em;
        color: #00f0ff;
        text-transform: uppercase;
        margin-top: 6px;
        margin-bottom: 1.5rem;
        text-shadow: 0 0 10px rgba(0, 240, 255, 0.5);
    }

    /* Tarjetas con cristal y bordes de oro reactivo */
    .glow-card {
        background: rgba(13, 16, 26, 0.8);
        border: 1px solid rgba(255, 215, 0, 0.25);
        border-radius: 12px;
        padding: 22px;
        backdrop-filter: blur(16px);
        box-shadow: 0 12px 40px rgba(0, 0, 0, 0.7), 0 0 20px rgba(255, 215, 0, 0.08);
        transition: all 0.3s ease;
        margin-bottom: 16px;
    }

    .glow-card:hover {
        border-color: #ffd700;
        box-shadow: 0 18px 50px rgba(0, 0, 0, 0.9), 0 0 30px rgba(255, 215, 0, 0.25);
        transform: translateY(-3px);
    }

    /* KPIs */
    .kpi-tile {
        background: rgba(10, 13, 22, 0.9);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-top: 3px solid #ffd700;
        border-radius: 8px;
        padding: 16px;
        text-align: center;
        transition: all 0.3s ease;
    }

    .kpi-tile:hover {
        border-color: #00f0ff;
        box-shadow: 0 0 20px rgba(0, 240, 255, 0.3);
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
        font-size: 0.72rem;
        letter-spacing: 0.12em;
        color: #94a3b8;
        text-transform: uppercase;
        margin-top: 4px;
    }

    /* Botones reactivos */
    .stButton > button {
        background: linear-gradient(135deg, rgba(20, 24, 38, 0.9), rgba(10, 12, 20, 0.95)) !important;
        border: 1.5px solid rgba(255, 215, 0, 0.35) !important;
        border-radius: 8px !important;
        color: #ffffff !important;
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 0.82rem !important;
        padding: 9px 18px !important;
        transition: all 0.25s ease !important;
    }

    .stButton > button:hover {
        border-color: #ffd700 !important;
        box-shadow: 0 0 25px rgba(255, 215, 0, 0.5), inset 0 0 10px rgba(255, 215, 0, 0.2) !important;
        transform: translateY(-2px) scale(1.02) !important;
        color: #ffd700 !important;
    }

    .stTextArea textarea {
        background: rgba(8, 11, 18, 0.95) !important;
        border: 1.5px solid rgba(255, 215, 0, 0.25) !important;
        border-radius: 8px !important;
        color: #ffffff !important;
        font-family: 'Spectral', serif !important;
        font-size: 1.05rem !important;
        padding: 14px 18px !important;
        box-shadow: inset 0 0 20px rgba(0, 0, 0, 0.8) !important;
    }

    .stTextArea textarea:focus {
        border-color: #00f0ff !important;
        box-shadow: 0 0 20px rgba(0, 240, 255, 0.4) !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# -----------------------------------------------------------------------------
# LIENZO INTERACTIVO: CONSTELACIÓN Y ESTELA REACTIVA
# -----------------------------------------------------------------------------
st.components.v1.html(
    """
    <script>
    (function() {
        const doc = window.parent.document;
        let canvas = doc.getElementById('noir-bg-canvas');
        if (!canvas) {
            canvas = doc.createElement('canvas');
            canvas.id = 'noir-bg-canvas';
            canvas.style.cssText = 'position:fixed;top:0;left:0;width:100vw;height:100vh;pointer-events:none;z-index:0;opacity:0.6;';
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
        const trail = [];
        let mouse = { x: -1000, y: -1000 };

        window.parent.addEventListener('mousemove', (e) => {
            mouse.x = e.clientX;
            mouse.y = e.clientY;
            for (let i = 0; i < 2; i++) {
                trail.push({
                    x: e.clientX,
                    y: e.clientY,
                    vx: (Math.random() - 0.5) * 1.5,
                    vy: (Math.random() - 0.5) * 1.5,
                    life: 1.0
                });
            }
        });

        for (let i = 0; i < 50; i++) {
            particles.push({
                x: Math.random() * w,
                y: Math.random() * h,
                vx: (Math.random() - 0.5) * 0.4,
                vy: (Math.random() - 0.5) * 0.4,
                r: Math.random() * 1.8 + 0.8
            });
        }

        function loop() {
            ctx.clearRect(0, 0, w, h);

            // Nodos
            for (let i = 0; i < particles.length; i++) {
                const p = particles[i];
                p.x += p.vx; p.y += p.vy;
                if (p.x < 0) p.x = w; if (p.x > w) p.x = 0;
                if (p.y < 0) p.y = h; if (p.y > h) p.y = 0;

                ctx.beginPath();
                ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
                ctx.fillStyle = '#ffd700';
                ctx.shadowBlur = 8;
                ctx.shadowColor = '#ffd700';
                ctx.fill();

                const dMouse = Math.hypot(p.x - mouse.x, p.y - mouse.y);
                if (dMouse < 120) {
                    ctx.beginPath();
                    ctx.moveTo(p.x, p.y);
                    ctx.lineTo(mouse.x, mouse.y);
                    ctx.strokeStyle = `rgba(0, 240, 255, ${1 - dMouse / 120})`;
                    ctx.lineWidth = 0.8;
                    ctx.stroke();
                }

                for (let j = i + 1; j < particles.length; j++) {
                    const p2 = particles[j];
                    const dist = Math.hypot(p.x - p2.x, p.y - p2.y);
                    if (dist < 100) {
                        ctx.beginPath();
                        ctx.moveTo(p.x, p.y);
                        ctx.lineTo(p2.x, p2.y);
                        ctx.strokeStyle = `rgba(255, 215, 0, ${(1 - dist / 100) * 0.25})`;
                        ctx.lineWidth = 0.6;
                        ctx.stroke();
                    }
                }
            }

            // Estela
            for (let i = trail.length - 1; i >= 0; i--) {
                const t = trail[i];
                t.x += t.vx; t.y += t.vy;
                t.life -= 0.03;
                if (t.life <= 0) { trail.splice(i, 1); continue; }
                ctx.beginPath();
                ctx.arc(t.x, t.y, 2 * t.life, 0, Math.PI * 2);
                ctx.fillStyle = `rgba(0, 240, 255, ${t.life})`;
                ctx.shadowBlur = 10;
                ctx.shadowColor = '#00f0ff';
                ctx.fill();
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
# ANÁLISIS
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
        tono_desc = "Tono muy positivo con alta emoción personal. Ideal para motivar equipos o presentar propuestas comerciales."
    elif polaridad >= 0.1 and subjetividad < 0.4:
        tono_nombre = "Profesional y Constructivo"
        tono_color = "#00f0ff"
        tono_desc = "Enfoque claro y optimista, respaldado en hechos y con excelente balance corporativo."
    elif polaridad <= -0.25 and subjetividad >= 0.45:
        tono_nombre = "Reclamo Severo / Frustración"
        tono_color = "#ff0055"
        tono_desc = "Carga emocional negativa alta. Expresa inconformidad frontal, enojo o desacuerdo tajante."
    elif polaridad <= -0.1 and subjetividad < 0.45:
        tono_nombre = "Observación Crítica Formal"
        tono_color = "#ffaa00"
        tono_desc = "Evaluación desfavorable pero explicada con sobriedad y fundamentos técnicos."
    elif subjetividad < 0.25:
        tono_nombre = "Reporte Técnico Objetivo"
        tono_color = "#94a3b8"
        tono_desc = "Completamente neutral y libre de opiniones personales. Óptimo para documentación y manuales."
    else:
        tono_nombre = "Conversación Equilibrada"
        tono_color = "#c084fc"
        tono_desc = "Mezcla casual de impresiones personales con hechos de forma balanceada."

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
        title={"text": titulo, "font": {"family": "JetBrains Mono", "size": 12, "color": color_linea}},
        gauge={
            "axis": {"range": rango, "tickwidth": 1, "tickcolor": "rgba(255,255,255,0.3)"},
            "bar": {"color": color_linea, "thickness": 0.25},
            "bgcolor": "rgba(0,0,0,0.5)",
            "borderwidth": 1,
            "bordercolor": "rgba(255,255,255,0.1)",
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
        line=dict(color="#00f0ff", width=3, shape="spline"),
        marker=dict(size=8, color="#ffd700", line=dict(width=2, color="#05060a")),
        hovertemplate="<b>Oración %{x}</b><br>Tono: %{y:.2f}<extra></extra>"
    ))
    fig.add_hline(y=0, line_dash="dash", line_color="rgba(255,255,255,0.3)")
    fig.update_layout(
        title="<b>Evolución del Tono por Oración</b>",
        title_font=dict(family="Spectral", size=14, color="#ffd700"),
        xaxis_title="Secuencia de Frases",
        yaxis_title="De Negativo (-1) a Positivo (+1)",
        height=260,
        margin=dict(l=35, r=20, t=40, b=35),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(10, 14, 24, 0.7)",
        font=dict(family="JetBrains Mono", color="#94a3b8", size=10),
        xaxis=dict(gridcolor="rgba(255,255,255,0.06)", tickmode="linear"),
        yaxis=dict(gridcolor="rgba(255,255,255,0.06)", range=[-1.05, 1.05]),
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
        fillcolor="rgba(255, 215, 0, 0.2)",
        line=dict(color="#ffd700", width=2),
        marker=dict(size=6, color="#00f0ff"),
    ))
    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 100], gridcolor="rgba(255,255,255,0.08)"),
            angularaxis=dict(gridcolor="rgba(255,255,255,0.08)"),
            bgcolor="rgba(0,0,0,0)"
        ),
        title="<b>Equilibrio General del Mensaje</b>",
        title_font=dict(family="Spectral", size=14, color="#ffd700"),
        height=260,
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
            colorscale=[[0, "#00f0ff"], [1, "#ffd700"]],
            line=dict(color="#ffffff", width=1)
        ),
        hovertemplate="Palabra: <b>%{y}</b><br>Frecuencia: %{x}<extra></extra>"
    ))
    fig.update_layout(
        title="<b>Palabras Más Usadas</b>",
        title_font=dict(family="Spectral", size=14, color="#ffd700"),
        height=260,
        margin=dict(l=40, r=20, t=40, b=20),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="JetBrains Mono", color="#94a3b8", size=10),
        xaxis=dict(gridcolor="rgba(255,255,255,0.06)"),
        yaxis=dict(gridcolor="rgba(255,255,255,0.0)")
    )
    return fig


PRESETS = {
    "pitch": (
        "¡Equipo, logramos un resultado extraordinario este trimestre! Superamos todas las proyecciones "
        "gracias a su dedicación y constancia. Esto confirma que la visión que trazamos es la correcta. "
        "Sigamos acelerando con este mismo entusiasmo para liderar nuestro sector."
    ),
    "crisis": (
        "Lamentamos profundamente los fallos técnicos ocurridos durante la mañana de hoy. "
        "Reconocemos el impacto negativo para nuestros clientes y asumimos total responsabilidad. "
        "El equipo implementó un plan de contingencia inmediato y auditorías continuas para resolverlo. "
        "Mantendremos informada a la comunidad con absoluta transparencia."
    ),
    "reclamo": (
        "Estoy muy molesto con la mala atención recibida. Es inaceptable que tras dos semanas de retraso "
        "nadie brinde una respuesta clara ni una solución concreta. El producto llegó defectuoso "
        "y el servicio al cliente fue pésimo. Exijo el reembolso de mi dinero hoy mismo."
    ),
    "tecnico": (
        "El sistema distribuye paquetes mediante una cola asíncrona de mensajes. "
        "La latencia promedio registrada en los nodos perimetrales se mantiene en doce milisegundos. "
        "El consumo de memoria permanece estable bajo una carga operativa del setenta por ciento. "
        "Las copias de seguridad se generan automáticamente cada seis horas."
    )
}

if "texto_activo" not in st.session_state:
    st.session_state.texto_activo = PRESETS["pitch"]

def cargar_preset(key):
    st.session_state.texto_activo = PRESETS[key]


# -----------------------------------------------------------------------------
# INTERFAZ
# -----------------------------------------------------------------------------
render_clean_html(
    """
    <div>
        <h1 class="hero-title">Analizador de Texto // Tono y Emociones</h1>
        <div class="hero-sub">Evaluación directa de actitud, claridad y vocabulario en cualquier mensaje</div>
    </div>
    """
)

st.markdown("<p style='font-size:0.85rem; color:#94a3b8; margin-bottom:8px;'>Prueba con un caso rápido:</p>", unsafe_allow_html=True)
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
    if st.button("🛑 Reclamo Fuerte", use_container_width=True):
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
        label="Escribe o pega aquí el texto a evaluar:",
        value=st.session_state.texto_activo,
        height=160,
        placeholder="Pega un correo, discurso, artículo o reclamo..."
    )

with col_opts:
    st.markdown('<div class="glow-card" style="padding: 16px;">', unsafe_allow_html=True)
    st.markdown("<p style='font-size:0.75rem; color:#ffd700; margin:0 0 8px 0; font-family:JetBrains Mono;'>ORIGEN</p>", unsafe_allow_html=True)
    modo_subida = st.radio("Fuente:", ["Escribir texto", "Subir archivo"], horizontal=True, label_visibility="collapsed")
    archivo_subido = None
    if modo_subida == "Subir archivo":
        archivo_subido = st.file_uploader("Archivo (.txt, .md, .csv)", type=["txt", "md", "csv"])

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
        st.error(f"Error al leer archivo: {e}")

if texto_usuario and len(texto_usuario.strip()) > 3:
    with st.spinner("Procesando tono y vocabulario..."):
        res = analizar_texto_profundo(texto_usuario)

    render_clean_html(
        f"""
        <div class="glow-card" style="border-left: 5px solid {res['tono_color']};">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">
                <span style="font-family:'JetBrains Mono'; font-size:0.75rem; color:{res['tono_color']}; letter-spacing:1px; text-transform:uppercase;">
                    DIAGNÓSTICO PRINCIPAL
                </span>
                <span style="font-family:'JetBrains Mono'; font-size:0.75rem; color:#94a3b8; background:rgba(0,0,0,0.5); padding:3px 10px; border-radius:12px; border:1px solid rgba(255,255,255,0.1);">
                    Variación emocional: {res['volatilidad']}
                </span>
            </div>
            <h2 style="font-family:'Spectral'; font-size:1.8rem; margin:0 0 6px 0; color:#ffffff;">
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
        st.markdown(f'<div class="kpi-tile"><div class="kpi-val">{res["diversidad_lexica"]}%</div><div class="kpi-lbl">Vocabulario Único</div></div>', unsafe_allow_html=True)
    with k_cols[2]:
        st.markdown(f'<div class="kpi-tile"><div class="kpi-val">{len(res["trayectoria"])}</div><div class="kpi-lbl">Oraciones</div></div>', unsafe_allow_html=True)
    with k_cols[3]:
        st.markdown(f'<div class="kpi-tile"><div class="kpi-val">{min_l}m {seg_l}s</div><div class="kpi-lbl">Lectura</div></div>', unsafe_allow_html=True)
    with k_cols[4]:
        st.markdown(f'<div class="kpi-tile"><div class="kpi-val">{min_o}m {seg_o}s</div><div class="kpi-lbl">Al Hablar</div></div>', unsafe_allow_html=True)

    st.write("")
    tab_g, tab_f, tab_s = st.tabs(["Telemetría y Gráficos", "Frase por Frase y Traducción", "Sugerencias Prácticas"])

    with tab_g:
        g1, g2 = st.columns(2)
        with g1:
            st.markdown('<div class="glow-card">', unsafe_allow_html=True)
            p_col = "#00f0ff" if res["polaridad"] > 0.05 else ("#ff0055" if res["polaridad"] < -0.05 else "#ffd700")
            st.plotly_chart(plot_speedometer(res["polaridad"], "Sentimiento (-1 negativo a +1 positivo)", [-1, 1], p_col), use_container_width=True, config={"displayModeBar": False})
            st.markdown("</div>", unsafe_allow_html=True)
        with g2:
            st.markdown('<div class="glow-card">', unsafe_allow_html=True)
            s_col = "#c084fc" if res["subjetividad"] > 0.5 else "#ffd700"
            st.plotly_chart(plot_speedometer(res["subjetividad"], "Subjetividad (0 objetivo a 1 opinión)", [0, 1], s_col), use_container_width=True, config={"displayModeBar": False})
            st.markdown("</div>", unsafe_allow_html=True)

        st.markdown('<div class="glow-card">', unsafe_allow_html=True)
        fig_t = plot_trayectoria_emocional(res["trayectoria"])
        if fig_t:
            st.plotly_chart(fig_t, use_container_width=True, config={"displayModeBar": False})
        else:
            st.info("Escribe al menos dos oraciones separadas por punto para graficar la evolución.")
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
                st.info("No hay suficientes palabras clave filtradas.")
            st.markdown("</div>", unsafe_allow_html=True)

    with tab_f:
        st.markdown("<p style='font-size:0.85rem; color:#94a3b8;'>Desglose secuencial de cada oración detectada:</p>", unsafe_allow_html=True)
        for item in res["trayectoria"]:
            p = item["polaridad"]
            s = item["subjetividad"]
            b_col = "#00f0ff" if p > 0.05 else ("#ff0055" if p < -0.05 else "#ffd700")
            b_icon = "Positiva" if p > 0.05 else ("Negativa" if p < -0.05 else "Neutra")
            tr_frase = traducir_a_idioma(item["es"], target_lang) if target_lang != "es" else item["en"]

            render_clean_html(
                f"""
                <div style="background:rgba(12,15,24,0.9); border:1px solid rgba(255,255,255,0.08); border-left:4px solid {b_col}; border-radius:8px; padding:12px 16px; margin-bottom:8px;">
                    <div style="display:flex; justify-content:space-between; font-size:0.75rem; font-family:'JetBrains Mono'; margin-bottom:4px;">
                        <span style="color:#ffd700;">Oración #{item['idx']}</span>
                        <span style="color:{b_col}; font-weight:600;">{b_icon} (Tono: {p:+.2f} | Opinión: {s:.2f})</span>
                    </div>
                    <div style="font-size:1rem; color:#ffffff; margin-bottom:4px; font-family:'Spectral';">
                        «{item['es']}»
                    </div>
                    <div style="font-size:0.82rem; color:#94a3b8; font-family:'JetBrains Mono';">
                        🌐 [{target_lang.upper()}]: {tr_frase}
                    </div>
                </div>
                """
            )

    with tab_s:
        st.markdown("### Recomendaciones para mejorar este texto")
        tips = []
        if res["polaridad"] < -0.15:
            tips.append(("Moderar el tono negativo", "El texto contiene alta hostilidad. Si tu meta es negociar o solucionar un desacuerdo, solicita acciones puntuales en vez de solo quejarte."))
        elif res["polaridad"] > 0.4:
            tips.append(("Aprovechar el entusiasmo", "Tu mensaje transmite mucha energía. Asegúrate de cerrar con una llamada clara a la acción antes de terminar."))

        if res["subjetividad"] > 0.6:
            tips.append(("Sumar datos verificables", f"El {int(res['subjetividad']*100)}% del texto son impresiones u opiniones personales. Acompañar tus afirmaciones con cifras le dará más credibilidad."))
        elif res["subjetividad"] < 0.25:
            tips.append(("Añadir cercanía", "El texto es muy frío y distante. Si buscas conectar con una audiencia amplia, incluye una breve frase humana o de contexto."))

        if res["volatilidad"] > 0.4:
            tips.append(("Estabilizar cambios de ánimo", f"Se observan saltos abruptos de tono ({res['volatilidad']}). Procura que las transiciones entre ideas fluyan mejor."))

        if res["diversidad_lexica"] < 40:
            tips.append(("Enriquecer el vocabulario", f"Tu variedad léxica es de {res['diversidad_lexica']}%. Sustituir palabras repetidas por sinónimos precisos reforzará tu estilo."))

        for t_tit, t_desc in tips:
            render_clean_html(
                f"""
                <div style="background:rgba(255,215,0,0.05); border:1px solid rgba(255,215,0,0.25); border-radius:8px; padding:14px; margin-bottom:10px;">
                    <div style="font-family:'Spectral'; font-size:1.05rem; color:#ffd700; font-weight:700; margin-bottom:2px;">
                        {t_tit}
                    </div>
                    <div style="font-size:0.92rem; color:#e2e8f0; line-height:1.5;">
                        {t_desc}
                    </div>
                </div>
                """
            )
else:
    st.info("Escribe un texto arriba o pulsa uno de los ejemplos para iniciar la evaluación.")
