# クイックスタート: Rust製エージェントとJSettlersの対戦

private-rust-catanで作成したエージェントをJSettlersと対戦させるための最短手順です。

## 注意: Python NNを使用している場合

**エージェントのニューラルネットワーク（NN）がPythonで実装されている場合**は、[Python + Rust ハイブリッドガイド](Rust-Python-Hybrid-Guide.ja.md)を参照してください。PyO3や分離アーキテクチャを使用した統合方法が説明されています。

## 最も簡単な方法

ネットワークプロトコルを実装してRustで直接JSettlersサーバーに接続する方法を推奨します。

## 必要なもの

1. JSettlersサーバー（このリポジトリ）
2. Rustの開発環境
3. private-rust-catanのエージェント実装

## 5ステップで開始

### ステップ1: JSettlersサーバーを起動

```bash
# プロジェクトをビルド
./gradlew assemble

# セキュリティクッキーを表示してサーバーを起動
java -Djsettlers.bots.showcookie=Y -jar build/libs/JSettlers-*.jar 8880
```

サーバーが起動すると、以下のようなメッセージが表示されます：
```
Robot cookie: abc123def456
```

このクッキー（`abc123def456`）をメモしてください。

### ステップ2: Rustプロジェクトを作成

```bash
cargo new jsettlers-rust-bot
cd jsettlers-rust-bot
```

`Cargo.toml` に依存関係を追加：

```toml
[dependencies]
tokio = { version = "1", features = ["full"] }
serde_json = "1"
```

### ステップ3: 基本的なボットを実装

`src/main.rs` に以下のコードをコピー：

```rust
use std::io::{Read, Write};
use std::net::TcpStream;

fn write_java_utf(stream: &mut TcpStream, msg: &str) -> std::io::Result<()> {
    let bytes = msg.as_bytes();
    let len = (bytes.len() as u16).to_be_bytes();
    stream.write_all(&len)?;
    stream.write_all(bytes)?;
    stream.flush()?;
    Ok(())
}

fn read_java_utf(stream: &mut TcpStream) -> std::io::Result<String> {
    let mut len_bytes = [0u8; 2];
    stream.read_exact(&mut len_bytes)?;
    let len = u16::from_be_bytes(len_bytes) as usize;
    
    let mut buf = vec![0u8; len];
    stream.read_exact(&mut buf)?;
    
    String::from_utf8(buf)
        .map_err(|e| std::io::Error::new(std::io::ErrorKind::InvalidData, e))
}

fn main() -> std::io::Result<()> {
    let args: Vec<String> = std::env::args().collect();
    if args.len() < 5 {
        eprintln!("Usage: {} <host> <port> <nickname> <cookie>", args[0]);
        eprintln!("Example: {} localhost 8880 mybot abc123def456", args[0]);
        std::process::exit(1);
    }
    
    let host = &args[1];
    let port: u16 = args[2].parse().expect("Invalid port");
    let nickname = &args[3];
    let cookie = &args[4];
    
    println!("Connecting to {}:{} as {}", host, port, nickname);
    let mut stream = TcpStream::connect((host.as_str(), port))?;
    
    // 1. バージョン情報を送信
    let version_msg = "VERSION:version=2.5.00,versionint=2500,locale=ja,cliFeats=;6pl;sb;";
    println!("Sending: {}", version_msg);
    write_java_utf(&mut stream, version_msg)?;
    
    // 2. ロボットとして識別
    let robot_msg = format!(
        "IMAROBOT:nickname={}|cookie={}|rbclass=rust.bot.RustAgent",
        nickname, cookie
    );
    println!("Sending: {}", robot_msg);
    write_java_utf(&mut stream, &robot_msg)?;
    
    // 3. メッセージループ
    println!("Connected! Waiting for messages...");
    loop {
        match read_java_utf(&mut stream) {
            Ok(msg) => {
                println!("Received: {}", msg);
                
                // 基本的なメッセージ処理
                if msg.starts_with("BOTJOINGAMEREQUEST:") {
                    // ゲーム参加要求を解析
                    if let Some(game_name) = extract_game_name(&msg) {
                        let join_msg = format!("JOINGAME:nickname={}|password=|host=-|game={}", 
                                              nickname, game_name);
                        println!("Joining game: {}", game_name);
                        write_java_utf(&mut stream, &join_msg)?;
                    }
                } else if msg.starts_with("TURN:") {
                    // 自分のターン - サイコロを振る
                    if msg.contains(&format!("playerNumber={}", extract_player_number(&msg)?)) {
                        let game_name = extract_game_name(&msg).unwrap_or("game".to_string());
                        let roll_msg = format!("ROLLDICE:game={}", game_name);
                        println!("Rolling dice");
                        write_java_utf(&mut stream, &roll_msg)?;
                    }
                }
                // その他のメッセージタイプは後で実装
            }
            Err(e) => {
                eprintln!("Error reading message: {}", e);
                break;
            }
        }
    }
    
    Ok(())
}

fn extract_game_name(msg: &str) -> Option<String> {
    msg.split("|")
        .find(|part| part.starts_with("game="))
        .and_then(|part| part.split("=").nth(1))
        .map(|s| s.to_string())
}

fn extract_player_number(msg: &str) -> std::io::Result<i32> {
    msg.split("|")
        .find(|part| part.starts_with("playerNumber="))
        .and_then(|part| part.split("=").nth(1))
        .and_then(|s| s.parse().ok())
        .ok_or_else(|| std::io::Error::new(std::io::ErrorKind::InvalidData, "No player number"))
}
```

### ステップ4: ボットを実行

```bash
cargo run -- localhost 8880 rustbot1 abc123def456
```

（`abc123def456` をステップ1で取得したクッキーに置き換えてください）

### ステップ5: ゲームを作成してテスト

別のターミナルで人間のクライアントを起動：

```bash
java -jar build/libs/JSettlers-*.jar localhost 8880
```

1. ゲームを作成
2. Rust製ボット（`rustbot1`）を追加
3. ゲームを開始

## 次のステップ

基本的な接続ができたら、以下を実装していきます：

1. **ゲーム状態の追跡** - ボード、資源、プレイヤー情報を保持
2. **より多くのアクション** - 建設、交易、開発カードの使用
3. **private-rust-catanの統合** - エージェントのロジックを接続
4. **戦略の改善** - より賢い判断

詳細なガイドは `doc/Rust-Agent-Integration-Guide.ja.md` を参照してください。

## トラブルシューティング

### 接続できない

```bash
# ポートが開いているか確認
telnet localhost 8880
```

### クッキーが違う

サーバーを起動し直してクッキーを確認：

```bash
java -Djsettlers.bots.showcookie=Y -jar build/libs/JSettlers-*.jar 8880
```

### より詳しいログ

サーバー側でトラフィックを表示：

```bash
java -Djsettlers.debug.traffic=Y \
     -Djsettlers.bots.showcookie=Y \
     -jar build/libs/JSettlers-*.jar 8880
```

## 参考資料

- 詳細ガイド: `doc/Rust-Agent-Integration-Guide.ja.md`
- メッセージシーケンス: `doc/Message-Sequences-for-Game-Actions.md`
- 開発者向けドキュメント: `doc/Readme.developer.md`
- サンプルボット: `src/main/java/soc/robot/sample3p/`

頑張ってください！
