import datetime
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
from . import shiftsheduling

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
SHIFTS_PREVIOUS_CALLBACK = "shifts_previous_callback"
SHIFTS_NEXT_CALLBACK = "shifts_next_callback"

KIND_CREDENTIALS = "credentials"

logger = logging.getLogger(__name__)

LOGIN_MESSAGE = (
    "Inserisci il tuo gruppo dei turni \n\n"
    "Questa informazione mi è essenziale per fornirti i turni corretti ️"
)

shift_users = dict()


@command
def start_command(update: Update, context: CallbackContext):
    update.message.reply_text(
        f"Ciao! Io sono {BOT_NAME}! Con me potrai capire i tuoi turni di presenza senza dover aprire 'excel' dei turni \n\n "
        "Ma prima devi effettuare il login, digitanto il tuo codice gruppo!",
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
    match = re.match(r"[\d]+", update.message.text)
    if not match:
        update.message.reply_markdown(
            "Il codie gruppo inserito non è in un formato valido\n"
            "Inserisci il codice gruppo di nuovo! 😑"
        )
        return

    group = "GROUP_" + update.message.text
    if not shiftsheduling.is_valid_group(group):
        update.message.reply_markdown(
            "Il codie gruppo inserito non è tra quelli validi\n"
            "Inserisci il codice gruppo corretto! 😑"
        )
        return

    context.user_data[LOGGED] = True
    context.user_data[USER_GROUP] = group
    context.user_data[INPUT_KIND] = None

    logger.info(
        "User %s (%s) registered: Group code %s",
        update.effective_user.id,
        update.effective_user.first_name,
        group,
    )

    update.message.reply_text(
        "Gruppo salvato con successo!\n\nUsa /turni per visualizzare i tuoi turni 🎫\nUsa /notifiche per impostare gli avvisi 📢"
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
    shift_user = context.user_data[USER_GROUP]

    if not shift_user:
        message = (
            f"Scusami tanto, ma mi sono dimenticato il tuo gruppo 😕\n"
            "Devi ri effettuare il login per poter utilizzare questo comando"
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
        context.user_data[USER_GROUP] = None
        return

    if datetime.datetime.today().weekday() < 6:
        base_datetime = datetime.datetime.now()
    else:
        base_datetime = datetime.datetime.now() + datetime.timedelta(days=2)

    context.user_data["shift_date"] = base_datetime

    shifts(update, context, context.user_data["shift_date"])


@command
@logged_user
def tomorrow_command(update: Update, context: CallbackContext):
    shift_user = get_shift_user(update, context)
    if not shift_user:
        context.user_data[LOGGED] = False
        context.user_data[USER_GROUP] = None
        return

    compare_date = datetime.datetime.now() + datetime.timedelta(days=1)
    if compare_date.weekday() == 5:
        compare_date = compare_date + datetime.timedelta(days=2)
    elif compare_date.weekday() == 6:
        compare_date = compare_date + datetime.timedelta(days=1)

    if shiftsheduling.is_smart_working_day(compare_date, context.user_data):
        message = "Domani sarai in Smart working"
    elif shiftsheduling.is_presence_day(compare_date, context.user_data):
        message = "Domani sarai in ufficio"
    else:
        message = "Non ci sono turni per domani :("

    update.message.reply_text(text=message)


def shifts(update: Update, context: CallbackContext, date: datetime):
    buttons = [
        ("️⬅️ Precedente", SHIFTS_PREVIOUS_CALLBACK),
        ("Successivo ➡", SHIFTS_NEXT_CALLBACK),
    ]

    message = "Ecco i turni della settimana \n\n" + shiftsheduling.get_current_week_message(date,
                                                                                            context.user_data)

    if update.message:
        update.message.reply_text(text=message, reply_markup=make_keyboard([buttons], context))
    else:
        update.callback_query.edit_message_text(text=message, reply_markup=make_keyboard([buttons], context))


@callback
def cancel_callback(update: Update, context: CallbackContext):
    update.callback_query.delete_message()


@callback
def previous_shifts_callback(update: Update, context: CallbackContext):
    context.user_data["shift_date"] = context.user_data["shift_date"] - datetime.timedelta(weeks=1)

    shifts(update, context, context.user_data["shift_date"])


@callback
def next_shifts_callback(update: Update, context: CallbackContext):
    context.user_data["shift_date"] = context.user_data["shift_date"] + datetime.timedelta(weeks=1)

    shifts(update, context, context.user_data["shift_date"])


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

    compare_date = datetime.datetime.now() + datetime.timedelta(days=1)

    if shift_type == "Smart":
        send_notify = shiftsheduling.is_smart_working_day(compare_date, user_data)
    elif shift_type == "Ufficio":
        send_notify = shiftsheduling.is_presence_day(compare_date, user_data)
    else:
        send_notify = False

    if send_notify:
        shift_user = user_data[USER_GROUP]
        if not shift_user:
            message = f"Hey! Dovrei avvisarti sul possibile turno, ma non ho più il tuo gruppo per poter verificare 😕"
            bot.send_message(
                chat_id=user_id,
                text=message,
                reply_markup=make_keyboard(("Login", LOGIN_CALLBACK), user_data=user_data),
            )
            return

        message = f"Hey. Ricordati che domani sarai in {shift_type} 📢"

        bot.send_message(chat_id=user_id, text=message)


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
                   CommandHandler("domani", tomorrow_command),
                   CommandHandler("messaggio", message_command),
                   CommandHandler("notifiche", notification_command),
                   CallbackQueryHandler(login_callback, pattern=callback_pattern(LOGIN_CALLBACK)),
                   CallbackQueryHandler(cancel_callback, pattern=callback_pattern(CANCEL_CALLBACK)),
                   CallbackQueryHandler(previous_shifts_callback, pattern=callback_pattern(SHIFTS_PREVIOUS_CALLBACK)),
                   CallbackQueryHandler(next_shifts_callback, pattern=callback_pattern(SHIFTS_NEXT_CALLBACK)),
                   MessageHandler(Filters.text & ~Filters.command, user_input),
               ] + notifications.handlers(shift_reminder)

    notifications.setup_scheduler(updater, shift_reminder)

    for handler in handlers:
        dispatcher.add_handler(handler)

    # Load shifts
    shiftsheduling.load_shifts(os.path.join(data_dir, "db.json"))

    updater.start_polling()

    updater.idle()
