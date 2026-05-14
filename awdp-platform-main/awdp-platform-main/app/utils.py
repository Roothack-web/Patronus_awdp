"""Shared utility functions for AWDP platform."""

import random
import string
from datetime import datetime, timedelta


def generate_flag():
    """Generate a random CTF flag with format: flag{awdp_<random>_<timestamp>}"""
    rand = ''.join(random.choices(string.ascii_lowercase + string.digits, k=12))
    ts = int(datetime.utcnow().timestamp())
    return f"flag{{awdp_{rand}_{ts}}}"


def flag_expiry_delta():
    """Return configured flag expiry timedelta (safe outside app context)."""
    try:
        from flask import current_app
        return timedelta(minutes=current_app.config.get('FLAG_EXPIRY_MINUTES', 5))
    except Exception:
        return timedelta(minutes=5)
