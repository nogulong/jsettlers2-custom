"""
単純なヒューリスティックエージェント（デモ用）

このエージェントはルールベースで動作し、学習済みモデルは不要です。
"""
import random

class SimpleHeuristicAgent:
    """
    単純なルールベースのエージェント
    
    このエージェントは：
    - ターン開始時にサイコロを振る
    - 資源が十分にあれば道路や集落を建設しようとする
    - それ以外はターンを終了する
    
    実際の強化学習エージェントの代わりにデモンストレーション用に使用できます。
    """
    
    def __init__(self):
        """エージェントを初期化"""
        print("🤖 Simple heuristic agent initialized")
        print("   This agent uses rule-based decisions (no ML model required)")
    
    def predict_action(self, observation=None, game_state=None) -> int:
        """
        ヒューリスティックに基づいてアクションを選択
        
        Args:
            observation: ゲーム状態（このエージェントでは使用しない）
            game_state: GameStateオブジェクト（リソースチェック用）
            
        Returns:
            アクション番号（整数）
        """
        # 基本的な戦略:
        # - ゲーム状態に関係なく、常にサイコロを振るかターンを終了
        # - 実際のゲームでは、サイコロを振った後に建設などができる
        
        if game_state is not None:
            # 簡単なヒューリスティック: 資源が多ければ建設を試みる
            total_resources = sum(game_state.my_resources.values())
            
            if total_resources >= 4:
                # 資源が4つ以上あれば、ランダムに建設アクションを選ぶ
                # （実際には建設可能な場所を確認する必要がある）
                print("   💡 Resources available, considering build action")
                return random.choice([0, 1, 2])  # 0=dice, 1=road, 2=settlement
        
        # デフォルト: サイコロを振る（アクション0）
        return 0
    
    def __repr__(self):
        return "SimpleHeuristicAgent(rule-based)"


# より高度なヒューリスティックエージェントの例
class ImprovedHeuristicAgent:
    """
    より洗練されたルールベースのエージェント
    """
    
    def __init__(self):
        print("🤖 Improved heuristic agent initialized")
        self.turn_count = 0
    
    def predict_action(self, observation=None, game_state=None) -> int:
        """
        より高度なヒューリスティックでアクションを選択
        """
        self.turn_count += 1
        
        if game_state is None:
            return 0  # サイコロを振る
        
        # ゲーム状態を分析
        my_resources = game_state.my_resources
        total_resources = sum(my_resources.values())
        
        # 戦略1: 初期段階では積極的に建設
        if self.turn_count < 20 and total_resources >= 4:
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
        
        # 戦略2: 資源が少ない場合はサイコロを振る
        if total_resources < 3:
            print("   🎲 Rolling dice (low resources)")
            return 0
        
        # デフォルト: サイコロを振る
        return 0
    
    def __repr__(self):
        return f"ImprovedHeuristicAgent(turn={self.turn_count})"


if __name__ == "__main__":
    # テスト
    print("Testing SimpleHeuristicAgent:")
    agent = SimpleHeuristicAgent()
    for i in range(5):
        action = agent.predict_action()
        print(f"  Turn {i+1}: action = {action}")
    
    print("\nTesting ImprovedHeuristicAgent:")
    agent2 = ImprovedHeuristicAgent()
    for i in range(5):
        action = agent2.predict_action()
        print(f"  Turn {i+1}: action = {action}")
