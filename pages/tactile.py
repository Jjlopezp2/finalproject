import base64
from urllib.parse import quote

import paho.mqtt.publish as publish
import streamlit as st

# ---------------------------------------------------------------
# CONFIGURACIÓN
# ---------------------------------------------------------------
MQTT_BROKER = "broker.mqttdashboard.com"      # o "broker.hivemq.com" (el mismo que uses en Wokwi)
MQTT_PORT = 1883
TOPIC_EMOCION = "myapp/MusicalMe"    # un solo topic: payload = up / down

AUDIO_FELIZ = "feliz.mp3"             # pon aquí tus archivos de audio
AUDIO_TRISTE = "triste.mp3"

st.set_page_config(page_title="MusicalMe", page_icon="☁️", layout="centered")

# ---------------------------------------------------------------
# ILUSTRACIONES (SVG geométrico, se usan como fondo de los botones)
# ---------------------------------------------------------------
SVG_NUBE_SOL = """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 150">
  <g stroke="#93C5FD" stroke-width="4" stroke-linecap="round">
    <line x1="148" y1="6"  x2="148" y2="16"/>
    <line x1="176" y1="18" x2="169" y2="25"/>
    <line x1="188" y1="46" x2="178" y2="46"/>
    <line x1="120" y1="18" x2="127" y2="25"/>
  </g>
  <circle cx="148" cy="46" r="22" fill="#93C5FD"/>
  <g fill="#DBEAFE">
    <rect x="28" y="78" width="140" height="44" rx="22"/>
    <circle cx="74" cy="76" r="30"/>
    <circle cx="116" cy="68" r="36"/>
  </g>
</svg>
"""

SVG_NUBE_LLUVIA = """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 150">
  <g fill="#C7D6EE">
    <rect x="28" y="40" width="144" height="46" rx="23"/>
    <circle cx="74" cy="40" r="28"/>
    <circle cx="118" cy="32" r="34"/>
  </g>
  <g stroke="#3B82F6" stroke-width="5" stroke-linecap="round">
    <line x1="60"  y1="102" x2="54"  y2="120"/>
    <line x1="90"  y1="102" x2="84"  y2="120"/>
    <line x1="120" y1="102" x2="114" y2="120"/>
    <line x1="150" y1="102" x2="144" y2="120"/>
    <line x1="75"  y1="124" x2="69"  y2="142"/>
    <line x1="105" y1="124" x2="99"  y2="142"/>
    <line x1="135" y1="124" x2="129" y2="142"/>
  </g>
</svg>
"""


def svg_a_css(svg: str) -> str:
    """Convierte un SVG en un valor url(...) para usar en CSS."""
    return 'url("data:image/svg+xml;utf8,' + quote(" ".join(svg.split())) + '")'


