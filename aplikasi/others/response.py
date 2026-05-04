from aplikasi import (log, secret_key_response, secret_key_header, TZ_JAKARTA)
from aplikasi.others.format import generate_checksum
from aplikasi.others.utility import safe_json
from fastapi import Request
from fastapi.responses import JSONResponse
from datetime import datetime
import json
import aiohttp


async def safe_json_response(resp: aiohttp.ClientResponse):
    try:
        return await resp.json()
    except aiohttp.ContentTypeError:
        text = await resp.text()
        try:
            return json.loads(text)
        except Exception:
            return {
                "err": "invalid_json",
                "content_type": resp.headers.get("Content-Type"),
                "raw": text[:800]
            }


async def response_service(
    request: Request,
    p_method: str,
    p_err_code: str,
    p_http_code: int,
    p_err_msg: str,
    p_param: dict = None
):
    data                = await safe_json(request)
    v_request_datetime  = data.get("datetime", "")

    response = {
        "err_code": p_err_code,
        "err_msg":  p_err_msg,
        **(p_param or {})
    }

    v_datetime_now  = datetime.now(TZ_JAKARTA)
    v_new_datetime  = v_datetime_now.strftime("%Y-%m-%d %H:%M:%S")

    clean_resp = {
        k: v for k, v in response.items()
        if k not in ("datetime", "checksum")
    }
    clean_resp["datetime"] = v_new_datetime

    payload_values      = [
        str(value) for value in clean_resp.values()
        if not isinstance(value, (list, dict))
    ]
    app_resp_payload    = "#".join(payload_values) + "#" + secret_key_response
    v_new_checksum      = generate_checksum(app_resp_payload)

    clean_resp["checksum"] = v_new_checksum

    public_key = request.headers.get("PublicKey", "").strip()
    if public_key:
        payload_sign    = f"{public_key}{secret_key_header}{v_request_datetime}"
        signature_key   = generate_checksum(payload_sign)
        headers         = {"SignatureKey": signature_key}
    else:
        headers = {}

    log.info(f"===== REQUEST ===== : {data} | ===== RESPONSE ===== : {clean_resp}")

    return JSONResponse(content=clean_resp, status_code=200, headers=headers)
