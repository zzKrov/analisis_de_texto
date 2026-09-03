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
    """Traduce a inglés para maximizar la precisión de análisis de TextBlob."""
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
# LISTA DE STOPWORDS (ESPAÑOL E INGLÉS)
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
    """Evita que el Markdown interprete el HTML con sangrías como código fuente."""
    clean = "".join(line.strip() for line in html_str.splitlines() if line.strip())
    st.markdown(clean, unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# CONFIGURACIÓN DE PÁGINA
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="VOX.AI // Neuro-Linguistic Terminal",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# -----------------------------------------------------------------------------
# ESTÉTICA CYBER-NOIR OVER-THE-TOP
# -----------------------------------------------------------------------------
CYBER_CSS = r"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@600;800;900&family=Plus+Jakarta+Sans:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;700&display=swap');

html, body, [data-testid="stAppViewContainer"] {
    background-color: #05070c !important;
    color: #e4edf8 !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    overflow-x: hidden;
}

[data-testid="stHeader"] {
    background: transparent !important;
}

.block-container {
    max-width: 1280px !important;
    padding-top: 1.5rem !important;
    padding-bottom: 3rem !important;
    margin: 0 auto !important;
    position: relative;
    z-index: 2;
}

/* Cuadrícula 3D animada en el suelo */
.cyber-grid-floor {
    position: fixed;
    bottom: 0;
    left: -50%;
    width: 200%;
    height: 45vh;
    background-image:
        linear-gradient(to right, rgba(0, 240, 255, 0.07) 1px, transparent 1px),
        linear-gradient(to bottom, rgba(0, 240, 255, 0.07) 1px, transparent 1px);
    background-size: 55px 55px;
    transform: perspective(350px) rotateX(65deg);
    animation: gridMove 16s linear infinite;
    z-index: 1;
    pointer-events: none;
    opacity: 0.6;
    mask-image: linear-gradient(to top, rgba(0,0,0,1) 0%, rgba(0,0,0,0) 80%);
    -webkit-mask-image: linear-gradient(to top, rgba(0,0,0,1) 0%, rgba(0,0,0,0) 80%);
}

@keyframes gridMove {
    0% { background-position: 0 0; }
    100% { background-position: 0 55px; }
}

/* Nebulosa de luz ambiental reactiva */
.cyber-nebula {
    position: fixed;
    top: 20%;
    left: 25%;
    width: 650px;
    height: 650px;
    border-radius: 50%;
    background: radial-gradient(circle, rgba(0, 229, 255, 0.15) 0%, rgba(191, 90, 242, 0.08) 50%, transparent 70%);
    filter: blur(90px);
    z-index: 1;
    pointer-events: none;
    animation: nebulaFloat 8s ease-in-out infinite alternate;
}

@keyframes nebulaFloat {
    0% { transform: scale(0.85) translate(-20px, -20px); opacity: 0.4; }
    100% { transform: scale(1.2) translate(25px, 25px); opacity: 0.8; }
}

/* Tipografía de Títulos */
.cyber-title {
    font-family: 'Orbitron', monospace;
    font-size: 2.5rem;
    font-weight: 900;
    letter-spacing: 3px;
    background: linear-gradient(135deg, #ffffff 0%, #00f0ff 50%, #7928ca 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    text-shadow: 0 0 35px rgba(0, 240, 255, 0.5);
    margin-bottom: 2px;
}

.cyber-subtitle {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.85rem;
    letter-spacing: 2px;
    color: #00f0ff;
    text-transform: uppercase;
    text-shadow: 0 0 12px rgba(0, 240, 255, 0.6);
}

/* Tarjetas Cyber con Glassmorphism y Glow */
.cyber-card {
    position: relative;
    background: linear-gradient(135deg, rgba(13, 19, 33, 0.9) 0%, rgba(8, 12, 22, 0.95) 100%);
    border: 1px solid rgba(0, 240, 255, 0.25);
    border-radius: 20px;
    padding: 22px;
    backdrop-filter: blur(20px);
    box-shadow: 0 15px 45px rgba(0, 0, 0, 0.8), 0 0 30px rgba(0, 240, 255, 0.12), inset 0 0 15px rgba(0, 240, 255, 0.03);
    transition: all 0.35s cubic-bezier(0.165, 0.84, 0.44, 1);
    margin-bottom: 16px;
}

.cyber-card:hover {
    border-color: #00f0ff;
    box-shadow: 0 20px 55px rgba(0, 0, 0, 0.9), 0 0 45px rgba(0, 240, 255, 0.3);
    transform: translateY(-4px);
}

/* Métricas KPI flotantes */
.kpi-card {
    background: rgba(10, 15, 28, 0.75);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 16px;
    padding: 16px;
    text-align: center;
    transition: all 0.3s ease;
}

.kpi-card:hover {
    border-color: #00f0ff;
    box-shadow: 0 0 25px rgba(0, 240, 255, 0.25);
    transform: translateY(-3px);
}

.kpi-val {
    font-family: 'Orbitron', monospace;
    font-size: 1.7rem;
    font-weight: 800;
    color: #ffffff;
}

.kpi-lbl {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.72rem;
    letter-spacing: 1.5px;
    color: #7d96b3;
    text-transform: uppercase;
    margin-top: 4px;
}

/* Botones interactivos neón */
.stButton > button {
    background: rgba(13, 19, 33, 0.85) !important;
    border: 1.5px solid rgba(0, 240, 255, 0.35) !important;
    border-radius: 30px !important;
    color: #ffffff !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.82rem !important;
    padding: 8px 18px !important;
    transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275) !important;
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.5) !important;
}

