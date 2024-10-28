from enum import Enum


class EMesage_Type(Enum):
    REJECT = 'REJECT'   # tin hieu disconnect
    HANDSHAKE = 'HANDSHAKE'  # gui va nhan handshake
    BLOCK = 'BLOCK'   # gui va nhan block
