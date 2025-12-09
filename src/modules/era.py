import time
from asyncio import to_thread
from pyrogram import filters
from pyrogram.types import Message
from pyrogram.enums import ChatAction
from src import app
from src.utils import chatbot_api

user_message_tracker = {}
triggered_words = ["era", "baby"]

def chatbot_filter_func(_, __, m: Message):
    if not m.text or not m.from_user or m.from_user.is_bot:
        return False

    text = m.text.lower()
    user_id = m.from_user.id
    current_time = time.time()

    if not any(word in text for word in triggered_words) and not m.mentioned:
        return False

    if text.startswith(("!", "/")) or m.via_bot or m.sticker:
        return False

    history = user_message_tracker.get(user_id, [])
    history = [t for t in history if current_time - t < 1]
    if len(history) >= 2:
        return False

    history.append(current_time)
    user_message_tracker[user_id] = history

    return True


chatbot_filter = filters.create(chatbot_filter_func)

@app.on_message(filters.text & filters.group & chatbot_filter)
async def mention_chatbot(_, message: Message):
    await app.send_chat_action(message.chat.id, ChatAction.TYPING)
    user_id = message.from_user.id
    chat_id = message.chat.id
    question = message.text.lower()
    user_name = " ".join(
        part for part in [message.from_user.first_name, message.from_user.last_name] if part
    )

    if any(word in question for word in triggered_words):
        reply = await to_thread(chatbot_api.ask_question, user_id, chat_id, question, user_name, True)
    else:
        reply = await to_thread(chatbot_api.ask_question, user_id, chat_id, question, user_name, False)

    if not reply or not isinstance(reply, str) or not reply.strip():
        await message.reply_text(f"⚠️ {app.name} is currently unavailable. Please try again later.")
    else:
        # Clean the reply to ensure it's valid for Telegram
        clean_reply = reply.strip()
        if clean_reply:
            await message.reply_text(clean_reply)
        else:
            await message.reply_text(f"⚠️ {app.name} is currently unavailable. Please try again later.")