.stButton > button:hover {
    border-color: #00f0ff !important;
    box-shadow: 0 0 30px rgba(0, 240, 255, 0.6), inset 0 0 12px rgba(0, 240, 255, 0.3) !important;
    transform: translateY(-3px) scale(1.04) !important;
    color: #00f0ff !important;
}

.stTextArea textarea {
    background: rgba(11, 16, 28, 0.9) !important;
    border: 1.5px solid rgba(0, 240, 255, 0.25) !important;
    border-radius: 16px !important;
    color: #ffffff !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.95rem !important;
    padding: 14px 18px !important;
    box-shadow: inset 0 0 20px rgba(0, 0, 0, 0.8) !important;
}

.stTextArea textarea:focus {
    border-color: #00f0ff !important;
    box-shadow: 0 0 25px rgba(0, 240, 255, 0.4), inset 0 0 10px rgba(0, 240, 255, 0.2) !important;
}

/* Tabs personalizadas */
.stTabs [data-baseweb="tab-list"] {
    gap: 12px;
    background-color: transparent;
}

.stTabs [data-baseweb="tab"] {
    background: rgba(13, 19, 33, 0.65) !important;
    border: 1px solid rgba(255, 255, 255, 0.08) !important;
    border-radius: 12px !important;
    padding: 8px 20px !important;
    color: #8da4be !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.85rem !important;
}

.stTabs [aria-selected="true"] {
    background: rgba(0, 240, 255, 0.12) !important;
    border-color: #00f0ff !important;
    color: #ffffff !important;
    box-shadow: 0 0 20px rgba(0, 240, 255, 0.3) !important;
}
</style>

