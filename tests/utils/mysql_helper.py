import pymysql
from pymysql.cursors import DictCursor


class MySQLHelper:
    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 3306,
        user: str = "root",
        password: str = "AGhappy888@",
        database: str = "occupancy_system_test",
    ):
        self.conn_params = {
            "host": host,
            "port": port,
            "user": user,
            "password": password,
            "database": database,
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