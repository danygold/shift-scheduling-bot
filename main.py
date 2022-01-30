import logging
import os
import sys

from dotenv import load_dotenv

from shift.bot import run

# noinspection SpellCheckingInspection
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

logger = logging.getLogger(__name__)


def main():
    if not load_dotenv():
        logger.debug("Failed to load environment variables from .env file")

    required_vars = ["TELEGRAM_TOKEN"]
    for var in required_vars:
        if not os.getenv(var):
            logger.error(f"{var} variable not present")
            return False

    run()

    return True


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
