import os
import re
import math
import numpy as np
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
import plotly.graph_objects as go

# ============================================================
# CONFIGURACIÓN GENERAL
# ============================================================
st.set_page_config(
    page_title="Analizador de Tono // Krov Industries",
    page_icon="⚜",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ============================================================
# ESTILOS VISUALES: RESPLANDOR Y BOTONES EN HOVER
# ============================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Spectral:ital,wght@0,500;0,700;1,400&family=JetBrains+Mono:wght@400;600&display=swap');

html, body, [data-testid="stAppViewContainer"], .stApp, section.main, .block-container {
    background: transparent !important;
    background-color: transparent !important;
    color: #f1f5f9 !important;
    font-family: 'Spectral', Georgia, serif !important;
}

body {
    background-color: #06070a !important;
}

[data-testid="stHeader"] { background: transparent !important; }
[data-testid="stSidebar"], section[data-testid="stSidebar"] { display: none !important; }

.brand-signature {
    text-align: center;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.72rem;
    letter-spacing: 0.2em;
    color: #ffd700;
    text-transform: uppercase;
}

.main-title {
    font-size: 2.3rem;
    font-weight: 700;
    text-align: center;
    color: #ffffff;
    margin-bottom: 0.2rem;
    text-shadow: 0 0 25px rgba(255, 215, 0, 0.4);
}

.sub-lead {
    text-align: center;
    color: #94a3b8;
    font-size: 0.95rem;
    margin-bottom: 1.5rem;
}

.kpi-card {
    background: rgba(14, 16, 26, 0.88);
    border: 1px solid rgba(255, 215, 0, 0.25);
    border-top: 3px solid #ffd700;
    border-radius: 8px;
    padding: 16px;
    text-align: center;
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.6);
    transition: transform 0.25s ease, border-color 0.25s ease, box-shadow 0.25s ease;
}

.kpi-card:hover {
    transform: translateY(-4px);
    border-color: #ffd700;
    box-shadow: 0 0 30px rgba(255, 215, 0, 0.45);
}

div.stButton > button {
    border-radius: 6px !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.85rem !important;
    background: rgba(18, 22, 34, 0.85) !important;
    color: #f1f5f9 !important;
    border: 1px solid rgba(255, 215, 0, 0.3) !important;
    padding: 0.65rem 1.2rem !important;
    transition: all 0.25s ease-in-out !important;
}

div.stButton > button:hover {
    transform: translateY(-2px) scale(1.02) !important;
    border-color: #ffd700 !important;
    color: #ffd700 !important;
    box-shadow: 0 0 25px rgba(255, 215, 0, 0.5) !important;
}

