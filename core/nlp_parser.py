import re
import dateparser
from datetime import datetime
from unidecode import unidecode
from typing import Dict, Optional, Tuple, List

# --- Cấu hình DateParser ---
DATE_SETTINGS = {
    'DATE_ORDER': 'DMY',
    'PREFER_DATES_FROM': 'future',
    'TIMEZONE': 'Asia/Ho_Chi_Minh'
}

# --- Regex ---
REMINDER_PATTERN = re.compile(
    r"(nhac|bao)\s+truoc\s+(\d+)\s+(phut|p|gio|h|tieng)", re.IGNORECASE
)

# (v13.7) SỬA LỖI: Quay lại pattern của v13.5 (xử lý dấu phẩy)
LOCATION_PATTERN = re.compile(
    r"\s(o|tai)\s+([^,]+?)(?=(,|$|\s(luc|vao|nhac)))", re.IGNORECASE
)

TIME_PATTERNS = [
    re.compile(r"((\s(luc|vao))?\s+)?(\d{1,2}(:|h| gio)\d{1,2})\s+(thu\s(\d|hai|ba|tu|nam|sau|bay|nhat))", re.IGNORECASE),
    re.compile(r"((\s(luc|vao))?\s+)?(\d{1,2}\s*(gio|h|g))\s+(sang|trua|chieu|toi)\s+(mai|kia|nay)", re.IGNORECASE),
    re.compile(r"((\s(luc|vao))?\s+)?(\d{1,2}(:|h| gio)\d{1,2})", re.IGNORECASE),
    re.compile(r"((\s(luc|vao))?\s+)?(sang|trua|chieu|toi)\s+(mai|kia|nay)", re.IGNORECASE),
    re.compile(r"((\s(luc|vao))?\s+)?(cuoi tuan( nay| toi)?)", re.IGNORECASE),
    re.compile(r"((\s(luc|vao))?\s+)?(thu\s(\d|hai|ba|tu|nam|sau|bay|nhat))", re.IGNORECASE),
    re.compile(r"((\s(luc|vao))?\s+)?(\d{1,2}\s*(gio|h|g))(?!\d)", re.IGNORECASE),
]

def _normalize_time_string(time_str: str) -> str:
    """
    (v13.7) - Chuẩn hóa chuỗi thời gian, xử lý AM/PM và "cuối tuần".
    """
    s = re.sub(r"(\d+)h(\d+)", r"\1:\2", time_str, flags=re.IGNORECASE)
    s = re.sub(r"(\d+)h(?=\b|\s|$)", r"\1:00", s, flags=re.IGNORECASE)
    s = re.sub(r"(\d+)\s*(gio|g)\b", r"\1:00", s, flags=re.IGNORECASE)
    s = re.sub(r"cuoi tuan", "thu 7", s, flags=re.IGNORECASE)
    s = re.sub(r"\bsang\b", "AM", s, flags=re.IGNORECASE)
    s = re.sub(r"\b(trua|chieu|toi)\b", "PM", s, flags=re.IGNORECASE)
    return s

def _extract_time(text: str, text_clean: str) -> Tuple[Optional[datetime], Optional[Tuple[int, int]]]:
    """
    (v13.7) - Trích xuất datetime và trả về SPAN (start, end)
    """
    for pattern in TIME_PATTERNS:
        match = pattern.search(text_clean)
        if match:
            original_time_str = text[match.start():match.end()]
            unidecoded_time_str = text_clean[match.start():match.end()]
            cleaned_time_str = re.sub(r"^(luc|vao)\s+", "", unidecoded_time_str, flags=re.IGNORECASE).strip()
            normalized_time_str = _normalize_time_string(cleaned_time_str)
            
            try:
                date_obj = dateparser.parse(normalized_time_str,
                                            languages=['vi'],
                                            settings=DATE_SETTINGS)
                if date_obj:
                    # Trả về (start, end) của match
                    return date_obj, (match.start(), match.end())
            except Exception as e:
                print(f"Lỗi phân tích thời gian ('{normalized_time_str}'): {e}")
                
    return None, None

