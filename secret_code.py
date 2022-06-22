from random import choice
from datetime import datetime, timedelta

# жюри преподаватель админ участник

symbols = '1234567890!@#&*()_+№?*-=[]{}\\/|<>qwertyuiopasdfghjklzxcvbnmQWERTYUIOPASDFGHJKLZXCVBNM'

active_codes = set()
code_to_time_status = {}


def generate_code(status="участник", size=20):
    while True:
        s = ''.join([choice(symbols) for _ in range(size)])
        if s in active_codes:
            if datetime.now() - code_to_time_status[s][0] > timedelta(days=1):
                code_to_time_status[s] = (datetime.now(), status)
                break
        else:
            active_codes.add(s)
            code_to_time_status[s] = (datetime.now(), status)
            break
    return s

def check_code(s):
    if s in active_codes:
        if datetime.now() - code_to_time_status[s][0] < timedelta(days=1):
            active_codes.remove(s)
            status = code_to_time_status[s][1]
            code_to_time_status.pop(s)
            return (True,status)
        else:
            return (False,"К сожалению время действия кода истекло.")
    else:
        return (False,"Ваш код не действителен.")