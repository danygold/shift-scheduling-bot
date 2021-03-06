"""This module contains the bot main commands."""

import datetime
import logging
import re

from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, ParseMode
from telegram.ext import (
    CallbackContext,
    CallbackQueryHandler,
    CommandHandler,
    Filters,
    MessageHandler,
    PicklePersistence,
    Updater, Dispatcher,
)

from . import notifications
from . import shiftsheduling
from .constants import *
from .datehelper import format_date, DAYS_OF_WEEK
from .helpers import (
    admin_user,
    callback,
    callback_pattern,
    command,
    logged_user,
    make_keyboard, valid_user,
)

CANCEL_CALLBACK = "cancel_callback"
APPROVE_CALLBACK = "approve_callback"
SHIFTS_PREVIOUS_CALLBACK = "shifts_previous_callback"
SHIFTS_NEXT_CALLBACK = "shifts_next_callback"
SHIFTS_DATE = "shifts_date"
KIND_CREDENTIALS = "credentials"
PENDING_APPROVAL = "pending_approval"

LOGIN_MESSAGE = (
    "Inserisci il tuo gruppo dei turni ๐ฅ\n\n"
    "Questa informazione mi รจ essenziale per fornirti i turni corretti ๏ธโ"
)
COMMAND_MESSAGE = (
    "๐ *Comandi*: \n\n"
    "/turni - Per visualizzare i tuoi turni ๐\n"
    "/domani - Per visualizzare il turno di domani ๐\n"
    "/notifiche - Per impostare gli avvisi ๐ข\n"
)

logger = logging.getLogger(__name__)


@command
def start_command(update: Update, context: CallbackContext):
    """
    Manage the /start command
    :param update: update
    :param context: context
    """
    update.message.reply_markdown(
        f"๐ Ciao! Io sono *{get_bot_name()}*! Con me potrai capire i tuoi turni di presenza senza dover aprire "
        "ogni volta email, excel o altri strumenti ormai obsoleti ๐ฅ\n\n"
        "Ma prima di iniziare devi effettuare il login, digitando il tuo codice gruppo! ๐",
        reply_markup=make_keyboard(("Login", LOGIN_CALLBACK), context),
    )


# noinspection PyUnusedLocal
@command
def help_command(update: Update, context: CallbackContext):
    """
    Manage the /aiuto command
    :param update: update
    :param context: context
    """
    message = f"๐ท Riepilogo *{get_bot_name()}* \n\n"
    keyboard = None

    group_code = context.user_data.get(USER_GROUP)

    if group_code:
        message += f"Hai effettuato l'accesso con il codice gruppo *{group_code.strip(GROUP_PREFIX)}* ๐"
    else:
        message += (
            "Attualmente non hai ancora fatto l'accesso selezionando il tuo gruppo dei turni."
            "Utilizza il comando /login."
        )
        keyboard = make_keyboard(("Login", LOGIN_CALLBACK), context)

    message += (
            "\n\n" +
            "Di seguito trovi l'elenco dei comandi disponibili ๐ฅ\n\n" +
            COMMAND_MESSAGE +
            "/aiuto - Per visualizzare questo messaggio ๐\n\n"
            "๐ *Problemi?* \n\n"
    )
    if os.getenv("REPOSITORY_URL"):
        message += (
            f"[Contatta]({os.getenv('REPOSITORY_URL')}) gli amministratori di sistema, ti sapranno aiutare nel "
            f"miglior modo possibile ๐ "
        )
    else:
        message += "Contatta gli amministratori di sistema, ti sapranno aiutare nel miglior modo possibile ๐"

    update.message.reply_markdown(
        message,
        reply_markup=keyboard
    )


@command
@valid_user
def login_command(update: Update, context: CallbackContext):
    """
    Manage the /login command
    :param update: update
    :param context: context
    """
    context.user_data[INPUT_KIND] = KIND_CREDENTIALS
    update.message.reply_text(
        LOGIN_MESSAGE,
        reply_markup=get_keyboard_group_markup()
    )


@callback
def login_callback(update: Update, context: CallbackContext):
    """
    Login callback action
    :param update: update
    :param context: context
    """
    context.user_data[INPUT_KIND] = KIND_CREDENTIALS
    update.effective_message.reply_text(
        LOGIN_MESSAGE,
        reply_markup=get_keyboard_group_markup()
    )


