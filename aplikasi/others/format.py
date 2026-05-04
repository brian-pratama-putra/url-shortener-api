import hashlib
import random
import string


def generate_checksum(payload):
    return hashlib.sha256(payload.encode()).hexdigest()


def generate_short_code(p_length=7):
    v_chars = string.ascii_letters + string.digits
    return ''.join(random.choices(v_chars, k=p_length))
