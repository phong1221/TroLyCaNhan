import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox, filedialog 

from queue import Queue, Empty 
import sys
import os
from datetime import datetime, timedelta
import calendar 

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core import database
from core import nlp_parser 
from core import exporter 
from core import reminder

class SearchDialog(ttk.Toplevel):
    def __init__(self, parent, callback):
        super().__init__(parent)
        self.title("Tìm kiếm nâng cao")
        self.geometry("450x450") 
        self.callback = callback 
        
        frame = ttk.Frame(self, padding=20)
        frame.pack(fill=BOTH, expand=True)

        ttk.Label(frame, text="Nhập các tiêu chí cần tìm:", font=("Arial", 11, "bold")).pack(anchor=W, pady=(0, 15))

        # 1. Tên
        ttk.Label(frame, text="Từ khóa (Tên sự kiện):").pack(anchor=W, pady=(0, 5))
        self.entry_keyword = ttk.Entry(frame)
        self.entry_keyword.pack(fill=X, pady=(0, 10))

        # 2. Địa điểm
        ttk.Label(frame, text="Địa điểm:").pack(anchor=W, pady=(0, 5))
        self.entry_location = ttk.Entry(frame)
        self.entry_location.pack(fill=X, pady=(0, 10))

        # 3. Khoảng thời gian
        date_frame = ttk.Labelframe(frame, text="Thời gian (YYYY-MM-DD HH:MM)", padding=10)
        date_frame.pack(fill=X, pady=(0, 20))

        ttk.Label(date_frame, text="Từ thời điểm:").pack(anchor=W)
        self.entry_from_date = ttk.Entry(date_frame)
        self.entry_from_date.pack(fill=X, pady=(0, 5))

        self.entry_from_date.insert(0, datetime.now().strftime("%Y-%m-%d 00:00"))

        ttk.Label(date_frame, text="Đến thời điểm:").pack(anchor=W)
        self.entry_to_date = ttk.Entry(date_frame)
        self.entry_to_date.pack(fill=X)
        self.entry_to_date.insert(0, datetime.now().strftime("%Y-%m-%d 23:59"))

        # Nút bấm
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=X, pady=(10, 0))
        
        ttk.Button(btn_frame, text="Tìm kiếm", command=self.on_search, bootstyle="primary", width=12).pack(side=RIGHT, padx=5)
        ttk.Button(btn_frame, text="Hủy", command=self.destroy, bootstyle="secondary", width=10).pack(side=RIGHT)

    def on_search(self):
        kw = self.entry_keyword.get().strip()
        loc = self.entry_location.get().strip()
        from_d = self.entry_from_date.get().strip()
        to_d = self.entry_to_date.get().strip()
        self.callback(kw, loc, from_d, to_d)
        self.destroy()

