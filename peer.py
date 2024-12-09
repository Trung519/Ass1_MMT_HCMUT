import random
import socket
import requests
from threading import Lock, Thread
import threading
import hashlib
import urllib.parse
import bencodepy
import uuid
import os
from tkinter import Tk, Label, Entry, Button, filedialog, messagebox
from clientFE import ClientUI
import time
from util import server_url, gen_set_connecting_peer, gen_set_peer, handle_message_client, convert_message_dict_to_byte, handle_message_server
import json
from message_type import EMesage_Type
import pickle
from tqdm import tqdm

from dotenv import load_dotenv

load_dotenv()

stop_event = threading.Event()


# # chọn 5 peer
# refresh peers
def refresh_peers_per_30_minutes():
    clientUi.peers = []
    clientUi.set_peers = []
    clientUi.connecting_peers = []
    while True:
        for progress in clientUi.list_progress:
            event = progress['event']
            if event == 'started':
                peer_id = progress['peer_id']
                left = progress['left']
                uploaded = progress['uploaded']
                downloaded = progress['downloaded']
                info_hash = progress['info_hash']
                url = f"{server_url}/track-peer?info_hash={info_hash}&peer_id={peer_id}&port={port}&uploaded={uploaded}&downloaded={downloaded}&left={left}&event={event}&ip={clientip}"
                # try:
                response = requests.get(url)
                if response.status_code == 200:
                    response_data = response.json()
                    clientUi.peers[peer_id] = response_data.get(
                        'Peers', [])
                    clientUi.set_peers = gen_set_peer(clientUi.peers, clientUi.set_peers)
                    clientUi.connecting_peers = gen_set_connecting_peer(
                        clientUi.set_peers)
                # except Exception as e:
                #     messagebox.showerror(
                #         "Lỗi hệ thông", 'Lỗi khi refresh peer')
                #     print(f"Failed to download: {
                #         response.status_code} - {response.text}")
        time.sleep(30*60)


# Function to get the host IP address


def get_host_default_interface_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 1))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip


clientip = get_host_default_interface_ip()
# port = random.randint(6000, 7000)
port = 6003
server_ip = os.getenv('SERVER_IP')
server_port = 5000       # Replace with your server's listening port (integer)
clientUi = ClientUI(clientip, port)


url = f"http://{server_ip}:{server_port}/metainfo-file"  # Example endpoint
check_ip_url = f"http://{server_ip}:{server_port}/check-ip"


def check_ip_exists(clientip, port):
    try:
        response = requests.get(f"{check_ip_url}/{clientip}/{port}")
        if response.status_code == 200:
            return response.json().get('exists', False)
        return False
    except Exception as e:
        print(f"Error occurred while checking IP: {e}")
        return False

# Function to send the filename to the server via HTTP POST request


def send_filename_to_server(filelength, pieces, name, hostname=None):
    info_data = {
        'piecelength': 512000,
        'filelength': filelength,
        'pieces': pieces,
        'name': name
    }

    # Bencode the info dictionary
    bencoded_info = bencodepy.encode(info_data)

    # Compute SHA1 hash
    sha1_hash = hashlib.sha1(bencoded_info).digest()

    # URL-encode the hash and convert to hex
    info_hash = urllib.parse.quote(sha1_hash.hex())

    data = {
        'info': info_data,
        'info_hash': info_hash,
        'createBy': hostname or "Auto-Detected",
    }

    try:
        response = requests.post(url, json=data)
        if response.status_code == 201:
            print(f"File '{name}' added successfully!")
        elif response.status_code == 409:
            print(f"File '{name}' already exists in the database.")
        else:
            print(f"Failed to add file: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Error occurred: {e}")




def new_connection(addr, conn):
    print(f"Listen to this {addr}")
  
    while True:
        try:
            is_receive_full_request = False
            request = b''
            while not is_receive_full_request:
                data = conn.recv(1024)
                request += data
                if request[-5:] == b'<END>':
                    is_receive_full_request = True
                    request = request[:-5]

            message_dict = json.loads(request.decode('utf-8'))
            handle_message_client(conn, message_dict,clientUi.connecting_peers, clientUi.list_progress)
        except Exception as e:
            print(e)
            message_reject = {
                'type': EMesage_Type.REJECT.value,
                'message': "Lỗi kết nối"
            }
            message_reject_byte = convert_message_dict_to_byte(message_reject)
            conn.sendall(message_reject_byte)
            conn.send(b'<END>')
            conn.close()

    # Peer-to-peer server to accept incoming connections
# Biến lưu tổng tốc độ upload


        

def server_process():
    clientsocket = socket.socket()
    clientsocket.bind((clientip, port))
    clientsocket.listen(10)

   
    while True:
        conn, addr = clientsocket.accept()
        nconn = Thread(target=new_connection, args=(addr, conn))
        nconn.start()

def file_handshake(downloading_file, peer):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    client_socket.connect((peer['ip'], peer['port']))
    message_handshake = {
        "type": EMesage_Type.HANDSHAKE.value,
        "ip": clientUi.ip,
        "port": clientUi.port,
        "file": {
            "info_hash": downloading_file['info_hash'],
            "peer_id": downloading_file['peer_id']
        }
    }
    message_request_block_queue = []
    progress = [item for item in clientUi.list_progress if item['peer_id'] == downloading_file['peer_id'] and item['info_hash'] == downloading_file['info_hash']]

    while progress[0]['event'] != 'completed':
        isDisconnect = clientUi.isDisconnect(peer)
        if isDisconnect:
            break
        if message_handshake != {}:
            # send_messsage_handshake
            message_handshake_byte = convert_message_dict_to_byte(
                message_handshake)
            client_socket.sendall(message_handshake_byte)
            client_socket.send(b'<END>')
            message_handshake = {}
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
                client_socket, message_dict, peer, clientUi.list_progress, isDisconnect)

    print('END CONNECT')
    return client_socket





if __name__ == "__main__":
    print(f"Listening on: {clientip}:{port}")

    # Start the peer server in a thread
    Thread(target=server_process, args=(), daemon=True).start()
    Thread(target=refresh_peers_per_30_minutes, args=(), daemon=True).start()
    clientUi.run()
