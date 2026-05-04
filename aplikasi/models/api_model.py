from typing import Optional
from pydantic import BaseModel

inquiry_examples = {
    "create_short_url": {
        "summary": "Buat short URL baru",
        "value": {
            "method": "create_short_url",
            "original_url": "https://www.example.com/artikel/sangat-panjang-sekali",
            "custom_code": "artikel1",
            "expired_days": "30",
            "session_key": "sess_xxx",
            "datetime": "2025-07-29 12:00:00",
            "checksum": "abc123"
        }
    },
    "get_url_detail": {
        "summary": "Detail short URL",
        "value": {
            "method": "get_url_detail",
            "short_code": "abc123",
            "session_key": "sess_xxx",
            "datetime": "2025-07-29 12:00:00",
            "checksum": "abc456"
        }
    },
    "get_url_list": {
        "summary": "Daftar semua short URL milik user",
        "value": {
            "method": "get_url_list",
            "session_key": "sess_xxx",
            "datetime": "2025-07-29 12:00:00",
            "checksum": "abc789"
        }
    },
    "delete_url": {
        "summary": "Hapus short URL",
        "value": {
            "method": "delete_url",
            "short_code": "abc123",
            "session_key": "sess_xxx",
            "datetime": "2025-07-29 12:00:00",
            "checksum": "def123"
        }
    },
    "get_url_stats": {
        "summary": "Statistik klik per short URL",
        "value": {
            "method": "get_url_stats",
            "short_code": "abc123",
            "session_key": "sess_xxx",
            "datetime": "2025-07-29 12:00:00",
            "checksum": "def456"
        }
    },
    "get_top_url": {
        "summary": "Top URL berdasarkan jumlah klik",
        "value": {
            "method": "get_top_url",
            "limit": "10",
            "session_key": "sess_xxx",
            "datetime": "2025-07-29 12:00:00",
            "checksum": "ghi123"
        }
    },
}


class CreateShortUrlRequest(BaseModel):
    method: str
    original_url: str
    custom_code: Optional[str] = None
    expired_days: Optional[str] = None
    session_key: str
    datetime: str
    checksum: str


class GetUrlDetailRequest(BaseModel):
    method: str
    short_code: str
    session_key: str
    datetime: str
    checksum: str


class GetUrlListRequest(BaseModel):
    method: str
    session_key: str
    datetime: str
    checksum: str


class DeleteUrlRequest(BaseModel):
    method: str
    short_code: str
    session_key: str
    datetime: str
    checksum: str


class GetUrlStatsRequest(BaseModel):
    method: str
    short_code: str
    session_key: str
    datetime: str
    checksum: str


class GetTopUrlRequest(BaseModel):
    method: str
    limit: Optional[str] = "10"
    session_key: str
    datetime: str
    checksum: str
