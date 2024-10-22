import socket
from threading import Thread

peers = []


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
port = 22236

clientsocket = socket.socket()
clientsocket.bind((clientip, port))
clientsocket.listen(10)


# Hàm kết nối đến các peer khác
def connect_to_peer(ip, port, peer_id):
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((ip, port))
        print(f"Peer {peer_id} connected to {ip}:{port}")

        # Gửi tin nhắn test
        message = f"Hello from peer {peer_id}"
        client_socket.sendall(message.encode())

        # Nhận phản hồi từ peer
        data = client_socket.recv(1024)
        print(f"Received from {ip}:{port}: {data.decode()}")

        return client_socket
    except Exception as e:
        print(f"Could not connect to {ip}:{port}: {e}")
        return None


def new_connection(addr, conn):
    # gửi/nhan hash_info
    # gửi/nhan bitfield
    print(addr)


def peer_server():

    while True:
        addr, conn = clientsocket.accept()
        # tạo luồng xử lí giao tiếp
        nconn = Thread(target=new_connection, args=(addr, conn))
        nconn.start()


if __name__ == "__main__":
    # hostname = socket.gethostname()

    print("Listening on: {}:{}".format(clientip, port))
    # tao luong listen de cac peer khac connect
    Thread(target=peer_server, args=()).start()
    # tao luong de nhan lenh tu user UI
    # lay metainfo
    # hash_info
    # send request --> receive peers
    # connect to peer
