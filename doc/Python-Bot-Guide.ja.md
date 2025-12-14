# PythonボットとJSettlersの統合ガイド

このガイドでは、PyTorchで実装したエージェント（ニューラルネットワーク）をJSettlersサーバーと対戦させる方法を説明します。

> **注意:** Python連携が正常に動作するか確認するには、まず [Python Integration Verification Guide](Python-Integration-Verification.ja.md) を参照してください。

## 概要

このガイドは、以下のような状況を想定しています：

- PyTorchで学習済みのエージェント（NN）がある
- Observationを入力として受け取り、Actionを出力する
- 学習済みモデルをJSettlersで評価したい
- **Rustは使用しない** - 純粋にPythonのみで実装

## アーキテクチャ

```
[JSettlersサーバー] <--TCP/UTF-8--> [Pythonボット] <--> [PyTorchエージェント]
```

Pythonボットは以下を行います：

1. JSettlersサーバーからメッセージを受信
2. メッセージをObservation形式に変換
3. PyTorchエージェントでActionを予測
4. ActionをJSettlersメッセージに変換して送信

## 必要なもの

```bash
pip install torch  # または既存の環境
```

その他の標準ライブラリのみ使用（socket, struct, json等）

## 実装ガイド

### ステップ1: Java UTF形式の実装

JSettlersはJavaの`DataOutputStream.writeUTF()`形式でメッセージを送受信します。

#### utils.py

```python
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
    length_bytes = sock.recv(2)
    if len(length_bytes) < 2:
        raise ConnectionError("Connection closed")
    
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
```

### ステップ2: ゲーム状態の管理

#### game_state.py

```python
from dataclasses import dataclass, field
from typing import List, Dict, Optional
import numpy as np

@dataclass
class GameState:
    """
    JSettlersゲームの状態を保持
    エージェントのObservation形式に変換可能
    """
    # ボード情報
    board_hexes: List[int] = field(default_factory=list)  # ヘックスのタイプ
    board_numbers: List[int] = field(default_factory=list)  # サイコロの数字
    
    # プレイヤー情報
    my_player_number: int = -1
    current_player: int = 0
    
    # 資源
    my_resources: Dict[str, int] = field(default_factory=lambda: {
        'clay': 0,
        'ore': 0,
        'sheep': 0,
        'wheat': 0,
        'wood': 0
    })
    
    # 駒の位置
    settlements: Dict[int, List[int]] = field(default_factory=dict)  # player -> positions
    cities: Dict[int, List[int]] = field(default_factory=dict)
    roads: Dict[int, List[int]] = field(default_factory=dict)
    
    # ゲーム状態
    game_state: int = 0  # JSettlersのゲーム状態番号
    dice_result: Optional[int] = None
    
    def to_observation(self) -> np.ndarray:
        """
        ゲーム状態をエージェントのObservation形式に変換
        
        Returns:
            エージェント用のObservation（numpy配列）
        """
        # エージェントの期待するObservation形式に合わせてカスタマイズ
        # 例: ボード状態 + 資源 + プレイヤー情報を連結
        
        # ボード状態（簡略化）
        board_state = np.array(self.board_hexes + self.board_numbers, dtype=np.float32)
        
        # 資源状態
        resource_state = np.array([
            self.my_resources['clay'],
            self.my_resources['ore'],
            self.my_resources['sheep'],
            self.my_resources['wheat'],
            self.my_resources['wood']
        ], dtype=np.float32)
        
        # 駒の情報（簡略化）
        my_settlements = len(self.settlements.get(self.my_player_number, []))
        my_cities = len(self.cities.get(self.my_player_number, []))
        my_roads = len(self.roads.get(self.my_player_number, []))
        
        piece_state = np.array([my_settlements, my_cities, my_roads], dtype=np.float32)
        
        # すべてを連結
        observation = np.concatenate([board_state, resource_state, piece_state])
        
        return observation
    
    def update_from_message(self, msg_type: str, params: dict):
        """
        JSettlersメッセージからゲーム状態を更新
        
        Args:
            msg_type: メッセージタイプ
            params: メッセージパラメータ
        """
        if msg_type == "GAMESTATE":
            if "state" in params:
                self.game_state = int(params["state"])
        
        elif msg_type == "DICERESULT":
            if "param" in params:
                self.dice_result = int(params["param"])
        
        elif msg_type == "PUTPIECE":
            # 駒の配置を記録
            player = int(params.get("playerNumber", -1))
            piece_type = int(params.get("pieceType", -1))
            coord = int(params.get("coord", -1))
            
            if piece_type == 0:  # Road
                if player not in self.roads:
                    self.roads[player] = []
                self.roads[player].append(coord)
            elif piece_type == 1:  # Settlement
                if player not in self.settlements:
                    self.settlements[player] = []
                self.settlements[player].append(coord)
            elif piece_type == 2:  # City
                if player not in self.cities:
                    self.cities[player] = []
                self.cities[player].append(coord)
        
        elif msg_type == "PLAYERELEMENT":
            # 資源の更新
            if params.get("playerNum") == str(self.my_player_number):
                action_type = int(params.get("actionType", 0))
                element_type = int(params.get("elementType", 0))
                amount = int(params.get("amount", 0))
                
                # elementType: 1=Clay, 2=Ore, 3=Sheep, 4=Wheat, 5=Wood
                resource_map = {1: 'clay', 2: 'ore', 3: 'sheep', 4: 'wheat', 5: 'wood'}
                if element_type in resource_map:
                    resource = resource_map[element_type]
                    if action_type == 1:  # SET
                        self.my_resources[resource] = amount
                    elif action_type == 2:  # GAIN
                        self.my_resources[resource] += amount
                    elif action_type == 3:  # LOSE
                        self.my_resources[resource] -= amount
```

