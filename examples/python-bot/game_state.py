"""
ゲーム状態を管理し、Observationに変換
"""
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
        
        注意: この実装は例です。実際のエージェントの要件に合わせてカスタマイズしてください。
        
        Returns:
            エージェント用のObservation（numpy配列）
        """
        # ボード状態（簡略化）
        # 実際には、ボードのヘックスタイプ、数字、駒の配置などを含める
        board_state = np.zeros(50, dtype=np.float32)  # プレースホルダー
        
        # 資源状態
        resource_state = np.array([
            self.my_resources['clay'],
            self.my_resources['ore'],
            self.my_resources['sheep'],
            self.my_resources['wheat'],
            self.my_resources['wood']
        ], dtype=np.float32)
        
        # 駒の情報
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
