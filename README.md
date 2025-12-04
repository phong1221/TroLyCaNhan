# 📅 Trợ Lý Lịch Trình Cá Nhân (Personal Schedule Assistant)

![Python](https://img.shields.io/badge/Python-3.13.1-blue.svg) ![Tkinter](https://img.shields.io/badge/GUI-ttkbootstrap_1.10.1-green.svg) ![SQLite](https://img.shields.io/badge/Database-SQLite3-lightgrey.svg) ![NLP](https://img.shields.io/badge/NLP-Hybrid_Approach-orange.svg)

> **Đồ án Chuyên ngành - Khoa Công Nghệ Thông Tin - Đại học Sài Gòn** > Ứng dụng quản lý lịch trình cá nhân trên Desktop tích hợp tính năng xử lý ngôn ngữ tự nhiên tiếng Việt, giúp người dùng tạo lịch nhanh chóng bằng câu lệnh tự nhiên.

---

## 📖 Giới thiệu

**Trợ Lý Lịch Trình Cá Nhân** là giải pháp thay thế cho việc nhập liệu thủ công rườm rà trên các ứng dụng lịch truyền thống. [cite_start]Ứng dụng cho phép người dùng ra lệnh bằng **ngôn ngữ tự nhiên tiếng Việt** (có dấu hoặc không dấu) để tự động tạo sự kiện, nhắc nhở và quản lý thời gian hiệu quả[cite: 745, 746].

## ✨ Tính năng nổi bật

### 1. Xử lý Ngôn ngữ Tự nhiên (NLP) - Mô hình Hybrid

[cite_start]Hệ thống sử dụng kiến trúc lai (Hybrid) kết hợp giữa luật (Rule-based) và thư viện `dateparser`, `regex` để trích xuất thông tin với độ chính xác cao[cite: 748, 749, 756]:

- [cite_start]**Trích xuất thông tin:** Tự động nhận diện Tên sự kiện, Thời gian (Bắt đầu/Kết thúc), Địa điểm, Thời gian nhắc nhở [cite: 757-762].
- [cite_start]**Xử lý thời gian linh hoạt:** Hiểu các mốc thời gian tương đối như _"sáng mai"_, _"cuối tuần"_, _"thứ 2 tới"_, _"trong 15 phút nữa"_[cite: 763].
- [cite_start]**Hỗ trợ đa dạng:** Xử lý tốt văn bản tiếng Việt có dấu, không dấu, viết tắt[cite: 764].

### 2. Quản lý Sự kiện (CRUD)

- [cite_start]**Thêm mới:** Tự động tạo từ câu lệnh NLP hoặc nhập liệu thủ công[cite: 768].
- [cite_start]**Chỉnh sửa & Xóa:** Thao tác trực tiếp trên bảng danh sách sự kiện[cite: 769, 770].
- [cite_start]**Tìm kiếm nâng cao:** Lọc sự kiện theo Từ khóa, Địa điểm và Khoảng thời gian (Ngày/Tuần/Tháng)[cite: 772].

### 3. Hệ thống Nhắc nhở Thông minh

- [cite_start]**Cơ chế chạy ngầm:** Sử dụng `Background Thread` kiểm tra định kỳ mỗi 60 giây (hoặc tùy chỉnh) mà không làm treo ứng dụng[cite: 777].
- [cite_start]**Thông báo:** Hiển thị Popup và phát âm thanh cảnh báo (Windows Beep) khi đến giờ hẹn[cite: 778].

### 4. Lưu trữ & Xuất dữ liệu

- [cite_start]**Cơ sở dữ liệu SQLite:** Lưu trữ cục bộ, bảo mật và truy xuất nhanh[cite: 774].
- [cite_start]**Xuất file:** Hỗ trợ xuất lịch trình ra định dạng **JSON** và **ICS** (iCalendar) để tương thích với Google Calendar/Outlook[cite: 794].

---

## 🛠️ Công nghệ sử dụng

[cite_start]Dự án được xây dựng dựa trên các công nghệ và thư viện mã nguồn mở[cite: 887]:

| STT | Công nghệ / Thư viện | Phiên bản | Mục đích sử dụng                          |
| :-- | :------------------- | :-------- | :---------------------------------------- |
| 1   | **Python**           | 3.13.1    | Ngôn ngữ lập trình chính.                 |
| 2   | **tkinter**          | Built-in  | Thư viện lõi xây dựng GUI.                |
| 3   | **ttkbootstrap**     | 1.10.1    | Wrapper làm đẹp giao diện (Theme Flatly). |
| 4   | **sqlite3**          | Built-in  | Hệ quản trị cơ sở dữ liệu (Serverless).   |
| 5   | **dateparser**       | 1.2.0     | Phân tích ngày giờ từ ngôn ngữ tự nhiên.  |
| 6   | **unidecode**        | 1.3.8     | Chuẩn hóa tiếng Việt (xử lý không dấu).   |
| 7   | **threading**        | Built-in  | Xử lý đa luồng cho tính năng nhắc nhở.    |

---

## 🚀 Hướng dẫn Cài đặt & Sử dụng

### Yêu cầu hệ thống

- **Hệ điều hành:** Windows, macOS, hoặc Linux.
- [cite_start]**Python:** Phiên bản 3.13.1 trở lên[cite: 921].

### [cite_start]Các bước cài đặt [cite: 924-933]

1.  **Clone dự án về máy:**

    ```bash
    git clone [https://github.com/phong1221/TroLyCaNhan.git](https://github.com/phong1221/TroLyCaNhan.git)
    cd TroLyCaNhan
    ```

2.  **Tạo và kích hoạt môi trường ảo (Khuyến nghị):**

    - _Windows:_
      ```bash
      python -m venv venv
      venv\Scripts\activate
      ```
    - _Linux/macOS:_
      ```bash
      python3 -m venv venv
      source venv/bin/activate
      ```

3.  **Cài đặt các thư viện phụ thuộc:**

    ```bash
    pip install ttkbootstrap dateparser unidecode ics
    ```

4.  **Chạy ứng dụng:**
    ```bash
    python main.py
    ```

### Hướng dẫn sử dụng nhanh

- **Nhập liệu NLP:** Tại ô nhập liệu trên cùng, gõ câu lệnh và nhấn Enter hoặc nút **Thêm**.
  - _Ví dụ:_ `Họp team dự án lúc 14h chiều nay tại phòng họp 2`
  - _Ví dụ:_ `Đi đón con lúc 16h30, nhắc trước 15 phút`
- **Lọc lịch trình:** Sử dụng các nút **Hôm nay**, **Tuần này**, **Tháng này** để xem nhanh.
- **Xuất dữ liệu:** Chọn **Xuất JSON** hoặc **Xuất ICS** để sao lưu dữ liệu.

---

## 📂 Cấu trúc dự án

```text
TroLyCaNhan/
│
├── main.py                 # Điểm khởi chạy ứng dụng (Entry Point)
├── schedule.db             # Cơ sở dữ liệu SQLite (Tự động tạo)
│
├── core/                   # Tầng xử lý nghiệp vụ (Business Logic)
│   ├── __init__.py
│   ├── database.py         # Lớp truy cập dữ liệu (DAL)
│   ├── nlp_parser.py       # Module xử lý ngôn ngữ tự nhiên
│   ├── reminder.py         # Luồng xử lý nhắc nhở ngầm
│   └── exporter.py         # Module xuất file
│
└── gui/                    # Tầng giao diện (Presentation)
    ├── __init__.py
    └── main_window.py      # Cửa sổ chính và các Dialog
```
