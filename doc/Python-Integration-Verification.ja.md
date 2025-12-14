# Pythonとの連携確認ガイド

このガイドでは、JSettlersとPythonの連携が正常に動作しているか確認する方法を、段階的に丁寧に説明します。

## 目次

1. [Python環境の確認](#1-python環境の確認)
2. [依存パッケージの確認](#2-依存パッケージの確認)
3. [JSettlersのビルド確認](#3-jsettlersのビルド確認)
4. [Pythonテストの実行](#4-pythonテストの実行)
5. [Pythonボットの接続確認](#5-pythonボットの接続確認)
6. [ゲームプレイの確認](#6-ゲームプレイの確認)
7. [トラブルシューティング](#7-トラブルシューティング)

---

## 1. Python環境の確認

### 1.1 Pythonのバージョン確認

まず、Pythonがインストールされており、適切なバージョンであることを確認します。

```bash
python3 --version
```

**期待される出力:**
```
Python 3.7.x 以上
```

または

```bash
python --version
```

**期待される出力:**
```
Python 3.7.x 以上
```

**説明:** JSettlersのPython連携には Python 3.7 以上が必要です。バージョンが古い場合は、Pythonをアップグレードしてください。

### 1.2 Pythonの実行パス確認

Pythonの実行パスを確認します。

```bash
which python3
```

**期待される出力例:**
```
/usr/bin/python3
```

または

```bash
which python
```

**期待される出力例:**
```
/usr/local/bin/python
```

**説明:** これにより、システムがどのPythonインタープリタを使用しているかを確認できます。

---

## 2. 依存パッケージの確認

### 2.1 pipの確認

Pythonパッケージマネージャー（pip）が正常に動作するか確認します。

```bash
pip3 --version
```

または

```bash
pip --version
```

**期待される出力例:**
```
pip 21.0 from /usr/local/lib/python3.9/site-packages/pip (python 3.9)
```

### 2.2 必要なパッケージのインストール確認

Pythonボットに必要なパッケージがインストールされているか確認します。

```bash
cd examples/python-bot
pip3 list | grep -E "(numpy|torch)"
```

**期待される出力例:**
```
numpy      1.21.0
torch      1.9.0
```

**もしパッケージがインストールされていない場合:**

```bash
pip3 install -r requirements.txt
```

**説明:** `numpy`はPythonボットの基本動作に必要です。`torch`はPyTorchベースのエージェントを使用する場合にのみ必要です。

### 2.3 パッケージのインポート確認

Pythonパッケージが正常にインポートできるか確認します。

```bash
python3 -c "import numpy; print('numpy version:', numpy.__version__)"
```

**期待される出力例:**
```
numpy version: 1.21.0
```

PyTorchを使用する場合:

```bash
python3 -c "import torch; print('torch version:', torch.__version__)"
```

**期待される出力例:**
```
torch version: 1.9.0
```

**説明:** インポートエラーが発生する場合、パッケージが正しくインストールされていません。

---

## 3. JSettlersのビルド確認

### 3.1 Gradleのバージョン確認

```bash
gradle --version
```

**期待される出力例:**
```
Gradle 7.x
```

**説明:** JSettlersのビルドには Gradle 6.9.x または 7.x が必要です。

### 3.2 JSettlersのビルド

プロジェクトのルートディレクトリで以下を実行します。

```bash
cd /home/runner/work/private-jsettler/private-jsettler
gradle assemble
```

**期待される出力:**
```
BUILD SUCCESSFUL
```

**説明:** ビルドが成功すると、`build/libs/`ディレクトリに JARファイルが生成されます。

### 3.3 ビルド成果物の確認

```bash
ls -lh build/libs/JSettlers*.jar
```

**期待される出力例:**
```
-rw-r--r-- 1 user user 5.2M Dec 14 10:00 build/libs/JSettlers-2.5.00.jar
```

**説明:** JARファイルが存在し、適切なサイズ（数MB）であることを確認します。

---

## 4. Pythonテストの実行

JSettlersには、Python連携が正常に動作するかを確認するためのテストスイートが含まれています。

### 4.1 環境変数の設定

Pythonテストを実行する前に、CLASSPATHを設定します（Gradleが自動的に行います）。

### 4.2 基本的なPythonテストの実行

```bash
cd /home/runner/work/private-jsettler/private-jsettler
gradle testPython
```

**期待される出力:**
```
> Task :testPython

Ran X tests in X.XXXs

OK

BUILD SUCCESSFUL
```

**説明:** このコマンドは、`src/test/python/`ディレクトリ内のすべてのPythonユニットテストを実行します。

### 4.3 拡張Pythonテストの実行

```bash
gradle extraTestPython
```

**期待される出力:**
```
> Task :extraTestPython

test_startup_params (server.test_startup_params.TestStartupParams) ... ok
...

Ran X tests in X.XXXs

OK

BUILD SUCCESSFUL
```

**説明:** このコマンドは、`src/extraTest/python/`ディレクトリ内の追加テストを実行します。

### 4.4 特定のテストファイルを個別に実行

環境変数を設定してから、特定のテストを実行できます。

```bash
# まずJARファイルのパスを確認
export CLASSPATH="$(pwd)/build/libs/JSettlers-*.jar"

# 特定のテストを実行
cd src/test/python
python3 -m unittest test_0_env
```

**期待される出力:**
```
.
----------------------------------------------------------------------
Ran 1 test in 0.001s

OK
```

**説明:** `test_0_env.py`は、Python環境が正しく設定されているかを確認するテストです。

### 4.5 詳細なテスト出力の表示

より詳細な情報を表示するには、`--verbose`オプションを使用します。

```bash
cd src/test/python
python3 -m unittest discover --verbose
```

**期待される出力例:**
```
test_env (test_0_env.test_0_env) ... ok
test_json_syntax (server.savegame.test_json_artifacts_syntax.TestJsonSyntax) ... ok
...

----------------------------------------------------------------------
Ran X tests in X.XXXs

OK
```

---

## 5. Pythonボットの接続確認

実際にPythonボットがJSettlersサーバーに接続できるかを確認します。

### 5.1 JSettlersサーバーの起動

**ターミナル1** で以下を実行します：

```bash
cd /home/runner/work/private-jsettler/private-jsettler
java -Djsettlers.bots.showcookie=Y -jar build/libs/JSettlers-*.jar 8880
```

**期待される出力:**
```
Robot cookie: abc123def456
...
Server listening on port 8880
```

**重要:** 表示された**ロボットクッキー**（例: `abc123def456`）をメモしてください。次のステップで使用します。

**説明:** `-Djsettlers.bots.showcookie=Y`オプションを使用すると、ボットが接続する際に必要なセキュリティクッキーが表示されます。

### 5.2 Pythonボットの起動（シンプルモード）

**ターミナル2** で以下を実行します：

```bash
cd /home/runner/work/private-jsettler/private-jsettler/examples/python-bot
python3 main.py localhost 8880 testbot <クッキー> --simple
```

`<クッキー>`の部分を、ステップ5.1で表示されたクッキーに置き換えてください。

**例:**
```bash
python3 main.py localhost 8880 testbot abc123def456 --simple
```

**期待される出力:**
```
🤖 JSettlers Python Bot
==================================================
Host: localhost:8880
Nickname: testbot

🧠 Loading agent...
🤖 Simple heuristic agent initialized
   This agent uses rule-based decisions (no ML model required)
✓ Using simple heuristic agent (no ML model required)
✓ Agent ready

🤖 Connecting to localhost:8880...
✓ Connected
🔐 Authenticating as robot...
→ VERSION:version=2.5.00|versionint=2500|locale=en_US|cliFeats=;6pl;sb;
→ IMAROBOT:nickname=testbot|cookie=abc123def456|rbclass=python.bot.PyTorchAgent
✓ Authenticated
⏳ Waiting for messages...

← UPDATEROBOTPARAMS:...
✓ Robot parameters updated
```

**説明:** 
- `localhost` - サーバーのホスト名（同じマシンの場合）
- `8880` - サーバーのポート番号
- `testbot` - ボットの名前
- `abc123def456` - ロボットクッキー
- `--simple` - シンプルなヒューリスティックエージェントを使用

### 5.3 接続確認のチェックポイント

**サーバー側（ターミナル1）で確認すべき出力:**
```
Robot connection from /127.0.0.1
Robot testbot authenticated
```

**ボット側（ターミナル2）で確認すべき出力:**
- ✓ Connected
- ✓ Authenticated
- ✓ Robot parameters updated

**説明:** 両方のターミナルで上記のメッセージが表示されれば、Pythonボットの接続は成功です。

---

## 6. ゲームプレイの確認

実際にPythonボットがゲームに参加してプレイできるかを確認します。

### 6.1 JSettlersクライアントの起動

**ターミナル3** で以下を実行します：

```bash
cd /home/runner/work/private-jsettler/private-jsettler
java -jar build/libs/JSettlers-*.jar localhost 8880
```

**説明:** GUIクライアントが起動し、サーバーへの接続ダイアログが表示されます。

### 6.2 ゲームの作成

クライアントで以下の手順を実行します：

1. **ニックネーム** を入力（例: "Player1"）
2. **接続** ボタンをクリック
3. **新しいゲームを作成** をクリック
4. **ゲーム名** を入力（例: "test"）
5. **プレイヤーを追加** で `testbot`（ステップ5.2で起動したボット）を選択
6. 必要に応じて他のボットも追加
7. **ゲーム開始** をクリック

### 6.3 ボットの参加確認

**ボット側（ターミナル2）で期待される出力:**
```
← BOTJOINGAMEREQUEST:game=test
📥 Joining game: test
→ JOINGAME:nickname=testbot|password=|host=-|game=test
← JOINGAMEAUTH:game=test|playerNumber=1
✓ Joined game: test as player 1
← GAMESTATE:game=test|state=0
← STARTGAME:game=test
...
```

**説明:** ボットがゲームに参加し、プレイヤー番号が割り当てられます。

### 6.4 ボットのアクション確認

ゲームが開始されると、ボットのターンで以下のようなログが表示されます：

```
← GAMESTATE:game=test|state=15
🎲 My turn - making decision...
🧠 Agent predicted action: 0
→ ROLLDICE:game=test
← DICERESULT:game=test|param=7
← GAMESTATE:game=test|state=20
🎮 Taking action in play phase...
→ ENDTURN:game=test
```

**説明:**
- `state=15` - サイコロを振る段階
- `ROLLDICE` - サイコロを振るアクション
- `DICERESULT` - サイコロの結果
- `state=20` - アクションフェーズ
- `ENDTURN` - ターンを終了

### 6.5 ゲーム完了の確認

ボットが正常にゲームをプレイし、ターンを繰り返すことを確認します。

**チェックポイント:**
- ✓ ボットが自動的にサイコロを振る
- ✓ ボットが資源を受け取る
- ✓ ボットがターンを終了する
- ✓ ボットが盗賊や交易に対応する
- ✓ ゲームが正常に進行する

---

## 7. トラブルシューティング

### 7.1 Pythonが見つからない

**エラー:**
```
python3: command not found
```

**解決方法:**

1. Pythonのインストール状況を確認：
```bash
which python python3
```

2. Pythonをインストール（Ubuntu/Debian）：
```bash
sudo apt-get update
sudo apt-get install python3 python3-pip
```

3. Pythonをインストール（macOS）：
```bash
brew install python3
```

### 7.2 必要なパッケージがインストールされていない

**エラー:**
```
ModuleNotFoundError: No module named 'numpy'
```

**解決方法:**

```bash
cd examples/python-bot
pip3 install -r requirements.txt
```

または個別にインストール：

```bash
pip3 install numpy torch
```

### 7.3 JSettlersのビルドエラー

**エラー:**
```
BUILD FAILED
```

**解決方法:**

1. Javaのバージョンを確認（JDK 8以上が必要）：
```bash
java -version
```

2. Gradleのバージョンを確認（6.9.x または 7.x が必要）：
```bash
gradle --version
```

3. クリーンビルドを試す：
```bash
gradle clean build
```

### 7.4 Pythonテストが失敗する

**エラー:**
```
FAILED (errors=1)
```

**解決方法:**

1. CLASSPATHが正しく設定されているか確認：
```bash
echo $CLASSPATH
```

2. まずJSettlersをビルド：
```bash
gradle assemble
```

3. 詳細なエラー情報を表示：
```bash
gradle testPython --info
```

### 7.5 ボットがサーバーに接続できない

**エラー:**
```
ConnectionRefusedError: [Errno 111] Connection refused
```

**解決方法:**

1. サーバーが起動しているか確認：
```bash
ps aux | grep JSettlers
```

2. ポートが開いているか確認：
```bash
netstat -an | grep 8880
```

または

```bash
lsof -i :8880
```

3. ファイアウォールの設定を確認：
```bash
sudo ufw status
```

4. サーバーを再起動：
```bash
java -Djsettlers.bots.showcookie=Y -jar build/libs/JSettlers-*.jar 8880
```

### 7.6 ボットの認証エラー

**エラー:**
```
Authentication failed: Invalid robot cookie
```

**解決方法:**

1. サーバー起動時に表示されたクッキーを正確にコピー
2. クッキーに余分なスペースが含まれていないか確認
3. サーバーを再起動して新しいクッキーを取得

### 7.7 ボットがゲームに参加しない

**問題:** ボットが接続されているが、ゲームに参加できない

**解決方法:**

1. ボットのログを確認：
   - `BOTJOINGAMEREQUEST`メッセージが届いているか
   - `JOINGAMEAUTH`で認証されているか

2. サーバーログでエラーを確認：
```bash
# サーバーを詳細ログで起動
java -Djsettlers.debug.traffic=Y \
     -Djsettlers.bots.showcookie=Y \
     -jar build/libs/JSettlers-*.jar 8880
```

3. ボット名が正しいか確認：
   - クライアントで選択したボット名とコマンドラインで指定した名前が一致しているか

### 7.8 ボットがアクションを実行しない

**問題:** ボットがターンで何もしない、またはタイムアウトする

**解決方法:**

1. ボットのログで例外が発生していないか確認

2. ゲーム状態が正しく更新されているか確認：
```python
# jsettlers_bot.pyに追加
print(f"Game state: {self.game_state.game_state}")
print(f"My turn: {self.is_my_turn()}")
```

3. エージェントが正常に動作しているか確認：
```python
# agent.pyに追加
print(f"Observation shape: {observation.shape}")
print(f"Predicted action: {action}")
```

### 7.9 PyTorchモデルのロードエラー

**エラー:**
```
RuntimeError: Error loading model
```

**解決方法:**

1. モデルファイルが存在するか確認：
```bash
ls -lh /path/to/model.pth
```

2. PyTorchのバージョンを確認：
```bash
python3 -c "import torch; print(torch.__version__)"
```

3. モデルが正しく保存されているか確認：
```python
import torch
model = torch.load('model.pth', map_location='cpu')
print(type(model))
```

---

## まとめ

このガイドでは、JSettlersとPythonの連携を確認するための以下の手順を説明しました：

1. ✅ **Python環境の確認** - バージョンとインストール状態
2. ✅ **依存パッケージの確認** - numpy、torchなどのインストール
3. ✅ **JSettlersのビルド確認** - Gradleでのビルド成功
4. ✅ **Pythonテストの実行** - `testPython`と`extraTestPython`
5. ✅ **Pythonボットの接続確認** - サーバーへの接続と認証
6. ✅ **ゲームプレイの確認** - 実際のゲームでの動作確認
7. ✅ **トラブルシューティング** - よくある問題と解決方法

### 推奨される確認手順

新しい環境でPython連携を確認する場合、以下の順序で実行することをお勧めします：

```bash
# 1. Python環境確認
python3 --version
pip3 --version

# 2. 依存パッケージインストール
cd examples/python-bot
pip3 install -r requirements.txt

# 3. JSettlersビルド
cd /home/runner/work/private-jsettler/private-jsettler
gradle assemble

# 4. Pythonテスト実行
gradle testPython

# 5. サーバー起動（ターミナル1）
java -Djsettlers.bots.showcookie=Y -jar build/libs/JSettlers-*.jar 8880

# 6. ボット起動（ターミナル2）
cd examples/python-bot
python3 main.py localhost 8880 testbot <クッキー> --simple

# 7. クライアント起動とゲーム作成（ターミナル3）
java -jar build/libs/JSettlers-*.jar localhost 8880
```

### 関連ドキュメント

より詳細な情報は以下を参照してください：

- **[Python Bot Quick Start (Japanese)](../examples/python-bot/QUICKSTART.ja.md)** - Pythonボットの基本的な使い方
- **[Python Bot Guide (Japanese)](Python-Bot-Guide.ja.md)** - Pythonボットの完全ガイド
- **[Python Bot Quick Reference (Japanese)](Python-Bot-Quick-Reference.ja.md)** - クイックリファレンス
- **[Readme.developer.md](Readme.developer.md)** - 開発者向けドキュメント

### サポート

問題が解決しない場合や、さらにサポートが必要な場合：

- JSettlersのGitHubリポジトリでIssueを作成
- `doc/Message-Sequences-for-Game-Actions.md`でメッセージプロトコルの詳細を確認
- サーバーログとボットログを確認して、エラーメッセージを特定

頑張ってください！🎲🤖