### ステップ3: Pythonボットクライアント

#### jsettlers_bot.py

```python
import socket
import sys
from typing import Optional
import torch

from utils import write_java_utf, read_java_utf, parse_message, build_message
from game_state import GameState

class JSettlersBot:
    """
    JSettlersサーバーに接続するPythonボット
    """
    
    def __init__(self, host: str, port: int, nickname: str, cookie: str, agent):
        """
        Args:
            host: JSettlersサーバーのホスト
            port: ポート番号
            nickname: ボットの名前
            cookie: サーバーのセキュリティクッキー
            agent: PyTorchエージェント（predict_action メソッドを持つ）
        """
        self.host = host
        self.port = port
        self.nickname = nickname
        self.cookie = cookie
        self.agent = agent
        
        self.sock: Optional[socket.socket] = None
        self.game_state = GameState()
        self.current_game: Optional[str] = None
        
    def connect(self):
        """サーバーに接続"""
        print(f"🤖 Connecting to {self.host}:{self.port}...")
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((self.host, self.port))
        print("✓ Connected")
        
    def authenticate(self):
        """ロボットとして認証"""
        print("🔐 Authenticating as robot...")
        
        # VERSIONメッセージを送信
        version_msg = build_message(
            "VERSION",
            version="2.5.00",
            versionint="2500",
            locale="en_US",
            cliFeats=";6pl;sb;"
        )
        write_java_utf(self.sock, version_msg)
        print(f"→ {version_msg}")
        
        # IMAROBOTメッセージを送信
        robot_msg = build_message(
            "IMAROBOT",
            nickname=self.nickname,
            cookie=self.cookie,
            rbclass="python.bot.PyTorchAgent"
        )
        write_java_utf(self.sock, robot_msg)
        print(f"→ {robot_msg}")
        print("✓ Authenticated")
        
    def run(self):
        """メインループ"""
        print("⏳ Waiting for messages...")
        print()
        
        try:
            while True:
                # メッセージを受信
                message = read_java_utf(self.sock)
                print(f"← {message}")
                
                # メッセージを処理
                self.handle_message(message)
                
        except KeyboardInterrupt:
            print("\n👋 Shutting down...")
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            if self.sock:
                self.sock.close()
    
    def handle_message(self, message: str):
        """メッセージを処理"""
        parsed = parse_message(message)
        msg_type = parsed["type"]
        
        # ゲーム状態を更新
        self.game_state.update_from_message(msg_type, parsed)
        
        # メッセージタイプに応じて処理
        if msg_type == "UPDATEROBOTPARAMS":
            print("✓ Robot parameters updated")
            
        elif msg_type == "BOTJOINGAMEREQUEST":
            # ゲーム参加要求
            game_name = parsed.get("game")
            if game_name:
                self.join_game(game_name)
                
        elif msg_type == "JOINGAMEAUTH":
            # ゲーム参加成功
            self.current_game = parsed.get("game")
            self.game_state.my_player_number = int(parsed.get("playerNumber", -1))
            print(f"✓ Joined game: {self.current_game} as player {self.game_state.my_player_number}")
            
        elif msg_type == "GAMESTATE":
            # ゲーム状態の変更
            self.handle_game_state(parsed)
            
        elif msg_type == "TURN":
            # ターン情報
            current_player = int(parsed.get("playerNumber", -1))
            self.game_state.current_player = current_player
            
    def join_game(self, game_name: str):
        """ゲームに参加"""
        print(f"📥 Joining game: {game_name}")
        join_msg = build_message(
            "JOINGAME",
            nickname=self.nickname,
            password="",
            host="-",
            game=game_name
        )
        write_java_utf(self.sock, join_msg)
        print(f"→ {join_msg}")
        
    def handle_game_state(self, params: dict):
        """ゲーム状態を処理"""
        state = int(params.get("state", 0))
        
        # 状態15 = ROLL_OR_CARD（サイコロを振る or 開発カードを使う）
        if state == 15 and self.is_my_turn():
            print("🎲 My turn - making decision...")
            self.make_decision()
    
    def is_my_turn(self) -> bool:
        """自分のターンかどうか"""
        return self.game_state.current_player == self.game_state.my_player_number
    
    def make_decision(self):
        """エージェントで決定を行い、アクションを実行"""
        try:
            # ゲーム状態をObservationに変換
            observation = self.game_state.to_observation()
            
            # エージェントでアクションを予測
            action = self.agent.predict_action(observation)
            
            print(f"🧠 Agent predicted action: {action}")
            
            # アクションを実行
            self.execute_action(action)
            
        except Exception as e:
            print(f"⚠️  Error in decision making: {e}")
            # フォールバック: サイコロを振る
            self.roll_dice()
    
    def execute_action(self, action: int):
        """
        アクションを実行
        
        Args:
            action: エージェントが出力したアクション
        """
        if not self.current_game:
            return
        
        # アクションの意味は、エージェントの実装に依存
        # ここでは例として簡単なマッピングを示す
        
        if action == 0:
            # サイコロを振る
            self.roll_dice()
        elif action == 1:
            # 道路を建設（座標は別途決定が必要）
            self.build_road(0x0)  # プレースホルダー座標
        elif action == 2:
            # 集落を建設
            self.build_settlement(0x0)
        # ... その他のアクション
        else:
            # デフォルト: サイコロを振る
            self.roll_dice()
    
    def roll_dice(self):
        """サイコロを振る"""
        msg = build_message("ROLLDICE", game=self.current_game)
        write_java_utf(self.sock, msg)
        print(f"→ {msg}")
    
    def build_road(self, coord: int):
        """道路を建設"""
        msg = build_message("BUILDREQUEST", game=self.current_game, pieceType="0", coord=str(coord))
        write_java_utf(self.sock, msg)
        print(f"→ {msg}")
    
    def build_settlement(self, coord: int):
        """集落を建設"""
        msg = build_message("BUILDREQUEST", game=self.current_game, pieceType="1", coord=str(coord))
        write_java_utf(self.sock, msg)
        print(f"→ {msg}")
```

