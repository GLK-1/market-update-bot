import asyncio
import logging
import sys

# Basic logging setup
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(message)s',
    stream=sys.stdout
)

logger = logging.getLogger(__name__)

async def test_async():
    print("Direct print: Starting test")  # Direct print for verification
    logger.info("Starting async test")
    await asyncio.sleep(1)
    logger.info("Async test complete")
    return True

if __name__ == "__main__":
    print("Script starting...")  # Direct print
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(test_async())