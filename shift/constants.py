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
    return os.getenv("BOT_NAME") or BOT_DEFAULT_NAME
