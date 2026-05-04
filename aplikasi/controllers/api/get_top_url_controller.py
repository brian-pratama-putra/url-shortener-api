from aplikasi import (log, secret_key_request)
from aplikasi.others.response import response_service
from aplikasi.others.format import generate_checksum
from aplikasi.dao.api.db_dao import get_top_url
from aplikasi.dao.api.redis_dao import cache_get


async def get_top_url_controller(request):
    data = await request.json()

    v_method        = data.get("method", "")
    v_limit         = data.get("limit", "10")
    v_session_key   = data.get("session_key", "")
    v_datetime      = data.get("datetime", "")
    v_checksum      = data.get("checksum", "")

    if not all([v_session_key, v_datetime, v_checksum]):
        return await response_service(request, v_method, 422, 400, "Invalid Request Data")

    v_app_payload   = f"{v_method}#{v_datetime}#{secret_key_request}"
    v_app_checksum  = generate_checksum(v_app_payload)

    if v_checksum != v_app_checksum:
        return await response_service(request, v_method, 406, 401, "Invalid Key")

    v_session_data = await cache_get(f"session_key:{v_session_key}")
    if not v_session_data:
        return await response_service(request, v_method, 401, 401, "Session tidak valid atau sudah expired")

    try:
        v_limit_int = int(v_limit)
        if v_limit_int < 1 or v_limit_int > 100:
            v_limit_int = 10
    except ValueError:
        v_limit_int = 10

    v_user_id   = v_session_data.get("user_id", "")
    v_hasil     = await get_top_url(v_user_id, v_limit_int)

    if v_hasil["status"] == "T":
        return await response_service(request, v_method, 200, 200, "Success", {"data": v_hasil["result"]})
    else:
        return await response_service(request, v_method, 400, 400, v_hasil["message"])
