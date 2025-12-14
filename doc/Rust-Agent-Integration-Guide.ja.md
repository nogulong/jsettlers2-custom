# Rust製エージェントとJSettlersの対戦ガイド

このドキュメントでは、private-rust-catanで作成したRust製エージェントをJSettlersサーバーと対戦させる方法を説明します。

## 目次

1. [概要](#概要)
2. [アプローチの選択](#アプローチの選択)
3. [方法1: ネットワークプロトコルの実装（推奨）](#方法1-ネットワークプロトコルの実装推奨)
4. [方法2: Javaラッパーの作成](#方法2-javaラッパーの作成)
5. [サーバーの設定](#サーバーの設定)
6. [テストと実行](#テストと実行)
7. [トラブルシューティング](#トラブルシューティング)
8. [参考資料](#参考資料)

## 概要

JSettlersは、Settlers of Catan（カタンの開拓者たち）のJava実装で、クライアント・サーバーアーキテクチャを採用しています。AIロボットは、ネットワークメッセージを通じてサーバーと通信します。

Rust製エージェントを対戦させるには、主に2つのアプローチがあります：

1. **ネットワークプロトコルを直接実装する**（推奨）
2. **Javaラッパーを作成してRustコードを呼び出す**

## アプローチの選択

### 方法1: ネットワークプロトコルの実装（推奨）

**利点:**
- Rust単体で実装可能
- Java環境不要
- デプロイが簡単
- パフォーマンスが良い

**欠点:**
- ネットワークプロトコルの実装が必要
- メッセージフォーマットの理解が必要

**適している場合:**
- Rustの経験がある
- ネットワークプログラミングの経験がある
- 完全にRustで実装したい

### 方法2: Javaラッパーの作成

**利点:**
- JSettlersの既存クラスを活用できる
- ネットワーク層の実装不要
- デバッグが簡単

**欠点:**
- JNI（Java Native Interface）が必要
- Java/Rustの相互運用が複雑
- デプロイが難しい

**適している場合:**
- JNIの経験がある
- Rustのロジックのみ移植したい

## 方法1: ネットワークプロトコルの実装（推奨）

この方法では、RustでJSettlersのネットワークプロトコルを実装します。

### ステップ1: プロトコルの理解

JSettlersは、TCP上でUTF-8エンコードされた文字列ベースのメッセージを使用します。

#### メッセージフォーマット

- メッセージは `DataOutputStream.writeUTF(String)` で送信されます
- メッセージは `DataInputStream.readUTF()` で受信されます
- Java UTF形式：最初の2バイトが長さ（big-endian）、その後にUTF-8データ

#### 重要なメッセージタイプ

接続時に必要な基本メッセージ：

1. **SOCVersion** - クライアントバージョンを送信
2. **SOCImARobot** - ロボットとして識別（セキュリティクッキーが必要）
3. **SOCUpdateRobotParams** - サーバーからのロボットパラメータ
4. **SOCBotJoinGameRequest** - サーバーからのゲーム参加要求
5. **SOCJoinGame** - ゲームに参加
6. **SOCJoinGameAuth** - ゲーム参加の認証

ゲーム中の主要メッセージ：

- **SOCGameState** - ゲーム状態の変更
- **SOCTurn** - プレイヤーのターン
- **SOCDiceResult** - サイコロの結果
- **SOCPutPiece** - 駒の配置
- **SOCBuildRequest** - 建設リクエスト
- **SOCBuyDevCardRequest** - 開発カードの購入
- その他多数...

### ステップ2: Rustでの実装

#### 必要なクレート

```toml
[dependencies]
tokio = { version = "1", features = ["full"] }
bytes = "1"
```

#### Java UTF形式の読み書き

```rust
use std::io::{Read, Write, Error, ErrorKind};
use bytes::{BufMut, BytesMut};

/// Java DataOutputStream.writeUTF形式でStringを書き込む
pub fn write_java_utf<W: Write>(writer: &mut W, s: &str) -> std::io::Result<()> {
    let bytes = s.as_bytes();
    let len = bytes.len();
    
    if len > 65535 {
        return Err(Error::new(ErrorKind::InvalidInput, "String too long"));
    }
    
    // 長さを2バイトのbig-endianで書き込む
    writer.write_all(&(len as u16).to_be_bytes())?;
    // UTF-8データを書き込む
    writer.write_all(bytes)?;
    Ok(())
}

/// Java DataInputStream.readUTF形式でStringを読み取る
pub fn read_java_utf<R: Read>(reader: &mut R) -> std::io::Result<String> {
    // 長さを2バイトのbig-endianで読み取る
    let mut len_bytes = [0u8; 2];
    reader.read_exact(&mut len_bytes)?;
    let len = u16::from_be_bytes(len_bytes) as usize;
    
    // UTF-8データを読み取る
    let mut buf = vec![0u8; len];
    reader.read_exact(&mut buf)?;
    
    String::from_utf8(buf)
        .map_err(|e| Error::new(ErrorKind::InvalidData, e))
}
```

#### 基本的なクライアント構造

```rust
use tokio::net::TcpStream;
use tokio::io::{AsyncReadExt, AsyncWriteExt};

pub struct RustBotClient {
    stream: TcpStream,
    nickname: String,
    cookie: String,
    version: i32,
}

impl RustBotClient {
    pub async fn connect(
        host: &str,
        port: u16,
        nickname: String,
        cookie: String,
    ) -> std::io::Result<Self> {
        let stream = TcpStream::connect((host, port)).await?;
        
        Ok(Self {
            stream,
            nickname,
            cookie,
            version: 2500, // JSettlers v2.5.00
        })
    }
    
    pub async fn send_message(&mut self, msg: &str) -> std::io::Result<()> {
        // Java UTF形式で送信
        let bytes = msg.as_bytes();
        let len = bytes.len() as u16;
        
        self.stream.write_all(&len.to_be_bytes()).await?;
        self.stream.write_all(bytes).await?;
        self.stream.flush().await?;
        
        Ok(())
    }
    
    pub async fn receive_message(&mut self) -> std::io::Result<String> {
        let mut len_bytes = [0u8; 2];
        self.stream.read_exact(&mut len_bytes).await?;
        let len = u16::from_be_bytes(len_bytes) as usize;
        
        let mut buf = vec![0u8; len];
        self.stream.read_exact(&mut buf).await?;
        
        String::from_utf8(buf)
            .map_err(|e| std::io::Error::new(std::io::ErrorKind::InvalidData, e))
    }
    
    pub async fn authenticate(&mut self) -> std::io::Result<()> {
        // SOCVersionメッセージを送信
        let version_msg = format!("VERSION:version={},versionint={},locale=ja,cliFeatures=;6pl;sb;", 
                                  self.version, self.version);
        self.send_message(&version_msg).await?;
        
        // SOCImARobotメッセージを送信
        let robot_msg = format!("IMAROBOT:nickname={}|cookie={}|rbclass=rust.bot.RustBotBrain", 
                               self.nickname, self.cookie);
        self.send_message(&robot_msg).await?;
        
        Ok(())
    }
    
    pub async fn run(&mut self) -> std::io::Result<()> {
        // 認証
        self.authenticate().await?;
        
        // メインループ
        loop {
            let msg = self.receive_message().await?;
            println!("Received: {}", msg);
            
            // メッセージを処理
            self.handle_message(&msg).await?;
        }
    }
    
    async fn handle_message(&mut self, msg: &str) -> std::io::Result<()> {
        // メッセージタイプを判定して処理
        if msg.starts_with("UPDATEROBOTPARAMS:") {
            println!("Robot parameters updated");
        } else if msg.starts_with("BOTJOINGAMEREQUEST:") {
            // ゲーム参加要求を処理
            self.handle_join_request(msg).await?;
        } else if msg.starts_with("GAMESTATE:") {
            // ゲーム状態を処理
            self.handle_game_state(msg).await?;
        }
        // その他のメッセージタイプ...
        
        Ok(())
    }
    
    async fn handle_join_request(&mut self, msg: &str) -> std::io::Result<()> {
        // ゲーム名を抽出
        // 実際の実装では適切なパーシングが必要
        println!("Joining game...");
        Ok(())
    }
    
    async fn handle_game_state(&mut self, msg: &str) -> std::io::Result<()> {
        // ゲーム状態を処理
        println!("Game state changed");
        Ok(())
    }
}
```

### ステップ3: メッセージパーサーの実装

詳細なメッセージフォーマットは以下を参照：
- `src/main/java/soc/message/` ディレクトリのJavaクラス
- `doc/Message-Sequences-for-Game-Actions.md`

### ステップ4: ゲームロジックの統合

private-rust-catanのゲームロジックを、メッセージハンドラーに統合します。

```rust
// private-rust-catanのエージェントをインポート
use your_rust_catan::agent::YourAgent;

impl RustBotClient {
    async fn make_decision(&self, game_state: &GameState) -> Action {
        // private-rust-catanのエージェントを使用
        let agent = YourAgent::new();
        agent.decide_action(game_state)
    }
}
```

## 方法2: Javaラッパーの作成

この方法では、JSettlersのSOCRobotClientとSOCRobotBrainを拡張し、JNIを通じてRustコードを呼び出します。

### ステップ1: JNIバインディングの作成

#### Rustサイド

```toml
[dependencies]
jni = "0.21"
```

```rust
use jni::JNIEnv;
use jni::objects::{JClass, JString, JObject};
use jni::sys::{jstring, jint};

#[no_mangle]
pub extern "system" fn Java_soc_robot_rust_RustBotBrain_makeDecision(
    env: JNIEnv,
    _class: JClass,
    game_state: JString,
) -> jstring {
    // ゲーム状態を処理
    let state: String = env.get_string(game_state).expect("Couldn't get java string!").into();
    
    // Rustのエージェントで決定
    let decision = make_rust_decision(&state);
    
    // 結果を返す
    let output = env.new_string(decision).expect("Couldn't create java string!");
    output.into_inner()
}

fn make_rust_decision(state: &str) -> String {
    // private-rust-catanのエージェントを使用
    "decision".to_string()
}
```

#### Javaサイド

```java
package soc.robot.rust;

import soc.baseclient.ServerConnectInfo;
import soc.game.SOCGame;
import soc.robot.SOCRobotBrain;
import soc.robot.SOCRobotClient;
import soc.util.CappedQueue;
import soc.util.SOCRobotParameters;
import soc.message.SOCMessage;

public class RustBotClient extends SOCRobotClient {
    private static final String RBCLASSNAME = "soc.robot.rust.RustBotBrain";
    
    static {
        // Rustのネイティブライブラリをロード
        System.loadLibrary("rust_bot");
    }
    
    public RustBotClient(final ServerConnectInfo sci, final String nn, final String pw) {
        super(sci, nn, pw);
        rbclass = RBCLASSNAME;
    }
    
    @Override
    public SOCRobotBrain createBrain(
        final SOCRobotParameters params,
        final SOCGame ga,
        final CappedQueue<SOCMessage> mq
    ) {
        return new RustBotBrain(this, params, ga, mq);
    }
    
    public static void main(String[] args) {
        if (args.length < 5) {
            System.err.println("usage: java RustBotClient hostname port nickname password cookie");
            return;
        }
        
        RustBotClient cli = new RustBotClient(
            new ServerConnectInfo(args[0], Integer.parseInt(args[1]), args[4]),
            args[2],
            args[3]
        );
        cli.init();
    }
}
```

```java
package soc.robot.rust;

import soc.game.SOCGame;
import soc.robot.SOCRobotBrain;
import soc.robot.SOCRobotClient;
import soc.util.CappedQueue;
import soc.util.SOCRobotParameters;
import soc.message.SOCMessage;

public class RustBotBrain extends SOCRobotBrain {
    
    public RustBotBrain(
        SOCRobotClient rc,
        SOCRobotParameters params,
        SOCGame ga,
        CappedQueue<SOCMessage> mq
    ) {
        super(rc, params, ga, mq);
    }
    
    // Rustのネイティブメソッドを宣言
    private native String makeDecision(String gameState);
    
    @Override
    protected void planStuff() {
        // ゲーム状態を文字列にシリアライズ
        String gameStateJson = serializeGameState();
        
        // Rustのエージェントを呼び出し
        String decision = makeDecision(gameStateJson);
        
        // 決定を実行
        executeDecision(decision);
    }
    
    private String serializeGameState() {
        // ゲーム状態をJSON等にシリアライズ
        return "{}";
    }
    
    private void executeDecision(String decision) {
        // Rustから返された決定を実行
    }
}
```

### ステップ2: ビルド設定

#### Cargo.toml

```toml
[lib]
crate-type = ["cdylib"]

[dependencies]
jni = "0.21"
```

#### build.rs

```rust
fn main() {
    println!("cargo:rustc-link-search=native=/path/to/jdk/lib");
}
```

## サーバーの設定

### ステップ1: サーバーの起動

```bash
# セキュリティクッキーを表示してサーバーを起動
java -jar JSettlers.jar -Djsettlers.bots.showcookie=Y 8880
```

または、特定のクッキーを設定：

```bash
java -jar JSettlers.jar -Djsettlers.bots.cookie=myrobotcookie123 8880
```

### ステップ2: サーバープロパティの設定

`jsserver.properties` ファイルを作成：

```properties
# サードパーティボットの設定
jsettlers.bots.percent3p=100
jsettlers.bots.timeout.turn=30
jsettlers.bots.botgames.wait_sec=10

# セキュリティクッキー
jsettlers.bots.cookie=myrobotcookie123

# 自動起動（オプション）
# jsettlers.bots.start3p=2,soc.robot.rust.RustBotClient
```

### ステップ3: ボットの接続

#### 方法1（ネットワークプロトコル実装）の場合

```bash
cargo run -- localhost 8880 rustbot1 x myrobotcookie123
```

#### 方法2（Javaラッパー）の場合

```bash
java -Djava.library.path=/path/to/rust/lib \
     -cp JSettlers.jar:rust-bot.jar \
     soc.robot.rust.RustBotClient \
     localhost 8880 rustbot1 x myrobotcookie123
```

## テストと実行

### ステップ1: 基本的な接続テスト

1. サーバーを起動
2. ボットを起動
3. サーバーログでボットの接続を確認

```
Robot rustbot1 connected from 127.0.0.1
```

### ステップ2: ゲームの作成

人間のクライアントで接続し、ボットを含むゲームを作成：

```bash
java -jar JSettlers.jar localhost 8880
```

### ステップ3: デバッグ

#### サーバー側

トラフィックを表示：

```bash
java -Djsettlers.debug.traffic=Y -jar JSettlers.jar 8880
```

#### クライアント側

ログ出力を追加：

```rust
println!("Sent: {}", msg);
println!("Received: {}", msg);
```

### ステップ4: 複数ボットでのテスト

```bash
# ボット1
cargo run -- localhost 8880 rustbot1 x myrobotcookie123 &

# ボット2
cargo run -- localhost 8880 rustbot2 x myrobotcookie123 &

# ボット3
cargo run -- localhost 8880 rustbot3 x myrobotcookie123 &
```

## トラブルシューティング

### 接続できない

**問題**: ボットがサーバーに接続できない

**解決策**:
- ファイアウォールの設定を確認
- サーバーが正しいポートで起動しているか確認
- `telnet localhost 8880` でポートが開いているか確認

### 認証エラー

**問題**: "Invalid robot cookie" エラー

**解決策**:
- サーバーのクッキーとボットのクッキーが一致しているか確認
- サーバーログでクッキーを確認： `-Djsettlers.bots.showcookie=Y`

### メッセージフォーマットエラー

**問題**: "Malformed message" エラー

**解決策**:
- メッセージフォーマットを確認
- 区切り文字（`|`, `:`, `=`）が正しいか確認
- 特殊文字がエスケープされているか確認

### ゲームに参加できない

**問題**: ボットがゲームに参加できない

**解決策**:
- `SOCBotJoinGameRequest` メッセージを正しく処理しているか確認
- `SOCJoinGame` メッセージを送信しているか確認
- サーバーログでエラーメッセージを確認

### タイムアウト

**問題**: ボットのターンがタイムアウトする

**解決策**:
- `jsettlers.bots.timeout.turn` を増やす（デフォルト: 8秒）
- ボットの処理速度を改善
- 非同期処理を使用

## 参考資料

### JSettlersのドキュメント

- `Readme.md` - 基本的な情報とセットアップ
- `doc/Readme.developer.md` - 開発者向けドキュメント
- `doc/Message-Sequences-for-Game-Actions.md` - メッセージシーケンス
- `src/main/java/soc/message/SOCMessage.java` - メッセージフォーマット

### サンプルコード

- `src/main/java/soc/robot/sample3p/Sample3PClient.java` - サードパーティボットの例
- `src/main/java/soc/robot/sample3p/Sample3PBrain.java` - ボットブレインの例
- `src/main/java/soc/robot/SOCRobotClient.java` - 標準ボットクライアント
- `src/main/java/soc/robot/SOCRobotBrain.java` - 標準ボットブレイン

### 重要なメッセージクラス

- `SOCVersion` - バージョン情報
- `SOCImARobot` - ロボット識別
- `SOCUpdateRobotParams` - ロボットパラメータ
- `SOCBotJoinGameRequest` - ゲーム参加要求
- `SOCJoinGame` - ゲーム参加
- `SOCGameState` - ゲーム状態
- `SOCTurn` - ターン情報
- `SOCDiceResult` - サイコロ結果
- `SOCPutPiece` - 駒の配置
- `SOCBuildRequest` - 建設リクエスト

### 関連プロジェクト

他の言語/フレームワークでボットを作成したプロジェクト：

- **STAC (Strategic Conversation Project)** - https://github.com/ruflab/StacSettlers
  - 複数のボットタイプを実装
  - ゲームログの記録と再生
  
- **Settlers of Botan** - https://github.com/sambattalio/settlers_of_botan
  - サードパーティボットの例
  - JSettlersをライブラリとして使用

### 次のステップ

1. **基本的な接続を確立** - まず簡単な接続とメッセージ送受信を実装
2. **メッセージパーサーを実装** - 主要なメッセージタイプの解析
3. **ゲーム状態の追跡** - ゲームの状態を内部で保持
4. **基本的なアクション** - サイコロを振る、駒を置くなどの基本アクション
5. **高度な戦略** - private-rust-catanのエージェントを統合
6. **最適化とデバッグ** - パフォーマンス改善とバグ修正

### サポートとコミュニティ

- JSettlers GitHub: https://github.com/jdmonin/JSettlers2
- Issues: https://github.com/jdmonin/JSettlers2/issues
- メール: jsettlers@nand.net

---

## まとめ

このガイドでは、private-rust-catanで作成したRust製エージェントをJSettlersサーバーと対戦させる2つの主要な方法を説明しました：

1. **ネットワークプロトコルの直接実装（推奨）**
   - Rust単体で実装
   - 完全な制御が可能
   - デプロイが簡単

2. **Javaラッパーの作成**
   - JSettlersの既存機能を活用
   - JNIを使用した統合
   - 既存のインフラを利用

**推奨される開始方法:**

1. まず簡単な接続テストから始める
2. 基本的なメッセージの送受信を実装
3. ゲーム参加までの流れを実装
4. 段階的にゲームロジックを追加
5. private-rust-catanのエージェントを統合

**重要なポイント:**

- セキュリティクッキーの設定が必須
- メッセージフォーマットは厳密に従う
- タイムアウト設定に注意
- サーバーログでデバッグ

ご不明な点がありましたら、JSettlersのドキュメントを参照するか、GitHubでissueを作成してください。

頑張ってください！
