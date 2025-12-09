from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, ChatMemberUpdated
from pyrogram.enums import ChatType, ParseMode
from src import app
from src.database import add_user, add_chat, remove_chat

@app.on_message(filters.command("start") & ~filters.bot)
async def start(client: Client, m: Message):
    bot_name = app.name

    if m.chat.type == ChatType.PRIVATE:
        await add_user(m.from_user.id, m.from_user.username or None)

        await m.reply_text(
            f"""
Welcome {m.from_user.mention} ✨  
I’m <b>{bot_name}</b>, a calm and wise friend here to listen and walk with you 🌿

Whenever you feel like talking, just say <b>{bot_name}</b> or reply here 🌸
""",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Add me to your group", url=f"https://t.me/{client.me.username}?startgroup=true")]
            ]),
            parse_mode=ParseMode.HTML,
            reply_to_message_id=m.id
        )

    elif m.chat.type in {ChatType.GROUP, ChatType.SUPERGROUP}:
        await add_chat(m.chat.id, m.chat.title)

        await m.reply_text(
            f"Hey {m.from_user.mention}, I'm here to assist your group!",
            parse_mode=ParseMode.HTML,
            reply_to_message_id=m.id
        )

@app.on_chat_member_updated()
async def chat_updates(client: Client, m: ChatMemberUpdated):
    bot_id = (await client.get_me()).id

    if m.new_chat_member and m.new_chat_member.user.id == bot_id:
        await add_chat(m.chat.id, m.chat.title)

    elif m.old_chat_member and m.old_chat_member.user.id == bot_id and not m.new_chat_member:
        await remove_chat(m.chat.id)