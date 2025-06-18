import os
import logging
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, MessageHandler, filters, CallbackContext, CommandHandler, CallbackQueryHandler

import subprocess
import uuid

# Enable logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# BOT TOKEN
BOT_TOKEN = "7660494660:AAGXM6PjRSc1XTZwHDnWKH4OSgp8WhFy_4E"

# Compression Presets
PRESETS = {
    "Ultra Fast": "-preset ultrafast -crf 32",
    "Fast": "-preset veryfast -crf 28",
    "Balanced": "-preset medium -crf 26",
    "High Quality": "-preset slow -crf 23",
    "Ultra Quality": "-preset slower -crf 20"
}

# Start command
async def start(update: Update, context: CallbackContext):
    await update.message.reply_text(
        "👋 Welcome to *VidShrinkBot*!\n\nSend me a video file, and I'll compress it for you with buttery smooth Apple-like quality. 🍏",
        parse_mode="Markdown"
    )

# Handle uploaded video
async def handle_video(update: Update, context: CallbackContext):
    file = update.message.video or update.message.document
    if not file:
        await update.message.reply_text("❌ Please send a video or file.")
        return

    context.user_data['file_id'] = file.file_id
    await update.message.reply_text(
        "✅ Video received! Choose a compression level:",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton(k, callback_data=k)] for k in PRESETS.keys()
        ])
    )

# Handle button press
async def compress_button(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()

    choice = query.data
    file_id = context.user_data.get('file_id')

    if not file_id:
        await query.edit_message_text("❌ Something went wrong. Try uploading the video again.")
        return

    await query.edit_message_text("📥 Downloading video...")

    file = await context.bot.get_file(file_id)
    input_path = f"{uuid.uuid4()}.mp4"
    output_path = f"compressed_{input_path}"

    await file.download_to_drive(input_path)

    await query.edit_message_text("🎬 Compressing video...")

    ffmpeg_cmd = f'ffmpeg -i "{input_path}" {PRESETS[choice]} -c:a copy "{output_path}" -y'
    process = await asyncio.create_subprocess_shell(ffmpeg_cmd)
    await process.communicate()

    if os.path.exists(output_path):
        await context.bot.send_chat_action(chat_id=query.message.chat_id, action="upload_video")
        await context.bot.send_video(
            chat_id=query.message.chat_id,
            video=open(output_path, 'rb'),
            caption=f"🎉 Here's your compressed video using *{choice}* mode!\n\nGlad to help!\nYours, @VidShrinkBot ❤️",
            parse_mode='Markdown'
        )
    else:
        await context.bot.send_message(query.message.chat_id, "❌ Compression failed.")

    # Clean up
    for path in [input_path, output_path]:
        if os.path.exists(path):
            os.remove(path)

# Main
if __name__ == '__main__':
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.VIDEO | filters.Document.VIDEO, handle_video))

    app.add_handler(CallbackQueryHandler(compress_button))

    print("🚀 Bot is running...")
    app.run_polling()
