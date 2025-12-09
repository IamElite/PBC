import time
import logging
import pyrogram
from motor.motor_asyncio import AsyncIOMotorClient

import config

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s - %(levelname)s] - %(name)s - %(message)s",
    datefmt="%d-%b-%y %H:%M:%S",
    handlers=[
        logging.FileHandler("log.txt"),
        logging.StreamHandler(),
    ],
)

logging.getLogger("pymongo").setLevel(logging.ERROR)
logging.getLogger("pyrogram").setLevel(logging.ERROR)
logger = logging.getLogger(__name__)

db = AsyncIOMotorClient(config.MONGO_URL).EraChatBot

START_TIME = time.time()


class Bot(pyrogram.Client):
    def __init__(self):
        super().__init__(
            name="era",
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            bot_token=config.BOT_TOKEN,
            parse_mode=pyrogram.enums.ParseMode.HTML,
            max_concurrent_transmissions=7,
        )
        self.owner = config.OWNER_ID
        self.logger = config.OWNER_ID

    async def start(self):
        await super().start()
        self.id = self.me.id
        self.name = self.me.first_name
        self.username = self.me.username
        self.mention = self.me.mention

    async def stop(self):
        await super().stop()


app = Bot()
