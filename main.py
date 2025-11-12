from gui.main_window import MainWindow
from core.database import init_db
from core.reminder import ReminderThread
import threading
import sys
from queue import Queue # <-- Import Queue

def main():
    # Bước 1: Khởi tạo/Kiểm tra CSDL (Nâng cấp CSDL nếu cần)
    try:
        init_db()
    except Exception as e:
        print(f"Lỗi nghiêm trọng khi khởi tạo CSDL: {e}")
        sys.exit(1)

    # Bước 2: (THAY ĐỔI) Tạo Kênh giao tiếp (Queue)
    print("[Main] Đang tạo Kênh giao tiếp (Queue)...")
    reminder_queue = Queue()

    # Bước 3: Khởi chạy luồng nhắc nhở (Truyền queue vào)
    print("[Main] Đang khởi chạy luồng nhắc nhở (v4.2)...")
    reminder_task = ReminderThread(
        queue=reminder_queue, 
        check_interval_seconds=5 # (Đề tài yêu cầu 60s)
    )
    reminder_task.start()
    
    # Bước 4: Khởi chạy Giao diện chính (Truyền queue vào)
    print("[Main] Đang khởi chạy giao diện chính...")
    app = MainWindow(queue=reminder_queue) 
    app.mainloop()
    
    # (Khi app.mainloop() kết thúc - tức là đóng cửa sổ)
    print("[Main] Đã đóng ứng dụng. Đang dừng luồng nhắc nhở...")
    reminder_task.stop()

if __name__ == "__main__":
    main()