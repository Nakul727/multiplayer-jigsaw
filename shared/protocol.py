import json

MSG_HOST_GAME = 'HOST_GAME'
MSG_JOIN_GAME = 'JOIN_GAME'
MSG_LEAVE_GAME = 'LEAVE_GAME'

MSG_HOST_GAME_ACK = 'HOST_GAME_ACK'
MSG_JOIN_GAME_ACK = 'JOIN_GAME_ACK'
MSG_LEAVE_GAME_ACK = 'LEAVE_GAME_ACK'

MSG_PLAYER_JOINED = 'PLAYER_JOINED'
MSG_PLAYER_LEFT = 'PLAYER_LEFT'
MSG_ERROR = 'ERROR'

def serialize(msg_type: str, payload: dict) -> bytes:
    """
    Serializes a message dictionary into bytes for network transmission
    """
    message = {'type': msg_type, 'payload': payload}
    return json.dumps(message).encode('utf-8')

def deserialize(data: bytes) -> dict:
    """
    Deserializes bytes from the network into a message dictionary
    """
    return json.loads(data.decode('utf-8'))