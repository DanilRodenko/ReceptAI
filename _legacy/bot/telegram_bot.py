import os
import tempfile
from telegram import Update
from telegram.ext import ContextTypes, ApplicationBuilder, MessageHandler, filters


from app.pipeline import run_pipeline

from dotenv import load_dotenv
load_dotenv()


async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    voice_file = await update.message.voice.get_file()

    if "history" not in context.user_data:
        context.user_data["history"] = []

    with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as tmp_in:
        input_path = tmp_in.name

    await voice_file.download_to_drive(input_path)

    try:
        bot_audio_path, new_history = run_pipeline(input_path, context.user_data["history"])
        context.user_data["history"] = new_history

        if bot_audio_path and os.path.exists(bot_audio_path):
            with open(bot_audio_path, 'rb') as audio:
                await update.message.reply_voice(voice=audio)
            os.remove(bot_audio_path)

    finally:
        if os.path.exists(input_path):
            os.remove(input_path)


if __name__ == '__main__':
    TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    application.add_handler(MessageHandler(filters.VOICE, handle_voice))

    application.run_polling()

