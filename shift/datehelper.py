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
    date_string = date.strftime("%Y-%m-%d")

    return f"{DAYS_OF_WEEK[date.weekday()]} {date_string}"
