from aplikasi import (log, secret_key_request, base_url, TZ_JAKARTA)
from aplikasi.others.response import response_service
from aplikasi.others.format import generate_checksum, generate_short_code
from aplikasi.others.utility import is_valid_url
from aplikasi.dao.api.db_dao import insert_short_url, check_short_code_exists
from aplikasi.dao.api.redis_dao import cache_get, cache_set_str
from datetime import datetime, timedelta
import asyncio


async def create_short_url(request):
    data = await request.json()

    v_method        = data.get("method", "")
    v_original_url  = data.get("original_url", "")
    v_custom_code   = data.get("custom_code", None)
    v_expired_days  = data.get("expired_days", "30")
    v_session_key   = data.get("session_key", "")
    v_datetime      = data.get("datetime", "")
    v_checksum      = data.get("checksum", "")

    if not all([v_original_url, v_session_key, v_datetime, v_checksum]):
        return await response_service(request, v_method, 422, 400, "Invalid Request Data")

    if not is_valid_url(v_original_url):
        return await response_service(request, v_method, 422, 400, "Format URL tidak valid")

    v_app_payload   = f"{v_method}#{v_original_url}#{v_datetime}#{secret_key_request}"
    v_app_checksum  = generate_checksum(v_app_payload)

    if v_checksum != v_app_checksum:
        return await response_service(request, v_method, 406, 401, "Invalid Key")

    v_session_data = await cache_get(f"session_key:{v_session_key}")
    if not v_session_data:
        return await response_service(request, v_method, 401, 401, "Session tidak valid atau sudah expired")

    v_user_id = v_session_data.get("user_id", "")

    if v_custom_code:
        v_cek = await asyncio.to_thread(check_short_code_exists, v_custom_code)
        if v_cek["status"] == "T" and v_cek["result"]:
            return await response_service(request, v_method, 409, 409, "Custom code sudah digunakan")
        v_short_code = v_custom_code
    else:
        v_short_code = generate_short_code()
        v_cek = await asyncio.to_thread(check_short_code_exists, v_short_code)
        while v_cek["status"] == "T" and v_cek["result"]:
            v_short_code    = generate_short_code()
            v_cek           = await asyncio.to_thread(check_short_code_exists, v_short_code)

    try:
        v_days          = int(v_expired_days) if v_expired_days else 30
    except ValueError:
        v_days          = 30

    v_expired_at    = (datetime.now(TZ_JAKARTA) + timedelta(days=v_days)).strftime("%Y-%m-%d %H:%M:%S")
    v_hasil         = await asyncio.to_thread(insert_short_url, v_user_id, v_original_url, v_short_code, v_expired_at)

    if v_hasil["status"] == "T" and v_hasil["result"]:
        v_ttl = v_days * 86400
        await cache_set_str(f"redirect:{v_short_code}", v_original_url, ttl=v_ttl)
        v_short_url = f"{base_url}/r/{v_short_code}"
        return await response_service(request, v_method, 200, 200, "Success", {
            "short_code" : v_short_code,
            "short_url"  : v_short_url,
            "expired_at" : v_expired_at,
        })
    else:
        return await response_service(request, v_method, 400, 400, v_hasil["message"])
