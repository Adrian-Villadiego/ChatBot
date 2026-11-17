
import asyncio
import os
import tempfile

from pathlib import Path
from faster_whisper import WhisperModel
from telegram import Update
from telegram.ext import ContextTypes

from predict import analizar_texto

# Modelo de transcripción
# "base" ofrece un equilibrio entre velocidad y precisión.
modelo_whisper = None


def obtener_modelo():
    global modelo_whisper

    if modelo_whisper is None:
        print("Cargando modelo Whisper...")

        modelo_whisper = WhisperModel(
            "base",
            device="cpu",
            compute_type="int8"
        )

        print("Modelo Whisper cargado correctamente")

    return modelo_whisper


def transcribir_audio(ruta_audio):
    modelo = obtener_modelo()

    segmentos, informacion = modelo.transcribe(
        ruta_audio,
        language="es",
        beam_size=5,
        vad_filter=True
    )

    texto = " ".join(
        segmento.text.strip()
        for segmento in segmentos
    ).strip()

    return texto


async def recibir_audio(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    mensaje = update.message

    if not mensaje:
        return

    audio = mensaje.voice or mensaje.audio

    if not audio:
        return

    if audio.file_size and audio.file_size > 20 * 1024 * 1024:
        await mensaje.reply_text(
            "El audio supera el límite de 20 MB."
        )
        return

    estado = await mensaje.reply_text(
        "🎙️ Audio recibido.\n"
        "⏳ Estoy transcribiendo tu mensaje..."
    )

    try:
        archivo = await audio.get_file()

        with tempfile.TemporaryDirectory() as carpeta:
            extension = (
                Path(getattr(audio, "file_name", "") or "").suffix
                or (".ogg" if mensaje.voice else ".mp3")
            )

            # Evitar extensiones inesperadas
            if extension.lower() not in {
                ".ogg", ".oga", ".mp3",
                ".m4a", ".wav", ".mp4"
            }:
                extension = ".audio"

            ruta = os.path.join(
                carpeta,
                "mensaje" + extension
            )

            await archivo.download_to_drive(
                custom_path=ruta
            )

            texto = await asyncio.to_thread(
                transcribir_audio,
                ruta
            )

        if not texto:
            await estado.edit_text(
                "No pude identificar palabras en el audio. "
                "Intenta grabarlo nuevamente."
            )
            return

        await estado.edit_text(
            "✅ Audio transcrito correctamente.\n"
            "🧠 Analizando su contenido..."
        )

        resultado = await asyncio.to_thread(
            analizar_texto,
            texto
        )

        emocion, toxicidad, ghosting, riesgo, intencion, confianza = resultado

        respuesta = (
            "🎙️ ANÁLISIS DE AUDIO\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            f"📝 Transcripción:\n{texto}\n\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            f"😊 Emoción: {emocion.capitalize()}\n"
            f"🚩 Toxicidad: {'Alta' if toxicidad == 'si' else 'Baja'}\n"
            f"🧠 Intención: {intencion.capitalize()}\n"
            f"💔 Ghosting estimado: {ghosting}%\n"
            f"🔥 Riesgo estimado: {riesgo}\n"
            f"🎯 Confianza emocional: {confianza}%\n\n"
            "🤖 Análisis orientativo generado con IA."
        )

        # Telegram limita el tamaño de cada mensaje.
        if len(respuesta) > 4000:
            await mensaje.reply_text(
                "📝 Transcripción:\n" + texto[:3500]
            )
            respuesta = (
                "🧠 ANÁLISIS EMOCIONAL\n\n"
                f"Emoción: {emocion.capitalize()}\n"
                f"Toxicidad: {toxicidad}\n"
                f"Intención: {intencion.capitalize()}\n"
                f"Ghosting estimado: {ghosting}%\n"
                f"Riesgo estimado: {riesgo}\n"
                f"Confianza emocional: {confianza}%"
            )

        await mensaje.reply_text(respuesta)

        await estado.delete()

    except Exception as error:
        print(f"Error procesando audio: {error}")

        await estado.edit_text(
            "⚠️ No pude procesar el audio.\n"
            "Revisa la terminal para conocer el error."
        )
