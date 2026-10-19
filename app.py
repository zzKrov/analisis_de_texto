import os
import re
import math
import pandas as pd
import streamlit as st
from textblob import TextBlob
import plotly.graph_objects as go

# ============================================================
# CONFIGURACIÓN GENERAL (SIN SIDEBAR)
# ============================================================
st.set_page_config(
    page_title="Analizador de Tono // Krov Industries",
    page_icon="⚜",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ============================================================
# ESTILOS VISUALES: ORO SOLAR LÍQUIDO Y RESPLANDOR
# ============================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Spectral:ital,wght@0,500;0,700;1,400&family=JetBrains+Mono:wght@400;600&display=swap');

html, body, [data-testid="stAppViewContainer"], .stApp {
    background-color: #06070a !important;
    color: #f1f5f9 !important;
    font-family: 'Spectral', Georgia, serif !important;
    overflow-x: hidden;
}

[data-testid="stHeader"] { background: transparent !important; }
[data-testid="stSidebar"], section[data-testid="stSidebar"] { display: none !important; }

/* Fondo líquido acelerado por GPU */
.stApp {
    background:
        radial-gradient(circle at 15% 20%, rgba(255, 215, 0, 0.16) 0%, transparent 40%),
        radial-gradient(circle at 85% 30%, rgba(255, 136, 0, 0.14) 0%, transparent 45%),
        linear-gradient(135deg, #06070a 0%, #151108 50%, #06070a 100%) !important;
    background-size: 200% 200% !important;
    animation: solarLava 14s ease infinite alternate !important;
}

@keyframes solarLava {
    0% { background-position: 0% 0%; }
    50% { background-position: 100% 100%; }
    100% { background-position: 0% 100%; }
}

.brand-signature {
    text-align: center;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.72rem;
    letter-spacing: 0.18em;
    color: #ffd700;
    text-transform: uppercase;
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
    margin-bottom: 1.4rem;
}

div.stButton > button {
    border-radius: 6px !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.85rem !important;
    transition: all 0.25s ease !important;
}

div.stButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 0 20px rgba(255, 215, 0, 0.4) !important;
}

.advice-card {
    background: rgba(255, 215, 0, 0.05);
    border: 1px solid rgba(255, 215, 0, 0.25);
    border-radius: 8px;
    padding: 14px;
    margin-bottom: 10px;
}
</style>
""", unsafe_allow_html=True)

# -------------------------------------------------------------
# PRESETS RICOS CON TEXTOS EXTENSOS Y VARIADOS
# -------------------------------------------------------------
PRESETS_RICOS = {
    "pitch": (
        "¡Equipo, logramos un resultado extraordinario este trimestre! Superamos con creces todas las proyecciones "
        "comerciales gracias a la constancia, el talento y la dedicación incansable de cada integrante. Esta victoria confirma "
        "que nuestra visión estratégica es acertada y nos impulsa con enorme entusiasmo a conquistar nuevos mercados."
    ),
    "reclamo": (
        "Estoy sumamente molesto y decepcionado con el servicio recibido. Llevo tres semanas esperando una respuesta concreta "
        "y la única atención que brindan son evasivas y respuestas automatizadas inaceptables. El producto llegó defectuoso, "
        "nadie se hace responsable y el trato de su personal fue grosero y pésimo. Exijo una solución inmediata y el reembolso íntegro de mi dinero."
    ),
    "tecnico": (
        "El microservicio procesa eventos mediante una cola asíncrona distribuida en tres nodos redundantes. "
        "La latencia promedio registrada se sitúa en catorce milisegundos bajo una carga constante de setenta por ciento. "
        "Las copias de seguridad de los registros se ejecutan de forma automática cada cuatro horas sin degradar el rendimiento."
    ),
    "crisis": (
        "Reconocemos el impacto negativo originado por la caída de los servidores durante las primeras horas de hoy. "
        "Entendemos la frustración y los inconvenientes causados a las operaciones de nuestros usuarios. Nuestro equipo técnico "
        "activó de inmediato el plan de recuperación y continuará trabajando de manera ininterrumpida hasta restablecer la totalidad de los servicios."
    )
}

if "analisis_txt" not in st.session_state:
    st.session_state.analisis_txt = PRESETS_RICOS["pitch"]

st.markdown('<div class="brand-signature">Krov Industries · Analítica Semántica</div>', unsafe_allow_html=True)
st.markdown('<div class="main-title">Analizador de Tono y Emociones</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-lead">Medición rigurosa de polaridad, objetividad y trayectoria emocional</div>', unsafe_allow_html=True)

c1, c2, c3, c4 = st.columns(4)
with c1:
    if st.button("🚀 Entusiasmo / Pitch", use_container_width=True):
        st.session_state.analisis_txt = PRESETS_RICOS["pitch"]
        st.rerun()
with c2:
    if st.button("🛑 Reclamo Severo", use_container_width=True):
        st.session_state.analisis_txt = PRESETS_RICOS["reclamo"]
        st.rerun()
with c3:
    if st.button("📋 Reporte Técnico", use_container_width=True):
        st.session_state.analisis_txt = PRESETS_RICOS["tecnico"]
        st.rerun()
with c4:
    if st.button("⚠️ Manejo de Crisis", use_container_width=True):
        st.session_state.analisis_txt = PRESETS_RICOS["crisis"]
        st.rerun()

texto = st.text_area("Texto a evaluar:", value=st.session_state.analisis_txt, height=130)

if texto.strip():
    # Traducción rápida para asegurar cálculo de sentimiento TextBlob preciso
    try:
        import urllib.request, urllib.parse, json
        url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=es&tl=en&dt=t&q={urllib.parse.quote(texto)}"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=3) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            en_txt = "".join(p[0] for p in data[0] if p[0])
            blob = TextBlob(en_txt)
    except Exception:
        blob = TextBlob(texto)

    pol = round(blob.sentiment.polarity, 2)
    subj = round(blob.sentiment.subjectivity, 2)

    palabras = re.findall(r"\b\w+\b", texto.lower())
    total_w = len(palabras)
    unicas_w = len(set(palabras))
    diversidad = round((unicas_w / max(1, total_w)) * 100, 1)

    # Cálculo por oraciones
    frases = [f.strip() for f in re.split(r"[.!?]+", texto) if len(f.strip()) > 3]
    trayectoria = []
    for idx, f in enumerate(frases, 1):
        b_f = TextBlob(f)
        trayectoria.append({"idx": idx, "frase": f, "pol": round(b_f.sentiment.polarity, 2)})

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Palabras", total_w)
    m2.metric("Vocabulario único", f"{diversidad}%")
    m3.metric("Sentimiento", f"{pol:+.2f}")
    m4.metric("Subjetividad", f"{int(subj * 100)}%")

    st.write("")
    tab1, tab2, tab3 = st.tabs(["Velocímetros y Radar", "Trayectoria por Frase", "Sugerencias de Estilo"])

    with tab1:
        g1, g2 = st.columns(2)
        with g1:
            fig_g = go.Figure(go.Indicator(
                mode="gauge+number",
                value=pol,
                title={"text": "Polaridad de Tono (-1 Negativo a +1 Positivo)"},
                gauge={
                    "axis": {"range": [-1, 1]},
                    "bar": {"color": "#ffd700"},
                    "steps": [
                        {"range": [-1, -0.15], "color": "rgba(239, 68, 68, 0.35)"},
                        {"range": [-0.15, 0.15], "color": "rgba(148, 163, 184, 0.35)"},
                        {"range": [0.15, 1], "color": "rgba(16, 185, 129, 0.35)"}
                    ]
                }
            ))
            fig_g.update_layout(height=230, margin=dict(l=20,r=20,t=40,b=20), paper_bgcolor="rgba(0,0,0,0)", font={"color": "#f1f5f9"})
            st.plotly_chart(fig_g, use_container_width=True)

        with g2:
            fig_s = go.Figure(go.Indicator(
                mode="gauge+number",
                value=subj,
                title={"text": "Subjetividad (0 Objetivo a 1 Opinión)"},
                gauge={
                    "axis": {"range": [0, 1]},
                    "bar": {"color": "#38bdf8"},
                    "steps": [
                        {"range": [0, 0.4], "color": "rgba(14, 165, 233, 0.25)"},
                        {"range": [0.4, 1], "color": "rgba(168, 85, 247, 0.35)"}
                    ]
                }
            ))
            fig_s.update_layout(height=230, margin=dict(l=20,r=20,t=40,b=20), paper_bgcolor="rgba(0,0,0,0)", font={"color": "#f1f5f9"})
            st.plotly_chart(fig_s, use_container_width=True)

        # Radar pentagonal
        pos_s = max(0, min(100, int(((pol + 1) / 2) * 100)))
        obj_s = max(0, min(100, int((1 - subj) * 100)))
        dim_cats = ["Positividad", "Objetividad", "Vocabulario", "Claridad", "Fuerza"]
        dim_vals = [pos_s, obj_s, int(diversidad), 85, int(abs(pol)*60 + subj*40)]
        dim_vals += dim_vals[:1]
        dim_cats += dim_cats[:1]

        fig_r = go.Figure(go.Scatterpolar(
            r=dim_vals, theta=dim_cats, fill="toself",
            fillcolor="rgba(255, 215, 0, 0.2)", line=dict(color="#ffd700", width=2)
        ))
        fig_r.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 100], gridcolor="rgba(255,255,255,0.1)"), bgcolor="rgba(0,0,0,0)"),
            height=260, margin=dict(l=30, r=30, t=30, b=20), paper_bgcolor="rgba(0,0,0,0)", font={"color": "#f1f5f9"}
        )
        st.plotly_chart(fig_r, use_container_width=True)

    with tab2:
        if trayectoria:
            df_tray = pd.DataFrame(trayectoria)
            fig_t = go.Figure(go.Scatter(
                x=df_tray["idx"], y=df_tray["pol"], mode="lines+markers",
                line=dict(color="#00f0ff", width=2.5), marker=dict(size=8, color="#ffd700")
            ))
            fig_t.add_hline(y=0, line_dash="dash", line_color="rgba(255,255,255,0.3)")
            fig_t.update_layout(
                title="Evolución del Sentimiento por Frase", height=230,
                xaxis_title="Frase", yaxis_title="Polaridad (-1 a +1)",
                margin=dict(l=30, r=20, t=40, b=30), paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(12,16,28,0.7)", font={"color": "#94a3b8"}
            )
            st.plotly_chart(fig_t, use_container_width=True)
            st.dataframe(df_tray.rename(columns={"idx": "N.º", "frase": "Frase", "pol": "Polaridad"}).set_index("N.º"), use_container_width=True)

    with tab3:
        st.markdown("#### Recomendaciones de redacción")
        if pol < -0.15:
            st.markdown('<div class="advice-card"><b>Tono confrontacional:</b> Se detecta fuerte inconformidad. Si el objetivo es negociar o resolver un problema, enfócate en solicitar soluciones puntuales.</div>', unsafe_allow_html=True)
        elif pol > 0.35:
            st.markdown('<div class="advice-card"><b>Tono inspirador:</b> Excelente nivel de motivación. Asegúrate de complementar con una llamada clara a la acción.</div>', unsafe_allow_html=True)

        if subj > 0.6:
            st.markdown('<div class="advice-card"><b>Alta carga subjetiva:</b> El texto se apoya fuertemente en impresiones personales. Incorporar cifras o datos verificables reforzará su credibilidad.</div>', unsafe_allow_html=True)
        elif subj < 0.25:
            st.markdown('<div class="advice-card"><b>Estilo formal y distante:</b> La redacción es estrictamente objetiva. Ideal para documentación técnica o reportes operativos.</div>', unsafe_allow_html=True)
