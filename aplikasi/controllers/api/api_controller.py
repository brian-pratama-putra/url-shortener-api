from aplikasi import (log, router)
from fastapi import Request, Depends, Body
from fastapi.responses import RedirectResponse
from fastapi_limiter.depends import RateLimiter
from aplikasi.others.response import response_service
from aplikasi.others.utility import safe_json, validate_request_datetime
from aplikasi.dao.api.db_dao import get_url_by_code, increment_click_count, insert_click_log
from aplikasi.dao.api.redis_dao import cache_get_str
from typing import Union
import asyncio
import traceback

from aplikasi.controllers.api.create_short_url_controller import create_short_url
from aplikasi.controllers.api.get_url_detail_controller import get_url_detail_controller
from aplikasi.controllers.api.get_url_list_controller import get_url_list_controller
from aplikasi.controllers.api.delete_url_controller import delete_url_controller
from aplikasi.controllers.api.get_url_stats_controller import get_url_stats_controller
from aplikasi.controllers.api.get_top_url_controller import get_top_url_controller
from aplikasi.controllers.api.generate_qr_url_controller import generate_qr_url

from aplikasi.models.api_model import (
    CreateShortUrlRequest,
    GetUrlDetailRequest,
    GetUrlListRequest,
    DeleteUrlRequest,
    GetUrlStatsRequest,
    GetTopUrlRequest,
    GenerateQrUrlRequest,
)

InquiryRequestUnion = Union[
    CreateShortUrlRequest,
    GetUrlDetailRequest,
    GetUrlListRequest,
    DeleteUrlRequest,
    GetUrlStatsRequest,
    GetTopUrlRequest,
    GenerateQrUrlRequest,
]


@router.post("/inquiry-docs", response_model=None, summary="Dokumentasi Skema /inquiry", tags=["Inquiry"])
async def inquiry_docs(body: InquiryRequestUnion = Body(...)):
    return {"message": "Hanya untuk dokumentasi schema"}


@router.post("/inquiry", dependencies=[Depends(RateLimiter(times=50, seconds=60))], include_in_schema=False)
async def inquiry(request: Request):
    try:
        data_request    = await safe_json(request)
        v_method        = data_request.get("method", "")
        v_datetime      = data_request.get("datetime", "")

        v_is_valid, v_msg = validate_request_datetime(v_datetime)
        if not v_is_valid:
            return await response_service(request, v_method, 405, 405, v_msg)

        if v_method == "create_short_url":
            return await create_short_url(request)
        elif v_method == "get_url_detail":
            return await get_url_detail_controller(request)
        elif v_method == "get_url_list":
            return await get_url_list_controller(request)
        elif v_method == "delete_url":
            return await delete_url_controller(request)
        elif v_method == "get_url_stats":
            return await get_url_stats_controller(request)
        elif v_method == "get_top_url":
            return await get_top_url_controller(request)
        elif v_method == "generate_qr_url":
            return await generate_qr_url(request)
        else:
            return await response_service(request, v_method, 405, 405, "Invalid Method")

    except Exception as e:
        log.error(f"===== ERROR INQUIRY ===== : {e}")
        traceback.print_exc()
        return await response_service(request, v_method, 405, 401, "Internal Server Error")


@router.get("/r/{short_code}", tags=["Redirect"])
async def redirect_url(short_code: str, request: Request):
    try:
        v_original_url = await cache_get_str(f"redirect:{short_code}")

        if not v_original_url:
            v_hasil = await asyncio.to_thread(get_url_by_code, short_code)

            if not (v_hasil["status"] == "T" and v_hasil["result"]):
                return RedirectResponse(url="/not-found", status_code=302)

            v_data          = v_hasil["result"][0]
            v_original_url  = v_data["original_url"]

            if not v_data["is_active"]:
                return RedirectResponse(url="/not-found", status_code=302)

        x_forwarded_for = request.headers.get("x-forwarded-for")
        v_ip_address    = x_forwarded_for.split(",")[0] if x_forwarded_for else request.client.host
        v_user_agent    = request.headers.get("user-agent", "")[:500]
        v_referer       = request.headers.get("referer", "")[:500]

        asyncio.create_task(asyncio.to_thread(increment_click_count, short_code))
        asyncio.create_task(asyncio.to_thread(insert_click_log, short_code, v_ip_address, v_user_agent, v_referer))

        return RedirectResponse(url=v_original_url, status_code=302)

    except Exception as e:
        log.error(f"===== ERROR REDIRECT ===== : {e}")
        return RedirectResponse(url="/not-found", status_code=302)


@router.get("/not-found", include_in_schema=False)
async def not_found_page():
    return {"err_code": 404, "err_msg": "Short URL tidak ditemukan atau sudah tidak aktif"}


@router.get("/health", include_in_schema=False)
async def health():
    return {"status": "running"}


@router.get("/")
async def root():
    return {"status": "running"}
