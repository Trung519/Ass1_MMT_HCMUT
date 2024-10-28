import os
from flask import Flask, request, jsonify
from pymongo import MongoClient
from bson.objectid import ObjectId
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Lấy URL MongoDB từ biến môi trường
mongo_url = os.getenv('MONGO_URL')
db_name = os.getenv('DB_NAME')

# Kết nối tới MongoDB
client = MongoClient(mongo_url)
db = client[db_name]  # Thay 'mydatabase' bằng tên database của bạn

# Collection tracking peer
tracking_peer_collection = db['tracking_peer']
# Collection metainfo file
metainfo_file_collection = db['metainfo_file']
# Collection peer
clients_db = db['peers']


@app.route('/check-ip/<ip>/<int:port>', methods=['GET'])
def check_ip(ip, port):
    # Check if the IP and port exist in the 'peers' collection
    client = clients_db.find_one({'ip': ip, 'port': port})

    if client:
        # If IP and port exist, return a message indicating its presence
        return jsonify({'exists': True, 'id': str(client['_id']), 'hostname': client['hostname']})
    else:
        # If IP and port don't exist, add it to the database with 'id' and 'hostname'
        # Get hostname from query params (default: 'unknown')
        hostname = request.args.get('hostname', 'unknown')

        # Insert new client document with 'id', 'ip', 'port', and 'hostname'
        new_client = {
            '_id': ObjectId(),  # Generate a new unique ID
            'ip': ip,
            'port': port,
            'hostname': hostname
        }
        clients_db.insert_one(new_client)

        # Return the new client info
        return jsonify({'exists': False, 'id': str(new_client['_id']), 'hostname': hostname})


# GET API để nhận tham số query và lưu vào tracking_peer
@app.route('/track-peer', methods=['GET'])
def track_peer():
    # Lấy các tham số query
    info_hash = request.args.get('info_hash')
    peer_id = request.args.get('peer_id')
    port = request.args.get('port')
    uploaded = request.args.get('uploaded')
    downloaded = request.args.get('downloaded')
    left = request.args.get('left')
    event = request.args.get('event')
    ip = request.args.get('ip')

    # Kiểm tra xem tất cả các tham số có tồn tại không
    if not all([info_hash, peer_id, port, uploaded, downloaded, left, event, ip]):
        return jsonify({"error": "Missing query parameters"}), 400

    # Kiểm tra nếu peer_id đã tồn tại trong collection
    existing_peer = tracking_peer_collection.find_one({"peer_id": peer_id})

    peer_data = {
        "info_hash": info_hash,
        "peer_id": peer_id,
        "port": int(port),  # Chuyển đổi sang số nguyên nếu cần
        "uploaded": int(uploaded),  # Chuyển đổi sang số nguyên nếu cần
        "downloaded": int(downloaded),  # Chuyển đổi sang số nguyên nếu cần
        "left": int(left),  # Chuyển đổi sang số nguyên nếu cần
        "event": event,
        "ip": ip
    }

    if (event == 'stopped'):
        # Nếu event là 'stopped', xóa peer khỏi collection
        tracking_peer_collection.delete_one({"peer_id": peer_id})
    if existing_peer:
        tracking_peer_collection.update_one(
            {"peer_id": peer_id},
            {"$set": peer_data}
        )

    else:
        # Nếu peer_id chưa tồn tại, thêm dữ liệu mới vào MongoDB
        result = tracking_peer_collection.insert_one(peer_data)

    if not info_hash:
        return jsonify({"error": "Missing 'info_hash' query parameter"}), 400

        # Tìm tất cả các peer có info_hash tương ứng
    peers = list(tracking_peer_collection.find(
        {"info_hash": info_hash}).sort("uploaded", -1))

    print("peer has hash info", peers)
    # Tính toán số lượng Complete và Incomplete
    complete_count = sum(1 for peer in peers if peer['left'] == 0)
    incomplete_count = sum(1 for peer in peers if peer['left'] != 0)

    # Lọc danh sách peer có event khác 'stopped'
    active_peers = [
        {
            "peer_id": peer["peer_id"],
            "ip": peer["ip"],
            "port": peer["port"],
            "speed": 0
        }
        for peer in peers if peer["event"] != "stopped" and peer["peer_id"] != peer_id
        and peer['port'] != port
    ]
    return jsonify({
        "Complete": complete_count,
        "Incomplete": incomplete_count,
        "Peers": active_peers
    }), 200

# POST để lưu metainfo file


@app.route('/metainfo-file', methods=['POST'])
def add_metainfo_file():
    data = request.json

    print('data')
    print(data)

    # Kiểm tra xem 'info' có trong request hay không
    if 'info' not in data:
        return jsonify({"error": "'info' field is required"}), 400

    # Kiểm tra trùng lặp dựa trên 'info'
    existing_file = metainfo_file_collection.find_one({"info": data['info']})

    if existing_file:
        return jsonify({"error": "A metainfo file with the same 'info' already exists"}), 409

    # Nếu không trùng lặp, thêm document mới vào MongoDB
    result = metainfo_file_collection.insert_one(data)

    return jsonify({
        "message": "Metainfo file added successfully",
        "id": str(result.inserted_id)
    }), 201


# GET API để lấy metainfo file theo ObjectId
@app.route('/metainfo-file/<id>', methods=['GET'])
def get_metainfo_file(id):
    try:
        # Chuyển chuỗi id thành ObjectId
        object_id = ObjectId(id)
    except:
        return jsonify({"error": "Invalid ObjectId"}), 400

    # Tìm document theo ObjectId
    metainfo = metainfo_file_collection.find_one({"_id": object_id})

    if metainfo:
        # Chuyển ObjectId thành chuỗi để trả về trong JSON
        metainfo['_id'] = str(metainfo['_id'])
        return jsonify(metainfo), 200
    else:
        return jsonify({"error": "Metainfo file not found"}), 404


# GET API để lấy tất cả metainfo file
@app.route('/metainfo-files', methods=['GET'])
def get_all_metainfo_files():
    # Lấy tất cả các document từ collection metainfo_file
    metainfo_files = list(metainfo_file_collection.find())

    # Chuyển ObjectId thành chuỗi để trả về trong JSON
    for metainfo in metainfo_files:
        metainfo['_id'] = str(metainfo['_id'])

    return jsonify(metainfo_files), 200


if __name__ == '__main__':
    app.run(debug=True)
