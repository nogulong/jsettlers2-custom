# JSettlers内蔵ボット統合ガイド

## 問題の要約

問題文のコードでは、ゲーム作成時に指定した数の内蔵ボットを追加し、Pythonボットが有効な座席に座れるようにし、内蔵ボットの座席を奪わないようにする必要があります。

## 解決策

### 1. 内蔵ボットの自動追加

JSettlersサーバーは、ゲームが準備完了状態（READY）になると、空いている席に自動的に内蔵ボットを追加します。したがって、**明示的にボットを要求する必要はありません**。

サーバーの動作：
1. ゲームが作成される
2. プレイヤーが席に座る
3. ゲームが開始準備ができると、サーバーは自動的に空席に内蔵ボットを配置
4. 全席が埋まるとゲーム開始

### 2. 座席選択の改善

問題文のコードでは `sit_down()` メソッドが常に席0を指定していますが、これを改善する必要があります。

#### 推奨される実装

```python
def sit_down(self, game_name: str, preferred_seat: int = -1):
    """
    席に座るリクエスト (1012)
    
    Args:
        game_name: ゲーム名
        preferred_seat: 希望する座席番号（-1 = 自動割り当て）
    """
    print(f"🪑 Requesting to sit in game: {game_name}, seat: {preferred_seat}")
    
    # -1を指定すると、サーバーが自動的に空いている席を割り当てる
    msg = f"1012|{game_name},-,{preferred_seat},true"
    
    write_java_utf(self.sock, msg)
    print(f"→ {msg}")
```

#### 使用方法

```python
# 方法1: 自動割り当て（推奨）
self.sit_down(self.current_game, preferred_seat=-1)

# 方法2: 特定の席を指定
self.sit_down(self.current_game, preferred_seat=0)
```

### 3. ゲーム作成フローの改善

問題文のコードの `create_game()` メソッドは正しく実装されていますが、座席確保のタイミングを改善する必要があります：

```python
def create_game(self, game_name: str):
    """ゲームを作成"""
    print(f"🛠️ Creating new game: {game_name}")
    
    # ゲーム作成リクエスト (1013)
    msg = f"1013|{self.nickname},-,-,{game_name}"
    write_java_utf(self.sock, msg)
    print(f"→ {msg}")
    
    # current_game をセット
    self.current_game = game_name
```

### 4. メッセージハンドラの改善

`handle_message()` メソッドで、ゲーム参加の確認を待ってから座席を要求：

```python
elif msg_type == "1013": # JOINGAME 誰かがゲームに入室した
    args = parsed.get("args", [])
    if len(args) >= 1:
        name = args[0]
        
        # 自分が入室した通知が来たら、座席を要求
        if name == self.nickname and self.player_id == -1:
            print("🚀 Join complete. Requesting seat...")
            # 自動割り当てを使用（推奨）
            self.sit_down(self.current_game, preferred_seat=-1)
```

## 完全な実装例

以下は、問題文のコードに必要な変更点です：

### 変更1: `__init__` メソッドの初期化

```python
def __init__(self, host: str, port: int, nickname: str, cookie: str, agent, device=None):
    # ... 既存のコード ...
    
    self.player_id = -1  # 初期化されていない座席番号
    self.target_num_robots = 0  # 目標ボット数
    
    # ... 既存のコード ...
```

### 変更2: `sit_down` メソッドの更新

```python
def sit_down(self, game_name: str, preferred_seat: int = -1):
    """
    席に座るリクエスト (1012)
    
    Args:
        game_name: ゲーム名  
        preferred_seat: 希望する座席番号（-1 = 自動割り当て）
    """
    print(f"🪑 Requesting to sit in game: {game_name}, seat: {preferred_seat}")
    
    msg = f"1012|{game_name},-,{preferred_seat},true"
    
    write_java_utf(self.sock, msg)
    print(f"→ {msg}")
```

### 変更3: メッセージハンドラの更新

