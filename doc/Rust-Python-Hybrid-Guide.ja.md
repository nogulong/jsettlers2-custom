# Python + Rust ハイブリッドエージェントの統合ガイド

このガイドは、Rust環境で学習したエージェントのニューラルネットワーク（NN）がPythonで実装されている場合に、JSettlersと統合する方法を説明します。

## 前提条件

- Rust環境で学習済みのエージェント
- PythonでトレーニングされたNNモデル（PyTorchやTensorFlowなど）
- JSettlersサーバー

## アーキテクチャの選択

### オプション1: Rustボット + PyO3（推奨）

**構成:**
```
[Rustボット] --PyO3--> [Python NN]
     |
     |
[JSettlersサーバー]
```

**利点:**
- 単一プロセス
- 低レイテンシ
- 簡単なデプロイ

**欠点:**
- Pythonランタイムが必要
- メモリフットプリント増加

### オプション2: 分離アーキテクチャ

**構成:**
```
[Rustボット] <--HTTP/gRPC--> [Python推論サーバー]
     |                              |
     |                         [NNモデル]
     |
[JSettlersサーバー]
```

**利点:**
- 独立したスケーリング
- NNサーバーを複数ボットで共有可能
- 言語の完全分離

**欠点:**
- ネットワークレイテンシ
- 複雑なデプロイ

## オプション1: Rustボット + PyO3の実装

### ステップ1: プロジェクトのセットアップ

#### Cargo.toml

```toml
[package]
name = "jsettlers-rust-bot-with-nn"
version = "0.1.0"
edition = "2021"

[dependencies]
pyo3 = { version = "0.20", features = ["auto-initialize"] }
serde = { version = "1", features = ["derive"] }
serde_json = "1"
```

### ステップ2: Python NNラッパーの作成

#### src/nn_agent.rs

```rust
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList};
use serde::{Serialize, Deserialize};

#[derive(Debug, Serialize, Deserialize)]
pub struct GameState {
    pub board: Vec<i32>,
    pub resources: Vec<i32>,
    pub player_positions: Vec<Position>,
    // その他のゲーム状態
}

#[derive(Debug, Serialize, Deserialize)]
pub struct Position {
    pub x: i32,
    pub y: i32,
}

pub struct NeuralNetworkAgent {
    py_module: Py<PyModule>,
}

impl NeuralNetworkAgent {
    /// Pythonモジュールを初期化
    pub fn new(python_path: &str, module_name: &str) -> PyResult<Self> {
        Python::with_gil(|py| {
            // Pythonのパスを追加
            let sys = py.import("sys")?;
            let path = sys.getattr("path")?;
            path.call_method1("insert", (0, python_path))?;
            
            // モジュールをインポート
            let module = py.import(module_name)?;
            
            // モデルを初期化（必要に応じて）
            module.call_method0("initialize_model")?;
            
            Ok(Self {
                py_module: module.into(),
            })
        })
    }
    
    /// ゲーム状態に基づいてアクションを予測
    pub fn predict_action(&self, game_state: &GameState) -> PyResult<i32> {
        Python::with_gil(|py| {
            let module = self.py_module.as_ref(py);
            
            // ゲーム状態をJSONに変換
            let state_json = serde_json::to_string(game_state)
                .map_err(|e| PyErr::new::<pyo3::exceptions::PyValueError, _>(
                    format!("Failed to serialize game state: {}", e)
                ))?;
            
            // PythonのNNで予測
            let result = module.call_method1("predict", (state_json,))?;
            
            // 結果を抽出
            let action: i32 = result.extract()?;
            Ok(action)
        })
    }
    
    /// バッチ予測（複数の状態を一度に処理）
    pub fn predict_actions_batch(&self, game_states: &[GameState]) -> PyResult<Vec<i32>> {
        Python::with_gil(|py| {
            let module = self.py_module.as_ref(py);
            
            // ゲーム状態のリストを作成
            let states_list = PyList::empty(py);
            for state in game_states {
                let state_json = serde_json::to_string(state)
                    .map_err(|e| PyErr::new::<pyo3::exceptions::PyValueError, _>(
                        format!("Failed to serialize game state: {}", e)
                    ))?;
                states_list.append(state_json)?;
            }
            
            // バッチ予測
            let result = module.call_method1("predict_batch", (states_list,))?;
            
            // 結果を抽出
            let actions: Vec<i32> = result.extract()?;
            Ok(actions)
        })
    }
}
```

### ステップ3: JSettlersボットとの統合

#### src/main.rs

