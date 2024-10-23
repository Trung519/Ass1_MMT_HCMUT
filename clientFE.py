from tkinter import Tk, messagebox, filedialog, Button, Frame, LEFT, TOP, X, BOTH, Label, RIGHT
import sys
import os
import hashlib
from util import calculate_piece_length, hash_file_pieces
from api import *

import math


class ClientUI:
    def __init__(self):
        self.root = Tk()
        self.root.geometry('800x600')
        self.root.title('BTL Mạng Máy Tính')
        # Tạo frame đầu trang
        self.head_frame = Frame(self.root, bg='#158aff',
                                highlightbackground='white', highlightthickness=1)

        # Nút để mở menu
        self.toggle_btn = Button(self.head_frame, text='☰', bg='#158aff', fg='white', font=('Bold', 20),
                                 activebackground='#158aff', activeforeground='white', command=self.toggle_menu)
        self.toggle_btn.pack(side=LEFT)

        self.head_frame.pack(side=TOP, fill=X)
        self.head_frame.pack_propagate(False)
        self.head_frame.configure(height=50)

        # Frame chính để hiển thị nội dung động
        self.content_frame = Frame(self.root, bg='white')
        self.content_frame.pack(fill=BOTH, expand=True)

# Hàm để chuyển đổi menu

    def toggle_menu(self):
        def collapse_toggle_menu():
            toggle_menu_fm.destroy()
            self.toggle_btn.config(text='☰')
            self.toggle_btn.config(command=self.toggle_menu)

        toggle_menu_fm = Frame(self.root, bg='#158aff')

        # Nút MetaInfo File
        metainfo_btn = Button(toggle_menu_fm, text='MetaInfo File', font=('Bold, 16'), bd=0, bg='#158aff', fg='white',
                              activebackground='#158aff', activeforeground='white', command=self.show_metainfo_content
                              )
        metainfo_btn.place(x=20, y=20)

        # Nút Downloads
        download_btn = Button(toggle_menu_fm, text='Downloads', font=('Bold, 16'), bd=0, bg='#158aff', fg='white',
                              activebackground='#158aff', activeforeground='white', command=self.show_download_content
                              )
        download_btn.place(x=20, y=60)

        # Nút Upload
        upload_btn = Button(toggle_menu_fm, text='Upload', font=('Bold, 16'), bd=0, bg='#158aff', fg='white',
                            activebackground='#158aff', activeforeground='white', command=self.show_upload_content
                            )
        upload_btn.place(x=20, y=100)

        windown_height = self.root.winfo_height()

        toggle_menu_fm.place(x=0, y=50, height=windown_height, width=200)
        self.toggle_btn.config(text='X')
        self.toggle_btn.config(command=collapse_toggle_menu)

    # Hàm hiển thị nội dung MetaInfo File

    def show_metainfo_content(self):
        # Xóa nội dung cũ
        list_metainfo = get_all_metainfo_file()
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        # Thêm tiêu đề
        label = Label(self.content_frame, text="MetaInfo File Content", font=(
            "Arial", 16), bg="white")
        label.pack(pady=10)

        # Duyệt qua danh sách MetaInfo và hiển thị mỗi item
        for idx, metainfo in enumerate(list_metainfo, start=1):
            # Lấy thông tin cần hiển thị, có thể tuỳ chỉnh theo cấu trúc metainfo
            info_text = f"File {idx}: {metainfo['info']['name']}, Length: {
                metainfo['info']['length']} bytes"

            # Tạo frame cho mỗi item MetaInfo (nội dung + nút download)
            file_frame = Frame(self.content_frame, bg="white")
            file_frame.pack(fill="x", padx=(200, 0), pady=5)

            # Hiển thị thông tin bằng Label (giảm kích thước chữ)
            file_label = Label(file_frame, text=info_text, font=(
                "Arial", 10), bg="white", anchor="w")
            file_label.pack(side=LEFT)

            # Thêm nút Download
            download_button = Button(file_frame, text="Download", font=(
                "Arial", 10), command=lambda m=metainfo: download_metainfo(m))
            download_button.pack(side=RIGHT, padx=10)


# Hàm hiển thị nội dung Downloads

    def show_download_content(self):
        # Xóa nội dung cũ
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        # Thêm nội dung Downloads
        label = Label(self.content_frame, text="Downloads Content",
                      font=("Arial", 18), bg="white")
        label.place(relx=0.5)

    # Hàm hiển thị nội dung Upload

    def show_upload_content(self):
        # Xóa nội dung cũ
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        # Thêm nội dung Upload
        label = Label(self.content_frame, text="Upload Content",
                      font=("Arial", 18), bg="white")
        label.place(relx=0.5)
        button = Button(self.content_frame, text="Select File to Upload",
                        command=self.select_file)
        button.pack(padx=10, pady=10)
        button.place(relx=0.55, rely=0.15)

    def select_file(self):
        file_path = filedialog.askopenfilename()
        if file_path:
            filelength = os.path.getsize(file_path)
            name = os.path.basename(file_path)
            piece_length = calculate_piece_length(filelength)
            num_piece = math.ceil(filelength/piece_length)
            pieces = hash_file_pieces(file_path, num_piece, piece_length)

            body = {
                "info": {
                    "piece_length": piece_length,
                    "pieces": pieces,
                    "name": name,
                    "length": filelength
                },
                "createBy": "phap"
            }
            print(body)
            add_metainfo_file(body)

    def on_closing(self):
        # Hiển thị hộp thoại xác nhận
        if messagebox.askokcancel("Thoát", "Bạn có chắc chắn muốn thoát chương trình?"):
            # self.root.destroy()  # Đóng cửa sổ và thoát chương trình
            sys.exit()  # Exit chương trình


# Chạy vòng lặp chính của Tkinter


    def run(self):
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()


ClientUI().run()
