# クイックスタート: Pythonボットの実行方法

このガイドでは、JSettlersサーバーに接続してボットを実行する手順を説明します。

## 前提条件

- Python 3.7以上
- JSettlersサーバー（このリポジトリ）

## ステップ1: JSettlersサーバーを起動

新しいターミナルを開いて、以下のコマンドを実行してください：

```bash
cd /home/runner/work/private-jsettler/private-jsettler
java -Djsettlers.bots.showcookie=Y -jar build/libs/JSettlers-*.jar 8880
```

**注意**: もしビルドファイルがない場合は、まずビルドしてください：
```bash
gradle assemble
```

サーバーが起動すると、以下のようなメッセージが表示されます：

```
Robot cookie: abc123def456
Server listening on port 8880
```

**重要**: この `abc123def456` のようなクッキー文字列をメモしてください。次のステップで使用します。

## ステップ2: 必要なパッケージをインストール

ボットのディレクトリに移動して、numpyをインストールします：

```bash
cd examples/python-bot
pip install numpy
```

**注意**: シンプルなヒューリスティックエージェントを使用する場合、PyTorchは不要です。

## ステップ3: ボットを実行

### オプションA: シンプルなヒューリスティックエージェント（推奨・すぐ動作確認）

```bash
python main.py localhost 8880 mybot <クッキー> --simple
```

例：
```bash
python main.py localhost 8880 testbot abc123def456 --simple
```

### オプションB: 改良版ヒューリスティックエージェント

```bash
python main.py localhost 8880 mybot <クッキー> --improved
```

### オプションC: PyTorchモデルを使用（将来的に）

```bash
pip install torch
python main.py localhost 8880 mybot <クッキー> model.pth
```

## ステップ4: ゲームを作成して対戦

ボットが正常に接続されると、以下のようなメッセージが表示されます：

```
🤖 JSettlers Python Bot
==================================================
Host: localhost:8880
Nickname: mybot

🧠 Loading agent...
🤖 Simple heuristic agent initialized
   This agent uses rule-based decisions (no ML model required)
✓ Using simple heuristic agent (no ML model required)
✓ Agent ready

🤖 Connecting to localhost:8880...
✓ Connected
🔐 Authenticating as robot...
→ VERSION:version=2.5.00|versionint=2500|locale=en_US|cliFeats=;6pl;sb;
→ IMAROBOT:nickname=mybot|cookie=abc123def456|rbclass=python.bot.PyTorchAgent
✓ Authenticated
⏳ Waiting for messages...
```

次に、**別のターミナル**でJSettlersクライアントを起動します：

```bash
java -jar build/libs/JSettlers-*.jar localhost 8880
```

クライアントが起動したら：

1. **新しいゲームを作成**をクリック
2. ゲーム名を入力（例: "test"）
3. **ボットを追加**で `mybot`（または指定したボット名）を選択
4. 必要に応じて他のプレイヤーやボットを追加
5. **ゲーム開始**をクリック

ボットがゲームに参加して、ヒューリスティックに基づいてプレイします！

## よくある問題と解決方法

### 1. `Connection refused` エラー

**問題**: ボットがサーバーに接続できない

**解決方法**:
- JSettlersサーバーが起動していることを確認
- ポート番号が正しいか確認（デフォルト: 8880）
- ファイアウォールの設定を確認

### 2. `Invalid robot cookie` エラー

**問題**: クッキーが正しくない

**解決方法**:
- サーバー起動時に表示されたクッキーを正確にコピー
- サーバーを再起動して新しいクッキーを取得

### 3. `ModuleNotFoundError: No module named 'numpy'`

**問題**: numpyがインストールされていない

**解決方法**:
```bash
pip install numpy
```

### 4. ボットがゲームに参加しない

**問題**: ボットの名前が見つからない

**解決方法**:
- ボットが正常に接続されているか確認（ログを確認）
- サーバーログでエラーメッセージを確認
- ボット名が正しいか確認

## ボットの動作確認

ボットが正常に動作している場合：

1. サーバーログに「Robot mybot connected」のようなメッセージが表示される
2. ボットのターミナルにゲームメッセージが表示される：
   ```
   ← BOTJOINGAMEREQUEST:game=test
   📥 Joining game: test
   → JOINGAME:nickname=mybot|password=|host=-|game=test
   ← JOINGAMEAUTH:game=test|playerNumber=1
   ✓ Joined game: test as player 1
   ```

3. ボットのターンになると、自動的にアクション（サイコロを振る、建設など）を実行

## ヒューリスティックエージェントの動作

### SimpleHeuristicAgent（デフォルト）
- 常にサイコロを振る
- シンプルで安定した動作

### ImprovedHeuristicAgent（`--improved`オプション）
- 資源状況を確認
- 可能であれば道路や集落を建設
- より積極的な戦略

## 次のステップ

ボットが正常に動作することを確認したら：

1. **`game_state.py`をカスタマイズ** - Observation形式を変更
2. **`simple_agent.py`を拡張** - より高度なヒューリスティックを実装
3. **PyTorchモデルを統合** - 学習済みモデルを使用

詳細は以下を参照：
- [Python Bot Guide](../../doc/Python-Bot-Guide.ja.md) - 完全ガイド
- [Python Bot Quick Reference](../../doc/Python-Bot-Quick-Reference.ja.md) - クイックリファレンス

## トラブルシューティングのヒント

### デバッグモード

より詳細なログを表示するには、`jsettlers_bot.py`に以下を追加：

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### サーバーのトラフィックを確認

サーバー側でメッセージを確認：

```bash
java -Djsettlers.debug.traffic=Y \
     -Djsettlers.bots.showcookie=Y \
     -jar build/libs/JSettlers-*.jar 8880
```

## サポート

問題が解決しない場合：
- JSettlersのドキュメント: `doc/Readme.developer.md`
- メッセージプロトコル: `doc/Message-Sequences-for-Game-Actions.md`

頑張ってください！🎲🤖
