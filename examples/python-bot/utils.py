"""
JSettlersプロトコル用のユーティリティ関数
"""
import struct
import socket
import logging

# デフォルトのバージョン情報
# JSettlersサーバーとの互換性のため、バージョン 2.5.00 (2500) を使用
DEFAULT_VERSION_NUM = "2500"  # 数値形式のバージョン (major*1000 + minor*100 + patch)
DEFAULT_VERSION_STR = "2.5.00"  # 文字列形式のバージョン

# ロガーの設定（モジュールレベル）
logger = logging.getLogger(__name__)

# Message type code to name mapping (from SOCMessage.java)
# ボットが受信する可能性のある主要なメッセージタイプ
MESSAGE_TYPES = {
    # 認証・接続関連
    999: "AUTHREQUEST",
    1000: "NULLMESSAGE",
    1020: "JOINCHANNELAUTH",
    1021: "JOINGAMEAUTH",
    1022: "IMAROBOT",
    1023: "BOTJOINGAMEREQUEST",
    1059: "REJECTCONNECTION",
    1071: "UPDATEROBOTPARAMS",
    9998: "VERSION",
    9999: "SERVERPING",
    
    # チャンネル関連
    1001: "NEWCHANNEL",
    1002: "CHANNELMEMBERS",
    1003: "CHANNELS",
    1004: "JOINCHANNEL",
    1005: "CHANNELTEXTMSG",
    1006: "LEAVECHANNEL",
    1007: "DELETECHANNEL",
    1008: "LEAVEALL",
    
    # ゲーム関連
    1013: "JOINGAME",
    1015: "DELETEGAME",
    1016: "NEWGAME",
    1017: "GAMEMEMBERS",
    1018: "STARTGAME",
    1019: "GAMES",
    1079: "NEWGAMEWITHOPTIONS",
    1078: "NEWGAMEWITHOPTIONSREQUEST",
    
    # ゲームプレイ
    1009: "PUTPIECE",
    1010: "GAMETEXTMSG",
    1011: "LEAVEGAME",
    1012: "SITDOWN",
    1024: "PLAYERELEMENT",
    1025: "GAMESTATE",
    1026: "TURN",
    1028: "DICERESULT",
    1029: "DISCARDREQUEST",
    1030: "ROLLDICEREQUEST",
    1031: "ROLLDICE",
    1032: "ENDTURN",
    1033: "DISCARD",
    1034: "MOVEROBBER",
    1035: "CHOOSEPLAYER",
    1036: "CHOOSEPLAYERREQUEST",
    1037: "REJECTOFFER",
    1038: "CLEAROFFER",
    1039: "ACCEPTOFFER",
    1040: "BANKTRADE",
    1041: "MAKEOFFER",
    1042: "CLEARTRADEMSG",
    1043: "BUILDREQUEST",
    1044: "CANCELBUILDREQUEST",
    1045: "BUYDEVCARDREQUEST",
    1046: "DEVCARDACTION",
    1047: "DEVCARDCOUNT",
    1048: "SETPLAYEDDEVCARD",
    1049: "PLAYDEVCARDREQUEST",
    1052: "PICKRESOURCES",
    1053: "PICKRESOURCETYPE",
    1054: "FIRSTPLAYER",
    1055: "SETTURN",
    1056: "ROBOTDISMISS",
    1057: "POTENTIALSETTLEMENTS",
    1066: "LONGESTROAD",
    1067: "LARGESTARMY",
    1069: "STATUSMESSAGE",
    1072: "ROLLDICEPROMPT",
    1086: "PLAYERELEMENTS",
    1089: "SIMPLEREQUEST",
    1090: "SIMPLEACTION",
    1094: "REMOVEPIECE",
    1099: "SETSPECIALITEM",
    1101: "SCENARIOINFO",
    1102: "ROBBERYRESULT",
    10001: "REVEALFOGHEX",
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
    if _is_numeric_message(message):
        return _parse_numeric_message(message)
    
    # テキスト形式のメッセージ（例: "GAMESTATE:game=test|state=15"）
    return _parse_text_message(message)


def _is_numeric_message(message: str) -> bool:
    """メッセージが数値形式かどうかを判定"""
    if '|' not in message:
        return False
    msg_type = message.split('|', 1)[0]
    return msg_type.isdigit()


def _parse_numeric_message(message: str) -> dict:
    """数値形式のメッセージをパース"""
    parts = message.split('|', 1)
    msg_code = int(parts[0])
    msg_type = MESSAGE_TYPES.get(msg_code)
    
    if msg_type is None:
        # 未知のメッセージタイプの場合はログに記録
        msg_type = f"UNKNOWN_{msg_code}"
        logger.warning(f"Unknown message type {msg_code}: {message[:100]}")
    
    return {
        "type": msg_type,
        "code": msg_code,
        "data": parts[1] if len(parts) > 1 else ""
    }


def _parse_text_message(message: str) -> dict:
    """テキスト形式のメッセージをパース"""
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
        version_num = params.get('versionint', DEFAULT_VERSION_NUM)
        version_str = params.get('version', DEFAULT_VERSION_STR)
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
