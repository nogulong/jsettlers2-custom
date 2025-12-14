"""
単純なヒューリスティックエージェント（デモ用）

このエージェントはルールベースで動作し、学習済みモデルは不要です。
"""
import random

class SimpleHeuristicAgent:
    """
    単純なルールベースのエージェント
    
    このエージェントは：
    - サイコロは自動的に振られる（ゲーム状態15で）
    - ターン中はすぐにターンを終了する
    
    実際の強化学習エージェントの代わりにデモンストレーション用に使用できます。
    """
    
    def __init__(self):
        """エージェントを初期化"""
        print("🤖 Simple heuristic agent initialized")
        print("   This agent uses rule-based decisions (no ML model required)")
        print("   Strategy: Roll dice (automatic) → End turn immediately")
    
    def predict_action(self, observation=None, game_state=None) -> int:
        """
        ヒューリスティックに基づいてアクションを選択
        
        Args:
            observation: ゲーム状態（このエージェントでは使用しない）
            game_state: GameStateオブジェクト（リソースチェック用）
            
        Returns:
            アクション番号（整数）
            0 = ターンを終了
        """
        # シンプルな戦略: 常にターンを終了
        # サイコロは状態15で自動的に振られます
        return 0  # ターンを終了
    
    def __repr__(self):
        return "SimpleHeuristicAgent(rule-based)"


# より高度なヒューリスティックエージェントの例
class ImprovedHeuristicAgent:
    """
    より洗練されたルールベースのエージェント
    """
    
    def __init__(self):
        print("🤖 Improved heuristic agent initialized")
        print("   Strategy: Roll dice → Check resources → Build or end turn")
        self.turn_count = 0
    
    def predict_action(self, observation=None, game_state=None) -> int:
        """
        より高度なヒューリスティックでアクションを選択
        
        Returns:
            0 = ターンを終了
            1 = 道路建設を試みる
            2 = 集落建設を試みる
        """
        self.turn_count += 1
        
        if game_state is None:
            return 0  # ターンを終了
        
        # ゲーム状態を分析
        my_resources = game_state.my_resources
        total_resources = sum(my_resources.values())
        
        print(f"   📊 Resources: {total_resources} total")
        
        # 戦略1: 初期段階では積極的に建設を試みる
        if self.turn_count < 50 and total_resources >= 4:
            # 集落建設の資源があるか確認
            if (my_resources['wood'] >= 1 and 
                my_resources['clay'] >= 1 and 
                my_resources['sheep'] >= 1 and 
                my_resources['wheat'] >= 1):
                print("   🏠 Attempting to build settlement")
                return 2  # 集落建設
            
            # 道路建設の資源があるか確認
            if my_resources['wood'] >= 1 and my_resources['clay'] >= 1:
                print("   🛣️  Attempting to build road")
                return 1  # 道路建設
        
        # デフォルト: ターンを終了
        print("   ⏭️  Ending turn")
        return 0
    
    def __repr__(self):
        return f"ImprovedHeuristicAgent(turn={self.turn_count})"


if __name__ == "__main__":
    # テスト
    print("Testing SimpleHeuristicAgent:")
    agent = SimpleHeuristicAgent()
    for i in range(5):
        action = agent.predict_action()
        print(f"  Turn {i+1}: action = {action} (0=end turn)")
    
    print("\nTesting ImprovedHeuristicAgent:")
    agent2 = ImprovedHeuristicAgent()
    for i in range(5):
        action = agent2.predict_action()
        print(f"  Turn {i+1}: action = {action}")
