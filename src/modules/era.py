import time
from pyrogram import filters
from pyrogram.types import Message
from pyrogram.enums import ChatAction
from src import app
from src.utils import chatbot_api

user_message_tracker = {}

def chatbot_filter_func(_, __, m: Message):
    # Ignore if not a real user text message
    if not m.text or not m.from_user or m.from_user.is_bot:
        return False

    # Ignore commands, bots, replies, stickers, forwards, etc.
    if (
        m.text.startswith(("!", "/", "#")) or
        m.via_bot or
        m.sticker or
        m.animation or
        m.photo or
        m.reply_to_message  # <-- IMPORTANT: skip if replying to someone
    ):
        return False

    # Rate limit: max 1 msg per second per user to avoid spam
    user_id = m.from_user.id
    current_time = time.time()
    history = user_message_tracker.get(user_id, [])
    history = [t for t in history if current_time - t < 1]
    if len(history) >= 1:
        return False

    history.append(current_time)
    user_message_tracker[user_id] = history
    return True

chatbot_filter = filters.create(chatbot_filter_func)

@app.on_message(filters.text & filters.group & chatbot_filter)
async def mention_chatbot(_, message: Message):
    # Check if bot is actually mentioned in the message
    bot_username = f"@{app.me.username}" if app.me else None
    is_mentioned = bot_username and bot_username in message.text
    
    # Only respond if bot is actually mentioned
    if not is_mentioned:
        return
    
    await app.send_chat_action(message.chat.id, ChatAction.TYPING)
    
    user_id = message.from_user.id
    chat_id = message.chat.id
    question = message.text
    user_name = " ".join(
        part for part in [message.from_user.first_name, message.from_user.last_name] if part
    )

    # Always use existing chat history (no new_chat = True)
    reply = await chatbot_api.ask_question(user_id, chat_id, question, user_name, is_group=True, new_chat=False)

    if not reply or not isinstance(reply, str) or not reply.strip():
        # Optional: silently fail instead of sending error (better UX)
        return  # <-- ya phir ek soft reply bhej sakte ho

    clean_reply = reply.strip()
    if clean_reply:
        await message.reply_text(clean_reply)
