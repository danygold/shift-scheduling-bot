import json
import datetime

from .constants import USER_GROUP

DAYS_OF_WEEK = {
    0: "Lunedì",
    1: "Martedì",
    2: "Mercoledì",
    3: "Giovedì",
    4: "Venerdì",
    5: "Sabato",
    6: "Domenica",
}

shifts_dict = dict()


def load_shifts(file):
    f = open(file)

    loaded_json = json.load(f)

    for group in loaded_json["groups"]:
        shifts_dict[group["name"]] = dict()
        for shift in group["shifts"]:
            shifts_dict[group["name"]][shift["date"]] = shift["presence"]

    f.close()


def is_valid_group(group):
    return group in shifts_dict


def get_group():
    return shifts_dict


def get_decoded_description(presence: bool):
    if presence:
        return "Ufficio"
    else:
        return "Smart working"


def get_current_week_message(date: datetime, user_data: dict):
    message = ""

    for date in get_working_date_of_week(date):
        date_string = date.strftime("%Y-%m-%d")
        message = message + f"{DAYS_OF_WEEK[date.weekday()]} {date_string} - "
        try:
            message = message + f"{get_decoded_description(shifts_dict[user_data[USER_GROUP]][date_string])} \n"
        except:
            message = message + "Nessun turno \n"

    return message


def is_presence_day(date: datetime, user_data: dict):
    try:
        date_string = date.strftime("%Y-%m-%d")
        return shifts_dict[user_data[USER_GROUP]][date_string] is True
    except:
        return False


def is_smart_working_day(date: datetime, user_data: dict):
    try:
        date_string = date.strftime("%Y-%m-%d")
        return shifts_dict[user_data[USER_GROUP]][date_string] is False
    except:
        return False


def get_working_date_of_week(date: datetime):
    return [date + datetime.timedelta(days=i) for i in range(0 - date.weekday(), 5 - date.weekday())]
