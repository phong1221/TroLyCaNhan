TroLyLichTrinh/
│
├── core/                       # Tầng Nghiệp vụ & Truy cập dữ liệu (Business & Data Layer)
│   ├── __init__.py             # Đánh dấu thư mục là một Python Package
│   ├── database.py             # Quản lý kết nối SQLite, thực hiện các truy vấn CRUD (Thêm, Sửa, Xóa, Tìm kiếm)
│   ├── nlp_parser.py           # Module NLP: Chứa các Regex pattern và logic phân tích ngôn ngữ tự nhiên
│   ├── exporter.py             # Module Tiện ích: Xử lý xuất dữ liệu ra file .json và .ics (iCalendar)
│   └── reminder.py             # Module Hệ thống: Chứa luồng (Thread) chạy ngầm để kiểm tra và phát thông báo nhắc nhở
│
├── gui/                        # Tầng Giao diện (Presentation Layer)
│   ├── __init__.py
│   └── main_window.py          # Giao diện chính: Chứa class MainWindow, SearchDialog, xử lý sự kiện và hiển thị Treeview
│
├── data/                       # Tầng Lưu trữ (Storage)
│   └── schedule.db             # File cơ sở dữ liệu SQLite (Tự động tạo nếu chưa tồn tại)
│
├── tests/                      # Kiểm thử (Testing)
│   └── test_nlp.py             # Các Unit Test để kiểm tra độ chính xác của module NLP
│
├── build/                      # (Generated) Thư mục tạm chứa các file biên dịch trung gian của PyInstaller
├── dist/                       # (Generated) Thư mục chứa file chạy (.exe) sau khi đóng gói
│   └── main.exe                # File thực thi ứng dụng (Executable)
│
├── main.py                     # Entry Point: File khởi chạy ứng dụng, thiết lập cấu hình ban đầu
├── main.spec                   # File cấu hình của PyInstaller dùng để đóng gói dự án
├── requirements.txt            # Danh sách các thư viện phụ thuộc (ttkbootstrap, dateparser,...)
└── README.md                   # Tài liệu hướng dẫn sử dụng và thông tin dự án
pip install -r requirements.txt