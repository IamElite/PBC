import os, time, requests

def load_system_prompt() -> str:
    base_dir = os.path.dirname(__file__)
    prompt_path = os.path.join(base_dir, "prompt.txt")
    with open(prompt_path, "r", encoding="utf-8") as f:
        return f.read().strip()


class era:
    def __init__(self):
        self.user_chats = {}
        self.api_url = "https://aivya.maybechiku.workers.dev/chat"
        self.system_prompt = load_system_prompt()

    def _get_key(self, user_id: int, chat_id: int):
        return f"{user_id}:{chat_id}"

    def get_chat(self, user_id: int, chat_id: int):
        key = self._get_key(user_id, chat_id)
        if key not in self.user_chats:
            self.user_chats[key] = []
        return self.user_chats[key]

    def add_message(self, user_id: int, chat_id: int, role: str, content: str):
        chat_history = self.get_chat(user_id, chat_id)
        chat_history.append({"role": role, "content": content})
        if len(chat_history) > 15:
            self.user_chats[self._get_key(user_id, chat_id)] = chat_history[-15:]

    def clear_chat(self, user_id: int, chat_id: int):
        self.user_chats[self._get_key(user_id, chat_id)] = []

    def ask_question(
        self, user_id: int, chat_id: int, message: str,
        user_name: str = None, new_chat: bool = False
    ) -> str | None:
        if new_chat:
            self.clear_chat(user_id, chat_id)

        self.add_message(user_id, chat_id, "user", message)
        chat_history = self.get_chat(user_id, chat_id)

        if user_name:
            system_prompt = self.system_prompt.format(user_name=user_name)
        else:
            system_prompt = self.system_prompt

        for _ in range(3):
            try:
                payload = {"messages": [{"role": "system", "content": system_prompt}] + chat_history}
                response = requests.post(self.api_url, json=payload)
                if response.status_code == 200:
                    data = response.json()
                    reply = data.get("reply", "").strip()
                    if reply:
                        self.add_message(user_id, chat_id, "assistant", reply)
                        return reply
            except Exception:
                time.sleep(1)
        return None


chatbot_api = era()
