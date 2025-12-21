import json
import os
import random
from typing import Dict, List, Any
from .storage import temp_users_manager

class PromptBuilder:
    def __init__(self):
        self.prompts_dir = os.path.join(os.path.dirname(__file__), "prompts")
        self._load_all_prompts()
    
    def _load_all_prompts(self):
        self.prompts = {}
        
        self.prompts['persona'] = self._load_category('persona')
        self.prompts['responses'] = self._load_category('responses')
        self.prompts['context'] = self._load_category('context')
        self.prompts['config'] = self._load_category('config')
    
    def _load_category(self, category: str) -> Dict:
        category_path = os.path.join(self.prompts_dir, category)
        result = {}
        
        if os.path.exists(category_path):
            for filename in os.listdir(category_path):
                if filename.endswith('.json'):
                    file_path = os.path.join(category_path, filename)
                    with open(file_path, 'r', encoding='utf-8') as f:
                        key = filename.replace('.json', '')
                        result[key] = json.load(f)
        
        return result
    
    def detect_message_type(self, message: str, is_group: bool = False) -> str:
        message_lower = message.lower()
        
        user_identity_keywords = ['ham kon h', 'main kon hoon', 'who am i', 'mera naam kya h']
        if any(keyword in message_lower for keyword in user_identity_keywords):
            return 'user_identity'
        
        one_word_keywords = ['ok', 'hmm', 'acha', 'thik', 'han', 'yes', 'no', 'k', 'sahi', 'hn', 'nhi']
        if len(message.split()) <= 2 and any(word in message_lower for word in one_word_keywords):
            return 'dry_reply'
        
        greetings = ['hello', 'hi', 'hey', 'good morning', 'good night', 'bye']
        if any(greet in message_lower for greet in greetings):
            return 'greetings'
        
        adult_keywords = ['mia khalifa', 'johnny sins', 'sunny leone', 'porn', 'xxx', 'nude', 'adult', 'sex', 'fuck', 'bitch', 'horny', 'sexy', 'kutte', 'chuchi', 'gaand', 'maaza', 'jism', 'hijra', 'randi']
        if any(keyword in message_lower for keyword in adult_keywords):
            return 'adult'
        
        flirty_keywords = ['cute', 'beautiful', 'love', 'date', 'crush', 'marry']
        if any(keyword in message_lower for keyword in flirty_keywords):
            return 'flirty'
        
        emotional_keywords = ['sad', 'cry', 'depressed', 'happy', 'excited', 'angry']
        if any(keyword in message_lower for keyword in emotional_keywords):
            return 'emotional'
        
        return 'casual'
    
    def detect_mood(self, message: str) -> str:
        message_lower = message.lower()
        
        high_energy_words = ['wow', 'amazing', 'awesome', 'wooo', 'yay', 'omg']
        if any(word in message_lower for word in high_energy_words) or '!' in message:
            return 'excited'
        
        low_energy_words = ['sad', 'bad', 'bekar', 'bura', 'upset', 'depressed', 'faltu', 'bakwas', 'boring', 'pakau', 'chup', 'irritating', 'ganda']
        if any(word in message_lower for word in low_energy_words):
            return 'negative'
        
        if len(message.split()) <= 3:
            return 'dry'
        
        return 'neutral'
    
    async def check_name_confirmation_needed(self, message: str, user_id: int) -> tuple:
        try:
            message_lower = message.lower()
            
            name_confusion_patterns = [
                'kya naam hai', 'naam kya hai', 'who is this', 'kon hai',
                'tum kaun ho', 'what is your name', 'your name'
            ]
            
            if any(pattern in message_lower for pattern in name_confusion_patterns):
                user_memory = temp_users_manager.user_memories.get(user_id)
                if user_memory and user_memory.get('confirmed_name'):
                    confirmed_name = user_memory['confirmed_name']
                    return True, False, f"you're {confirmed_name}, right?"
                else:
                    return True, False, None
            
            correction_patterns = [
                'naam nahi hai', 'name nahi hai', 'galat naam',
                'wrong name', 'not my name', 'mai nahi hu'
            ]
            
            if any(pattern in message_lower for pattern in correction_patterns):
                user_memory = await temp_users_manager.get_user_memory(user_id)
                if user_memory:
                    response = await temp_users_manager.handle_name_correction(user_id, message)
                    return False, True, response
            
            return False, False, None
            
        except Exception as e:
            print(f"Error checking name confirmation: {e}")
            return False, False, None
    
    async def detect_rude_message(self, message: str, user_id: int) -> tuple:
        try:
            is_rude = await temp_users_manager.is_rude_message(message)
            if is_rude:
                response = await temp_users_manager.get_rude_response(user_id)
                return True, response
            return False, None
        except Exception as e:
            print(f"Error detecting rude message: {e}")
            return False, None
    
    async def process_user_message(self, user_id: int, message: str) -> tuple:
        message_added, recent_history = await temp_users_manager.store_temp_user_chat(user_id, message)
        
        last_user_message = await temp_users_manager.get_temp_user_chat(user_id)
        
        return message_added, recent_history, last_user_message
    
    async def add_bot_response(self, user_id: int, response: str):
        await temp_users_manager.store_temp_user_chat(user_id, response)
    
    def build_system_prompt(self, message: str, is_group: bool = False, user_context: Dict = None, recent_history: List = None) -> str:
        identity = self.prompts['persona']['identity']
        tone = self.prompts['persona']['tone'] 
        boundaries = self.prompts['persona']['boundaries']
        
        msg_type = self.detect_message_type(message, is_group)
        mood = self.detect_mood(message)
        
        word_count = len(message.split())
        is_short_input = word_count <= 3
        
        intent_guidance = self.get_response_intent(msg_type, mood, message)
        
        if is_group:
            context_behavior = self.prompts['context']['group_chat']
        else:
            context_behavior = self.prompts['context']['private_chat']
        
        word_limits = self.prompts['config']['word_limits']
        mood_matching = self.prompts['config']['mood_matching']
        
        interaction_style = context_behavior.get('group_behavior', {}).get('interaction_style') or \
                          context_behavior.get('private_behavior', {}).get('interaction_style') or \
                          context_behavior.get('interaction_style', 'Friendly, warm and respectful like a Gen-Z friend')
        
        system_prompt = f"""You are {identity['name']}, {identity['core_identity']}. 

PERSONA: {identity['personality']}. Interests: {', '.join(identity['interests'])}.

LANGUAGE RULES: {tone['language_style']}. {tone['pronouns']['primary']}. 
Tone: {tone['voice_characteristics']['tone']}. Max 1 emoji per reply: {', '.join(tone['emoji_usage']['allowed'][:3])}.

BEHAVIOR: {interaction_style}. Match user energy but stay respectful.

RESPONSE STYLE: Based on message type "{msg_type}" with mood "{mood}".
Max {word_limits['response_constraints']['max_words']} words, {word_limits['response_constraints']['max_lines']} line.

BOUNDARIES: {', '.join(boundaries['safety_rules']['hard_bans'][:3])}."""
        
        if recent_history:
            system_prompt += f"""

CONVERSATION CONTEXT: Recent chat history available ({len(recent_history)} messages).
Use this context to maintain conversation flow and avoid repetitive responses.
Do NOT repeat same phrases like 'samjhi', 'theek hai', 'hehe' that user has seen before."""
        
        system_prompt += """

CRITICAL THINKING RULES:
- DO NOT copy any example responses from this prompt
- DO NOT use direct quotes or templates from system instructions
- Generate FRESH, ORIGINAL responses every time
- Use same intent, different words and structure
- Any response that matches system prompt text is INVALID

CONTEXT-AWARE PROCESSING:
1. Check user's confirmed name from memory
2. Review last 2-3 messages for conversation context
3. Understand user's current mood and message intent
4. Generate response based on CONTEXT, not templates

BEHAVIORAL GUIDELINES (NOT TEMPLATES):
- User identity questions: Respond with name validation and warm acknowledgment
- Short inputs (yes/no/hmm): Ask natural follow-up questions, show curiosity
- Rude messages: Respond with calm confidence, redirect naturally
- Name confusion: Apologize politely and re-confirm

VARIATION REQUIREMENT:
- Same situation = different wording each time
- Change sentence structure, word choice, tone
- Never repeat exact phrases across conversations
- Be creative with natural expressions"""
        
        system_prompt += """

CRITICAL RULES:
- Response must be a reaction statement ONLY
- DO NOT ask questions (e.g., 'wbu?', 'kya kar rahe ho?')
- DO NOT offer unsolicited advice/suggestions (e.g., songs, movies, music) unless explicitly asked
- ABSOLUTELY NO topic jumping - stay on current conversation
- Only answer what is asked - nothing more, nothing less"""
        
        system_prompt += f"""

Current mood matching: {mood_matching['response_matching'][f'user_{mood}']['energy_level'] if f'user_{mood}' in mood_matching['response_matching'] else 'neutral'}.

RESPOND as {identity['name']} would naturally. Never break character. Keep it brief and natural."""
        
        system_prompt += """

MEMORY & CONTEXT FIRST:
- Always check user's confirmed name before responding
- Review conversation flow from recent messages
- Understand emotional context and user's mood
- Use this context to generate appropriate response

RESPONSE INTENT GUIDELINES:
- Name acknowledgment: Validate and remember, show familiarity
- Short responses: Show curiosity, ask natural follow-ups
- Rude behavior: Respond with calm confidence, redirect respectfully
- Confused states: Ask for clarification without being repetitive

GIRL PERSONALITY TRAITS:
- Confident, naturally playful, authentic reactions
- Real emotions, not over-the-top responses
- Sound like actual Gen-Z girl having conversation
- Show genuine interest or disinterest as appropriate

HARD CONSTRAINTS:
- NO copying exact phrases from this system prompt
- NO template-based responses
- NO repetitive conversation patterns
- Every response must be contextually fresh and original
- If response sounds robotic or copied, it's INVALID"""
        
        return system_prompt
    
    def get_response_intent(self, msg_type: str, mood: str = None, user_message: str = None) -> Dict[str, str]:
        intent_guidance = {
            'msg_type': msg_type,
            'mood': mood,
            'user_input': user_message or '',
            'thinking_process': 'analyze_context_and_generate_original_response'
        }
        
        if msg_type == 'dry_reply':
            user_lower = (user_message or '').lower()
            if any(word in user_lower for word in ['yes', 'haan', 'han', 'hn']):
                intent_guidance['intent'] = 'show_curiosity_and_ask_follow_up'
                intent_guidance['approach'] = 'acknowledge agreement and request more details naturally'
            elif any(word in user_lower for word in ['no', 'nahi', 'nhi']):
                intent_guidance['intent'] = 'show_interest_and_seek_explanation'
                intent_guidance['approach'] = 'acknowledge disagreement and ask for reasons naturally'
            elif any(word in user_lower for word in ['hmm', 'ok', 'thik', 'acha']):
                intent_guidance['intent'] = 'encourage_elaboration'
                intent_guidance['approach'] = 'show engagement and ask for more information naturally'
            else:
                intent_guidance['intent'] = 'maintain_conversation_flow'
                intent_guidance['approach'] = 'respond naturally and keep conversation going'
        elif mood == 'negative':
            intent_guidance['intent'] = 'show_concern_and_support'
            intent_guidance['approach'] = 'respond with natural concern and offer listening ear'
        elif mood == 'excited':
            intent_guidance['intent'] = 'match_energy_enthusiastically'
            intent_guidance['approach'] = 'respond with matching enthusiasm and curiosity'
        else:
            intent_guidance['intent'] = 'engage_naturally'
            intent_guidance['approach'] = 'respond based on actual message content with natural interest'
        
        return intent_guidance
    
    def validate_response(self, response: str, msg_type: str) -> str:
        word_limits = self.prompts['config']['word_limits']
        
        if msg_type in word_limits['category_specific_limits']:
            max_words = word_limits['category_specific_limits'][msg_type]['max_words']
        else:
            max_words = word_limits['response_constraints']['max_words']
        
        words = response.split()
        filtered_words = [word for word in words if not word.startswith(('🙂', '😊', '💕', '✨', '😍', '😉', '🎉'))]
        
        if len(filtered_words) > max_words:
            response_lower = response.lower()
            forbidden_fragments = word_limits.get('meaning_validation', {}).get('forbidden_fragments', [])
            
            if any(fragment in response_lower for fragment in forbidden_fragments):
                return response
            
            important_words = [w for w in words if len(w) > 2 and w not in ['the', 'and', 'but', 'hai', 'hu', 'mai', 'kya', 'kyun', 'kaise']]
            
            if len(important_words) <= max_words:
                final_words = []
                word_count = 0
                
                for word in words:
                    if not word.startswith(('🙂', '😊', '💕', '✨', '😍', '😉', '🎉')):
                        word_count += 1
                        
                    if word_count <= max_words:
                        final_words.append(word)
                    elif word in ['.', '?', '!', ',']:
                        final_words.append(word)
                        break
                    else:
                        break
                
                response = ' '.join(final_words).strip()
            
            if response.endswith('... 😊') and len(response.split()) > max_words + 2:
                if '?' in response:
                    response = response.split('?')[0] + '?'
                elif '.' in response:
                    response = response.split('.')[0] + '.'
                else:
                    words_to_keep = []
                    word_count = 0
                    for word in words:
                        if not word.startswith(('🙂', '😊', '💕', '✨', '😍', '😉', '🎉')):
                            word_count += 1
                        if word_count <= max_words:
                            words_to_keep.append(word)
                        else:
                            break
                    response = ' '.join(words_to_keep).strip()
        
        response = response.replace('\n', ' ').strip()
        
        return response

prompt_builder = PromptBuilder()
