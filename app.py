import base64
import platform

import numpy as np
import paho.mqtt.publish as publish
import streamlit as st
from keras.models import load_model
from PIL import Image

# ---------------------------------------------------------------
# CONFIGURACIÓN
# ---------------------------------------------------------------
MQTT_BROKER = "broker.mqttgo.io"      # o "broker.hivemq.com" (el mismo que uses en Wokwi)
MQTT_PORT = 1883
TOPIC_EMOCION = "mi_app/emociones"    # un solo topic: payload = FELIZ / TRISTE / OFF

AUDIO_FELIZ = "feliz.mp3"             # pon aquí tus archivos de audio
AUDIO_TRISTE = "triste.mp3"

UMBRAL = 0.5


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
    """estado: 'FELIZ', 'TRISTE' u 'OFF'"""
    enviar_mqtt(TOPIC_EMOCION, estado)


# ---------------------------------------------------------------
# INTERFAZ
# ---------------------------------------------------------------
st.write("Versión de Python:", platform.python_version())

model = cargar_modelo()

st.title("Reconocimiento de Imágenes")

with open("OIG5.jpg", "rb") as f:
    b64 = base64.b64encode(f.read()).decode()
st.html(f'<img src="data:image/jpeg;base64,{b64}" width="350">')

with st.sidebar:
    st.subheader(
        "Usando un modelo entrenado en teachable Machine puedes Usarlo en esta app para identificar"
    )

img_file_buffer = st.camera_input("Toma una Foto")

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
        st.header(
            f"Estás: {p_feliz * 100:.1f}% Feliz! "
            "Aquí hay una iluminación y un track que te pondrá en buenos ánimos"
        )
        actualizar_leds("FELIZ")
        st.audio(AUDIO_FELIZ, autoplay=True)

    elif p_triste > UMBRAL:
        st.header(
            f"Estás: {p_triste * 100:.1f}% Triste. "
            "Aquí hay una música y una iluminación que te dejaran estar en un poco de paz"
        )
        actualizar_leds("TRISTE")
        st.audio(AUDIO_TRISTE, autoplay=True)

    else:
        st.info("No pude determinar tu estado con suficiente confianza. Intenta otra foto.")
        actualizar_leds("OFF")
