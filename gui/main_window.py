import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox, simpledialog
from tkinter import filedialog # <-- IMPORT MỚI

from queue import Queue, Empty 
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core import database
from core import nlp_parser 
from core import exporter # <-- IMPORT MỚI

class MainWindow(ttk.Window):
    def __init__(self, queue: Queue): 
        super().__init__(themename="flatly")
        self.reminder_queue = queue 
        self.title("Trợ lý lịch trình cá nhân")
        self.geometry("950x750") # Nới rộng form một chút cho thoáng
        
        main_frame = ttk.Frame(self, padding="15")
        main_frame.pack(fill=BOTH, expand=True)

        # --- 1. Frame Nhập liệu (NLP) ---
        input_frame = ttk.Labelframe(main_frame, text="Thêm sự kiện (NLP)", padding="10")
        input_frame.pack(fill=X, pady=10)
        
        self.nlp_entry = ttk.Entry(input_frame, font=("Arial", 12))
        self.nlp_entry.pack(fill=X, ipady=5, padx=5, pady=5, side=LEFT, expand=True)
        self.nlp_entry.bind("<Return>", self.add_event_from_nlp)
        
        self.add_nlp_button = ttk.Button(input_frame, text="Thêm", command=self.add_event_from_nlp, bootstyle="primary")
        self.add_nlp_button.pack(side=LEFT, padx=5, fill=Y)

        # --- 2. Khung Sửa/Chi tiết (SỬA LẠI LAYOUT BẰNG GRID) ---
        edit_frame = ttk.Labelframe(main_frame, text="Chi tiết / Sửa sự kiện", padding="15")
        edit_frame.pack(fill=X, expand=False, pady=5)
        
        # Cấu hình cột để các ô nhập liệu giãn đều đẹp mắt
        edit_frame.columnconfigure(1, weight=1) 
        edit_frame.columnconfigure(3, weight=1)

        # Dòng 1: Tên sự kiện (Trải dài hết chiều ngang)
        ttk.Label(edit_frame, text="Tên sự kiện:").grid(row=0, column=0, sticky=W, padx=5, pady=5)
        self.entry_event = ttk.Entry(edit_frame)
        self.entry_event.grid(row=0, column=1, columnspan=3, sticky=EW, padx=5, pady=5)

        # Dòng 2: Bắt đầu và Kết thúc (Chia đôi màn hình)
        ttk.Label(edit_frame, text="Bắt đầu (ISO):").grid(row=1, column=0, sticky=W, padx=5, pady=5)
        self.entry_start = ttk.Entry(edit_frame)
        self.entry_start.grid(row=1, column=1, sticky=EW, padx=5, pady=5)

        ttk.Label(edit_frame, text="Kết thúc (ISO):").grid(row=1, column=2, sticky=W, padx=(20, 5), pady=5)
        self.entry_end = ttk.Entry(edit_frame)
        self.entry_end.grid(row=1, column=3, sticky=EW, padx=5, pady=5)

        # Dòng 3: Địa điểm và Nhắc nhở
        ttk.Label(edit_frame, text="Địa điểm:").grid(row=2, column=0, sticky=W, padx=5, pady=5)
        self.entry_location = ttk.Entry(edit_frame)
        self.entry_location.grid(row=2, column=1, sticky=EW, padx=5, pady=5)

        ttk.Label(edit_frame, text="Nhắc (phút):").grid(row=2, column=2, sticky=W, padx=(20, 5), pady=5)
        self.entry_reminder = ttk.Entry(edit_frame)
        self.entry_reminder.grid(row=2, column=3, sticky=EW, padx=5, pady=5)
        self.entry_reminder.insert(0, "0") # Giá trị mặc định

        # --- 3. Nút bấm ---
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=X, pady=10)

        # Gom nhóm nút thao tác
        self.update_button = ttk.Button(button_frame, text="Lưu Sửa", command=self.update_event, bootstyle="success")
        self.update_button.pack(side=LEFT, padx=5, expand=True, fill=X)
        self.delete_button = ttk.Button(button_frame, text="Xóa", command=self.delete_event, bootstyle="danger")
        self.delete_button.pack(side=LEFT, padx=5, expand=True, fill=X)
        self.search_button = ttk.Button(button_frame, text="Tìm kiếm", command=self.search_event, bootstyle="info")
        self.search_button.pack(side=LEFT, padx=5, expand=True, fill=X)
        self.clear_button = ttk.Button(button_frame, text="Làm mới", command=self.clear_fields, bootstyle="secondary")
        self.clear_button.pack(side=LEFT, padx=5, expand=True, fill=X)
        
        # --- 4. Khung Export ---
        export_frame = ttk.Frame(main_frame)
        export_frame.pack(fill=X, pady=(0, 10))

        self.export_json_button = ttk.Button(export_frame, text="Xuất JSON", command=self.export_json, bootstyle="light")
        self.export_json_button.pack(side=LEFT, padx=5, expand=True, fill=X)
        self.export_ics_button = ttk.Button(export_frame, text="Xuất ICS (Lịch)", command=self.export_ics, bootstyle="light")
        self.export_ics_button.pack(side=LEFT, padx=5, expand=True, fill=X)

        # --- 5. Bảng hiển thị (Treeview) ---
        tree_frame = ttk.Frame(main_frame, padding="0")
        tree_frame.pack(fill=BOTH, expand=True)
        columns = ("id", "event_name", "start_time", "end_time", "location", "reminder_minutes")
        
        # Thêm Scrollbar
        scrollbar = ttk.Scrollbar(tree_frame, orient=VERTICAL, bootstyle="primary-round")
        self.tree = ttk.Treeview(tree_frame, columns=columns, show="headings", bootstyle="primary", yscrollcommand=scrollbar.set)
        
        scrollbar.config(command=self.tree.yview) # Link scrollbar với treeview
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

    # --- (HÀM MỚI CHO EXPORT) ---

    def export_json(self):
        # Mở hộp thoại "Lưu file"
        filepath = filedialog.asksaveasfilename(
            title="Lưu file JSON",
            defaultextension=".json",
            filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")]
        )
        if not filepath:
            return # Người dùng nhấn Cancel

        try:
            success = exporter.export_to_json(filepath)
            if success:
                messagebox.showinfo("Thành công", f"Đã xuất dữ liệu JSON thành công!\nTại: {filepath}")
            else:
                messagebox.showerror("Lỗi", "Không thể xuất file JSON.")
        except Exception as e:
            messagebox.showerror("Lỗi", f"Đã xảy ra lỗi: {e}")

    def export_ics(self):
        # Mở hộp thoại "Lưu file"
        filepath = filedialog.asksaveasfilename(
            title="Lưu file Lịch (ICS)",
            defaultextension=".ics",
            filetypes=[("iCalendar Files", "*.ics"), ("All Files", "*.*")]
        )
        if not filepath:
            return # Người dùng nhấn Cancel

        try:
            success = exporter.export_to_ics(filepath)
            if success:
                messagebox.showinfo("Thành công", f"Đã xuất dữ liệu Lịch (ICS) thành công!\nTại: {filepath}")
            else:
                messagebox.showerror("Lỗi", "Không thể xuất file ICS.")
        except Exception as e:
            messagebox.showerror("Lỗi", f"Đã xảy ra lỗi: {e}")

    # --- (Các hàm còn lại giữ nguyên) ---

    def check_reminder_queue(self):
        try:
            event = self.reminder_queue.get(block=False) 
            event_name = event['event_name']
            location = event.get('location', 'không có')
            minutes = event['reminder_minutes']
            message = (f"Sự kiện: {event_name}\n\n"
                       f"Địa điểm: {location}\n\n"
                       f"(Nhắc trước {minutes} phút)")
            messagebox.showinfo("Thông báo nhắc nhở!", message)
        except Empty:
            pass 
        except Exception as e:
            print(f"Lỗi queue pop-up: {e}")
        self.after(1000, self.check_reminder_queue)
            
    def add_event_from_nlp(self, event=None):
        text = self.nlp_entry.get()
        if not text:
            messagebox.showwarning("Thiếu thông tin", "Vui lòng nhập yêu cầu của bạn.")
            return
        try:
            data_dict = nlp_parser.process_nlp(text)
            if not data_dict.get("event"):
                messagebox.showerror("Lỗi NLP", "Không thể hiểu được tên sự kiện.")
                return
            event_id = database.add_event(
                event_name=data_dict["event"],
                start_time=data_dict["start_time"],
                end_time=data_dict["end_time"],
                location=data_dict["location"],
                reminder_minutes=data_dict["reminder_minutes"]
            )
            if event_id:
                messagebox.showinfo("Thành công", f"Đã thêm sự kiện: '{data_dict['event']}'")
                self.refresh_event_list()
                self.nlp_entry.delete(0, "end")
            else:
                messagebox.showerror("Lỗi CSDL", "Không thể lưu sự kiện vào CSDL.")
        except Exception as e:
            messagebox.showerror("Lỗi nghiêm trọng", f"Đã xảy ra lỗi: {e}")

    def refresh_event_list(self, events=None):
        self.tree.delete(*self.tree.get_children())
        if events is None:
            events = database.get_all_events()
        for event in events:
            self.tree.insert("", "end", values=(
                event['id'],
                event['event_name'],
                event['start_time'] if event['start_time'] else "",
                event['end_time'] if event['end_time'] else "", 
                event['location'] if event['location'] else "",
                event['reminder_minutes']
            ))

    def on_item_select(self, event):
        selected_items = self.tree.selection()
        if not selected_items:
            return
        item = self.tree.item(selected_items[0])
        values = item['values']
        self.clear_detail_fields()
        self.entry_event.insert(0, values[1]) 
        self.entry_start.insert(0, values[2] if values[2] else "")
        self.entry_end.insert(0, values[3] if values[3] else "")
        self.entry_location.insert(0, values[4] if values[4] else "")
        self.entry_reminder.insert(0, values[5])

    def clear_detail_fields(self):
        self.entry_event.delete(0, END)
        self.entry_start.delete(0, END)
        self.entry_end.delete(0, END)
        self.entry_location.delete(0, END)
        self.entry_reminder.delete(0, END)

    def clear_fields(self, clear_tree_selection=True):
        self.nlp_entry.delete(0, END)
        self.clear_detail_fields()
        if clear_tree_selection:
            if self.tree.selection():
                self.tree.selection_remove(self.tree.selection()[0])
            self.refresh_event_list()

    def update_event(self):
        selected_items = self.tree.selection()
        if not selected_items:
            messagebox.showerror("Lỗi", "Bạn phải chọn một sự kiện trên bảng để sửa!")
            return
        item = self.tree.item(selected_items[0])
        event_id = item['values'][0]
        event_name = self.entry_event.get()
        start_time = self.entry_start.get() or None
        end_time = self.entry_end.get() or None
        location = self.entry_location.get() or None
        reminder = int(self.entry_reminder.get() or 0)
        if not event_name:
            messagebox.showwarning("Lỗi Sửa", "Tên sự kiện không được để trống.")
            return
        success = database.update_event(event_id, event_name, start_time, end_time, location, reminder)
        if success:
            messagebox.showinfo("Thành công", f"Đã cập nhật sự kiện (ID: {event_id})")
            self.refresh_event_list()
            self.clear_fields(clear_tree_selection=False)
        else:
            messagebox.showerror("Lỗi", "Không thể cập nhật sự kiện.")

    def delete_event(self):
        selected_items = self.tree.selection()
        if not selected_items:
            messagebox.showerror("Lỗi", "Bạn phải chọn một sự kiện để xóa!")
            return
        item = self.tree.item(selected_items[0])
        event_id = item['values'][0]
        event_name = item['values'][1]
        if messagebox.askyesno("Xác nhận xóa", f"Bạn có chắc muốn xóa sự kiện:\n'{event_name}' (ID: {event_id})?"):
            success = database.delete_event(event_id)
            if success:
                messagebox.showinfo("Thành công", f"Đã xóa sự kiện (ID: {event_id})")
                self.refresh_event_list()
                self.clear_fields(clear_tree_selection=False)
            else:
                messagebox.showerror("Lỗi", "Không thể xóa sự kiện.")
    
    def search_event(self):
        keyword = simpledialog.askstring("Tìm kiếm", "Nhập từ khóa cần tìm (tên hoặc địa điểm):")
        if keyword:
            events = database.search_events(keyword)
            if not events:
                messagebox.showinfo("Kết quả", "Không tìm thấy sự kiện nào.")
            self.refresh_event_list(events)

if __name__ == "__main__":
    database.init_db()
    test_q = Queue()
    app = MainWindow(queue=test_q)
    app.mainloop()