import random
import socket
import struct
import threading
import requests
from threading import Thread
import hashlib
import urllib.parse
import bencodepy
import uuid
import os
from tkinter import Tk, Label, Entry, Button, filedialog

peers = []

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


def generate_random_local_ip():
    # Tạo IP ngẫu nhiên từ dải 127.x.x.x (localhost)
    ip = f"127.{random.randint(1, 255)}.{random.randint(0, 255)}.{random.randint(1, 255)}"
    return ip

# Mỗi lần gọi hàm này bạn sẽ có một IP mới
clientip = generate_random_local_ip()
print(f"Client IP: {clientip}")
clienID = None
#clientip = get_host_default_interface_ip()
port = random.randint(6000, 7000)
server_ip = '127.0.0.1'  # Replace with your server's IP
server_port = 5000       # Replace with your server's listening port (integer)

clientsocket = socket.socket()
clientsocket.bind((clientip, port))
clientsocket.listen(10)
url = f"http://{server_ip}:{server_port}/metainfo-file"  # Example endpoint

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
            
        #Create and push in server tracker
        peer_id = create_peer_id()
        url_tracker = f"http://{server_ip}:{server_port}/track-peer?info_hash={info_hash}&peer_id={peer_id.decode()}&port={port}&uploaded={0}&downloaded={filelength}&left={0}&event={'completed'}&ip={clientip}"
        response = requests.get(url_tracker)
        if response.status_code == 200:
            print(f"Upload success: {response.text}")
        else:
            print(f"Failed to download: {response.status_code} - {response.text}")
    
    except Exception as e:
        print(f"Error occurred: {e}")

# Function to connect to a peer
def connect_to_peer(ip, port, peer_id):
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((ip, port))
        print(f"Peer {peer_id} connected to {ip}:{port}")

        # Send a test message
        message = f"Hello from peer {peer_id}"
        client_socket.sendall(message.encode())

        # Receive response from peer
        data = client_socket.recv(1024)
        print(f"Received from {ip}:{port}: {data.decode()}")

        return client_socket
    except Exception as e:
        print(f"Could not connect to {ip}:{port}: {e}")
        return None


# Create and use 2 way handshake in TCP:
# -------------------
PSTR = "BitTorrent protocol"
PSTRLEN = len(PSTR)
RESERVED = b'\x00' * 8  # 8 reserved bytes, all set to zero
PEER_ID_LENGTH = 20  # Length of the peer_id and info_hash

def create_peer_id():
    return f"-PB0001-{str(uuid.uuid4())[:12]}".encode()  # Ensure it's bytes

def create_handshake(info_hash, peer_id):
    # Ensure info_hash and peer_id are bytes
    if not isinstance(peer_id, bytes):
        raise ValueError("peer_id must be byte objects.")
    if not isinstance(info_hash, bytes):
        raise ValueError("info_hash must be byte objects.")

    # Create the handshake message
    handshake = struct.pack(f"!B{PSTRLEN}s8s20s20s",
                            PSTRLEN,  # pstrlen
                            PSTR.encode(),  # pstr
                            RESERVED,  # reserved bytes
                            info_hash,  # 20-byte info_hash
                            peer_id)  # 20-byte peer_id
    return handshake

def send_handshake(peer_ip, peer_port, info_hash, peer_id):
    # Open a connection to the peer
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((peer_ip, peer_port))

        # Create and send the handshake
        info_hash_bytes = bytes.fromhex(info_hash)
        handshake = create_handshake(info_hash_bytes, peer_id)
        
        s.send(handshake)

        # Wait for the peer's handshake response
        response = s.recv(49 + PSTRLEN)
        
        # Parse the peer's response
        if len(response) < 49 + PSTRLEN:
            print(f"Handshake failed: incomplete response from peer {peer_ip}")
            return False

        # Extract info_hash and peer_id from the response
        recv_pstrlen = struct.unpack("!B", response[0:1])[0]
        recv_pstr = response[1:1+recv_pstrlen].decode()
        recv_info_hash_bytes = response[28:48]
        recv_peer_id = response[48:68]

        # Validate the received info_hash and peer_id
        recv_info_hash = recv_info_hash_bytes.hex()
        if recv_info_hash != info_hash:
            print(f"Info hash mismatch from peer {peer_ip}. Dropping connection.")
            return False

        print(f"Handshake successful with peer {peer_ip}. Peer ID: {recv_peer_id.decode(errors='ignore')}")
        return True

    except Exception as e:
        print(f"Error during handshake with peer {peer_ip}: {e}")
        return False

def download_file(info_hash, event):
    global clienID
    peer_id = create_peer_id()  # Generate a 20-byte peer_id for this client
    left = 0  # Adjust based on actual download status
    uploaded = 0
    downloaded = 0
    clienID = peer_id

    # Request to tracker server to get the list of peers
    url = f"http://{server_ip}:{server_port}/track-peer?info_hash={info_hash}&peer_id={peer_id.decode()}&port={port}&uploaded={uploaded}&downloaded={downloaded}&left={left}&event={event}&ip={clientip}"
    
    try:
        response = requests.get(url)
        if response.status_code == 200:
            print(f"Downloaded: {response.text}")
            peers_data = response.json().get("Peers", [])
            
            # Start handshake with each peer
            for peer in peers_data:
                peer_ip = peer.get("ip")
                peer_port = peer.get("port")
                
                # Initiating handshake with each peer
                if send_handshake(peer_ip, peer_port, info_hash, peer_id):
                    print(f"Peer {peer_ip}:{peer_port} handshake successful.")
                    # Proceed to download logic after successful handshake

        else:
            print(f"Failed to download: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Error during download: {e}")

