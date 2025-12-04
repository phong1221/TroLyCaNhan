import re
import dateparser
from datetime import datetime, timedelta
from unidecode import unidecode
from typing import Dict, Optional, Tuple, List


DATE_SETTINGS = {
    'DATE_ORDER': 'DMY',
    'PREFER_DATES_FROM': 'future',
    'TIMEZONE': 'Asia/Ho_Chi_Minh'
}

#Thêm regex cho các từ khóa kích hoạt
TRIGGER_PATTERN = re.compile(
    r"^(nhac( toi| em)?|dat lich( gium)?|tao( gium)?( su kien)?|hen( gap)?|(toi|minh) se)\s+",
    re.IGNORECASE
)

REMINDER_PATTERN = re.compile(
    r"(nhac|bao)\s+truoc\s+(\d+)\s*(phut|p|gio|h|tieng)", re.IGNORECASE
)

# Cập nhật regex địa điểm để xử lý dấu phẩy
LOCATION_PATTERN = re.compile(
    r"\s(o|tai)\s+"                # Bắt đầu bằng "o" hoặc "tai"
    r"([^,]+?(?:,\s*[^,]+?)*?)"    # Bắt các cụm có dấu phẩy (non-greedy)
    r"(?=(,|$|\s(luc|vao|nhac)))",  # Dừng lại khi gặp dấu phẩy, hết chuỗi, hoặc từ khóa thời gian/nhắc nhở
    re.IGNORECASE
)

#  - Thêm Pattern ưu tiên lên đầu
TIME_PATTERNS = [
    # Cấu trúc: [Số] [dấu cách?] [giờ/h/g] [dấu cách] [Số] [dấu cách?] [phút/p]
    re.compile(r"((\s(luc|vao))?\s+)?(\d{1,2}\s*(gio|h|g)\s+\d{1,2}\s*(phut|p))", re.IGNORECASE), 

    # Các Pattern cũ (đã được sắp xếp lại độ ưu tiên)
    re.compile(r"((\s(luc|vao))?\s+)?(\d{1,2}(:|h| gio)\d{1,2}(\s*p(hut)?)?)\s+(thu\s(\d|hai|ba|tu|nam|sau|bay|nhat))", re.IGNORECASE),
    re.compile(r"((\s(luc|vao))?\s+)?(\d{1,2}\s*(gio|h|g))\s+(sang|trua|chieu|toi)\s+(mai|kia|nay)", re.IGNORECASE),
    
    # Pattern HH:MM (vẫn giữ nguyên nhưng độ ưu tiên thấp hơn cái mới ở trên)
    re.compile(r"((\s(luc|vao))?\s+)?(\d{1,2}(:|h| gio)\d{1,2}(\s*p(hut)?)?)", re.IGNORECASE),
    
    re.compile(r"((\s(luc|vao))?\s+)?(sang|trua|chieu|toi)\s+(mai|kia|nay)", re.IGNORECASE),
    re.compile(r"((\s(luc|vao))?\s+)?(cuoi tuan( nay| toi| sau)?)", re.IGNORECASE),
    re.compile(r"((\s(luc|vao))?\s+)?(thu\s(\d|hai|ba|tu|nam|sau|bay|nhat))", re.IGNORECASE),
    re.compile(r"((\s(luc|vao))?\s+)?(\d{1,2}\s*(gio|h|g))(?!\d)", re.IGNORECASE),
]


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
    # Chuẩn hóa "19 gio 50 phut" thành "19:50" để dateparser hiểu
    # Thay thế "gio", "phut" bằng dấu ":"
    s = re.sub(r"(\d+)\s*(gio|h|g)\s*(\d+)\s*(phut|p)", r"\1:\3", time_str, flags=re.IGNORECASE)
    
    s = re.sub(r"(\d+)h(\d+)", r"\1:\2", s, flags=re.IGNORECASE)
    s = re.sub(r"(\d+)h(?=\b|\s|$)", r"\1:00", s, flags=re.IGNORECASE)
    s = re.sub(r"(\d+)\s*(gio|g)\b", r"\1:00", s, flags=re.IGNORECASE)
    s = re.sub(r"cuoi tuan( sau| toi)?", "thu 7", s, flags=re.IGNORECASE)
    s = re.sub(r"\bsang\b", "AM", s, flags=re.IGNORECASE)
    s = re.sub(r"\b(trua|chieu|toi)\b", "PM", s, flags=re.IGNORECASE)
    return s

