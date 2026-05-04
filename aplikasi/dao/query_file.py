from aplikasi import (log, app)
import redis.asyncio
import psycopg2
import psycopg2.pool
from aplikasi.settings import settings
import os
import uuid
import asyncio
import threading

_PG_POOL_WRITE  = None
_PG_POOL_READ   = None
_pg_lock        = threading.Lock()

INSTANCE_ID = os.getenv("K_REVISION", f"local-{uuid.uuid4().hex[:8]}")
APP_NAME    = f"url-shortener-{INSTANCE_ID}"


def _get_pg_pool_write():
    global _PG_POOL_WRITE
    if _PG_POOL_WRITE is None:
        with _pg_lock:
            if _PG_POOL_WRITE is None:
                _PG_POOL_WRITE = psycopg2.pool.ThreadedConnectionPool(
                    settings.POSTGRES_POOL_MIN,
                    settings.POSTGRES_POOL_MAX,
                    user             = settings.POSTGRES_DB_USER,
                    password         = settings.POSTGRES_DB_PASS,
                    host             = settings.POSTGRES_DB_HOST,
                    port             = settings.POSTGRES_DB_PORT,
                    database         = settings.POSTGRES_DB_DATA,
                    connect_timeout  = 5,
                    application_name = APP_NAME,
                )
    return _PG_POOL_WRITE


def _get_pg_pool_read():
    global _PG_POOL_READ
    if _PG_POOL_READ is None:
        with _pg_lock:
            if _PG_POOL_READ is None:
                _PG_POOL_READ = psycopg2.pool.ThreadedConnectionPool(
                    settings.POSTGRES_POOL_MIN,
                    settings.POSTGRES_POOL_MAX,
                    user             = settings.POSTGRES_DB_USER,
                    password         = settings.POSTGRES_DB_PASS,
                    host             = settings.POSTGRES_DB_HOST,
                    port             = settings.POSTGRES_DB_PORT,
                    database         = settings.POSTGRES_DB_DATA,
                    connect_timeout  = 5,
                    application_name = APP_NAME,
                )
    return _PG_POOL_READ


REDIS_TEXT_CLIENT    = None
REDIS_LIMITER_CLIENT = None
_redis_text_lock     = asyncio.Lock()
_redis_limiter_lock  = asyncio.Lock()


def _make_redis_client(decode: bool, max_connections: int):
    return redis.asyncio.from_url(
        settings.CONNECTION_STRING_REDIS,
        decode_responses       = decode,
        max_connections        = max_connections,
        socket_timeout         = 3,
        socket_connect_timeout = 3,
        retry_on_timeout       = True,
        health_check_interval  = 30,
    )


async def get_redis_text_client():
    global REDIS_TEXT_CLIENT
    if REDIS_TEXT_CLIENT is None:
        async with _redis_text_lock:
            if REDIS_TEXT_CLIENT is None:
                REDIS_TEXT_CLIENT = _make_redis_client(decode=True, max_connections=20)
    return REDIS_TEXT_CLIENT


async def get_redis_limiter_client():
    global REDIS_LIMITER_CLIENT
    if REDIS_LIMITER_CLIENT is None:
        async with _redis_limiter_lock:
            if REDIS_LIMITER_CLIENT is None:
                REDIS_LIMITER_CLIENT = _make_redis_client(decode=True, max_connections=10)
    return REDIS_LIMITER_CLIENT


async def connection_redis_async():
    return await get_redis_text_client()


def response_json(p_status_code, p_flag, p_message, p_result):
    return {
        "status_code": p_status_code,
        "status":      p_flag,
        "message":     p_message,
        "result":      p_result,
    }


def rows_to_dict_list(p_cursor):
    columns = [desc[0] for desc in p_cursor.description]
    return [dict(zip(columns, row)) for row in p_cursor.fetchall()]


class CreateConnectionDb(object):

    def __init__(self, p_list_connection):
        self._v_read        = p_list_connection["read"]
        self._v_write       = p_list_connection["write"]
        self._ps_connection = None
        self._ps_cursor     = None

    def __enter__(self):
        if self._v_read:
            self._ps_connection = _get_pg_pool_read().getconn()
        elif self._v_write:
            self._ps_connection = _get_pg_pool_write().getconn()
        self._ps_cursor = self._ps_connection.cursor()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            if exc_type:
                self._ps_connection.rollback()
        finally:
            if self._ps_cursor:
                self._ps_cursor.close()
            if self._v_read and self._ps_connection:
                _get_pg_pool_read().putconn(self._ps_connection)
            elif self._v_write and self._ps_connection:
                _get_pg_pool_write().putconn(self._ps_connection)

    def get_connection(self):
        return self._ps_connection

    def get_cursor(self):
        return self._ps_cursor

    def rollback(self):
        self._ps_connection.rollback()

    def commit(self):
        self._ps_connection.commit()


class QueryStringDb(object):
    def __init__(self, connection):
        self._db_connection = connection

    def select(self, p_query, p_param, p_response="Select data successfully!"):
        try:
            self._db_connection.get_cursor().execute(p_query, p_param)
            result = rows_to_dict_list(self._db_connection.get_cursor())
            return response_json(200, "T", p_response, result)
        except psycopg2.Error as error:
            v_msg = f"Error select: {error.pgcode}, {str(error.pgerror)}"
            return response_json(400, "F", v_msg, [])

    def execute(self, p_query, p_param, p_response="Execute commit successfully!"):
        try:
            self._db_connection.get_cursor().execute(p_query, p_param)
            self._db_connection.commit()
            return response_json(200, "T", p_response, None)
        except psycopg2.Error as error:
            self._db_connection.rollback()
            v_msg = f"Error execute commit: {error.pgcode}, {str(error.pgerror)}"
            return response_json(400, "F", v_msg, None)
