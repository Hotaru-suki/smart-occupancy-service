from __future__ import annotations

from typing import Any

import pymysql
from pymysql.connections import Connection
from pymysql.cursors import DictCursor

from tests.utils.env_loader import get_env


class MySQLHelper:
    def __init__(
        self,
        host: str | None = None,
        port: int | None = None,
        user: str | None = None,
        password: str | None = None,
        database: str | None = None,
    ) -> None:
        mysql_host = host if host is not None else get_env("MYSQL_HOST", "127.0.0.1")
        mysql_port = port if port is not None else int(get_env("MYSQL_PORT", "3306"))
        mysql_user = user if user is not None else get_env("MYSQL_USER", "root")
        mysql_password = (
            password
            if password is not None
            else get_env("MYSQL_PASSWORD", "AGhappy888@")
        )
        mysql_database = (
            database
            if database is not None
            else get_env("MYSQL_DB", get_env("MYSQL_DATABASE", "occupancy_system_test"))
        )
        self.conn_params = {
            "host": mysql_host,
            "port": mysql_port,
            "user": mysql_user,
            "password": mysql_password,
            "database": mysql_database,
            "charset": "utf8mb4",
            "cursorclass": DictCursor,
        }

    def _connect(self) -> Connection:
        return pymysql.connect(**self.conn_params)

    def query_one(self, sql: str, args: tuple[Any, ...] | None = None) -> dict[str, Any] | None:
        with self._connect() as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql, args or ())
                return cursor.fetchone()

    def query_all(self, sql: str, args: tuple[Any, ...] | None = None) -> list[dict[str, Any]]:
        with self._connect() as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql, args or ())
                return cursor.fetchall()

    def execute(self, sql: str, args: tuple[Any, ...] | None = None) -> int:
        with self._connect() as conn:
            with conn.cursor() as cursor:
                rows = cursor.execute(sql, args or ())
            conn.commit()
            return rows

    def truncate_table(self, table_name: str) -> None:
        sql = f"TRUNCATE TABLE {table_name}"
        self.execute(sql)

    def get_latest_event(self) -> dict[str, Any] | None:
        sql = """
        SELECT id, event_type, people_count, event_time
        FROM occupancy_events
        ORDER BY id DESC
        LIMIT 1
        """
        return self.query_one(sql)

    def get_today_stat(self) -> dict[str, Any] | None:
        sql = """
        SELECT id, stat_date, max_people, total_occupied_sec, updated_at
        FROM daily_stats
        ORDER BY id DESC
        LIMIT 1
        """
        return self.query_one(sql)