def _fallback_parse_time(normalized: str) -> Optional[datetime]:
    """
    (v14.1) - Xử lý fallback khi dateparser không parse được.
    """
    now = datetime.now()
    day_offset = 0
    hour = None
    minute = 0

    # Ưu tiên tìm giờ cụ thể đã được chuẩn hóa 
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
                    date_obj = _fallback_parse_time(normalized_time_str)
                if date_obj:
                    return date_obj, (match.start(), match.end())
            except Exception as e:
                print(f"Lỗi phân tích thời gian ('{normalized_time_str}'): {e}")
                
    return None, None

def process_nlp(text: str) -> dict:
    """
    (v14.2) - Logic dọn dẹp event (span-based, cải tiến).
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

    spans_to_remove: List[Tuple[int, int]] = []


    trigger_match = TRIGGER_PATTERN.search(text_clean)
    if trigger_match and trigger_match.start() == 0:
        spans_to_remove.append((trigger_match.start(), trigger_match.end()))

    # --- 1. Nhắc nhở ---
    for reminder_match in REMINDER_PATTERN.finditer(text_clean):
        value, unit = int(reminder_match.group(2)), reminder_match.group(3).lower()
        result["reminder_minutes"] = value * 60 if unit in ("gio", "h", "tieng") else value
        spans_to_remove.append((reminder_match.start(), reminder_match.end()))

    # --- 2. Địa điểm ---
    loc_matches = list(LOCATION_PATTERN.finditer(text_clean))
    if loc_matches:
        loc_match = max(loc_matches, key=lambda m: len(m.group(2)))
        location = original_text[loc_match.start(2):loc_match.end(2)].strip(" ,.")
        result["location"] = location
        spans_to_remove.extend([(m.start(), m.end()) for m in loc_matches])

    # --- 3. Thời gian ---
    date_obj, time_span = _extract_time(original_text, text_clean)
    if date_obj:
        # Dùng strftime để format theo ý muốn (bỏ chữ T)
        result["start_time"] = date_obj.strftime("%Y-%m-%d %H:%M:%S")
        result["end_time"] = (date_obj + timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")
        if time_span:
            spans_to_remove.append(time_span)

    # --- 4. Xây dựng Event ---
    event_parts = []
    last_index = 0
    
    spans_to_remove.sort(key=lambda x: x[0])
    
    for start, end in spans_to_remove:
        if start > last_index:
            part = original_text[last_index:start].strip(" .,")
            if part:
                event_parts.append(part)
        last_index = max(last_index, end)
    
    if last_index < len(original_text):
        part = original_text[last_index:].strip(" .,")
        if part:
            event_parts.append(part)

    event = " ".join(event_parts) 
    
    # Dọn dẹp lại lần cuối
    event = event.strip(" .,")
    event = re.sub(r"^(lúc|luc|vào|vao|ở|o|tại|tai)\s+", "", event, flags=re.IGNORECASE)
    event = re.sub(r"\s+(lúc|luc|vào|vao|ở|o|tại|tai)$", "", event, flags=re.IGNORECASE)
    event = re.sub(r"\s{2,}", " ", event).strip(" ,")
    
    result["event"] = event or None

    return result

# --- Test Cases ---
if __name__ == "__main__":
    tests = [
        "nhắc tôi họp vào lúc 19 giờ 50 phút nhắc trước 1 phút",
        "Nhắc tôi đi họp lúc 14h, nhắc trước 15p",
        "Học bài nhắc trước 30 phút",
        "Đi đá banh lúc 17h 30p"
    ]
    for t in tests:
        print(f"Input: {t}")
        print(f"Output: {process_nlp(t)}")
        print("-" * 20)