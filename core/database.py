import sqlite3
import os


# Lấy đường dẫn thư mục "Documents" của người dùng (VD: C:\Users\Quang\Documents)
USER_DOCS = os.path.join(os.path.expanduser('~'), 'Documents')
# Tạo một thư mục riêng cho ứng dụng
APP_DATA_DIR = os.path.join(USER_DOCS, 'TroLyLichTrinh')
# Tạo đường dẫn CSDL
DB_PATH = os.path.join(APP_DATA_DIR, 'schedule.db')

# Đảm bảo thư mục 'TroLyLichTrinh' trong Documents tồn tại
os.makedirs(APP_DATA_DIR, exist_ok=True)

def get_db_connection():
    """Tạo và trả về một kết nối CSDL."""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        print(f"Lỗi kết nối CSDL: {e}")
        return None

def _check_and_add_reminded_column():
    """Tự động thêm cột 'reminded' nếu nó chưa tồn tại."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(events)")
            columns = [col['name'] for col in cursor.fetchall()]
            
            if 'reminded' not in columns:
                print("--- [Database] Đang nâng cấp: Thêm cột 'reminded' ---")
                cursor.execute("ALTER TABLE events ADD COLUMN reminded INTEGER DEFAULT 0")
                conn.commit()
                print("--- [Database] Nâng cấp thành công ---")
    except sqlite3.Error as e:
        print(f"Lỗi khi nâng cấp CSDL: {e}")

def init_db():
    """Khởi tạo bảng 'events' VÀ nâng cấp CSDL nếu cần."""
    sql_create_table = """
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_name TEXT NOT NULL,
            start_time TEXT NOT NULL,
            end_time TEXT,
            location TEXT,
            reminder_minutes INTEGER DEFAULT 0,
            reminded INTEGER DEFAULT 0 
        );
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql_create_table)
            conn.commit()
            
        _check_and_add_reminded_column()
        
        print(f"Cơ sở dữ liệu đã được khởi tạo/kiểm tra thành công tại: {DB_PATH}")
            
    except sqlite3.Error as e:
        print(f"Lỗi khi khởi tạo bảng: {e}")

def mark_event_as_reminded(event_id):
    """Đánh dấu một sự kiện là đã được nhắc nhở."""
    sql = "UPDATE events SET reminded = 1 WHERE id = ?"
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, (event_id,))
            conn.commit()
            return True
    except sqlite3.Error as e:
        print(f"Lỗi khi đánh dấu đã nhắc: {e}")
        return False

def add_event(event_name, start_time, end_time, location, reminder_minutes):
    """Thêm một sự kiện mới vào CSDL (reset 'reminded' về 0)."""
    sql = """
        INSERT INTO events (event_name, start_time, end_time, location, reminder_minutes, reminded)
        VALUES (?, ?, ?, ?, ?, 0)
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, (event_name, start_time, end_time, location, reminder_minutes))
            conn.commit()
            return cursor.lastrowid
    except sqlite3.Error as e:
        print(f"Lỗi khi thêm sự kiện: {e}")
        return None

def get_all_events():
    """Lấy tất cả sự kiện (Giữ nguyên)."""
    sql = "SELECT * FROM events ORDER BY start_time ASC"
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql)
            events = [dict(row) for row in cursor.fetchall()]
            return events
    except sqlite3.Error as e:
        print(f"Lỗi khi lấy sự kiện: {e}")
        return []

def update_event(event_id, event_name, start_time, end_time, location, reminder_minutes):
    """Cập nhật một sự kiện (NÂNG CẤP: reset 'reminded' về 0)."""
    sql = """
        UPDATE events
        SET event_name = ?, start_time = ?, end_time = ?, location = ?, reminder_minutes = ?, reminded = 0
        WHERE id = ?
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, (event_name, start_time, end_time, location, reminder_minutes, event_id))
            conn.commit()
            return True
    except sqlite3.Error as e:
        print(f"Lỗi khi cập nhật sự kiện: {e}")
        return False

def delete_event(event_id):
    sql = "DELETE FROM events WHERE id = ?"
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, (event_id,))
            conn.commit()
            return True
    except sqlite3.Error as e:
        print(f"Lỗi khi xóa sự kiện: {e}")
        return False

def search_events_advanced(keyword=None, location=None, from_date=None, to_date=None):
    """
    Tìm kiếm nâng cao hỗ trợ chính xác từng giây (YYYY-MM-DD HH:MM:SS)
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = "SELECT * FROM events WHERE 1=1"
    params = []

    if keyword:
        query += " AND event_name LIKE ?"
        params.append(f"%{keyword}%")
    
    if location:
        query += " AND location LIKE ?"
        params.append(f"%{location}%")
    
    if from_date:
        # Nếu chỉ nhập ngày (độ dài <= 10), mặc định là đầu ngày (00:00:00)
        if len(from_date) <= 10:
            from_date += " 00:00:00"
        query += " AND start_time >= ?"
        params.append(from_date)
    
    if to_date:
        # Nếu chỉ nhập ngày, mặc định là cuối ngày (23:59:59)
        if len(to_date) <= 10:
            to_date += " 23:59:59"
        # Nếu người dùng nhập giờ (VD: 14:00), giữ nguyên để so sánh chính xác
        query += " AND start_time <= ?"
        params.append(to_date)

    query += " ORDER BY start_time ASC"

    cursor.execute(query, params)
    rows = cursor.fetchall()
    
    events = []
    for row in rows:
        events.append({
            "id": row[0],
            "event_name": row[1],
            "start_time": row[2],
            "end_time": row[3],
            "location": row[4],
            "reminder_minutes": row[5]
        })
    
    conn.close()
    return events
if __name__ == "__main__":
    print("Đang khởi tạo cơ sở dữ liệu (và nâng cấp nếu cần)...")
    init_db()