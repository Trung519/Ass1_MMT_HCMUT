import hashlib
import os
import urllib.parse


def calculate_piece_length(file_length):
    """
    Tính toán piece length dựa trên file length.

    :param file_length: Kích thước file (tính bằng byte)
    :return: piece length (tính bằng byte)
    """
    # Định nghĩa các khoảng kích thước file và piece length tương ứng
    if file_length < 1 * 1024 * 1024 * 1024:  # Dưới 1 GB
        return 512 * 1024  # 512 KB
    elif file_length < 4 * 1024 * 1024 * 1024:  # Dưới 4 GB
        return 1 * 1024 * 1024  # 1 MB
    elif file_length < 16 * 1024 * 1024 * 1024:  # Dưới 16 GB
        return 2 * 1024 * 1024  # 2 MB
    elif file_length < 64 * 1024 * 1024 * 1024:  # Dưới 64 GB
        return 4 * 1024 * 1024  # 4 MB
    else:  # Trên 64 GB
        return 8 * 1024 * 1024  # 8 MB


def hash_file_pieces(file_path, num_piece, piece_length):
    """
    Chia file thành các piece, băm từng piece và nối lại thành pieces.

    :param file_path: Đường dẫn đến file cần chia
    :param num_piece: Số lượng pieces
    :return: Chuỗi các pieces (được nối lại)
    """
    pieces = ""  # Khởi tạo chuỗi pieces

    with open(file_path, 'rb') as file:
        for i in range(num_piece):
            piece_data = file.read(piece_length)  # Đọc dữ liệu cho piece
            if not piece_data:  # Kiểm tra nếu không còn dữ liệu
                break
            # Băm dữ liệu của piece và nối vào pieces
            sha1_hash = hashlib.sha1(piece_data).digest()
            pieces += urllib.parse.quote(sha1_hash.hex())

    return pieces