```rust
mod nn_agent;

use std::io::{Read, Write};
use std::net::TcpStream;
use nn_agent::{NeuralNetworkAgent, GameState};

const GAME_STATE_ROLL_OR_CARD: &str = "15";

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

struct BotWithNN {
    stream: TcpStream,
    nickname: String,
    nn_agent: NeuralNetworkAgent,
    current_game: Option<String>,
    game_state: GameState,
}

impl BotWithNN {
    fn new(
        stream: TcpStream,
        nickname: String,
        nn_agent: NeuralNetworkAgent,
    ) -> Self {
        Self {
            stream,
            nickname,
            nn_agent,
            current_game: None,
            game_state: GameState::default(),
        }
    }
    
    fn authenticate(&mut self, cookie: &str) -> std::io::Result<()> {
        let version_msg = "VERSION:version=2.5.00,versionint=2500,locale=en_US,cliFeats=;6pl;sb;";
        println!("→ {}", version_msg);
        write_java_utf(&mut self.stream, version_msg)?;
        
        let robot_msg = format!(
            "IMAROBOT:nickname={}|cookie={}|rbclass=rust.bot.NNAgent",
            self.nickname, cookie
        );
        println!("→ {}", robot_msg);
        write_java_utf(&mut self.stream, &robot_msg)?;
        
        Ok(())
    }
    
    fn run(&mut self) -> std::io::Result<()> {
        loop {
            let msg = read_java_utf(&mut self.stream)?;
            println!("← {}", msg);
            
            if let Err(e) = self.handle_message(&msg) {
                eprintln!("Error handling message: {}", e);
            }
        }
    }
    
    fn handle_message(&mut self, msg: &str) -> std::io::Result<()> {
        let msg_type = match msg.split(':').next() {
            Some(t) if !t.is_empty() => t,
            _ => return Ok(()),
        };
        
        match msg_type {
            "UPDATEROBOTPARAMS" => {
                println!("✓ Robot parameters updated");
            }
            "GAMESTATE" => {
                self.handle_game_state(msg)?;
            }
            "PUTPIECE" => {
                self.update_game_state_from_piece(msg)?;
            }
            "DICERESULT" => {
                self.update_game_state_from_dice(msg)?;
            }
            // その他のメッセージタイプ...
            _ => {}
        }
        
        Ok(())
    }
    
    fn handle_game_state(&mut self, msg: &str) -> std::io::Result<()> {
        // ゲーム状態を更新
        // TODO: メッセージをパースして以下を更新：
        // - self.game_state.board (ボードの状態)
        // - self.game_state.resources (自分の資源)
        // - self.game_state.player_positions (プレイヤーの駒の位置)
        // 例: extract_field(msg, "state") でゲーム状態番号を取得
        
        // 自分のターンの場合、NNで次のアクションを決定
        if self.is_my_turn() {
            match self.nn_agent.predict_action(&self.game_state) {
                Ok(action) => {
                    self.execute_action(action)?;
                }
                Err(e) => {
                    eprintln!("NN prediction error: {}", e);
                    // フォールバック: ランダムまたはルールベースのアクション
                    self.execute_fallback_action()?;
                }
            }
        }
        
        Ok(())
    }
    
    fn is_my_turn(&self) -> bool {
        // ターンチェックのロジックを実装
        // 実際の実装では、ゲームメッセージから現在のプレイヤー番号を追跡する必要があります
        // TODO: 実装例 - self.current_player == self.my_player_number
        true // 簡略化のためのプレースホルダー
    }
    
    fn execute_action(&mut self, action: i32) -> std::io::Result<()> {
        // アクションをJSettlersメッセージに変換して送信
        let game = match &self.current_game {
            Some(g) => g,
            None => {
                eprintln!("Error: Not in a game");
                return Ok(());
            }
        };
        
        match action {
            0 => {
                // サイコロを振る
                let msg = format!("ROLLDICE:game={}", game);
                write_java_utf(&mut self.stream, &msg)?;
            }
            1 => {
                // 道路を建設
                // ... 実装 ...
            }
            // その他のアクション...
            _ => {}
        }
        
        Ok(())
    }
    
    fn execute_fallback_action(&mut self) -> std::io::Result<()> {
        // NNが失敗した場合のフォールバックロジック
        Ok(())
    }
    
    fn update_game_state_from_piece(&mut self, msg: &str) -> std::io::Result<()> {
        // 駒の配置メッセージからゲーム状態を更新
        Ok(())
    }
    
    fn update_game_state_from_dice(&mut self, msg: &str) -> std::io::Result<()> {
        // サイコロの結果からゲーム状態を更新
        Ok(())
    }
}

impl Default for GameState {
    fn default() -> Self {
        Self {
            board: vec![],
            resources: vec![],
            player_positions: vec![],
        }
    }
}

fn main() -> std::io::Result<()> {
    let args: Vec<String> = std::env::args().collect();
    
    if args.len() < 6 {
        eprintln!("Usage: {} <host> <port> <nickname> <cookie> <python_module_path>", args[0]);
        eprintln!("Example: {} localhost 8880 mybot abc123 /path/to/python/nn", args[0]);
        std::process::exit(1);
    }
    
    let host = &args[1];
    let port: u16 = args[2].parse().unwrap_or_else(|_| {
        eprintln!("Error: Invalid port number '{}'", args[2]);
        std::process::exit(1);
    });
    let nickname = &args[3];
    let cookie = &args[4];
    let python_path = &args[5];
    
    println!("🤖 JSettlers Rust Bot with Python NN");
    println!("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");
    
    // Python NNエージェントを初期化
    println!("🧠 Initializing neural network...");
    let nn_agent = NeuralNetworkAgent::new(python_path, "agent_module")
        .unwrap_or_else(|e| {
            eprintln!("Failed to initialize NN agent: {}", e);
            eprintln!("Make sure the Python module is in the correct path and dependencies are installed");
            std::process::exit(1);
        });
    println!("✓ Neural network ready");
    
    // JSettlersサーバーに接続
    println!("Connecting to {}:{}", host, port);
    let stream = TcpStream::connect((host.as_str(), port))?;
    println!("✓ Connected to server");
    
    let mut bot = BotWithNN::new(stream, nickname.to_string(), nn_agent);
    
    println!("🔐 Authenticating...");
    bot.authenticate(cookie)?;
    println!("✓ Authenticated");
    println!("⏳ Waiting for messages...");
    println!("");
    
    bot.run()?;
    
    Ok(())
}
```

