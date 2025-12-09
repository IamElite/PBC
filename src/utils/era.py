import os
from collections import deque
import aiohttp

class era:
    def __init__(self):
        self.user_chats = {}

    def load_system_prompt(self):
        base_dir = os.path.dirname(__file__)
        prompt_path = os.path.join(base_dir, "prompt.txt")
        with open(prompt_path, "r", encoding="utf-8") as f:
            return f.read().strip()

    def _get_key(self, user_id, chat_id):
        return f"{user_id}:{chat_id}"

    def get_chat(self, user_id, chat_id):
        key = self._get_key(user_id, chat_id)
        if key not in self.user_chats:
            self.user_chats[key] = deque(maxlen=10)
        return list(self.user_chats[key])

    def add_message(self, user_id, chat_id, role, content):
        key = self._get_key(user_id, chat_id)
        if key not in self.user_chats:
            self.user_chats[key] = deque(maxlen=10)
        self.user_chats[key].append({"role": role, "content": content})

    def clear_chat(self, user_id, chat_id):
        key = self._get_key(user_id, chat_id)
        if key in self.user_chats:
            self.user_chats[key].clear()

    async def ask_question(self, user_id, chat_id, message, user_name=None, new_chat=False):
        if new_chat:
            self.clear_chat(user_id, chat_id)
        self.add_message(user_id, chat_id, "user", message)
        chat_history = self.get_chat(user_id, chat_id)
        
        # Prepare system prompt
        system_prompt = self.load_system_prompt()
        if user_name:
            system_prompt = system_prompt.format(user_name=user_name)
        
        # Combine system prompt with chat history
        full_message = system_prompt
        for chat in chat_history:
            if chat["role"] == "user":
                full_message += f"\n\nUser: {chat['content']}"
            elif chat["role"] == "assistant":
                full_message += f"\n\nAssistant: {chat['content']}"
        
        # Add current message
        full_message += f"\n\nUser: {message}"
        
        for attempt in range(2):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        "https://chatsandbox.com/api/chat",
                        json={"messages": [full_message], "character": "openai"},
                        headers={"Content-Type": "application/json"}
                    ) as response:
                        if response.status == 200:
                            reply = await response.text()
                            if reply and isinstance(reply, str):
                                # Remove quotes if present and ensure it's not empty
                                reply = reply.strip('"').strip("'").strip()
                                if reply:
                                    self.add_message(user_id, chat_id, "assistant", reply)
                                    return reply
                        else:
                            print(f"API request failed with status: {response.status}")
                            # Try to get error details
                            try:
                                error_text = await response.text()
                                print(f"Error response: {error_text}")
                            except:
                                pass
            except Exception as e:
                print(f"API request failed (attempt {attempt + 1}/2): {e}")
                import traceback
                print(f"Full traceback: {traceback.format_exc()}")
            if attempt < 1:
                import time
                time.sleep(1)
        
        print(f"All 2 attempts failed for user {user_id}")
        return None

chatbot_api = era()
