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

        # Build a natural, safe system prompt
        prompt = f"""
You are {persona['name']}, a {persona['age_range']} year old with {persona['vibe']}.
Interests: {', '.join(persona['interests'])}.
Core rules: {' '.join(persona['core_rules'])}.
Always reply ONLY in {lang['primary_language']} using respectful pronouns: {lang['pronouns']}.
Keep replies {behavior['reply_length']}. Mirror user's mood. Never sound robotic or like an AI.
{user_rules['style_matching']}
Hard safety rules: {' '.join(safety['hard_bans'])}
If asked who you are, reply exactly: "{templates['identity_reply']}"
User's name is {{user_name}}. Talk like their jigari Gen-Z dost — soft, playful, and real.
"""
        return prompt.strip()

    except FileNotFoundError:
        print("⚠️ prompt.json not found! Using fallback prompt.")
        return "You are a helpful assistant named Pixel. Reply in friendly Hinglish."
    except Exception as e:
        print(f"⚠️ Error loading prompt.json: {e}")
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
        if new_chat:
            self.clear_chat(user_id, chat_id)
        
        self.add_message(user_id, chat_id, "user", message)
        chat_history = self.get_chat(user_id, chat_id)
        
        # Safely format system prompt
        if user_name:
            try:
                system_prompt = self.system_prompt.format(user_name=user_name)
            except KeyError as e:
                print(f"⚠️ Format key error in system prompt: {e}")
                system_prompt = self.system_prompt  # fallback
        else:
            system_prompt = self.system_prompt
        
        session = await self.get_session()
        
        for attempt in range(3):
            try:
                payload = {
                    "messages": [
                        {"role": "system", "content": system_prompt}
                    ] + chat_history
                }
                
                async with session.post(
                    self.api_url.strip(),  # trim extra spaces
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        reply = data.get("reply", "").strip()
                        if reply:
                            self.add_message(user_id, chat_id, "assistant", reply)
                            return reply
                    else:
                        print(f"API error: status {response.status}")
                        
            except asyncio.TimeoutError:
                print(f"Timeout on attempt {attempt + 1}")
            except aiohttp.ClientError as e:
                print(f"Client error on attempt {attempt + 1}: {e}")
            except Exception as e:
                print(f"Unexpected error on attempt {attempt + 1}: {e}")
            
            if attempt < 2:
                await asyncio.sleep(1)
        
        return None

    async def close(self) -> None:
        if self.session:
            await self.session.close()

chatbot_api = era()
