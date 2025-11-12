import re
import dateparser
from datetime import datetime, timedelta
from unidecode import unidecode
from typing import Dict, Optional, Tuple, List

# --- Cấu hình DateParser ---
DATE_SETTINGS = {
    'DATE_ORDER': 'DMY',
    'PREFER_DATES_FROM': 'future',
    'TIMEZONE': 'Asia/Ho_Chi_Minh'
}

# --- Regex ---
# (Cải tiến 3 - v14.3) - Thêm regex cho các từ khóa kích hoạt, bao gồm "toi se"
TRIGGER_PATTERN = re.compile(
    r"^(nhac( toi| em)?|dat lich( gium)?|tao( gium)?( su kien)?|hen( gap)?|(toi|minh) se)\s+",
    re.IGNORECASE
)

REMINDER_PATTERN = re.compile(
    r"(nhac|bao)\s+truoc\s+(\d+)\s+(phut|p|gio|h|tieng)", re.IGNORECASE
)

# (Cải tiến 1) - Cập nhật regex địa điểm để xử lý dấu phẩy
LOCATION_PATTERN = re.compile(
    r"\s(o|tai)\s+"                # Bắt đầu bằng "o" hoặc "tai"
    r"([^,]+?(?:,\s*[^,]+?)*?)"    # Bắt các cụm có dấu phẩy (non-greedy)
    r"(?=(,|$|\s(luc|vao|nhac)))",  # Dừng lại khi gặp dấu phẩy, hết chuỗi, hoặc từ khóa thời gian/nhắc nhở
    re.IGNORECASE
)

# (v14.3) - Sửa lỗi dính chữ "p" (phút) vào event
TIME_PATTERNS = [
    # (Sửa đổi) Thêm (\s*p(hut)?)?
    re.compile(r"((\s(luc|vao))?\s+)?(\d{1,2}(:|h| gio)\d{1,2}(\s*p(hut)?)?)\s+(thu\s(\d|hai|ba|tu|nam|sau|bay|nhat))", re.IGNORECASE),
    re.compile(r"((\s(luc|vao))?\s+)?(\d{1,2}\s*(gio|h|g))\s+(sang|trua|chieu|toi)\s+(mai|kia|nay)", re.IGNORECASE),
    # (Sửa đổi) Thêm (\s*p(hut)?)?
    re.compile(r"((\s(luc|vao))?\s+)?(\d{1,2}(:|h| gio)\d{1,2}(\s*p(hut)?)?)", re.IGNORECASE),
    re.compile(r"((\s(luc|vao))?\s+)?(sang|trua|chieu|toi)\s+(mai|kia|nay)", re.IGNORECASE),
    re.compile(r"((\s(luc|vao))?\s+)?(cuoi tuan( nay| toi| sau)?)", re.IGNORECASE),
    re.compile(r"((\s(luc|vao))?\s+)?(thu\s(\d|hai|ba|tu|nam|sau|bay|nhat))", re.IGNORECASE),
    re.compile(r"((\s(luc|vao))?\s+)?(\d{1,2}\s*(gio|h|g))(?!\d)", re.IGNORECASE),
]

# --- Mapping buổi trong ngày ---
TIME_OF_DAY = {
    "sang": 8,
    "trua": 12,
    "chieu": 16,
    "toi": 19
}

def _normalize_time_string(time_str: str) -> str:
    """
    (v14.0) - Chuẩn hóa chuỗi thời gian, xử lý AM/PM và 'cuối tuần'.
    """
    s = re.sub(r"(\d+)h(\d+)", r"\1:\2", time_str, flags=re.IGNORECASE)
    s = re.sub(r"(\d+)h(?=\b|\s|$)", r"\1:00", s, flags=re.IGNORECASE)
    s = re.sub(r"(\d+)\s*(gio|g)\b", r"\1:00", s, flags=re.IGNORECASE)
    s = re.sub(r"cuoi tuan( sau| toi)?", "thu 7", s, flags=re.IGNORECASE)
    s = re.sub(r"\bsang\b", "AM", s, flags=re.IGNORECASE)
    s = re.sub(r"\b(trua|chieu|toi)\b", "PM", s, flags=re.IGNORECASE)
    return s

def _fallback_parse_time(normalized: str) -> Optional[datetime]:
    """
    (v14.1) - Xử lý fallback khi dateparser không parse được.
    (Cải tiến 4) - Ưu tiên tìm giờ cụ thể trước khi dùng giờ mặc định.
    """
    now = datetime.now()
    day_offset = 0
    hour = None
    minute = 0

    # (Cải tiến 4) - Ưu tiên tìm giờ cụ thể đã được chuẩn hóa (ví dụ: "9:00")
    hour_match = re.search(r"(\d{1,2}):(\d{1,2})", normalized)
    if hour_match:
        hour = int(hour_match.group(1))
        minute = int(hour_match.group(2))
    else:
        # Nếu không có giờ, mới dùng TIME_OF_DAY
        for k, v in TIME_OF_DAY.items():
            if k in normalized:
                hour = v
                break
        if hour is None: # Nếu không có gì, mặc định là 8h
            hour = 8

    if "mai" in normalized:
        day_offset = 1
    elif "kia" in normalized:
        day_offset = 2
    elif "cuoi tuan" in normalized or "thu 7" in normalized:
        day_offset = (5 - now.weekday()) % 7 + 1  # đến thứ 7
    
    return (now + timedelta(days=day_offset)).replace(hour=hour, minute=minute, second=0, microsecond=0)

