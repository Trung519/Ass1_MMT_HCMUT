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
port = 6000
clientUi = ClientUI(clientip, port)





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


if __name__ == "__main__":
    print(f"Listening on: {clientip}:{port}")

    # Start the peer server in a thread
    Thread(target=server_process, args=(), daemon=True).start()
    Thread(target=refresh_peers_per_30_minutes, args=(), daemon=True).start()
    clientUi.run()
