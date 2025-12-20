import os
import asyncio
import aiohttp
from typing import Optional

def load_system_prompt() -> str:
    base_dir = os.path.dirname(__file__)
    prompt_path = os.path.join(base_dir, "prompt.json")
    try:
        with open(prompt_path, "r", encoding="utf-8") as f:
            return f.read().strip()
    except FileNotFoundError:
        return "You are a helpful assistant."

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
        # Keep last 15 messages
        if len(chat_history) > 15:
            self.user_chats[self._get_key(user_id, chat_id)] = chat_history[-15:]

    def clear_chat(self, user_id: int, chat_id: int) -> None:
        self.user_chats[self._get_key(user_id, chat_id)] = []

    async def ask_question(
        self,
        user_id: int,
        chat_id: int,
        message: str,
        user_name: Optional[str] = None,
        new_chat: bool = False
    ) -> Optional[str]:
        """
        Async method to ask a question to the chatbot.
        """
        if new_chat:
            self.clear_chat(user_id, chat_id)
        
        self.add_message(user_id, chat_id, "user", message)
        chat_history = self.get_chat(user_id, chat_id)
        
        # Format system prompt with user name if provided
        if user_name:
            system_prompt = self.system_prompt.format(user_name=user_name)
        else:
            system_prompt = self.system_prompt
        
        session = await self.get_session()
        
        # Retry logic: 3 attempts
        for attempt in range(3):
            try:
                payload = {
                    "messages": [
                        {"role": "system", "content": system_prompt}
                    ] + chat_history
                }
                
                async with session.post(self.api_url, json=payload, timeout=aiohttp.ClientTimeout(total=30)) as response:
                    if response.status == 200:
                        data = await response.json()
                        reply = data.get("reply", "").strip()
                        
                        if reply:
                            self.add_message(user_id, chat_id, "assistant", reply)
                            return reply
                    else:
                        print(f"API returned status {response.status}")
                        
            except asyncio.TimeoutError:
                print(f"Timeout on attempt {attempt + 1}")
            except aiohttp.ClientError as e:
                print(f"Client error on attempt {attempt + 1}: {e}")
            except Exception as e:
                print(f"Error on attempt {attempt + 1}: {e}")
            
            # Wait before retry
            if attempt < 2:
                await asyncio.sleep(1)
        
        return None

    async def close(self) -> None:
        """Close the aiohttp session."""
        if self.session:
            await self.session.close()

chatbot_api = era()
