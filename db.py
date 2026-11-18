import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "reminders.db")

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS reminders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                chat_id INTEGER NOT NULL,
                message TEXT NOT NULL,
                remind_at TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                created_at TEXT NOT NULL
            )
        """)
        conn.commit()

def add_reminder(user_id: int, chat_id: int, message: str, remind_at: str) -> int:
    now_str = datetime.now().isoformat()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO reminders (user_id, chat_id, message, remind_at, status, created_at)
            VALUES (?, ?, ?, ?, 'pending', ?)
        """, (user_id, chat_id, message, remind_at, now_str))
        conn.commit()
        return cursor.lastrowid

def get_pending_reminders():
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM reminders
            WHERE status = 'pending'
            ORDER BY remind_at ASC
        """)
        return [dict(row) for row in cursor.fetchall()]

def get_user_reminders(user_id: int):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM reminders
            WHERE user_id = ? AND status = 'pending'
            ORDER BY remind_at ASC
        """, (user_id,))
        return [dict(row) for row in cursor.fetchall()]

def mark_completed(reminder_id: int):
    with get_connection() as conn:
        conn.execute("""
            UPDATE reminders
            SET status = 'completed'
            WHERE id = ?
        """, (reminder_id,))
        conn.commit()

def cancel_reminder(reminder_id: int, user_id: int) -> bool:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE reminders
            SET status = 'cancelled'
            WHERE id = ? AND user_id = ? AND status = 'pending'
        """, (reminder_id, user_id))
        conn.commit()
        return cursor.rowcount > 0

def cancel_reminder_by_time(user_id: int, date_str: str, time_str: str) -> list:
    """Hủy lịch hẹn 1 lần theo ngày và giờ"""
    with get_connection() as conn:
        cursor = conn.cursor()
        # Tìm các reminder phù hợp
        cursor.execute("""
            SELECT id, message, remind_at FROM reminders
            WHERE user_id = ? AND status = 'pending'
        """, (user_id,))
        
        cancelled = []
        for row in cursor.fetchall():
            remind_time = datetime.fromisoformat(row['remind_at'])
            # So sánh ngày và giờ
            if remind_time.strftime('%d/%m') == date_str and remind_time.strftime('%H:%M') == time_str:
                cursor.execute("""
                    UPDATE reminders SET status = 'cancelled' WHERE id = ?
                """, (row['id'],))
                cancelled.append({'id': row['id'], 'message': row['message']})
        
        conn.commit()
        return cancelled

# ===== RECURRING SCHEDULES =====

def init_schedules_table():
    """Khởi tạo bảng lịch học định kỳ"""
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS schedules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                chat_id INTEGER NOT NULL,
                day_of_week INTEGER NOT NULL,
                time TEXT NOT NULL,
                message TEXT NOT NULL,
                active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL
            )
        """)
        conn.commit()

def init_user_settings_table():
    """Khởi tạo bảng cài đặt người dùng"""
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS user_settings (
                user_id INTEGER PRIMARY KEY,
                reminder_minutes INTEGER NOT NULL DEFAULT 15,
                updated_at TEXT NOT NULL
            )
        """)
        conn.commit()

def get_reminder_minutes(user_id: int) -> int:
    """Lấy số phút nhắc trước của user (mặc định 15 phút)"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT reminder_minutes FROM user_settings
            WHERE user_id = ?
        """, (user_id,))
        result = cursor.fetchone()
        return result['reminder_minutes'] if result else 15

def set_reminder_minutes(user_id: int, minutes: int):
    """Thiết lập số phút nhắc trước"""
    now_str = datetime.now().isoformat()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO user_settings (user_id, reminder_minutes, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                reminder_minutes = excluded.reminder_minutes,
                updated_at = excluded.updated_at
        """, (user_id, minutes, now_str))
        conn.commit()

def add_schedule(user_id: int, chat_id: int, day_of_week: int, time: str, message: str) -> int:
    """Thêm lịch học định kỳ
    day_of_week: 0=Thứ 2, 1=Thứ 3, 2=Thứ 4, 3=Thứ 5, 4=Thứ 6, 5=Thứ 7, 6=Chủ nhật
    time: HH:MM (ví dụ: "08:00")
    """
    now_str = datetime.now().isoformat()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO schedules (user_id, chat_id, day_of_week, time, message, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (user_id, chat_id, day_of_week, time, message, now_str))
        conn.commit()
        return cursor.lastrowid

def get_user_schedules(user_id: int):
    """Lấy tất cả lịch học của user"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM schedules
            WHERE user_id = ? AND active = 1
            ORDER BY day_of_week, time
        """, (user_id,))
        return [dict(row) for row in cursor.fetchall()]

def get_all_active_schedules():
    """Lấy tất cả lịch học đang active"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM schedules
            WHERE active = 1
            ORDER BY day_of_week, time
        """)
        return [dict(row) for row in cursor.fetchall()]

def delete_schedule(schedule_id: int, user_id: int) -> bool:
    """Xóa lịch học"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE schedules
            SET active = 0
            WHERE id = ? AND user_id = ?
        """, (schedule_id, user_id))
        conn.commit()
        return cursor.rowcount > 0

def delete_schedule_by_time(user_id: int, day_of_week: int, time_str: str) -> list:
    """Xóa lịch hẹn tuần theo thứ và giờ"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, message FROM schedules
            WHERE user_id = ? AND day_of_week = ? AND time = ? AND active = 1
        """, (user_id, day_of_week, time_str))
        
        deleted = []
        for row in cursor.fetchall():
            cursor.execute("""
                UPDATE schedules SET active = 0 WHERE id = ?
            """, (row['id'],))
            deleted.append({'id': row['id'], 'message': row['message']})
        
        conn.commit()
        return deleted

def update_schedule(schedule_id: int, user_id: int, day_of_week: int = None, time: str = None, message: str = None) -> bool:
    """Cập nhật lịch hẹn tuần"""
    with get_connection() as conn:
        cursor = conn.cursor()
        
        # Lấy thông tin hiện tại
        cursor.execute("SELECT * FROM schedules WHERE id = ? AND user_id = ?", (schedule_id, user_id))
        current = cursor.fetchone()
        
        if not current:
            return False
        
        # Cập nhật các trường được cung cấp
        new_day = day_of_week if day_of_week is not None else current['day_of_week']
        new_time = time if time is not None else current['time']
        new_message = message if message is not None else current['message']
        
        cursor.execute("""
            UPDATE schedules
            SET day_of_week = ?, time = ?, message = ?
            WHERE id = ? AND user_id = ?
        """, (new_day, new_time, new_message, schedule_id, user_id))
        conn.commit()
        return cursor.rowcount > 0

def get_schedule_by_id(schedule_id: int, user_id: int):
    """Lấy thông tin lịch hẹn theo ID"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM schedules
            WHERE id = ? AND user_id = ? AND active = 1
        """, (schedule_id, user_id))
        result = cursor.fetchone()
        return dict(result) if result else None

