import json
import ics
import datetime

try:
    from . import database
except ImportError:
    import database

def export_to_json(filepath: str) -> bool:
    """Lấy tất cả sự kiện và lưu vào file JSON."""
    try:
        events = database.get_all_events()
        with open(filepath, 'w', encoding='utf-8') as f:
            # ensure_ascii=False để giữ tiếng Việt
            json.dump(events, f, ensure_ascii=False, indent=4)
        return True
    except Exception as e:
        print(f"Lỗi khi xuất JSON: {e}")
        return False

def export_to_ics(filepath: str) -> bool:
    """Lấy tất cả sự kiện và lưu vào file .ics (iCalendar)."""
    try:
        events = database.get_all_events()
        c = ics.Calendar() # Tạo 1 lịch mới

        for event in events:
            # Bỏ qua nếu không có thời gian
            if not event.get('start_time'):
                continue
            
            e = ics.Event()
            e.name = event['event_name']
            
            try:
                # Chuyển đổi chuỗi ISO thành datetime
                e.begin = datetime.datetime.fromisoformat(event['start_time'])
            except Exception:
                continue # Bỏ qua nếu thời gian lỗi

            if event.get('end_time'):
                try:
                    e.end = datetime.datetime.fromisoformat(event['end_time'])
                except Exception:
                    pass # Bỏ qua nếu end_time lỗi

            e.location = event.get('location')
            
            # Thêm thông tin nhắc nhở vào phần mô tả
            if event.get('reminder_minutes', 0) > 0:
                e.description = f"Nhắc trước {event['reminder_minutes']} phút."
            
            c.events.add(e) # Thêm sự kiện vào lịch

        # Ghi ra file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.writelines(c.serialize_iter()) # Dùng .serialize_iter()
            
        return True
    except Exception as e:
        print(f"Lỗi khi xuất ICS: {e}")
        return False