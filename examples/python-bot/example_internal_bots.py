"""
JSettlers内蔵ボットを使用したゲームプレイの例

このスクリプトは、問題文のコードに基づいて、内蔵ボットとプレイする方法を示します。
"""

# 注意: このコードは問題文で提供されたjsettlers_bot.pyファイルが
# 必要な変更を含んでいることを前提としています。

# 必要なインポート（問題文のコードに基づく）
# from jsettlers_bot import JSettlersBot
# import pycatan
# import torch
# from your_agent_module import YourAgent  # 実際のエージェントクラス


def example_create_game_with_internal_bots():
    """
    例1: 3体の内蔵ボットと一緒に新しいゲームを作成
    
    この例では：
    - Pythonボットがゲームを作成
    - Pythonボットが自動的に座席を確保
    - サーバーが残りの3席に内蔵ボットを自動配置
    """
    
    # サーバー接続情報
    HOST = "localhost"
    PORT = 8880
    NICKNAME = "PyBot"
    COOKIE = "your_robot_cookie"  # サーバーのロボット認証クッキー
    
    # エージェントの初期化（実際のエージェント実装に置き換えてください）
    # agent = YourAgent()
    # device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    
    # ボットの初期化
    # bot = JSettlersBot(
    #     host=HOST,
    #     port=PORT,
    #     nickname=NICKNAME,
    #     cookie=COOKIE,
    #     agent=agent,
    #     device=device
    # )
    
    # ゲームを実行（3体の内蔵ボットと）
    # bot.run(
    #     game_name="MyGame",
    #     mode="create",        # ゲームを新規作成
    #     num_robots=3,         # 3体の内蔵ボット（サーバーが自動追加）
    #     num_games=1           # 1ゲームプレイ
    # )
    
    print("✅ 例1: 3体の内蔵ボットとゲームを作成")
    print("   - Pythonボット: 1体（自分）")
    print("   - 内蔵ボット: 3体（サーバーが自動追加）")
    print("   - 合計: 4人ゲーム")


def example_join_existing_game():
    """
    例2: 既存のゲームに参加
    
    この例では：
    - 既に作成されているゲームに参加
    - 空いている席に座る
    """
    
    HOST = "localhost"
    PORT = 8880
    NICKNAME = "PyBot2"
    COOKIE = "your_robot_cookie"
    
    # bot = JSettlersBot(
    #     host=HOST,
    #     port=PORT,
    #     nickname=NICKNAME,
    #     cookie=COOKIE,
    #     agent=agent,
    #     device=device
    # )
    
    # 既存のゲームに参加
    # bot.run(
    #     game_name="ExistingGame_0",
    #     mode="join",          # 既存ゲームに参加
    #     num_robots=0,         # 既に他のプレイヤーがいる想定
    #     num_games=1
    # )
    
    print("✅ 例2: 既存のゲームに参加")


def example_multiple_games():
    """
    例3: 複数のゲームを連続でプレイ
    
    この例では：
    - 複数のゲームを自動的に作成してプレイ
    - 各ゲームで内蔵ボットを使用
    """
    
    HOST = "localhost"
    PORT = 8880
    NICKNAME = "PyBot3"
    COOKIE = "your_robot_cookie"
    
    # bot = JSettlersBot(
    #     host=HOST,
    #     port=PORT,
    #     nickname=NICKNAME,
    #     cookie=COOKIE,
    #     agent=agent,
    #     device=device
    # )
    
    # 5ゲーム連続でプレイ
    # bot.run(
    #     game_name="TrainingGame",
    #     mode="create",
    #     num_robots=3,
    #     num_games=5            # 5ゲームプレイ
    # )
    # 実際には: TrainingGame_0, TrainingGame_1, ..., TrainingGame_4 が作成される
    
    print("✅ 例3: 5ゲーム連続でプレイ")


def explanation_of_seat_selection():
    """
    座席選択の説明
    """
    print("\n" + "="*60)
    print("座席選択について")
    print("="*60)
    
    print("\n【推奨方法】自動割り当て:")
    print("```python")
    print("self.sit_down(self.current_game, preferred_seat=-1)")
    print("```")
    print("- サーバーが自動的に空いている席を割り当て")
    print("- 内蔵ボットとの競合を回避")
    print("- 最も安全で推奨される方法")
    
    print("\n【代替方法】特定の席を指定:")
    print("```python")
    print("self.sit_down(self.current_game, preferred_seat=0)  # 席0を要求")
    print("```")
    print("- 特定の席番号（0〜3）を指定")
    print("- その席が空いている場合のみ成功")
    print("- 競合のリスクあり")


def explanation_of_bot_types():
    """
    内蔵ボットの種類の説明
    """
    print("\n" + "="*60)
    print("内蔵ボットの種類")
    print("="*60)
    
    print("\n【FAST_STRATEGY ボット】")
    print("- 名前: dumb01, dumb02, dumb03, ...")
    print("- 特徴: 高速だが単純な判断")
    print("- 割合: 約70%")
    print("- 戦略: 基本的な建設と交易のみ")
    
    print("\n【SMART_STRATEGY ボット】")
    print("- 名前: robot 1, robot 2, ...")
    print("- 特徴: 賢いが計算に時間がかかる")
    print("- 割合: 約30%")
    print("- 戦略: Win Game ETA（勝利推定ターン数）を計算")
    print("         最適な建設計画を立てる")
    
    print("\n【サーバーの動作】")
    print("- サーバーは自動的にこれらのボットを選択")
    print("- 約70%がFAST、30%がSMARTの比率で配置")
    print("- クライアント側から種類を指定することはできない")


def troubleshooting_guide():
    """
    トラブルシューティングガイド
    """
    print("\n" + "="*60)
    print("トラブルシューティング")
    print("="*60)
    
    print("\n【問題1】内蔵ボットが参加しない")
    print("原因: サーバーに内蔵ボットが起動していない")
    print("解決策:")
    print("  サーバー起動時にボットを有効化:")
    print("  $ java -jar JSettlersServer.jar \\")
    print("      -Djsettlers.bots.cookie=your_cookie \\")
    print("      -Djsettlers.startrobots=7")
    
    print("\n【問題2】Pythonボットが座席を確保できない")
    print("原因: タイミングの問題または全席が埋まっている")
    print("解決策:")
    print("  1. ゲーム参加確認（1013）を待ってから座席を要求")
    print("  2. 自動割り当て（-1）を使用")
    print("  3. player_idを正しく初期化・管理")
    
    print("\n【問題3】ゲームが開始しない")
    print("原因: すべての席が埋まるのを待っている")
    print("解決策:")
    print("  - サーバーログを確認")
    print("  - num_robotsパラメータが正しいか確認")
    print("    例: 4人ゲームならnum_robots=3（自分+ボット3=4）")


def main():
    """
    メイン関数 - すべての例を表示
    """
    print("=" * 60)
    print("JSettlers内蔵ボット使用例")
    print("=" * 60)
    
    # 例の実行
    print("\n" + "-"*60)
    example_create_game_with_internal_bots()
    
    print("\n" + "-"*60)
    example_join_existing_game()
    
    print("\n" + "-"*60)
    example_multiple_games()
    
    # 説明の表示
    explanation_of_seat_selection()
    explanation_of_bot_types()
    troubleshooting_guide()
    
    print("\n" + "="*60)
    print("詳細は以下のドキュメントを参照してください:")
    print("- INTERNAL_BOTS.ja.md - 内蔵ボットシステムの概要")
    print("- IMPLEMENTING_INTERNAL_BOTS.ja.md - 実装ガイド")
    print("="*60)


if __name__ == "__main__":
    main()
