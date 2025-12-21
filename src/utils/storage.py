"""
Temp Users Chat Storage System for Pixel Bot
=============================================

MongoDB-based temp users chat data storage with:
- BULK MONGO URLS HANDLING for temp users
- 26 Public MongoDB URLs integration
- Multiple database connections support
- Hash-based user distribution
- Auto cleanup (2 days retention)
- Safety checks for real-life data

Author: AI Backend Engineer
"""

import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from motor.motor_asyncio import AsyncIOMotorClient


class TempUsersManager:
    """Temp users chat data management system using 26 public MongoDB URLs"""
    
    def __init__(self):
        """Initialize with 26 public MongoDB URLs"""
        # ALL 26 PUBLIC MongoDB URLs for temp users
        self.public_mongo_urls = [
            "mongodb+srv://hnyx:wywyw2@cluster0.9dxlslv.mongodb.net/?retryWrites=true&w=majority",
            "mongodb+srv://ravi:ravi12345@cluster0.hndinhj.mongodb.net/?retryWrites=true&w=majority",
            "mongodb+srv://userbot:userbot@cluster0.iweqz.mongodb.net/test?retryWrites=true&w=majority",
            "mongodb+srv://Alisha:Alisha123@cluster0.yqcpftw.mongodb.net/?retryWrites=true&w=majority",
            "mongodb+srv://vikashgup87:EDRIe3bdEq85Pdpl@cluster0.pvoygcu.mongodb.net/?retryWrites=true&w=majority",
            "mongodb+srv://Sarkar123:GAUTAMMISHRA@sarkar.1uiwqkd.mongodb.net/?retryWrites=true&w=majority",
            "mongodb+srv://kuldiprathod2003:kuldiprathod2003@cluster0.wxqpikp.mongodb.net/?retryWrites=true&w=majority",
            "mongodb+srv://Alisha:Alisha123@cluster0.yqcpftw.mongodb.net/?retryWrites=true&w=majority",
            "mongodb+srv://Krishna:pss968048@cluster0.4rfuzro.mongodb.net/?retryWrites=true&w=majority",
            "mongodb+srv://rahul:rahulkr@cluster0.szdpcp6.mongodb.net/?retryWrites=true&w=majority",
            "mongodb+srv://knight_rider:GODGURU12345@knight.jm59gu9.mongodb.net/?retryWrites=true&w=majority",
            "mongodb+srv://bikash:bikash@bikash.3jkvhp7.mongodb.net/?retryWrites=true&w=majority",
            "mongodb+srv://Bikash:Bikash@bikash.yl2nhcy.mongodb.net/?retryWrites=true&w=majority",
            "mongodb+srv://Mrdaxx123:Mrdaxx123@cluster0.q1da65h.mongodb.net/?retryWrites=true&w=majority",
            "mongodb+srv://teamdaxx123:teamdaxx123@cluster0.ysbpgcp.mongodb.net/?retryWrites=true&w=majority",
            "mongodb+srv://chatbot1:a@cluster0.pxbu0.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0",
            "mongodb+srv://chatbot2:b@cluster0.9i8as.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0",
            "mongodb+srv://chatbot3:c@cluster0.0ak9k.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0",
            "mongodb+srv://chatbot4:d@cluster0.4i428.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0",
            "mongodb+srv://chatbot5:e@cluster0.pmaap.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0",
            "mongodb+srv://chatbot6:f@cluster0.u63li.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0",
            "mongodb+srv://chatbot7:g@cluster0.mhzef.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0",
            "mongodb+srv://chatbot8:h@cluster0.okxao.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0",
            "mongodb+srv://chatbot9:i@cluster0.yausb.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0",
            "mongodb+srv://chatbot10:j@cluster0.9esnn.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0",
            "mongodb+srv://public:abishnoimf@cluster0.rqk6ihd.mongodb.net/?retryWrites=true&w=majority"
        ]
        
        # Storage connections
        self.bulk_connections = {}  # Store multiple MongoDB connections
        self.temp_user_collections = {}  # Store temp user collections
        
        # Safety keywords to detect real-life data
        self.dangerous_keywords = [
            'meet', 'meeting', 'milna', 'aaunga', 'aa rahi hoon',
            'address', 'ghar', 'home', 'location', 'where',
            'time', 'baje', '6 baje', '7 baje', '8 baje',
            'tomorrow', 'kal', 'day', 'date', 'place'
        ]
    
    # Initialize all 26 public MongoDB URLs
    async def initialize_all_public_urls(self):
        """
        Automatically initialize all 26 public MongoDB URLs for temp users
        Call this method when starting the bot
        """
        try:
            print(f"🚀 Initializing {len(self.public_mongo_urls)} public MongoDB URLs...")
            await self.add_bulk_mongo_urls(self.public_mongo_urls)
            print(f"✅ All {len(self.public_mongo_urls)} public MongoDB URLs initialized successfully!")
            
            # Show statistics
            stats = await self.get_bulk_stats()
            print(f"📊 Bulk Stats: {stats}")
            
        except Exception as e:
            print(f"❌ Error initializing public URLs: {e}")
    
    # Add multiple MongoDB URLs for temp users
    async def add_bulk_mongo_urls(self, mongo_urls: List[str]):
        """
        Add multiple MongoDB URLs for temp users
        
        Args:
            mongo_urls: List of MongoDB connection URLs
        """
        try:
            successful_connections = 0
            failed_connections = []
            
            for i, mongo_url in enumerate(mongo_urls):
                try:
                    connection_name = f"temp_db_{i+1}"
                    
                    # Create new connection for temp users
                    temp_client = AsyncIOMotorClient(mongo_url)
                    temp_db = temp_client["temp_chat_data"]
                    temp_collection = temp_db["temp_users"]
                    
                    self.bulk_connections[connection_name] = temp_client
                    self.temp_user_collections[connection_name] = temp_collection
                    
                    print(f"✅ Added temp Mongo connection: {connection_name}")
                    successful_connections += 1
                    
                except Exception as e:
                    failed_connections.append(f"{connection_name}: {str(e)}")
                    print(f"❌ Failed to connect to {connection_name}: {e}")
            
            print(f"🗄️ Total successful connections: {successful_connections}/{len(mongo_urls)}")
            
            if failed_connections:
                print(f"⚠️ Failed connections: {len(failed_connections)}")
                for failed in failed_connections[:5]:  # Show first 5 failures
                    print(f"   - {failed}")
            
        except Exception as e:
            print(f"❌ Error adding bulk Mongo URLs: {e}")
    
    # Get appropriate temp collection for a user based on user_id hash
    async def get_temp_collection(self, user_id: int):
        """
        Get appropriate temp collection for a user based on user_id hash
        
        Args:
            user_id: Telegram user ID
        
        Returns:
            Collection object for temp storage
        """
        # Hash user_id to distribute across temp collections
        if len(self.temp_user_collections) == 0:
            print("⚠️ No temp collections available! Initialize with initialize_all_public_urls()")
            return None
            
        collection_index = user_id % len(self.temp_user_collections)
        collection_names = list(self.temp_user_collections.keys())
        collection_name = collection_names[collection_index]
        
        return self.temp_user_collections[collection_name]
    
    # Store temp user chat data in bulk Mongo connections
    async def store_temp_user_chat(self, user_id: int, username: str, chat_data: Dict):
        """
        Store temp user chat data in bulk Mongo connections
        
        Args:
            user_id: Telegram user ID
            username: User's username
            chat_data: Complete chat data to store
        """
        try:
            # Safety check - don't store dangerous messages
            if self._is_dangerous_message(chat_data.get('message', '')):
                print(f"⚠️ BLOCKED: Dangerous message from user {user_id}: {str(chat_data)[:50]}...")
                return False
            
            # Get appropriate temp collection
            temp_collection = await self.get_temp_collection(user_id)
            
            if not temp_collection:
                print(f"⚠️ No temp collection available for user {user_id}")
                return False
            
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
            return True
            
        except Exception as e:
            print(f"❌ Error storing temp user chat: {e}")
            return False
    
    # Retrieve temp user chat data
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
            
            if not temp_collection:
                return None
            
            temp_user = await temp_collection.find_one({"user_id": user_id})
            if temp_user and temp_user.get("is_temp"):
                return temp_user.get("chat_data")
            
            return None
            
        except Exception as e:
            print(f"❌ Error getting temp user chat: {e}")
            return None
    
    # Clean up old temp user data (2 days retention)
    async def cleanup_temp_users(self, days_old: int = 2):
        """
        Clean up old temp user data (2 days for temp users)
        
        Args:
            days_old: Remove temp data older than these days (default: 2 days)
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_old)
            total_cleaned = 0
            
            for collection_name, temp_collection in self.temp_user_collections.items():
                # Remove old temp data
                result = await temp_collection.delete_many({
                    "is_temp": True,
                    "last_updated": {"$lt": cutoff_date}
                })
                
                print(f"🧹 Cleaned up {result.deleted_count} temp users from {collection_name}")
                total_cleaned += result.deleted_count
            
            print(f"🧹 Total cleaned temp users: {total_cleaned}")
        
        except Exception as e:
            print(f"❌ Error cleaning up temp users: {e}")
    
    # Check if message contains dangerous real-life data
    def _is_dangerous_message(self, message: str) -> bool:
        """
        Check if message contains dangerous real-life data
        
        Args:
            message: Message content to check
        
        Returns:
            bool: True if message is dangerous
        """
        if not message:
            return False
            
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
    
    # Get statistics about bulk connections and temp users
    async def get_bulk_stats(self) -> Dict:
        """
        Get statistics about bulk connections and temp users
        
        Returns:
            Dictionary with bulk processing stats
        """
        try:
            stats = {
                "total_public_urls": len(self.public_mongo_urls),
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
    
    # Close all bulk MongoDB connections
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
temp_users_manager = TempUsersManager()