def process_nlp(text: str) -> dict:
    """
    (v13.7) - Logic dọn dẹp event (span-based).
    """
    result = {
        "event": None,
        "start_time": None,
        "end_time": None,
        "location": None,
        "reminder_minutes": 0
    }

    original_text = text
    # (v13.7) Dùng 2 bản clean: 1 bản không dấu phẩy (cho time/reminder), 1 bản có (cho location)
    text_clean = unidecode(original_text).lower()
    text_clean_no_punctuation = re.sub(r"[,.?!]", "", text_clean)

    # Mảng chứa các đoạn (start, end) cần xóa
    spans_to_remove: List[Tuple[int, int]] = []

    # --- 1. Nhắc nhở ---
    reminder_match = REMINDER_PATTERN.search(text_clean_no_punctuation)
    if reminder_match:
        value, unit = int(reminder_match.group(2)), reminder_match.group(3).lower()
        result["reminder_minutes"] = value * 60 if unit in ("gio", "h", "tieng") else value
        spans_to_remove.append((reminder_match.start(), reminder_match.end()))

    # --- 2. Địa điểm ---
    # (v13.7) Dùng text_clean (có dấu phẩy) cho location
    loc_match = LOCATION_PATTERN.search(text_clean) 
    if loc_match:
        location = original_text[loc_match.start(2):loc_match.end(2)].strip(" ,.")
        result["location"] = location
        spans_to_remove.append((loc_match.start(), loc_match.end()))

    # --- 3. Thời gian ---
    # (v13.7) Dùng text_clean_no_punctuation
    date_obj, time_span = _extract_time(original_text, text_clean_no_punctuation)
    if date_obj:
        result["start_time"] = date_obj.isoformat()
        if time_span:
            spans_to_remove.append(time_span)

    # --- 4. Xây dựng Event ---
    event_parts = []
    last_index = 0
    
    spans_to_remove.sort(key=lambda x: x[0])
    
    for start, end in spans_to_remove:
        if start > last_index:
            event_parts.append(original_text[last_index:start])
        last_index = max(last_index, end) # Tránh overlap
    
    if last_index < len(original_text):
        event_parts.append(original_text[last_index:])

    # Ghép lại và dọn dẹp
    event = "".join(event_parts)
    event = event.strip(" .,")
    event = re.sub(r"^(lúc|luc|vào|vao|ở|o|tại|tai)\s+", "", event, flags=re.IGNORECASE)
    event = re.sub(r"\s+(lúc|luc|vào|vao|ở|o|tại|tai)$", "", event, flags=re.IGNORECASE)
    event = event.strip(" ,") 
    event = re.sub(r"\s{2,}", " ", event).strip()
    
    result["event"] = event

    return result

# --- Test Cases ---
if __name__ == "__main__":
    try:
        from freezegun import freeze_time
        FROZEN_TIME = "2025-11-12 12:40:00"
        
        with freeze_time(FROZEN_TIME):
            print(f"Gia lap thoi gian chay: {datetime.now()} (Thu 4, 12/11/2025 12:40)")
            print("--- (v13.7 - Đã sửa lỗi location) ---")
            
            tests = [
                "Nhắc tôi họp nhóm lúc 10 giờ sáng mai ở phòng 302, nhắc trước 15 phút",
                "di tap gym luc 2 gio",
                "Họp cuối tuần tại Cty XYZ",
                "gặp khách hàng 10h30 thứ 6",
                "Ăn trưa 12h",
                "Sự kiện không có thời gian, chỉ nhắc nhở",
                "Lấy đồ ở siêu thị"
            ]
            
            for i, t in enumerate(tests, 1):
                print(f"Test {i}: '{t}'")
                result = process_nlp(t)
                print(f"==> {result}")
                print("---")

    except ImportError:
        print("Lỗi: Vui lòng cài đặt 'freezegun' để chạy test này.")
        print("Chạy lệnh: pip install freezegun")