<div class="cyber-grid-floor"></div>
<div class="cyber-nebula"></div>
"""

render_clean_html(CYBER_CSS)

# -----------------------------------------------------------------------------
# LIENZO JAVASCRIPT INTERACTIVO: CONSTELACIONES, ESTELA Y SHOCKWAVE
# -----------------------------------------------------------------------------
st.components.v1.html(
    r"""
    <script>
    (function() {
        let doc = document;
        let win = window;
        try {
            if (window.parent && window.parent.document) {
                doc = window.parent.document;
                win = window.parent;
            }
        } catch(e) {}

        let canvas = doc.getElementById('vox-interactive-canvas');
        if (!canvas) {
            canvas = doc.createElement('canvas');
            canvas.id = 'vox-interactive-canvas';
            canvas.style.position = 'fixed';
            canvas.style.top = '0';
            canvas.style.left = '0';
            canvas.style.width = '100vw';
            canvas.style.height = '100vh';
            canvas.style.zIndex = '0';
            canvas.style.pointerEvents = 'none';
            doc.body.prepend(canvas);
        }

        const ctx = canvas.getContext('2d');
        let w = canvas.width = win.innerWidth;
        let h = canvas.height = win.innerHeight;

        win.addEventListener('resize', () => {
            w = canvas.width = win.innerWidth;
            h = canvas.height = win.innerHeight;
        });

        const particles = [];
        const trail = [];
        const shockwaves = [];
        let mouse = { x: -1000, y: -1000 };

        win.addEventListener('mousemove', (e) => {
            mouse.x = e.clientX;
            mouse.y = e.clientY;
            for (let i = 0; i < 2; i++) {
                trail.push({
                    x: e.clientX + (Math.random() - 0.5) * 8,
                    y: e.clientY + (Math.random() - 0.5) * 8,
                    size: Math.random() * 2.5 + 1,
                    alpha: 0.9,
                    decay: 0.025,
                    vx: (Math.random() - 0.5) * 1.5,
                    vy: (Math.random() - 0.5) * 1.5 - 0.3
                });
            }
        });

        win.addEventListener('click', (e) => {
            for (let i = 0; i < 14; i++) {
                const angle = (Math.PI * 2 / 14) * i;
                const spd = Math.random() * 4 + 2.5;
                trail.push({
                    x: e.clientX,
                    y: e.clientY,
                    size: Math.random() * 3.5 + 1.5,
                    alpha: 1,
                    decay: 0.02,
                    vx: Math.cos(angle) * spd,
                    vy: Math.sin(angle) * spd
                });
            }
            shockwaves.push({
                x: e.clientX,
                y: e.clientY,
                radius: 10,
                maxRadius: 190,
                alpha: 1
            });
        });

        for (let i = 0; i < 60; i++) {
            particles.push({
                x: Math.random() * w,
                y: Math.random() * h,
                r: Math.random() * 1.8 + 0.6,
                vx: (Math.random() - 0.5) * 0.3,
                vy: (Math.random() - 0.5) * 0.3,
                alpha: Math.random() * 0.5 + 0.2
            });
        }

        const CYBER_CYAN = '#00f0ff';

        function loop() {
            ctx.clearRect(0, 0, w, h);

            for (let i = 0; i < particles.length; i++) {
                const p = particles[i];
                p.x += p.vx;
                p.y += p.vy;
                if (p.x < 0) p.x = w;
                if (p.x > w) p.x = 0;
                if (p.y < 0) p.y = h;
                if (p.y > h) p.y = 0;

                const dm = Math.hypot(p.x - mouse.x, p.y - mouse.y);
                if (dm < 130) {
                    ctx.beginPath();
                    ctx.moveTo(p.x, p.y);
                    ctx.lineTo(mouse.x, mouse.y);
                    ctx.strokeStyle = CYBER_CYAN;
                    ctx.globalAlpha = (1 - dm / 130) * 0.4;
                    ctx.lineWidth = 0.8;
                    ctx.stroke();
                    ctx.globalAlpha = 1;
                }

                for (let j = i + 1; j < particles.length; j++) {
                    const p2 = particles[j];
                    const d = Math.hypot(p.x - p2.x, p.y - p2.y);
                    if (d < 110) {
                        ctx.beginPath();
                        ctx.moveTo(p.x, p.y);
                        ctx.lineTo(p2.x, p2.y);
                        ctx.strokeStyle = CYBER_CYAN;
                        ctx.globalAlpha = (1 - d / 110) * 0.2;
                        ctx.lineWidth = 0.6;
                        ctx.stroke();
                        ctx.globalAlpha = 1;
                    }
                }

                ctx.beginPath();
                ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
                ctx.fillStyle = CYBER_CYAN;
                ctx.shadowBlur = 8;
                ctx.shadowColor = CYBER_CYAN;
                ctx.globalAlpha = p.alpha;
                ctx.fill();
                ctx.globalAlpha = 1;
            }

            for (let i = shockwaves.length - 1; i >= 0; i--) {
                const sw = shockwaves[i];
                sw.radius += 4.5;
                sw.alpha -= 0.024;
                if (sw.alpha <= 0 || sw.radius >= sw.maxRadius) {
                    shockwaves.splice(i, 1);
                    continue;
                }
                ctx.beginPath();
                ctx.arc(sw.x, sw.y, sw.radius, 0, Math.PI * 2);
                ctx.strokeStyle = CYBER_CYAN;
                ctx.globalAlpha = sw.alpha * 0.7;
                ctx.lineWidth = 2;
                ctx.shadowBlur = 18;
                ctx.shadowColor = CYBER_CYAN;
                ctx.stroke();
                ctx.globalAlpha = 1;
            }

            for (let i = trail.length - 1; i >= 0; i--) {
                const t = trail[i];
                t.x += t.vx;
                t.y += t.vy;
                t.alpha -= t.decay;
                if (t.alpha <= 0) {
                    trail.splice(i, 1);
                    continue;
                }
                ctx.beginPath();
                ctx.arc(t.x, t.y, t.size, 0, Math.PI * 2);
                ctx.fillStyle = CYBER_CYAN;
                ctx.globalAlpha = t.alpha;
                ctx.shadowBlur = 12;
                ctx.shadowColor = CYBER_CYAN;
                ctx.fill();
                ctx.globalAlpha = 1;
            }

            win.requestAnimationFrame(loop);
        }
        loop();
    })();
    </script>
    """,
    height=0,
    width=0,
)


# -----------------------------------------------------------------------------
# LÓGICA DE PROCESAMIENTO ANALÍTICO
# -----------------------------------------------------------------------------
def analizar_texto_profundo(texto_original: str):
    # Traducir a inglés para TextBlob
    texto_en = traducir_a_ingles(texto_original)
    blob = TextBlob(texto_en)

    # Sentimiento y Subjetividad globales
    polaridad = round(blob.sentiment.polarity, 2)
    subjetividad = round(blob.sentiment.subjectivity, 2)

    # Conteo y extracción de palabras (limpias de stopwords)
    palabras_totales = re.findall(r"\b\w+\b", texto_original.lower())
    palabras_filtradas = [
        p for p in palabras_totales if p not in STOP_WORDS and len(p) > 2 and not p.isdigit()
    ]
    conteo_frecuencia = {}
    for p in palabras_filtradas:
        conteo_frecuencia[p] = conteo_frecuencia.get(p, 0) + 1
    frecuencia_ordenada = dict(sorted(conteo_frecuencia.items(), key=lambda x: x[1], reverse=True))

    # Métricas de Lectura y Retórica
    total_palabras = len(palabras_totales)
    vocabulario_unico = len(set(palabras_totales))
    diversidad_lexica = round((vocabulario_unico / max(1, total_palabras)) * 100, 1)

    tiempo_lectura_seg = round((total_palabras / 200) * 60)
    tiempo_oratoria_seg = round((total_palabras / 130) * 60)

    # Análisis de Frases y Trayectoria Emocional
    frases_es = [f.strip() for f in re.split(r"[.!?]+", texto_original) if len(f.strip()) > 3]
    frases_en = [f.strip() for f in re.split(r"[.!?]+", texto_en) if len(f.strip()) > 3]

    trayectoria = []
    min_frases = min(len(frases_es), len(frases_en))
    for i in range(min_frases):
        b_frase = TextBlob(frases_en[i])
        p_frase = round(b_frase.sentiment.polarity, 2)
        s_frase = round(b_frase.sentiment.subjectivity, 2)
        trayectoria.append({
            "idx": i + 1,
            "es": frases_es[i],
            "en": frases_en[i],
            "polaridad": p_frase,
            "subjetividad": s_frase
        })

    # Volatilidad Emocional (desviación de polaridad entre oraciones)
    if len(trayectoria) > 1:
        pols = [t["polaridad"] for t in trayectoria]
        media_p = sum(pols) / len(pols)
        varianza = sum((p - media_p) ** 2 for p in pols) / len(pols)
        volatilidad = round(math.sqrt(varianza), 2)
    else:
        volatilidad = 0.0

    # Diagnóstico del Tono de Comunicación
    if polaridad >= 0.35 and subjetividad >= 0.4:
        tono_nombre = "Liderazgo Inspirador / Persuasivo"
        tono_color = "#00ff88"
        tono_desc = "Carga emocional positiva alta. Ideal para discursos motivacionales, pitches de venta o arengas de equipo."
    elif polaridad >= 0.1 and subjetividad < 0.4:
        tono_nombre = "Propuesta Constructiva / Objetiva"
        tono_color = "#00f0ff"
        tono_desc = "Equilibrio profesional excelente. Predominan hechos con una perspectiva optimista y pragmática."
    elif polaridad <= -0.25 and subjetividad >= 0.45:
        tono_nombre = "Crítica Severa / Descontento Agudo"
        tono_color = "#ff0055"
        tono_desc = "Fuerte carga negativa y subjetiva. Indica reclamo enfático, frustración o postura combativa."
    elif polaridad <= -0.1 and subjetividad < 0.45:
        tono_nombre = "Reporte Crítico / Advertencia Formal"
        tono_color = "#ffd600"
        tono_desc = "Evaluación desfavorable pero sustentada con tono analítico y mesurado."
    elif subjetividad < 0.25:
        tono_nombre = "Informe Técnico Imparcial"
        tono_color = "#64d2ff"
        tono_desc = "Neutralidad quirúrgica. Libre de sesgos afectivos, óptimo para documentación legal o científica."
    else:
        tono_nombre = "Reflexión Mixta / Conversacional"
        tono_color = "#bf5af2"
        tono_desc = "Tono equilibrado que combina observaciones personales con datos casuales."

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
# GRÁFICOS INTERACTIVOS CON PLOTLY
# -----------------------------------------------------------------------------
def plot_speedometer(valor, titulo, rango, color_linea):
    """Crea un medidor holográfico con aguja y gradiente."""
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=valor,
        number={"font": {"family": "Orbitron", "size": 28, "color": "#ffffff"}},
        title={"text": titulo, "font": {"family": "JetBrains Mono", "size": 13, "color": color_linea}},
        gauge={
            "axis": {"range": rango, "tickwidth": 1, "tickcolor": "rgba(255,255,255,0.2)"},
            "bar": {"color": color_linea, "thickness": 0.25},
            "bgcolor": "rgba(0,0,0,0.4)",
            "borderwidth": 1,
            "bordercolor": "rgba(255,255,255,0.1)",
            "steps": [
                {"range": [rango[0], 0 if rango[0] < 0 else rango[1] / 2], "color": "rgba(255, 255, 255, 0.03)"},
                {"range": [0 if rango[0] < 0 else rango[1] / 2, rango[1]], "color": "rgba(255, 255, 255, 0.06)"},
            ],
        }
    ))
    fig.update_layout(
        height=200,
        margin=dict(l=20, r=20, t=35, b=20),
        paper_bgcolor="rgba(0,0,0,0)",
        font={"color": "#e0e6ed"}
    )
    return fig


def plot_trayectoria_emocional(trayectoria):
    """Mapea la curva narrativa / emocional oración por oración."""
    if not trayectoria:
        return None

    df = pd.DataFrame(trayectoria)
    fig = go.Figure()

    # Línea de polaridad con relleno suave
    fig.add_trace(go.Scatter(
        x=df["idx"],
        y=df["polaridad"],
        mode="lines+markers",
        name="Polaridad",
        line=dict(color="#00f0ff", width=3, shape="spline"),
        marker=dict(
            size=8,
            color=df["polaridad"].apply(lambda p: "#00ff88" if p > 0.05 else ("#ff0055" if p < -0.05 else "#ffd600")),
            line=dict(width=2, color="#ffffff")
        ),
        hovertemplate="<b>Oración %{x}</b><br>Sentimiento: %{y:.2f}<extra></extra>"
    ))

    # Línea base de neutralidad
    fig.add_hline(y=0, line_dash="dash", line_color="rgba(255,255,255,0.25)")

    fig.update_layout(
        title="<b>TRAYECTORIA EMOCIONAL // CURVA NARRATIVA DEL TEXTO</b>",
        title_font=dict(family="Orbitron", size=13, color="#00f0ff"),
        xaxis_title="Secuencia de Oraciones",
        yaxis_title="Índice de Sentimiento (-1 a +1)",
        height=270,
        margin=dict(l=35, r=20, t=40, b=35),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(11, 16, 28, 0.6)",
        font=dict(family="JetBrains Mono", color="#9bb0c9", size=11),
        xaxis=dict(gridcolor="rgba(255,255,255,0.06)", tickmode="linear"),
        yaxis=dict(gridcolor="rgba(255,255,255,0.06)", range=[-1.05, 1.05]),
    )
    return fig


def plot_radar_dimensiones(res):
    """Gráfico radial de 5 ejes para diagnóstico de comunicación."""
    # Normalización de variables a escala 0-100
    pos_score = max(0, min(100, int(((res["polaridad"] + 1) / 2) * 100)))
    obj_score = max(0, min(100, int((1 - res["subjetividad"]) * 100)))
    lex_score = max(0, min(100, int(res["diversidad_lexica"])))
    claridad_score = max(0, min(100, int(100 - (res["volatilidad"] * 100))))
    impacto_score = max(0, min(100, int((abs(res["polaridad"]) * 50) + (res["subjetividad"] * 50))))

    categorias = [
        "Positividad",
        "Objetividad",
        "Riqueza Léxica",
        "Estabilidad / Claridad",
        "Fuerza Retórica"
    ]
    valores = [pos_score, obj_score, lex_score, claridad_score, impacto_score]
    valores += valores[:1]
    categorias += categorias[:1]

    fig = go.Figure(go.Scatterpolar(
        r=valores,
        theta=categorias,
        fill="toself",
        fillcolor="rgba(0, 240, 255, 0.2)",
        line=dict(color="#00f0ff", width=2),
        marker=dict(size=6, color="#00ff88"),
    ))

    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 100], gridcolor="rgba(255,255,255,0.08)", linecolor="rgba(255,255,255,0.08)"),
            angularaxis=dict(gridcolor="rgba(255,255,255,0.08)", linecolor="rgba(255,255,255,0.08)"),
            bgcolor="rgba(0,0,0,0)"
        ),
        title="<b>RADAR DE 5 DIMENSIONES RETÓRICAS</b>",
        title_font=dict(family="Orbitron", size=13, color="#00f0ff"),
        height=270,
        margin=dict(l=35, r=35, t=40, b=30),
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="JetBrains Mono", color="#9bb0c9", size=10)
    )
    return fig


def plot_barras_frecuencia(frecuencia_dict):
    """Barras horizontales con las palabras clave más densas."""
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
            colorscale=[[0, "#0077ff"], [0.5, "#00f0ff"], [1, "#00ff88"]],
            line=dict(color="#ffffff", width=1)
        ),
        hovertemplate="Palabra: <b>%{y}</b><br>Frecuencia: %{x}<extra></extra>"
    ))

    fig.update_layout(
        title="<b>DENSIDAD DE PALABRAS CLAVE</b>",
        title_font=dict(family="Orbitron", size=13, color="#00f0ff"),
        height=270,
        margin=dict(l=40, r=20, t=40, b=20),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="JetBrains Mono", color="#9bb0c9", size=11),
        xaxis=dict(gridcolor="rgba(255,255,255,0.06)"),
        yaxis=dict(gridcolor="rgba(255,255,255,0.0)")
    )
    return fig


# -----------------------------------------------------------------------------
# GESTIÓN DE PRESETS RÁPIDOS
# -----------------------------------------------------------------------------
PRESETS = {
    "pitch": (
        "¡Equipo, hemos alcanzado un récord histórico este trimestre! Los resultados "
        "superaron todas nuestras proyecciones iniciales gracias a su dedicación incansable. "
        "Este triunfo no es casualidad, es la prueba irrefutable de que nuestra visión es la correcta. "
        "Sigamos acelerando con este mismo entusiasmo para liderar el mercado global."
    ),
    "crisis": (
        "Lamentamos profundamente los fallos técnicos experimentados durante el despliegue del sistema. "
        "Reconocemos el impacto negativo que esto ocasionó a nuestros usuarios y asumimos total responsabilidad. "
        "Hemos implementado un plan de mitigación inmediato y auditorías de seguridad las 24 horas. "
        "Nuestro compromiso con la transparencia y la estabilidad sigue siendo absoluto."
    ),
    "reclamo": (
        "Estoy sumamente molesto con la pésima atención al cliente que recibí hoy. "
        "Es inaceptable que tras semanas de retrasos nadie brinde una respuesta seria ni una solución. "
        "El producto que entregaron está defectuoso y el servicio es una completa falta de respeto. "
        "Exijo la devolución inmediata de mi dinero o escalaré esta queja formalmente."
    ),
    "tecnico": (
        "La arquitectura del sistema procesa paquetes mediante una cola asíncrona distribuida. "
        "El tiempo de latencia promedio registrado en los nodos periféricos se mantiene en doce milisegundos. "
        "Los índices de memoria operativa permanecen estables bajo un régimen de carga del setenta por ciento. "
        "El módulo de almacenamiento ejecuta copias incrementales cada seis horas de forma autónoma."
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
    <div style="text-align: center; margin-bottom: 20px;">
        <span class="cyber-subtitle">// NEURO-LINGUISTIC COGNITIVE TELEMETRY //</span>
        <div class="cyber-title">VOX.AI // AUDITOR DE COMUNICACIÓN</div>
        <p style="color: #7e9bb9; font-size: 0.95rem; font-family: 'JetBrains Mono', monospace; margin-top: 4px;">
            Diagnóstico de tono retórico, carga emocional, trayectoria discursiva y densidad léxica.
        </p>
    </div>
    """
)

