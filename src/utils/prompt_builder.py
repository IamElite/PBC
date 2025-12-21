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
        
        short_uninterested = ['nhi', 'no', 'nahi', 'k', 'ok', 'thik']
        if any(word in message_lower for word in short_uninterested) and len(message.split()) <= 2:
            return 'short_uninterested'
        
        short_confusion = ['q', 'kyun', 'what', 'why', 'kya', 'kya re']
        if any(word in message_lower for word in short_confusion) and len(message.split()) <= 2:
            return 'short_confusion'
        
        short_annoyance = ['kya re', 'what', 'kyun', 'matlab kya', 'explain']
        if any(word in message_lower for word in short_annoyance) and len(message.split()) <= 3:
            return 'short_annoyance'
        
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
        
        boredom_indicators = ['nhi', 'no', 'nahi', 'boring', 'chup', 'kuch nhi']
        if any(word in message_lower for word in boredom_indicators) and len(message.split()) <= 3:
            return 'short_low_energy'
        
        confusion_indicators = ['q', 'kyun', 'what', 'why', 'matlab kya', 'samajh nhi aaya']
        if any(word in message_lower for word in confusion_indicators) and len(message.split()) <= 3:
            return 'short_confusion'
        
        irritation_indicators = ['kya re', 'annoying', 'irritating', 'gussa', 'mad']
        if any(word in message_lower for word in irritation_indicators) and len(message.split()) <= 3:
            return 'short_irritation'
        
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
        
        intent_guidance = self.get_response_intent(msg_type, mood, message, recent_history)
        
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
- NO QUESTIONS unless user explicitly asks something
- NO repetitive suggestions (khana, movie, song) spam
- NO interrogation patterns like 'wbu?', 'kya kar rahe ho?', 'tell me more'
- If user seems disengaged (short replies like 'nhi', 'q', 'kya re'): respond calmly without forcing conversation
- Show natural understanding of user's emotional intent behind short messages
- BEHAVIOR: Calm, understanding, slightly casual - never teacher/therapist tone"""
        
        system_prompt += f"""

INTENT UNDERSTANDING FOR SHORT MESSAGES:
- "nhi", "no", "nahi" = User uninterested/low energy → Respond calmly, don't push
- "q", "what", "kyun" = User confused/irritated → Gentle clarification, no pressure
- "kya re", "what", "why" = User annoyed → Acknowledge and deescalate naturally
- "hmm", "ok", "thik" = User neutral/acknowledging → Calm response, no forced follow-up

Current mood matching: {mood_matching['response_matching'][f'user_{mood}']['energy_level'] if f'user_{mood}' in mood_matching['response_matching'] else 'neutral'}.

RESPOND as {identity['name']} would naturally. Never break character. Keep it brief and natural."""
        
        system_prompt += """

MEMORY & CONTEXT FIRST:
- Always check user's confirmed name before responding
- Review conversation flow from recent messages
- Understand emotional context and user's mood
- Use this context to generate appropriate response

RESPONSE INTENT GUIDELINES:
- Uninterested user ("nhi", "no"): Calm acknowledgment, supportive presence, no pressure
- Confused user ("q", "what"): Gentle clarification, helpful but not pushy
- Annoyed user ("kya re"): Acknowledge, deescalate, stay calm
- Neutral user ("hmm", "ok"): Calm response, no forced engagement
- Name acknowledgment: Validate and remember, show familiarity
- Rude behavior: Respond with calm confidence, redirect respectfully

TONE GUIDANCE: {intent_guidance.get('tone', 'natural and calm')}
APPROACH: {intent_guidance.get('approach', 'respond naturally')}

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
    
    def get_response_intent(self, msg_type: str, mood: str = None, user_message: str = None, recent_history: List = None) -> Dict[str, str]:
        intent_guidance = {
            'msg_type': msg_type,
            'mood': mood,
            'user_input': user_message or '',
            'thinking_process': 'analyze_context_and_generate_original_response'
        }
        
        user_lower = (user_message or '').lower()
        
        if msg_type == 'short_uninterested':
            intent_guidance['intent'] = 'acknowledge_and_present_supportive_presence'
            intent_guidance['approach'] = 'user seems uninterested, respond with calm acknowledgment and be present without forcing conversation'
            intent_guidance['tone'] = 'calm, understanding, slightly low energy'
        elif msg_type == 'short_confusion':
            intent_guidance['intent'] = 'provide_clarification_naturally'
            intent_guidance['approach'] = 'user seems confused, provide gentle clarification without being pushy'
            intent_guidance['tone'] = 'helpful, slightly concerned'
        elif msg_type == 'short_annoyance':
            intent_guidance['intent'] = 'acknowledge_and_deescalate'
            intent_guidance['approach'] = 'user seems annoyed, acknowledge and deescalate naturally'
            intent_guidance['tone'] = 'calm, understanding'
        elif msg_type == 'dry_reply':
            if any(word in user_lower for word in ['yes', 'haan', 'han', 'hn']):
                intent_guidance['intent'] = 'acknowledge_with_gentle_curiosity'
                intent_guidance['approach'] = 'acknowledge agreement with gentle interest, ask soft follow-up only if context allows'
                intent_guidance['tone'] = 'warm, slightly curious'
            elif any(word in user_lower for word in ['no', 'nahi', 'nhi']):
                intent_guidance['intent'] = 'acknowledge_without_pressure'
                intent_guidance['approach'] = 'acknowledge disagreement calmly, do not push for explanations'
                intent_guidance['tone'] = 'understanding, calm'
            elif any(word in user_lower for word in ['hmm', 'ok', 'thik', 'acha']):
                intent_guidance['intent'] = 'acknowledge_neutrally'
                intent_guidance['approach'] = 'neutral acknowledgment, do not force follow-up questions'
                intent_guidance['tone'] = 'calm, neutral'
            else:
                intent_guidance['intent'] = 'maintain_gentle_presence'
                intent_guidance['approach'] = 'maintain conversation with gentle presence, no forced engagement'
                intent_guidance['tone'] = 'calm, supportive'
        elif mood == 'negative':
            intent_guidance['intent'] = 'show_concern_and_support'
            intent_guidance['approach'] = 'respond with natural concern and offer listening ear'
            intent_guidance['tone'] = 'concerned, supportive'
        elif mood == 'excited':
            intent_guidance['intent'] = 'match_energy_enthusiastically'
            intent_guidance['approach'] = 'respond with matching enthusiasm and curiosity'
            intent_guidance['tone'] = 'enthusiastic, curious'
        else:
            intent_guidance['intent'] = 'engage_naturally'
            intent_guidance['approach'] = 'respond based on actual message content with natural interest'
            intent_guidance['tone'] = 'natural, interested'
        
        return intent_guidance
    
    def detect_disengagement(self, recent_history: List = None) -> bool:
        if not recent_history or len(recent_history) < 4:
            return False
        
        recent_messages = recent_history[-4:]
        disengagement_count = 0
        
        for msg in recent_messages:
            if isinstance(msg, dict) and msg.get('message'):
                message = msg['message'].lower()
                if any(word in message for word in ['nhi', 'no', 'nahi', 'k', 'ok', 'hmm']) and len(message.split()) <= 2:
                    disengagement_count += 1
        
        return disengagement_count >= 2
    
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
