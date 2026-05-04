from aplikasi import TZ_JAKARTA
from fastapi import Request
import datetime
import re


def get_ttl_until_midnight_jakarta():
    v_now       = datetime.datetime.now(TZ_JAKARTA)
    v_midnight  = (v_now + datetime.timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    return int((v_midnight - v_now).total_seconds())


async def safe_json(request: Request):
    if request.method in ["POST", "PUT", "PATCH"]:
        try:
            return await request.json()
        except:
            return {}
    return {}


def validate_request_datetime(v_datetime: str):
    from zoneinfo import ZoneInfo
    JAKARTA_TZ = ZoneInfo("Asia/Jakarta")

    try:
        v_request_dt = datetime.datetime.strptime(v_datetime, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return False, "Format datetime tidak valid. Gunakan YYYY-MM-DD HH:MM:SS"

    v_request_dt    = v_request_dt.replace(tzinfo=JAKARTA_TZ)
    v_now_jakarta   = datetime.datetime.now(JAKARTA_TZ)
    v_24_hour       = datetime.timedelta(hours=24)

    if not (v_now_jakarta - v_24_hour <= v_request_dt <= v_now_jakarta + v_24_hour):
        return False, "Datetime request harus dalam rentang ±24 jam dari waktu sekarang"

    return True, "OK"


def is_valid_url(p_url: str) -> bool:
    v_pattern = re.compile(
        r'^(https?://)'
        r'([a-zA-Z0-9\-\.]+)'
        r'(\.[a-zA-Z]{2,})'
        r'(:\d+)?'
        r'(/[^\s]*)?$'
    )
    return bool(v_pattern.match(p_url))
