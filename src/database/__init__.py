from motor.motor_asyncio import AsyncIOMotorClient
import config 

ChatBot = AsyncIOMotorClient(config.MONGO_URL)
db = ChatBot["Era"]

usersdb = db["users"] # Users Collection
chatsdb = db["chats"] # Chats Collection


from .chats import *
