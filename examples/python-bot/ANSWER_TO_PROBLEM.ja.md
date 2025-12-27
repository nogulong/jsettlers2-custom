# 問題文への回答

## 質問1: ゲーム作成時に指定した数だけ内蔵ボットを追加する方法

### 答え: サーバーが自動的に追加します

JSettlersサーバーは、**ゲームが準備完了状態になると自動的に空席に内蔵ボットを配置します**。クライアント側から明示的にボットを要求する必要はありません。

### 実装方法

問題文のコードは既に正しく実装されています：

```python
def run(self, game_name, mode="create", num_robots=3, num_games=1):
    """メインループ"""
    
    # num_robotsパラメータは記録用
    self.target_num_robots = num_robots 
    
    if mode == "create":
        self.create_game(current_game_name)
    
    # サーバーが自動的に残りの席に内蔵ボットを追加
```

### 仕組み

1. **ゲーム作成**: `1013` メッセージでゲームを作成
2. **席の確保**: Pythonボットが席に座る
3. **自動配置**: サーバーが空席を検出し、内蔵ボットに参加を要求（`1023` メッセージを送信）
4. **ゲーム開始**: 全席が埋まるとゲーム開始

### 重要ポイント

- `num_robots` パラメータは、何体のボットが必要かを**記録する目的**で使用
- サーバーは利用可能な内蔵ボットがある限り、自動的に空席に配置
- クライアント側でボット追加の特別な処理は**不要**

## 質問2: ボットが有効な座席に座り、内蔵ボットの座席を奪わない方法

### 答え: 自動座席割り当てを使用する

座席番号に `-1` を指定すると、サーバーが自動的に空いている席を割り当てます。

### 実装方法

現在のコード（問題文）:
```python
def sit_down(self, game_name: str):
    """席に座るリクエスト (1012)"""
    msg = f"1012|{game_name},-,0,true"  # 常に0を指定（問題あり）
    write_java_utf(self.sock, msg)
```

**推奨される改善版**:
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

### 使用方法

```python
# メッセージハンドラで自動割り当てを使用
elif msg_type == "1013": # JOINGAME 誰かがゲームに入室した
    args = parsed.get("args", [])
    if len(args) >= 1:
        name = args[0]
        
        if name == self.nickname and self.player_id == -1:
            print("🚀 Join complete. Requesting auto-seat assignment...")
            # -1を指定して自動割り当て
            self.sit_down(self.current_game, preferred_seat=-1)
```

### なぜこれが機能するか

1. **タイミング**: Pythonボットがゲーム作成直後に参加し、最初に席を確保
2. **自動割り当て**: `-1` を使用することで、サーバーが利用可能な席を選択
3. **競合回避**: サーバーが既に座っている席を割り当てることはない
4. **ボット配置**: Pythonボットが席を確保した後、サーバーが残りの席に内蔵ボットを配置

## 質問3: 内蔵ボットの種類について

### 答え: 2種類の戦略があります

JSettlersには以下の2種類の内蔵ボット戦略があります：

### 1. FAST_STRATEGY（高速戦略）

**特徴**:
- より高速だが、よりシンプルなAI
- 基本的な判断で素早く行動
- 単純な建設と交易のみ

**割合**: 約70%の内蔵ボット

**名前の例**:
- `dumb01`
- `dumb02`
- `dumb03`
- （最大30体まで）

**実装**:
```java
// src/main/java/soc/robot/SOCRobotDM.java
public static final int FAST_STRATEGY = 1;
```

**戦略の概要**:
- 資源を取得したら建設可能なものをすぐに建設
- 複雑な計算を行わず、単純なルールベースで判断
- ターンを早く終わらせる

### 2. SMART_STRATEGY（スマート戦略）

**特徴**:
- より賢いが、計算に時間がかかる
- Win Game ETA（勝利までの推定ターン数）を計算
- より複雑な判断を行う

**割合**: 約30%の内蔵ボット

**名前の例**:
- `robot 1`
- `robot 2`
- `robot 3`
- （最大30体まで）

**実装**:
```java
// src/main/java/soc/robot/SOCRobotDM.java
public static final int SMART_STRATEGY = 0;
```

**戦略の概要**:
- Win Game ETA（WinGameETA）を計算し、最も効率的な建設計画を立てる
- 他のプレイヤーの戦略を考慮
- 開発カードや特殊な戦略を活用
- より長い時間をかけて最適な手を選択

### サーバー設定

サーバー起動時に内蔵ボットを有効化:

```bash
java -jar JSettlersServer.jar \
    -Djsettlers.bots.cookie=your_cookie \
    -Djsettlers.startrobots=7
```

オプション:
- `-Djsettlers.bots.cookie`: ボット認証用のクッキー
- `-Djsettlers.startrobots`: 起動するボット数（推奨: 7以上）

### ボットの選択方法

サーバーは以下のロジックでボットを選択します：

```java
// src/main/java/soc/server/SOCServer.java
// 30% will be "smart" robots, the other 70% will be "fast" robots.
final int fast30 = (int) (rcount * 0.70f);  // 70% FAST
boolean loadSuccess = setupLocalRobots(fast30, rcount - fast30);  // 30% SMART
```

### ボットの割り当て

ゲーム開始時、サーバーは利用可能なボットからランダムに選択し、適切な比率（70% FAST、30% SMART）で配置します。

### クライアント側での制御

**重要**: クライアント側からボットの種類を指定することは**できません**。サーバーが自動的に適切な比率で選択します。

## まとめ

### 必要な変更点

問題文のコードに対して、以下の変更を推奨します：

1. **`sit_down()` メソッドの改善**
   ```python
   def sit_down(self, game_name: str, preferred_seat: int = -1):
       msg = f"1012|{game_name},-,{preferred_seat},true"
       write_java_utf(self.sock, msg)
   ```

2. **メッセージハンドラで自動割り当てを使用**
   ```python
   if name == self.nickname and self.player_id == -1:
       self.sit_down(self.current_game, preferred_seat=-1)
   ```

3. **`player_id` の初期化**
   ```python
   def __init__(self, ...):
       self.player_id = -1  # 初期化
   ```

### 内蔵ボットの追加

- **手動での操作は不要**: サーバーが自動的に追加
- **`num_robots` パラメータ**: 記録目的で使用可能だが、サーバーの動作に影響しない
- **重要**: サーバー起動時に内蔵ボットを有効化する必要がある

### ボットの種類

- **FAST_STRATEGY** (70%): `dumb01`, `dumb02`, ... - 高速で単純
- **SMART_STRATEGY** (30%): `robot 1`, `robot 2`, ... - 賢いが遅い
- **選択**: サーバーが自動的に適切な比率で選択

### 参考資料

- `INTERNAL_BOTS_GUIDE.md` - 英語の概要
- `INTERNAL_BOTS.ja.md` - 日本語の詳細ガイド
- `IMPLEMENTING_INTERNAL_BOTS.ja.md` - 実装ガイド
- `example_internal_bots.py` - 使用例

これらのドキュメントに、より詳細な情報と実装例が記載されています。
