"""
Helper module
"""

import logging
import re
import uuid
from typing import Union

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext

from .constants import *

CALLBACK_SESSION = "callback_session"

logger = logging.getLogger(__name__)


def make_keyboard(buttons: Union[list, tuple], context: CallbackContext = None, user_data: dict = None):
    """
    Create inline keyboard markup
    :param buttons: buttons to add (Supported type are List of Tuple)
    :param context: context
    :param user_data: user_data
    :return: inline keyboard markup
    """
    keyboard = []

    session = str(uuid.uuid4())
    if context:
        context.user_data[CALLBACK_SESSION] = session
    else:
        user_data[CALLBACK_SESSION] = session

    if isinstance(buttons, list):
        for row in buttons:
            keyboard.append(
                [
                    InlineKeyboardButton(
                        text=button[0],
                        callback_data=f"{button[1]}#{session}"
                    )
                    for button in row
                ]
            )
    elif isinstance(buttons, tuple):
        keyboard = [
            [
                InlineKeyboardButton(
                    text=buttons[0],
                    callback_data=f"{buttons[1]}#{session}"
                )
            ]
        ]
    else:
        raise Exception("Invalid buttons type")

    return InlineKeyboardMarkup(keyboard)


def logged_user(func):
    """
    Logged user checks
    :param func: func
    :return: wrapper
    """

    def wrapper(*args, **kwargs):
        """
        Effective checks
        :param args: args
        :param kwargs: kwargs
        """
        update, context = args[0], args[1]

        if context.user_data.get(LOGGED):
            func(*args, **kwargs)
        else:
            message = "Devi prima comunicare il tuo gruppo per utilizzare questo comando! ⛔"
            keyboard = make_keyboard(("Login", LOGIN_CALLBACK), context)
            if update.callback_query:
                update.callback_query.answer()
                update.callback_query.edit_message_text(
                    text=message,
                    reply_markup=keyboard
                )
            else:
                update.message.reply_text(
                    text=message,
                    reply_markup=keyboard
                )

    return wrapper


def valid_user(func):
    """
    Valid user checks
    :param func: func
    :return: wrapper
    """

    def wrapper(*args, **kwargs):
        """
        Effective checks
        :param args: args
        :param kwargs: kwargs
        """
        update, context = args[0], args[1]

        users = os.getenv("USERS")

        if not users:
            return

        if not "\"" + str(update.message.from_user.id) + "\"" in users:
            logger.warning(
                "User %s (%s) try to use a restricted command",
                update.effective_user.id,
                update.effective_user.full_name,
            )

            message = ("Il tuo utente non risulta abilitato all'utilizzo di questo comando\n\n"
                       f"Se devi effettivamente utilizzare {get_bot_name()} contatta gli amministratori di sistema")

            if update.callback_query:
                update.callback_query.answer()
                update.callback_query.edit_message_text(text=message)
            else:
                update.message.reply_text(text=message)

            return

        func(*args, **kwargs)

    return wrapper


def admin_user(func):
    """
    Admin user checks
    :param func: func
    :return: wrapper
    """

    def wrapper(*args, **kwargs):
        """
        Effective checks
        :param args: args
        :param kwargs: kwargs
        """
        update = args[0]

        admins = os.getenv("ADMIN_USERS")
        if not admins:
            return

        if not "\"" + str(update.message.from_user.id) + "\"" in admins:
            logger.warning(
                "User %s (%s) try to use an admin command",
                update.effective_user.id,
                update.effective_user.full_name,
            )
            return

        func(*args, **kwargs)

    return wrapper


def callback(func):
    """
    Callback preliminary checks
    :param func: func
    :return: wrapper
    """

    def wrapper(*args, **kwargs):
        """
        Effective checks
        :param args: args
        :param kwargs: kwargs
        """
        update, context = args[0], args[1]

        if not update.callback_query:
            func(*args, **kwargs)
            return

        update.callback_query.answer()

        match = re.match(r"^([\w]+)#([\w-]+)$", update.callback_query.data)
        if not match:
            update.callback_query.delete_message()
            return

        if match[2] != context.user_data.get(CALLBACK_SESSION):
            update.callback_query.delete_message()
            return

        func(*args, **kwargs)

    return wrapper


def command(func):
    """
    Command preliminary checks
    :param func: func
    :return: wrapper
    """

    def wrapper(*args, **kwargs):
        """
        Effective checks
        :param args: args
        :param kwargs: kwargs
        """
        context = args[1]

        context.user_data[INPUT_KIND] = None

        func(*args, **kwargs)

    return wrapper


def callback_pattern(key):
    """
    Callback pattern
    :param key: key to use
    :return: callback pattern
    """
    return "^" + key + "#[\\w-]+$"
