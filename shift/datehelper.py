"""This module contains date helper methods"""

import datetime

DAYS_OF_WEEK = {
    0: "Lunedì",
    1: "Martedì",
    2: "Mercoledì",
    3: "Giovedì",
    4: "Venerdì",
    5: "Sabato",
    6: "Domenica",
}


def format_date(date: datetime):
    """
    Format date method in YYYY-MM-DD format (E.g. 2022-01-30)
    :param date: date
    :return: formatted date in YYYY-MM-DD format
    """
    date_string = date.strftime("%Y-%m-%d")

    return f"{DAYS_OF_WEEK[date.weekday()]} {date_string}"
