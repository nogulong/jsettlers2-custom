# JSettlers Internal Bots - Documentation Index

このディレクトリには、JSettlersの内蔵ボットシステムに関する包括的なドキュメントが含まれています。

## クイックスタート

1. **[ANSWER_TO_PROBLEM.ja.md](ANSWER_TO_PROBLEM.ja.md)** または **[ANSWER_TO_PROBLEM.md](ANSWER_TO_PROBLEM.md)** から始める
   - 問題文の3つの質問に対する直接的な回答
   - 必要な変更点の要約
   - すぐに実装を開始できる

## ドキュメント一覧

### 日本語ドキュメント

| ファイル | 内容 | 読む順序 |
|---------|------|---------|
| **ANSWER_TO_PROBLEM.ja.md** | 問題文への直接的な回答 | 1️⃣ 最初に読む |
| **INTERNAL_BOTS.ja.md** | 内蔵ボットシステムの詳細ガイド | 2️⃣ 次に読む |
| **IMPLEMENTING_INTERNAL_BOTS.ja.md** | 実装ガイドとコード例 | 3️⃣ 実装時に参照 |

### English Documentation

| File | Content | Reading Order |
|------|---------|---------------|
| **ANSWER_TO_PROBLEM.md** | Direct answers to problem statement | 1️⃣ Read first |
| **INTERNAL_BOTS_GUIDE.md** | Overview of internal bot system | 2️⃣ Read next |

### コードとサンプル

| ファイル | 内容 |
|---------|------|
| **example_internal_bots.py** | 内蔵ボットの使用例と説明を出力するスクリプト |
| **jsettler_utils.py** | 問題文のコードで使用するユーティリティ関数 |

## 各ドキュメントの概要

### ANSWER_TO_PROBLEM.ja.md / .md
問題文で提起された3つの質問に対する直接的な回答：
1. ゲーム作成時に指定した数だけ内蔵ボットを追加する方法
2. ボットが有効な座席に座り、内蔵ボットの座席を奪わない方法
3. 内蔵ボットの種類についての詳細

**こんな人におすすめ**:
- すぐに答えが欲しい
- 問題文のコードを修正したい
- 要点だけを知りたい

### INTERNAL_BOTS.ja.md
内蔵ボットシステムの包括的なガイド：
- ボットの種類（FAST_STRATEGY と SMART_STRATEGY）の詳細
- プロトコルメッセージの説明（1012, 1013, 1023）
- 座席選択の仕組み
- トラブルシューティング

**こんな人におすすめ**:
- 内蔵ボットシステムの全体像を理解したい
- プロトコルの詳細を知りたい
- トラブルシューティングが必要

### IMPLEMENTING_INTERNAL_BOTS.ja.md
実装ガイドと具体的なコード例：
- 問題文のコードに必要な変更点
- 完全な実装例
- ゲーム作成フローの説明
- 重要なポイントのまとめ

**こんな人におすすめ**:
- 実際にコードを書いている
- 具体的な実装方法を知りたい
- コピー＆ペーストできるコード例が欲しい

### INTERNAL_BOTS_GUIDE.md
English version of the overview:
- Bot types and characteristics
- How internal bots are added automatically
- Seat selection best practices
- Implementation summary

**Who should read this**:
- English speakers
- Want a quick overview
- Need implementation guidance

### example_internal_bots.py
実行可能なサンプルスクリプト：
```bash
python3 example_internal_bots.py
```

出力内容：
- 3つの使用例
- 座席選択の説明
- ボットタイプの詳細
- トラブルシューティングガイド

**こんな人におすすめ**:
- 実際に動くコードを見たい
- 使用例を確認したい
- 視覚的に理解したい

### jsettler_utils.py
問題文のコードで使用するユーティリティ関数：
- `write_java_utf()` - Javaプロトコルでメッセージ送信
- `read_java_utf()` - Javaプロトコルでメッセージ受信
- `parse_message()` - メッセージのパース
- `parse_board_layout_1084()` - ボードレイアウトのパース

**こんな人におすすめ**:
- 問題文のコードを実装している
- プロトコル通信の実装が必要
- ユーティリティ関数が必要

## 推奨される読み方

### 初めての方
1. **ANSWER_TO_PROBLEM.ja.md** を読む（5分）
2. **example_internal_bots.py** を実行して出力を確認（2分）
3. 必要に応じて **IMPLEMENTING_INTERNAL_BOTS.ja.md** を参照

### 詳細を知りたい方
1. **ANSWER_TO_PROBLEM.ja.md** で概要を把握
2. **INTERNAL_BOTS.ja.md** で詳細を理解
3. **IMPLEMENTING_INTERNAL_BOTS.ja.md** で実装方法を学習
4. **example_internal_bots.py** で実例を確認

### トラブルシューティング中の方
1. **ANSWER_TO_PROBLEM.ja.md** の「トラブルシューティング」セクション
2. **INTERNAL_BOTS.ja.md** の「トラブルシューティング」セクション
3. **example_internal_bots.py** の出力を参照

## よくある質問

### Q: 内蔵ボットが参加しない
→ **ANSWER_TO_PROBLEM.ja.md** の「トラブルシューティング」セクションを参照

### Q: 座席の競合が発生する
→ **IMPLEMENTING_INTERNAL_BOTS.ja.md** の「座席選択の改善」セクションを参照

### Q: ボットの種類を指定したい
→ **ANSWER_TO_PROBLEM.ja.md** の「質問3」を参照（クライアント側から指定はできません）

### Q: プロトコルメッセージの詳細を知りたい
→ **INTERNAL_BOTS.ja.md** の「プロトコルメッセージ」セクションを参照

## サポート

これらのドキュメントで解決しない問題がある場合：
1. JSettlersのソースコードを参照
   - `src/main/java/soc/robot/` - ロボットAIの実装
   - `src/main/java/soc/server/SOCServer.java` - サーバー側のロボット管理
2. サーバーログを確認
3. デバッグ出力を有効化

## 更新履歴

- 2024-12-27: 初版作成
  - 問題文への回答ドキュメント作成
  - 内蔵ボットシステムの包括的なガイド作成
  - 実装ガイドとサンプルコード作成

## ライセンス

このドキュメントは、JSettlersプロジェクトと同じGPLv3ライセンスの下で提供されます。
