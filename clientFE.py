from tkinter import Tk, messagebox, filedialog, Button, Frame, LEFT, TOP, X, BOTH, Label, RIGHT
import sys
import os
import hashlib
from util import *
from api import *
import urllib.parse
import bencodepy
import uuid

import math


class ClientUI:
    def __init__(self, ip, port):
        self.ip = ip
        self.peers = []
        self.port = port
        self.root = Tk()
        self.root.geometry('800x600')
        self.root.title('BTL Mạng Máy Tính')
        self.list_progress = read_download_progress()

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
        metainfo_btn = Button(toggle_menu_fm, text='MetaInfo File', font=('Bold, 14'), bd=0, bg='#158aff', fg='white',
                              activebackground='#158aff', activeforeground='white', command=self.show_metainfo_content
                              )
        metainfo_btn.place(x=15, y=20)

        # Nút Downloads
        download_btn = Button(toggle_menu_fm, text='Downloads & Uploads', font=('Bold, 14'), bd=0, bg='#158aff', fg='white',
                              activebackground='#158aff', activeforeground='white', command=self.show_download_content
                              )
        download_btn.place(x=15, y=60)

        # Nút Upload
        upload_btn = Button(toggle_menu_fm, text='Upload', font=('Bold, 14'), bd=0, bg='#158aff', fg='white',
                            activebackground='#158aff', activeforeground='white', command=self.show_upload_content
                            )
        upload_btn.place(x=15, y=100)

        windown_height = self.root.winfo_height()

        toggle_menu_fm.place(x=0, y=50, height=windown_height, width=220)
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
        label.place(relx=0.5)

        # Duyệt qua danh sách MetaInfo và hiển thị mỗi item
        for idx, metainfo in enumerate(list_metainfo, start=1):
            # Lấy thông tin cần hiển thị, có thể tuỳ chỉnh theo cấu trúc metainfo
            info_text = f"File {idx}: {metainfo['info']['name']} \n Length: {
                metainfo['info']['length']} bytes, createBy: {metainfo['createBy']} "

            # Tạo frame cho mỗi item MetaInfo (nội dung + nút download)
            file_frame = Frame(self.content_frame,
                               bg="white", bd=2, relief="solid")
            file_frame.pack(fill="x", padx=(220, 0), pady=5)

            # Hiển thị thông tin bằng Label (giảm kích thước chữ)
            file_label = Label(file_frame, text=info_text, font=(
                "Arial", 10), bg="white", anchor="w")
            file_label.pack(side=LEFT)

            # Thêm nút Download
            download_button = Button(file_frame, text="Download", font=(
                "Arial", 10), command=lambda m=metainfo: self. download_metainfo(m))
            download_button.pack(side=RIGHT, padx=10)

    def download_metainfo(self, metainfo):
        peer_id = str(uuid.uuid4())
        info_hash = hash_info(metainfo['info'])
        left = metainfo['info']['length']
        uploaded = 0
        downloaded = 0
        event = 'started'

        url = f"{server_url}/track-peer?info_hash={info_hash}&peer_id={peer_id}&port={
            self.port}&uploaded={uploaded}&downloaded={downloaded}&left={left}&event={event}&ip={self.ip}"
        try:
            response = requests.get(url)
            print(response.status_code)
            if response.status_code == 200:
                print(f"Successfully downloaded: {response.text}")
            # Giả sử server trả về JSON
                response_data = response.json()  # Chuyển đổi thành đối tượng Python
                self.peers = response_data.get('Peers', [])
                print(f"Peers: {self.peers}")
            else:
                print(f"Failed to download: {
                      response.status_code} - {response.text}")
        except Exception as e:
            print(f"Error during download: {e}")
        # Hàm hiển thị nội dung Downloads

    def show_download_content(self):
        # Xóa nội dung cũ
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        # Thêm nội dung Downloads
        label = Label(self.content_frame, text="Downloads Content",
                      font=("Arial", 18), bg="white")
        label.place(relx=0.5)
        for idx, progress in enumerate(self.list_progress, start=1):
            downloaded = progress['downloaded']
            file_length = progress['metainfo_file']['info']['length']
            event = progress['event']
            percentage = (downloaded/file_length) * 100
            infor_text = f"File {idx}: {progress['metainfo_file']['info']['name']} \n createBy: {progress['metainfo_file']['createBy']}, uploaded: {
                progress['uploaded']}, downloaded: {progress['downloaded']} \n Progress: {percentage:.2f}% "
            progress_frame = Frame(
                self.content_frame, bg='white', bd=2, relief='solid')
            progress_frame.pack(fill='x', padx=(220, 0), pady=5)

            progress_label = Label(progress_frame, text=infor_text, font=(
                'Arial', 10), bg='white', anchor='w')
            progress_label.pack(side=LEFT)

            # Thêm nút dựa trên trạng thái event
            if event == "started":
                button = Button(
                    progress_frame, text="Pause", command=lambda: self.pause_download(progress))
                button.pack(side=RIGHT, padx=10)

            elif event == "stopped":
                button = Button(
                    progress_frame, text="Resume", command=lambda: self.resume_download(progress))
                button.pack(side=RIGHT, padx=10)
            else:
                finish_label = Label(progress_frame, text='Chia sẽ', font=(
                    'Arial', 10), bg='white', anchor='w')
                finish_label.pack(side=RIGHT, padx=10)
            delete_button = Button(
                progress_frame, text="Delete", command=lambda: self.pause_download(progress))
            delete_button.pack(side=RIGHT, padx=10)

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
            body = genMetainfoFile(file_path)
            progress = genProgress(file_path, True)
            add_metainfo_file(body)
            self.list_progress.append(progress)
            print(self.list_progress)
            save_download_progress(self.list_progress)

    def on_closing(self):
        # Hiển thị hộp thoại xác nhận
        if messagebox.askokcancel("Thoát", "Bạn có chắc chắn muốn thoát chương trình?"):
            # self.root.destroy()  # Đóng cửa sổ và thoát chương trình
            sys.exit()  # Exit chương trình
# Chạy vòng lặp chính của Tkinter

    def run(self):
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()