### ステップ4: Pythonモジュールの作成

#### agent_module.py

```python
import json
import torch  # または tensorflow
import numpy as np

# グローバルモデル
_model = None

def initialize_model():
    """モデルを初期化（起動時に1回だけ呼ばれる）"""
    global _model
    # モデルをロード
    # セキュリティ: 信頼できるモデルのみを使用してください
    _model = torch.load('path/to/your/model.pth', map_location='cpu')
    _model.eval()
    print("Model loaded successfully")

def predict(game_state_json):
    """
    ゲーム状態からアクションを予測
    
    Args:
        game_state_json: ゲーム状態のJSON文字列
        
    Returns:
        予測されたアクションのID（整数）
    """
    global _model
    
    # JSONをパース
    state = json.loads(game_state_json)
    
    # モデル入力に変換
    features = preprocess_state(state)
    
    # 予測
    with torch.no_grad():
        output = _model(features)
        action = output.argmax().item()
    
    return action

def predict_batch(game_states_json_list):
    """
    複数のゲーム状態をバッチ処理
    
    Args:
        game_states_json_list: ゲーム状態のJSONのリスト
        
    Returns:
        予測されたアクションのリスト
    """
    global _model
    
    states = [json.loads(s) for s in game_states_json_list]
    features_batch = [preprocess_state(s) for s in states]
    features_tensor = torch.stack(features_batch)
    
    with torch.no_grad():
        outputs = _model(features_tensor)
        actions = outputs.argmax(dim=1).tolist()
    
    return actions

def preprocess_state(state):
    """
    ゲーム状態を前処理してモデル入力に変換
    
    Args:
        state: ゲーム状態の辞書
        
    Returns:
        torch.Tensor: モデル入力テンソル
    """
    # ボード状態を特徴ベクトルに変換
    board = torch.tensor(state['board'], dtype=torch.float32)
    resources = torch.tensor(state['resources'], dtype=torch.float32)
    
    # 必要に応じて正規化や追加の特徴エンジニアリング
    features = torch.cat([board, resources])
    
    return features

# TensorFlowを使用する場合の例
# import tensorflow as tf
# 
# _model = None
# 
# def initialize_model():
#     global _model
#     _model = tf.keras.models.load_model('path/to/your/model.h5')
#     print("TensorFlow model loaded")
# 
# def predict(game_state_json):
#     global _model
#     state = json.loads(game_state_json)
#     features = preprocess_state(state)
#     prediction = _model.predict(features.reshape(1, -1))
#     action = np.argmax(prediction)
#     return int(action)
```

### ステップ5: ビルドと実行

#### build.rs（必要に応じて）

```rust
fn main() {
    // PyO3の設定
    println!("cargo:rerun-if-changed=agent_module.py");
}
```

#### ビルド

```bash
# 開発環境でのビルド
cargo build --release

# 実行
./target/release/jsettlers-rust-bot-with-nn \
    localhost 8880 mybot abc123 /path/to/python/module
```

## オプション2: 分離アーキテクチャの実装

### Python推論サーバー

