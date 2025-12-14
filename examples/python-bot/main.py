#!/usr/bin/env python3
"""
JSettlers Python Bot メイン実行ファイル

Usage:
    python main.py <host> <port> <nickname> <cookie> [--simple | model_path]
    
Examples:
    # シンプルなヒューリスティックエージェント（モデル不要）
    python main.py localhost 8880 mybot abc123 --simple
    
    # PyTorchモデルを使用
    python main.py localhost 8880 mybot abc123 model.pth
"""
import sys
from pathlib import Path

from jsettlers_bot import JSettlersBot

def main():
    if len(sys.argv) < 5:
        print("Usage: python main.py <host> <port> <nickname> <cookie> [--simple | model_path]")
        print()
        print("Examples:")
        print("  # シンプルなヒューリスティックエージェント（推奨・すぐ動作確認可能）")
        print("  python main.py localhost 8880 mybot abc123 --simple")
        print()
        print("  # PyTorchモデルを使用")
        print("  python main.py localhost 8880 mybot abc123 model.pth")
        print()
        sys.exit(1)
    
    host = sys.argv[1]
    port = int(sys.argv[2])
    nickname = sys.argv[3]
    cookie = sys.argv[4]
    agent_type = sys.argv[5] if len(sys.argv) > 5 else "--simple"
    
    print("🤖 JSettlers Python Bot")
    print("=" * 50)
    print(f"Host: {host}:{port}")
    print(f"Nickname: {nickname}")
    print()
    
    # エージェントをロード
    print("🧠 Loading agent...")
    
    if agent_type == "--simple" or agent_type == "-s":
        # シンプルなヒューリスティックエージェントを使用
        from simple_agent import SimpleHeuristicAgent
        agent = SimpleHeuristicAgent()
        print("✓ Using simple heuristic agent (no ML model required)")
    elif agent_type == "--improved" or agent_type == "-i":
        # 改良版ヒューリスティックエージェントを使用
        from simple_agent import ImprovedHeuristicAgent
        agent = ImprovedHeuristicAgent()
        print("✓ Using improved heuristic agent (no ML model required)")
    else:
        # PyTorchモデルを使用
        try:
            from agent import CatanAgent
            agent = CatanAgent(agent_type)
            print(f"✓ Loaded PyTorch agent from {agent_type}")
        except ImportError:
            print("⚠️  PyTorch not installed. Using simple heuristic agent instead.")
            from simple_agent import SimpleHeuristicAgent
            agent = SimpleHeuristicAgent()
    
    print("✓ Agent ready")
    print()
    
    # ボットを作成
    bot = JSettlersBot(host, port, nickname, cookie, agent)
    
    # 接続して実行
    bot.connect()
    bot.authenticate()
    bot.run()

if __name__ == "__main__":
    main()
