import base64

import numpy as np
import paho.mqtt.publish as publish
import streamlit as st
from keras.models import load_model
from PIL import Image

# ---------------------------------------------------------------
# CONFIGURACIÓN
# ---------------------------------------------------------------
MQTT_BROKER = "broker.mqttdashboard.com"      # o "broker.hivemq.com" (el mismo que uses en Wokwi)
MQTT_PORT = 1883
TOPIC_EMOCION = "myapp/MusicalMe"    # un solo topic: payload = up / down / OFF

AUDIO_FELIZ = "feliz.mp3"             # pon aquí tus archivos de audio
AUDIO_TRISTE = "triste.mp3"

UMBRAL = 0.5

st.set_page_config(page_title="MusicalMe", page_icon="☁️", layout="centered")

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

/* Nubes geométricas: una pastilla + dos círculos */
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

/* ---------- Cámara ---------- */
[data-testid="stCameraInput"] {
    background: var(--azul-bruma);
    border: 1px solid var(--azul-nube);
    border-radius: 24px;
    padding: 1rem;
}
[data-testid="stCameraInput"] video,
[data-testid="stCameraInput"] img { border-radius: 16px; }
[data-testid="stCameraInput"] label p {
    font-weight: 500; color: var(--azul-profundo);
}

/* ---------- Botones ---------- */
.stButton > button,
[data-testid="stCameraInput"] button {
    background: var(--azul);
    color: #FFFFFF;
    border: none;
    border-radius: 999px;
    padding: .5rem 1.4rem;
    font-weight: 500;
    transition: background .2s ease, transform .2s ease;
}
.stButton > button:hover,
[data-testid="stCameraInput"] button:hover {
    background: var(--azul-profundo);
    color: #FFFFFF;
    transform: translateY(-1px);
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
.resultado .pct {
    font-size: 3rem; font-weight: 300; letter-spacing: -0.03em;
    color: var(--azul-profundo); line-height: 1.1; margin: .2rem 0 .5rem;
}
.resultado .pct small { font-size: 1.1rem; font-weight: 500; margin-left: .3rem; }
.resultado .texto { color: #4A6285; font-size: 1rem; line-height: 1.55; margin: 0; }

/* Barra de confianza */
.barra { height: 6px; border-radius: 6px; background: var(--azul-nube); margin-top: 1.2rem; }
.barra > div { height: 100%; border-radius: 6px; background: var(--azul); }

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

st.markdown(ESTILO, unsafe_allow_html=True)


# ---------------------------------------------------------------
# FUNCIONES
# ---------------------------------------------------------------
@st.cache_resource
def cargar_modelo():
    return load_model("keras_model.h5")


def enviar_mqtt(topic, mensaje):
    """Publica un mensaje MQTT y avisa si algo falla."""
    try:
        publish.single(topic, mensaje, hostname=MQTT_BROKER, port=MQTT_PORT)
        return True
    except Exception as e:
        st.warning(f"No se pudo enviar MQTT a {topic}: {e}")
        return False


def actualizar_leds(estado: str):
    """estado: 'up', 'down' u 'OFF'"""
    enviar_mqtt(TOPIC_EMOCION, estado)


def tarjeta_resultado(etiqueta: str, porcentaje: float, texto: str, clase: str = ""):
    st.markdown(
        f"""
        <div class="resultado {clase}">
            <div class="etiqueta">{etiqueta}</div>
            <div class="pct">{porcentaje:.1f}<small>%</small></div>
            <p class="texto">{texto}</p>
            <div class="barra"><div style="width:{porcentaje:.1f}%"></div></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------
# INTERFAZ
# ---------------------------------------------------------------
model = cargar_modelo()

st.markdown(
    """
    <div class="hero">
        <div class="sol"></div>
        <div class="aro"></div><div class="aro dos"></div>
        <div class="nube a"></div><div class="nube b"></div><div class="nube c"></div>
        <h1>Musical<b>Me</b></h1>
        <p>Hola, te doy la bienvenida. Una foto, y tu cuarto se llena de la luz y la música que necesitas.</p>
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
        "Te doy la bienvenida a tu cuarto nuevamente, toma tu foto para adaptar tu ilumiación y música de fondo"
    )

img_file_buffer = st.camera_input("Toma una foto")

if img_file_buffer is not None:
    # Preparar la imagen
    img = Image.open(img_file_buffer).convert("RGB").resize((224, 224))
    img_array = np.array(img)
    normalized_image_array = (img_array.astype(np.float32) / 127.0) - 1

    data = np.ndarray(shape=(1, 224, 224, 3), dtype=np.float32)
    data[0] = normalized_image_array

    # Inferencia
    prediction = model.predict(data)
    p_feliz = float(prediction[0][0])
    p_triste = float(prediction[0][1])

    # Se elige el estado con mayor probabilidad (si supera el umbral)
    if p_feliz > UMBRAL and p_feliz >= p_triste:
        tarjeta_resultado(
            "Estás feliz",
            p_feliz * 100,
            "Aquí hay una iluminación y un track que te pondrá en buenos ánimos.",
        )
        actualizar_leds("up")
        st.audio(AUDIO_FELIZ, autoplay=True)

    elif p_triste > UMBRAL:
        tarjeta_resultado(
            "Estás triste",
            p_triste * 100,
            "Aquí hay una música y una iluminación que te dejarán estar en un poco de paz.",
            clase="triste",
        )
        actualizar_leds("down")
        st.audio(AUDIO_TRISTE, autoplay=True)

    else:
        st.info("No pude determinar tu estado con suficiente confianza. Intenta otra foto.")
        actualizar_leds("OFF")