# Handle new peer connections as the server

stop_event = threading.Event()

# This is function to decode handshake data
def parse_handshake(handshake_message):
    """Parse the received handshake message."""
    if len(handshake_message) != 68:
        raise ValueError("Invalid handshake length. Expected 68 bytes.")

    # Unpack the entire handshake message in one go
    pstrlen, pstr, reserved, received_info_hash, received_peer_id = struct.unpack(
        f"!B{PSTRLEN}s8s20s20s", handshake_message[:68])

    # Decode the protocol string (pstr)
    pstr = pstr.decode()
    received_info_hash_hex = received_info_hash.hex()
    
    return pstrlen, pstr, reserved, received_info_hash_hex, received_peer_id

#function to get new connect with IP need to change data
def new_connection(addr, conn):
    print(f"Waiting for handshake from peer at {addr}...")

    # First, try to receive the full 68-byte handshake
    handshake_length = 68
    response = b''
    while len(response) < handshake_length:
        chunk = conn.recv(handshake_length - len(response))  # Receive in chunks until we have all 68 bytes
        if not chunk:
            print("Connection closed unexpectedly.")
            return
        response += chunk

    print(f"Received raw bytes from peer {addr}: {response}")

    if len(response) != handshake_length:  # Handshake should be 68 bytes
        print(f"Invalid handshake length: {len(response)}")
        conn.close()
        return

    try:
        # Parse the handshake from the peer
        pslen, pstr, reserved, received_info_hash_byte, received_peer_id = parse_handshake(response)
        if pstr == PSTR:
            print("Valid BitTorrent protocol handshake received.")
            print(f"Received info_hash: {received_info_hash_byte}")
            print(f"Received peer_id: {received_peer_id}")

            # Use the received info_hash for further communication
            # Send back a handshake using the same info_hash
            # my_peer_data = requests.get(f"http://{server_ip}:{server_port}/get-id/{clientip}")
            # my_peer_ip = my_peer_data.text
            # print("============", my_peer_data)
            received_info_hash = bytes.fromhex(received_info_hash_byte)
            # handshake_message = create_handshake(received_info_hash,my_peer_ip.encode('utf-8'))
            print("================", clienID)
            handshake_message = create_handshake(received_info_hash,clienID)
            conn.sendall(handshake_message)
            print(f"Sent handshake back to {addr} with info_hash: {received_info_hash}")

        else:
            print("Unexpected protocol string in handshake.")
    except Exception as e:
        print(f"Error processing handshake: {e}")

    # Close the connection
    conn.close()

# Peer-to-peer server để chấp nhận các kết nối đến
def peer_server():
    while not stop_event.is_set():  # Kiểm tra stop_event để dừng server
        try:
            conn, addr = clientsocket.accept()
            nconn = threading.Thread(target=new_connection, args=(addr, conn))
            nconn.start()
        except Exception as e:
            print(f"Error accepting connection: {e}")
            break  # Thoát khỏi vòng lặp nếu có lỗi lớn xảy ra

# Khởi động server trên thread riêng
def start_peer_server():
    server_thread = threading.Thread(target=peer_server)
    server_thread.start()

# Chọn file từ GUI và bắt đầu upload
def select_file():
    file_path = filedialog.askopenfilename()
    if file_path:
        filelength = os.path.getsize(file_path)
        name = os.path.basename(file_path)
        
        with open(file_path, 'rb') as f:
            file_data = f.read()
            pieces = hashlib.sha256(file_data).hexdigest()  # Simple hash example
        
        hostname = hostname_entry.get()
        send_filename_to_server(filelength, pieces, name, hostname)

# Khởi động GUI upload file
def start_upload_gui():
    global hostname_entry
    root = Tk()
    root.title("File Uploader")

    Label(root, text="Enter Hostname:").pack(pady=5)
    hostname_entry = Entry(root)
    hostname_entry.pack(pady=5)

    Button(root, text="Select File to Upload", command=select_file).pack(pady=20)
    root.mainloop()
if __name__ == "__main__":
    print(f"Listening on: {clientip}:{port}")

    # Start the peer server thread
    start_peer_server()

    while True:
        # Ask the user if they want to upload or download
        action = input("Do you want to upload or download a file? (upload/download) or type 'exit' to stop: ").lower()

        if action == "upload":
            start_upload_gui()

        elif action == "download":
            info_hash = input("Enter info_hash of the file you want to download: ")
            event = input("Enter event (started/stopped/completed): ").lower()

            if event in ['started', 'stopped', 'completed']:
                download_file(info_hash, event)
                if event == 'stopped':
                    print("Download stopped.")
                    continue  # Quay lại đầu vòng lặp để hỏi lại action
            else:
                print("Invalid event. Please enter 'started', 'stopped', or 'completed'.")

        elif action == "exit":
            print("Exiting the program.")
            break  # Dừng vòng lặp khi người dùng chọn 'exit'

        else:
            print("Invalid action. Please enter 'upload', 'download', or 'exit'.")
