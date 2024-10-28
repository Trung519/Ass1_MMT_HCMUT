import base64
import hashlib
import os
import urllib.parse
import json
import bencodepy
import math
from dotenv import load_dotenv
from tkinter import messagebox
import requests
import random
from message_type import EMesage_Type


load_dotenv()

username = os.getenv('USERNAME') or 'Unknown'
server_url = os.getenv('SERVER_URL')


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
    pieces = b""  # Khởi tạo chuỗi pieces

    with open(file_path, 'rb') as file:
        for i in range(num_piece):
            piece_data = file.read(piece_length)  # Đọc dữ liệu cho piece
            if not piece_data:  # Kiểm tra nếu không còn dữ liệu
                break
            # Băm dữ liệu của piece và nối vào pieces
            sha1_hash = hashlib.sha1(piece_data).digest()
            # pieces += urllib.parse.quote(sha1_hash.hex())
            pieces += sha1_hash
    encoded_pieces = base64.b64encode(pieces).decode('utf-8')

    return encoded_pieces


# Giải mã chuỗi Base64 về byte
def decode_pieces_base64(encoded_pieces):
    return base64.b64decode(encoded_pieces)


def save_download_progress(download_progress, filename='progress.json'):
    """
    Lưu tiến trình tải xuống vào file JSON.

    :param download_progress: Danh sách các đối tượng chứa thông tin tiến trình tải xuống.
    :param filename: Tên file để lưu dữ liệu.
    """
    with open(filename, 'w') as json_file:
        json.dump(download_progress, json_file, indent=4)


def read_download_progress(filename='progress.json'):
    """
Đọc tiến trình tải xuống từ file JSON và trả về dưới dạng dictionary.

    :param filename: Tên file để đọc dữ liệu.
    :return: Danh sách các đối tượng chứa thông tin tiến trình tải xuống.
    """
    try:
        with open(filename, 'r') as json_file:
            # Đọc dữ liệu và chuyển đổi thành dictionary
            download_progress = json.load(json_file)
        return download_progress
    except FileNotFoundError:
        print(f"File '{filename}' not found.")
        return []
    except json.JSONDecodeError:
        print("Error decoding JSON.")
        return []


def hash_info(info):
    bencoded_info = bencodepy.encode(info)
    # Compute SHA1 hash
    sha1_hash = hashlib.sha1(bencoded_info).digest()

    # URL-encode the hash and convert to hex
    info_hash = urllib.parse.quote(sha1_hash.hex())
    return info_hash


def genMetainfoFile(file_path):
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
        "createBy": username
    }
    info_hash = hash_info(body['info'])
    body['info_hash'] = info_hash
    return body


def split_piece_into_blocks(piece_length, isUpload, block_size=16*1024):
    blocks = []
    offset = 0
    while offset < piece_length:
        current_block_size = min(block_size, piece_length - offset)
        blocks.append({
            'offset': offset,
            'block_size': current_block_size,
            'isDownloaded': isUpload,
        })
        offset += current_block_size
    return blocks


def genProgress(file_path, isUpload):
    metainfo_file = genMetainfoFile(file_path)
    piece_length = metainfo_file['info']['piece_length']
    num_piece = math.ceil(metainfo_file['info']['length'] / piece_length)
    pieces = []
    for i in range(num_piece):
        blocks = split_piece_into_blocks(piece_length, isUpload)
        pieces.append({
            'piece_index': i,
            'isDownloaded': isUpload,
            'blocks': blocks,
        })

    progress = {
        "metainfo_file": metainfo_file,
        "file_path": file_path,
        "info_hash": hash_info(metainfo_file['info']),
        'file_path': file_path,
        "uploaded": 0,
        "downloaded": metainfo_file['info']['length'],
        "left": 0,
        "event": "completed",
        'pieces': pieces,
    }
    return progress


def removeByPeerId(list_progress, peer_id):
    return list(filter(lambda item: item['peer_id'] != peer_id, list_progress))


def insert_before_extension(file_name, idx):
    # Tìm vị trí của dấu chấm cuối cùng
    dot_index = file_name.rfind('.')

    # Nếu không tìm thấy dấu chấm, trả về chuỗi gốc
    if dot_index == -1:
        return file_name

    # Chèn chuỗi trước phần mở rộng
    new_file_name = file_name[:dot_index] + \
        f"({idx})" + file_name[dot_index:]

    return new_file_name


def gen_set_connecting_peer(set_peer):
    if len(set_peer) <= 5:
        return set_peer
    result = set_peer[:4]
    random_peer = random.randint(4, len(set_peer))
    result.append(set_peer[random_peer])


