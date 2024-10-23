from dotenv import load_dotenv
import os
import requests

load_dotenv()


server_url = os.getenv('SERVER_URL')
ENDPOINT_METAINFO = server_url + '/metainfo-file'


def add_metainfo_file(body):
    try:
        response = requests.post(ENDPOINT_METAINFO, json=body)
        if response.status_code == 201:
            # Sử dụng cú pháp từ điển
            print(f"File '{body['info']['name']}' added successfully!")
        elif response.status_code == 409:
            print(f"File '{body['info']['name']
                           }' already exists in the database.")
        else:
            print(f"Failed to add file: {
                  response.status_code} - {response.text}")
    except Exception as e:
        print(f"Error occurred: {e}")


def get_all_metainfo_file():
    try:
        response = requests.get(ENDPOINT_METAINFO+'s')
        # Kiểm tra mã trạng thái phản hồi
        response.raise_for_status()  # Gây ra lỗi nếu mã trạng thái không phải 2xx
        return response.json()  # Trả về dữ liệu JSON nếu có
    except requests.exceptions.RequestException as e:
        print(f"Error occurred: {e}")
        return None  # Trả về None nếu có lỗi
