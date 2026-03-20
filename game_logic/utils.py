import time


def current_time():
    return time.time()


def calculate_time_taken(start_time):
    return round(time.time() - start_time, 2)