.advice-box {
    background: rgba(255, 215, 0, 0.05);
    border: 1px solid rgba(255, 215, 0, 0.25);
    border-radius: 8px;
    padding: 16px;
    margin-bottom: 10px;
    line-height: 1.6;
}
</style>
""", unsafe_allow_html=True)

# Fondo interactivo líquido oro animado en Canvas (Cero Lag)
components.html(
    """
    <script>
    (function() {
        const pWin = window.parent;
        const pDoc = pWin.document;
        if (pWin.__TONE_BG_INIT__) return;
        pWin.__TONE_BG_INIT__ = true;

        let canvas = pDoc.getElementById('tone-fluid-canvas');
        if (!canvas) {
            canvas = pDoc.createElement('canvas');
            canvas.id = 'tone-fluid-canvas';
            canvas.style.cssText = 'position:fixed;top:0;left:0;width:100vw;height:100vh;pointer-events:none;z-index:0;background:#06070a;';
            pDoc.body.prepend(canvas);
        }

        const ctx = canvas.getContext('2d');
        let w = canvas.width = pWin.innerWidth;
        let h = canvas.height = pWin.innerHeight;

        pWin.addEventListener('resize', () => {
            w = canvas.width = pWin.innerWidth;
            h = canvas.height = pWin.innerHeight;
        });

        const orbs = [
            { x: w * 0.2, y: h * 0.25, r: 260, vx: 0.5, vy: 0.4, color: 'rgba(255, 215, 0, 0.16)' },
            { x: w * 0.8, y: h * 0.35, r: 280, vx: -0.4, vy: 0.5, color: 'rgba(255, 136, 0, 0.15)' },
            { x: w * 0.45, y: h * 0.8, r: 240, vx: 0.4, vy: -0.5, color: 'rgba(0, 240, 255, 0.12)' }
        ];

        function loop() {
            ctx.clearRect(0, 0, w, h);
            ctx.fillStyle = '#06070a';
            ctx.fillRect(0, 0, w, h);
            ctx.globalCompositeOperation = 'screen';

            for (let b of orbs) {
                b.x += b.vx;
                b.y += b.vy;
                if (b.x < -100 || b.x > w + 100) b.vx *= -1;
                if (b.y < -100 || b.y > h + 100) b.vy *= -1;

                const g = ctx.createRadialGradient(b.x, b.y, 10, b.x, b.y, b.r);
                g.addColorStop(0, b.color);
                g.addColorStop(1, 'transparent');
                ctx.beginPath();
                ctx.arc(b.x, b.y, b.r, 0, Math.PI * 2);
                ctx.fillStyle = g;
                ctx.fill();
            }
            requestAnimationFrame(loop);
        }
        loop();
    })();
    </script>
    """,
    height=0,
    width=0
)

# ============================================================
# MOTOR LÉXICO NATIVO EN ESPAÑOL
# ============================================================
LEXICO_ES = {
    "extraordinario": 0.9, "excelente": 0.85, "increíble": 0.85, "triunfo": 0.8,
    "éxito": 0.8, "victoria": 0.8, "logramos": 0.7, "superamos": 0.7, "talento": 0.6,
    "constancia": 0.6, "dedicación": 0.6, "entusiasmo": 0.75, "conquistar": 0.6,
    "felicitaciones": 0.8, "maravilloso": 0.85, "genial": 0.75, "acertada": 0.6,
    "agradecido": 0.65, "alegría": 0.7, "óptimo": 0.7, "eficaz": 0.6, "feliz": 0.75,
    "pésimo": -0.9, "grosero": -0.85, "inaceptable": -0.85, "decepcionado": -0.8,
    "molesto": -0.75, "defectuoso": -0.7, "evasivas": -0.65, "retraso": -0.6,
    "frustración": -0.7, "inconvenientes": -0.5, "negativo": -0.6, "caída": -0.5,
    "fallos": -0.6, "desastre": -0.85, "terrible": -0.8, "enojo": -0.75, "rabia": -0.8,
    "daño": -0.6, "error": -0.5, "lamentamos": -0.45, "peor": -0.7, "malo": -0.5,
    "inútil": -0.7, "injusto": -0.75
}

INTENSIFICADORES = {"muy": 1.4, "sumamente": 1.6, "profundamente": 1.5, "enormemente": 1.5, "totalmente": 1.3}
NEGADORES = {"no", "nunca", "jamás", "sin", "tampoco", "nadie"}

def analizar_sentimiento_es(texto: str):
    palabras = re.findall(r"\b\w+\b", texto.lower())
    total_w = len(palabras)
    if total_w == 0:
        return 0.0, 0.0, 0, 0.0, []

    puntuacion_total = 0.0
    palabras_evaluadas = 0
    carga_subjetiva = 0

    frases = [f.strip() for f in re.split(r"[.!?]+", texto) if len(f.strip()) > 3]
    trayectoria = []

    for idx, f in enumerate(frases, 1):
        palabras_f = re.findall(r"\b\w+\b", f.lower())
        pol_f = 0.0
        conteo_f = 0

        for i, p in enumerate(palabras_f):
            mult = 1.0
            if i > 0 and palabras_f[i-1] in INTENSIFICADORES:
                mult *= INTENSIFICADORES[palabras_f[i-1]]
            if i > 0 and palabras_f[i-1] in NEGADORES:
                mult *= -1.0
            elif i > 1 and palabras_f[i-2] in NEGADORES:
                mult *= -1.0

            if p in LEXICO_ES:
                val = LEXICO_ES[p] * mult
                pol_f += val
                conteo_f += 1
                carga_subjetiva += 1

        puntuacion_total += pol_f
        palabras_evaluadas += conteo_f
        media_f = round(max(-1.0, min(1.0, pol_f / max(1, conteo_f))), 2) if conteo_f > 0 else 0.0
        trayectoria.append({"idx": idx, "frase": f, "pol": media_f})

    polaridad = round(max(-1.0, min(1.0, puntuacion_total / max(1, palabras_evaluadas))), 2) if palabras_evaluadas > 0 else 0.0
    subjetividad = round(min(1.0, (carga_subjetiva * 3.5) / max(1, total_w)), 2)
    unicas_w = len(set(palabras))
    diversidad = round((unicas_w / max(1, total_w)) * 100, 1)

    return polaridad, subjetividad, total_w, diversidad, trayectoria

# ============================================================
# PRESETS RICOS CON TEXTOS EXTENSOS
# ============================================================
PRESETS = {
    "pitch": (
        "¡Equipo, logramos un resultado extraordinario este trimestre! Superamos con creces todas las proyecciones "
        "gracias a la constancia, el talento y la dedicación incansable de cada integrante. Esta victoria confirma "
        "nuestra visión estratégica y nos impulsa con enorme entusiasmo a conquistar nuevos mercados."
    ),
    "reclamo": (
        "Estoy sumamente molesto y decepcionado con el servicio recibido. Llevo tres semanas esperando una respuesta concreta "
        "y la única atención que brindan son evasivas y respuestas automatizadas inaceptables. El producto llegó defectuoso, "
        "nadie se hace responsable y el trato de su personal fue grosero y pésimo. Exijo una solución inmediata y el reembolso íntegro."
    ),
    "tecnico": (
        "El microservicio procesa eventos mediante una cola asíncrona distribuida en tres nodos redundantes. "
        "La latencia promedio registrada se sitúa en catorce milisegundos bajo una carga constante de setenta por ciento. "
        "Las copias de seguridad de los registros se ejecutan automáticamente cada cuatro horas."
    ),
    "crisis": (
        "Reconocemos el impacto negativo originado por la caída de los servidores durante las primeras horas de hoy. "
        "Entendemos la frustración y los inconvenientes causados a las operaciones de nuestros usuarios. Nuestro equipo técnico "
        "activó de inmediato el plan de contingencia para mitigar los daños y continuará trabajando hasta restablecer el servicio."
    )
}

if "texto_activo" not in st.session_state:
    st.session_state.texto_activo = PRESETS["pitch"]

st.markdown('<div class="brand-signature">Krov Industries · Analítica Semántica</div>', unsafe_allow_html=True)
st.markdown('<div class="main-title">Analizador de Tono y Emociones</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-lead">Diagnóstico objetivo de actitud, carga emocional y estructura del discurso</div>', unsafe_allow_html=True)

c1, c2, c3, c4 = st.columns(4)
with c1:
    if st.button("🚀 Entusiasmo / Pitch", use_container_width=True):
        st.session_state.texto_activo = PRESETS["pitch"]
        st.rerun()
with c2:
    if st.button("🛑 Reclamo Severo", use_container_width=True):
        st.session_state.texto_activo = PRESETS["reclamo"]
        st.rerun()
with c3:
    if st.button("📋 Reporte Técnico", use_container_width=True):
        st.session_state.texto_activo = PRESETS["tecnico"]
        st.rerun()
with c4:
    if st.button("⚠️ Manejo de Crisis", use_container_width=True):
        st.session_state.texto_activo = PRESETS["crisis"]
        st.rerun()

texto_input = st.text_area("Texto a evaluar:", value=st.session_state.texto_activo, height=130)

if st.button("Analizar Tono y Emociones", use_container_width=True):
    pol, subj, total_w, diversidad, trayectoria = analizar_sentimiento_es(texto_input)
    st.session_state.analisis_res = (pol, subj, total_w, diversidad, trayectoria)

if "analisis_res" in st.session_state and texto_input.strip():
    pol, subj, total_w, diversidad, trayectoria = st.session_state.analisis_res

    # Gasómetros SVG animados que crecen y escalan números desde cero
    gasometros_svg = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <style>
    body {{
        margin: 0; background: transparent; font-family: 'JetBrains Mono', monospace;
        display: flex; justify-content: center; gap: 24px; padding: 10px;
    }}
    .gauge-wrapper {{
        background: rgba(14, 16, 26, 0.88); border: 1px solid rgba(255, 215, 0, 0.25);
        border-radius: 10px; padding: 18px 24px; text-align: center; width: 280px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.6); transition: all 0.3s ease;
    }}
    .gauge-wrapper:hover {{
        border-color: #ffd700; transform: translateY(-3px) scale(1.02);
        box-shadow: 0 0 30px rgba(255, 215, 0, 0.45);
    }}
    .label {{ font-size: 11px; letter-spacing: 0.15em; text-transform: uppercase; color: #94a3b8; margin-bottom: 8px; }}
    .number {{ font-family: 'Spectral', serif; font-size: 42px; font-weight: 700; line-height: 1; }}
    .bar-bg {{ width: 100%; height: 8px; background: rgba(255,255,255,0.08); border-radius: 4px; overflow: hidden; margin-top: 12px; }}
    .bar-fill {{ height: 100%; width: 0%; border-radius: 4px; transition: width 1.2s cubic-bezier(0.16, 1, 0.3, 1); }}
    </style>
    </head>
    <body>
    <div class="gauge-wrapper">
        <div class="label">Polaridad Afectiva</div>
        <div class="number" id="num-pol" style="color:{'#00ff88' if pol > 0.05 else ('#ff3344' if pol < -0.05 else '#ffd700')};">0.00</div>
        <div class="bar-bg">
            <div id="bar-pol" class="bar-fill" style="background:{'#00ff88' if pol > 0.05 else ('#ff3344' if pol < -0.05 else '#ffd700')};"></div>
        </div>
    </div>

    <div class="gauge-wrapper">
        <div class="label">Subjetividad / Emoción</div>
        <div class="number" id="num-subj" style="color:#38bdf8;">0%</div>
        <div class="bar-bg">
            <div id="bar-subj" class="bar-fill" style="background:#38bdf8;"></div>
        </div>
    </div>

    <script>
    const targetPol = {pol};
    const targetSubj = {int(subj * 100)};

    let currentPol = 0.0;
    const stepPol = targetPol / 40;
    let countPol = 0;
    const intervalPol = setInterval(() => {{
        countPol++;
        currentPol += stepPol;
        if (countPol >= 40) {{
            currentPol = targetPol;
            clearInterval(intervalPol);
        }}
        document.getElementById('num-pol').innerText = (currentPol >= 0 ? '+' : '') + currentPol.toFixed(2);
    }}, 25);

    let currentSubj = 0;
    const stepSubj = targetSubj / 40;
    let countSubj = 0;
    const intervalSubj = setInterval(() => {{
        countSubj++;
        currentSubj += stepSubj;
        if (countSubj >= 40) {{
            currentSubj = targetSubj;
            clearInterval(intervalSubj);
        }}
        document.getElementById('num-subj').innerText = Math.round(currentSubj) + '%';
    }}, 25);

    setTimeout(() => {{
        const polPercent = Math.max(5, Math.min(100, Math.round(((targetPol + 1.0) / 2.0) * 100)));
        document.getElementById('bar-pol').style.width = polPercent + '%';
        document.getElementById('bar-subj').style.width = Math.max(5, targetSubj) + '%';
    }}, 80);
    </script>
    </body>
    </html>
    """
    components.html(gasometros_svg, height=140)

    st.write("")
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.markdown(f'<div class="kpi-card"><div style="font-size:0.7rem; color:#94a3b8;">PALABRAS</div><div style="font-size:2rem; font-weight:700;">{total_w}</div></div>', unsafe_allow_html=True)
    with k2:
        st.markdown(f'<div class="kpi-card"><div style="font-size:0.7rem; color:#94a3b8;">VOCABULARIO ÚNICO</div><div style="font-size:2rem; font-weight:700;">{diversidad}%</div></div>', unsafe_allow_html=True)
    with k3:
        color_p = "#00ff88" if pol > 0.05 else ("#ff3344" if pol < -0.05 else "#ffd700")
        st.markdown(f'<div class="kpi-card"><div style="font-size:0.7rem; color:#94a3b8;">POLARIDAD</div><div style="font-size:2rem; font-weight:700; color:{color_p};">{pol:+.2f}</div></div>', unsafe_allow_html=True)
    with k4:
        st.markdown(f'<div class="kpi-card"><div style="font-size:0.7rem; color:#94a3b8;">SUBJETIVIDAD</div><div style="font-size:2rem; font-weight:700; color:#38bdf8;">{int(subj*100)}%</div></div>', unsafe_allow_html=True)

    st.write("")
    tab1, tab2 = st.tabs(["Evolución por Oración", "Diagnóstico y Sugerencias"])

    with tab1:
        if trayectoria:
            df_tray = pd.DataFrame(trayectoria)
            fig_t = go.Figure(go.Scatter(
                x=df_tray["idx"], y=df_tray["pol"], mode="lines+markers",
                line=dict(color="#00f0ff", width=2.5), marker=dict(size=8, color="#ffd700")
            ))
            fig_t.add_hline(y=0, line_dash="dash", line_color="rgba(255,255,255,0.3)")
            fig_t.update_layout(
                title="Evolución del Sentimiento por Frase", height=230,
                xaxis_title="Frase", yaxis_title="Tono (-1 a +1)",
                margin=dict(l=30, r=20, t=40, b=30), paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(12,16,28,0.7)", font={"color": "#94a3b8"}
            )
            st.plotly_chart(fig_t, use_container_width=True)
            st.dataframe(df_tray.rename(columns={"idx": "N.º", "frase": "Frase", "pol": "Polaridad"}).set_index("N.º"), use_container_width=True)

    with tab2:
        st.markdown("#### Recomendaciones de redacción")
        if pol < -0.15:
            st.markdown('<div class="advice-box"><b>Tono de queja o molestia:</b> Se detecta fuerte inconformidad. En ámbitos profesionales o de negociación, enfoca el mensaje en peticiones y soluciones concretas.</div>', unsafe_allow_html=True)
        elif pol > 0.35:
            st.markdown('<div class="advice-box"><b>Tono motivador o pitch:</b> Nivel de energía muy favorable. Asegúrate de incluir llamadas claras a la acción.</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="advice-box"><b>Tono neutral u operativo:</b> El texto se mantiene apegado a hechos y procedimientos. Óptimo para informes técnicos y documentación.</div>', unsafe_allow_html=True)

        if subj > 0.6:
            st.markdown('<div class="advice-box"><b>Alta carga subjetiva:</b> El texto depende en gran medida de impresiones personales. Apoyar las aseveraciones con datos aumentará la credibilidad.</div>', unsafe_allow_html=True)
        elif subj < 0.25:
            st.markdown('<div class="advice-box"><b>Redacción objetiva y formal:</b> No se percibe sesgo afectivo personal.</div>', unsafe_allow_html=True)
