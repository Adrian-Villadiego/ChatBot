
import os
import random
import asyncio
import logging

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

from predict import analizar_texto
from audio import recibir_audio
from historial import (crear_base_datos, guardar_analisis, consultar_historial, obtener_estadisticas, eliminar_historial)


# ============================================================
# CONFIGURACIÓN
# ============================================================

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.WARNING,
)

logger = logging.getLogger(__name__)

TOKEN = os.getenv("TELEGRAM_TOKEN")

if not TOKEN:
    raise SystemExit(
        "ERROR: TELEGRAM_TOKEN no está configurado.\n"
        "Configúralo en PowerShell antes de iniciar el bot."
    )


# ============================================================
# INTERPRETACIONES
# ============================================================

INTERPRETACIONES = {
    "reclamo": [
        "La persona podría sentirse ignorada y estar reclamando atención.",
        "El mensaje puede expresar frustración por una respuesta que esperaba.",
        "Parece existir una necesidad de comunicación y atención.",
    ],
    "celos": [
        "El mensaje podría reflejar inseguridad o preocupación.",
        "La persona parece buscar tranquilidad sobre la relación.",
        "Podría existir desconfianza que conviene conversar.",
    ],
    "agresion": [
        "El mensaje contiene expresiones que podrían resultar agresivas.",
        "Existe tensión y conviene evitar respuestas impulsivas.",
        "Es recomendable establecer límites y comunicarse con calma.",
    ],
    "tristeza": [
        "La persona podría estar atravesando un momento difícil.",
        "El mensaje parece expresar tristeza o vulnerabilidad.",
        "Podría necesitar comprensión y apoyo emocional.",
    ],
    "manipulacion": [
        "El mensaje podría contener presión emocional.",
        "Conviene revisar si se están utilizando condiciones o culpa.",
        "Es importante mantener límites y una comunicación respetuosa.",
    ],
    "control": [
        "El mensaje podría reflejar una necesidad de supervisión.",
        "Conviene conversar sobre confianza y límites personales.",
        "Podría existir preocupación por conocer constantemente tus actividades.",
    ],
    "ruptura": [
        "El mensaje podría indicar dudas sobre continuar la relación.",
        "Parece existir una conversación importante pendiente.",
        "Podría expresar agotamiento emocional o necesidad de distancia.",
    ],
    "desinteres": [
        "El mensaje parece breve o poco expresivo.",
        "La persona podría estar ocupada o no querer profundizar ahora.",
        "No es posible determinar el interés de alguien solo por este mensaje.",
    ],
    "inseguridad": [
        "El mensaje podría expresar dudas o necesidad de tranquilidad.",
        "La persona parece buscar seguridad emocional.",
        "Podría ser útil conversar sobre sus preocupaciones.",
    ],
    "afecto": [
        "El mensaje expresa cariño y sentimientos positivos.",
        "Parece existir una intención de acercamiento emocional.",
        "Las palabras transmiten aprecio y conexión.",
    ],
    "curiosidad": [
        "El mensaje parece mostrar interés por conocer algo.",
        "Podría ser una invitación a continuar la conversación.",
        "La persona está realizando preguntas o buscando información.",
    ],
    "normal": [
        "El mensaje parece formar parte de una conversación cotidiana.",
        "No se identifican señales claras de conflicto.",
        "El contenido no permite determinar una intención emocional específica.",
    ],
}


# ============================================================
# SUGERENCIAS DE RESPUESTA
# ============================================================

