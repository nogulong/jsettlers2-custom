import argparse # argparseを使うと引数処理が楽になります
import sys
from jsettlers_bot import JSettlersBot

def main():
    parser = argparse.ArgumentParser(description='JSettlers Python Bot')
    parser.add_argument('host', help='Server Host')
    parser.add_argument('port', type=int, help='Server Port')
    parser.add_argument('nickname', help='Bot Nickname')
    parser.add_argument('cookie', help='Auth Cookie (dummy)')
    parser.add_argument('--model', default=None, help='Path to model file')
    
    # ★追加: モード切替
    parser.add_argument('--create', action='store_true', help='Create a new game instead of joining')
    parser.add_argument('--game', default='eval', help='Game name to join (if not creating)')
    parser.add_argument('--num_games', type=int, default=1, help='Number of games to create/join (default: 1)')
    
    # ★追加: CPUボットを何体追加するか (デフォルトは3=ソロプレイ用)
    parser.add_argument('--robots', type=int, default=3, help='Number of CPU robots to add (0-3)')

    args = parser.parse_args()

    # エージェントのロード（簡略化しています）
    if args.model:
        print(f"🧠 Loading ML agent from {args.model}...")
        # agent = ...
        agent = None # 仮
    else:
        print("🧠 Using Simple Heuristic Agent")
        from simple_agent import SimpleHeuristicAgent
        agent = SimpleHeuristicAgent()

    # ボット作成
    bot = JSettlersBot(args.host, args.port, args.nickname, args.cookie, agent)
    
    bot.connect()
    bot.authenticate() 

    # 実行モードの指定
    if args.create:
        print(f"🛠️  Mode: CREATOR (Adding {args.robots} CPU bots)")
        # 作成モード: CPUボットの数も渡す
        bot.run(mode="create", num_robots=args.robots, game_name=args.game, num_games=args.num_games)
        
    elif args.game:
        print(f"👉 Mode: JOINER (Joining '{args.game}')")
        # 参加モード: 既存ゲームに入るだけ
        bot.run(mode="join", game_name=args.game, num_games=args.num_games)
        
    else:
        # デフォルト動作（ランダム作成、CPU3体）
        bot.run(mode="create", num_robots=3)

if __name__ == "__main__":
    main()