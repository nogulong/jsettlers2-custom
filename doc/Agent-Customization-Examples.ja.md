# エージェント統合カスタマイズ例

このドキュメントでは、一般的なCatanエージェントの形式に合わせたカスタマイズ例を示します。

## パターン1: 辞書形式のObservation

```python
def to_observation(self) -> dict:
    """
    辞書形式でObservationを返す
    """
    return {
        'board': self.get_board_state(),
        'resources': self.get_resource_state(),
        'players': self.get_player_states(),
        'legal_actions': self.get_legal_actions()
    }
```

## パターン2: Gym形式のObservation

```python
def to_observation(self) -> Dict[str, np.ndarray]:
    """
    OpenAI Gym形式のObservation
    """
    return {
        'board': np.array(self.board_hexes + self.board_numbers, dtype=np.float32),
        'resources': np.array([...], dtype=np.float32),
        'current_player': self.current_player,
        'my_player': self.my_player_number
    }
```

## パターン3: フラット化されたObservation

```python
def to_observation(self) -> np.ndarray:
    """
    すべての情報を1次元配列にフラット化
    """
    features = []
    
    # ボード情報（19ヘックス x 特徴数）
    for hex_type in self.board_hexes:
        features.append(hex_type)
    
    # 資源（5種類）
    features.extend([
        self.my_resources['clay'],
        self.my_resources['ore'],
        self.my_resources['sheep'],
        self.my_resources['wheat'],
        self.my_resources['wood']
    ])
    
    # プレイヤー情報
    features.extend([
        self.my_player_number,
        len(self.settlements.get(self.my_player_number, [])),
        len(self.cities.get(self.my_player_number, [])),
        len(self.roads.get(self.my_player_number, []))
    ])
    
    return np.array(features, dtype=np.float32)
```

## パターン4: マスク付きアクション

```python
def predict_action(self, observation: np.ndarray, action_mask: np.ndarray) -> int:
    """
    マスク付きアクション選択
    
    Args:
        observation: ゲーム状態
        action_mask: 有効なアクションのマスク（1=有効, 0=無効）
    """
    obs_tensor = torch.from_numpy(observation).float().unsqueeze(0)
    mask_tensor = torch.from_numpy(action_mask).float().unsqueeze(0)
    
    with torch.no_grad():
        logits = self.model(obs_tensor)
        # 無効なアクションに大きな負の値を設定
        masked_logits = logits + (mask_tensor - 1) * 1e9
        action = masked_logits.argmax().item()
    
    return action
```

## パターン5: RLlib形式

```python
# RLlibのPolicyを使用する場合
from ray.rllib.policy.policy import Policy

class CatanAgent:
    def __init__(self, checkpoint_path: str):
        self.policy = Policy.from_checkpoint(checkpoint_path)
    
    def predict_action(self, observation: dict) -> int:
        action = self.policy.compute_single_action(observation)
        return action
```

## パターン6: Stable-Baselines3形式

```python
from stable_baselines3 import PPO

class CatanAgent:
    def __init__(self, model_path: str):
        self.model = PPO.load(model_path)
    
    def predict_action(self, observation: np.ndarray) -> int:
        action, _states = self.model.predict(observation, deterministic=True)
        return int(action)
```

## アクション空間の例

### 離散アクション空間

```python
# アクション番号 -> JSettlersコマンドのマッピング
ACTION_MAP = {
    0: 'roll_dice',
    1: 'end_turn',
    2: 'buy_dev_card',
    3: 'play_knight',
    # 4-23: 道路建設（20箇所）
    # 24-43: 集落建設（20箇所）
    # ...
}

def execute_action(self, action: int):
    action_type = ACTION_MAP.get(action)
    
    if action_type == 'roll_dice':
        self.roll_dice()
    elif action_type == 'buy_dev_card':
        self.buy_dev_card()
    elif 4 <= action < 24:
        # 道路建設
        coord = self.get_road_coordinate(action - 4)
        self.build_road(coord)
    # ...
```

### 構造化アクション空間

```python
def execute_action(self, action: dict):
    """
    辞書形式のアクション
    例: {'type': 'build_road', 'coord': 0x33}
    """
    action_type = action['type']
    
    if action_type == 'build_road':
        self.build_road(action['coord'])
    elif action_type == 'build_settlement':
        self.build_settlement(action['coord'])
    elif action_type == 'trade':
        self.make_trade(action['give'], action['get'])
```

## 実装のヒント

1. **Observation次元**: エージェントの学習時と同じ次元を維持
2. **正規化**: 学習時と同じ正規化を適用
3. **アクションマスク**: 無効なアクションを除外
4. **デバッグ**: `print(observation.shape)` でObservationの形状を確認
5. **テスト**: ダミーデータでagent.predict_action()をテスト

## カスタマイズ手順

1. **`agent.py`を変更**: エージェントのロード方法を調整
2. **`game_state.py`の`to_observation()`を変更**: Observation形式を調整
3. **`jsettlers_bot.py`の`execute_action()`を変更**: アクション実行を調整
4. **テスト実行**: サーバーに接続してログを確認
5. **デバッグ**: 必要に応じて調整

## よくある問題

### Observation形状の不一致

```python
# エラー: Expected input of size [1, 58], got [1, 50]
# 解決: to_observation()の返り値を確認
print(f"Observation shape: {observation.shape}")
```

### アクションが実行されない

```python
# デバッグ: アクション番号を確認
print(f"Predicted action: {action}, type: {type(action)}")
```

### モデルロードエラー

```python
# PyTorchバージョンの確認
import torch
print(f"PyTorch version: {torch.__version__}")
```
