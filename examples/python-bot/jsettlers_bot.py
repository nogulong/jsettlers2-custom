"""
JSettlersサーバーに接続するPythonボット
"""
import random
import string
import socket
import traceback
from typing import Optional

from utils import write_java_utf, read_java_utf, parse_message
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
    
    def create_game(self, game_name):
        print(f"🛠️ Creating new game: {game_name}")
        
        # 存在しない名前で 1013 を送ると、サーバーが新規作成してくれる
        # 形式: 1013 | ニックネーム | - | - | ゲーム名
        msg = f"1013|{self.nickname},-,-,{game_name}"
        write_java_utf(self.sock, msg)
        print(f"→ {msg}")
        
        # current_game をセットしておく（サーバーからの承認待ち）
        self.current_game = game_name
        
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
        version_msg = "9998|2700,2.7.00,JM20251205,;6pl;sb;,en_US"
        write_java_utf(self.sock, version_msg)
        print(f"→ {version_msg}")
        
        # IMAROBOTメッセージを送信
        robot_msg = f"1022|{self.nickname},{self.cookie},python.bot.PyTorchAgent"
        write_java_utf(self.sock, robot_msg)
        print(f"→ {robot_msg}")
        print("✓ Authenticated")
        
    def run(self, game_name, mode="create", num_robots=3, num_games=1):
        """メインループ"""
        
        # 設定を保存しておく
        self.target_num_robots = num_robots 
        games_played = 0

        if not self.sock:
            self.connect()
            self.authenticate()
        try:
            while games_played < num_games:
                current_game_name = f"{game_name}_{games_played}"
                # self.reset_internal_state() # いらないかも
                if mode == "create":
                    self.create_game(current_game_name)
                elif mode == "join":
                    self.current_game = current_game_name
                    self.join_game(current_game_name)
            
                    while True:
                        # メッセージを受信
                        message = read_java_utf(self.sock)
                        print(f"← {message}")
                        
                        # メッセージを処理
                        self.handle_message(message)
                        # is_game_finished = self.handle_message(message)
                        # if is_game_finished:
                        #     leave_msg = f"1011|{self.current_game},{self.nickname}"
                        #     write_java_utf(self.sock, leave_msg)

                        #     games_played += 1
                        #     break
                    
        except KeyboardInterrupt:
            print("\n👋 Shutting down...")
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            # このあたりでcreatorに勝敗報告とかを送らせる
            if self.sock:
                self.sock.close()
    
    def handle_message(self, message: str):
        """メッセージを処理"""
        parsed = parse_message(message)
        msg_type = parsed["type"]
        
        # ゲーム状態を更新
        self.game_state.update_from_message(msg_type, parsed)
        
        # メッセージタイプに応じて処理
        if msg_type == "1071":
            print("✓ Robot parameters updated")

        elif msg_type == "1009": # PutPiece
            # 何かの駒を置いた通知 1009|testplay,3,0,201
            pass

        
        elif msg_type == "1012":
            # ログ表示や自分の着席確認だけ行い、リトライ処理は削除してOK
            args = parsed.get("args", [])
            if len(args) >= 3:
                name = args[1]
                seat = int(args[2])
                
                if name == self.nickname: # または "-" から変換された名前
                    self.game_state.my_player_number = seat
                    print(f"✅ Success! I am Player {seat}!")
        
        elif msg_type == "1013": # JOINGAME 誰かがゲームに入室した
            args = parsed.get("args", [])
            if len(args) >= 1:
                name = args[0]
                
                # 自分が入室した通知が来たら、1回だけ座るリクエストを送る
                if name == self.nickname and self.game_state.my_player_number == -1:
                    print("🚀 Join complete. Requesting auto-seat assignment...")
                    # ここで1回だけ呼ぶ！
                    self.sit_down(self.current_game)# とりあえず,常に0を指定
        
        elif msg_type == "1018": # GAMESTART
            pass
                
        elif msg_type == "1021": # JOINGAMEAUTH
            # ゲーム参加成功
            self.current_game = parsed.get("game")
            self.game_state.my_player_number = int(parsed.get("playerNumber", -1))
            print(f"✓ Joined game: {self.current_game} as player {self.game_state.my_player_number}")

        elif msg_type == "1023": #BOTJOINGAMEREQUEST
            # ゲーム参加要求
            game_name = parsed.get("game")
            if game_name:
                self.join_game(game_name)
        
        elif msg_type == "1024": # PLAYERELEMENTS　発展カードの使用関連
            # ← 1024|testplay,1,100,19,1
            # ← 1024|testplay,1,101,15,1
            # ← 1024|testplay,2,100,4,0,Y　4(麦)を0にセット
            # ← 1063|testplay,2,6
            # ← 1024|testplay,3,100,4,0,Y　monopolyでの増減もある
            # ← 1063|testplay,3,3

            args = parsed.get("args", [])
            if len(args) >= 5:
                p_num = int(args[1])
                action = int(args[2])
                element = int(args[3])
                amount = int(args[4])
                if element == 17: # 手持ち資源の総数
                    if action == 100: # SET
                        self.game_state.player_resources[p_num] = amount
                    elif action == 101: # ADD
                        self.game_state.player_resources[p_num] += amount
                    elif action == 102: # REMOVE
                        self.game_state.player_resources[p_num] -= amount
                elif element == 15:#騎士力をプラスする
                    if action == 101: # ADD
                        self.game_state.player_knights[p_num] += amount

                elif element == 19 and amount == 1: # 誰かが発展カードを使い, PLAYER_DEV_CARD_FLAGが立った
                    pass
        
        elif msg_type == "1025": # GAMESTATE, pycatanでいうphase変更
            args = parsed.get("args", [])
            self.handle_game_state(parsed) # 消すかも, ゲーム状態の変更
            if len(args) >= 2:
                phase = int(args[1])
                if phase == 5: #initial placement, 1st settlement
                    pass
                elif phase == 6:
                    pass #initial placement, 1st road
                elif phase == 10:
                    pass #initial placement, 2nd settlement
                elif phase == 11:
                    pass #initial placement, 2nd road
                elif phase == 15:
                    pass #roll or card, preroll
                elif phase == 20:
                    pass #roll finished, main turn
                # 30, 31, 32 はそれぞれ道, 集落, 都市の建設フェーズ, actionがbuyとputに分かれる
                elif phase == 33:
                    pass #MT
                elif phase == 40:
                    pass # road placing, 2left=true
                elif phase == 41:
                    pass # road placing, 2left=false
                elif phase == 50:
                    pass # discarding いらないかも
                elif phase == 1000:
                    pass # game over
            
        elif msg_type == "1026": # TURN
            # 形式: 1026 | ゲーム名 | プレイヤー番号 | アクションID(ボード状態)
            args = parsed.get("args", [])
            
            if len(args) >= 2:
                try:
                    next_player = int(args[1])
                    # args[2]はうえのphaseと同じ
                    # 同様のphase変更処理が必要
                    
                    print(f"🔄 Turn changed to Player {next_player}")
                    self.game_state.current_player = next_player

                    # もし自分の番なら行動開始！
                    if self.is_my_turn():
                        print("🚀 It's my turn! (From TURN msg)")
                        # ここでアクション（ダイスを振る、建設するなど）を呼び出す
                        # phaseをprerollに変更して, pickactionを呼び出す
                        # self.do_turn_action() 
                        
                except ValueError:
                    print(f"⚠️ Failed to parse turn player number: {args}")
        
        elif msg_type == "1028": # DiceRollResult
            args = parsed.get("args", [])
            if len(args) >= 2:
                dice_result = int(args[1])
                # dice_resultに基づいて変更
        
        elif msg_type == "1029":
            # カードを捨てる要求にこたえる
            args = parsed.get("args", [])
            if len(args) >= 2:
                num_discard = int(args[1])
            self.handle_discard_request(parsed)

        elif msg_type == "1030":
            # サイコロを振る要求, 来てないかも
            pass

        elif msg_type == "1034": # MT
            # victim と hex, 1034|testplay,1,183
            pass

        elif msg_type == "1038" or msg_type == "1042": # trade終わり
            pass

        elif msg_type == "1039": # Accept
            #受諾者, 提案者, 資源オファー, 資源リクエスト
            pass
        
        elif msg_type == "1040": # BackTrade 1040|testplay,4,0,0,0,0,0,0,0,0,1,2
            # 最後プレイヤー
            pass
        
        elif msg_type == "1041":
            # トレード提案を受信
            # 提案者, 提案相手(bool), 資源オファー, 資源リクエスト
            self.handle_trade_offer(parsed)

        elif msg_type == "1046": 
            # BuyDevelopの結果　1046|testplay,3,0,0　最後がどのカードを引いたか
            # useの場合, 1046|testplay,1,1,3 1番が3(Monopoly)をuse(1)した
            pass
        
        elif msg_type == "1035":
            # プレイヤーを選択（盗賊で奪う相手）
            self.handle_choose_player(parsed)

        elif msg_type == "1061":# かなり怪しい
            args = parsed.get("args", [])
            # if len(args) >= 3:
            #     p_num = int(args[1])
            #     vp = int(args[2])
                
            #     # 誰かが10点取ったら終わり
            #     if vp >= 10:
            #         print(f"🏆 Player {p_num} reached {vp} points!")
            #         self.on_game_finished(winner_seat=p_num)
        
        elif msg_type == "1072": # ROLLDICEPROMPT
            # 多分早くダイスを振れと言われてる
            pass

        elif msg_type == "1086": # リソース使用関係 1086|testplay|3|102|1|1|5|1
            pass

        elif msg_type == "1090": # 発展カード枚数の更新　1090|testplay,3,1,24,0
            pass
            
        elif msg_type == "1092": # DICERESULTRESOURCES　1092|testplay|2|2|8|1|1|0|3|3|1|2
            # 獲得人数, (playerid, player所有数, (prod, resType)*gain_res)*gain_player
            pass

        elif msg_type == "1102": # ROBBERYRESULT, 1102|testplay,1,3,R,6,1,T
            # 1が3から不明なリソース6を1枚奪った
            pass
            
    def join_game(self, game_name: str):
        """ゲームに参加"""
        print(f"📥 Joining game: {game_name}")
        join_msg = f"1013|{self.nickname},-,-,{game_name}"
        write_java_utf(self.sock, join_msg)
        print(f"→ {join_msg}")
    
    def sit_down(self, game_name: str): # とりあえず,常に0を指定
        """席に座るリクエスト (1012)"""
        print(f"🪑 Requesting to sit in game: {game_name}")
        
        msg = f"1012|{game_name},-,0,true"
        
        write_java_utf(self.sock, msg)
        print(f"→ {msg}")
        
    def handle_game_state(self, params: dict):
        """ゲーム状態を処理"""
        state = int(params.get("state", 0))
        
        # 状態15 = ROLL_OR_CARD（サイコロを振る or 開発カードを使う）
        if state == 15 and self.is_my_turn():
            print("🎲 My turn - rolling dice...")
            self.roll_dice()
        
        # 状態20 = PLAY1（ターン中のアクション - 建設、交易など）
        elif state == 20 and self.is_my_turn():
            print("🎮 My turn - deciding action...")
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
            action = self.agent.predict_action(observation, self.game_state)
            
            print(f"🧠 Agent predicted action: {action}")
            
            # アクションを実行
            self.execute_action(action)
            
        except Exception as e:
            print(f"⚠️  Error in decision making: {e}")
            traceback.print_exc()
            # フォールバック: ターンを終了
            self.end_turn()
    
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
            # ターンを終了
            self.end_turn()
        elif action == 1:
            # 道路を建設（座標は別途決定が必要）
            # TODO: 実際の建設可能な座標を見つける
            print("⚠️  Road building not implemented, ending turn instead")
            self.end_turn()
        elif action == 2:
            # 集落を建設
            # TODO: 実際の建設可能な座標を見つける
            print("⚠️  Settlement building not implemented, ending turn instead")
            self.end_turn()
        else:
            # デフォルト: ターンを終了
            self.end_turn()
    
    def roll_dice(self):
        """サイコロを振る"""
        msg = f"1031|{self.current_game}"
        write_java_utf(self.sock, msg)
        print(f"→ {msg}")
    
    def end_turn(self):
        """ターンを終了"""
        msg = f"1032|{self.current_game}"
        write_java_utf(self.sock, msg)
        print(f"→ {msg} (ending turn)")
    
    def build_road(self, coord: int):
        """道路を建設"""
        msg = f"1043|game={self.current_game}|pieceType=0|coord={coord}"
        write_java_utf(self.sock, msg)
        print(f"→ {msg}")
    
    def build_settlement(self, coord: int):
        """集落を建設"""
        msg = f"1043|game={self.current_game}|pieceType=1|coord={coord}"
        write_java_utf(self.sock, msg)
        print(f"→ {msg}")
    
    def handle_discard_request(self, params: dict):
        """カードを捨てる要求を処理"""
        num_discard = int(params.get("numDiscard", 0))
        print(f"🗑️  Must discard {num_discard} cards")
        
        # ランダムに捨てるカードを選択
        resources_to_discard = {'clay': 0, 'ore': 0, 'sheep': 0, 'wheat': 0, 'wood': 0}
        remaining = num_discard
        
        # 持っている資源からランダムに選んで捨てる
        for resource in ['clay', 'ore', 'sheep', 'wheat', 'wood']:
            available = self.game_state.my_resources.get(resource, 0)
            if available > 0 and remaining > 0:
                discard = min(available, remaining)
                resources_to_discard[resource] = discard
                remaining -= discard
        
        # カードを捨てる
        self.discard_cards(resources_to_discard)
    
    def discard_cards(self, resources: dict):
        """カードを捨てる"""
        # DISCARD -> 1033
        res_str = f"{resources['clay']},{resources['ore']},{resources['sheep']},{resources['wheat']},{resources['wood']}"
        msg = f"1033|game={self.current_game}|resources={res_str}"
        write_java_utf(self.sock, msg)
        print(f"→ {msg}")
        print(f"   Discarding: {resources}")
    
    def handle_trade_offer(self, params: dict):
        """トレード提案を処理（常に断る）"""
        from_player = params.get("from")
        print(f"🔄 Trade offer from player {from_player} - declining")
        self.decline_trade()
    
    def decline_trade(self):
        """トレードを断る"""
        # REJECTOFFER -> 1037
        msg = f"1037|game={self.current_game}"
        write_java_utf(self.sock, msg)
        print(f"→ {msg}")
    
    def handle_choose_player(self, params: dict):
        """プレイヤーを選択（盗賊で奪う相手）"""
        choices = params.get("choices", "")
        print(f"👤 Choosing player to rob from: {choices}")
        
        # 選択肢がある場合は最初のプレイヤーを選択
        if choices:
            choice_list = [int(x) for x in choices.split(",") if x.strip().isdigit()]
            if choice_list:
                chosen = choice_list[0]
                self.choose_player(chosen)
            else:
                # 選択肢がない場合は-1（誰も奪わない）
                self.choose_player(-1)
        else:
            self.choose_player(-1)
    
    def choose_player(self, player_number: int):
        """プレイヤーを選択"""
        # CHOOSEPLAYER -> 1035
        msg = f"1035|game={self.current_game}|choice={player_number}"
        write_java_utf(self.sock, msg)
        print(f"→ {msg}")
