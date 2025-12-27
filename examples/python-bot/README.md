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

**カスタマイズ用テンプレート:**
- `agent_template.py` - エージェントカスタマイズ用テンプレート
- `game_state_template.py` - ゲーム状態カスタマイズ用テンプレート

## カスタマイズ

### オプション1: 既存ファイルを直接編集

#### Observation形式

`game_state.py`の`to_observation()`メソッドを編集して、エージェントの期待する形式に合わせてください。

#### Action空間

`jsettlers_bot.py`の`execute_action()`メソッドを編集して、エージェントのアクション空間に合わせてください。

### オプション2: テンプレートを使用（推奨）

1. **`agent_template.py`をコピー**して`agent.py`にリネーム
2. **`game_state_template.py`をコピー**して`game_state.py`にリネーム
3. TODOマークの部分をあなたのエージェントの形式に合わせて編集

テンプレートには以下が含まれます：
- 複数のモデルロード方法の例
- 様々なObservation形式のパターン
- アクションマスクのサポート
- 詳細なコメントとヒント

## カスタマイズ例

詳細な例は以下を参照：
- [Agent Customization Examples (Japanese)](../../doc/Agent-Customization-Examples.ja.md) - 一般的なパターンと例
- [Python Bot Guide (Japanese)](../../doc/Python-Bot-Guide.ja.md) - 完全なガイド
- [Python Bot Quick Reference (Japanese)](../../doc/Python-Bot-Quick-Reference.ja.md) - クイックリファレンス

## デバッグ

詳細なログを表示：

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## トラブルシューティング

### Observation形状の不一致

```python
# game_state.pyのto_observation()に追加
observation = self.to_observation()
print(f"Observation shape: {observation.shape}")
```

### モデルロードエラー

```python
# agent.pyで確認
import torch
print(f"PyTorch version: {torch.__version__}")
```

### アクションが実行されない

```python
# jsettlers_bot.pyのexecute_action()に追加
print(f"Executing action: {action}, type: {type(action)}")
```

## 内蔵ボットの使用

JSettlersの内蔵ボットと一緒にプレイする方法については、以下のドキュメントを参照してください：

- **[INTERNAL_BOTS_GUIDE.md](INTERNAL_BOTS_GUIDE.md)** - 内蔵ボットシステムの概要（英語）
- **[INTERNAL_BOTS.ja.md](INTERNAL_BOTS.ja.md)** - 内蔵ボットシステムの詳細（日本語）
- **[IMPLEMENTING_INTERNAL_BOTS.ja.md](IMPLEMENTING_INTERNAL_BOTS.ja.md)** - 実装ガイド（日本語）
- **[example_internal_bots.py](example_internal_bots.py)** - 使用例

### 内蔵ボットの種類

- **FAST_STRATEGY** (70%): `dumb01`, `dumb02`, ... - 高速だが単純
- **SMART_STRATEGY** (30%): `robot 1`, `robot 2`, ... - 賢いが遅い

### 使用例

```python
bot = JSettlersBot(host, port, nickname, cookie, agent)
bot.run(
    game_name="MyGame",
    mode="create",
    num_robots=3,  # サーバーが自動的に3体の内蔵ボットを追加
    num_games=1
)
```

## 詳細ドキュメント

詳細は [Python Bot Guide (Japanese)](../../doc/Python-Bot-Guide.ja.md) を参照してください。