SUGERENCIAS = {
    "reclamo": [
        "Entiendo que esto te molestó. ¿Podemos hablarlo?",
        "Perdón por la demora. Me gustaría entender cómo te sientes.",
        "Quiero escucharte. Cuéntame qué ocurrió.",
    ],
    "celos": [
        "Entiendo tu preocupación. Podemos hablar con tranquilidad.",
        "Me gustaría que conversemos sobre lo que te preocupa.",
        "Creo que podemos aclararlo mediante una conversación sincera.",
    ],
    "agresion": [
        "Prefiero que conversemos cuando podamos hacerlo con respeto.",
        "Quiero escucharte, pero necesito que hablemos sin insultos.",
        "Podemos retomar esta conversación cuando estemos más tranquilos.",
    ],
    "tristeza": [
        "Estoy aquí para escucharte si quieres hablar.",
        "Lamento que estés pasando por esto. ¿Cómo puedo ayudarte?",
        "Puedes contar conmigo si necesitas conversar.",
    ],
    "manipulacion": [
        "Quiero escucharte, pero prefiero que conversemos sin presiones.",
        "Podemos hablar sobre lo que necesitas con tranquilidad.",
        "Me gustaría encontrar una solución respetando nuestros límites.",
    ],
    "control": [
        "Creo que es importante respetar nuestros espacios personales.",
        "Podemos conversar sobre la confianza y nuestras preocupaciones.",
        "Me gustaría que encontremos una forma saludable de comunicarnos.",
    ],
    "ruptura": [
        "Entiendo que es una conversación importante. ¿Podemos hablar?",
        "Quisiera comprender mejor cómo te sientes.",
        "Respeto tus sentimientos y me gustaría escucharte.",
    ],
    "desinteres": [
        "Está bien, podemos hablar después.",
        "Cuando tengas tiempo, seguimos conversando.",
        "Espero que estés bien. Hablamos luego.",
    ],
    "inseguridad": [
        "Si algo te preocupa, podemos hablarlo.",
        "Quiero que podamos comunicarnos con confianza.",
        "Me importa entender cómo te sientes.",
    ],
    "afecto": [
        "Qué bonito mensaje. Gracias por tus palabras.",
        "Me alegra mucho saber que te sientes así.",
        "Yo también valoro mucho nuestra conexión.",
    ],
    "curiosidad": [
        "Claro, te cuento. ¿Qué te gustaría saber?",
        "Me alegra que preguntes. ¿Y tú cómo estás?",
        "Qué bueno conversar contigo.",
    ],
    "normal": [
        "Todo bien, ¿y tú?",
        "Perfecto, seguimos hablando.",
        "Qué bueno saber de ti.",
    ],
}


# ============================================================
# EMOJIS
# ============================================================

EMOJIS = {
    "reclamo": "📢",
    "celos": "😒",
    "agresion": "⚠️",
    "tristeza": "😢",
    "manipulacion": "🚩",
    "control": "🔒",
    "ruptura": "💔",
    "desinteres": "😶",
    "inseguridad": "😟",
    "afecto": "💕",
    "curiosidad": "🤔",
    "normal": "💬",
}

EMOJIS_EMOCION = {
    "positivo": "😊",
    "tristeza": "😢",
    "enojo": "😠",
    "sorpresa": "😲",
    "disgusto": "😖",
    "miedo": "😨",
    "neutral": "😐",
}


# ============================================================
# FUNCIONES AUXILIARES
# ============================================================

def construir_barra(valor):
    valor = max(0, min(100, int(valor)))
    bloques = valor // 10

    return "█" * bloques + "░" * (10 - bloques)


def obtener_texto(diccionario, clave):
    opciones = diccionario.get(
        clave,
        diccionario["normal"]
    )

    return random.choice(opciones)


def preparar_resultado(resultado):
    emocion, toxicidad, ghosting, riesgo, intencion, confianza = resultado

    return {
        "emoji_principal": EMOJIS.get(intencion, "💬"),
        "emoji_emocion": EMOJIS_EMOCION.get(emocion, "😐"),
        "emocion": emocion.capitalize(),
        "toxicidad": (
            "🔴 Posible contenido ofensivo"
            if toxicidad == "si"
            else "🟢 Sin señales detectadas"
        ),
        "intencion": intencion.capitalize(),
        "ghosting": ghosting,
        "barra": construir_barra(ghosting),
        "riesgo": riesgo,
        "confianza": confianza,
        "interpretacion": obtener_texto(
            INTERPRETACIONES,
            intencion
        ),
        "sugerencia": obtener_texto(
            SUGERENCIAS,
            intencion
        ),
    }


