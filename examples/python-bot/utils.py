"""
JSettlersプロトコル用のユーティリティ関数
"""
import struct
import socket

def write_java_utf(sock: socket.socket, message: str):
    """
    Javaの DataOutputStream.writeUTF 形式でメッセージを送信
    
    Args:
        sock: ソケット
        message: 送信するメッセージ
    """
    # UTF-8にエンコード
    encoded = message.encode('utf-8')
    
    # 長さを2バイトのビッグエンディアンで送信
    length = len(encoded)
    if length > 65535:
        raise ValueError(f"Message too long: {length} bytes")
    
    sock.sendall(struct.pack('>H', length))
    sock.sendall(encoded)

def read_java_utf(sock: socket.socket) -> str:
    """
    Javaの DataInputStream.readUTF 形式でメッセージを受信
    
    Args:
        sock: ソケット
        
    Returns:
        受信したメッセージ
    """
    # 長さを2バイトのビッグエンディアンで受信
    length_bytes = b''
    while len(length_bytes) < 2:
        chunk = sock.recv(2 - len(length_bytes))
        if not chunk:
            raise ConnectionError("Connection closed")
        length_bytes += chunk
    
    length = struct.unpack('>H', length_bytes)[0]
    
    # メッセージ本体を受信
    data = b''
    while len(data) < length:
        chunk = sock.recv(length - len(data))
        if not chunk:
            raise ConnectionError("Connection closed")
        data += chunk
    
    return data.decode('utf-8')

def parse_message(message: str) -> dict:
    """
    JSettlersメッセージをパース
    
    Args:
        message: メッセージ文字列（例: "GAMESTATE:game=test|state=15"）
        
    Returns:
        パースされたメッセージ {"type": "GAMESTATE", "game": "test", "state": "15"}
    """
    if ':' not in message:
        return {"type": message}
    
    msg_type, data = message.split(':', 1)
    result = {"type": msg_type}
    
    # パラメータを解析
    if '|' in data:
        for param in data.split('|'):
            if '=' in param:
                key, value = param.split('=', 1)
                result[key] = value
    elif '=' in data:
        key, value = data.split('=', 1)
        result[key] = value
    
    return result

def build_message(msg_type: str, **params) -> str:
    """
    JSettlersメッセージを構築
    
    Args:
        msg_type: メッセージタイプ
        **params: パラメータ
        
    Returns:
        メッセージ文字列
    """
    if not params:
        return msg_type
    
    param_str = '|'.join(f"{k}={v}" for k, v in params.items())
    return f"{msg_type}:{param_str}"
