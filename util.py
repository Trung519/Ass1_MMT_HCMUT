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
import pickle
from threading import Lock
import shutil
lockConnect = Lock()

lockFile = Lock()


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

    if file_length < 1 * 512 * 1024:
        return file_length
    elif file_length < 1 * 1024 * 1024 * 1024:  # Dưới 1 GB
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


def genMetainfoFolder(folder_path):
    folder_info = {
        "name": os.path.basename(folder_path),
        "files": [],
        "length": 0
    }
    for dirpath, dirnames, filenames in os.walk(folder_path):
        for file in filenames:
            file_path = os.path.join(dirpath, file)
            if os.path.isfile(file_path):
                filelength = os.path.getsize(file_path)
                folder_info['length'] += filelength
                relative_file_path = os.path.relpath(file_path, folder_path)
                name_file = os.path.basename(file_path)
                piece_length = calculate_piece_length(filelength)
                num_piece = math.ceil(filelength/piece_length)
                pieces = hash_file_pieces(file_path, num_piece, piece_length)
                folder_info['files'] += [{"name": name_file, "length": filelength,
                                          "pieces": pieces, "piece_length": piece_length, "path": relative_file_path}]
    body = {
        "info": folder_info,
        "createBy": username
    }
    info_hash = hash_info(body['info'])
    body['info_hash'] = info_hash
    return body


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
    block_index = 0
    while offset < piece_length:
        current_block_size = min(block_size, piece_length - offset)
        blocks.append({
            'offset': offset,
            'block_size': current_block_size,
            'isDownloaded': isUpload,
            'block_index': block_index
        })
        block_index += 1
        offset += current_block_size
    return blocks


def genProgressFolder(folder_path, isUpload):
    metainfo_folder = genMetainfoFolder(folder_path)
    files = metainfo_folder['info']['files']
    for j in range(len(files)):
        file = files[j]
        piece_length = file['piece_length']
        length = file['length']
        num_piece = math.ceil(length/piece_length)
        pieces_info = []
        for i in range(num_piece):
            rest = length - i*piece_length
            blocks = split_piece_into_blocks(
                min(rest, piece_length), isUpload)
            pieces_info.append({
                "piece_index": i,
                "isDownloaded": isUpload,
                "done_block": len(blocks),
                "blocks": blocks
            })
        file['pieces_info'] = pieces_info
        file['isDownloaded'] = isUpload
        file['file_index'] = j
        file['done_piece'] = num_piece

    progress = {
        "metainfo_folder": metainfo_folder,
        "folder_path": folder_path,
        "info_hash": hash_info(metainfo_folder['info']),
        "uploaded": 0,
        "downloaded": metainfo_folder['info']['length'] if isUpload else 0,
        "left": 0,
        "event": "completed" if isUpload else 'started',
    }
    return progress


