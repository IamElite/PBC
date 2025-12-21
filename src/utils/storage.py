"""
Chat History Storage System for Pixel Bot
=========================================

MongoDB-based chat history management with:
- Per-user data storage
- Memory logic for daily vs inactive users  
- Auto cleanup of old history
- Conversation consistency
- Safety checks for real-life data

Author: AI Backend Engineer
"""

import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import config
from src.database import usersdb


class ChatHistoryManager:
    """MongoDB-based chat history management system"""
    
    def __init__(self):
        """Initialize with database connection"""
        self.history_retention_days = config.CHAT_HISTORY_DAYS
        self.collection = usersdb  # Using existing usersdb for simplicity
        
        # Safety keywords to detect real-life data
        self.dangerous_keywords = [
            'meet', 'meeting', 'milna', 'aaunga', 'aa rahi hoon',
            'address', 'ghar', 'home', 'location', 'where',
            'time', 'baje', '6 baje', '7 baje', '8 baje',
            'tomorrow', 'kal', 'day', 'date', 'place'
        ]
    
    async def add_message(self, user_id: int, message: str, role: str = "user") -> bool:
        """
        Add message to user's chat history with safety checks
        
        Args:
            user_id: Telegram user ID
            message: Message content
            role: "user" or "assistant"
        
        Returns:
            bool: True if message was added safely
        """
        try:
            # Safety check - don't store dangerous messages
            if await self._is_dangerous_message(message):
                print(f"⚠️ BLOCKED: Dangerous message from user {user_id}: {message[:50]}...")
                return False
            
            # Get or create user record
            user_record = await self.collection.find_one({"user_id": user_id})
            if not user_record:
                user_record = {
                    "user_id": user_id,
                    "chat_history": [],
                    "last_active": datetime.utcnow(),
                    "created_at": datetime.utcnow()
                }
                await self.collection.insert_one(user_record)
            
            # Add message to history
            message_data = {
                "content": message,
                "role": role,
                "timestamp": datetime.utcnow()
            }
            
            # Update user record
            await self.collection.update_one(
                {"user_id": user_id},
                {
                    "$push": {"chat_history": message_data},
                    "$set": {"last_active": datetime.utcnow()}
                }
            )
            
            # Trigger cleanup after adding message
            await self._cleanup_old_history()
            
            return True
            
        except Exception as e:
            print(f"❌ Error adding message: {e}")
            return False
    
    async def get_recent_history(self, user_id: int, limit: int = 10) -> List[Dict]:
        """
        Get recent chat history for a user
        
        Args:
            user_id: Telegram user ID
            limit: Number of recent messages to retrieve
        
        Returns:
            List of recent messages
        """
        try:
            user_record = await self.collection.find_one({"user_id": user_id})
            if not user_record or not user_record.get("chat_history"):
                return []
            
            # Get recent messages
            history = user_record["chat_history"]
            recent_messages = history[-limit:] if len(history) > limit else history
            
            return recent_messages
            
        except Exception as e:
            print(f"❌ Error getting history: {e}")
            return []
    
    async def get_last_user_message(self, user_id: int) -> Optional[str]:
        """
        Get the last message from user (for consistency checking)
        
        Args:
            user_id: Telegram user ID
        
        Returns:
            Last user message or None
        """
        try:
            history = await self.get_recent_history(user_id, limit=20)
            for msg in reversed(history):
                if msg["role"] == "user":
                    return msg["content"]
            return None
            
        except Exception as e:
            print(f"❌ Error getting last message: {e}")
            return None
    
    async def get_user_activity_status(self, user_id: int) -> str:
        """
        Check if user is daily active or inactive
        
        Args:
            user_id: Telegram user ID
        
        Returns:
            "daily", "inactive", or "new"
        """
        try:
            user_record = await self.collection.find_one({"user_id": user_id})
            if not user_record:
                return "new"
            
            last_active = user_record.get("last_active")
            if not last_active:
                return "new"
            
            # Check if active in last 24 hours
            now = datetime.utcnow()
            if isinstance(last_active, str):
                last_active = datetime.fromisoformat(last_active.replace('Z', '+00:00'))
            
            days_diff = (now - last_active).days
            if days_diff == 0:
                return "daily"
            elif days_diff < self.history_retention_days:
                return "inactive"
            else:
                return "inactive"
                
        except Exception as e:
            print(f"❌ Error checking activity: {e}")
            return "new"
    
    async def _cleanup_old_history(self):
        """Auto cleanup old history based on retention days"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=self.history_retention_days)
            
            # Get all users
            async for user in self.collection.find({}):
                user_id = user["user_id"]
                chat_history = user.get("chat_history", [])
                
                # Filter recent messages only
                recent_messages = []
                for msg in chat_history:
                    msg_time = msg.get("timestamp")
                    if isinstance(msg_time, str):
                        msg_time = datetime.fromisoformat(msg_time.replace('Z', '+00:00'))
                    
                    if msg_time >= cutoff_date:
                        recent_messages.append(msg)
                
                # Update user with recent messages only
                await self.collection.update_one(
                    {"user_id": user_id},
                    {
                        "$set": {"chat_history": recent_messages}
                    }
                )
            
            print(f"🧹 Cleanup completed: Kept messages from last {self.history_retention_days} days")
            
        except Exception as e:
            print(f"❌ Error during cleanup: {e}")
    
    async def delete_user_history(self, user_id: int):
        """
        Delete all history for a user (for inactive users)
        
        Args:
            user_id: Telegram user ID
        """
        try:
            await self.collection.update_one(
                {"user_id": user_id},
                {"$set": {"chat_history": []}}
            )
            print(f"🗑️ Deleted history for user {user_id}")
            
        except Exception as e:
            print(f"❌ Error deleting history: {e}")
    
    async def _is_dangerous_message(self, message: str) -> bool:
        """
        Check if message contains dangerous real-life data
        
        Args:
            message: Message content to check
        
        Returns:
            bool: True if message is dangerous
        """
        message_lower = message.lower()
        
        # Check for dangerous keywords
        for keyword in self.dangerous_keywords:
            if keyword in message_lower:
                return True
        
        # Check for specific dangerous patterns
        dangerous_patterns = [
            'aa rahi hoon', 'meet karte hain', 'milenge',
            '6 baje', '7 baje', '8 baje', 'kal milenge',
            'address', 'ghar ka address', 'where are you'
        ]
        
        for pattern in dangerous_patterns:
            if pattern in message_lower:
                return True
        
        return False
    
    async def should_delete_user_history(self, user_id: int) -> bool:
        """
        Check if user's history should be deleted (inactive users)
        
        Args:
            user_id: Telegram user ID
        
        Returns:
            bool: True if history should be deleted
        """
        activity_status = await self.get_user_activity_status(user_id)
        
        # Delete history for inactive users
        if activity_status == "inactive":
            print(f"🗑️ User {user_id} is inactive - deleting history")
            return True
        
        return False
    
    async def process_user_message(self, user_id: int, message: str) -> Tuple[bool, List[Dict]]:
        """
        Complete processing of user message:
        1. Check if history should be deleted
        2. Add message if safe
        3. Return recent history for consistency
        
        Args:
            user_id: Telegram user ID
            message: User message content
        
        Returns:
            Tuple of (message_added_safely, recent_history)
        """
        try:
            # Check if should delete history (inactive users)
            if await self.should_delete_user_history(user_id):
                await self.delete_user_history(user_id)
            
            # Add message safely
            message_added = await self.add_message(user_id, message, "user")
            
            # Get recent history for AI to use
            recent_history = await self.get_recent_history(user_id, limit=8)
            
            return message_added, recent_history
            
        except Exception as e:
            print(f"❌ Error processing user message: {e}")
            return False, []
    
    async def add_bot_response(self, user_id: int, response: str):
        """
        Add bot response to history
        
        Args:
            user_id: Telegram user ID
            response: Bot response content
        """
        await self.add_message(user_id, response, "assistant")


# Global instance
chat_manager = ChatHistoryManager()