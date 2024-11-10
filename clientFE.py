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
from message_type import EMesage_Type
import time
from threading import Thread
import socket


class ClientUI:
    def __init__(self, ip, port):
        self.ip = ip
        self.peers = []
        self.set_peers = []
        self.connecting_peers = []
        self.port = port
        self.root = Tk()
        self.root.geometry('800x600')
        self.root.title('BTL Mạng Máy Tính')
        self.list_progress = read_download_progress()
        self.message_handshake = {
            "type": EMesage_Type.HANDSHAKE.value,
            'ip': ip,
            'port': port,
            "downloading_file": [],
        }

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
        self.update_progress = None

        for progress in self.list_progress:
            if (progress['event'] == 'completed'):
                self.complete_download(progress)

        # send to tracker all completed file

    def stop_update_progress(self):
        # Hủy vòng lặp cập nhật
        if self.update_progress:
            self.content_frame.after_cancel(self.update_progress)


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
        self.stop_update_progress()
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

            if 'files' in metainfo['info']:
                download_button = Button(file_frame, text="Download", font=(
                    "Arial", 10), command=lambda m=metainfo: self. download_metainfo_folder(m))
            else:
                download_button = Button(file_frame, text="Download", font=(
                    "Arial", 10), command=lambda m=metainfo: self. download_metainfo(m))

            download_button.pack(side=RIGHT, padx=10)

    def download_metainfo_folder(self, metainfo):
        peer_id = str(uuid.uuid4())
        info_hash = metainfo['info_hash']
        name_folder_download = metainfo['info']['name']
        isSameName = True
        idxFolder = 1
        while isSameName:
            isSameName = False
            i = 0
            while i < len(self.list_progress):
                item = self.list_progress[i]
                folder_name_proress = item['metainfo_folder']['info']['name']

                if folder_name_proress == name_folder_download:
                    name_folder_download = name_folder_download + \
                        str(idxFolder)
                    idxFolder += 1
                    isSameName = True
                    break
                i += 1
        metainfo['info']['name'] = name_folder_download
        left = metainfo['info']['length']
        uploaded = 0
        downloaded = 0
        event = 'started'
        url = f"{server_url}/track-peer?info_hash={info_hash}&peer_id={peer_id}&port={
            self.port}&uploaded={uploaded}&downloaded={downloaded}&left={left}&event={event}&ip={self.ip}"

        for file in metainfo['info']['files']:
            piece_length = file['piece_length']
            length = file['length']
            num_piece = math.ceil(length/piece_length)
            pieces_info = []
            for i in range(num_piece):
                rest = length - i * piece_length
                blocks = split_piece_into_blocks(
                    min(rest, piece_length), False)
                pieces_info.append({
                    "piece_index": i,
                    "isDownloaded": False,
                    "blocks": blocks
                })
            file['pieces_info'] = pieces_info
            file['isDownloaded'] = False

        progress = {
            "metainfo_folder": metainfo,
            "folder_path": f'repo/{metainfo['info']['name']}',
            "peer_id": peer_id,
            "info_hash": info_hash,
            "uploaded": uploaded,
            "downloaded": downloaded,
            "left": metainfo['info']['length'],
            "event": 'started'
        }
        self.list_progress = [progress] + self.list_progress
        try:
            response = requests.get(url)
            if response.status_code == 200:
                messagebox.showinfo(
                    "Download folder", "File đang được tải xuống vui lòng kiểm tra trong Downloads & Uploads")
                response_data = response.json()
                self.peers += response_data.get('Peers', [])
                self.set_peers = gen_set_peer(self.peers)
                self.connecting_peers = gen_set_connecting_peer(self.set_peers)
                Thread(target=self.handle_download_folder,
                       args=(progress,), daemon=True).start()
            else:
                messagebox.showerror(
                    "Lỗi hệ thống", "Lỗi trong quá trình tải folder")
        except Exception as e:
            messagebox.showerror(
                "Lỗi hệ thống", "Lỗi trong quá trình tải folder")

    def download_metainfo(self, metainfo):
        peer_id = str(uuid.uuid4())

        info_hash = metainfo['info_hash']
        name_file_download = metainfo['info']['name']
        isSameName = True
        idxfile = 1

        while isSameName:
            isSameName = False  # Đặt lại isSameName để kiểm tra cho mỗi lần lặp mới
            i = 0
            while i < len(self.list_progress):
                item = self.list_progress[i]
                file_name_progress = item['metainfo_file']['info']['name']

                if file_name_progress == name_file_download:
                    name_file_download = insert_before_extension(
                        name_file_download, idxfile)
                    idxfile += 1
                    isSameName = True  # Đánh dấu phát hiện tên trùng
                    break  # Thoát vòng lặp để thử lại với tên file mới
                i += 1

        metainfo['info']['name'] = name_file_download

        left = metainfo['info']['length']
        uploaded = 0
        downloaded = 0
        event = 'started'
        piece_length = metainfo['info']['piece_length']
        num_piece = math.ceil(metainfo['info']['length'] / piece_length)
        pieces = []

        url = f"{server_url}/track-peer?info_hash={info_hash}&peer_id={peer_id}&port={
            self.port}&uploaded={uploaded}&downloaded={downloaded}&left={left}&event={event}&ip={self.ip}"
        length = metainfo['info']['length']
        for i in range(num_piece):
            rest = length - i*piece_length
            blocks = split_piece_into_blocks(min(rest, piece_length), False)
            pieces.append({
                'piece_index': i,
                'isDownloaded': False,
                "blocks": blocks,
            })
        progress = {
            "metainfo_file": metainfo,
            "file_path": f'./repo/{metainfo['info']['name']}.part',
            "peer_id": peer_id,
            "info_hash": info_hash,
            "uploaded": uploaded,
            "downloaded": downloaded,
            "left": left,
            "event": event,
            "pieces": pieces
        }
        # luu tien trinh upload
        self.list_progress = [progress] + self.list_progress

        try:
            response = requests.get(url)
            if response.status_code == 200:
                messagebox.showinfo(
                    "Download file", 'File đang được tải xuống vui lòng kiểm tra trong Downloads & Uploads')
            # Giả sử server trả về JSON
                response_data = response.json()  # Chuyển đổi thành đối tượng Python
                self.peers += response_data.get('Peers', [])
                self.set_peers = gen_set_peer(self.peers)
                self.connecting_peers = gen_set_connecting_peer(self.set_peers)
                Thread(target=self.handle_download_file,
                       args=(progress,), daemon=True).start()

                # push downloadding_file to message_handshake
                self.message_handshake['downloading_file'].append(
                    {'info_hash': info_hash, 'peer_id': peer_id})
            else:
                messagebox.showerror("Lỗi hệ thông", 'Thử lại sau')
                print(f"Failed to download: {
                      response.status_code} - {response.text}")
        except Exception as e:
            messagebox.showerror("Lỗi hệ thông", 'Thử lại sau')
            print(f"Error during download: {e}")

        # Hàm hiển thị nội dung Downloads

    def show_download_content(self):
        # print(self.set_peers, 'set peers')
        # print(self.connecting_peers, 'connecting peer')
        # print(self.peers, 'peers')
        # print('message handshake', self.message_handshake)
        # self.update_progress = self.content_frame.after(
        #     1000, self.show_download_content)
        # Xóa nội dung cũ
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        # Thêm nội dung Downloads
        label = Label(self.content_frame, text="Downloads Content",
                      font=("Arial", 18), bg="white")
        label.place(relx=0.5)

        for idx, progress in enumerate(self.list_progress, start=1):

            downloaded = progress['downloaded']
            if 'metainfo_file' in progress:
                file_length = progress['metainfo_file']['info']['length']
                createBy = progress['metainfo_file']['createBy']
                name = progress['metainfo_file']['info']['name']
                percentage = (downloaded/file_length) * 100
                infor_text = f"File {idx}: {name} \n createBy: {createBy}, uploaded: {
                    progress['uploaded']}, downloaded: {progress['downloaded']} \n Progress: {percentage:.2f}% "
            else:
                file_length = progress['metainfo_folder']['info']['length']
                createBy = progress['metainfo_folder']['createBy']
                name = progress['metainfo_folder']['info']['name']
                percentage = (downloaded/file_length) * 100
                infor_text = f"Folder {idx}: {name} \n createBy: {createBy}, uploaded: {
                    progress['uploaded']}, downloaded: {progress['downloaded']} \n Progress: {percentage:.2f}% "

            event = progress['event']
            progress_frame = Frame(
                self.content_frame, bg='white', bd=2, relief='solid')
            progress_frame.pack(fill='x', padx=(220, 0), pady=5)

            progress_label = Label(progress_frame, text=infor_text, font=(
                'Arial', 10), bg='white', anchor='w')
            progress_label.pack(side=LEFT)

            # Thêm nút dựa trên trạng thái event
            if event == "started":
                button = Button(
                    progress_frame, text="Pause", command=lambda progress=progress: self.pause_download(progress))
                button.pack(side=RIGHT, padx=10)

            elif event == "stopped":
                button = Button(
                    progress_frame, text="Resume", command=lambda progress=progress: self.resume_download(progress))
                button.pack(side=RIGHT, padx=10)
            else:
                finish_label = Label(progress_frame, text='Chia sẽ', font=(
                    'Arial', 10), bg='white', anchor='w')
                finish_label.pack(side=RIGHT, padx=10)
            delete_button = Button(
                progress_frame, text="Delete", command=lambda progress=progress: self.delete_download(progress))
            delete_button.pack(side=RIGHT, padx=10)

    def delete_download(self, progress):
        info_hash = progress['info_hash']
        peer_id = progress['peer_id']
        uploaded = progress['uploaded']
        downloaded = progress['downloaded']
        left = progress['left']
        event = 'stopped'
        file_path = progress['file_path']
        url = f"{server_url}/track-peer?info_hash={info_hash}&peer_id={peer_id}&port={
            self.port}&uploaded={uploaded}&downloaded={downloaded}&left={left}&event={event}&ip={self.ip}"

        try:
            response = requests.get(url)
            if response.status_code == 200:
                # xoa peers tham gia tai file nay
                if progress['event'] == 'started' or progress['event'] == 'completed':
                    progress['event'] = 'stopped'
                    self.peers = [
                        peer for peer in self.peers if peer['client_id'] != peer_id]
                    self.set_peers = gen_set_peer(self.peers)
                    self.connecting_peers = gen_set_connecting_peer(
                        self.set_peers)
                # xoa tien trinh
                self.list_progress = [
                    item for item in self.list_progress if not (item['info_hash'] == info_hash and item['peer_id'] == peer_id)]
                self.message_handshake['downloading_file'] = [message for message in self.message_handshake['downloading_file'] if not (
                    message['info_hash'] == info_hash and message['peer_id'] == peer_id)]
                if file_path.endswith('.part'):
                    # time.sleep(1)
                    delete_file(file_path)

            else:
                messagebox.showerror("Lỗi hệ thông", 'Thử lại sau')
                print(f"Failed to download: {
                    response.status_code} - {response.text}")
        except Exception as e:
            messagebox.showerror("Lỗi hệ thông", 'Thử lại sau')
            print(f"Error during download: {e}")
        # delete partial file if exist

        # Hàm hiển thị nội dung Upload

    def pause_download(self, progress):
        progress['event'] = 'stopped' if progress['event'] == 'started' else progress['event']
        info_hash = progress['info_hash']
        peer_id = progress['peer_id']
        uploaded = progress['uploaded']
        downloaded = progress['downloaded']
        left = progress['left']
        event = 'stopped'
        url = f"{server_url}/track-peer?info_hash={info_hash}&peer_id={peer_id}&port={
            self.port}&uploaded={uploaded}&downloaded={downloaded}&left={left}&event={event}&ip={self.ip}"
        # try:
        response = requests.get(url)
        if response.status_code == 200:
            # Giả sử server trả về JSON

            self.peers = [
                peer for peer in self.peers if peer['client_id'] != peer_id]

            self.set_peers = gen_set_peer(self.peers)
            self.connecting_peers = gen_set_connecting_peer(self.set_peers)

            self.message_handshake['downloading_file'] = [message for message in self.message_handshake['downloading_file'] if not (
                message['info_hash'] == info_hash and message['peer_id'] == peer_id)]

        else:
            try:
                messagebox.showerror("Lỗi hệ thông", 'Thử lại sau')
                print(f"Failed to download: {
                    response.status_code} - {response.text}")
            except Exception as e:
                print(e)
                messagebox.showerror("Lỗi hệ thông", 'Thử lại sau')
                print(f"Error during download: {e}")
            # send request to server tracker

    def resume_download(self, progress):
        progress['event'] = 'started'
        info_hash = progress['info_hash']
        peer_id = progress['peer_id']
        uploaded = progress['uploaded']
        downloaded = progress['downloaded']
        left = progress['left']
        event = progress['event']
        url = f"{server_url}/track-peer?info_hash={info_hash}&peer_id={peer_id}&port={
            self.port}&uploaded={uploaded}&downloaded={downloaded}&left={left}&event={event}&ip={self.ip}"

        try:
            response = requests.get(url)
            if response.status_code == 200:
                # Giả sử server trả về JSON
                response_data = response.json()
                self.peers += response_data.get('Peers', [])
                self.set_peers = gen_set_peer(self.peers)
                self.connecting_peers = gen_set_connecting_peer(self.set_peers)
                Thread(target=self.handle_download_file,
                       args=(progress,), daemon=True).start()
                self.message_handshake['downloading_file'].append(
                    {'info_hash': info_hash, 'peer_id': peer_id, })

            else:
                messagebox.showerror("Lỗi hệ thông", 'Thử lại sau')
                print(f"Failed to download: {
                    response.status_code} - {response.text}")
        except Exception as e:
            messagebox.showerror("Lỗi hệ thông", 'Thử lại sau')
            print(f"Error during download: {e}")
        # send request to server tracker

    def complete_download(self, progress):
        progress['event'] = "completed"
        info_hash = progress['info_hash']
        peer_id = progress['peer_id']
        uploaded = progress['uploaded']
        downloaded = progress['downloaded']
        left = progress['left']
        event = progress['event']
        url = f"{server_url}/track-peer?info_hash={info_hash}&peer_id={peer_id}&port={
            self.port}&uploaded={uploaded}&downloaded={downloaded}&left={left}&event={event}&ip={self.ip}"
        try:
            response = requests.get(url)
            if response.status_code == 200:
                self.message_handshake['downloading_file'] = [
                    item for item in self.message_handshake['downloading_file'] if item['info_hash'] != info_hash and item['peer_id'] != peer_id]
            else:
                messagebox.showerror("Lỗi hệ thông", 'Thử lại sau')
                print(f"Failed to download: {
                    response.status_code} - {response.text}")
        except Exception as e:
            messagebox.showerror("Lỗi hệ thông", 'Thử lại sau')
            print(f"Error during download: {e}")
    # send reqeust to server tracker

    def pause_all_progress(self, list_progress):
        for progress in list_progress:
            if progress['event'] == 'started' or progress['event'] == 'completed':
                self. pause_download(progress)
                # file_path = progress['file_path']
                # if file_path.endswith('.part'):
                #     delete_file(file_path)

    def show_upload_content(self):
        self.stop_update_progress()
        # Xóa nội dung cũ
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        # Thêm nội dung Upload
        label = Label(self.content_frame, text="Upload Content",
                      font=("Arial", 18), bg="white")
        label.place(relx=0.5)
        button_frame = Frame(self.content_frame, bg='white')
        # button_frame.pack(padx=10, pady=10)
        button_frame.place(relx=0.5, rely=0.15)
        button_file = Button(button_frame, text="Select File to Upload",
                             command=self.select_file)
        button_file.pack(side=LEFT)
        # button_file.pack(padx=10, pady=10)
        # button_file.place(relx=0.55, rely=0.15)
        button_folder = Button(
            button_frame, text='Select folder to Upload', command=self.select_folder)
        button_folder.pack(side=RIGHT, padx=10)
        # button_file.pack(padx=10, pady=10)
        # button_file.place(relx=0.55, rely=0.15)

    def select_file(self):
        file_path = filedialog.askopenfilename()
        if file_path:
            peer_id = str(uuid.uuid4())
            body = genMetainfoFile(file_path)
            progress = genProgress(file_path, True)
            progress['peer_id'] = peer_id
            info_hash = body['info_hash']
            uploaded = progress['uploaded']
            downloaded = progress['downloaded']
            left = progress['left']
            event = progress['event']
            # server track file peer upload
            url = f"{server_url}/track-peer?info_hash={info_hash}&peer_id={peer_id}&port={
                self.port}&uploaded={uploaded}&downloaded={downloaded}&left={left}&event={event}&ip={self.ip}"

            try:
                response = requests.get(url)
                if response.status_code == 200:
                    response_data = response.json()
                    # luu peers
                    self.peers += response_data.get("Peers", [])
                    # luu mata info
                    add_metainfo_file(body)
                    # luu progress
                    self.list_progress = [progress] + self.list_progress
                else:
                    messagebox.showerror(
                        "Lỗi hệ thông", 'Lỗi trong quá trình upload file')
                    print(f"Failed to download: {
                        response.status_code} - {response.text}")
            except Exception as e:
                messagebox.showerror(
                    "Lỗi hệ thông", 'Lỗi trong quá trình upload file')
                print(f"Error during download: {e}")

    def select_folder(self):
        folder_path = filedialog.askdirectory()
        if folder_path:
            peer_id = str(uuid.uuid4())
            body = genMetainfoFolder(folder_path)

            progress = genProgressFolder(folder_path, True)
            progress['peer_id'] = peer_id
            info_hash = body['info_hash']
            progress['info_hash'] = info_hash
            uploaded = progress['uploaded']
            downloaded = progress['downloaded']
            left = progress['left']
            event = progress['event']
            url = f"{server_url}/track-peer?info_hash={info_hash}&peer_id={peer_id}&port={
                self.port}&uploaded={uploaded}&downloaded={downloaded}&left={left}&event={event}&ip={self.ip}"

            try:
                response = requests.get(url)
                if response.status_code == 200:
                    response_data = response.json()
                    # luu peers
                    self.peers += response_data.get("Peers", [])
                    # luu mata info
                    add_metainfo_file(body)
                    # luu progress
                    self.list_progress = [progress] + self.list_progress
                else:
                    messagebox.showerror(
                        "Lỗi hệ thông", 'Lỗi trong quá trình upload folder')
            except Exception as e:
                messagebox.showerror(
                    "Lỗi hệ thông", 'Lỗi trong quá trình upload folder')

    def on_closing(self):
        # Hiển thị hộp thoại xác nhận
        if messagebox.askokcancel("Thoát", "Bạn có chắc chắn muốn thoát chương trình?"):
            try:
                self.pause_all_progress(self.list_progress)
                save_download_progress(self.list_progress)
            except Exception as e:
                messagebox.showerror(
                    "Lỗi server", "Lỗi gửi đến server tracker")
            # self.root.destroy()  # Đóng cửa sổ và thoát chương trình
            sys.exit()  # Exit chương trình

    def isDisconnect(self, peer):
        with lockConnect:
            # Kiểm tra trong connecting_peers có peer nào có IP và port giống peer không
            for connected_peer in self.connecting_peers:
                if connected_peer['ip'] == peer['ip'] and connected_peer['port'] == peer['port']:
                    return False  # Có peer với IP và port giống -> không ngắt kết nối
            return True  # Không có peer nào trùng IP và port -> ngắt kết nối
