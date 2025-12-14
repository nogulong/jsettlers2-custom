"""
ゲーム状態カスタマイズ用テンプレート

このファイルをコピーして、あなたのエージェントのObservation形式に合わせて修正してください。
"""
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
import numpy as np

@dataclass
class CustomGameState:
    """
    JSettlersゲームの状態を保持し、カスタムObservation形式に変換
    
    このクラスを以下のように修正してください：
    1. 必要なフィールドを追加
    2. to_observation()をエージェントの期待する形式に変更
    3. update_from_message()に必要なメッセージ処理を追加
    """
    
    # ============================================
    # ゲーム状態のフィールド（必要に応じて追加・削除）
    # ============================================
    
    # ボード情報
    board_hexes: List[int] = field(default_factory=list)
    board_numbers: List[int] = field(default_factory=list)
    
    # プレイヤー情報
    my_player_number: int = -1
    current_player: int = 0
    num_players: int = 4
    
    # 資源
    my_resources: Dict[str, int] = field(default_factory=lambda: {
        'clay': 0, 'ore': 0, 'sheep': 0, 'wheat': 0, 'wood': 0
    })
    
    # 駒の位置
    settlements: Dict[int, List[int]] = field(default_factory=dict)
    cities: Dict[int, List[int]] = field(default_factory=dict)
    roads: Dict[int, List[int]] = field(default_factory=dict)
    
    # ゲーム状態
    game_state: int = 0
    dice_result: Optional[int] = None
    
    # 追加情報（必要に応じて）
    dev_cards: List[int] = field(default_factory=list)
    victory_points: int = 0
    
    def to_observation(self) -> Any:
        """
        ゲーム状態をエージェントのObservation形式に変換
        
        ============================================
        TODO: あなたのエージェントの形式に変更
        ============================================
        
        Returns:
            エージェント用のObservation
            （形式: np.ndarray, dict, など）
        """
        
        # ----------------------------------------
        # パターン1: フラットな1次元配列
        # ----------------------------------------
        features = []
        
        # ボード情報（例: 19ヘックス）
        for hex_type in self.board_hexes[:19]:
            features.append(hex_type)
        
        # ボードの数字（例: 19ヘックス）
        for number in self.board_numbers[:19]:
            features.append(number)
        
        # 自分の資源（5種類）
        features.extend([
            self.my_resources['clay'],
            self.my_resources['ore'],
            self.my_resources['sheep'],
            self.my_resources['wheat'],
            self.my_resources['wood']
        ])
        
        # 自分の駒の数
        features.extend([
            len(self.settlements.get(self.my_player_number, [])),
            len(self.cities.get(self.my_player_number, [])),
            len(self.roads.get(self.my_player_number, []))
        ])
        
        # プレイヤー番号
        features.append(self.my_player_number)
        
        # 現在のプレイヤー
        features.append(self.current_player)
        
        return np.array(features, dtype=np.float32)
        
        # ----------------------------------------
        # パターン2: 辞書形式
        # ----------------------------------------
        # return {
        #     'board': np.array(self.board_hexes + self.board_numbers, dtype=np.float32),
        #     'resources': np.array([
        #         self.my_resources['clay'],
        #         self.my_resources['ore'],
        #         self.my_resources['sheep'],
        #         self.my_resources['wheat'],
        #         self.my_resources['wood']
        #     ], dtype=np.float32),
        #     'settlements': len(self.settlements.get(self.my_player_number, [])),
        #     'cities': len(self.cities.get(self.my_player_number, [])),
        #     'roads': len(self.roads.get(self.my_player_number, [])),
        #     'current_player': self.current_player,
        #     'my_player': self.my_player_number
        # }
        
        # ----------------------------------------
        # パターン3: 2次元配列（画像形式）
        # ----------------------------------------
        # # ボードを2次元グリッドとして表現
        # board_grid = np.zeros((7, 7, 3), dtype=np.float32)  # (height, width, channels)
        # # ... ボード情報を配置 ...
        # return board_grid
        
        # ----------------------------------------
        # パターン4: 複数の配列
        # ----------------------------------------
        # return {
        #     'board_state': np.array(...),
        #     'player_state': np.array(...),
        #     'action_mask': self.get_action_mask()
        # }
    
    def get_action_mask(self) -> np.ndarray:
        """
        有効なアクションのマスクを生成
        
        Returns:
            アクションマスク（1=有効, 0=無効）
        """
        # ============================================
        # TODO: アクション空間のサイズに合わせて変更
        # ============================================
        action_space_size = 100
        mask = np.ones(action_space_size, dtype=np.float32)
        
        # 例: 資源チェック
        if self.my_resources['wood'] < 1 or self.my_resources['clay'] < 1:
            # 道路建設を無効化
            mask[4:24] = 0
        
        if self.my_resources['wood'] < 1 or self.my_resources['clay'] < 1 or \
           self.my_resources['sheep'] < 1 or self.my_resources['wheat'] < 1:
            # 集落建設を無効化
            mask[24:44] = 0
        
        return mask
    
    def update_from_message(self, msg_type: str, params: dict):
        """
        JSettlersメッセージからゲーム状態を更新
        
        ============================================
        必要に応じてメッセージ処理を追加
        ============================================
        
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
        
        # ============================================
        # TODO: 他のメッセージタイプを追加
        # ============================================
        
        elif msg_type == "BOARDLAYOUT":
            # ボード配置の解析
            pass
        
        elif msg_type == "DEVCARDACTION":
            # 開発カードの使用
            pass
        
        elif msg_type == "TURN":
            # ターン情報
            if "playerNumber" in params:
                self.current_player = int(params["playerNumber"])


# ============================================
# 使用例とテスト
# ============================================
if __name__ == "__main__":
    # ゲーム状態の初期化
    game_state = CustomGameState()
    game_state.my_player_number = 0
    game_state.current_player = 0
    
    # ダミーデータで状態を設定
    game_state.board_hexes = [0, 1, 2, 3, 4] * 4  # 20ヘックス
    game_state.board_numbers = [6, 8, 5, 10, 9] * 4
    game_state.my_resources = {'clay': 2, 'ore': 1, 'sheep': 3, 'wheat': 1, 'wood': 2}
    
    # Observationを生成
    observation = game_state.to_observation()
    print(f"Observation type: {type(observation)}")
    if isinstance(observation, np.ndarray):
        print(f"Observation shape: {observation.shape}")
        print(f"Observation: {observation}")
    elif isinstance(observation, dict):
        print(f"Observation keys: {observation.keys()}")
        for key, value in observation.items():
            if isinstance(value, np.ndarray):
                print(f"  {key}: shape={value.shape}, dtype={value.dtype}")
            else:
                print(f"  {key}: {value}")
    
    # アクションマスクを生成
    action_mask = game_state.get_action_mask()
    print(f"\nAction mask shape: {action_mask.shape}")
    print(f"Valid actions: {np.sum(action_mask)} / {len(action_mask)}")
