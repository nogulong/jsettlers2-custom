# クイックリファレンス: PythonボットでPyTorchエージェントを評価

## 最短手順（5ステップ）

### 1. JSettlersサーバーを起動

```bash
java -Djsettlers.bots.showcookie=Y -jar JSettlers.jar 8880
```

クッキーをメモ（例: `abc123def456`）

### 2. Pythonボットをダウンロード

```bash
cd examples/python-bot
pip install -r requirements.txt
```

### 3. エージェントをカスタマイズ

#### Observation形式を調整（`game_state.py`）

```python
def to_observation(self) -> np.ndarray:
    # エージェントの期待する形式に変更
    # 例: ボード状態、資源、プレイヤー情報など
    return observation  # あなたのObservation形式
```

#### Action空間を調整（`jsettlers_bot.py`）

```python
def execute_action(self, action: int):
    # エージェントのアクション定義に従う
    if action == 0:
        self.roll_dice()
    elif action == 1:
        self.build_road(coord)
    # ...
```

### 4. ボットを実行

```bash
python main.py localhost 8880 mybot abc123def456 /path/to/model.pth
```

### 5. ゲームを作成

別のターミナルでJSettlersクライアントを起動し、ボット入りゲームを作成。

## 主要なファイル

| ファイル | 役割 | カスタマイズ |
|---------|------|-------------|
| `game_state.py` | ゲーム状態 → Observation変換 | **必須** - `to_observation()`を実装 |
| `jsettlers_bot.py` | JSettlers通信とアクション実行 | **推奨** - `execute_action()`を実装 |
| `agent.py` | PyTorchモデルのラッパー | **オプション** - モデルロード方法を変更 |
| `utils.py` | プロトコルユーティリティ | **変更不要** |
| `main.py` | エントリーポイント | **変更不要** |

## カスタマイズのポイント

### 1. Observation形式

エージェントが期待する入力形式に`to_observation()`を変更：

```python
def to_observation(self) -> np.ndarray:
    # 例: (board, resources, positions) を結合
    obs = np.concatenate([
        self.board_state,      # ボードの状態
        self.resource_vector,  # 自分の資源
        self.piece_positions,  # 駒の位置
        self.opponent_info     # 相手の情報
    ])
    return obs
```

### 2. メッセージ処理の追加

より詳細な情報が必要な場合、`game_state.py`の`update_from_message()`に処理を追加：

```python
def update_from_message(self, msg_type: str, params: dict):
    if msg_type == "BOARDLAYOUT":
        # ボード配置を解析
        pass
    elif msg_type == "DEVCARDACTION":
        # 開発カードの使用を記録
        pass
    # ...
```

### 3. アクションの実装

エージェントが出力するアクションに対応する処理を`execute_action()`に追加：

```python
def execute_action(self, action: int):
    # アクション0-9: サイコロを振る、カードを買う、etc.
    # アクション10-99: 特定の座標に建設、etc.
    if action < 10:
        # 単純なアクション
        self.simple_actions[action]()
    else:
        # 座標が必要なアクション
        coord = self.determine_coordinate(action)
        self.build_piece(action_type, coord)
```

## トラブルシューティング

### Q: モデルファイルが見つからない

A: パスを絶対パスで指定してください：
```bash
python main.py localhost 8880 mybot cookie /home/user/model.pth
```

### Q: Observationの形状が合わない

A: `game_state.py`の`to_observation()`で正しい形状を返すように調整してください。

### Q: アクションが実行されない

A: `jsettlers_bot.py`の`execute_action()`に実装を追加してください。

### Q: ゲームメッセージが分からない

A: `print()`でメッセージをログ出力し、`doc/Message-Sequences-for-Game-Actions.md`を参照してください。

## デバッグ

詳細なログを表示：

```python
# main.pyの先頭に追加
import logging
logging.basicConfig(level=logging.DEBUG)
```

受信メッセージを確認：

```python
# jsettlers_bot.pyのhandle_message()で
print(f"Received: {msg_type} - {parsed}")
```

## 参考資料

- 詳細ガイド: `doc/Python-Bot-Guide.ja.md`
- メッセージプロトコル: `doc/Message-Sequences-for-Game-Actions.md`
- JSettlers開発ドキュメント: `doc/Readme.developer.md`

## まとめ

1. **Observation変換を実装** - `game_state.py`
2. **Action実行を実装** - `jsettlers_bot.py`
3. **モデルをロード** - `agent.py`
4. **ボットを実行** - `python main.py ...`

必要最小限のカスタマイズで、PyTorchエージェントをJSettlersで評価できます。
