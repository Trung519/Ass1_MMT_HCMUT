message_request_handshake = {
  type: "HANDSHAKE",
  DOWNLOADING_FILE = [
    {
      "info_hash": string,
      "peer_id" : string,
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


message_reject = {
  type: "REJECT".
  message: ""
}

message_request_block = {
  peer_id_client: string,
  peer_id_server: string
  info_hash: string,
  piece_index : number,
  offset:number
  type: "BLOCK"
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


# gen mesage_request_block_queue = 

# gửi message request block: check xem block đã được tải chưa

# đợi nhận phản hồi từ server


# server gửi block gửi kèm thêm b'END' 

# client 