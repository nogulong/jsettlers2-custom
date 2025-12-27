# JSettlers内蔵ボットシステム

## 概要

JSettlersサーバーには内蔵のロボットプレイヤー（ボット）システムがあり、人間プレイヤーやサードパーティのボットと一緒にゲームをプレイできます。

## 内蔵ボットの種類

JSettlersには2種類の内蔵ボット戦略があります：

### 1. FAST_STRATEGY（高速戦略）
- **特徴**: より高速だが、よりシンプルなAI
- **割合**: 内蔵ボットの約70%
- **適用**: `dumb01`、`dumb02`、`dumb03` などの名前のボット
- **戦略**: 基本的な判断で素早く行動

### 2. SMART_STRATEGY（スマート戦略）
- **特徴**: より賢いが、計算に時間がかかる
- **割合**: 内蔵ボットの約30%
- **適用**: `robot 1`、`robot 2` などの名前のボット
- **戦略**: Win Game ETA（勝利までの推定ターン数）を計算し、より複雑な判断を行う

## ゲーム作成時の内蔵ボット追加方法

### 基本的な流れ

1. **ゲームを作成する**
   - メッセージ `1013` (JOINGAME) または `1078` (NEWGAMEWITHOPTIONSREQUEST) を使用
   - サーバーが新しいゲームを作成

2. **ゲームに参加する**
   - Pythonボットはゲーム作成時に自動的に参加
   - または別途 `1013` メッセージで参加

3. **席に座る**
   - メッセージ `1012` (SITDOWN) で特定の席を要求
   - または `-1` を指定して空いている席に自動割り当て

4. **内蔵ボットを要求する**
   - サーバーは空席があり、利用可能な内蔵ボットがいる場合、自動的にボットを追加
   - ゲームの準備が整うと（全席が埋まるか、プレイヤーがゲーム開始を要求すると）自動的に開始

### Pythonボットの実装

Pythonボットで内蔵ボットを使用する場合：

```python
# ゲーム作成時にnum_robotsパラメータを指定
bot = JSettlersBot(host, port, nickname, cookie, agent)
bot.run(game_name="MyGame", mode="create", num_robots=3, num_games=1)
```

## 座席の選択

### 重要事項

1. **自動座席割り当て**: `sit_down()` メソッドで `-1` を指定すると、サーバーが自動的に空いている席を割り当てます
   ```python
   msg = f"1012|{game_name},-,-1,true"
   ```

2. **特定の席を指定**: 0〜3の座席番号を指定できます（4人ゲームの場合）
   ```python
   msg = f"1012|{game_name},-,0,true"  # 席0を要求
   ```

3. **内蔵ボットとの競合回避**: 
   - 内蔵ボットはサーバーが管理し、空いている席に自動的に配置されます
   - Pythonボットが先に座席を確保すれば、内蔵ボットはその席を取りません
   - サーバーは `BOTJOINGAMEREQUEST` (メッセージ1023) を使って内蔵ボットに特定の席に座るよう指示します

## プロトコルメッセージ

### SITDOWN (1012)
席に座るリクエスト/通知

**クライアント→サーバー**:
```
1012|{ゲーム名}|{ニックネーム}|{座席番号}|{ロボットフラグ}
```

例:
```
1012|MyGame|-,0,true
```

**サーバー→クライアント**: 誰かが座ったことを通知

### BOTJOINGAMEREQUEST (1023)
サーバーが内蔵ボットに特定のゲームと席に参加するよう要求（サーバー→ボットのみ）

```
1023|{ゲーム名}|{座席番号}|{ゲームオプション}
```

### JOINGAME (1013)
ゲームに参加する（作成または既存のゲームに参加）

```
1013|{ニックネーム}|-,-,{ゲーム名}
```

## 実装例

### 例1: 3体の内蔵ボットと一緒にゲームを作成

```python
bot = JSettlersBot("localhost", 8880, "MyPyBot", "cookie", agent)
bot.run(game_name="TestGame", mode="create", num_robots=3)
```

この場合：
1. Pythonボットがゲームを作成
2. Pythonボットが自動的に座席0に座る
3. サーバーが残りの3席に内蔵ボットを配置
4. 全席が埋まったらゲーム開始

### 例2: 特定の席を選択

```python
# jsettlers_bot.py の sit_down メソッドを変更
def sit_down(self, game_name: str, seat_number: int = -1):
    """席に座るリクエスト"""
    print(f"🪑 Requesting to sit in game: {game_name}, seat: {seat_number}")
    
    msg = f"1012|{game_name},-,{seat_number},true"
    
    write_java_utf(self.sock, msg)
    print(f"→ {msg}")
```

## トラブルシューティング

### 問題: 内蔵ボットが参加しない
- **原因**: サーバーに利用可能な内蔵ボットがない
- **解決策**: サーバー起動時に `-Djsettlers.bots.cookie={cookie}` オプションで内蔵ボットを有効化

### 問題: Pythonボットが内蔵ボットの席を奪う
- **原因**: 座席の競合
- **解決策**: ゲーム作成直後に素早く `sit_down()` を呼び出し、特定の席を確保する

### 問題: ゲームが開始しない
- **原因**: 全席が埋まっていない、またはプレイヤーが開始を待っている
- **解決策**: すべてのプレイヤー（Pythonボット + 内蔵ボット）が席に座るのを待つ

## 参考資料

- JSettlers ソースコード: `src/main/java/soc/robot/`
- ロボット戦略: `SOCRobotDM.java` の `FAST_STRATEGY` と `SMART_STRATEGY`
- サーバーのボット管理: `SOCServer.java` の `setupLocalRobots()` と `readyGameAskRobotsJoin()`
