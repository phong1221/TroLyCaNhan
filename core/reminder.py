import threading
import time
from datetime import datetime, timedelta
from queue import Queue # <-- Import Queue
# (Không import tkinter ở đây nữa)

try:
    from . import database
except ImportError:
    import database

class ReminderThread(threading.Thread):
    # (SỬA LỖI Ở ĐÂY)
    def __init__(self, queue: Queue, check_interval_seconds=60):
        super().__init__()
        self.queue = queue # <-- Nhận Kênh giao tiếp
        self.check_interval = check_interval_seconds
        self.daemon = True
        self._running = True
        print(f"[ReminderThread] Đã khởi tạo (v4.2 - Thread-safe Queue).")

    def stop(self):
        self._running = False

    def check_for_reminders(self):
        """
        Logic v4.1 (vẫn giữ nguyên), nhưng thay vì show_popup(),
        chúng ta sẽ put(event) vào queue.
        """
        try:
            events = database.get_all_events()
            if not events:
                return

            now = datetime.now()

            for event in events:
                if (not event.get('start_time') or 
                    event.get('reminder_minutes', 0) == 0):
                    continue
                
                if event.get('reminded', 0) == 1:
                    continue
                    
                try:
                    start_time = datetime.fromisoformat(event['start_time'])
                except (ValueError, TypeError):
                    # Đây là lỗi "sự kiện 2" mà bạn thấy
                    print(f"Lỗi: Bỏ qua sự kiện {event['id']} vì định dạng thời gian sai.")
                    continue
                    
                reminder_time = start_time - timedelta(minutes=event['reminder_minutes'])

                if reminder_time <= now:
                    
                    print(f"!!! PHÁT HIỆN NHẮC NHỞ: {event['event_name']} !!!")
                    
                    # (THAY ĐỔI LỚN)
                    # Không gọi show_popup() nữa
                    # Gửi sự kiện vào Kênh (Queue)
                    self.queue.put(event)
                    
                    # ĐÁNH DẤU LÀ ĐÃ NHẮC
                    database.mark_event_as_reminded(event['id'])

        except Exception as e:
            print(f"Lỗi nghiêm trọng trong luồng nhắc nhở: {e}")

    # (Hàm show_popup() đã bị xóa khỏi file này)

    def run(self):
        while self._running:
            self.check_for_reminders()
            time.sleep(self.check_interval)

# (Phần test 'if __name__' đã được rút gọn/xóa, không cần thiết)

# --- Test (Giữ nguyên) ---
if __name__ == "__main__":
    print("--- CHẠY THỬ MODULE NHẮC NHỞ (v4.1) ---")
    
    database.init_db()
    
    # Thêm 1 sự kiện test (nhắc trước 1 phút)
    test_start_time = datetime.now() + timedelta(minutes=2) # 2 phút tới
    
    print(f"Thời gian hiện tại: {datetime.now().isoformat()}")
    print(f"Đang thêm sự kiện test lúc: {test_start_time.isoformat()}")
    
    database.add_event(
        event_name="TEST NHẮC NHỞ (v4.1)",
        start_time=test_start_time.isoformat(),
        end_time=None,
        location="Tại máy tính",
        reminder_minutes=1 # <-- Nhắc trước 1 phút
    )
    
    # Khởi chạy luồng (kiểm tra mỗi 5 giây cho nhanh)
    reminder_task = ReminderThread(check_interval_seconds=5)
    reminder_task.start()
    
    print("\n--- Đã khởi chạy luồng. Chờ khoảng 1 phút... ---")
    
    try:
        time.sleep(70) # Chờ 70 giây
    except KeyboardInterrupt:
        pass
    
    reminder_task.stop()
    print("\nĐã dừng test.")