# ---------------------------------------------------------------
# ESTILO  (minimalista · geométrico · cielo y nubes)
# ---------------------------------------------------------------
ESTILO = """
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;700&display=swap');

:root {
    --azul-profundo: #1D4ED8;
    --azul: #3B82F6;
    --azul-cielo: #93C5FD;
    --azul-nube: #DBEAFE;
    --azul-bruma: #F0F7FF;
    --tinta: #0F2547;
}

html, body, [class*="css"], .stApp {
    font-family: 'DM Sans', sans-serif;
    color: var(--tinta);
}

.stApp { background: #FFFFFF; }

/* Limpieza de la interfaz por defecto */
#MainMenu, footer { visibility: hidden; }
header[data-testid="stHeader"] { background: transparent; }
.block-container { max-width: 760px; padding-top: 2rem; padding-bottom: 4rem; }

/* ---------- Hero ---------- */
.hero {
    position: relative;
    overflow: hidden;
    padding: 3.2rem 2rem 2.6rem;
    border-radius: 28px;
    background: linear-gradient(180deg, var(--azul-bruma) 0%, #FFFFFF 100%);
    border: 1px solid var(--azul-nube);
    text-align: center;
    margin-bottom: 1.5rem;
}
.hero .sol {
    position: absolute; top: 24px; right: 40px;
    width: 64px; height: 64px; border-radius: 50%;
    border: 2px solid var(--azul-cielo);
}
.hero .sol::after {
    content: ""; position: absolute; inset: 14px;
    border-radius: 50%; background: var(--azul-cielo); opacity: .55;
}
.hero .aro {
    position: absolute; bottom: -90px; left: -60px;
    width: 220px; height: 220px; border-radius: 50%;
    border: 1.5px solid var(--azul-nube);
}
.hero .aro.dos { bottom: -130px; left: -100px; width: 300px; height: 300px; }

.nube {
    position: absolute;
    width: 110px; height: 30px;
    background: var(--azul-nube);
    border-radius: 30px;
}
.nube::before, .nube::after {
    content: ""; position: absolute; background: inherit; border-radius: 50%;
}
.nube::before { width: 44px; height: 44px; left: 18px; bottom: 10px; }
.nube::after  { width: 32px; height: 32px; left: 54px; bottom: 10px; }
.nube.a { top: 34px; left: 34px; }
.nube.b { top: 96px; right: 14%; transform: scale(.7); opacity: .8; }
.nube.c { bottom: 26px; right: 30px; transform: scale(.5); opacity: .7; }

.hero h1 {
    position: relative;
    font-weight: 300; font-size: 2.6rem; letter-spacing: -0.02em;
    margin: 0; padding: 0; color: var(--tinta);
}
.hero h1 b { font-weight: 700; color: var(--azul-profundo); }
.hero p {
    position: relative;
    margin: .8rem auto 0; max-width: 460px;
    font-size: 1rem; font-weight: 400; color: #4A6285;
}
.linea {
    position: relative; width: 48px; height: 3px; border-radius: 3px;
    background: var(--azul); margin: 1.1rem auto 0;
}

/* ---------- Imagen ---------- */
.imagen-wrap { display: flex; justify-content: center; margin: 0 0 1.5rem; }
.imagen-wrap img {
    width: 260px; height: 260px; object-fit: cover;
    border-radius: 50%;
    border: 6px solid #FFFFFF;
    box-shadow: 0 0 0 2px var(--azul-cielo), 0 18px 40px rgba(59, 130, 246, .18);
}

/* ---------- Sidebar ---------- */
section[data-testid="stSidebar"] {
    background: var(--azul-bruma);
    border-right: 1px solid var(--azul-nube);
}
section[data-testid="stSidebar"] h3 {
    font-size: 1rem; font-weight: 500; line-height: 1.6; color: var(--tinta);
}
.sidebar-icono {
    width: 40px; height: 40px; border-radius: 50%;
    border: 2px solid var(--azul-cielo);
    display: flex; align-items: center; justify-content: center;
    margin-bottom: 1rem;
}
.sidebar-icono span {
    width: 16px; height: 16px; border-radius: 50%; background: var(--azul);
}

/* ---------- Pregunta ---------- */
.pregunta {
    text-align: center; font-size: .78rem; letter-spacing: .2em;
    text-transform: uppercase; font-weight: 700; color: var(--azul);
    margin: .5rem 0 1rem;
}

/* ---------- Botones nube ---------- */
.st-key-btn_feliz button,
.st-key-btn_triste button {
    width: 100%;
    height: 250px;
    border-radius: 28px;
    border: 1px solid var(--azul-nube);
    background-color: var(--azul-bruma);
    background-repeat: no-repeat;
    background-position: center 18px;
    background-size: 190px auto;
    display: flex;
    align-items: flex-end;
    justify-content: center;
    padding-bottom: 1.3rem;
    transition: transform .25s ease, box-shadow .25s ease, border-color .25s ease;
}
.st-key-btn_feliz button p,
.st-key-btn_triste button p {
    font-size: 1.05rem; font-weight: 700; letter-spacing: .22em;
    color: var(--azul-profundo);
}
.st-key-btn_feliz button  { background-image: __NUBE_SOL__; }
.st-key-btn_triste button { background-image: __NUBE_LLUVIA__; }

.st-key-btn_feliz button:hover,
.st-key-btn_triste button:hover {
    transform: translateY(-4px);
    border-color: var(--azul-cielo);
    box-shadow: 0 16px 34px rgba(59, 130, 246, .18);
    background-color: var(--azul-bruma);
    color: var(--azul-profundo);
}
.st-key-btn_feliz button:active,
.st-key-btn_triste button:active {
    transform: translateY(-1px);
    background-color: var(--azul-nube);
}
.st-key-btn_feliz button:focus:not(:active),
.st-key-btn_triste button:focus:not(:active) {
    border-color: var(--azul);
    box-shadow: 0 0 0 3px var(--azul-nube);
    color: var(--azul-profundo);
}

/* ---------- Tarjeta de resultado ---------- */
.resultado {
    position: relative; overflow: hidden;
    margin: 1.8rem 0 1rem;
    padding: 1.8rem 1.8rem 1.8rem 2.2rem;
    border-radius: 24px;
    background: var(--azul-bruma);
    border: 1px solid var(--azul-nube);
}
.resultado::before {
    content: ""; position: absolute; left: 0; top: 0; bottom: 0; width: 8px;
    background: var(--azul);
}
.resultado.triste { background: #F5F8FC; }
.resultado.triste::before { background: var(--azul-cielo); }
.resultado .etiqueta {
    font-size: .75rem; letter-spacing: .18em; text-transform: uppercase;
    color: var(--azul); font-weight: 700;
}
.resultado .estado {
    font-size: 2.6rem; font-weight: 300; letter-spacing: -0.03em;
    color: var(--azul-profundo); line-height: 1.15; margin: .2rem 0 .5rem;
}
.resultado .texto { color: #4A6285; font-size: 1rem; line-height: 1.55; margin: 0; }

/* ---------- Mensajes y audio ---------- */
[data-testid="stAlert"] {
    border-radius: 18px;
    background: var(--azul-bruma);
    border: 1px solid var(--azul-nube);
    color: var(--tinta);
}
audio { width: 100%; border-radius: 999px; }
</style>
"""

