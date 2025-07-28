import json

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

# C2S: Client to Server
MSG_JOIN_LOBBY = 'JOIN_LOBBY'
MSG_CREATE_ROOM = 'CREATE_ROOM'
MSG_LIST_ROOMS = 'LIST_ROOMS'
MSG_JOIN_ROOM = 'JOIN_ROOM'
MSG_LEAVE_ROOM = 'LEAVE_ROOM'
MSG_SEND_CHAT = 'SEND_CHAT'
MSG_PLAYER_INPUT = 'PLAYER_INPUT'

# S2C: Server to Client
MSG_JOIN_LOBBY_ACK = 'JOIN_LOBBY_ACK'
MSG_LOBBY_STATE = 'LOBBY_STATE'
MSG_CREATE_ROOM_ACK = 'CREATE_ROOM_ACK'
MSG_JOIN_ROOM_ACK = 'JOIN_ROOM_ACK'
MSG_ROOM_STATE = 'ROOM_STATE'
MSG_GAME_UPDATE = 'GAME_UPDATE'
MSG_PLAYER_JOINED_ROOM = 'PLAYER_JOINED_ROOM'
MSG_PLAYER_LEFT_ROOM = 'PLAYER_LEFT_ROOM'
MSG_CHAT_MESSAGE = 'CHAT_MESSAGE'
MSG_ERROR = 'ERROR'

# Input Action Constants
# Add more here later
INPUT_ACTION_MOVE = 'MOVE'
INPUT_ACTION_LOCK_OBJECT = 'LOCK_OBJECT'
INPUT_ACTION_RELEASE_OBJECT = 'RELEASE_OBJECT'