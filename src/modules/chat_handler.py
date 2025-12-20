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
    """Main chat handler - only for private chats or bot mentions in groups"""
    
    try:
        # Add user to database if not exists
        if message.from_user:
            await add_user(message.from_user.id, message.from_user.username or None)
        
        # Get message text
        user_message = message.text or message.caption or ""
        
        # Check if this is a group chat
        is_group = message.chat.type in [ChatType.GROUP, ChatType.SUPERGROUP]
        
        # In group chats, only respond if bot is mentioned
        if is_group:
            bot_username = f"@{client.me.username}" if client.me else None
            if not (bot_username and bot_username in user_message):
                return  # Don't respond in groups without mention
        
        # Check if message contains other bot commands (ignore them)
        other_bot_commands = [
            '/play', '/pause', '/skip', '/volume', '/queue', '/stop', '/resume',  # Music bots
            '/start', '/help', '/stats', '/ban', '/mute', '/kick', '/warn',  # Admin bots
            '/weather', '/time', '/joke', '/quote', '/translate', '/convert',  # Utility bots
            '/anime', '/manga', '/character', '/search', '/download',  # Media bots
            '/crypto', '/price', '/chart', '/balance', '/transfer',  # Finance bots
            '/news', '/article', '/blog', '/post', '/tweet'  # Social bots
        ]
        
        # Check if it's a command for another bot
        message_lower = user_message.lower()
        is_other_bot_command = False
        
        for command in other_bot_commands:
            if command in message_lower:
                # Check if it's specifically for another bot (contains @username but not our bot)
                if '@' in user_message:
                    bot_username = f"@{client.me.username}" if client.me else None
                    if bot_username and bot_username not in user_message:
                        is_other_bot_command = True
                        break
                # If no @username, still treat as potential other bot command if it starts with /
                elif message_lower.strip().startswith(command):
                    is_other_bot_command = True
                    break
        
        if is_other_bot_command:
            return  # Ignore commands for other bots
        
        # Get AI response using our dynamic system
        user_name = message.from_user.first_name if message.from_user else None
        
        # Call AI API for messages that should be handled
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
                ai_response = "Nahi pata... par main try karti hoon! 😊"
        
        # Send the response
        if ai_response and ai_response.strip():
            await message.reply_text(
                ai_response,
                reply_to_message_id=message.id if not is_group else None
            )
        
    except Exception as e:
        print(f"Error in chat handler: {e}")
        # Fallback response for any errors
        fallback_response = "sorry... technical issue! bas ek minute 😊"
        await message.reply_text(fallback_response)

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
