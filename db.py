import sqlite3
from config import DB_PATH
from models import TimeEntry


def get_conn():
    return sqlite3.connect(DB_PATH)


def init_db():
    with get_conn() as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS time_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            work_date TEXT NOT NULL,
            start_time TEXT NOT NULL,
            end_time TEXT NOT NULL,
            hours REAL NOT NULL,
            client TEXT NOT NULL,
            category TEXT,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)


def insert_entry(entry: TimeEntry):
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO time_entries
            (work_date, start_time, end_time, hours, client, category, description)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                entry.work_date.isoformat(),
                entry.start_time.isoformat(),
                entry.end_time.isoformat(),
                entry.hours,
                entry.client,
                entry.category,
                entry.description,
            ),
        )


def entries_for_month(month: str, client: str = None):
    with get_conn() as conn:
        query = """
            SELECT id, work_date, start_time, end_time, hours, client, description
            FROM time_entries
            WHERE strftime('%Y-%m', work_date) = ?
        """
        params = [month]
        if client:
            query += " AND client = ?"
            params.append(client)

        query += " ORDER BY work_date, start_time"

        cur = conn.execute(query, params)
        return cur.fetchall()


def total_hours_for_month(month: str, client: str = None) -> float:
    with get_conn() as conn:
        query = """
            SELECT COALESCE(SUM(hours), 0)
            FROM time_entries
            WHERE strftime('%Y-%m', work_date) = ?
        """
        params = [month]
        if client:
            query += " AND client = ?"
            params.append(client)

        cur = conn.execute(query, params)
        return cur.fetchone()[0]

def entries_for_client(client: str):
    with get_conn() as conn:
        query = """
            SELECT id, work_date, start_time, end_time, hours, client, description
            FROM time_entries
            WHERE client = ?
        """
        params = [client]
        query += " ORDER BY work_date, start_time"

        cur = conn.execute(query, params)
        return cur.fetchall()


def total_hours_for_client(client: str) -> float:
    with get_conn() as conn:
        query = """
            SELECT COALESCE(SUM(hours), 0)
            FROM time_entries
            WHERE client = ?
        """
        params = [client]

        cur = conn.execute(query, params)
        return cur.fetchone()[0]


def entries_by_ids(ids: list[int]):
    if not ids:
        return []
    placeholders = ",".join("?" * len(ids))
    with get_conn() as conn:
        cur = conn.execute(
            f"""
            SELECT id, work_date, start_time, end_time, hours, client, description
            FROM time_entries
            WHERE id IN ({placeholders})
            ORDER BY work_date, start_time
            """,
            ids,
        )
        return cur.fetchall()


def total_hours_for_ids(ids: list[int]) -> float:
    if not ids:
        return 0.0
    placeholders = ",".join("?" * len(ids))
    with get_conn() as conn:
        cur = conn.execute(
            f"""
            SELECT COALESCE(SUM(hours), 0)
            FROM time_entries
            WHERE id IN ({placeholders})
            """,
            ids,
        )
        return cur.fetchone()[0]


def entries_for_month_excluding_ids(
    month: str, exclude_ids: list[int], client: str = None
):
    if not exclude_ids:
        return entries_for_month(month, client)
    placeholders = ",".join("?" * len(exclude_ids))
    with get_conn() as conn:
        query = f"""
            SELECT id, work_date, start_time, end_time, hours, client, description
            FROM time_entries
            WHERE strftime('%Y-%m', work_date) = ?
            AND id NOT IN ({placeholders})
        """
        params = [month] + exclude_ids
        if client:
            query += " AND client = ?"
            params.append(client)

        query += " ORDER BY work_date, start_time"

        cur = conn.execute(query, params)
        return cur.fetchall()


def total_hours_for_month_excluding_ids(
    month: str, exclude_ids: list[int], client: str = None
) -> float:
    if not exclude_ids:
        return total_hours_for_month(month, client)
    placeholders = ",".join("?" * len(exclude_ids))
    with get_conn() as conn:
        query = f"""
            SELECT COALESCE(SUM(hours), 0)
            FROM time_entries
            WHERE strftime('%Y-%m', work_date) = ?
            AND id NOT IN ({placeholders})
        """
        params = [month] + exclude_ids
        if client:
            query += " AND client = ?"
            params.append(client)

        cur = conn.execute(query, params)
        return cur.fetchone()[0]
