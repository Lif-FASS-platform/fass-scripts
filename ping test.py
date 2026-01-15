from re import findall
import time

import requests


def ping(address, ping_count):
    log = []
    while True:
        res = requests.get(
            "https://www.fass.se/LIF/startpage", timeout=5
        ).elapsed.total_seconds()
        log.append(res)
        print(res)


ping("https://www.fass.se/LIF/startpage", 3)
