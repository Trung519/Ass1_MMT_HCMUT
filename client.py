import random
import socket
import requests
from threading import Thread
import hashlib
import urllib.parse
import bencodepy
import uuid
import os
from tkinter import Tk, Label, Entry, Button, filedialog, messagebox

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

clientip = get_host_default_interface_ip()
port = random.randint(6000, 7000)
server_ip = '127.0.0.1'  # Replace with your server's IP
server_port = 5000       # Replace with your server's listening port (integer)

clientsocket = socket.socket()
clientsocket.bind((clientip, port))
clientsocket.listen(10)
url = f"http://{server_ip}:{server_port}/metainfo-file"  # Example endpoint
check_ip_url = f"http://{server_ip}:{server_port}/check-ip"

# Function to check if IP exists in server database
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

# Function to download file using P2P
def download_file(info_hash, event):
    peer_id = str(uuid.uuid4())
    left = 0  # Adjust based on actual download status
    uploaded = 0
    downloaded = 0

    url = f"http://{server_ip}:{server_port}/track-peer?info_hash={info_hash}&peer_id={peer_id}&port={port}&uploaded={uploaded}&downloaded={downloaded}&left={left}&event={event}&ip={clientip}"
    
    try:
        response = requests.get(url)
        if response.status_code == 200:
            print(f"Successfully downloaded: {response.text}")
        else:
            print(f"Failed to download: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Error during download: {e}")

# Handle new peer connections as the server
def new_connection(addr, conn):
    print(f"New peer connected from {addr}")
    
    # Generate server's info_hash and peer_id for demonstration
    server_info_hash = "server_info_hash"
    server_peer_id = "server_peer_id"
    
    # Send the server's info_hash and peer_id
    conn.sendall(f"{server_info_hash},{server_peer_id}".encode())
    
    # Receive client response
    response = conn.recv(1024).decode()
    print(f"Received from peer {addr}: {response}")
    
    conn.close()

# Peer-to-peer server to accept incoming connections
def peer_server():
    while True:
        addr, conn = clientsocket.accept()
        nconn = Thread(target=new_connection, args=(addr, conn))
        nconn.start()

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

# Function to start the GUI
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

    # Start the peer server in a thread
    Thread(target=peer_server, args=()).start()

    # Ask the user if they want to upload or download
    action = input("Do you want to upload or download a file? (upload/download): ").lower()

    if action == "upload":
        start_upload_gui()

    elif action == "download":
        info_hash = input("Enter info_hash of the file you want to download: ")
        event = input("Enter event (started/stopped/completed): ").lower()

        if event in ['started', 'stopped', 'completed']:
            download_file(info_hash, event)
        else:
            print("Invalid event. Please enter 'started', 'stopped', or 'completed'.")

    else:
        print("Invalid action. Please enter 'upload' or 'download'.")