### ステップ4: エージェントの統合

#### agent.py

```python
import torch
import torch.nn as nn
import numpy as np

class CatanAgent:
    """
    PyTorchで実装したエージェント
    """
    
    def __init__(self, model_path: str):
        """
        Args:
            model_path: 学習済みモデルのパス
        """
        # モデルをロード
        self.model = torch.load(model_path, map_location='cpu')
        self.model.eval()
        
    def predict_action(self, observation: np.ndarray) -> int:
        """
        Observationからアクションを予測
        
        Args:
            observation: ゲーム状態のObservation
            
        Returns:
            予測されたアクション（整数）
        """
        # NumPy配列をTensorに変換
        obs_tensor = torch.from_numpy(observation).float().unsqueeze(0)
        
        # 予測
        with torch.no_grad():
            output = self.model(obs_tensor)
            action = output.argmax().item()
        
        return action
```

### ステップ5: メイン実行ファイル

#### main.py

```python
#!/usr/bin/env python3
import sys
from jsettlers_bot import JSettlersBot
from agent import CatanAgent

def main():
    if len(sys.argv) < 6:
        print("Usage: python main.py <host> <port> <nickname> <cookie> <model_path>")
        print("Example: python main.py localhost 8880 mybot abc123 model.pth")
        sys.exit(1)
    
    host = sys.argv[1]
    port = int(sys.argv[2])
    nickname = sys.argv[3]
    cookie = sys.argv[4]
    model_path = sys.argv[5]
    
    print("🤖 JSettlers Python Bot with PyTorch Agent")
    print("=" * 50)
    print(f"Host: {host}:{port}")
    print(f"Nickname: {nickname}")
    print(f"Model: {model_path}")
    print()
    
    # エージェントをロード
    print("🧠 Loading agent...")
    agent = CatanAgent(model_path)
    print("✓ Agent loaded")
    print()
    
    # ボットを作成
    bot = JSettlersBot(host, port, nickname, cookie, agent)
    
    # 接続して実行
    bot.connect()
    bot.authenticate()
    bot.run()

if __name__ == "__main__":
    main()
```

