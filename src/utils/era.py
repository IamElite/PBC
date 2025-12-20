import os
import asyncio
import aiohttp
import json
from typing import Optional
from .prompt_builder import prompt_builder

def load_system_prompt() -> str:
    """Fallback system prompt if dynamic fails"""
    return "You are Pixel. Reply in 15-word max Hinglish using 'aap'."

class era:
    def __init__(self):
        self.user_chats = {}
        self.api_url = "https://aivya.maybechiku.workers.dev/chat"
        self.system_prompt = load_system_prompt()
        self.session: Optional[aiohttp.ClientSession] = None

    async def get_session(self) -> aiohttp.ClientSession:
        if self.session is None:
            self.session = aiohttp.ClientSession()
        return self.session

    def _get_key(self, user_id: int, chat_id: int) -> str:
        return f"{user_id}:{chat_id}"

    def get_chat(self, user_id: int, chat_id: int) -> list:
        key = self._get_key(user_id, chat_id)
        if key not in self.user_chats:
            self.user_chats[key] = []
        return self.user_chats[key]

    def add_message(self, user_id: int, chat_id: int, role: str, content: str) -> None:
        chat_history = self.get_chat(user_id, chat_id)
        chat_history.append({"role": role, "content": content})
        if len(chat_history) > 10:
            self.user_chats[self._get_key(user_id, chat_id)] = chat_history[-10:]

    def clear_chat(self, user_id: int, chat_id: int) -> None:
        self.user_chats[self._get_key(user_id, chat_id)] = []

    async def ask_question(
        self,
        user_id: int,
        chat_id: int,
        message: str,
        user_name: Optional[str] = None,
        is_group: bool = False,
        new_chat: bool = False
    ) -> Optional[str]:
        if new_chat:
            self.clear_chat(user_id, chat_id)
        
        self.add_message(user_id, chat_id, "user", message)
        chat_history = self.get_chat(user_id, chat_id)
        
        # 🔥 DYNAMIC PROMPT BUILDING - Using new modular system!
        try:
            system_prompt = prompt_builder.build_system_prompt(
                message=message,
                is_group=is_group,
                user_context={
                    "user_id": user_id,
                    "chat_id": chat_id,
                    "user_name": user_name,
                    "is_mentioned": True  # Assume mentioned since API is called
                }
            )
        except Exception as e:
            print(f"⚠️ Dynamic prompt failed: {e}")
            system_prompt = self.system_prompt  # Fallback to static
        
        session = await self.get_session()
        
        for attempt in range(3):
            try:
                payload = {
                    "messages": [
                        {"role": "system", "content": system_prompt}
                    ] + chat_history
                }
                
                async with session.post(
                    self.api_url.strip(),
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=20)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        reply = data.get("reply", "").strip()
                        if reply:
                            # 🔥 SMART WORD LIMIT WITH VALIDATION
                            msg_type = prompt_builder.detect_message_type(message, is_group)
                            validated_reply = prompt_builder.validate_response(reply, msg_type)
                            self.add_message(user_id, chat_id, "assistant", validated_reply)
                            return validated_reply
                    else:
                        print(f"API error {response.status}")
            except Exception as e:
                print(f"Attempt {attempt+1} failed: {str(e)[:50]}")
            if attempt < 2:
                await asyncio.sleep(0.5)
        
        return "Nahi pata... baad mein puchna 😊"

    async def close(self) -> None:
        if self.session:
            await self.session.close()

chatbot_api = era()
