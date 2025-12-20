import os
import asyncio
import aiohttp
import json
from typing import Optional

def load_system_prompt() -> str:
    base_dir = os.path.dirname(__file__)
    prompt_path = os.path.join(base_dir, "prompt.json")
    try:
        with open(prompt_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        persona = data["persona"]
        lang = data["language_rules"]
        behavior = data["chat_behavior"]
        safety = data["safety_boundaries"]
        user_rules = data["user_specific_rules"]
        templates = data["response_templates"]

        prompt = f"""
You are {persona['name']}, a {persona['age_range']} year old with {persona['vibe']}.
Interests: {', '.join(persona['interests'])}.
Core rules: {' '.join(persona['core_rules'])}.
ALWAYS reply in {lang['primary_language']} using ONLY "{lang['pronouns']}".
REPLY LENGTH: MAX 15 WORDS. 1 LINE ONLY. NO EXCEPTIONS.
MOOD RULES: {' '.join(behavior['mood_matching'])}
NEVER say identity unless user asks "who are you?".
HARD BANS: {' '.join(safety['hard_bans'])}
If user corrects tone (e.g., "bhai nhi"), APOLOGIZE + SWITCH FORMAL.
User's name is {{user_name}}. Talk like their respectful Gen-Z friend.
"""
        return prompt.strip()

    except Exception as e:
        print(f"⚠️ Prompt load error: {e}")
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
        new_chat: bool = False
    ) -> Optional[str]:
        if new_chat:
            self.clear_chat(user_id, chat_id)
        
        self.add_message(user_id, chat_id, "user", message)
        chat_history = self.get_chat(user_id, chat_id)
        
        system_prompt = self.system_prompt
        if user_name:
            try:
                system_prompt = system_prompt.format(user_name=user_name)
            except:
                pass
        
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
                            # 🔥 HARD 15-WORD LIMIT ENFORCEMENT
                            words = reply.split()
                            if len(words) > 15:
                                reply = " ".join(words[:15]) + "... 😊"
                            self.add_message(user_id, chat_id, "assistant", reply)
                            return reply
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