def gen_set_peer(peers):
    # print('gen set peer --------------')
    seen_ip_port = set()
    unique_peers = []
    for item in peers.items():
        list_peer = item[1]
        for peer in list_peer:
            # peer = {ip, port, peer_id, speed }
            ip_port = (peer["ip"], peer["port"])
            if ip_port not in seen_ip_port:
                peer['isConnected'] = False
                unique_peers.append(peer)
                seen_ip_port.add(ip_port)
    # print(unique_peers, 'unique_peers')
    # print('-------------')
    unique_peers.sort(key=lambda x: x['speed'], reverse=True)
    return unique_peers


def convert_message_dict_to_byte(message):
    message_json = json.dumps(message)
    return message_json.encode('utf-8')


def handle_message_client(conn, message_dict, connecting_peers, status, list_progress):
    if message_dict['type'] == EMesage_Type.HANDSHAKE.value:
        handle_message_request_handshake(
            conn, message_dict, connecting_peers, status, list_progress)
    elif message_dict['type'] == EMesage_Type.BLOCK.value:
        handle_message_request_block(conn, message_dict)
    else:
        print('type message khong xac dinh')
        conn.close()


def handle_message_request_handshake(conn, message_dict, connecting_peers, status, list_progress):
    '''
    message_dict = {
        type: 'HANDSHAKE'
        dowloading_file = [
            {
                info_hash :string,
                peer_id: string,
            }
        ]
    }
    connectiong_peers = [
        {
            ip: string,
            port: string,
            peer_id: string,
            speed: number,
            isConnected: boolean
        }
    ]
    '''
    downloading_files = message_dict['downloading_file']
    if is_allow_connect(downloading_files, connecting_peers):
        list_progess = list_progress
        list_downloading_info_hash = [item['info_hash']
                                      for item in downloading_files]
        pieces_info = []
        for progress in list_progess:
            if progress['info_hash'] in list_downloading_info_hash:
                pieces_info += [{
                    "info_hash": progress['info_hash'],
                    'peer_id': progress['peer_id'],
                    'piece_index': item['piece_index']
                } for item in progress['pieces']
                    if item['isDownloaded']]
        message_response_handshake = {
            "type": EMesage_Type.HANDSHAKE.value,
            'pieces_info': pieces_info
        }
        message_response_handshake_byte = convert_message_dict_to_byte(
            message_response_handshake)
        conn.sendall(message_response_handshake_byte)
        status['isAccept'] = True
    else:
        message_reject = {
            "type": EMesage_Type.REJECT.value,
            "message": 'chặn kết nối'
        }
        message_reject_byte = convert_message_dict_to_byte(message_reject)
        conn.sendall(message_reject_byte)
        status['isAccept'] = False
        conn.close()


def is_allow_connect(downloading_files, connecting_peers):
    connecting_peer_ids = [item['peer_id'] for item in connecting_peers]
    list_exist = [
        item for item in downloading_files if item['peer_id'] in connecting_peer_ids]
    return len(list_exist) != 0


def handle_message_request_block(conn, message_dict):
    pass


def handle_message_server(client_socket, message_dict, peer, list_progress):
    if message_dict['type'] == EMesage_Type.HANDSHAKE.value:
        handle_message_reponse_handshake(
            client_socket, message_dict, list_progress)
    elif message_dict['type'] == EMesage_Type.REJECT.value:
        handle_message_response_reject(client_socket, message_dict, peer)


def handle_message_reponse_handshake(client_socket, message_dict, list_progress):
    '''
    message_dict = {
        type: 'HANDSHAKE',
        pieces_info: [
            {
                info_hash : string,
                peer_id : string,
                piece_index: number
            }
        ]
    }
    '''
    pieces_info = message_dict['pieces_info']
    for piece_info in pieces_info:
        piece_index_is_downloaded = piece_info['piece_index']
        peer_id_server = piece_info['peer_id']
        info_hash = piece_info['info_hash']
        for progress in list_progress:
            if progress['info_hash'] == piece_info['info_hash']:
                list_pieces_need_to_download = [{"piece_id_client": progress['peer_id'], "peer_id_server": peer_id_server, 'info_hash': info_hash,
                                                 'piece_index':  piece_index_is_downloaded} for piece in progress['pieces'] if not piece[piece_index_is_downloaded]]
    print('MESSAGE_SERVER_RESPONSE_HANDSHAKE', message_dict)


def handle_message_response_reject(client_socket, message_dict, peer):
    peer['isConnected'] = False
    client_socket.close()