```python
elif msg_type == "1012": # SITDOWN
    args = parsed.get("args", [])
    if len(args) >= 3:
        name = args[1]
        seat = int(args[2])
        
        if name == self.nickname:
            self.player_id = seat
            self.game_state.set_player_id(seat)
            print(f"✅ Success! I am Player {seat}!")

elif msg_type == "1013": # JOINGAME
    args = parsed.get("args", [])
    if len(args) >= 1:
        name = args[0]
        
        # 自分が入室した通知が来たら、座席を要求
        if name == self.nickname and self.player_id == -1:
            print("🚀 Join complete. Requesting auto-seat assignment...")
            # 自動割り当てを使用
            self.sit_down(self.current_game, preferred_seat=-1)
```

### 変更4: `run` メソッドの改善

```python
def run(self, game_name, mode="create", num_robots=3, num_games=1):
    """
    メインループ
    
    Args:
        game_name: ゲーム名のベース
        mode: "create" または "join"
        num_robots: 内蔵ボットの数（注: サーバーが自動的に追加）
        num_games: プレイするゲーム数
    """
    self.target_num_robots = num_robots 
    games_played = 0

    if not self.sock:
        self.connect()
        self.authenticate()
        
    try:
        while games_played < num_games:
            current_game_name = f"{game_name}_{games_played}"
            self.player_id = -1  # リセット
            
            if mode == "create":
                self.create_game(current_game_name)
            elif mode == "join":
                self.current_game = current_game_name
                self.join_game(current_game_name)
        
            # メインメッセージループ
            while True:
                message = read_java_utf(self.sock)
                print(f"← {message}")
                
                self.handle_message(message)
                
                # ゲーム終了条件のチェック（実装が必要）
                # if game_finished:
                #     games_played += 1
                #     break
                
    except KeyboardInterrupt:
        print("\n👋 Shutting down...")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if self.sock:
            self.sock.close()
```

## 重要なポイント

### 1. サーバーが自動的にボットを追加

JSettlersサーバーは、ゲームが開始準備完了状態になると、自動的に空席に内蔵ボットを配置します。クライアント側から明示的にボットを要求する必要は**ありません**。

### 2. 座席の自動割り当てを使用

`preferred_seat=-1` を使用すると、サーバーが自動的に空いている席を割り当てるため、内蔵ボットとの競合を避けることができます。

### 3. タイミングが重要

1. ゲームを作成
2. ゲーム参加の確認を待つ（1013メッセージ）
3. 座席を要求（1012メッセージ）
4. 座席確保の確認を待つ（1012メッセージの受信）
5. サーバーが自動的に残りの席に内蔵ボットを追加
6. ゲーム開始（1018メッセージ）

## 内蔵ボットの種類について

### FAST_STRATEGY ボット
- **名前**: `dumb01`, `dumb02`, `dumb03`, ...
- **特徴**: 高速だが単純な判断
- **割合**: 約70%

### SMART_STRATEGY ボット
- **名前**: `robot 1`, `robot 2`, ...
- **特徴**: 賢いが計算に時間がかかる
- **割合**: 約30%

サーバーは自動的にこれらのボットを適切な比率で選択します。

## トラブルシューティング

### 問題: 内蔵ボットが参加しない

**原因**: サーバーに内蔵ボットが起動していない

**解決策**:
```bash
# サーバー起動時にボットを有効化
java -jar JSettlersServer.jar -Djsettlers.bots.cookie=your_cookie -Djsettlers.startrobots=7
```

### 問題: Pythonボットが座席を確保できない

**原因**: タイミングの問題、または全席が埋まっている

**解決策**:
1. ゲーム参加確認（1013）を待ってから座席を要求
2. 自動割り当て（-1）を使用
3. リトライロジックを実装

### 問題: ゲームが開始しない

**原因**: すべての席が埋まるのを待っている

**解決策**:
- サーバーログを確認
- すべてのプレイヤー（Python + 内蔵ボット）が席に座るまで待つ
- `num_robots` パラメータが正しいことを確認（例：4人ゲームでnum_robots=3）

## まとめ

問題文のコードに必要な主な変更点：

1. ✅ `sit_down()` メソッドに `preferred_seat` パラメータを追加
2. ✅ メッセージハンドラで自動割り当て（-1）を使用
3. ✅ `player_id` を適切に初期化・管理
4. ✅ サーバーが自動的にボットを追加することを理解

これらの変更により、Pythonボットは内蔵ボットと競合することなく、適切な座席に座ることができます。
