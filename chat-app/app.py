from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
import random
import string

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

# Dictionary để lưu trạng thái người dùng (username, socket id và ip)
users = {}

# Tạo một tên người dùng ngẫu nhiên
def generate_random_username():
    return 'User_' + ''.join(random.choices(string.ascii_letters + string.digits, k=6))

@app.route('/')
def index():
    return render_template('index.html')

# Khi người dùng kết nối
@socketio.on('connect')
def handle_connect():
    # Tạo tên người dùng ngẫu nhiên
    username = generate_random_username()
    # Lưu trữ thông tin người dùng, socket id, và địa chỉ IP
    users[request.sid] = {
        'username': username,
        'ip': request.remote_addr
    }
    print(f"{username} đã kết nối. SID: {request.sid}, IP: {request.remote_addr}")
    
    # Gửi danh sách người dùng đang online cho tất cả
    emit('update_user_list', [user['username'] for user in users.values()], broadcast=True)

# Khi người dùng ngắt kết nối
@socketio.on('disconnect')
def handle_disconnect():
    user = users.pop(request.sid, None)
    if user:
        print(f"{user['username']} đã ngắt kết nối. IP: {user['ip']}")
    
    # Cập nhật lại danh sách người dùng online
    emit('update_user_list', [user['username'] for user in users.values()], broadcast=True)

# Khi nhận tin nhắn từ người dùng
@socketio.on('send_message')
def handle_send_message(data):
    recipient = data['recipient']  # Người nhận
    message = data['message']  # Nội dung tin nhắn
    sender = users[request.sid]['username']  # Người gửi

    # Tìm socket id của người nhận
    recipient_sid = next((sid for sid, user in users.items() if user['username'] == recipient), None)
    
    if recipient_sid:
        # Gửi tin nhắn riêng cho người nhận
        emit('private_message', {'sender': sender, 'message': message}, room=recipient_sid)
        
        # Gửi tin nhắn cho chính người gửi để hiển thị tin nhắn của mình
        emit('private_message', {'sender': sender, 'message': message}, room=request.sid)
    else:
        # Nếu không tìm thấy người nhận, báo lỗi
        emit('error', {'message': f'Người dùng {recipient} không tồn tại.'}, room=request.sid)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)