class MainWindow(ttk.Window):
    def __init__(self, queue: Queue): 
        super().__init__(themename="flatly")
        self.reminder_queue = queue 
        self.title("Trợ lý lịch trình cá nhân")
        self.geometry("1000x800") 
        
        main_frame = ttk.Frame(self, padding="15")
        main_frame.pack(fill=BOTH, expand=True)

        # --- 1. NLP Frame ---
        input_frame = ttk.Labelframe(main_frame, text="Thêm sự kiện (NLP)", padding="10")
        input_frame.pack(fill=X, pady=10)
        
        self.nlp_entry = ttk.Entry(input_frame, font=("Arial", 12))
        self.nlp_entry.pack(fill=X, ipady=5, padx=5, pady=5, side=LEFT, expand=True)
        self.nlp_entry.bind("<Return>", self.add_event_from_nlp)
        
        self.add_nlp_button = ttk.Button(input_frame, text="Thêm", command=self.add_event_from_nlp, bootstyle="primary")
        self.add_nlp_button.pack(side=LEFT, padx=5, fill=Y)

        # --- 2. Edit Frame ---
        edit_frame = ttk.Labelframe(main_frame, text="Chi tiết / Sửa sự kiện", padding="15")
        edit_frame.pack(fill=X, expand=False, pady=5)
        edit_frame.columnconfigure(1, weight=1) 
        edit_frame.columnconfigure(3, weight=1)

        ttk.Label(edit_frame, text="Tên sự kiện:").grid(row=0, column=0, sticky=W, padx=5, pady=5)
        self.entry_event = ttk.Entry(edit_frame)
        self.entry_event.grid(row=0, column=1, columnspan=3, sticky=EW, padx=5, pady=5)

        ttk.Label(edit_frame, text="Bắt đầu (ISO):").grid(row=1, column=0, sticky=W, padx=5, pady=5)
        self.entry_start = ttk.Entry(edit_frame)
        self.entry_start.grid(row=1, column=1, sticky=EW, padx=5, pady=5)

        ttk.Label(edit_frame, text="Kết thúc (ISO):").grid(row=1, column=2, sticky=W, padx=(20, 5), pady=5)
        self.entry_end = ttk.Entry(edit_frame)
        self.entry_end.grid(row=1, column=3, sticky=EW, padx=5, pady=5)

        ttk.Label(edit_frame, text="Địa điểm:").grid(row=2, column=0, sticky=W, padx=5, pady=5)
        self.entry_location = ttk.Entry(edit_frame)
        self.entry_location.grid(row=2, column=1, sticky=EW, padx=5, pady=5)

        ttk.Label(edit_frame, text="Nhắc (phút):").grid(row=2, column=2, sticky=W, padx=(20, 5), pady=5)
        self.entry_reminder = ttk.Entry(edit_frame)
        self.entry_reminder.grid(row=2, column=3, sticky=EW, padx=5, pady=5)
        self.entry_reminder.insert(0, "0") 

        # --- 3. Buttons Frame ---
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=X, pady=10)

        self.update_button = ttk.Button(button_frame, text="Lưu Sửa", command=self.update_event, bootstyle="success")
        self.update_button.pack(side=LEFT, padx=5, expand=True, fill=X)
        self.delete_button = ttk.Button(button_frame, text="Xóa", command=self.delete_event, bootstyle="danger")
        self.delete_button.pack(side=LEFT, padx=5, expand=True, fill=X)
        self.search_button = ttk.Button(button_frame, text="Tìm kiếm nâng cao", command=self.open_search_dialog, bootstyle="info")
        self.search_button.pack(side=LEFT, padx=5, expand=True, fill=X)
        
        # Export Buttons
        self.export_json_button = ttk.Button(button_frame, text="Xuất JSON", command=self.export_json, bootstyle="light-outline")
        self.export_json_button.pack(side=RIGHT, padx=5)
        self.export_ics_button = ttk.Button(button_frame, text="Xuất ICS", command=self.export_ics, bootstyle="light-outline")
        self.export_ics_button.pack(side=RIGHT, padx=5)

        # --- 4. Thanh Lọc Nhanh ---
        filter_frame = ttk.Frame(main_frame)
        filter_frame.pack(fill=X, pady=(0, 5))
        
        ttk.Label(filter_frame, text="Xem lịch theo:", font=("Arial", 10)).pack(side=LEFT, padx=(0, 10))
        ttk.Button(filter_frame, text="Hôm nay", command=lambda: self.quick_filter("today"), bootstyle="secondary-outline").pack(side=LEFT, padx=2)
        ttk.Button(filter_frame, text="Tuần này", command=lambda: self.quick_filter("week"), bootstyle="secondary-outline").pack(side=LEFT, padx=2)
        ttk.Button(filter_frame, text="Tháng này", command=lambda: self.quick_filter("month"), bootstyle="secondary-outline").pack(side=LEFT, padx=2)
        ttk.Button(filter_frame, text="Hiện tất cả", command=lambda: self.clear_fields(True), bootstyle="link").pack(side=LEFT, padx=10)

        # --- 5. Treeview ---
        tree_frame = ttk.Frame(main_frame, padding="0")
        tree_frame.pack(fill=BOTH, expand=True)
        columns = ("id", "event_name", "start_time", "end_time", "location", "reminder_minutes")
        
        scrollbar = ttk.Scrollbar(tree_frame, orient=VERTICAL, bootstyle="primary-round")
        self.tree = ttk.Treeview(tree_frame, columns=columns, show="headings", bootstyle="primary", yscrollcommand=scrollbar.set)
        
        scrollbar.config(command=self.tree.yview) 
        scrollbar.pack(side=RIGHT, fill=Y)
        self.tree.pack(side=LEFT, fill=BOTH, expand=True)

        self.tree.heading("id", text="ID")
        self.tree.column("id", width=40, anchor="center")
        self.tree.heading("event_name", text="Tên sự kiện")
        self.tree.column("event_name", width=250)
        self.tree.heading("start_time", text="Thời gian bắt đầu")
        self.tree.column("start_time", width=160)
        self.tree.heading("end_time", text="Thời gian kết thúc")
        self.tree.column("end_time", width=160)
        self.tree.heading("location", text="Địa điểm")
        self.tree.column("location", width=120)
        self.tree.heading("reminder_minutes", text="Nhắc (phút)")
        self.tree.column("reminder_minutes", width=80, anchor="center")
        
        self.tree.bind("<<TreeviewSelect>>", self.on_item_select)
        
        self.refresh_event_list()
        self.check_reminder_queue()

    # --- HÀM LỌC NHANH (CẬP NHẬT GIỜ CHÍNH XÁC) ---
    def quick_filter(self, mode):
        now = datetime.now()
        from_date = ""
        to_date = ""

        if mode == "today":
            # 00:00:00 -> 23:59:59 hôm nay
            from_date = now.strftime("%Y-%m-%d 00:00:00")
            to_date = now.strftime("%Y-%m-%d 23:59:59")
        
        elif mode == "week":
            # Đầu tuần (Thứ 2) -> Cuối tuần (Chủ nhật)
            start_week = now - timedelta(days=now.weekday()) 
            end_week = start_week + timedelta(days=6)
            from_date = start_week.strftime("%Y-%m-%d 00:00:00")
            to_date = end_week.strftime("%Y-%m-%d 23:59:59")
            
        elif mode == "month":
            start_month = now.replace(day=1)
            last_day = calendar.monthrange(now.year, now.month)[1]
            end_month = now.replace(day=last_day)
            
            from_date = start_month.strftime("%Y-%m-%d 00:00:00")
            to_date = end_month.strftime("%Y-%m-%d 23:59:59")

        self.perform_advanced_search(keyword="", location="", from_date=from_date, to_date=to_date)
        # messagebox.showinfo("Bộ lọc", f"Đang hiển thị lịch trình: {mode.upper()}\n({from_date} \n-> {to_date})")

    # --- CÁC HÀM TÌM KIẾM ---
    def open_search_dialog(self):
        SearchDialog(self, self.perform_advanced_search)

    def perform_advanced_search(self, keyword, location, from_date, to_date):
        try:
            events = database.search_events_advanced(keyword, location, from_date, to_date)
            if not events:
                messagebox.showinfo("Kết quả", "Không tìm thấy sự kiện nào trong khoảng thời gian này.")
                self.tree.delete(*self.tree.get_children())
            else:
                self.refresh_event_list(events) 
        except AttributeError:
            messagebox.showerror("Lỗi Database", "Vui lòng cập nhật file database.py")
        except Exception as e:
            messagebox.showerror("Lỗi", f"{e}")

    def export_json(self):
        filepath = filedialog.asksaveasfilename(title="Lưu file JSON", defaultextension=".json", filetypes=[("JSON Files", "*.json")])
        if not filepath: return 
        try:
            if exporter.export_to_json(filepath): messagebox.showinfo("Thành công", f"Đã xuất JSON: {filepath}")
        except Exception as e: messagebox.showerror("Lỗi", f"{e}")

    def export_ics(self):
        filepath = filedialog.asksaveasfilename(title="Lưu file Lịch", defaultextension=".ics", filetypes=[("iCalendar", "*.ics")])
        if not filepath: return 
        try:
            if exporter.export_to_ics(filepath): messagebox.showinfo("Thành công", f"Đã xuất ICS: {filepath}")
        except Exception as e: messagebox.showerror("Lỗi", f"{e}")

    def check_reminder_queue(self):
        try:
            event = self.reminder_queue.get(block=False) 
            messagebox.showinfo("Nhắc nhở!", f"Sự kiện: {event['event_name']}\nTại: {event.get('location', '')}\n(Trước {event['reminder_minutes']}p)")
        except Empty: pass 
        self.after(1000, self.check_reminder_queue)
            
    def add_event_from_nlp(self, event=None):
        text = self.nlp_entry.get()
        if not text: return messagebox.showwarning("Thiếu thông tin", "Nhập nội dung sự kiện.")
        try:
            data = nlp_parser.process_nlp(text)
            if not data.get("event"): return messagebox.showerror("Lỗi", "Không hiểu tên sự kiện.")
            if database.add_event(data["event"], data["start_time"], data["end_time"], data["location"], data["reminder_minutes"]):
                messagebox.showinfo("OK", f"Đã thêm: {data['event']}")
                self.refresh_event_list()
                self.nlp_entry.delete(0, END)
        except Exception as e: messagebox.showerror("Lỗi", f"{e}")

    def refresh_event_list(self, events=None):
        self.tree.delete(*self.tree.get_children())
        if events is None: events = database.get_all_events()
        for e in events:
            self.tree.insert("", "end", values=(e['id'], e['event_name'], e['start_time'] or "", e['end_time'] or "", e['location'] or "", e['reminder_minutes']))

    def on_item_select(self, event):
        sel = self.tree.selection()
        if not sel: return
        val = self.tree.item(sel[0])['values']
        self.clear_detail_fields()
        self.entry_event.insert(0, val[1]) 
        self.entry_start.insert(0, val[2] if val[2] else "")
        self.entry_end.insert(0, val[3] if val[3] else "")
        self.entry_location.insert(0, val[4] if val[4] else "")
        self.entry_reminder.insert(0, str(val[5]))

    def clear_detail_fields(self):
        for e in [self.entry_event, self.entry_start, self.entry_end, self.entry_location, self.entry_reminder]: e.delete(0, END)

    def clear_fields(self, clear_tree=True):
        self.nlp_entry.delete(0, END)
        self.clear_detail_fields()
        self.entry_reminder.insert(0, "0")
        if clear_tree:
            if self.tree.selection(): self.tree.selection_remove(self.tree.selection()[0])
            self.refresh_event_list()

    def update_event(self):
        sel = self.tree.selection()
        if not sel: return messagebox.showerror("Lỗi", "Chọn sự kiện để sửa.")
        eid = self.tree.item(sel[0])['values'][0]
        if database.update_event(eid, self.entry_event.get(), self.entry_start.get(), self.entry_end.get(), self.entry_location.get(), int(self.entry_reminder.get() or 0)):
            messagebox.showinfo("OK", "Đã cập nhật.")
            self.refresh_event_list()
            self.clear_fields(False)

    def delete_event(self):
        sel = self.tree.selection()
        if not sel: return messagebox.showerror("Lỗi", "Chọn sự kiện để xóa.")
        val = self.tree.item(sel[0])['values']
        if messagebox.askyesno("Xóa", f"Xóa: {val[1]}?"):
            if database.delete_event(val[0]):
                self.refresh_event_list()
                self.clear_fields(False)

if __name__ == "__main__":
    # 1. Khởi tạo Database
    database.init_db()
    
    # 2. Tạo kênh giao tiếp (Queue)
    main_queue = Queue()
    
    # 3. KHỞI CHẠY LUỒNG NHẮC NHỞ (Đây là phần còn thiếu)
    # Kiểm tra mỗi 5 giây cho nhanh (mặc định là 60s)
    reminder_thread = reminder.ReminderThread(queue=main_queue, check_interval_seconds=5)
    reminder_thread.start()
    print("--- Hệ thống nhắc nhở đã bắt đầu chạy ngầm ---")

    # 4. Chạy giao diện chính
    try:
        app = MainWindow(queue=main_queue)
        app.mainloop()
    finally:
        # 5. Dừng luồng khi tắt app để không bị treo máy
        print("Đang dừng hệ thống...")
        reminder_thread.stop()