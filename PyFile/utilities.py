
import datetime


def get_formatted_datetime():
    return str(datetime.datetime.now()).replace('-', '').replace(' ', '_').replace(':', '').replace('.', '')