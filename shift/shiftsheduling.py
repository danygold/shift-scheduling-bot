"""
Shift scheduling module
"""

import datetime
import json
from enum import Enum

from .constants import USER_GROUP
from .datehelper import DAYS_OF_WEEK

shifts_dict = dict()


class ShiftType(Enum):
    """
    Shift type
    """
    SMART_WORKING = 0, "Smart working", "🏠"
    PRESENCE = 1, "Ufficio", "💼"

    def __new__(cls, *args, **kwds):
        """
        Redefine __new__ method
        :param args: args
        :param kwds: kwds
        """
        obj = object.__new__(cls)
        obj._value_ = args[0]
        return obj

    def __init__(self, _: str, description: str = None, emoji: str = None):
        """
        Redefine __init__ method. Ignore first parameter because is already set in _value_ in __new__ method
        :param _: ignored param
        :param description: description
        :param emoji: emoji
        """
        self._description_ = description
        self._emoji_ = emoji

    def __str__(self):
        """
        Redefine __str__ method
        :return: value
        """
        return self.value

    @property
    def description(self):
        """
        Description
        :return: description
        """
        return self._description_

    @property
    def emoji(self):
        """
        Emoji
        :return: emoji
        """
        return self._emoji_

    @property
    def formatted(self):
        """
        Formatted text (description + emoji)
        :return: formatted text
        """
        return self._description_ + " " + self._emoji_


def load_shifts(file):
    """
    Load shifts json file
    :param file: file
    """
    with open(file) as f:
        loaded_json = json.load(f)

        for group in loaded_json["groups"]:
            shifts_dict[group["name"]] = dict()
            for shift in group["shifts"]:
                shifts_dict[group["name"]][shift["date"]] = shift["presence"]


def is_valid_group(group):
    """
    Return if group is valid or not
    :param group: group to validate
    :return: True if group is valid, False otherwise
    """
    return group in shifts_dict


def get_decoded_description(presence: bool):
    """
    Decode shifts description
    :param presence: presence
    :return: decoded description
    """
    if presence:
        return ShiftType.PRESENCE.formatted
    else:
        return ShiftType.SMART_WORKING.formatted


def get_week_shifts_message(date: datetime, user_data: dict):
    """
    Get the week shifts message
    :param date: date
    :param user_data: user date
    :return: the week shifts message
    """
    message = ""

    for date in get_working_date_of_week(date):
        date_string = date.strftime("%Y-%m-%d")
        message = message + f"{DAYS_OF_WEEK[date.weekday()]} {date_string} - "
        try:
            message = message + f"{get_decoded_description(shifts_dict[user_data[USER_GROUP]][date_string])} \n"
        except KeyError:
            message = message + "Nessun turno 😢\n"

    return message


def is_presence_day(date: datetime, user_data: dict):
    """
    Return if the given date is a presence day or not
    :param date: date
    :param user_data: user data
    :return: True if date is a presence day, False otherwise
    """
    try:
        date_string = date.strftime("%Y-%m-%d")
        return shifts_dict[user_data[USER_GROUP]][date_string] is True
    except KeyError:
        return False


def is_smart_working_day(date: datetime, user_data: dict):
    """
    Return if the given date is a smart working day or not
    :param date: date
    :param user_data: user data
    :return: True if date is a smart working day, False otherwise
    """
    try:
        date_string = date.strftime("%Y-%m-%d")
        return shifts_dict[user_data[USER_GROUP]][date_string] is False
    except KeyError:
        return False


def get_working_date_of_week(date: datetime):
    """
    Get the working dats of week.
    Working day are:
    - Monday
    - Tuesday
    - Wednesday
    - Thursday
    - Friday
    :param date: date
    :return: working date
    """
    return [date + datetime.timedelta(days=i) for i in range(0 - date.weekday(), 5 - date.weekday())]
