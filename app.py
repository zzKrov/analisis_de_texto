import re
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
# ESTILOS VISUALES: ORO SOLAR Y GASÓMETROS ANIMADOS
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

/* Fondo líquido animado en GPU */
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
    box-shadow: 0 0 25px rgba(255, 215, 0, 0.45) !important;
}

.advice-card {
    background: rgba(255, 215, 0, 0.05);
    border: 1px solid rgba(255, 215, 0, 0.25);
    border-radius: 8px;
    padding: 14px;
    margin-bottom: 10px;
    box-shadow: 0 4px 15px rgba(0,0,0,0.4);
}
</style>
""", unsafe_allow_html=True)

# ============================================================
# MOTOR LÉXICO Y SEMÁNTICO NATIVO EN ESPAÑOL (SIN 0.00 FIJO)
# ============================================================
LEXICO_POSITIVO = {
    "extraordinario": 0.9, "excelente": 0.85, "increíble": 0.85, "triunfo": 0.8,
    "éxito": 0.8, "victoria": 0.8, "logramos": 0.7, "superamos": 0.7,
    "talento": 0.6, "constancia": 0.6, "dedicación": 0.6, "entusiasmo": 0.75,
    "conquistar": 0.6, "felicitaciones": 0.8, "maravilloso": 0.85, "genial": 0.75,
    "acertada": 0.6, "agradecido": 0.65, "alegría": 0.7, "óptimo": 0.7, "eficaz": 0.6,
    "ventaja": 0.5, "feliz": 0.75, "brillante": 0.75, "confirma": 0.4, "bueno": 0.5
}

LEXICO_NEGATIVO = {
    "pésimo": -0.9, "grosero": -0.85, "inaceptable": -0.85, "decepcionado": -0.8,
    "molesto": -0.75, "defectuoso": -0.7, "evasivas": -0.65, "retraso": -0.6,
    "frustración": -0.7, "inconvenientes": -0.5, "negativo": -0.6, "caída": -0.5,
    "fallos": -0.6, "desastre": -0.85, "terrible": -0.8, "enojo": -0.75,
    "rabia": -0.8, "daño": -0.6, "error": -0.5, "lamentamos": -0.45, "peor": -0.7,
    "malo": -0.5, "exijo": -0.4, "inútil": -0.7, "injusto": -0.75
}

INTENSIFICADORES = {"muy": 1.4, "sumamente": 1.6, "profundamente": 1.5, "enormemente": 1.5, "totalmente": 1.4, "completamente": 1.4}
NEGADORES = {"no", "nunca", "jamás", "sin", "tampoco", "nadie"}

def analizar_espanol_nativo(texto: str):
    palabras = re.findall(r"\b\w+\b", texto.lower())
    total_w = len(palabras)
    if total_w == 0:
        return 0.0, 0.0, 0, 0.0, []

    puntuacion_polaridad = 0.0
    palabras_con_carga = 0
    subjetividad_score = 0.0

    frases = [f.strip() for f in re.split(r"[.!?]+", texto) if len(f.strip()) > 3]
    trayectoria = []

    for idx, frase in enumerate(frases, 1):
        palabras_f = re.findall(r"\b\w+\b", frase.lower())
        pol_f = 0.0
        conteo_f = 0

        for i, p in enumerate(palabras_f):
            multiplicador = 1.0
            # Comprueba intensificador previo
            if i > 0 and palabras_f[i-1] in INTENSIFICADORES:
                multiplicador *= INTENSIFICADORES[palabras_f[i-1]]
            # Comprueba negador previo
            if i > 0 and palabras_f[i-1] in NEGADORES:
                multiplicador *= -1.0
            elif i > 1 and palabras_f[i-2] in NEGADORES:
                multiplicador *= -1.0

            if p in LEXICO_POSITIVO:
                val = LEXICO_POSITIVO[p] * multiplicador
                pol_f += val
                conteo_f += 1
                subjetividad_score += 1.0
            elif p in LEXICO_NEGATIVO:
                val = LEXICO_NEGATIVO[p] * multiplicador
                pol_f += val
                conteo_f += 1
                subjetividad_score += 1.0

        puntuacion_polaridad += pol_f
        palabras_con_carga += conteo_f
        media_f = round(max(-1.0, min(1.0, pol_f / max(1, conteo_f))), 2) if conteo_f > 0 else 0.0
        trayectoria.append({"idx": idx, "frase": frase, "pol": media_f})

    if palabras_con_carga > 0:
        polaridad_final = round(max(-1.0, min(1.0, puntuacion_polaridad / palabras_con_carga)), 2)
    else:
        polaridad_final = 0.0

    subjetividad_final = round(min(1.0, (subjetividad_score * 3.5) / max(1, total_w)), 2)
    unicas_w = len(set(palabras))
    diversidad = round((unicas_w / max(1, total_w)) * 100, 1)

    return polaridad_final, subjetividad_final, total_w, diversidad, trayectoria

# ============================================================
# PRESETS RICOS CON TEXTOS EXTENSOS
# ============================================================
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
st.markdown('<div class="sub-lead">Medición rigurosa de polaridad afectiva, objetividad y estructura del discurso</div>', unsafe_allow_html=True)

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
    pol, subj, total_w, diversidad, trayectoria = analizar_espanol_nativo(texto)

    # Componente HTML con Gasómetros animados que crecen y escalan números desde cero
    gasometros_html = f"""
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

    // Animación numérica desde 0 hasta el valor final
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

    // Animación de llenado de barra
    setTimeout(() => {{
        const polPercent = Math.max(5, Math.min(100, Math.round(((targetPol + 1.0) / 2.0) * 100)));
        document.getElementById('bar-pol').style.width = polPercent + '%';
        document.getElementById('bar-subj').style.width = Math.max(5, targetSubj) + '%';
    }}, 80);
    </script>
    </body>
    </html>
    """
    components.html(gasometros_html, height=140)

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Palabras", total_w)
    m2.metric("Vocabulario único", f"{diversidad}%")
    m3.metric("Sentimiento", f"{pol:+.2f}")
    m4.metric("Subjetividad", f"{int(subj * 100)}%")

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
                xaxis_title="Frase", yaxis_title="Polaridad (-1 a +1)",
                margin=dict(l=30, r=20, t=40, b=30), paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(12,16,28,0.7)", font={"color": "#94a3b8"}
            )
            st.plotly_chart(fig_t, use_container_width=True)
            st.dataframe(df_tray.rename(columns={"idx": "N.º", "frase": "Frase", "pol": "Polaridad"}).set_index("N.º"), use_container_width=True)

    with tab2:
        st.markdown("#### Recomendaciones de redacción")
        if pol < -0.15:
            st.markdown('<div class="advice-card"><b>Tono de queja o molestia:</b> Se detecta fuerte inconformidad. Para negociaciones, se sugiere enfocar las demandas en acciones concretas.</div>', unsafe_allow_html=True)
        elif pol > 0.35:
            st.markdown('<div class="advice-card"><b>Tono entusiasta y motivador:</b> Excelente nivel de energía positiva. Asegúrate de incluir llamadas claras a la acción.</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="advice-card"><b>Tono neutral u objetivo:</b> El mensaje se mantiene enfocado en hechos sin sesgo emocional marcado.</div>', unsafe_allow_html=True)

        if subj > 0.6:
            st.markdown('<div class="advice-card"><b>Alta carga subjetiva:</b> El texto se apoya en impresiones y adjetivos. Incorporar métricas o datos aumentará su precisión.</div>', unsafe_allow_html=True)
        elif subj < 0.25:
            st.markdown('<div class="advice-card"><b>Estilo técnico u operativo:</b> Redacción concisa y desprovista de juicio de valor. Óptimo para manuales e informes.</div>', unsafe_allow_html=True)
