import json

# Client to Server
MSG_HOST_GAME = 'HOST_GAME'
MSG_JOIN_GAME = 'JOIN_GAME'
MSG_LEAVE_GAME = 'LEAVE_GAME'
MSG_LOCK_OBJECT = 'LOCK_OBJECT'
MSG_RELEASE_OBJECT = 'RELEASE_OBJECT'
MSG_MOVE_LOCKED_OBJECT = 'MOVE_LOCKED_OBJECT'
MSG_PUZZLE_SOLVED = 'PUZZLE_SOLVED'
MSG_PLAYER_INPUT = 'PLAYER_INPUT'

# Player Input Actions
INPUT_ACTION_LOCK_OBJECT = 'LOCK_OBJECT'
INPUT_ACTION_RELEASE_OBJECT = 'RELEASE_OBJECT'
INPUT_ACTION_MOVE_OBJECT = 'MOVE_OBJECT'

# Server to Client ACKs
MSG_HOST_GAME_ACK = 'HOST_GAME_ACK'
MSG_JOIN_GAME_ACK = 'JOIN_GAME_ACK'
MSG_LEAVE_GAME_ACK = 'LEAVE_GAME_ACK'
MSG_LOCK_OBJECT_ACK = 'LOCK_OBJECT_ACK'
MSG_RELEASE_OBJECT_ACK = 'RELEASE_OBJECT_ACK'
MSG_PUZZLE_SOLVED_ACK = 'PUZZLE_SOLVED_ACK'

# Server to Client Broadcasts 
MSG_PLAYER_JOINED_BROD = 'PLAYER_JOINED_BROD'
MSG_PLAYER_LEFT_BROD = 'PLAYER_LEFT_BROD'
MSG_LOCK_OBJECT_BROD = 'LOCK_OBJECT_BROD'
MSG_RELEASE_OBJECT_BROD = 'RELEASE_OBJECT_BROD'
MSG_MOVE_LOCKED_OBJECT_BROD = 'MOVE_LOCKED_OBJECT_BROD'
MSG_PUZZLE_SOLVED_BROD = 'PUZZLE_SOLVED_BROD'

# Error
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