def formatear_respuesta(datos):
    return (
        f"{datos['emoji_principal']} ANÁLISIS EMOCIONAL\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"

        f"{datos['emoji_emocion']} Emoción detectada:\n"
        f"{datos['emocion']}\n\n"

        f"🚩 Toxicidad:\n"
        f"{datos['toxicidad']}\n\n"

        f"🧠 Intención estimada:\n"
        f"{datos['intencion']}\n\n"

        f"💔 Indicador de ghosting:\n"
        f"{datos['barra']} {datos['ghosting']}%\n\n"

        f"🔥 Riesgo estimado:\n"
        f"{datos['riesgo']}\n\n"

        f"🎯 Confianza de emoción:\n"
        f"{datos['confianza']}%\n\n"

        "━━━━━━━━━━━━━━━━━━━━\n"
        "💡 POSIBLE INTERPRETACIÓN\n\n"
        f"{datos['interpretacion']}\n\n"

        "💬 SUGERENCIA DE RESPUESTA\n\n"
        f"«{datos['sugerencia']}»\n\n"

        "━━━━━━━━━━━━━━━━━━━━\n"
        "🤖 ChatMind IA\n"
        "Resultados orientativos, no conclusiones definitivas."
    )


# ============================================================
# MENÚS
# ============================================================

def teclado_principal():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "📝 Analizar texto",
                callback_data="texto"
            ),
            InlineKeyboardButton(
                "🎙️ Analizar audio",
                callback_data="audio"
            ),
        ],
        [
            InlineKeyboardButton(
                "🧠 Cómo funciona",
                callback_data="funcionamiento"
            ),
            InlineKeyboardButton(
                "❓ Ayuda",
                callback_data="ayuda"
            ),
        ],
        [
            InlineKeyboardButton("📚 Mi historial", callback_data="historial"),
            InlineKeyboardButton("📊 Estadísticas", callback_data="estadisticas"),
        ],
        [
            InlineKeyboardButton("🗑️ Borrar historial", callback_data="borrar_historial"),
        ],
        [
            InlineKeyboardButton(
                "🏠 Menú principal",
                callback_data="menu"
            ),
        ],
    ])


def teclado_volver():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "🏠 Volver al menú",
                callback_data="menu"
            )
        ]
    ])


def mensaje_bienvenida(nombre):
    return (
        "✨ BIENVENIDO A CHATMIND IA ✨\n\n"
        f"👋 Hola, {nombre}.\n\n"

        "🧠 Soy tu asistente de análisis emocional.\n\n"

        "Puedo ayudarte a comprender mensajes "
        "mediante inteligencia artificial.\n\n"

        "━━━━━━━━━━━━━━━━━━━━\n\n"

        "🚀 MIS FUNCIONES\n\n"

        "📝 Analizar mensajes escritos\n"
        "🎙️ Interpretar notas de voz\n"
        "🧠 Identificar emociones\n"
        "💬 Sugerir posibles respuestas\n"
        "📊 Consultar historial y estadísticas\n\n"

        "━━━━━━━━━━━━━━━━━━━━\n\n"

        "👇 Selecciona una opción para comenzar."
    )


# ============================================================
# COMANDOS
# ============================================================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    context.user_data["modo"] = None

    nombre = update.effective_user.first_name or "Usuario"

    await update.message.reply_text(
        mensaje_bienvenida(nombre),
        reply_markup=teclado_principal()
    )


