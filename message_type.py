from enum import Enum


class EMesage_Type(Enum):
    REJECT = 'REJECT'   # tin hieu disconnect
    HANDSHAKE = 'HANDSHAKE'  # gui va nhan handshake
    HANDSHAKEFOLDER = 'HANDSHAKEFOLDER'
    BLOCKFOLDER = 'BLOCKFOLDER'
    BLOCK = 'BLOCK'   # gui va nhan block
