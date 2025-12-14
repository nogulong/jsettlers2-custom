"""
PyTorchエージェントのラッパー
"""
import torch
import torch.nn as nn
import numpy as np
from pathlib import Path

class CatanAgent:
    """
    PyTorchで実装したエージェント
    
    注意: これは例です。実際のモデルアーキテクチャに合わせてカスタマイズしてください。
    """
    
    def __init__(self, model_path: str = None):
        """
        Args:
            model_path: 学習済みモデルのパス（Noneの場合はランダムエージェント）
        """
        if model_path is None or not Path(model_path).exists():
            # モデルファイルが存在しない場合は、ダミーモデルを使用
            print(f"⚠️  Model file not found: {model_path}")
            print("⚠️  Using dummy random agent for demonstration")
            self.model = None
        else:
            # モデルをロード
            self.model = torch.load(model_path, map_location='cpu')
            self.model.eval()
            print(f"✓ Loaded model from {model_path}")
        
    def predict_action(self, observation: np.ndarray) -> int:
        """
        Observationからアクションを予測
        
        Args:
            observation: ゲーム状態のObservation
            
        Returns:
            予測されたアクション（整数）
        """
        if self.model is None:
            # ダミーエージェント: ランダムなアクション（0: サイコロを振る）
            return 0
        
        # NumPy配列をTensorに変換
        obs_tensor = torch.from_numpy(observation).float().unsqueeze(0)
        
        # 予測
        with torch.no_grad():
            output = self.model(obs_tensor)
            action = output.argmax().item()
        
        return action
