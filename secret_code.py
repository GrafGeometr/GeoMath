from random import choice
from datetime import datetime, timedelta

# жюри преподаватель администратор участник

symbols = '1234567890!@#&*()_+№?*-=[]{}\\/|<>qwertyuiopasdfghjklzxcvbnmQWERTYUIOPASDFGHJKLZXCVBNM'


def generate_code(status="участник", size=20):
    s = ''.join([choice(symbols) for _ in range(size)])
    return s