ESTILO = ESTILO.replace("__NUBE_SOL__", svg_a_css(SVG_NUBE_SOL)).replace(
    "__NUBE_LLUVIA__", svg_a_css(SVG_NUBE_LLUVIA)
)
st.markdown(ESTILO, unsafe_allow_html=True)


# ---------------------------------------------------------------
# FUNCIONES
# ---------------------------------------------------------------
def enviar_mqtt(topic, mensaje):
    """Publica un mensaje MQTT y avisa si algo falla."""
    try:
        publish.single(topic, mensaje, hostname=MQTT_BROKER, port=MQTT_PORT)
        return True
    except Exception as e:
        st.warning(f"No se pudo enviar MQTT a {topic}: {e}")
        return False


def actualizar_leds(estado: str):
    """estado: 'up' o 'down'"""
    enviar_mqtt(TOPIC_EMOCION, estado)


def tarjeta_resultado(etiqueta: str, estado: str, texto: str, clase: str = ""):
    st.markdown(
        f"""
        <div class="resultado {clase}">
            <div class="etiqueta">{etiqueta}</div>
            <div class="estado">{estado}</div>
            <p class="texto">{texto}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------
# INTERFAZ
# ---------------------------------------------------------------
st.markdown(
    """
    <div class="hero">
        <div class="sol"></div>
        <div class="aro"></div><div class="aro dos"></div>
        <div class="nube a"></div><div class="nube b"></div><div class="nube c"></div>
        <h1>Musical<b>Me</b></h1>
        <p>Hola, te doy la bienvenida. Dime cómo te sientes, y tu cuarto se llena de la luz y la música que necesitas.</p>
        <div class="linea"></div>
    </div>
    """,
    unsafe_allow_html=True,
)

with open("OIG5.jpg", "rb") as f:
    b64 = base64.b64encode(f.read()).decode()
st.markdown(
    f'<div class="imagen-wrap"><img src="data:image/jpeg;base64,{b64}"></div>',
    unsafe_allow_html=True,
)

with st.sidebar:
    st.markdown('<div class="sidebar-icono"><span></span></div>', unsafe_allow_html=True)
    st.subheader(
        "Te doy la bienvenida a tu cuarto nuevamente, elige cómo te sientes para adaptar tu iluminación y música de fondo"
    )

st.markdown('<div class="pregunta">¿Cómo te sientes hoy?</div>', unsafe_allow_html=True)

col1, col2 = st.columns(2, gap="medium")
with col1:
    if st.button("FELIZ", key="btn_feliz", use_container_width=True):
        st.session_state["estado"] = "feliz"
        actualizar_leds("up")
with col2:
    if st.button("TRISTE", key="btn_triste", use_container_width=True):
        st.session_state["estado"] = "triste"
        actualizar_leds("down")

estado = st.session_state.get("estado")

if estado == "feliz":
    tarjeta_resultado(
        "Estás",
        "Feliz",
        "Aquí hay una iluminación y un track que te pondrá en buenos ánimos.",
    )
    st.audio(AUDIO_FELIZ, autoplay=True)

elif estado == "triste":
    tarjeta_resultado(
        "Estás",
        "Triste",
        "Aquí hay una música y una iluminación que te dejarán estar en un poco de paz.",
        clase="triste",
    )
    st.audio(AUDIO_TRISTE, autoplay=True)
