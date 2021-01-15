import datetime


def get_current_time_str():
    return datetime.datetime.now().strftime('[%d.%m.%y %H:%M:%S]')


def handle_text(text):
    return '{} {}\n'.format(get_current_time_str(), text)