# Chạy vòng lặp chính của Tkinter

    def handle_download_folder(self, progress):
        threads = [Thread(target=self.connect_to_peer_download_folder, args=(
            progress, peer)) for peer in self.connecting_peers]
        [t.start() for t in threads]

    def handle_download_file(self, progress):
        # print('CONNECTING PEER', self.connecting_peers)
        threads = [Thread(target=self.connect_to_peer, args=(
            progress, peer)) for peer in self.connecting_peers]
        [t.start() for t in threads]

    def connect_to_peer_download_folder(self, progress, peer):
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((peer['ip'], peer['port']))

    def connect_to_peer(self, progress, peer):
        # print('thread')
        # print('PROGRESS', progress)
        # print('PEER', self.peers)
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((peer['ip'], peer['port']))
        message_request_block_queue = []
        message_handshake = {
            "type": EMesage_Type.HANDSHAKE.value,
            "ip": self.ip,
            "port": self.port,
            "file": {
                "info_hash": progress['info_hash'],
                "peer_id": progress['peer_id']
            }
        }
        isSent = False
        while progress['event'] == 'started':
            if self.isDisconnect(peer):
                break
            if progress['event'] != 'started':
                break
            if not isSent:
                message_handshake_byte = convert_message_dict_to_byte(
                    message_handshake)
                client_socket.sendall(message_handshake_byte)
                client_socket.send(b'<END>')
                isSent = True
                is_receive_full_response = False
                response = b''
                while not is_receive_full_response:
                    data = client_socket.recv(1024)
                    response += data
                    if response[-5:] == b'<END>':
                        is_receive_full_response = True
                        response = response[:-5]
                message_dict = json.loads(response.decode('utf-8'))
                handle_message_server(
                    client_socket, message_dict, peer, progress, message_request_block_queue)

            if message_request_block_queue != []:
                if self.isDisconnect(peer):
                    break
                if progress['event'] != 'started':
                    break
                message_request_block = message_request_block_queue.pop(0)
                pieces = progress['pieces']
                downloading_piece = pieces[message_request_block['piece_index']]
                blocks = downloading_piece['blocks']
                downloading_block = blocks[message_request_block['block_index']]
                if downloading_block['isDownloaded']:
                    continue

                message_request_block_byte = convert_message_dict_to_byte(
                    message_request_block)
                message_request_block_byte
                client_socket.sendall(message_request_block_byte)
                client_socket.send(b'<END>')
                is_receive_full_response = False
                response = b''

                while not is_receive_full_response:
                    data = client_socket.recv(1024)
                    response += data
                    if response[-5:] == b'<END>':
                        is_receive_full_response = True
                        response = response[:-5]

                message_dict = pickle.loads(response)
                handle_message_server(
                    client_socket, message_dict, peer, progress, message_request_block_queue)

        print('END CONNECT')
        return client_socket

    def run(self):
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()
