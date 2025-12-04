import threading
import time
from datetime import datetime, timedelta
from queue import Queue
import winsound 

try:
    from . import database
except ImportError:
    import database

class ReminderThread(threading.Thread):
    def __init__(self, queue: Queue, check_interval_seconds=60):
        super().__init__()
        self.queue = queue 
        self.check_interval = check_interval_seconds
        self.daemon = True
        self._running = True
        print(f"[ReminderThread] Đã khởi tạo (v5.0 - Windows Sound).")

    def stop(self):
        self._running = False

    def play_notification_sound(self):
        """Phát tiếng BÍP điện tử (Giống đồng hồ báo thức)"""
        try:
            # winsound.Beep(tần_số_Hz, thời_gian_ms)
            for _ in range(10):
                winsound.Beep(1000, 200) # Tần số 1000Hz trong 200ms
                time.sleep(0.1)          # Nghỉ xíu giữa các tiếng bíp
            
            print("[Audio] Đã phát tiếng Bíp báo thức.")
        except Exception as e:
            print(f"[Audio] Lỗi phát âm thanh: {e}")

    def check_for_reminders(self):
        """
        Logic v5.0: Phát âm thanh Windows và put(event) vào queue.
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
                    # Xử lý chuỗi thời gian (bỏ chữ T nếu có để tránh lỗi)
                    time_str = event['start_time'].replace("T", " ")
                    start_time = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
                except (ValueError, TypeError):
                    # print(f"Lỗi: Bỏ qua sự kiện {event['id']} vì định dạng thời gian sai.")
                    continue
                    
                reminder_time = start_time - timedelta(minutes=event['reminder_minutes'])

                if reminder_time <= now:
                    
                    print(f"!!! PHÁT HIỆN NHẮC NHỞ: {event['event_name']} !!!")
                    
                    # 1. Phát âm thanh (Logic Mới)
                    self.play_notification_sound()

                    # 2. Gửi sự kiện vào Kênh (Queue) để hiện Popup
                    self.queue.put(event)
                    
                    # 3. Đánh dấu là đã nhắc
                    database.mark_event_as_reminded(event['id'])

        except Exception as e:
            print(f"Lỗi nghiêm trọng trong luồng nhắc nhở: {e}")

    def run(self):
        while self._running:
            self.check_for_reminders()
            time.sleep(self.check_interval)

# --- Test ---
if __name__ == "__main__":
    print("--- CHẠY THỬ MODULE NHẮC NHỞ ---")
    
    database.init_db()
    
    # Thêm 1 sự kiện test (nhắc trước 1 phút)
    test_start_time = datetime.now() + timedelta(minutes=2) # 2 phút tới
    
    print(f"Thời gian hiện tại: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Đang thêm sự kiện test lúc: {test_start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    database.add_event(
        event_name="TEST NHẮC NHỞ ",
        start_time=test_start_time.strftime('%Y-%m-%d %H:%M:%S'),
        end_time=None,
        location="Tại máy tính",
        reminder_minutes=1 
    )
    
    # Tạo hàng đợi giả để test
    test_queue = Queue()
    
    # Khởi chạy luồng (kiểm tra mỗi 5 giây cho nhanh)
    reminder_task = ReminderThread(queue=test_queue, check_interval_seconds=5)
    reminder_task.start()
    
    print("\n--- Đã khởi chạy luồng. Chờ khoảng 1 phút... ---")
    
    try:
        while True:
            # Mô phỏng việc GUI nhận tin nhắn
            if not test_queue.empty():
                evt = test_queue.get()
                print(f"\n[MAIN THREAD] Nhận được tin nhắn từ Queue: {evt['event_name']}")
                break
            time.sleep(1)
            
        time.sleep(5) # Chờ thêm chút để nghe hết nhạc
    except KeyboardInterrupt:
        pass
    
    reminder_task.stop()
    print("\nĐã dừng test.")