# -----------------------------------------------------------------------------
# PRESETS DE PRUEBA RÁPIDA (4 CASOS EXTREMOS)
# -----------------------------------------------------------------------------
render_clean_html(
    """
    <div style="text-align: center; margin-bottom: 10px;">
        <span style="font-family: 'JetBrains Mono', monospace; font-size: 0.72rem; color: #00f0ff; letter-spacing: 2px;">
            CARGAR CASO DE ESTUDIO TÁCTICO:
        </span>
    </div>
    """
)

col_p1, col_p2, col_p3, col_p4 = st.columns(4)
with col_p1:
    if st.button("🚀 Pitch Inspirador", use_container_width=True):
        cargar_preset("pitch")
        st.rerun()
with col_p2:
    if st.button("⚠️ Gestión de Crisis", use_container_width=True):
        cargar_preset("crisis")
        st.rerun()
with col_p3:
    if st.button("🛑 Queja Furiosa", use_container_width=True):
        cargar_preset("reclamo")
        st.rerun()
with col_p4:
    if st.button("📋 Informe Técnico", use_container_width=True):
        cargar_preset("tecnico")
        st.rerun()

st.write("")

# -----------------------------------------------------------------------------
# ÁREA DE ENTRADA Y SELECCIÓN DE IDIOMA
# -----------------------------------------------------------------------------
col_input_txt, col_opciones = st.columns([3.3, 1], gap="medium")

