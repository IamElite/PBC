import asyncio
import importlib

import pyrogram
from pyrogram import idle

from src import app, logger
from src.modules import ALL_MODULES


async def main():
    logger.info("Bot is starting...")
    
    await app.start()
    
    try:
        await app.send_message(app.logger, "Bot Started")
    except Exception as ex:
        raise SystemExit(f"Bot has failed to access the log group: {app.logger}")
    
    for module in ALL_MODULES:
        importlib.import_module(f"src.modules.{module}")
    logger.info(f"Loaded {len(ALL_MODULES)} modules.")
    
    logger.info(f"Bot started as @{app.username}")

    await idle()
    
    await app.stop()
    logger.info("Bot stopped.")


if __name__ == "__main__":
    try:
        asyncio.get_event_loop().run_until_complete(main())
    except KeyboardInterrupt:
        pass