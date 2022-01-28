import os

LOGIN_CALLBACK = "login_callback"
INPUT_KIND = "input_kind"
LOGGED = "logged"
USER_GROUP = "user_group"
BOT_DEFAULT_NAME = "shift-scheduling-bot"
BOT_NAME = os.getenv("BOT_NAME") or BOT_DEFAULT_NAME
DB_DEFAULT_NAME = "bot.db"
DB_NAME = os.getenv("DB_NAME") or DB_DEFAULT_NAME
SHIFTS_DEFAULT_FILENAME = "shifts.json"
SHIFTS_FILENAME = os.getenv("SHIFTS_FILENAME") or SHIFTS_DEFAULT_FILENAME
