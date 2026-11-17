"""Работа с базой данных SQLite: схема и все SQL-запросы."""

import sqlite3

DB_PATH = "habits.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS habits (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            name         TEXT    NOT NULL UNIQUE,
            description  TEXT    DEFAULT '',
            color        TEXT    DEFAULT '#10b981',
            freq_type    TEXT    NOT NULL CHECK (freq_type IN ('daily', 'weekly')),
            freq_target  INTEGER          CHECK (freq_target BETWEEN 1 AND 7),
            created_at   TEXT    NOT NULL,
            archived     INTEGER NOT NULL DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS completions (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            habit_id INTEGER NOT NULL REFERENCES habits (id) ON DELETE CASCADE,
            date     TEXT    NOT NULL,
            UNIQUE (habit_id, date)
        );

        CREATE INDEX IF NOT EXISTS idx_completions_habit_date
            ON completions (habit_id, date);
        CREATE INDEX IF NOT EXISTS idx_habits_archived
            ON habits (archived);
        """
    )
    conn.commit()
    conn.close()


# ----- привычки -----

def create_habit(name, description, color, freq_type, freq_target):
    conn = get_connection()
    cur = conn.execute(
        "INSERT INTO habits (name, description, color, freq_type, freq_target,"
        " created_at, archived) VALUES (?, ?, ?, ?, ?, date('now', 'localtime'), 0)",
        (name, description, color, freq_type, freq_target),
    )
    conn.commit()
    habit_id = cur.lastrowid
    conn.close()
    return habit_id


def get_habit(habit_id):
    conn = get_connection()
    row = conn.execute("SELECT * FROM habits WHERE id = ?", (habit_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_all_habits():
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM habits WHERE archived = 0 ORDER BY name"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_archived_habits():
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM habits WHERE archived = 1 ORDER BY name"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def update_habit(habit_id, name, description, color, freq_type, freq_target):
    conn = get_connection()
    conn.execute(
        "UPDATE habits SET name = ?, description = ?, color = ?,"
        " freq_type = ?, freq_target = ? WHERE id = ?",
        (name, description, color, freq_type, freq_target, habit_id),
    )
    conn.commit()
    conn.close()


def set_archived(habit_id, archived):
    conn = get_connection()
    conn.execute(
        "UPDATE habits SET archived = ? WHERE id = ?", (int(archived), habit_id)
    )
    conn.commit()
    conn.close()


def delete_habit(habit_id):
    conn = get_connection()
    conn.execute("DELETE FROM habits WHERE id = ?", (habit_id,))
    conn.commit()
    conn.close()


# ----- отметки -----

def add_completion(habit_id, day):
    conn = get_connection()
    conn.execute(
        "INSERT OR IGNORE INTO completions (habit_id, date) VALUES (?, ?)",
        (habit_id, day),
    )
    conn.commit()
    conn.close()


def remove_completion(habit_id, day):
    conn = get_connection()
    conn.execute(
        "DELETE FROM completions WHERE habit_id = ? AND date = ?",
        (habit_id, day),
    )
    conn.commit()
    conn.close()


def has_completion(habit_id, day):
    conn = get_connection()
    row = conn.execute(
        "SELECT COUNT(*) FROM completions WHERE habit_id = ? AND date = ?",
        (habit_id, day),
    ).fetchone()
    conn.close()
    return row[0] > 0


def toggle_completion(habit_id, day):
    if has_completion(habit_id, day):
        remove_completion(habit_id, day)
        return False
    add_completion(habit_id, day)
    return True


def get_completions(habit_id, start=None, end=None):
    conn = get_connection()
    if start and end:
        rows = conn.execute(
            "SELECT date FROM completions WHERE habit_id = ?"
            " AND date BETWEEN ? AND ?",
            (habit_id, start, end),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT date FROM completions WHERE habit_id = ?", (habit_id,)
        ).fetchall()
    conn.close()
    return [r["date"] for r in rows]


def export_all():
    conn = get_connection()
    rows = conn.execute(
        "SELECT h.name, c.date FROM completions c"
        " JOIN habits h ON h.id = c.habit_id ORDER BY c.date"
    ).fetchall()
    conn.close()
    return [(r["name"], r["date"]) for r in rows]
