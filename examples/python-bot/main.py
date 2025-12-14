#!/usr/bin/env python3
"""
JSettlers Python Bot メイン実行ファイル

Usage:
    python main.py <host> <port> <nickname> <cookie> <model_path>
    
Example:
    python main.py localhost 8880 mybot abc123 model.pth
"""
import sys
from pathlib import Path

from jsettlers_bot import JSettlersBot
from agent import CatanAgent

def main():
    if len(sys.argv) < 5:
        print("Usage: python main.py <host> <port> <nickname> <cookie> [model_path]")
        print("Example: python main.py localhost 8880 mybot abc123 model.pth")
        print()
        print("Note: model_path is optional. If not provided, a random agent will be used.")
        sys.exit(1)
    
    host = sys.argv[1]
    port = int(sys.argv[2])
    nickname = sys.argv[3]
    cookie = sys.argv[4]
    model_path = sys.argv[5] if len(sys.argv) > 5 else "model.pth"
    
    print("🤖 JSettlers Python Bot with PyTorch Agent")
    print("=" * 50)
    print(f"Host: {host}:{port}")
    print(f"Nickname: {nickname}")
    print(f"Model: {model_path}")
    print()
    
    # エージェントをロード
    print("🧠 Loading agent...")
    agent = CatanAgent(model_path)
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
