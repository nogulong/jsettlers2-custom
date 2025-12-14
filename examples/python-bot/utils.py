"""
JSettlersプロトコル用のユーティリティ関数
"""
import struct
import socket

# Message type code to name mapping (from SOCMessage.java)
MESSAGE_TYPES = {
    1003: "CHANNELS",
    1019: "GAMES",
    1020: "JOINCHANNELAUTH",
    1021: "JOINGAMEAUTH",
    1022: "IMAROBOT",
    1023: "BOTJOINGAMEREQUEST",
    1024: "PLAYERELEMENT",
    1025: "GAMESTATE",
    1026: "TURN",
    1028: "DICERESULT",
    1071: "UPDATEROBOTPARAMS",
    9998: "VERSION",
    9999: "SERVERPING",
}

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
    
    サーバーは数値形式（例: "9998|2700,2.7.00,..."）または
    テキスト形式（例: "GAMESTATE:game=test|state=15"）でメッセージを送信します。
    
    Args:
        message: メッセージ文字列
        
    Returns:
        パースされたメッセージ辞書
        例: {"type": "VERSION", "data": "2700,2.7.00,..."}
        または {"type": "GAMESTATE", "game": "test", "state": "15"}
    """
    # 数値形式のメッセージをチェック（例: "9998|..."）
    if '|' in message:
        parts = message.split('|', 1)
        if parts[0].isdigit():
            msg_code = int(parts[0])
            msg_type = MESSAGE_TYPES.get(msg_code, f"UNKNOWN_{msg_code}")
            result = {
                "type": msg_type,
                "code": msg_code,
                "data": parts[1] if len(parts) > 1 else ""
            }
            return result
    
    # テキスト形式のメッセージ（例: "GAMESTATE:game=test|state=15"）
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
    
    サーバーが期待する形式でメッセージを構築します。
    VERSIONとIMAROBOTは特別な形式を使用します。
    
    Args:
        msg_type: メッセージタイプ（"VERSION", "IMAROBOT", etc.）
        **params: パラメータ
        
    Returns:
        メッセージ文字列
    """
    # VERSIONメッセージの特別処理
    if msg_type == "VERSION":
        # VERSION|versionnum,versionstr,build,feats,locale
        # 例: "VERSION|2500,2.5.00,,;6pl;sb;,en_US"
        version_num = params.get('versionint', '2500')
        version_str = params.get('version', '2.5.00')
        build = params.get('build', '')
        feats = params.get('cliFeats', '')
        locale = params.get('locale', 'en_US')
        return f"VERSION|{version_num},{version_str},{build},{feats},{locale}"
    
    # IMAROBOTメッセージの特別処理
    if msg_type == "IMAROBOT":
        # IMAROBOT|nickname,cookie,rbclass
        nickname = params.get('nickname', '')
        cookie = params.get('cookie', '')
        rbclass = params.get('rbclass', '')
        return f"IMAROBOT|{nickname},{cookie},{rbclass}"
    
    # その他のメッセージ（テキスト形式）
    if not params:
        return msg_type
    
    param_str = '|'.join(f"{k}={v}" for k, v in params.items())
    return f"{msg_type}:{param_str}"