## 使い方

### 1. JSettlersサーバーを起動

```bash
java -Djsettlers.bots.showcookie=Y -jar JSettlers.jar 8880
```

表示されたクッキーをメモしてください。

### 2. Pythonボットを実行

```bash
python main.py localhost 8880 mybot <cookie> /path/to/your/model.pth
```

### 3. ゲームを作成

別のターミナルでJSettlersクライアントを起動し、ボットを含むゲームを作成します。

## カスタマイズ

### Observation形式の調整

`game_state.py`の`to_observation()`メソッドを、エージェントの期待する形式に合わせて変更してください：

```python
def to_observation(self) -> np.ndarray:
    # エージェントに合わせた形式に変換
    # 例: (board_size, features) のような形状
    return observation
```

### Action空間の調整

`jsettlers_bot.py`の`execute_action()`メソッドを、エージェントのAction空間に合わせて変更してください：

```python
def execute_action(self, action: int):
    # エージェントのアクション定義に従って実装
    if action == 0:
        self.roll_dice()
    elif action == 1:
        self.build_road(coord)
    # ...
```

### より詳細なObservation

より詳細な情報が必要な場合は、`GameState`クラスにフィールドを追加し、メッセージハンドラーを拡張してください。

## トラブルシューティング

### 接続できない

```bash
# ポートが開いているか確認
telnet localhost 8880
```

### クッキーエラー

サーバーを起動し直してクッキーを確認：

```bash
java -Djsettlers.bots.showcookie=Y -jar JSettlers.jar 8880
```

### モデルのロードエラー

モデルのパスと、PyTorchのバージョンが正しいか確認してください。

### アクションが実行されない

- ゲーム状態が正しいか確認
- ターン判定が正しいか確認
- サーバーログでエラーを確認

## まとめ

このガイドでは、以下を実装しました：

1. **Java UTF形式の送受信** - JSettlersプロトコルの実装
2. **ゲーム状態の管理** - メッセージからObservationへの変換
3. **PyTorchエージェントの統合** - モデルによるアクション予測
4. **JSettlersとの通信** - メッセージの送受信とゲームの進行

これにより、PyTorchで学習したエージェントをJSettlersで評価できます。

**注意**: このコードは基本的な実装例です。実際のエージェントの要件に合わせて、Observation形式やAction空間をカスタマイズしてください。
