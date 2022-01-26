import logging
import os
import re

from telegram import Update
from telegram.ext import (
    CallbackContext,
    CallbackQueryHandler,
    CommandHandler,
    Filters,
    MessageHandler,
    PicklePersistence,
    Updater,
)

from . import notifications

from .constants import *
from .helpers import (
    admin_user,
    callback,
    callback_pattern,
    command,
    logged_user,
    make_keyboard,
)

CANCEL_CALLBACK = "cancel_callback"

KIND_CREDENTIALS = "credentials"

logger = logging.getLogger(__name__)

LOGIN_MESSAGE = (
    "Inserisci il tuo identificato di rete \n\n"
    "Dovrò salvare le tuo nome utente in memoria per non richiedertelo ogni volta, ma non le scriverò da nessuna parte. Lo giuro! 🙇🏽‍♂️"
)

shift_users = dict()


@command
def start_command(update: Update, context: CallbackContext):
    update.message.reply_text(
        "Ciao! Io sono shift-shift-bot! Con me potrai capire i tuoi turni di presenza senza dover aprire quell'orribile 'excel' dei turni 💩\n\n "
        "Ma prima devi effettuare il login!",
        reply_markup=make_keyboard(("Login", LOGIN_CALLBACK), context),
    )


@command
def login_command(update: Update, context: CallbackContext):
    context.user_data[INPUT_KIND] = KIND_CREDENTIALS
    update.message.reply_text(LOGIN_MESSAGE)


@callback
def login_callback(update: Update, context: CallbackContext):
    context.user_data[INPUT_KIND] = KIND_CREDENTIALS
    update.callback_query.edit_message_text(LOGIN_MESSAGE)


def credentials_input(update: Update, context: CallbackContext):
    match = re.match(r"[a-zA-Z]{6}", update.message.text)
    if not match:
        update.message.reply_markdown(
            "Il nome utente inserito non è in un formato valido\n"
            "Inserisci il nome utente di nuovo! 😑"
        )
        return

    context.user_data[LOGGED] = True
    context.user_data[SHIFT_USERNAME] = update.message.text
    context.user_data[INPUT_KIND] = None

    logger.info(
        "User %s (%s) logged in",
        update.effective_user.id,
        update.effective_user.first_name,
    )

    update.message.reply_text(
        "Nome utente salvato con successo!\n\nUsa /turni per visualizzare i tuoi turni 🎫\nUsa /notifiche per impostare gli avvisi 📢"
    )


def user_input(update: Update, context: CallbackContext):
    input_kinds = [
                      (KIND_CREDENTIALS, credentials_input)
                  ] + notifications.user_input_handlers(shift_reminder)

    for input_kind, input_callback in input_kinds:
        if context.user_data.get(INPUT_KIND) == input_kind:
            input_callback(update, context)

            return


def get_shift_user(update: Update, context: CallbackContext):
    shift_user = context.user_data[SHIFT_USERNAME]

    if not shift_user:
        message = (
            f"Scusami tanto, ma mi sono dimenticato il tuo nome utente 😕\n"
            "Devi ri effettuare il login per timbrare nuovamente"
        )
        keyboard = make_keyboard(("Login", LOGIN_CALLBACK), context)

        if update.callback_query:
            update.callback_query.edit_message_text(text=message, reply_markup=keyboard)
        else:
            update.message.reply_text(text=message, reply_markup=keyboard)

    return shift_user


@command
@logged_user
def shift_command(update: Update, context: CallbackContext):
    shift_user = get_shift_user(update, context)
    if not shift_user:
        context.user_data[LOGGED] = False
        context.user_data[SHIFT_USERNAME] = None
        return

    buttons = [("Cancella", CANCEL_CALLBACK)]

    message = "Turni ecc ecc"

    update.message.reply_text(
        text=message, reply_markup=make_keyboard([buttons], context)
    )


@callback
def cancel_callback(update: Update, context: CallbackContext):
    update.callback_query.delete_message()


@command
@admin_user
def message_command(update: Update, context: CallbackContext):
    message = re.sub("^/messaggio", "", update.message.text).strip()
    if message == "":
        return

    for user_id, _ in context.dispatcher.persistence.get_user_data().items():
        context.bot.send_message(
            chat_id=user_id, text=f"{update.effective_user.first_name}: {message}"
        )


def shift_reminder(context) -> None:
    bot = context.job.context["bot"]
    user_id = context.job.context["user_id"]
    user_data = context.job.context["user_data"]
    schedule_data = context.job.context["schedule_data"]

    user_data[INPUT_KIND] = None

    shift_type = schedule_data["shift_type"]
    shift_user = user_data[SHIFT_USERNAME]
    if not shift_user:
        message = f"Hey! Dovrei avvisarti sul possibile turno, ma non ho più il tuo nome utente per poter verificare 😕"
        bot.send_message(
            chat_id=user_id,
            text=message,
            reply_markup=make_keyboard(("Login", LOGIN_CALLBACK), user_data=user_data),
        )
        return

    message = f"Testo! 📢"
    keyboard = make_keyboard(
        [[("Cancella", CANCEL_CALLBACK)]], user_data=user_data
    )

    bot.send_message(chat_id=user_id, text=message, reply_markup=keyboard)


@command
def notification_command(update: Update, context: CallbackContext):
    notifications.main_menu(update, context)


def run() -> None:
    data_dir = os.getenv("DATA_DIR") or os.getcwd()
    persistence = PicklePersistence(filename=os.path.join(data_dir, "bot.db"))
    updater = Updater(os.getenv("TELEGRAM_TOKEN"), persistence=persistence)

    dispatcher = updater.dispatcher

    handlers = [
                   CommandHandler("start", start_command),
                   CommandHandler("login", login_command),
                   CommandHandler("turni", shift_command),
                   CommandHandler("messaggio", message_command),
                   CommandHandler("notifiche", notification_command),
                   CallbackQueryHandler(login_callback, pattern=callback_pattern(LOGIN_CALLBACK)),
                   CallbackQueryHandler(
                       cancel_callback, pattern=callback_pattern(CANCEL_CALLBACK)
                   ),
                   MessageHandler(Filters.text & ~Filters.command, user_input),
               ] + notifications.handlers(shift_reminder)

    notifications.setup_scheduler(updater, shift_reminder)

    for handler in handlers:
        dispatcher.add_handler(handler)

    updater.start_polling()

    updater.idle()
