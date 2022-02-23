"""
This module contains the constants of the application
"""

import os

LOGIN_CALLBACK = "login_callback"
REGISTER_CALLBACK = "register_callback"
INPUT_KIND = "input_kind"
LOGGED = "logged"
USER_GROUP = "user_group"
REGISTRATION = "registration"
BOT_DEFAULT_NAME = "shift-scheduling-bot"
DB_DEFAULT_NAME = "bot.db"
SHIFTS_DEFAULT_FILENAME = "shifts.json"
GROUP_PREFIX = "GROUP_"


def get_bot_name():
    """
    Returns the bot name, using the following logic:
    BOT_NAME env if variabile is filled, otherwise, BOT_DEFAULT_NAME
    :return: the bot name
    """
    return os.getenv("BOT_NAME") or BOT_DEFAULT_NAME


def get_database_name():
    """
    Returns the database name, using the following logic:
    DB_NAME env if variable is filled, otherwise, DB_DEFAULT_NAME
    :return: the database name
    """
    return os.getenv("DB_NAME") or DB_DEFAULT_NAME


def get_shifts_filename():
    """
    Returns the shifts file name, using the following logic:
    SHIFTS_FILENAME env if variabile is filled, otherwise, SHIFTS_DEFAULT_FILENAME
    :return: the shifts file name
    """
    return os.getenv("SHIFTS_FILENAME") or SHIFTS_DEFAULT_FILENAME
