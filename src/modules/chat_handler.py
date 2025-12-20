import asyncio
import random
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.enums import ChatType
from src import app
from src.utils.prompt_builder import prompt_builder
from src.database import add_user
from src.utils.era import chatbot_api

@app.on_message(filters.text & ~filters.bot & ~filters.command(["start", "ping", "broadcast"]))
async def handle_chat(client: Client, message: Message):
    """Main chat handler using AI API with dynamic prompt system"""
    
    try:
        # Add user to database if not exists
        if message.from_user:
            await add_user(message.from_user.id, message.from_user.username or None)
        
        # Get message text
        user_message = message.text or message.caption or ""
        
        # Check if message mentions the bot
        bot_username = f"@{client.me.username}" if client.me else None
        is_mentioned = bot_username and bot_username in user_message
        
        # Check if this is a group chat
        is_group = message.chat.type in [ChatType.GROUP, ChatType.SUPERGROUP]
        
        # In groups, only respond if mentioned or with some probability
        if is_group and not is_mentioned:
            # Small chance to respond naturally in groups (5%)
            if random.random() > 0.05:
                return
        
        # 🤖 CALL AI API WITH DYNAMIC PROMPT!
        user_name = message.from_user.first_name if message.from_user else None
        
        # Get AI response using our new dynamic system
        ai_response = await chatbot_api.ask_question(
            user_id=message.from_user.id if message.from_user else 0,
            chat_id=message.chat.id,
            message=user_message,
            user_name=user_name,
            is_group=is_group
        )
        
        # Handle special cases if AI fails or needs override
        if not ai_response:
            if "who are you" in user_message.lower() or "tum kaun ho" in user_message.lower():
                ai_response = prompt_builder.prompts['persona']['identity']['introduction']
            elif any(correction in user_message.lower() for correction in ["bhai nhi", "yaar nhi", "be nhi"]):
                apology_responses = ["maaf kijiye! aap kaise hain? 😊", "sorry! respect karungi 💕", "got it! aapke liye ✨"]
                ai_response = random.choice(apology_responses)
            else:
                ai_response = "tech issue... sorry 😊"
        
        # Send the response
        await message.reply_text(
            ai_response,
            reply_to_message_id=message.id if not is_group else None
        )
        
    except Exception as e:
        print(f"Error in chat handler: {e}")
        # Fallback response
        await message.reply_text("tech issue... sorry 😊")

@app.on_message(filters.photo | filters.video | filters.document)
async def handle_media(client: Client, message: Message):
    """Handle media messages with simple responses"""
    
    try:
        is_group = message.chat.type in [ChatType.GROUP, ChatType.SUPERGROUP]
        
        # Only respond in groups if mentioned or randomly
        if is_group:
            bot_username = f"@{client.me.username}" if client.me else None
            if not (bot_username and bot_username in (message.caption or "")):
                if random.random() > 0.03:  # 3% chance
                    return
        
        # Simple media responses
        media_responses = [
            "nice! interesting media 😊",
            "cool content! share more 💕",
            "accha laga! ✨",
            "creative! I like it 😊",
            "good stuff! 👏"
        ]
        
        response = random.choice(media_responses)
        
        await message.reply_text(
            response,
            reply_to_message_id=message.id if not is_group else None
        )
        
    except Exception as e:
        print(f"Error in media handler: {e}")
        pass  # Silently fail for media messages

@app.on_message(filters.sticker)
async def handle_sticker(client: Client, message: Message):
    """Handle sticker messages"""
    
    try:
        is_group = message.chat.type in [ChatType.GROUP, ChatType.SUPERGROUP]
        
        # Only respond in groups if mentioned or randomly
        if is_group:
            if random.random() > 0.04:  # 4% chance
                return
        
        # Simple sticker responses
        sticker_responses = [
            "haha! cute sticker 😊",
            "nice choice! 💕",
            "relatable sticker! ✨",
            "funny! lol 😊",
            "cool sticker! 👏"
        ]
        
        response = random.choice(sticker_responses)
        
        await message.reply_text(
            response,
            reply_to_message_id=message.id if not is_group else None
        )
        
    except Exception as e:
        print(f"Error in sticker handler: {e}")
        pass
