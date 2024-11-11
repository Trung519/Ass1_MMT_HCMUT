message_request_handshake = {
  type: "HANDSHAKE",
  ip: string
  port: number
  file =  {
    info_hash :string,
    peer_id: string,
  }
        
}

message_request_handshake_folder{
  type: handshakeFolder
  ip: string
  port:number,
  folder : {
    info_hash: string
    peer_id: string
  }
}
message_response_handshake_folder = {
  type: HANDSHAKEFOLDER,
  info_hash: string
  files : [
    {
      peer_id: string
      file_index: number
      pieces_info: [
        {
          piece_index: number
        }
      ]
    }
  ]
}

message_response_handshake = {
  type: "HANDSHAKE",
  pieces_info : [
    {
      info_hash: string,
      peer_id: string,
      piece_index: number
    } 
  ]
}


message_response_handshake_folder = {
  type: HANDSHAKEFOLDER,
  info_hash:string
  peer_id
  files: [
    {
      file_index: number
      pieces_info: [
        {
          piece_index: number
        }
      ]
    }
  ]
}


message_reject = {
  type: "REJECT".
  message: ""
}

message_request_block_folder = {
  type: BLOCKFOLDER
  peer_id_client: string
  peer_id_server: string,
  file_index: number,
  piece_index: number,
  block_index: number,
  block_size: number,
  offset: number
}

message_request_block = {
        peer_id_client: string,
        peer_id_server: string,
        info_hash: string,
        piece_index: number
        block_index: number
        block_size: number
        offset:number,
        type: BLOCK
    }

message_response_block = {
  data: byte,
  info_hash: string,
  peer_id_client: string,
  piece_index: number,
  block_index: number
  offset: number,
  block_size: number
  type: "BLOCK",
}

peers = [
  {
    peer_id: string,
    info_hash: string,
    ip: string,
    port: number,
    speed: number
  }
]

set_peers = [
  {
    ip: string,
    port: string,
    speed: string,
    isConnected : boolean
  }
]


client gui info_hash và peer_id để định danh --> kiểm tra trong peers 
  nếu connecting_peer nhỏ hơn 5 kiểm tra trong peers
  nếu lớn hơn 5 reject


# gen mesage_request_block_queue = 

# gửi message request block: check xem block đã được tải chưa

# đợi nhận phản hồi từ server


# server gửi block gửi kèm thêm b'END' 

# client 

# todo:
- xử lí dừng  thread connect khi gọi hàm pause và hàm delete progress ✅
- upload thư mục
- phân luồng để tải nhiều file đồng thời hơn
- hiện các lỗi lên mesage_box
- cập nhật isdownloaded của piece



metainfo_folder = {
  name: string
  files: [
    {
      name: string
      length: number,
      pieces: string
      piece_length : number,
      path: string,
    }
  ]
}

progress_folder = {
  "metainfo_folder": {
    "info": {
      name: string,
      files: [
        {
          name: string
          length: number,
          pieces: string
          piece_length: number
          path: string
          pieces_info: [
            {
              piece_index: number,
              isDownloaded: boolean
              blocks: [
                {
                  offset: number,
                  block_size: number
                  isDownloaded: boolean
                  block_index: number
                }
              ]
            }
          ]
        }
      ]
      

    }
    "createBy": string,
    "info_hash": string
  }
  peer_id: string
  "folder_path" : string,
  "uploaded": number,
  "downloaded": number
  "left": number,
  "event": string
}




