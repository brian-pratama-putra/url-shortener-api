from aplikasi.dao.query_file import CreateConnectionDb, QueryStringDb, response_json
from aplikasi.dao.api.redis_dao import cache_get, cache_set, cache_delete, cache_incr, cache_get_str, cache_set_str
from aplikasi.others.utility import get_ttl_until_midnight_jakarta


def get_url_by_code(p_short_code):
    try:
        with CreateConnectionDb({"read": True, "write": False}) as v_connection_db:
            v_query_string_db   = QueryStringDb(v_connection_db)
            v_query             = """
                                    SELECT
                                        short_code,
                                        original_url,
                                        to_char(expired_at, 'YYYY-MM-DD HH24:MI:SS') expired_at,
                                        is_active
                                    FROM short_urls
                                    WHERE short_code = %(short_code)s
                                    AND is_deleted = false
                                """
            v_kondisi           = {"short_code": p_short_code}
            return v_query_string_db.select(v_query, v_kondisi)
    except Exception as e:
        return response_json(400, "F", str(e), [])


def insert_short_url(p_user_id, p_original_url, p_short_code, p_expired_at):
    try:
        with CreateConnectionDb({"read": False, "write": True}) as v_connection_db:
            v_query_string_db   = QueryStringDb(v_connection_db)
            v_query             = """
                                    INSERT INTO short_urls
                                    (user_id, original_url, short_code, expired_at, created_at)
                                    VALUES(%(user_id)s, %(original_url)s, %(short_code)s,
                                    %(expired_at)s, CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Jakarta')
                                    RETURNING short_code
                                """
            v_kondisi           = {
                                    "user_id"       : p_user_id,
                                    "original_url"  : p_original_url,
                                    "short_code"    : p_short_code,
                                    "expired_at"    : p_expired_at,
                                }
            return v_query_string_db.select(v_query, v_kondisi)
    except Exception as e:
        return response_json(400, "F", str(e), [])


def check_short_code_exists(p_short_code):
    try:
        with CreateConnectionDb({"read": True, "write": False}) as v_connection_db:
            v_query_string_db   = QueryStringDb(v_connection_db)
            v_query             = """
                                    SELECT short_code
                                    FROM short_urls
                                    WHERE short_code = %(short_code)s
                                    AND is_deleted = false
                                """
            v_kondisi           = {"short_code": p_short_code}
            return v_query_string_db.select(v_query, v_kondisi)
    except Exception as e:
        return response_json(400, "F", str(e), [])


async def get_url_detail(p_short_code, p_user_id):
    v_cache_key     = f"url:detail:{p_short_code}"
    cached_result   = await cache_get(v_cache_key)
    if cached_result:
        return response_json(200, "T", "Success", cached_result)

    try:
        with CreateConnectionDb({"read": True, "write": False}) as v_connection_db:
            v_query_string_db   = QueryStringDb(v_connection_db)
            v_query             = """
                                    SELECT
                                        s.short_code,
                                        s.original_url,
                                        s.is_active,
                                        COALESCE(s.click_count, 0)::varchar click_count,
                                        to_char(s.expired_at, 'YYYY-MM-DD HH24:MI:SS') expired_at,
                                        to_char(s.created_at, 'YYYY-MM-DD HH24:MI:SS') created_at
                                    FROM short_urls s
                                    WHERE s.short_code = %(short_code)s
                                    AND s.user_id = %(user_id)s
                                    AND s.is_deleted = false
                                """
            v_kondisi           = {
                                    "short_code" : p_short_code,
                                    "user_id"    : p_user_id,
                                }
            v_hasil             = v_query_string_db.select(v_query, v_kondisi)
            if v_hasil["status"] == "T" and v_hasil["result"]:
                await cache_set(v_cache_key, v_hasil["result"][0], ttl=300)
            return v_hasil
    except Exception as e:
        return response_json(400, "F", str(e), [])


async def get_url_list(p_user_id):
    v_cache_key     = f"url:list:{p_user_id}"
    cached_result   = await cache_get(v_cache_key)
    if cached_result:
        return response_json(200, "T", "Success", cached_result)

    try:
        with CreateConnectionDb({"read": True, "write": False}) as v_connection_db:
            v_query_string_db   = QueryStringDb(v_connection_db)
            v_query             = """
                                    SELECT
                                        short_code,
                                        original_url,
                                        is_active,
                                        COALESCE(click_count, 0)::varchar click_count,
                                        to_char(expired_at, 'YYYY-MM-DD HH24:MI:SS') expired_at,
                                        to_char(created_at, 'YYYY-MM-DD HH24:MI:SS') created_at
                                    FROM short_urls
                                    WHERE user_id = %(user_id)s
                                    AND is_deleted = false
                                    ORDER BY created_at DESC
                                """
            v_kondisi           = {"user_id": p_user_id}
            v_hasil             = v_query_string_db.select(v_query, v_kondisi)
            if v_hasil["status"] == "T" and v_hasil["result"]:
                await cache_set(v_cache_key, v_hasil["result"], ttl=120)
            return v_hasil
    except Exception as e:
        return response_json(400, "F", str(e), [])


