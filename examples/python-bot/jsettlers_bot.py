"""
JSettlersサーバーに接続するPythonボット
"""
import socket
from typing import Optional

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
            import traceback
            traceback.print_exc()
            # フォールバック: サイコロを振る
            self.roll_dice()
    
    def execute_action(self, action: int):
        """
        アクションを実行
        
        Args:
            action: エージェントが出力したアクション
        
        注意: アクション空間は実際のエージェントに合わせてカスタマイズしてください
        """
        if not self.current_game:
            return
        
        # 例: 簡単なアクションマッピング
        # 実際のエージェントのアクション空間に合わせて変更してください
        
        if action == 0:
            # サイコロを振る
            self.roll_dice()
        elif action == 1:
            # 道路を建設（座標は別途決定が必要）
            # TODO: 実際の建設可能な座標を見つける
            print("⚠️  Road building not implemented, rolling dice instead")
            self.roll_dice()
        elif action == 2:
            # 集落を建設
            # TODO: 実際の建設可能な座標を見つける
            print("⚠️  Settlement building not implemented, rolling dice instead")
            self.roll_dice()
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
        msg = build_message(
            "BUILDREQUEST",
            game=self.current_game,
            pieceType="0",
            coord=str(coord)
        )
        write_java_utf(self.sock, msg)
        print(f"→ {msg}")
    
    def build_settlement(self, coord: int):
        """集落を建設"""
        msg = build_message(
            "BUILDREQUEST",
            game=self.current_game,
            pieceType="1",
            coord=str(coord)
        )
        write_java_utf(self.sock, msg)
        print(f"→ {msg}")
