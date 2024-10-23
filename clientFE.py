import tkinter as tk

root = tk.Tk()
root.geometry('800x600')
root.title('BTL Mạng Máy Tính')

# Hàm để chuyển đổi menu
def toggle_menu():
    def collapse_toggle_menu():
        toggle_menu_fm.destroy()
        toggle_btn.config(text='☰')
        toggle_btn.config(command=toggle_menu)
    
    toggle_menu_fm = tk.Frame(root, bg='#158aff')
    
    # Nút MetaInfo File
    metainfo_btn = tk.Button(toggle_menu_fm, text='MetaInfo File', font=('Bold, 16'), bd=0, bg='#158aff', fg='white',
                             activebackground='#158aff', activeforeground='white', command=show_metainfo_content
                             )
    metainfo_btn.place(x=20, y=20)
    
    # Nút Downloads
    download_btn = tk.Button(toggle_menu_fm, text='Downloads', font=('Bold, 16'), bd=0, bg='#158aff', fg='white',
                             activebackground='#158aff', activeforeground='white', command=show_download_content
                             )
    download_btn.place(x=20, y=60)
    
    # Nút Upload
    upload_btn = tk.Button(toggle_menu_fm, text='Upload', font=('Bold, 16'), bd=0, bg='#158aff', fg='white',
                             activebackground='#158aff', activeforeground='white', command=show_upload_content
                             )
    upload_btn.place(x=20, y=100)

    windown_height = root.winfo_height()

    toggle_menu_fm.place(x=0, y=50, height=windown_height, width=200)
    toggle_btn.config(text='X')
    toggle_btn.config(command=collapse_toggle_menu)

# Tạo frame đầu trang
head_frame = tk.Frame(root, bg='#158aff', highlightbackground='white', highlightthickness=1)

# Nút để mở menu
toggle_btn = tk.Button(head_frame, text='☰', bg='#158aff', fg='white', font=('Bold',20),  
                       activebackground='#158aff', activeforeground='white', command=toggle_menu)
toggle_btn.pack(side=tk.LEFT)

head_frame.pack(side=tk.TOP, fill=tk.X)
head_frame.pack_propagate(False)
head_frame.configure(height=50)

# Frame chính để hiển thị nội dung động
content_frame = tk.Frame(root, bg='white')
content_frame.pack(fill=tk.BOTH, expand=True)

# Hàm hiển thị nội dung MetaInfo File
def show_metainfo_content():
    # Xóa nội dung cũ
    for widget in content_frame.winfo_children():
        widget.destroy()

    # Thêm nội dung MetaInfo File
    label = tk.Label(content_frame, text="MetaInfo File Content", font=("Arial", 18), bg="white")
    label.place(relx=0.5)

# Hàm hiển thị nội dung Downloads
def show_download_content():
    # Xóa nội dung cũ
    for widget in content_frame.winfo_children():
        widget.destroy()

    # Thêm nội dung Downloads
    label = tk.Label(content_frame, text="Downloads Content", font=("Arial", 18), bg="white")
    label.place(relx=0.5)

# Hàm hiển thị nội dung Upload
def show_upload_content():
    # Xóa nội dung cũ
    for widget in content_frame.winfo_children():
        widget.destroy()

    # Thêm nội dung Upload
    label = tk.Label(content_frame, text="Upload Content", font=("Arial", 18), bg="white")
    label.place(relx=0.5)

# Chạy vòng lặp chính của Tkinter
root.mainloop()