def delete_url(p_short_code, p_user_id):
    try:
        with CreateConnectionDb({"read": False, "write": True}) as v_connection_db:
            v_query_string_db   = QueryStringDb(v_connection_db)
            v_query             = """
                                    UPDATE short_urls
                                    SET is_deleted = true
                                    WHERE short_code = %(short_code)s
                                    AND user_id = %(user_id)s
                                    AND is_deleted = false
                                """
            v_kondisi           = {
                                    "short_code" : p_short_code,
                                    "user_id"    : p_user_id,
                                }
            return v_query_string_db.execute(v_query, v_kondisi)
    except Exception as e:
        return response_json(400, "F", str(e), None)


def increment_click_count(p_short_code):
    try:
        with CreateConnectionDb({"read": False, "write": True}) as v_connection_db:
            v_query_string_db   = QueryStringDb(v_connection_db)
            v_query             = """
                                    UPDATE short_urls
                                    SET click_count = COALESCE(click_count, 0) + 1
                                    WHERE short_code = %(short_code)s
                                    AND is_deleted = false
                                """
            v_kondisi           = {"short_code": p_short_code}
            return v_query_string_db.execute(v_query, v_kondisi)
    except Exception as e:
        return response_json(400, "F", str(e), None)


def insert_click_log(p_short_code, p_ip_address, p_user_agent, p_referer):
    try:
        with CreateConnectionDb({"read": False, "write": True}) as v_connection_db:
            v_query_string_db   = QueryStringDb(v_connection_db)
            v_query             = """
                                    INSERT INTO click_logs
                                    (short_code, ip_address, user_agent, referer, clicked_at)
                                    VALUES(%(short_code)s, %(ip_address)s, %(user_agent)s, %(referer)s,
                                    CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Jakarta')
                                """
            v_kondisi           = {
                                    "short_code"  : p_short_code,
                                    "ip_address"  : p_ip_address,
                                    "user_agent"  : p_user_agent,
                                    "referer"     : p_referer,
                                }
            return v_query_string_db.execute(v_query, v_kondisi)
    except Exception as e:
        return response_json(400, "F", str(e), None)


async def get_url_stats(p_short_code, p_user_id):
    v_cache_key     = f"url:stats:{p_short_code}"
    cached_result   = await cache_get(v_cache_key)
    if cached_result:
        return response_json(200, "T", "Success", cached_result)

    try:
        with CreateConnectionDb({"read": True, "write": False}) as v_connection_db:
            v_query_string_db   = QueryStringDb(v_connection_db)
            v_query             = """
                                    SELECT
                                        s.short_code,
                                        s.original_url,
                                        COALESCE(s.click_count, 0)::varchar total_click,
                                        COUNT(CASE WHEN cl.clicked_at::date = CURRENT_DATE THEN 1 END)::varchar click_today,
                                        COUNT(CASE WHEN cl.clicked_at >= (CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Jakarta') - INTERVAL '7 days' THEN 1 END)::varchar click_7_days,
                                        to_char(s.expired_at, 'YYYY-MM-DD HH24:MI:SS') expired_at,
                                        to_char(s.created_at, 'YYYY-MM-DD HH24:MI:SS') created_at
                                    FROM short_urls s
                                    LEFT JOIN click_logs cl ON cl.short_code = s.short_code
                                    WHERE s.short_code = %(short_code)s
                                    AND s.user_id = %(user_id)s
                                    AND s.is_deleted = false
                                    GROUP BY s.short_code, s.original_url, s.click_count, s.expired_at, s.created_at
                                """
            v_kondisi           = {
                                    "short_code" : p_short_code,
                                    "user_id"    : p_user_id,
                                }
            v_hasil             = v_query_string_db.select(v_query, v_kondisi)
            if v_hasil["status"] == "T" and v_hasil["result"]:
                await cache_set(v_cache_key, v_hasil["result"][0], ttl=60)
            return v_hasil
    except Exception as e:
        return response_json(400, "F", str(e), [])


async def get_top_url(p_user_id, p_limit):
    v_cache_key     = f"url:top:{p_user_id}:{p_limit}"
    cached_result   = await cache_get(v_cache_key)
    if cached_result:
        return response_json(200, "T", "Success", cached_result)

    try:
        with CreateConnectionDb({"read": True, "write": False}) as v_connection_db:
            v_query_string_db   = QueryStringDb(v_connection_db)
            v_query             = """
                                    SELECT
                                        short_code,
                                        original_url,
                                        COALESCE(click_count, 0)::varchar click_count,
                                        to_char(created_at, 'YYYY-MM-DD HH24:MI:SS') created_at
                                    FROM short_urls
                                    WHERE user_id = %(user_id)s
                                    AND is_deleted = false
                                    ORDER BY click_count DESC NULLS LAST
                                    LIMIT %(limit)s
                                """
            v_kondisi           = {
                                    "user_id" : p_user_id,
                                    "limit"   : p_limit,
                                }
            v_hasil             = v_query_string_db.select(v_query, v_kondisi)
            if v_hasil["status"] == "T" and v_hasil["result"]:
                await cache_set(v_cache_key, v_hasil["result"], ttl=120)
            return v_hasil
    except Exception as e:
        return response_json(400, "F", str(e), [])
