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
        """Load all JSON files from prompts directory"""
        self.prompts = {}
        
        # Load persona files
        self.prompts['persona'] = self._load_category('persona')
        # Load response files  
        self.prompts['responses'] = self._load_category('responses')
        # Load context files
        self.prompts['context'] = self._load_category('context')
        # Load config files
        self.prompts['config'] = self._load_category('config')
    
    def _load_category(self, category: str) -> Dict:
        """Load all JSON files from a category folder"""
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
        """Detect the type of message based on content"""
        message_lower = message.lower()
        
        # User Identity detection
        user_identity_keywords = ['ham kon h', 'main kon hoon', 'who am i', 'mera naam kya h']
        if any(keyword in message_lower for keyword in user_identity_keywords):
            return 'user_identity'
        
        # Dry Reply detection (enhanced with 'sahi')
        dry_keywords = ['ok', 'hmm', 'acha', 'thik', 'han', 'yes', 'no', 'k', 'sahi']
        if len(message.split()) < 3 and any(word in message_lower for word in dry_keywords):
            return 'dry_reply'
        
        # Greeting detection
        greetings = ['hello', 'hi', 'hey', 'good morning', 'good night', 'bye']
        if any(greet in message_lower for greet in greetings):
            return 'greetings'
        
        # Adult/inappropriate content detection (expanded)
        adult_keywords = ['mia khalifa', 'johnny sins', 'sunny leone', 'porn', 'xxx', 'nude', 'adult', 'sex', 'fuck', 'bitch', 'horny', 'sexy', 'kutte', 'chuchi', 'gaand', 'maaza', 'jism', 'hijra', 'randi']
        if any(keyword in message_lower for keyword in adult_keywords):
            return 'adult'
        
        # Flirting detection
        flirty_keywords = ['cute', 'beautiful', 'love', 'date', 'crush', 'marry']
        if any(keyword in message_lower for keyword in flirty_keywords):
            return 'flirty'
        
        # Emotional content detection
        emotional_keywords = ['sad', 'cry', 'depressed', 'happy', 'excited', 'angry']
        if any(keyword in message_lower for keyword in emotional_keywords):
            return 'emotional'
        
        # Default to casual
        return 'casual'
    
    def detect_mood(self, message: str) -> str:
        """Detect user's mood from message"""
        message_lower = message.lower()
        
        # High energy detection
        high_energy_words = ['wow', 'amazing', 'awesome', 'wooo', 'yay', 'omg']
        if any(word in message_lower for word in high_energy_words) or '!' in message:
            return 'excited'
        
        # Low energy detection (expanded with dismissive/insult words)
        low_energy_words = ['sad', 'bad', 'bekar', 'bura', 'upset', 'depressed', 'faltu', 'bakwas', 'boring', 'pakau', 'chup', 'irritating', 'ganda']
        if any(word in message_lower for word in low_energy_words):
            return 'negative'
        
        # Short/dry response
        if len(message.split()) <= 3:
            return 'dry'
        
        return 'neutral'
    
    # NEW: Chat History Integration Methods
    async def process_user_message(self, user_id: int, message: str) -> tuple:
        """
        Process user message with chat history integration
        
        Args:
            user_id: Telegram user ID
            message: User message content
        
        Returns:
            tuple: (message_added_safely, recent_history, last_user_message)
        """
        # Process message with storage system
        message_added, recent_history = await temp_users_manager.store_temp_user_chat(user_id, message)
        
        # Get last user message for consistency
        last_user_message = await temp_users_manager.get_temp_user_chat(user_id)
        
        return message_added, recent_history, last_user_message
    
    async def add_bot_response(self, user_id: int, response: str):
        """
        Add bot response to chat history
        
        Args:
            user_id: Telegram user ID
            response: Bot response content
        """
        await temp_users_manager.store_temp_user_chat(user_id, response)
    
    def build_system_prompt(self, message: str, is_group: bool = False, user_context: Dict = None, recent_history: List = None) -> str:
        """Build dynamic system prompt based on context and chat history"""
        
        # Get base persona
        identity = self.prompts['persona']['identity']
        tone = self.prompts['persona']['tone'] 
        boundaries = self.prompts['persona']['boundaries']
        
        # Detect message type and mood
        msg_type = self.detect_message_type(message, is_group)
        mood = self.detect_mood(message)
        
        # Check for short inputs
        word_count = len(message.split())
        is_short_input = word_count <= 3
        
        # Get appropriate response templates
        if msg_type in self.prompts['responses']:
            response_templates = self.prompts['responses'][msg_type]
        else:
            response_templates = self.prompts['responses']['casual']
        
        # Get context-specific behavior
        if is_group:
            context_behavior = self.prompts['context']['group_chat']
        else:
            context_behavior = self.prompts['context']['private_chat']
        
        # Get config limits
        word_limits = self.prompts['config']['word_limits']
        mood_matching = self.prompts['config']['mood_matching']
        
        # Get interaction style safely
        interaction_style = context_behavior.get('group_behavior', {}).get('interaction_style') or \
                          context_behavior.get('private_behavior', {}).get('interaction_style') or \
                          context_behavior.get('interaction_style', 'Friendly, warm and respectful like a Gen-Z friend')
        
        # Build the system prompt
        system_prompt = f"""You are {identity['name']}, {identity['core_identity']}. 

PERSONA: {identity['personality']}. Interests: {', '.join(identity['interests'])}.

LANGUAGE RULES: {tone['language_style']}. {tone['pronouns']['primary']}. 
Tone: {tone['voice_characteristics']['tone']}. Max 1 emoji per reply: {', '.join(tone['emoji_usage']['allowed'][:3])}.

BEHAVIOR: {interaction_style}. Match user energy but stay respectful.

RESPONSE STYLE: Based on message type "{msg_type}" with mood "{mood}".
Max {word_limits['response_constraints']['max_words']} words, {word_limits['response_constraints']['max_lines']} line.

BOUNDARIES: {', '.join(boundaries['safety_rules']['hard_bans'][:3])}."""

        # NEW: Add conversation consistency logic
        if recent_history:
            system_prompt += f"""

CONVERSATION CONTEXT: Recent chat history available ({len(recent_history)} messages).
Use this context to maintain conversation flow and avoid repetitive responses.
Do NOT repeat same phrases like 'samjhi', 'theek hai', 'hehe' that user has seen before."""

        # Add special handling for different message types
        if msg_type == 'user_identity':
            system_prompt += """

SPECIAL HANDLING: If message type is 'user_identity', respond with warm validation (e.g., 'Aap mere dost ho! 💕'). Do NOT introduce yourself."""
        elif msg_type in ['who are you', 'tum kaun ho']:
            system_prompt += """

BOT IDENTITY: Respond with: 'Pixel hoon, aapki sweet friend 😊' - Do NOT ask about user's identity."""
        elif is_short_input:
            system_prompt += """

SHORT INPUT HANDLING: If the user input is short (less than 3 words like 'ok', 'hmm', 'acha'), the Response must be a playful statement or tease. DO NOT ask a generic question like "kya kar rahe ho". Just acknowledge nicely. Example: 'samjhi... 😊' or 'theek hai 😊'."""
        
        # CRITICAL: Strict No-Question & No-Advice Rule
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
        
        return system_prompt
    
    def get_response_template(self, msg_type: str, mood: str = None) -> str:
        """Get a random response template based on type and mood"""
        original_msg_type = msg_type  # Remember original type for dry_reply logic
        
        if msg_type not in self.prompts['responses']:
            msg_type = 'casual'
        
        templates = self.prompts['responses'][msg_type]
        
        # Get appropriate sub-category based on mood
        if mood == 'negative' and 'empathy' in templates:
            choices = templates['empathy']
        elif mood == 'excited' and 'celebration' in templates:
            choices = templates['celebration']
        elif original_msg_type == 'greetings':
            choices = templates.get('hello', list(templates.values())[0])
        elif original_msg_type == 'dry_reply':
            # For dry replies, use casual templates and pick one_word_responses sub-category
            if 'one_word_responses' in templates:
                choices = templates['one_word_responses']
            elif 'curiosity' in templates:
                choices = templates['curiosity']
            else:
                choices = templates.get('general_chat', list(templates.values())[0])
        else:
            # Get first available category
            first_key = list(templates.keys())[0]
            choices = templates[first_key]
        
        return random.choice(choices)
    
    def validate_response(self, response: str, msg_type: str) -> str:
        """Validate and ensure response has meaningful content"""
        word_limits = self.prompts['config']['word_limits']
        
        # Get appropriate max words for this type
        if msg_type in word_limits['category_specific_limits']:
            max_words = word_limits['category_specific_limits'][msg_type]['max_words']
        else:
            max_words = word_limits['response_constraints']['max_words']
        
        # Count words (excluding emojis)
        words = response.split()
        filtered_words = [word for word in words if not word.startswith(('🙂', '😊', '💕', '✨', '😍', '😉', '🎉'))]
        
        # If response is too long, try to make it shorter without losing meaning
        if len(filtered_words) > max_words:
            # Check if response contains meaningful elements
            response_lower = response.lower()
            forbidden_fragments = word_limits.get('meaning_validation', {}).get('forbidden_fragments', [])
            
            # If it's already a short meaningless response, don't truncate further
            if any(fragment in response_lower for fragment in forbidden_fragments):
                return response
            
            # Try to shorten by removing less important words
            important_words = [w for w in words if len(w) > 2 and w not in ['the', 'and', 'but', 'hai', 'hu', 'mai', 'kya', 'kyun', 'kaise']]
            
            if len(important_words) <= max_words:
                # Keep important words and essential punctuation
                final_words = []
                word_count = 0
                
                for word in words:
                    if not word.startswith(('🙂', '😊', '💕', '✨', '😍', '😉', '🎉')):
                        word_count += 1
                        
                    if word_count <= max_words:
                        final_words.append(word)
                    elif word in ['.', '?', '!', ',']:
                        # Add punctuation only if it helps complete thought
                        final_words.append(word)
                        break
                    else:
                        break
                
                response = ' '.join(final_words).strip()
            
            # If still too long and ends with ellipsis, try to find better ending
            if response.endswith('... 😊') and len(response.split()) > max_words + 2:
                # Find natural ending points
                if '?' in response:
                    response = response.split('?')[0] + '?'
                elif '.' in response:
                    response = response.split('.')[0] + '.'
                else:
                    # Take only up to max_words
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
        
        # Ensure single line
        response = response.replace('\n', ' ').strip()
        
        return response

# Global instance
prompt_builder = PromptBuilder()
