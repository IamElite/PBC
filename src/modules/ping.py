from pyrogram import filters
from src import app
from datetime import datetime

@app.on_message(filters.command("ping"))
async def ping_pong(client, message):
    start = datetime.now()
    msg = await message.reply_text("🏓 Pong...")
    end = datetime.now()
    ping_time = (end - start).total_seconds() * 1000
    await msg.edit_text(f"<b>🏓 Pong!</b> {int(ping_time)} ms")