async def menu(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    await start(update, context)


async def ayuda(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    await update.message.reply_text(
        "❓ CENTRO DE AYUDA\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"

        "📝 ANÁLISIS DE TEXTO\n"
        "Envía un mensaje escrito para analizarlo.\n\n"

        "🎙️ ANÁLISIS DE AUDIO\n"
        "Envía una nota de voz o archivo de audio.\n\n"

        "🧠 INTELIGENCIA ARTIFICIAL\n"
        "El bot utiliza modelos para identificar "
        "emociones y analizar el contenido.\n\n"

        "🏠 MENÚ PRINCIPAL\n"
        "Escribe /menu para regresar al inicio.\n\n"

        "⚠️ Los resultados son orientativos.",
        reply_markup=teclado_volver()
    )


# ============================================================
# BOTONES INTERACTIVOS
# ============================================================

async def botones(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    query = update.callback_query

    await query.answer()

    opcion = query.data

    if opcion == "menu":
        context.user_data["modo"] = None

        nombre = query.from_user.first_name or "Usuario"

        await query.edit_message_text(
            mensaje_bienvenida(nombre),
            reply_markup=teclado_principal()
        )

    elif opcion == "historial":
        registros = await asyncio.to_thread(consultar_historial, query.from_user.id)
        if not registros:
            contenido = "📚 MI HISTORIAL\n\nTodavía no tienes análisis guardados."
        else:
            lineas = ["📚 MIS ÚLTIMOS 10 ANÁLISIS", "━━━━━━━━━━━━━━━━━━━━"]
            for registro in registros:
                fecha = registro["fecha"][:16].replace("T", " ")
                lineas.append(f"• {fecha} UTC | {registro['tipo_mensaje']} | {registro['emocion'].capitalize()}")
            contenido = "\n".join(lineas)
        await query.edit_message_text(contenido, reply_markup=teclado_volver())

    elif opcion == "estadisticas":
        registros = await asyncio.to_thread(obtener_estadisticas, query.from_user.id)
        total = sum(r["cantidad"] for r in registros)
        if total == 0:
            contenido = "📊 ESTADÍSTICAS (7 DÍAS)\n\nTodavía no hay análisis en este período."
        else:
            lineas = [f"📊 ESTADÍSTICAS (7 DÍAS)\n\nTotal: {total} análisis", "━━━━━━━━━━━━━━━━━━━━"]
            for registro in registros:
                porcentaje = registro["cantidad"] * 100 / total
                lineas.append(f"• {registro['emocion'].capitalize()}: {registro['cantidad']} ({porcentaje:.1f}%)")
            lineas.append(f"\nEmoción más frecuente: {registros[0]['emocion'].capitalize()}")
            contenido = "\n".join(lineas)
        await query.edit_message_text(contenido, reply_markup=teclado_volver())

    elif opcion == "borrar_historial":
        await query.edit_message_text(
            "🗑️ ¿Eliminar todo tu historial emocional?\n\nEsta acción no se puede deshacer.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Sí, eliminar", callback_data="confirmar_borrado")],
                [InlineKeyboardButton("Cancelar", callback_data="menu")],
            ]),
        )

    elif opcion == "confirmar_borrado":
        cantidad = await asyncio.to_thread(eliminar_historial, query.from_user.id)
        await query.edit_message_text(
            f"🗑️ Se eliminaron {cantidad} registros de tu historial.",
            reply_markup=teclado_volver(),
        )

    elif opcion == "texto":
        context.user_data["modo"] = "texto"

        await query.edit_message_text(
            "📝 ANÁLISIS DE TEXTO\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"

            "Envíame el mensaje que deseas analizar.\n\n"

            "🔍 Identificaré:\n\n"
            "😊 Emoción predominante\n"
            "🚩 Posible toxicidad\n"
            "🧠 Intención estimada\n"
            "💔 Indicadores de ghosting\n"
            "💬 Sugerencia de respuesta\n\n"

            "✍️ Escribe tu mensaje ahora.",
            reply_markup=teclado_volver()
        )

    elif opcion == "audio":
        context.user_data["modo"] = "audio"

        await query.edit_message_text(
            "🎙️ ANÁLISIS DE AUDIO\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"

            "🎤 Envíame una nota de voz "
            "o un archivo de audio.\n\n"

            "Mi sistema realizará:\n\n"

            "1️⃣ Transcripción del audio\n"
            "2️⃣ Identificación de emociones\n"
            "3️⃣ Análisis de intención\n"
            "4️⃣ Evaluación del contenido\n"
            "5️⃣ Presentación de resultados\n\n"

            "👇 Graba y envía tu audio.",
            reply_markup=teclado_volver()
        )

    elif opcion == "funcionamiento":
        await query.edit_message_text(
            "🧠 CÓMO FUNCIONA CHATMIND IA\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"

            "ChatMind IA utiliza modelos de "
            "procesamiento del lenguaje natural.\n\n"

            "🔹 Pysentimiento:\n"
            "Analiza emociones y posibles "
            "expresiones de odio.\n\n"

            "🔹 Whisper:\n"
            "Convierte audios en texto.\n\n"

            "🔹 Reglas de análisis:\n"
            "Estiman intenciones y señales "
            "relacionadas con ghosting.\n\n"

            "🔹 Recomendaciones:\n"
            "Genera sugerencias de respuesta "
            "según la categoría detectada.\n\n"

            "⚠️ No determina con certeza "
            "los sentimientos de una persona.",
            reply_markup=teclado_volver()
        )

    elif opcion == "ayuda":
        await query.edit_message_text(
            "❓ AYUDA DE CHATMIND IA\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"

            "📝 Para analizar texto:\n"
            "1. Selecciona Analizar texto.\n"
            "2. Escribe el mensaje.\n"
            "3. Consulta los resultados.\n\n"

            "🎙️ Para analizar audio:\n"
            "1. Selecciona Analizar audio.\n"
            "2. Graba o adjunta un audio.\n"
            "3. Espera la transcripción.\n"
            "4. Consulta el análisis.\n\n"

            "🏠 Regresa al menú cuando quieras.",
            reply_markup=teclado_volver()
        )