with col_input_txt:
    texto_usuario = st.text_area(
        label="Terminal de Transmisión de Texto:",
        value=st.session_state.texto_activo,
        height=170,
        placeholder="Escribe o pega aquí el discurso, correo, artículo o propuesta...",
    )

with col_opciones:
    st.markdown('<div class="cyber-card" style="padding: 16px;">', unsafe_allow_html=True)
    st.markdown(
        """
        <div style="font-family: 'JetBrains Mono'; font-size: 0.75rem; color: #00f0ff; letter-spacing: 1px; margin-bottom: 8px;">
            ● MODO DE ENTRADA
        </div>
        """,
        unsafe_allow_html=True
    )
    modo_subida = st.radio("Fuente:", ["Texto en Terminal", "Cargar Archivo"], horizontal=True, label_visibility="collapsed")

    archivo_subido = None
    if modo_subida == "Cargar Archivo":
        archivo_subido = st.file_uploader("Sube .txt, .md, .csv", type=["txt", "md", "csv"])

    target_lang = st.selectbox(
        label="Traducir oraciones a:",
        options=["en", "es", "fr", "ja", "de", "it", "pt"],
        format_func=lambda c: {
            "en": "🇬🇧 Inglés (EN)",
            "es": "🇪🇸 Español (ES)",
            "fr": "🇫🇷 Francés (FR)",
            "ja": "🇯🇵 Japonés (JA)",
            "de": "🇩🇪 Alemán (DE)",
            "it": "🇮🇹 Italiano (IT)",
            "pt": "🇵🇹 Portugués (PT)",
        }.get(c, c),
        index=0
    )
    st.markdown("</div>", unsafe_allow_html=True)

