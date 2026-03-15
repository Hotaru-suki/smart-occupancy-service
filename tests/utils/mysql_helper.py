from __future__ import annotations

import pymysql
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
    ):
        self.conn_params = {
            "host": host or get_env("MYSQL_HOST", "127.0.0.1"),
            "port": int(port or get_env("MYSQL_PORT", "3306")),
            "user": user or get_env("MYSQL_USER", "root"),
            "password": password if password is not None else get_env("MYSQL_PASSWORD", "AGhappy888@"),
            "database": database or get_env("MYSQL_DB", get_env("MYSQL_DATABASE", "occupancy_system_test")),
            "charset": "utf8mb4",
            "cursorclass": DictCursor,
        }

    def query_one(self, sql: str, args=None):
        with pymysql.connect(**self.conn_params) as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql, args or ())
                return cursor.fetchone()

    def query_all(self, sql: str, args=None):
        with pymysql.connect(**self.conn_params) as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql, args or ())
                return cursor.fetchall()

    def execute(self, sql: str, args=None):
        with pymysql.connect(**self.conn_params) as conn:
            with conn.cursor() as cursor:
                rows = cursor.execute(sql, args or ())
            conn.commit()
            return rows

    def truncate_table(self, table_name: str):
        sql = f"TRUNCATE TABLE {table_name}"
        self.execute(sql)

    def get_latest_event(self):
        sql = """
        SELECT id, event_type, people_count, event_time
        FROM occupancy_events
        ORDER BY id DESC
        LIMIT 1
        """
        return self.query_one(sql)

    def get_today_stat(self):
        sql = """
        SELECT id, stat_date, max_people, total_occupied_sec, updated_at
        FROM daily_stats
        ORDER BY id DESC
        LIMIT 1
        """
        return self.query_one(sql)