def genProgress(file_path, isUpload):
    metainfo_file = genMetainfoFile(file_path)
    piece_length = metainfo_file['info']['piece_length']
    num_piece = math.ceil(metainfo_file['info']['length'] / piece_length)
    length = metainfo_file['info']['length']
    pieces = []
    for i in range(num_piece):
        rest = length - i * piece_length
        blocks = split_piece_into_blocks(min(rest, piece_length), isUpload)
        pieces.append({
            'piece_index': i,
            'isDownloaded': isUpload,
            "done_block": len(blocks),
            'blocks': blocks,
        })

    progress = {
        "metainfo_file": metainfo_file,
        "file_path": file_path,
        "info_hash": hash_info(metainfo_file['info']),
        'file_path': file_path,
        "uploaded": 0,
        "downloaded":   metainfo_file['info']['length'] if isUpload else 0,
        "left": 0,
        "event": "completed" if isUpload else 'started',
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
    

    for peer in peers:
        # peer = {ip, port, peer_id, speed }
        ip_port = (peer["ip"], peer["port"])
        
        if ip_port not in seen_ip_port:
            # peer['isConnected'] = False
            
            
            unique_peers.append({
                "ip": peer['ip'],
                'port': peer['port'],
                "speed": peer['speed'],
                # "isConnected": False,
            })
            seen_ip_port.add(ip_port)
    # print(unique_peers, 'unique_peers')
    # print('-------------')
    unique_peers.sort(key=lambda x: x['speed'], reverse=True)
    return unique_peers


def convert_message_dict_to_byte(message):
    message_json = json.dumps(message)
    return message_json.encode('utf-8')


def handle_message_client(conn, message_dict, connecting_peers, list_progress):
    # print('--------------------')
    # print('MESSAGE FROM CLIENT', message_dict)
    # print('--------------------')

    if message_dict['type'] == EMesage_Type.HANDSHAKE.value:
        handle_message_request_handshake(
            conn, message_dict, connecting_peers, list_progress)
    elif message_dict['type'] == EMesage_Type.BLOCKFOLDER.value:
        handle_message_request_block_folder(conn, message_dict, list_progress)
    elif message_dict['type'] == EMesage_Type.BLOCK.value:
        handle_message_request_block(conn, message_dict, list_progress)
    elif message_dict['type'] == EMesage_Type.HANDSHAKEFOLDER.value:
        handle_message_request_handshake_folder(
            conn, message_dict, connecting_peers, list_progress)
    else:
        print('type message khong xac dinh')
        message_reject = {
            "type": EMesage_Type.REJECT.value,
            "message": 'chặn kết nối'
        }
        message_reject_byte = convert_message_dict_to_byte(message_reject)
        conn.sendall(message_reject_byte)
        conn.send(b'<END>')
        conn.close()


def handle_message_request_handshake_folder(conn, message_dict, connecting_peers, list_progress):
    '''
    message_dict = {
        type: HANDSHAKEFOLDER,
        ip: string,
        port: number,
        info_hash

    }
    '''
    # print('MESSAGE REQUEST HANDSHAKE', message_dict)
    if not is_allow_connect(message_dict, connecting_peers):
        message_reject = {
            "type": EMesage_Type.REJECT.value,
            "message": 'chặn kết nối'
        }
        message_reject_byte = convert_message_dict_to_byte(message_reject)
        conn.sendall(message_reject_byte)
        conn.send(b'<END>')
        conn.close()
        return
    files_info = []
    for progress in list_progress:
        if progress['info_hash'] != message_dict['info_hash']:
            continue
        files = progress['metainfo_folder']['info']['files']
        for file in files:
            peer_id = progress['peer_id']
            file_index = file['file_index']
            pieces_info = [{"piece_index": piece['piece_index']} for piece in file['pieces_info']
                           if piece['isDownloaded']]
            files_info += [{"peer_id": peer_id,
                            "file_index": file_index, "pieces_info": pieces_info}]

    message_response_handshake_folder = {
        "type": EMesage_Type.HANDSHAKEFOLDER.value,
        "info_hash": message_dict['info_hash'],
        "files": files_info,
    }
    message_response_handshake_folder_byte = convert_message_dict_to_byte(
        message_response_handshake_folder)
    conn.sendall(message_response_handshake_folder_byte)
    conn.send(b'<END>')


def handle_message_request_handshake(conn, message_dict, connecting_peers, list_progress):
    '''
    message_dict = {
        type: 'HANDSHAKE',
        ip: string,
        port:number,
        file =  {
                info_hash :string,
                peer_id: string,
            }
        ]
    }
    connectiong_peers = [
        {
            ip: string,
            port: string,
            speed: number,
            isConnected: boolean
        }
    ]
    '''
    file = message_dict['file']
    if is_allow_connect(message_dict, connecting_peers):
        pieces_info = []
        for progress in list_progress:
            if progress['info_hash'] == file['info_hash']:
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
        conn.send(b'<END>')
    else:
        message_reject = {
            "type": EMesage_Type.REJECT.value,
            "message": 'chặn kết nối'
        }
        message_reject_byte = convert_message_dict_to_byte(message_reject)
        conn.sendall(message_reject_byte)
        conn.send(b'<END>')
        conn.close()


def is_allow_connect(message_dict, connecting_peers):
    if len(connecting_peers) < 5:
        connecting_peers += [{
            "ip": message_dict['ip'],
            "port": message_dict['port'],
            "speed": 0,
            # 'isConnected': False
        }]
    for peer in connecting_peers:
        if peer['ip'] == message_dict['ip'] and peer['port'] == message_dict['port']:
            return True
    return False


def handle_message_request_block_folder(conn, message_dict, list_progress):
    '''
    message_dict = {
        type: BLOCKFOLDER,
        peer_id_client: string,
        peer_id_server: string,
        file_index: number,
        piece_index: number,
        block_index: number,
        block_size: number,
        offset: number
    }
    '''
    # print('REQUEST BLOCK', message_dict)
    peer_id_server = message_dict['peer_id_server']
    file_index = message_dict['file_index']
    piece_index = message_dict['piece_index']
    block_index = message_dict['block_index']
    block_size = message_dict['block_size']
    offset = message_dict['offset']
    find_progress = next(
        (progress for progress in list_progress if progress['peer_id'] == peer_id_server), None)

    # print('RESPONSE', piece_index, block_index)

    if find_progress:
        folder_path = find_progress['folder_path']
        file = find_progress['metainfo_folder']['info']['files'][file_index]
        piece_length = file['piece_length']
        file_path = file['path']
        piece = file['pieces_info'][piece_index]
        data = read_block_folder(
            folder_path, file_path, piece_index * piece_length + offset, block_size)
        message_response_block = {
            "type": EMesage_Type.BLOCKFOLDER.value,
            "peer_id_client": message_dict['peer_id_client'],
            "file_index": file_index,
            "piece_index": piece_index,
            "block_index": block_index,
            "offset": offset,
            "block_size": block_size,
            "data": data,
        }
        message_response_block_byte = pickle.dumps(message_response_block)
        find_progress['uploaded'] += block_size
        conn.sendall(message_response_block_byte)
        conn.send(b"<END>")


def handle_message_request_block(conn, message_dict, list_progress):
    '''
    message_dict= {
        peer_id_client: string,
        peer_id_server: string,
        info_hash: string,
        piece_index: number
        block_index: number
        block_size: number
        offset:number,
        type: BLOCK
    }
    '''
    # print('MESSAGE REQUEST BLOCK', message_dict)
    info_hash = message_dict['info_hash']
    peer_id_server = message_dict['peer_id_server']
    offset = message_dict['offset']
    block_size = message_dict['block_size']
    piece_index = message_dict['piece_index']
    find_progress = next(
        (progress for progress in list_progress if progress['info_hash'] == info_hash and progress['peer_id'] == peer_id_server), None)

    if find_progress:
        file_path = find_progress['file_path']
        piece_length = find_progress['metainfo_file']['info']['piece_length']
        data = read_block(file_path, piece_index *
                          piece_length + offset, block_size)
        message_response_block = {
            "data": data,
            "info_hash": info_hash,
            'peer_id_client': message_dict['peer_id_client'],
            "piece_index": message_dict['piece_index'],
            "block_index": message_dict['block_index'],
            "offset": offset,
            "block_size": block_size,
            "type": EMesage_Type.BLOCK.value,
        }
        message_response_block_byte = pickle.dumps(message_response_block)
        conn.sendall(message_response_block_byte)
        find_progress['uploaded'] += block_size
        conn.send(b"<END>")


def handle_message_server(clienUI,client_socket, message_dict, peer, progress,lock_download_block):
    # print('---------------------------------')
    # print('MESSAGE FROM SERVER', message_dict)
    # print('---------------------------------')

    if message_dict['type'] == EMesage_Type.HANDSHAKE.value:
        handle_message_reponse_handshake(clienUI,
            client_socket, message_dict,peer, progress,lock_download_block)
    elif message_dict['type'] == EMesage_Type.HANDSHAKEFOLDER.value:
        handle_message_response_handshake_folder(clienUI,
            client_socket, message_dict,peer, progress,lock_download_block)
    elif message_dict['type'] == EMesage_Type.REJECT.value:
        handle_message_response_reject(client_socket, message_dict, peer)
    elif message_dict['type'] == EMesage_Type.BLOCKFOLDER.value:
        handle_message_response_block_folder(
            client_socket, message_dict, progress)
    elif message_dict['type'] == EMesage_Type.BLOCK.value:
        handle_message_response_block(
            client_socket, message_dict, progress)
    else:
        print('type khong xac dinh')
        client_socket.close()
        # peer['isConnected'] = False


def handle_message_response_handshake_folder(clientUi,client_socket, message_dict,peer, progress,lock_download_block):
    '''
    message_dict = {
        type: HANDSHAKEFOLDER,
        info_hash: string,
        files: [
            {
                peer_id: string,
                file_index: number,
                pieces_info:[
                    piece_index: number
                ]
            }
        ]
    }
    '''
    if message_dict['info_hash'] != progress['info_hash']:
        client_socket.close()
        return
    if progress['event'] !='started' or clientUi.isDisconnect(peer):
        client_socket.close()
        return
    
    progress_files = progress['metainfo_folder']['info']['files']
    files = message_dict['files']
    for file in files:
        if clientUi.isDisconnect(peer) or progress['event'] !='started': 
            client_socket.close()
            return
        progress_file = progress_files[file['file_index']]
        if progress_file['isDownloaded']:
            continue
        progress_file_pieces_info = progress_file['pieces_info']
        for piece_info in file['pieces_info']:
            if clientUi.isDisconnect(peer) or progress['event'] !='started': 
                client_socket.close()
                return
            progress_file_piece_info = progress_file_pieces_info[piece_info['piece_index']]
            if progress_file_piece_info['isDownloaded']:
                continue
            progress_file_piece_info_blocks = progress_file_piece_info['blocks']
            for block in progress_file_piece_info_blocks:
                if clientUi.isDisconnect(peer) or progress['event'] != 'started':
                    client_socket.close()
                    return
                with lock_download_block:
                    if block['isDownloaded']:
                        continue
                    message_request_block ={
                            "type": EMesage_Type.BLOCKFOLDER.value,
                            "peer_id_client": progress['peer_id'],
                            "peer_id_server": file['peer_id'],
                            "file_index": file['file_index'],
                            "piece_index": piece_info['piece_index'],
                            "block_index": block['block_index'],
                            "block_size": block['block_size'],
                            "offset": block['offset']
                    } 
                    message_request_block_byte = convert_message_dict_to_byte(message_request_block)
                    client_socket.sendall(message_request_block_byte)
                    client_socket.send(b'<END>')
                    is_receive_full_response = False
                    response = b''
                    while not is_receive_full_response:
                        data = client_socket.recv(1024)
                        response+=data
                        if response[-5:] == b'<END>':
                            is_receive_full_response = True
                            response = response[:-5]
                    message_dict = pickle.loads(response)
                    # receive block
                    peer['speed']+=block['block_size']
                    handle_message_response_block_folder(client_socket,message_dict,progress)
                


def handle_message_reponse_handshake(clientUi,client_socket, message_dict,peer, progress,lock_download_block):
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
    
    
    
    if progress['event'] != 'started'or clientUi.isDisconnect(peer):
        client_socket.close()
        return
    
    pieces = progress['pieces']
    for piece_info in message_dict['pieces_info']:
        if clientUi.isDisconnect(peer) or progress['event'] !='started': 
            client_socket.close()
            return
        # if progress['info_hash'] != piece_info['info_hash']:
        #     continue
        piece_index_server = piece_info['piece_index']
        peer_id_server = piece_info['peer_id']
        piece_client = pieces[piece_index_server]
        if not piece_client['isDownloaded']:
            blocks = piece_client['blocks']
            for block in blocks:
                if clientUi.isDisconnect(peer) or progress['event'] != 'started':
                    client_socket.close()
                    return
                with lock_download_block:
                    if block['isDownloaded']:
                        continue
                    #send message_request_block --> 
                    message_request_block =  {
                            "peer_id_client": progress['peer_id'],
                            "peer_id_server": peer_id_server,
                            "info_hash": progress['info_hash'],
                            "piece_index": piece_index_server,
                            "offset": block['offset'],
                            'block_index': block['block_index'],
                            'block_size': block['block_size'],
                            "type": EMesage_Type.BLOCK.value,
                    }
                    message_request_block_byte = convert_message_dict_to_byte(message_request_block)
                    client_socket.sendall(message_request_block_byte)
                    client_socket.send(b'<END>')
                    is_receive_full_response = False
                    response = b''
                    while not is_receive_full_response:
                        data = client_socket.recv(1024)
                        response+=data
                        if response[-5:] == b'<END>':
                            is_receive_full_response = True
                            response = response[:-5]
                    message_dict = pickle.loads(response)
                    # receive block
                    peer['speed'] +=block['block_size']
                    handle_message_response_block(client_socket,message_dict,progress)


def handle_message_response_reject(client_socket, message_dict, peer):
    # peer['isConnected'] = False
    client_socket.close()


def handle_message_response_block_folder(client_socket, message_dict, progress):
    '''
    message_dict = {
        type: BLOCKFOLDER,
        peer_id_client: string,
        file_index: number,
        piece_index: number,
        block_index: number,
        offset: number,
        block_size: block_size,
        "data": data
    }
    '''

    block_size = message_dict['block_size']
    file_index = message_dict['file_index']
    piece_index = message_dict['piece_index']
    block_index = message_dict['block_index']
    folder_path = progress['folder_path']
    file = progress['metainfo_folder']['info']['files'][file_index]
    piece_info = file['pieces_info'][piece_index]
    piece_length = file['piece_length']
    block = piece_info['blocks'][block_index]
    file_path = file['path']
    offset = message_dict['offset']
    with lockFile:
        write_block_to_file_folder(
            folder_path, file_path, message_dict['data'], piece_index * piece_length + offset, block_size)
    # print('RECEIVE', piece_index, block_index)

    block['isDownloaded'] = True
    progress['downloaded'] += block['block_size']
    progress['left'] -= block['block_size']
    piece_info['done_block'] += 1
    if piece_info['done_block'] == len(piece_info['blocks']):
        piece_info['isDownloaded'] = True
        file['done_piece'] += 1
        num_piece = math.ceil(file['length']/piece_length)
        if file['done_piece'] == num_piece:
            file['isDownloaded'] = True
            pieces_hash = file['pieces']
            full_path = os.path.join(folder_path, file_path)
            pieces_hash_receive = hash_file_pieces(
                full_path, num_piece, piece_length)
            if pieces_hash != pieces_hash_receive:

                delete_file(full_path)
                messagebox.showerror('Lỗi Tải file', "File tải về không khớp")
                client_socket.close()
                return
            rename_file(full_path)
            if progress['downloaded'] >= progress['metainfo_folder']['info']['length']:
                from peer import clientUi
                clientUi.complete_download(progress)
                client_socket.close()


def handle_message_response_block(client_socket, message_dict, progress):
    '''
    message_dict = {
        type: 'BLOCK',
        data: byte,
        info_hash: string,
        peer_id_client: string,
        piece_index: string,
        block_index: number,
        block_size: number
        offset : number,

    }
    '''
    info_hash = message_dict['info_hash']
    peer_id_client = message_dict['peer_id_client']
    piece_index = message_dict['piece_index']
    block_index = message_dict['block_index']
    offset = message_dict['offset']
    block_size = message_dict['block_size']

    # print('----------------------------')
    # print('PIECE INDEX', piece_index)
    # print('BLOCK INDEX', block_index)
    # print('----------
    # ------------------')
    if progress:
        file_path = progress['file_path']
        piece_length = progress['metainfo_file']['info']['piece_length']
        length = progress['metainfo_file']['info']['length']
        num_piece = math.ceil(length/piece_length)
        with lockFile:
            write_block_to_file(
                file_path, message_dict['data'], piece_index * piece_length + offset, block_size)
        pieces = progress['pieces']
        piece = pieces[piece_index]
        piece['done_block'] += 1
        block = pieces[piece_index]["blocks"][block_index]
        block['isDownloaded'] = True
        progress['downloaded'] += block['block_size']
        progress['left'] -= block['block_size']
        if piece['done_block'] == len(piece['blocks']):
            piece['isDownloaded'] = True
        if progress['downloaded'] >= progress['metainfo_file']['info']['length']:
            pieces_hash = progress['metainfo_file']['info']['pieces']
            pieces_hash_receive = hash_file_pieces(
                file_path, num_piece, piece_length)
            if pieces_hash != pieces_hash_receive:
                delete_file(file_path)
                messagebox.showerror('Lỗi Tải file', "File tải về không khớp")
                # client_socket.close()
                return
            from peer import clientUi
            clientUi.complete_download(progress)
            rename_file(file_path)
            # client_socket.close()


def read_block(file_path, offset, block_size):
    with open(file_path, "rb") as file:
        file.seek(offset)
        data = file.read(block_size)
    return data


def read_block_folder(folder_path, file_path, offset, block_size):
    full_path = os.path.join(folder_path, file_path)
    # if not os.path.isfile(full_path):
    #     print(f"Tệp không tồn tại: {full_path}")
    #     return None
    # print('READ DATA', full_path, offset, block_size)

    with open(full_path, 'rb') as file:
        file.seek(offset)
        data = file.read(block_size)
    # sha1_hash = hashlib.sha1(data).digest()
    # encoded_data = base64.b64encode(sha1_hash).decode('utf-8')
    # print('READ DATA', encoded_data)
    return data


def write_block_to_file_folder(folder_path, file_path, data, offset, block_size):
    # Tạo đường dẫn đầy đủ cho file
    full_path = os.path.join(folder_path, file_path)

    # Tạo tất cả thư mục trong đường dẫn (bao gồm các thư mục con) nếu chưa có
    os.makedirs(os.path.dirname(full_path), exist_ok=True)

    # Tạo file trống nếu chưa tồn tại
    if not os.path.exists(full_path):
        with open(full_path, 'wb') as file:
            pass

    # Mở file ở chế độ đọc và ghi nhị phân, không xóa dữ liệu cũ
    with open(full_path, 'r+b') as file:
        # Di chuyển con trỏ file đến vị trí offset
        file.seek(offset)
        # Ghi dữ liệu block vào vị trí chỉ định
        file.write(data[:block_size])


def write_block_to_file(file_path, data, offset, block_size):

    if not os.path.exists(file_path):
        with open(file_path, 'wb') as file:
            pass  # Tạo file trống nếu không tồn tại
    with open(file_path, 'r+b') as file:  # Mở file ở chế độ đọc và ghi nhị phân
        file.seek(offset)  # Di chuyển con trỏ file đến vị trí offset
        # Ghi dữ liệu có kích thước block_size vào file
        file.write(data[:block_size])


def rename_file(file_path):
    # Tách phần tên và phần mở rộng của file
    base_name, ext = os.path.splitext(file_path)

    # Nếu phần mở rộng là ".part", bắt đầu đổi tên
    if ext == ".part":
        new_name = base_name  # Tên mới bỏ phần mở rộng ".part"

        # Kiểm tra xem tên file mới đã tồn tại chưa, nếu có thì thêm số thứ tự
        counter = 1
        while os.path.exists(new_name):  # Kiểm tra trùng tên
            base_name2, ext2 = os.path.splitext(new_name)
            new_name = f"{base_name2}({counter}){ext2}"
            counter += 1

        # Đổi tên file
        os.rename(file_path, new_name)


def delete_file(file_path):
    with lockFile:
        if os.path.exists(file_path):
            os.remove(file_path)


def gen_info_text(idx, progress):
    if progress['metainfo_file']:
        pass
    else:
        pass


def delete_folder(folder_path):
    # Kiểm tra xem thư mục có tồn tại không
    if os.path.exists(folder_path) and os.path.isdir(folder_path):
        shutil.rmtree(folder_path)
        print(f"Đã xóa thư mục: {folder_path}")
    else:
        print(f"Thư mục không tồn tại: {folder_path}")

# def change_extension_to_part(file_path):
#     # Tách phần gốc và phần mở rộng của đường dẫn file
#     base, _ = os.path.splitext(file_path)
#     # Thêm phần mở rộng mới .part
#     new_file_path = f"{base}.part"
#     return new_file_path
