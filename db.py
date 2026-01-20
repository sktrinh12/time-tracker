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
            (work_date, start_time, end_time, hours, category, description)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                entry.work_date.isoformat(),
                entry.start_time.isoformat(),
                entry.end_time.isoformat(),
                entry.hours,
                entry.category,
                entry.description,
            ),
        )

def entries_for_month(month: str):
    with get_conn() as conn:
        cur = conn.execute(
            """
            SELECT work_date, start_time, end_time, hours, category, description
            FROM time_entries
            WHERE strftime('%Y-%m', work_date) = ?
            ORDER BY work_date, start_time
            """,
            (month,),
        )
        return cur.fetchall()

def total_hours_for_month(month: str) -> float:
    with get_conn() as conn:
        cur = conn.execute(
            """
            SELECT COALESCE(SUM(hours), 0)
            FROM time_entries
            WHERE strftime('%Y-%m', work_date) = ?
            """,
            (month,),
        )
        return cur.fetchone()[0]

def entries_for_month(month: str):
    with get_conn() as conn:
        cur = conn.execute(
            """
            SELECT work_date, start_time, end_time, hours, description
            FROM time_entries
            WHERE strftime('%Y-%m', work_date) = ?
            ORDER BY work_date, start_time
            """,
            (month,),
        )
        return cur.fetchall()