# Procesar archivo si fue cargado
if archivo_subido is not None:
    try:
        texto_usuario = archivo_subido.getvalue().decode("utf-8")
    except Exception as e:
        st.error(f"Error al leer archivo: {e}")

# -----------------------------------------------------------------------------
# EJECUCIÓN DEL ANÁLISIS
# -----------------------------------------------------------------------------
if texto_usuario and len(texto_usuario.strip()) > 3:
    with st.spinner("Procesando telemetría neuro-lingüística..."):
        res = analizar_texto_profundo(texto_usuario)

    # 1. DIAGNÓSTICO EJECUTIVO PRINCIPAL
    render_clean_html(
        f"""
        <div class="cyber-card" style="border-left: 5px solid {res['tono_color']}; margin-top: 10px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                <span style="font-family: 'Orbitron'; font-size: 0.85rem; color: {res['tono_color']}; letter-spacing: 2px;">
                    ● DIAGNÓSTICO RETÓRICO EJECUTIVO
                </span>
                <span style="font-family: 'JetBrains Mono'; font-size: 0.8rem; background: rgba(0,0,0,0.5); padding: 4px 12px; border-radius: 20px; border: 1px solid {res['tono_color']}; color: {res['tono_color']};">
                    Volatilidad Emocional: {res['volatilidad']}
                </span>
            </div>
            <h2 style="font-family: 'Orbitron'; font-size: 1.8rem; margin: 0 0 6px 0; color: #ffffff;">
                {res['tono_nombre']}
            </h2>
            <p style="color: #9cb4ce; font-size: 0.95rem; margin: 0;">
                {res['tono_desc']}
            </p>
        </div>
        """
    )

    # 2. TELEMETRÍA DE LECTURA Y RETÓRICA (KPIs)
    min_lectura = res["tiempo_lectura_seg"] // 60
    seg_lectura = res["tiempo_lectura_seg"] % 60
    min_oratoria = res["tiempo_oratoria_seg"] // 60
    seg_oratoria = res["tiempo_oratoria_seg"] % 60

    kpi_cols = st.columns(5)
    with kpi_cols[0]:
        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-val">{res['total_palabras']}</div>
                <div class="kpi-lbl">Palabras Totales</div>
            </div>
            """,
            unsafe_allow_html=True
        )
    with kpi_cols[1]:
        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-val">{res['diversidad_lexica']}%</div>
                <div class="kpi-lbl">Riqueza de Vocabulario</div>
            </div>
            """,
            unsafe_allow_html=True
        )
    with kpi_cols[2]:
        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-val">{len(res['trayectoria'])}</div>
                <div class="kpi-lbl">Oraciones Clave</div>
            </div>
            """,
            unsafe_allow_html=True
        )
    with kpi_cols[3]:
        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-val">{min_lectura}m {seg_lectura}s</div>
                <div class="kpi-lbl">Tiempo de Lectura</div>
            </div>
            """,
            unsafe_allow_html=True
        )
    with kpi_cols[4]:
        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-val">{min_oratoria}m {seg_oratoria}s</div>
                <div class="kpi-lbl">Tiempo de Oratoria</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.write("")

    # 3. PANELES VISUALES INTERACTIVOS
    tab_graficos, tab_oraciones, tab_coaching = st.tabs([
        "📊 Telemetría & Gráficos Holográficos",
        "📑 Matriz de Oraciones & Traducción",
        "💡 Estrategia de Comunicación"
    ])

    with tab_graficos:
        # Velocímetros
        col_g1, col_g2 = st.columns(2)
        with col_g1:
            st.markdown('<div class="cyber-card">', unsafe_allow_html=True)
            pol_color = "#00ff88" if res["polaridad"] > 0.05 else ("#ff0055" if res["polaridad"] < -0.05 else "#ffd600")
            fig_pol = plot_speedometer(res["polaridad"], "POLARIDAD (-1.0 A +1.0)", [-1, 1], pol_color)
            st.plotly_chart(fig_pol, use_container_width=True, config={"displayModeBar": False})
            st.markdown("</div>", unsafe_allow_html=True)

        with col_g2:
            st.markdown('<div class="cyber-card">', unsafe_allow_html=True)
            sub_color = "#bf5af2" if res["subjetividad"] > 0.5 else "#00f0ff"
            fig_sub = plot_speedometer(res["subjetividad"], "SUBJETIVIDAD (0.0 A 1.0)", [0, 1], sub_color)
            st.plotly_chart(fig_sub, use_container_width=True, config={"displayModeBar": False})
            st.markdown("</div>", unsafe_allow_html=True)

        # Trayectoria Emocional (Curva del discurso)
        st.markdown('<div class="cyber-card">', unsafe_allow_html=True)
        fig_tray = plot_trayectoria_emocional(res["trayectoria"])
        if fig_tray:
            st.plotly_chart(fig_tray, use_container_width=True, config={"displayModeBar": False})
        else:
            st.info("Ingresa al menos dos oraciones separadas por punto para graficar la curva narrativa.")
        st.markdown("</div>", unsafe_allow_html=True)

        # Radar de Dimensiones + Frecuencia de palabras
        col_rad, col_bar = st.columns(2)
        with col_rad:
            st.markdown('<div class="cyber-card">', unsafe_allow_html=True)
            fig_radar = plot_radar_dimensiones(res)
            st.plotly_chart(fig_radar, use_container_width=True, config={"displayModeBar": False})
            st.markdown("</div>", unsafe_allow_html=True)

        with col_bar:
            st.markdown('<div class="cyber-card">', unsafe_allow_html=True)
            fig_bar = plot_barras_frecuencia(res["frecuencia"])
            if fig_bar:
                st.plotly_chart(fig_bar, use_container_width=True, config={"displayModeBar": False})
            else:
                st.info("No hay suficientes palabras clave filtradas.")
            st.markdown("</div>", unsafe_allow_html=True)

    with tab_oraciones:
        st.markdown(
            """
            <div style="font-family: 'JetBrains Mono'; font-size: 0.8rem; color: #00f0ff; letter-spacing: 1.5px; margin-bottom: 12px;">
                INSPECTOR RETÓRICO SECUENCIAL
            </div>
            """,
            unsafe_allow_html=True
        )

        for item in res["trayectoria"]:
            p = item["polaridad"]
            s = item["subjetividad"]
            badge_color = "#00ff88" if p > 0.05 else ("#ff0055" if p < -0.05 else "#ffd600")
            badge_icon = "😊 Positiva" if p > 0.05 else ("😟 Negativa" if p < -0.05 else "😐 Neutral")

            # Traducción bajo demanda si se seleccionó otro idioma
            traduccion_frase = traducir_a_idioma(item["es"], target_lang) if target_lang != "es" else item["en"]

            render_clean_html(
                f"""
                <div style="background: rgba(11, 16, 28, 0.8); border: 1px solid rgba(255,255,255,0.08); border-left: 4px solid {badge_color}; border-radius: 12px; padding: 14px; margin-bottom: 10px;">
                    <div style="display: flex; justify-content: space-between; font-size: 0.75rem; font-family: 'JetBrains Mono'; margin-bottom: 6px;">
                        <span style="color: #64d2ff;">ORACIÓN #{item['idx']}</span>
                        <span style="color: {badge_color}; font-weight: 700;">{badge_icon} (Polaridad: {p:+.2f} | Subjetividad: {s:.2f})</span>
                    </div>
                    <div style="font-size: 0.95rem; color: #ffffff; margin-bottom: 6px;">
                        "{item['es']}"
                    </div>
                    <div style="font-size: 0.85rem; color: #829cb8; font-family: 'JetBrains Mono';">
                        🌐 ({target_lang.upper()}): {traduccion_frase}
                    </div>
                </div>
                """
            )

    with tab_coaching:
        st.markdown(
            """
            <div style="font-family: 'Orbitron'; font-size: 1.1rem; color: #00f0ff; letter-spacing: 2px; margin-bottom: 12px;">
                💡 RECOMENDACIONES TÁCTICAS PARA ESTE TEXTO
            </div>
            """,
            unsafe_allow_html=True
        )

        # Generar recomendaciones dinámicas según los datos
        tips = []
        if res["polaridad"] < -0.15:
            tips.append(
                ("🛑 Modulación de Hostilidad",
                 "El texto tiene una carga negativa considerable. Si el objetivo es persuadir o negociar, intenta transformar quejas directas en peticiones de solución para evitar activar sesgos defensivos en el receptor.")
            )
        elif res["polaridad"] > 0.4:
            tips.append(
                ("🚀 Aprovechamiento de Momentum",
                 "El tono es altamente positivo e inspirador. Asegúrate de cerrar con una llamada a la acción (Call to Action) contundente antes de que decaiga el pico de entusiasmo.")
            )

        if res["subjetividad"] > 0.6:
            tips.append(
                ("📊 Fortalecimiento de Evidencia",
                 f"La subjetividad es alta ({int(res['subjetividad']*100)}%). Tus opiniones ganarán 3 veces más autoridad si las respaldas con métricas concretas, plazos o hechos verificables.")
            )
        elif res["subjetividad"] < 0.25:
            tips.append(
                ("✨ Inyección de Humanidad",
                 "El texto es extremadamente frío y objetivo. Si buscas conectar con un público general, añade una breve anécdota o analogía para evitar que suene como un reporte de máquina.")
            )

        if res["volatilidad"] > 0.4:
            tips.append(
                ("📈 Estabilización de la Curva Narrativa",
                 f"Tu texto presenta alta volatilidad emocional ({res['volatilidad']}). Los saltos bruscos entre optimismo y pesimismo pueden confundir. Revisa la transición entre tus ideas principales.")
            )

        if res["diversidad_lexica"] < 40:
            tips.append(
                ("🔁 Enriquecimiento de Vocabulario",
                 f"Tu riqueza léxica es de {res['diversidad_lexica']}%. Intenta sustituir palabras repetitivas usando sinónimos más precisos para enriquecer el impacto retórico.")
            )

        for titulo_tip, desc_tip in tips:
            render_clean_html(
                f"""
                <div style="background: rgba(0, 240, 255, 0.05); border: 1px solid rgba(0, 240, 255, 0.2); border-radius: 14px; padding: 16px; margin-bottom: 12px;">
                    <div style="font-family: 'Orbitron'; font-size: 0.9rem; color: #00ff88; font-weight: 700; margin-bottom: 4px;">
                        {titulo_tip}
                    </div>
                    <div style="font-size: 0.92rem; color: #dce7f3; line-height: 1.5;">
                        {desc_tip}
                    </div>
                </div>
                """
            )

else:
    st.info("Ingresa un texto en el terminal o selecciona uno de los casos de estudio arriba para desplegar la telemetría.")


# -----------------------------------------------------------------------------
# SIDEBAR INFORMATIVA
# -----------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### ⚡ Parámetros del Auditor")
    st.info(
        """
        - **Polaridad (-1.0 a +1.0):** Mide si el sentimiento es favorable, adverso o neutral.
        - **Subjetividad (0% a 100%):** Proporción de juicios personales frente a hechos objetivos.
        - **Volatilidad:** Desvío de polaridad entre oraciones a lo largo del texto.
        - **Riqueza Léxica (TTR):** Porcentaje de vocabulario único respecto al total.
        """
    )
    st.caption("VOX.AI // Python 3.11 // TextBlob & Plotly Cyber-Engine")
