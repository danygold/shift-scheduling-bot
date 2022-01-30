"""
This module contains the constants of the application
"""

import os

LOGIN_CALLBACK = "login_callback"
INPUT_KIND = "input_kind"
LOGGED = "logged"
USER_GROUP = "user_group"
BOT_DEFAULT_NAME = "shift-scheduling-bot"
DB_DEFAULT_NAME = "bot.db"
DB_NAME = os.getenv("DB_NAME") or DB_DEFAULT_NAME
SHIFTS_DEFAULT_FILENAME = "shifts.json"
SHIFTS_FILENAME = os.getenv("SHIFTS_FILENAME") or SHIFTS_DEFAULT_FILENAME


def get_bot_name():
    """
    Returns the bot name, using the following logic:
    BOT_NAME if env variabile is filled, otherwise, BOT_DEFAULT_NAME
    :return: the bot name
    """
    return os.getenv("BOT_NAME") or BOT_DEFAULT_NAME
