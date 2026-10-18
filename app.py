import os
import re
import math
import pandas as pd
import streamlit as st
from textblob import TextBlob
import plotly.graph_objects as go

# -----------------------------------------------------------------------------
# CONFIGURACIÓN GENERAL
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Analizador de Tono y Emociones // Krov Industries",
    page_icon="⚜",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# -----------------------------------------------------------------------------
# LÍNEA BASE VISUAL: DORADO SOLAR Y FLUIDOS DE ALTO CONTRASTE
# -----------------------------------------------------------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Spectral:ital,wght@0,400;0,600;0,700;1,400&family=JetBrains+Mono:wght@400;500;700&display=swap');

html, body, [data-testid="stAppViewContainer"], .stApp {
    background-color: #06070a !important;
    color: #f1f5f9 !important;
    font-family: 'Spectral', Georgia, serif !important;
    overflow-x: hidden;
}

[data-testid="stHeader"] { background: transparent !important; }

/* 1. Malla continua de gradientes */
.stApp {
    background: linear-gradient(135deg, #06070a 0%, #121019 30%, #1c1508 60%, #08090f 100%) !important;
    background-size: 300% 300% !important;
    animation: solarShift 18s ease infinite alternate !important;
}

@keyframes solarShift {
    0% { background-position: 0% 50%; }
    50% { background-position: 100% 50%; }
    100% { background-position: 0% 50%; }
}

/* 2. Fluidos orgánicos */
.fluid-solar-1 {
    position: fixed;
    top: 15%;
    left: -120px;
    width: 520px;
    height: 520px;
    background: radial-gradient(circle, rgba(255, 215, 0, 0.12) 0%, rgba(255, 136, 0, 0.03) 55%, transparent 70%);
    border-radius: 40% 60% 70% 30% / 50% 60% 40% 50%;
    filter: blur(85px);
    animation: solarDrift1 20s infinite alternate ease-in-out;
    pointer-events: none;
    z-index: 0;
}

.fluid-solar-2 {
    position: fixed;
    bottom: 5%;
    right: -100px;
    width: 560px;
    height: 560px;
    background: radial-gradient(circle, rgba(0, 240, 255, 0.1) 0%, rgba(255, 215, 0, 0.03) 55%, transparent 70%);
    border-radius: 60% 40% 50% 50% / 40% 50% 60% 50%;
    filter: blur(90px);
    animation: solarDrift2 24s infinite alternate ease-in-out;
    pointer-events: none;
    z-index: 0;
}

@keyframes solarDrift1 {
    0% { transform: translate(0, 0) scale(1); }
    50% { transform: translate(110px, 60px) scale(1.15); }
    100% { transform: translate(30px, 130px) scale(0.95); }
}

@keyframes solarDrift2 {
    0% { transform: translate(0, 0) scale(1); }
    50% { transform: translate(-100px, -70px) scale(1.2); }
    100% { transform: translate(-20px, -110px) scale(0.9); }
}

.brand-signature {
    text-align: center;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.72rem;
    letter-spacing: 0.18em;
    color: #ffd700;
    text-transform: uppercase;
    margin-bottom: 2px;
}

.main-title {
    font-size: 2.2rem;
    font-weight: 700;
    text-align: center;
    color: #ffffff;
    margin-bottom: 0.2rem;
    text-shadow: 0 0 25px rgba(255, 215, 0, 0.35);
}

.sub-lead {
    text-align: center;
    color: #94a3b8;
    font-size: 0.95rem;
    margin-bottom: 1.8rem;
}

.glow-card {
    background: rgba(13, 16, 26, 0.85);
    border: 1px solid rgba(255, 215, 0, 0.25);
    border-radius: 10px;
    padding: 22px;
    backdrop-filter: blur(14px);
    box-shadow: 0 10px 35px rgba(0, 0, 0, 0.6);
    margin-bottom: 16px;
}

div.stButton > button {
    border-radius: 6px !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.85rem !important;
    transition: all 0.25s ease !important;
}
</style>

<div class="fluid-solar-1"></div>
<div class="fluid-solar-2"></div>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# FUNCIONES DE ANÁLISIS LÉXICO Y SENTIMIENTO
# -----------------------------------------------------------------------------
PRESETS = {
    "pitch": "¡Equipo, logramos un resultado extraordinario este trimestre! Superamos todas las metas gracias a su constancia.",
    "crisis": "Lamentamos profundamente los fallos ocurridos hoy. Asumimos total responsabilidad y ejecutamos un plan de contingencia.",
    "reclamo": "Estoy muy molesto con la mala atención recibida. Es inaceptable el retraso sin respuestas claras.",
    "tecnico": "El sistema procesa paquetes mediante colas asíncronas con una latencia promedio de doce milisegundos."
}

if "analizador_texto" not in st.session_state:
    st.session_state.analizador_texto = PRESETS["pitch"]

st.markdown('<div class="brand-signature">Krov Industries · Analítica Léxica</div>', unsafe_allow_html=True)
st.markdown('<div class="main-title">Analizador de Tono y Emociones</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-lead">Evaluación directa de actitud, claridad y vocabulario en cualquier mensaje</div>', unsafe_allow_html=True)

col_p1, col_p2, col_p3, col_p4 = st.columns(4)
with col_p1:
    if st.button("🚀 Motivación / Pitch", use_container_width=True):
        st.session_state.analizador_texto = PRESETS["pitch"]
        st.rerun()
with col_p2:
    if st.button("⚠️ Manejo de Crisis", use_container_width=True):
        st.session_state.analizador_texto = PRESETS["crisis"]
        st.rerun()
with col_p3:
    if st.button("🛑 Reclamo Formal", use_container_width=True):
        st.session_state.analizador_texto = PRESETS["reclamo"]
        st.rerun()
with col_p4:
    if st.button("📋 Reporte Técnico", use_container_width=True):
        st.session_state.analizador_texto = PRESETS["tecnico"]
        st.rerun()

texto_evaluar = st.text_area("Texto a evaluar:", value=st.session_state.analizador_texto, height=130)

if texto_evaluar.strip():
    blob = TextBlob(texto_evaluar)
    # Cálculo simple de sentimiento sobre el texto
    pol = round(blob.sentiment.polarity, 2)
    subj = round(blob.sentiment.subjectivity, 2)
    palabras = re.findall(r"\b\w+\b", texto_evaluar.lower())
    total_w = len(palabras)
    unicas_w = len(set(palabras))
    diversidad = round((unicas_w / max(1, total_w)) * 100, 1)

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Palabras totales", total_w)
    m2.metric("Vocabulario único", f"{diversidad}%")
    m3.metric("Sentimiento", f"{pol:+.2f}")
    m4.metric("Subjetividad", f"{int(subj*100)}%")

    st.write("")
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=pol,
        title={"text": "Polaridad de Tono (-1 Negativo a +1 Positivo)"},
        gauge={
            "axis": {"range": [-1, 1]},
            "bar": {"color": "#ffd700"},
            "steps": [
                {"range": [-1, -0.1], "color": "rgba(239, 68, 68, 0.3)"},
                {"range": [-0.1, 0.1], "color": "rgba(148, 163, 184, 0.3)"},
                {"range": [0.1, 1], "color": "rgba(0, 240, 255, 0.3)"}
            ]
        }
    ))
    fig.update_layout(height=260, paper_bgcolor="rgba(0,0,0,0)", font={"color": "#f1f5f9"})
    st.plotly_chart(fig, use_container_width=True)
