from aplikasi import (log, secret_key_request, base_url)
from aplikasi.others.response import response_service
from aplikasi.others.format import generate_checksum
from aplikasi.dao.api.redis_dao import cache_get, cache_set_str, cache_get_str
from aplikasi.dao.api.db_dao import get_url_by_code
import qrcode
import io
import base64
import asyncio


async def generate_qr_url(request):
    data = await request.json()

    v_method        = data.get("method", "")
    v_short_code    = data.get("short_code", "")
    v_session_key   = data.get("session_key", "")
    v_datetime      = data.get("datetime", "")
    v_checksum      = data.get("checksum", "")

    if not all([v_short_code, v_session_key, v_datetime, v_checksum]):
        return await response_service(request, v_method, 422, 400, "Invalid Request Data")

    v_app_payload   = f"{v_method}#{v_short_code}#{v_datetime}#{secret_key_request}"
    v_app_checksum  = generate_checksum(v_app_payload)
    if v_checksum != v_app_checksum:
        return await response_service(request, v_method, 406, 401, "Invalid Key")

    v_session_data = await cache_get(f"session_key:{v_session_key}")
    if not v_session_data:
        return await response_service(request, v_method, 401, 401, "Session tidak valid atau sudah expired")

    v_cached_qr = await cache_get_str(f"url:qr:{v_short_code}")
    if v_cached_qr:
        return await response_service(request, v_method, 200, 200, "Success", {
            "short_code" : v_short_code,
            "short_url"  : f"{base_url}/r/{v_short_code}",
            "qr_base64"  : v_cached_qr,
        })

    v_hasil = await asyncio.to_thread(get_url_by_code, v_short_code)
    if not (v_hasil["status"] == "T" and v_hasil["result"]):
        return await response_service(request, v_method, 404, 404, "Short URL tidak ditemukan")

    v_data = v_hasil["result"][0]
    if not v_data["is_active"]:
        return await response_service(request, v_method, 400, 400, "Short URL sudah tidak aktif")

    v_short_url     = f"{base_url}/r/{v_short_code}"
    v_qr            = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=10, border=4)
    v_qr.add_data(v_short_url)
    v_qr.make(fit=True)

    v_img           = v_qr.make_image(fill_color="black", back_color="white")
    v_buffer        = io.BytesIO()
    v_img.save(v_buffer, format="PNG")
    v_qr_base64     = base64.b64encode(v_buffer.getvalue()).decode("utf-8")

    await cache_set_str(f"url:qr:{v_short_code}", v_qr_base64, ttl=86400)

    return await response_service(request, v_method, 200, 200, "Success", {
        "short_code" : v_short_code,
        "short_url"  : v_short_url,
        "qr_base64"  : v_qr_base64,
    })