# ============================================================
# ANÁLISIS DE TEXTO
# ============================================================

async def responder(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    mensaje = update.message

    if not mensaje or not mensaje.text:
        return

    texto = mensaje.text.strip()

    if not texto:
        await mensaje.reply_text(
            "⚠️ Escribe un mensaje válido."
        )
        return

    estado = await mensaje.reply_text(
        "🔎 Analizando tu mensaje...\n"
        "🧠 Procesando emociones e intención."
    )

    try:
        resultado = await asyncio.to_thread(
            analizar_texto,
            texto
        )

        # Guardar solo la emoción, nunca el contenido del mensaje.
        try:
            await asyncio.to_thread(
                guardar_analisis, update.effective_user.id, "texto", resultado[0]
            )
        except Exception:
            logger.exception("No se pudo guardar el historial del texto")

        datos = preparar_resultado(resultado)

        respuesta = formatear_respuesta(datos)

        await estado.edit_text(
            "✅ Análisis completado."
        )

        await mensaje.reply_text(
            respuesta,
            reply_markup=teclado_principal()
        )

    except Exception:
        logger.exception("Error analizando texto")

        await estado.edit_text(
            "⚠️ Ocurrió un error al analizar "
            "el mensaje. Inténtalo nuevamente."
        )


# ============================================================
# MANEJO DE AUDIOS
# ============================================================

async def procesar_audio(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    await recibir_audio(update, context)


# ============================================================
# MANEJO DE ERRORES
# ============================================================

async def manejar_error(
    update: object,
    context: ContextTypes.DEFAULT_TYPE
):
    logger.error(
        "Error no controlado en el bot",
        exc_info=(
            type(context.error),
            context.error,
            context.error.__traceback__
        ) if context.error else None
    )


# ============================================================
# INICIALIZACIÓN
# ============================================================

def main():
    print("======================================")
    print("       CHATMIND IA - TELEGRAM")
    print("======================================")

    print("Iniciando inteligencia artificial...")
    crear_base_datos()

    app = (
        ApplicationBuilder()
        .token(TOKEN)
        .build()
    )

    # Comandos
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("menu", menu))
    app.add_handler(CommandHandler("ayuda", ayuda))

    # Botones
    app.add_handler(
        CallbackQueryHandler(botones)
    )

    # Audios
    app.add_handler(
        MessageHandler(
            filters.VOICE | filters.AUDIO,
            procesar_audio
        )
    )

    # Mensajes escritos
    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            responder
        )
    )

    # Errores
    app.add_error_handler(manejar_error)

    print("ChatMind IA iniciado correctamente.")
    print("Menú interactivo: ACTIVO")
    print("Análisis de texto: ACTIVO")
    print("Análisis de audio: CONFIGURADO")
    print("Esperando mensajes de Telegram...")

    app.run_polling()


if __name__ == "__main__":
    main()