def get_keyboard_group_markup():
    """
    Get the keyboard group markup
    :return: ReplyKeyboardMarkup with groups
    """
    return ReplyKeyboardMarkup(
        [[KeyboardButton(text=group.strip(GROUP_PREFIX)) for group in shiftsheduling.shifts_dict]],
        resize_keyboard=True
    )


@valid_user
def credentials_input(update: Update, context: CallbackContext):
    """
    Login input validation
    :param update: update
    :param context: context
    """
    match = re.match(r"[\d]+", update.message.text)
    if not match:
        update.message.reply_markdown(
            "Il codice gruppo inserito non รจ in un formato valido โ?\n"
            "Inserisci il codice gruppo di nuovo! ๐"
        )
        return

    group = GROUP_PREFIX + update.message.text
    if not shiftsheduling.is_valid_group(group):
        update.message.reply_markdown(
            "Il codice gruppo inserito non รจ tra quelli validi โ?\n"
            "Inserisci il codice gruppo corretto! ๐"
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

    update.message.reply_markdown(
        "Gruppo salvato con successo! ๐\n\n" +
        COMMAND_MESSAGE +
        "/aiuto - Per visualizzare la pagina di aiuto ๐",
        reply_markup=ReplyKeyboardRemove()
    )


def user_input(update: Update, context: CallbackContext):
    """
    User input management
    :param update: update
    :param context: context
    """
    input_kinds = [
                      (KIND_CREDENTIALS, credentials_input)
                  ] + notifications.user_input_handlers(shift_reminder)

    for input_kind, input_callback in input_kinds:
        if context.user_data.get(INPUT_KIND) == input_kind:
            input_callback(update, context)

            return


def get_user_group(update: Update, context: CallbackContext):
    """
    Gets the user group.
    If not user group is found, return login callback
    :param update: update
    :param context: context
    :return: founded group, or None in negative case
    """
    shift_user = context.user_data[USER_GROUP]

    if not shift_user:
        message = (
            f"Scusami tanto, ma mi sono dimenticato il tuo gruppo ๐\n"
            "Devi ri effettuare il login per poter utilizzare questo comando"
        )
        keyboard = make_keyboard(("Login", LOGIN_CALLBACK), context)

        if update.callback_query:
            update.callback_query.edit_message_text(
                text=message,
                reply_markup=keyboard
            )
        else:
            update.message.reply_text(
                text=message,
                reply_markup=keyboard
            )

    return shift_user


@command
@valid_user
@logged_user
def shift_command(update: Update, context: CallbackContext):
    """
    Manage /turni command
    :param update: update
    :param context: context
    """
    user_group = get_user_group(update, context)
    if not user_group:
        context.user_data[LOGGED] = False
        context.user_data[USER_GROUP] = None
        return

    if datetime.datetime.today().weekday() < 6:
        base_datetime = datetime.datetime.now()
    else:
        base_datetime = datetime.datetime.now() + datetime.timedelta(days=2)

    context.user_data[SHIFTS_DATE] = base_datetime

    shifts(update, context, context.user_data[SHIFTS_DATE])


@command
@valid_user
@logged_user
def tomorrow_command(update: Update, context: CallbackContext):
    """
    Manage /domani command
    :param update: update
    :param context: context
    """
    user_group = get_user_group(update, context)
    if not user_group:
        context.user_data[LOGGED] = False
        context.user_data[USER_GROUP] = None
        return

    compare_date = datetime.datetime.now() + datetime.timedelta(days=1)

    if compare_date.weekday() == 5:
        compare_date = compare_date + datetime.timedelta(days=2)
        when_text = DAYS_OF_WEEK[0]
    elif compare_date.weekday() == 6:
        compare_date = compare_date + datetime.timedelta(days=1)
        when_text = DAYS_OF_WEEK[0]
    else:
        when_text = "Domani"

    if shiftsheduling.is_smart_working_day(compare_date, context.user_data):
        message = f"{when_text} sarai in {shiftsheduling.ShiftType.SMART_WORKING.formatted}"
    elif shiftsheduling.is_presence_day(compare_date, context.user_data):
        message = f"{when_text} sarai in {shiftsheduling.ShiftType.PRESENCE.formatted}"
    else:
        message = f"Non ci sono turni per {when_text.lower()} ๐ข"

    update.message.reply_text(text=message)


def shifts(update: Update, context: CallbackContext, date: datetime):
    """
    Shifts command text
    :param update: update
    :param context: context
    :param date: compare date
    """
    buttons = [
        ("๏ธโฌ๏ธ Precedente", SHIFTS_PREVIOUS_CALLBACK),
        ("Successivo โก", SHIFTS_NEXT_CALLBACK),
    ]

    message = "Ecco i turni della settimana: \n\n" + shiftsheduling.get_week_shifts_message(date, context.user_data)

    if update.message:
        update.message.reply_text(
            text=message,
            reply_markup=make_keyboard([buttons], context)
        )
    else:
        update.callback_query.edit_message_text(
            text=message,
            reply_markup=make_keyboard([buttons], context)
        )


# noinspection PyUnusedLocal
@callback
def cancel_callback(update: Update, context: CallbackContext):
    """
    Cancel callback
    :param update: update
    :param context: context
    """
    update.callback_query.delete_message()


@callback
def previous_shifts_callback(update: Update, context: CallbackContext):
    """
    Previous shifts' callback.
    Method remove 1 week from last /turni command
    :param update: update
    :param context: context
    """
    context.user_data[SHIFTS_DATE] = context.user_data[SHIFTS_DATE] - datetime.timedelta(weeks=1)

    shifts(update, context, context.user_data[SHIFTS_DATE])


@callback
def next_shifts_callback(update: Update, context: CallbackContext):
    """
    Next shifts' callback
    Method add 1 week from last /turni command
    :param update: update
    :param context: context
    """
    context.user_data[SHIFTS_DATE] = context.user_data[SHIFTS_DATE] + datetime.timedelta(weeks=1)

    shifts(update, context, context.user_data[SHIFTS_DATE])


@command
@admin_user
def message_command(update: Update, context: CallbackContext):
    """
    Manage /message command
    :param update: update
    :param context: context
    """
    message = re.sub("^/messaggio", "", update.message.text).strip()
    if message == "":
        return

    for user_id, _ in context.dispatcher.persistence.get_user_data().items():
        context.bot.send_message(
            chat_id=user_id,
            text=message
        )


def shift_reminder(context) -> None:
    """
    Manage the shift reminder
    :param context: context
    """
    bot = context.job.context[notifications.BOT_TAG]
    user_id = context.job.context[notifications.USER_ID_TAG]
    user_data = context.job.context[notifications.USER_DATA_TAG]
    schedule_data = context.job.context[notifications.SCHEDULE_DATA_TAG]

    user_data[INPUT_KIND] = None

    shift_type = schedule_data[notifications.SHIFT_TYPE]

    # Tomorrow
    compare_date = datetime.datetime.now() + datetime.timedelta(days=1)

    shift_message = None

    if shift_type == shiftsheduling.ShiftType.SMART_WORKING.value:
        send_notify = shiftsheduling.is_smart_working_day(compare_date, user_data)
        shift_message = shiftsheduling.ShiftType.SMART_WORKING.formatted
    elif shift_type == shiftsheduling.ShiftType.PRESENCE.value:
        send_notify = shiftsheduling.is_presence_day(compare_date, user_data)
        shift_message = shiftsheduling.ShiftType.PRESENCE.formatted
    else:
        send_notify = False

    if send_notify:
        shift_user = user_data[USER_GROUP]
        if not shift_user:
            message = f"Hey! Dovrei avvisarti sui turni, ma non ho piรน il tuo gruppo per poter verificare ๐"
            bot.send_message(
                chat_id=user_id,
                text=message,
                reply_markup=make_keyboard(("Login", LOGIN_CALLBACK), user_data=user_data),
            )
            return

        if datetime.datetime.now().weekday() == 5 or datetime.datetime.now() == 6:
            message = f"Hey. Ricordati che {format_date(compare_date)} sarai in {shift_message}"
        else:
            message = f"Hey. Ricordati che domani sarai in {shift_message}"

        bot.send_message(
            chat_id=user_id,
            text=message
        )


@command
def notification_command(update: Update, context: CallbackContext):
    """
    Manage /notifiche command
    :param update: update
    :param context: context
    """
    notifications.main_menu(update, context)


@callback
def register_callback(update: Update, context: CallbackContext):
    """
    Register callback action
    :param update: update
    :param context: context
    """
    context.user_data[REGISTRATION] = True

    message = "Richiesta di registrazione inviata. Riceverai una notifica quando la tua richiesta verrร? approvata"

    if update.message:
        update.message.reply_text(
            text=message,
            reply_markup=ReplyKeyboardRemove()
        )
    else:
        update.callback_query.edit_message_text(text=message)

    if context.bot_data.get(PENDING_APPROVAL) is None:
        context.bot_data[PENDING_APPROVAL] = list()
    context.bot_data[PENDING_APPROVAL].append(update.effective_user.id)

    admins = [int(x.strip()) for x in os.getenv("ADMIN_USERS").split(",")]

    for user_id, _ in context.dispatcher.persistence.get_user_data().items():
        if user_id in admins:
            context.bot.send_message(
                chat_id=user_id,
                parse_mode=ParseMode.MARKDOWN,
                text=(
                    f"L'utente ```{update.effective_user.id}``` ({update.effective_user.full_name}) ha richiesto "
                    f"l'utilizzo di {get_bot_name()}"
                ),
                reply_markup=make_keyboard(("Approva", APPROVE_CALLBACK), user_data=context.user_data)
            )


def approve_callback(update: Update, context: CallbackContext):
    """
    Approve action callback.
    NOTE: This is a special callback because original message is send to another user. DON'T use @callback decorator
    :param update: update
    :param context: context
    """
    if update.effective_message:
        m = re.search("<pre>(.*?)</pre>", update.effective_message.text_html)

        user_id = int(m.group(1))

        if user_id in context.bot_data[PENDING_APPROVAL]:
            context.bot_data[PENDING_APPROVAL].remove(user_id)
            context.bot_data[ENABLED_USERS].add(user_id)
            context.bot.send_message(
                chat_id=user_id,
                text=(
                    f"La tua richiesta รจ stata approvata. Ora potrai utilizzare {get_bot_name()}"
                )
            )
            message = update.effective_message.text_markdown + "\n\nRichiesta approvata"
        else:
            message = update.effective_message.text_markdown + "\n\nLa richiesta รจ giร? stata approvata"

        if update.message:
            update.message.reply_markdown(text=message)
        else:
            update.callback_query.edit_message_text(text=message, parse_mode=ParseMode.MARKDOWN)


def check_admin_users(dispatcher: Dispatcher):
    """
    Add ADMIN_USERS users to valid users
    :param dispatcher: dispatcher
    """
    if dispatcher.bot_data.get(ENABLED_USERS) is None:
        dispatcher.bot_data[ENABLED_USERS] = set()

        admins = [int(x.strip()) for x in os.getenv("ADMIN_USERS").split(",")]
        for user_id in admins:
            dispatcher.bot_data[ENABLED_USERS].add(int(user_id))


def run() -> None:
    """
    Run method.
    Start bot and add all command handler
    """
    data_dir = os.getenv("DATA_DIR") or os.getcwd()
    persistence = PicklePersistence(filename=os.path.join(data_dir, get_database_name()))
    updater = Updater(os.getenv("TELEGRAM_TOKEN"), persistence=persistence)

    dispatcher = updater.dispatcher

    handlers = [
                   CommandHandler("start", start_command),
                   CommandHandler("aiuto", help_command),
                   CommandHandler("login", login_command),
                   CommandHandler("turni", shift_command),
                   CommandHandler("domani", tomorrow_command),
                   CommandHandler("messaggio", message_command),
                   CommandHandler("notifiche", notification_command),
                   CallbackQueryHandler(login_callback, pattern=callback_pattern(LOGIN_CALLBACK)),
                   CallbackQueryHandler(cancel_callback, pattern=callback_pattern(CANCEL_CALLBACK)),
                   CallbackQueryHandler(previous_shifts_callback, pattern=callback_pattern(SHIFTS_PREVIOUS_CALLBACK)),
                   CallbackQueryHandler(next_shifts_callback, pattern=callback_pattern(SHIFTS_NEXT_CALLBACK)),
                   CallbackQueryHandler(register_callback, pattern=callback_pattern(REGISTER_CALLBACK)),
                   CallbackQueryHandler(approve_callback, pattern=callback_pattern(APPROVE_CALLBACK)),
                   MessageHandler(Filters.text & ~Filters.command, user_input),
               ] + notifications.handlers(shift_reminder)

    notifications.setup_scheduler(updater, shift_reminder)

    for handler in handlers:
        dispatcher.add_handler(handler)

    # Load shifts
    shiftsheduling.load_shifts(os.path.join(data_dir, get_shifts_filename()))

    # Check if all admin users is also in valid users set
    check_admin_users(dispatcher)

    updater.start_polling()

    updater.idle()