def _extract_time(text: str, text_clean: str) -> Tuple[Optional[datetime], Optional[Tuple[int, int]]]:
    """
    (v14.1) - Trích xuất datetime và trả về SPAN (start, end)
    (Sử dụng _fallback_parse_time v14.1)
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
                if not date_obj:
                    date_obj = _fallback_parse_time(normalized_time_str) # v14.1
                if date_obj:
                    return date_obj, (match.start(), match.end())
            except Exception as e:
                print(f"Lỗi phân tích thời gian ('{normalized_time_str}'): {e}")
                
    return None, None

def process_nlp(text: str) -> dict:
    """
    (v14.2) - Logic dọn dẹp event (span-based, cải tiến).
    (Cải tiến) - Sửa lỗi dính dấu phẩy vào event.
    """
    result = {
        "event": None,
        "start_time": None,
        "end_time": None,
        "location": None,
        "reminder_minutes": 0
    }

    # Làm sạch chuỗi đầu vào
    text = re.sub(r'[!?…]+', '', text)
    text = re.sub(r'\s+', ' ', text).strip()

    original_text = text
    text_clean = unidecode(original_text).lower()
    # (Sửa đổi) - Chúng ta sẽ dùng text_clean cho tất cả regex để đảm bảo span đồng nhất
    # text_clean_no_punctuation = re.sub(r"[,.?!]", "", text_clean) 

    spans_to_remove: List[Tuple[int, int]] = []

    # --- (Cải tiến 3) 0. Từ khóa kích hoạt ---
    trigger_match = TRIGGER_PATTERN.search(text_clean) # Dùng text_clean
    if trigger_match and trigger_match.start() == 0:
        spans_to_remove.append((trigger_match.start(), trigger_match.end()))

    # --- 1. Nhắc nhở ---
    for reminder_match in REMINDER_PATTERN.finditer(text_clean): # Dùng text_clean
        value, unit = int(reminder_match.group(2)), reminder_match.group(3).lower()
        result["reminder_minutes"] = value * 60 if unit in ("gio", "h", "tieng") else value
        spans_to_remove.append((reminder_match.start(), reminder_match.end()))

    # --- 2. Địa điểm (chọn cụm dài nhất nếu nhiều) ---
    loc_matches = list(LOCATION_PATTERN.finditer(text_clean))
    if loc_matches:
        loc_match = max(loc_matches, key=lambda m: len(m.group(2)))
        location = original_text[loc_match.start(2):loc_match.end(2)].strip(" ,.")
        result["location"] = location
        spans_to_remove.extend([(m.start(), m.end()) for m in loc_matches])

    # --- 3. Thời gian ---
    date_obj, time_span = _extract_time(original_text, text_clean) # Dùng text_clean
    if date_obj:
        result["start_time"] = date_obj.isoformat()
        result["end_time"] = (date_obj + timedelta(hours=1)).isoformat()
        if time_span:
            spans_to_remove.append(time_span)

    # --- 4. Xây dựng Event (SỬA LỖI DẤU PHẨY) ---
    event_parts = []
    last_index = 0
    
    spans_to_remove.sort(key=lambda x: x[0])
    
    for start, end in spans_to_remove:
        if start > last_index:
            # (Cải tiến v14.2) - strip (làm sạch) từng phần trước khi thêm
            part = original_text[last_index:start].strip(" .,")
            if part: # Chỉ thêm nếu phần đó có nội dung
                event_parts.append(part)
        last_index = max(last_index, end)
    
    if last_index < len(original_text):
         # (Cải tiến v14.2) - strip (làm sạch) phần cuối cùng
        part = original_text[last_index:].strip(" .,")
        if part:
            event_parts.append(part)

    # (Cải tiến v14.2) - Nối các phần sạch lại bằng 1 khoảng trắng
    event = " ".join(event_parts) 
    
    # Dọn dẹp lại lần cuối (vẫn giữ lại để cho chắc)
    event = event.strip(" .,")
    event = re.sub(r"^(lúc|luc|vào|vao|ở|o|tại|tai)\s+", "", event, flags=re.IGNORECASE)
    event = re.sub(r"\s+(lúc|luc|vào|vao|ở|o|tại|tai)$", "", event, flags=re.IGNORECASE)
    event = re.sub(r"\s{2,}", " ", event).strip(" ,")
    
    result["event"] = event or None

    return result

# --- Test Cases ---
if __name__ == "__main__":
    try:
        from freezegun import freeze_time
        FROZEN_TIME = "2025-11-12 12:40:00"
        
        with freeze_time(FROZEN_TIME):
            print(f"Giả lập thời gian chạy: {datetime.now()} (Thứ 4, 12/11/2025 12:40)")
            print("--- (v14.1 - Đã cải tiến) ---")
            
            tests = [
                "Nhắc tôi họp nhóm lúc 10 giờ sáng mai ở phòng 302, nhắc trước 15 phút",
                "Đi tập gym lúc 2 giờ chiều nay",
                "Họp cuối tuần tại Cty XYZ",
                "Gặp khách hàng 10h30 thứ 6",
                "Ăn trưa 12h",
                "Sự kiện không có thời gian, chỉ nhắc nhở",
                "Lấy đồ ở siêu thị",
                "Đi họp ở tòa nhà A, phòng 302, nhắc trước 30 phút",
                # (Test Cải tiến 1 & 3)
                "Đặt lịch đi khám răng lúc 3h chiều mai", 
                # (Test Cải tiến 1)
                "Họp ở 123 Nguyễn Huệ, Quận 1 lúc 5h chiều nay",
            ]
            
            for i, t in enumerate(tests, 1):
                print(f"Test {i}: '{t}'")
                result = process_nlp(t)
                print(f"==> {result}")
                print("---")

    except ImportError:
        print("Lỗi: Vui lòng cài đặt 'freezegun' để chạy test này.")
        print("Chạy lệnh: pip install freezegun")