import json
from collections import deque
from dotenv import load_dotenv
import os

load_dotenv()


def split_piece_into_blocks(piece_index, piece_size, block_size=16 * 1024):
    """
    Chia một piece thành các block nhỏ để gửi yêu cầu tải.

    :param piece_index: Chỉ số của piece đang tải.
    :param piece_size: Kích thước của piece.
    :param block_size: Kích thước mặc định của block (thường là 16KB).
    :return: Danh sách các block, mỗi block chứa (piece_index, offset, block_size).
    """
    blocks = []
    offset = 0

    while offset < piece_size:
        current_block_size = min(block_size, piece_size - offset)
        blocks.append({
            'piece_index': piece_index,
            'offset': offset,
            'block_size': current_block_size
        })
        offset += current_block_size

    return blocks


def create_request_queue(pieces_info):
    """
    Tạo hàng đợi yêu cầu tải block.

    :param pieces_info: Danh sách chứa thông tin về các pieces cần tải.
    :return: Hàng đợi yêu cầu tải block (queue).
    """
    request_queue = deque()

    for piece_info in pieces_info:
        piece_index = piece_info['piece_index']
        piece_size = piece_info['piece_size']

        # Chia piece thành các block nhỏ
        blocks = split_piece_into_blocks(piece_index, piece_size)

        # Đưa các block vào hàng đợi
        for block in blocks:
            request_queue.append(block)

    return request_queue


# # Ví dụ tạo request queue cho nhiều pieces
# pieces_info = [
#     {'piece_index': 0, 'piece_size': 512 * 1024},
#     {'piece_index': 1, 'piece_size': 512 * 1024}
# ]
# request_queue = create_request_queue(pieces_info)

# Xem danh sách các yêu cầu trong request queue
# for request in request_queue:
#     print(request)


def save_download_progress(download_progress, filename='progress.json'):
    """
    Lưu tiến trình tải xuống vào file JSON.

    :param download_progress: Danh sách các đối tượng chứa thông tin tiến trình tải xuống.
    :param filename: Tên file để lưu dữ liệu.
    """
    with open(filename, 'w') as json_file:
        json.dump(download_progress, json_file, indent=4)


# Ví dụ lưu danh sách tiến trình tải xuống
download_progress = [
    {"file": "file1.txt", "progress": 50},
]

save_download_progress(download_progress)
