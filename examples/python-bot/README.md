# JSettlers Python Bot Example

PyTorchエージェントをJSettlersサーバーと対戦させるための完全な実装例です。

## 概要

このボットは：
- JSettlersサーバーに接続
- ゲームメッセージをObservationに変換
- PyTorchモデルでアクションを予測
- アクションをJSettlersに送信

## 必要なもの

```bash
pip install torch numpy
```

## 使い方

### 1. JSettlersサーバーを起動

```bash
java -Djsettlers.bots.showcookie=Y -jar ../../build/libs/JSettlers-*.jar 8880
```

クッキーをメモしてください（例: `abc123def456`）

### 2. ボットを実行

```bash
python main.py localhost 8880 mybot <cookie> model.pth
```

`model.pth`は学習済みのPyTorchモデルのパスです。

### 3. ゲームを作成

別のターミナルでJSettlersクライアントを起動し、ボットを含むゲームを作成します。

## ファイル構成

- `main.py` - メイン実行ファイル
- `jsettlers_bot.py` - JSettlersボットクライアント
- `game_state.py` - ゲーム状態管理
- `agent.py` - PyTorchエージェントラッパー
- `utils.py` - ユーティリティ関数
- `requirements.txt` - 依存パッケージ

## カスタマイズ

### Observation形式

`game_state.py`の`to_observation()`メソッドを編集して、エージェントの期待する形式に合わせてください。

### Action空間

`jsettlers_bot.py`の`execute_action()`メソッドを編集して、エージェントのアクション空間に合わせてください。

## デバッグ

詳細なログを表示するには：

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 詳細ドキュメント

詳細は [Python Bot Guide (Japanese)](../../doc/Python-Bot-Guide.ja.md) を参照してください。
