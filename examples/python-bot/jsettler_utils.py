"""
JSettlersプロトコル用のユーティリティ関数
(問題文で使用されているユーティリティ関数の実装)
"""
import struct
import socket
import re


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
        message: メッセージ文字列（例: "1015|aaa" や "1079|aaa,2700,BC=t4"）
        
    Returns:
        パースされたメッセージ辞書
    """
    # 1. メッセージIDと中身を分離 (区切りはパイプ "|")
    if '|' not in message:
        return {"type": message, "args": []}
    
    msg_type, content = message.split('|', 1)
    result = {"type": msg_type}
    
    # 2. 中身をトークンに分割
    # サーバーはパイプ "|" とカンマ "," の両方を区切りに使うため、正規表現で分割
    tokens = re.split(r'[|,]', content)
    
    # 空のトークンを除去（末尾のカンマなどで空文字が入るのを防ぐ）
    tokens = [t for t in tokens if t]
    result["args"] = tokens  # 生のリストも保存しておく
    
    # 3. key=value 形式の解析
    for token in tokens:
        if '=' in token:
            key, value = token.split('=', 1)
            result[key] = value
            
    # 4. 位置による値の割り当て (Positional Arguments)
    if len(tokens) > 0:
        # 多くのメッセージで、最初の値は「ゲーム名」です
        if msg_type in ["1015", "1023", "1079", "1021", "1013"]:
             if "game" not in result:
                 result["game"] = tokens[0]

    if len(tokens) > 1:
        # JOINGAMEAUTH(1021) の場合、2番目はプレイヤー番号
        if msg_type == "1021":
             if "playerNumber" not in result:
                 result["playerNumber"] = tokens[1]
                 
        # TURN(1026) の場合、1番目がプレイヤー番号
        if msg_type == "1026":
             if "playerNumber" not in result:
                 result["playerNumber"] = tokens[1]

    return result


def parse_board_layout_1084(message: str) -> dict:
    """
    BOARDLAYOUT2 (1084) メッセージをパース
    
    Args:
        message: 1084メッセージ文字列
        
    Returns:
        パースされたボードレイアウト情報
    """
    result = {}
    
    # メッセージを分割
    parts = message.split('|')
    if len(parts) < 2:
        return result
    
    content = parts[1]
    
    # HL, NL, RH を抽出
    hl_match = re.search(r'HL,\[([\d,\-]+)\]', content)
    if hl_match:
        hl_str = hl_match.group(1)
        result["HL"] = [int(x) for x in hl_str.split(',')]
    
    nl_match = re.search(r'NL,\[([\d,\-]+)\]', content)
    if nl_match:
        nl_str = nl_match.group(1)
        result["NL"] = [int(x) for x in nl_str.split(',')]
    
    rh_match = re.search(r'RH,(\d+)', content)
    if rh_match:
        result["RH"] = int(rh_match.group(1))
    
    return result
