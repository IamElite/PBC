"""
Chat History Storage System for Pixel Bot
=========================================

MongoDB-based chat history management with:
- Per-user data storage
- Memory logic for daily vs inactive users  
- Auto cleanup of old history
- Conversation consistency
- Safety checks for real-life data
- BULK MONGO URLS HANDLING for temp users
- Multiple database connections support

Author: AI Backend Engineer
"""

import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import config
from src.database import usersdb
from motor.motor_asyncio import AsyncIOMotorClient


class ChatHistoryManager:
    """MongoDB-based chat history management system with bulk processing"""
    
    def __init__(self):
        """Initialize with database connection"""
        self.history_retention_days = config.CHAT_HISTORY_DAYS
        self.collection = usersdb  # Using existing usersdb for simplicity
        
        # BULK: Multiple Mongo connections for temp users
        self.bulk_connections = {}  # Store multiple MongoDB connections
        self.temp_user_collections = {}  # Store temp user collections
        
        # Safety keywords to detect real-life data
        self.dangerous_keywords = [
            'meet', 'meeting', 'milna', 'aaunga', 'aa rahi hoon',
            'address', 'ghar', 'home', 'location', 'where',
            'time', 'baje', '6 baje', '7 baje', '8 baje',
            'tomorrow', 'kal', 'day', 'date', 'place'
        ]
    
    # NEW: Bulk Mongo URL handling methods
    async def add_bulk_mongo_urls(self, mongo_urls: List[str]):
        """
        Add multiple MongoDB URLs for temp users
        
        Args:
            mongo_urls: List of MongoDB connection URLs
        """
        try:
            for i, mongo_url in enumerate(mongo_urls):
                connection_name = f"temp_db_{i+1}"
                
                # Create new connection for temp users
                temp_client = AsyncIOMotorClient(mongo_url)
                temp_db = temp_client["temp_chat_data"]
                temp_collection = temp_db["temp_users"]
                
                self.bulk_connections[connection_name] = temp_client
                self.temp_user_collections[connection_name] = temp_collection
                
                print(f"✅ Added temp Mongo connection: {connection_name}")
            
            print(f"🗄️ Total bulk connections: {len(self.bulk_connections)}")
            
        except Exception as e:
            print(f"❌ Error adding bulk Mongo URLs: {e}")
    
    async def get_temp_collection(self, user_id: int):
        """
        Get appropriate temp collection for a user based on user_id hash
        
        Args:
            user_id: Telegram user ID
        
        Returns:
            Collection object for temp storage
        """
        # Hash user_id to distribute across temp collections
        collection_index = user_id % len(self.temp_user_collections)
        collection_names = list(self.temp_user_collections.keys())
        collection_name = collection_names[collection_index]
        
        return self.temp_user_collections[collection_name]
    
    async def store_temp_user_chat(self, user_id: int, username: str, chat_data: Dict):
        """
        Store temp user chat data in bulk Mongo connections
        
        Args:
            user_id: Telegram user ID
            username: User's username
            chat_data: Complete chat data to store
        """
        try:
            # Get appropriate temp collection
            temp_collection = await self.get_temp_collection(user_id)
            
            # Prepare temp user data
            temp_user_data = {
                "user_id": user_id,
                "username": username,
                "chat_data": chat_data,
                "created_at": datetime.utcnow(),
                "last_updated": datetime.utcnow(),
                "is_temp": True  # Mark as temporary data
            }
            
            # Store in temp collection (upsert)
            await temp_collection.update_one(
                {"user_id": user_id},
                {"$set": temp_user_data},
                upsert=True
            )
            
            print(f"📦 Stored temp chat data for user {user_id} ({username})")
            
        except Exception as e:
            print(f"❌ Error storing temp user chat: {e}")
    
    async def get_temp_user_chat(self, user_id: int) -> Optional[Dict]:
        """
        Retrieve temp user chat data
        
        Args:
            user_id: Telegram user ID
        
        Returns:
            Chat data or None
        """
        try:
            temp_collection = await self.get_temp_collection(user_id)
            
            temp_user = await temp_collection.find_one({"user_id": user_id})
            if temp_user and temp_user.get("is_temp"):
                return temp_user.get("chat_data")
            
            return None
            
        except Exception as e:
            print(f"❌ Error getting temp user chat: {e}")
            return None
    
    async def cleanup_temp_users(self, days_old: int = 7):
        """
        Clean up old temp user data
        
        Args:
            days_old: Remove temp data older than these days
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_old)
            
            for collection_name, temp_collection in self.temp_user_collections.items():
                # Remove old temp data
                result = await temp_collection.delete_many({
                    "is_temp": True,
                    "last_updated": {"$lt": cutoff_date}
                })
                
                print(f"🧹 Cleaned up {result.deleted_count} temp users from {collection_name}")
        
        except Exception as e:
            print(f"❌ Error cleaning up temp users: {e}")
    
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
    
    # BULK: Additional utility methods for temp users
    async def get_bulk_stats(self) -> Dict:
        """
        Get statistics about bulk connections and temp users
        
        Returns:
            Dictionary with bulk processing stats
        """
        try:
            stats = {
                "bulk_connections": len(self.bulk_connections),
                "temp_collections": len(self.temp_user_collections),
                "connection_names": list(self.bulk_connections.keys())
            }
            
            # Count temp users in each collection
            for collection_name, collection in self.temp_user_collections.items():
                count = await collection.count_documents({"is_temp": True})
                stats[f"temp_users_{collection_name}"] = count
            
            return stats
            
        except Exception as e:
            print(f"❌ Error getting bulk stats: {e}")
            return {}
    
    async def close_all_connections(self):
        """Close all bulk MongoDB connections"""
        try:
            for connection_name, client in self.bulk_connections.items():
                client.close()
                print(f"🔌 Closed connection: {connection_name}")
            
            self.bulk_connections.clear()
            self.temp_user_collections.clear()
            
        except Exception as e:
            print(f"❌ Error closing connections: {e}")


# Global instance
chat_manager = ChatHistoryManager()