#### requirements.txt

```
flask==3.0.0
torch==2.1.0  # または tensorflow
gunicorn==21.2.0
```

#### inference_server.py

```python
from flask import Flask, request, jsonify
import torch
import json

app = Flask(__name__)

# グローバルモデル
model = None

def load_model():
    global model
    model = torch.load('path/to/model.pth')
    model.eval()

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy'})

@app.route('/predict', methods=['POST'])
def predict():
    try:
        game_state = request.json
        
        # 前処理
        features = preprocess_state(game_state)
        
        # 予測
        with torch.no_grad():
            output = model(features)
            action = output.argmax().item()
        
        return jsonify({
            'action': action,
            'confidence': float(output.max())
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/predict_batch', methods=['POST'])
def predict_batch():
    try:
        game_states = request.json['states']
        
        features_batch = [preprocess_state(s) for s in game_states]
        features_tensor = torch.stack(features_batch)
        
        with torch.no_grad():
            outputs = model(features_tensor)
            actions = outputs.argmax(dim=1).tolist()
        
        return jsonify({'actions': actions})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def preprocess_state(state):
    # ゲーム状態の前処理
    board = torch.tensor(state['board'], dtype=torch.float32)
    resources = torch.tensor(state['resources'], dtype=torch.float32)
    features = torch.cat([board, resources])
    return features

if __name__ == '__main__':
    load_model()
    app.run(host='0.0.0.0', port=5000)
```

#### サーバー起動

```bash
# 開発用
python inference_server.py

# 本番用
gunicorn -w 4 -b 0.0.0.0:5000 inference_server:app
```

### Rustボット（HTTPクライアント）

#### Cargo.toml

```toml
[dependencies]
reqwest = { version = "0.11", features = ["json"] }
tokio = { version = "1", features = ["full"] }
serde = { version = "1", features = ["derive"] }
serde_json = "1"
```

#### src/nn_client.rs

```rust
use reqwest;
use serde::{Serialize, Deserialize};

#[derive(Debug, Serialize)]
pub struct GameState {
    pub board: Vec<i32>,
    pub resources: Vec<i32>,
}

#[derive(Debug, Deserialize)]
struct PredictionResponse {
    action: i32,
    confidence: f32,
}

pub struct NNClient {
    client: reqwest::Client,
    server_url: String,
}

impl NNClient {
    pub fn new(server_url: String) -> Self {
        Self {
            client: reqwest::Client::new(),
            server_url,
        }
    }
    
    pub async fn predict(&self, game_state: &GameState) -> Result<i32, Box<dyn std::error::Error>> {
        let url = format!("{}/predict", self.server_url);
        
        let response = self.client
            .post(&url)
            .json(game_state)
            .send()
            .await?;
        
        let result: PredictionResponse = response.json().await?;
        Ok(result.action)
    }
    
    pub async fn health_check(&self) -> Result<bool, Box<dyn std::error::Error>> {
        let url = format!("{}/health", self.server_url);
        let response = self.client.get(&url).send().await?;
        Ok(response.status().is_success())
    }
}
```

## トラブルシューティング

### PyO3関連の問題

**問題**: `pyo3` のビルドエラー

**解決策**:
```bash
# Pythonの開発ヘッダーをインストール
# Ubuntu/Debian
sudo apt-get install python3-dev

# macOS
brew install python3

# 環境変数を設定
export PYO3_PYTHON=python3
```

### Python モジュールが見つからない

**問題**: `ModuleNotFoundError: No module named 'agent_module'`

**解決策**:
- Pythonパスが正しいか確認
- `PYTHONPATH` 環境変数を設定
```bash
export PYTHONPATH=/path/to/your/python/code:$PYTHONPATH
```

### メモリ使用量が高い

**解決策**:
- 分離アーキテクチャを使用
- モデルの量子化を検討
- バッチ予測を使用してオーバーヘッドを削減

### レイテンシが高い

**解決策**:
- GPU推論を有効化（PyTorch/TensorFlowで）
- モデルを最適化（ONNX、TensorRT等）
- キャッシング戦略を実装
- 非同期処理を使用

## まとめ

Python + Rustハイブリッドの統合には：

1. **PyO3アプローチ**: 単純で低レイテンシだが、Pythonランタイムが必要
2. **分離アーキテクチャ**: 柔軟でスケーラブルだが、ネットワークオーバーヘッドあり

どちらの方法も、`examples/rust-bot/`のサンプルをベースに、NN推論部分を追加することで実装できます。

詳細は以下を参照：
- [Rust Agent Integration Guide](Rust-Agent-Integration-Guide.ja.md)
- [Rust Agent Quick Start](Rust-Agent-Quick-Start.ja.md)
