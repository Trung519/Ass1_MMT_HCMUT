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

    # print('PORT', port)
    # print('IP', ip)
    # Tính toán số lượng Complete và Incomplete
    complete_count = sum(1 for peer in peers if peer['left'] == 0)
    incomplete_count = sum(1 for peer in peers if peer['left'] != 0)

    # Lọc danh sách peer có event khác 'stopped'
    active_peers = []
    for peer in peers:
        if peer['event'] == 'stopped':
            continue
        if peer['peer_id'] == peer_id:
            continue

        if str(peer['port']) == str(port) and peer['ip'] == ip:
            continue
        active_peers += [{
            "peer_id": peer["peer_id"],
            "client_id": peer_id,
            "ip": peer["ip"],
            "port": peer["port"],
            "info_hash": info_hash,
            "speed": 0
            }]

    # active_peers = [
    #     {
    #         "peer_id": peer["peer_id"],
    #         "ip": peer["ip"],
    #         "port": peer["port"],
    #         "info_hash": info_hash,
    #         "speed": 0
    #     }
#     for peer in peers if peer["event"] != "stopped" and peer["peer_id"] != peer_id
    #     and (peer['port'] != port or peer['ip'] != ip)
    # ]
    return jsonify({
        "Complete": complete_count,
        "Incomplete": incomplete_count,
        "Peers": active_peers
    }), 200

# POST để lưu metainfo file
@app.route('/metainfo-file', methods=['POST'])
def add_metainfo():
    data = request.json

    # print('data')
    # print(data)

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



# GET API để lấy tất cả metainfo file
@app.route('/metainfo-files', methods=['GET'])
def get_all_metainfo():
    # Lấy tất cả các document từ collection metainfo_file
    metainfo_files = list(metainfo_file_collection.find())

    # Chuyển ObjectId thành chuỗi để trả về trong JSON
    for metainfo in metainfo_files:
        metainfo['_id'] = str(metainfo['_id'])

    return jsonify(metainfo_files), 200


if __name__ == '__main__':
    server_ip = os.getenv('SERVER_IP')
    app.run(host=server_ip, port=5000, debug=True)
