"""
エージェントカスタマイズ用テンプレート

このファイルをコピーして、あなたのエージェントの形式に合わせて修正してください。
"""
import torch
import numpy as np
from pathlib import Path
from typing import Optional, Dict, Any

class CustomCatanAgent:
    """
    カスタムエージェントのテンプレート
    
    このクラスを以下のように修正してください：
    1. __init__: モデルのロード方法を変更
    2. predict_action: エージェントの推論方法を変更
    3. 必要に応じてヘルパーメソッドを追加
    """
    
    def __init__(self, model_path: Optional[str] = None, **kwargs):
        """
        エージェントを初期化
        
        Args:
            model_path: モデルファイルのパス
            **kwargs: 追加のパラメータ（デバイス、設定など）
        """
        self.model = None
        self.device = kwargs.get('device', 'cpu')
        
        if model_path is None or not Path(model_path).exists():
            print(f"⚠️  Model not found: {model_path}")
            print("⚠️  Using random agent")
            return
        
        # ============================================
        # TODO: あなたのモデルのロード方法に変更
        # ============================================
        
        # 例1: 標準的なPyTorchモデル
        self.model = torch.load(model_path, map_location=self.device)
        self.model.eval()
        
        # 例2: state_dictのみを保存している場合
        # from your_model import YourModelClass
        # self.model = YourModelClass()
        # self.model.load_state_dict(torch.load(model_path, map_location=self.device))
        # self.model.eval()
        
        # 例3: Stable-Baselines3
        # from stable_baselines3 import PPO
        # self.model = PPO.load(model_path, device=self.device)
        
        # 例4: RLlib
        # from ray.rllib.policy.policy import Policy
        # self.model = Policy.from_checkpoint(model_path)
        
        print(f"✓ Model loaded from {model_path}")
    
    def predict_action(
        self,
        observation: Any,
        action_mask: Optional[np.ndarray] = None,
        **kwargs
    ) -> int:
        """
        Observationからアクションを予測
        
        Args:
            observation: ゲーム状態のObservation
                        （形式はto_observation()の返り値に依存）
            action_mask: 有効なアクションのマスク（オプション）
            **kwargs: 追加のパラメータ
            
        Returns:
            予測されたアクション（整数）
        """
        if self.model is None:
            # ランダムエージェント
            return 0
        
        # ============================================
        # TODO: あなたのエージェントの推論方法に変更
        # ============================================
        
        # 例1: 標準的なPyTorchモデル（numpy入力）
        if isinstance(observation, np.ndarray):
            obs_tensor = torch.from_numpy(observation).float().unsqueeze(0).to(self.device)
            
            with torch.no_grad():
                logits = self.model(obs_tensor)
                
                # アクションマスクを適用（オプション）
                if action_mask is not None:
                    mask_tensor = torch.from_numpy(action_mask).float().to(self.device)
                    logits = logits + (mask_tensor - 1) * 1e9
                
                action = logits.argmax().item()
            
            return action
        
        # 例2: 辞書形式のObservation
        elif isinstance(observation, dict):
            # 辞書の各要素をTensorに変換
            obs_tensors = {}
            for key, value in observation.items():
                if isinstance(value, np.ndarray):
                    obs_tensors[key] = torch.from_numpy(value).float().unsqueeze(0).to(self.device)
                else:
                    obs_tensors[key] = torch.tensor([value]).to(self.device)
            
            with torch.no_grad():
                logits = self.model(obs_tensors)
                action = logits.argmax().item()
            
            return action
        
        # 例3: Stable-Baselines3
        # action, _states = self.model.predict(observation, deterministic=True)
        # return int(action)
        
        # 例4: RLlib
        # action = self.model.compute_single_action(observation)
        # return int(action)
        
        else:
            raise ValueError(f"Unsupported observation type: {type(observation)}")
    
    def get_action_mask(self, game_state) -> np.ndarray:
        """
        現在のゲーム状態から有効なアクションのマスクを生成
        
        Args:
            game_state: GameStateオブジェクト
            
        Returns:
            アクションマスク（1=有効, 0=無効）
        """
        # ============================================
        # TODO: アクション空間のサイズに合わせて変更
        # ============================================
        action_space_size = 100  # あなたのアクション空間のサイズ
        mask = np.ones(action_space_size, dtype=np.float32)
        
        # 例: 資源が足りない場合は建設アクションを無効化
        # if game_state.my_resources['wood'] < 1 or game_state.my_resources['clay'] < 1:
        #     mask[4:24] = 0  # 道路建設アクション（4-23）を無効化
        
        return mask


# ============================================
# 使用例
# ============================================
if __name__ == "__main__":
    # エージェントの初期化
    agent = CustomCatanAgent("path/to/model.pth")
    
    # ダミーのObservationでテスト
    dummy_obs = np.random.randn(58).astype(np.float32)
    action = agent.predict_action(dummy_obs)
    print(f"Predicted action: {action}")
    
    # アクションマスク付きでテスト
    action_mask = np.ones(100, dtype=np.float32)
    action_mask[50:] = 0  # 後半のアクションを無効化
    action = agent.predict_action(dummy_obs, action_mask)
    print(f"Predicted action with mask: {action}")
