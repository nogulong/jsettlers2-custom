# Pythonボット アクションガイド

このガイドでは、JSettlers Pythonボットから各ゲームアクション（道路建設、開発カード購入など）を実行する方法を説明します。

## 目次

1. [概要](#概要)
2. [メッセージ送信の基本](#メッセージ送信の基本)
3. [サイコロを振る](#サイコロを振る)
4. [建設アクション](#建設アクション)
5. [開発カードの購入](#開発カードの購入)
6. [開発カードの使用](#開発カードの使用)
7. [交易](#交易)
8. [ターン終了](#ターン終了)

---

## 概要

JSettlersサーバーとの通信は、テキストベースのメッセージプロトコルを使用します。各アクションには以下が含まれます：

1. **送信メッセージ**: Pythonボットからサーバーへ送信
2. **受信メッセージ**: サーバーからの応答（複数の場合あり）
3. **タイミング**: 次のメッセージを送信するタイミング

### メッセージ形式

サーバーへ送信するメッセージは以下の形式：
```
MESSAGETYPE:param1=value1|param2=value2
```

例:
```
BUILDREQUEST:game=test|pieceType=0
PUTPIECE:game=test|playerNumber=3|pieceType=0|coord=809
```

---

## メッセージ送信の基本

### utils.pyのbuild_message関数を使用

```python
from utils import write_java_utf, build_message

# 例: 道路建設リクエスト
msg = build_message("BUILDREQUEST", game=self.current_game, pieceType="0")
write_java_utf(self.sock, msg)
```

### 直接メッセージを構築

```python
msg = f"BUILDREQUEST:game={self.current_game}|pieceType=0"
write_java_utf(self.sock, msg)
```

---

## サイコロを振る

### アクション: ROLLDICE

**タイミング**: ゲーム状態が15 (ROLL_OR_CARD) の時、自分のターンの最初

### 送信メッセージ

```python
def roll_dice(self):
    """サイコロを振る"""
    msg = build_message("ROLLDICE", game=self.current_game)
    write_java_utf(self.sock, msg)
```

**メッセージ形式**:
```
ROLLDICE:game=test
```

### 受信メッセージシーケンス

#### ケース1: 7以外の出目

```
← DICERESULT:game=test|param=9
← DICERESULTRESOURCES:game=test|p=2|p=2|...
← PLAYERELEMENTS:game=test|playerNum=2|actionType=SET|e1=2,e2=0,...
← GAMESTATE:game=test|state=20  // PLAY1
```

**次のアクション**: `GAMESTATE:state=20`を受信したら、建設や開発カード購入などのアクションが可能

#### ケース2: 7の出目（盗賊移動）

```
← DICERESULT:game=test|param=7
← GAMESTATE:game=test|state=33  // PLACING_ROBBER
```

**次のアクション**: `GAMESTATE:state=33`を受信したら、`MOVEROBBER`メッセージを送信

#### ケース3: 7の出目（カード破棄）

```
← DICERESULT:game=test|param=7
← GAMESTATE:game=test|state=50  // WAITING_FOR_DISCARDS
← DISCARDREQUEST:game=test|numDiscards=4
```

**次のアクション**: `DISCARDREQUEST`を受信したら、`DISCARD`メッセージで破棄するカードを送信

---

## 建設アクション

### 建設方法の2パターン

JSettlersでは、建設に2つの方法があります：

#### 方法1: BUILDREQUEST + PUTPIECE (推奨)

1. `BUILDREQUEST`で建設タイプを宣言
2. サーバーがリソースを消費し、状態を変更
3. `PUTPIECE`で具体的な位置を指定

#### 方法2: PUTPIECE のみ

直接`PUTPIECE`を送信（初期配置やリソース不要な場合）

---

### 道路建設 (BUILDREQUEST + PUTPIECE)

**タイミング**: ゲーム状態20 (PLAY1) で、十分なリソース（木材1、粘土1）がある時

#### ステップ1: BUILDREQUESTを送信

```python
def request_build_road(self):
    """道路建設をリクエスト"""
    msg = build_message("BUILDREQUEST", game=self.current_game, pieceType="0")
    write_java_utf(self.sock, msg)
```

**メッセージ形式**:
```
BUILDREQUEST:game=test|pieceType=0
```

**pieceType値**:
- `0`: 道路
- `1`: 集落
- `2`: 都市
- `3`: 船

#### 受信メッセージ

```
← PLAYERELEMENTS:game=test|playerNum=3|actionType=LOSE|e1=1,e5=1
← GAMESTATE:game=test|state=30  // PLACING_ROAD
```

**重要**: `GAMESTATE:state=30`を受信したら、道路を配置できる状態になっています。

#### ステップ2: PUTPIECEを送信

```python
def place_road(self, coord: int):
    """道路を配置（BUILDREQUESTの後）"""
    msg = build_message(
        "PUTPIECE",
        game=self.current_game,
        playerNumber=str(self.game_state.my_player_number),
        pieceType="0",
        coord=str(coord)
    )
    write_java_utf(self.sock, msg)
```

**メッセージ形式**:
```
PUTPIECE:game=test|playerNumber=3|pieceType=0|coord=809
```

**coord値**: 16進数形式の座標（例: `809`, `a06`）

#### 受信メッセージ

```
← PUTPIECE:game=test|playerNumber=3|pieceType=0|coord=809
← GAMESTATE:game=test|state=20  // PLAY1
```

**次のアクション**: `GAMESTATE:state=20`を受信したら、通常のプレイ状態に戻ります。

---

### 集落建設

**タイミング**: ゲーム状態20 (PLAY1) で、十分なリソース（木材1、粘土1、羊1、小麦1）がある時

#### ステップ1: BUILDREQUESTを送信

```python
def request_build_settlement(self):
    """集落建設をリクエスト"""
    msg = build_message("BUILDREQUEST", game=self.current_game, pieceType="1")
    write_java_utf(self.sock, msg)
```

**メッセージ形式**:
```
BUILDREQUEST:game=test|pieceType=1
```

#### 受信メッセージ

```
← PLAYERELEMENTS:game=test|playerNum=3|actionType=LOSE|e1=1,e3=1,e4=1,e5=1
← GAMESTATE:game=test|state=31  // PLACING_SETTLEMENT
```

#### ステップ2: PUTPIECEを送信

```python
def place_settlement(self, coord: int):
    """集落を配置"""
    msg = build_message(
        "PUTPIECE",
        game=self.current_game,
        playerNumber=str(self.game_state.my_player_number),
        pieceType="1",
        coord=str(coord)
    )
    write_java_utf(self.sock, msg)
```

**メッセージ形式**:
```
PUTPIECE:game=test|playerNumber=3|pieceType=1|coord=67
```

#### 受信メッセージ

```
← PUTPIECE:game=test|playerNumber=3|pieceType=1|coord=67
← GAMESTATE:game=test|state=20  // PLAY1
```

---

### 都市建設

**タイミング**: ゲーム状態20 (PLAY1) で、十分なリソース（鉱石3、小麦2）と配置済みの集落がある時

#### ステップ1: BUILDREQUESTを送信

```python
def request_build_city(self):
    """都市建設をリクエスト"""
    msg = build_message("BUILDREQUEST", game=self.current_game, pieceType="2")
    write_java_utf(self.sock, msg)
```

**メッセージ形式**:
```
BUILDREQUEST:game=test|pieceType=2
```

#### 受信メッセージ

```
← PLAYERELEMENTS:game=test|playerNum=3|actionType=LOSE|e2=3,e4=2
← GAMESTATE:game=test|state=32  // PLACING_CITY
```

#### ステップ2: PUTPIECEを送信

```python
def place_city(self, coord: int):
    """都市を配置（既存の集落の座標）"""
    msg = build_message(
        "PUTPIECE",
        game=self.current_game,
        playerNumber=str(self.game_state.my_player_number),
        pieceType="2",
        coord=str(coord)
    )
    write_java_utf(self.sock, msg)
```

**メッセージ形式**:
```
PUTPIECE:game=test|playerNumber=3|pieceType=2|coord=67
```

#### 受信メッセージ

```
← PUTPIECE:game=test|playerNumber=3|pieceType=2|coord=67
← GAMESTATE:game=test|state=20  // PLAY1
```

---

### 直接PUTPIECE（初期配置など）

初期配置やリソース不要な状況では、`BUILDREQUEST`なしで直接`PUTPIECE`を送信できます。

```python
def place_piece_direct(self, piece_type: int, coord: int):
    """駒を直接配置（初期配置用）"""
    msg = build_message(
        "PUTPIECE",
        game=self.current_game,
        playerNumber=str(self.game_state.my_player_number),
        pieceType=str(piece_type),
        coord=str(coord)
    )
    write_java_utf(self.sock, msg)
```

---

## 開発カードの購入

### アクション: BUYDEVCARDREQUEST

**タイミング**: ゲーム状態20 (PLAY1) で、十分なリソース（鉱石1、羊1、小麦1）がある時

### 送信メッセージ

```python
def buy_dev_card(self):
    """開発カードを購入"""
    msg = build_message("BUYDEVCARDREQUEST", game=self.current_game)
    write_java_utf(self.sock, msg)
```

**メッセージ形式**:
```
BUYDEVCARDREQUEST:game=test
```

### 受信メッセージシーケンス

```
← PLAYERELEMENTS:game=test|playerNum=3|actionType=LOSE|e2=1,e3=1,e4=1
← DEVCARDACTION:game=test|playerNum=3|actionType=DRAW|cardType=5
← DEVCARDACTION:game=test|playerNum=3|actionType=DRAW|cardType=0  // 他のプレイヤー向け（隠蔽）
← SIMPLEACTION:game=test|pn=3|actType=1|v1=22|v2=0
← GAMESTATE:game=test|state=20  // PLAY1
```

**cardType値**:
- `1`: Road Building (道路建設)
- `2`: Year of Plenty (豊作)
- `3`: Monopoly (独占)
- `4`: Victory Point (勝利点)
- `5`: Knight (騎士)

**次のアクション**: `GAMESTATE:state=20`を受信したら、通常のプレイ状態に戻ります。

---

## 開発カードの使用

### 基本形式: PLAYDEVCARDREQUEST

```python
def play_dev_card(self, card_type: int):
    """開発カードを使用"""
    msg = build_message("PLAYDEVCARDREQUEST", game=self.current_game, devCard=str(card_type))
    write_java_utf(self.sock, msg)
```

---

### 騎士カード (Knight)

**タイミング**: ゲーム状態15 (ROLL_OR_CARD) または 20 (PLAY1)

#### 送信メッセージ

```python
def play_knight(self):
    """騎士カードを使用"""
    msg = build_message("PLAYDEVCARDREQUEST", game=self.current_game, devCard="5")
    write_java_utf(self.sock, msg)
```

**メッセージ形式**:
```
PLAYDEVCARDREQUEST:game=test|devCard=5
```

#### 受信メッセージ

```
← DEVCARDACTION:game=test|playerNum=3|actionType=PLAY|cardType=5
← PLAYERELEMENT:game=test|playerNum=3|actionType=SET|elementType=19|amount=1
← GAMESTATE:game=test|state=33  // PLACING_ROBBER
```

**次のアクション**: `GAMESTATE:state=33`を受信したら、`MOVEROBBER`で盗賊を移動

---

### 道路建設カード (Road Building)

**タイミング**: ゲーム状態15 (ROLL_OR_CARD) または 20 (PLAY1)

#### 送信メッセージ

```python
def play_road_building(self):
    """道路建設カードを使用"""
    msg = build_message("PLAYDEVCARDREQUEST", game=self.current_game, devCard="1")
    write_java_utf(self.sock, msg)
```

**メッセージ形式**:
```
PLAYDEVCARDREQUEST:game=test|devCard=1
```

#### 受信メッセージ

```
← DEVCARDACTION:game=test|playerNum=3|actionType=PLAY|cardType=1
← PLAYERELEMENT:game=test|playerNum=3|actionType=SET|elementType=19|amount=1
← GAMESTATE:game=test|state=40  // PLACING_FREE_ROAD1
```

**次のアクション**: `GAMESTATE:state=40`を受信したら、`PUTPIECE`で1本目の道路を配置

#### 1本目の道路配置

```python
def place_free_road_1(self, coord: int):
    """無料道路1本目を配置"""
    msg = build_message(
        "PUTPIECE",
        game=self.current_game,
        playerNumber=str(self.game_state.my_player_number),
        pieceType="0",
        coord=str(coord)
    )
    write_java_utf(self.sock, msg)
```

#### 受信メッセージ

```
← PUTPIECE:game=test|playerNumber=3|pieceType=0|coord=704
← GAMESTATE:game=test|state=41  // PLACING_FREE_ROAD2
```

**次のアクション**: `GAMESTATE:state=41`を受信したら、`PUTPIECE`で2本目の道路を配置

#### 2本目の道路配置

```python
def place_free_road_2(self, coord: int):
    """無料道路2本目を配置"""
    msg = build_message(
        "PUTPIECE",
        game=self.current_game,
        playerNumber=str(self.game_state.my_player_number),
        pieceType="0",
        coord=str(coord)
    )
    write_java_utf(self.sock, msg)
```

#### 受信メッセージ

```
← PUTPIECE:game=test|playerNumber=3|pieceType=0|coord=804
← GAMESTATE:game=test|state=20  // PLAY1
```

---

### 豊作カード (Year of Plenty)

**タイミング**: ゲーム状態15 (ROLL_OR_CARD) または 20 (PLAY1)

#### 送信メッセージ

```python
def play_year_of_plenty(self):
    """豊作カードを使用"""
    msg = build_message("PLAYDEVCARDREQUEST", game=self.current_game, devCard="2")
    write_java_utf(self.sock, msg)
```

**メッセージ形式**:
```
PLAYDEVCARDREQUEST:game=test|devCard=2
```

#### 受信メッセージ

```
← DEVCARDACTION:game=test|playerNum=3|actionType=PLAY|cardType=2
← PLAYERELEMENT:game=test|playerNum=3|actionType=SET|elementType=19|amount=1
← GAMESTATE:game=test|state=52  // WAITING_FOR_DISCOVERY
```

**次のアクション**: `GAMESTATE:state=52`を受信したら、`PICKRESOURCES`で2つのリソースを選択

#### リソース選択

```python
def pick_resources_year_of_plenty(self, clay=0, ore=0, sheep=0, wheat=0, wood=0):
    """豊作カードでリソースを選択（合計2つ）"""
    msg = build_message(
        "PICKRESOURCES",
        game=self.current_game,
        resources=f"clay={clay}|ore={ore}|sheep={sheep}|wheat={wheat}|wood={wood}|unknown=0"
    )
    write_java_utf(self.sock, msg)
```

**メッセージ形式例**:
```
PICKRESOURCES:game=test|resources=clay=0|ore=1|sheep=0|wheat=1|wood=0|unknown=0
```

**重要**: リソースの合計は2つである必要があります（例: ore=1, wheat=1）

#### 受信メッセージ

```
← PICKRESOURCES:game=test|resources=clay=0|ore=1|sheep=0|wheat=1|wood=0|unknown=0|pn=3|reason=2
← GAMESTATE:game=test|state=20  // PLAY1
```

---

### 独占カード (Monopoly)

**タイミング**: ゲーム状態15 (ROLL_OR_CARD) または 20 (PLAY1)

#### 送信メッセージ

```python
def play_monopoly(self):
    """独占カードを使用"""
    msg = build_message("PLAYDEVCARDREQUEST", game=self.current_game, devCard="3")
    write_java_utf(self.sock, msg)
```

**メッセージ形式**:
```
PLAYDEVCARDREQUEST:game=test|devCard=3
```

#### 受信メッセージ

```
← DEVCARDACTION:game=test|playerNum=3|actionType=PLAY|cardType=3
← PLAYERELEMENT:game=test|playerNum=3|actionType=SET|elementType=19|amount=1
← GAMESTATE:game=test|state=53  // WAITING_FOR_MONOPOLY
```

**次のアクション**: `GAMESTATE:state=53`を受信したら、`PICKRESOURCETYPE`でリソースタイプを選択

#### リソースタイプ選択

```python
def pick_resource_type_monopoly(self, resource_type: int):
    """独占カードでリソースタイプを選択"""
    msg = build_message("PICKRESOURCETYPE", game=self.current_game, resType=str(resource_type))
    write_java_utf(self.sock, msg)
```

**メッセージ形式例**:
```
PICKRESOURCETYPE:game=test|resType=3
```

**resType値**:
- `1`: 粘土 (Clay)
- `2`: 鉱石 (Ore)
- `3`: 羊 (Sheep)
- `4`: 小麦 (Wheat)
- `5`: 木材 (Wood)

#### 受信メッセージ

```
← PICKRESOURCETYPE:game=test|resType=3|pn=3
← PLAYERELEMENT:game=test|playerNum=3|actionType=GAIN|elementType=3|amount=4
← GAMESTATE:game=test|state=20  // PLAY1
```

---

## 交易

### 銀行との交易 (Bank Trade)

**タイミング**: ゲーム状態20 (PLAY1)

#### 送信メッセージ

```python
def bank_trade(self, give_resources: dict, get_resources: dict):
    """銀行と交易"""
    # give_resources = {"clay": 4, "ore": 0, ...}
    # get_resources = {"clay": 0, "ore": 1, ...}
    
    give_str = "|".join(f"{k}={v}" for k, v in give_resources.items())
    get_str = "|".join(f"{k}={v}" for k, v in get_resources.items())
    
    msg = build_message(
        "BANKTRADE",
        game=self.current_game,
        give=give_str,
        get=get_str
    )
    write_java_utf(self.sock, msg)
```

**メッセージ形式例** (粘土4つを鉱石1つに交換):
```
BANKTRADE:game=test|give=clay=4|ore=0|sheep=0|wheat=0|wood=0|get=clay=0|ore=1|sheep=0|wheat=0|wood=0
```

#### 受信メッセージ

```
← PLAYERELEMENTS:game=test|playerNum=3|actionType=LOSE|e1=4
← PLAYERELEMENT:game=test|playerNum=3|actionType=GAIN|elementType=2|amount=1
← GAMESTATE:game=test|state=20  // PLAY1
```

---

### プレイヤーとの交易提案 (Make Offer)

**タイミング**: ゲーム状態20 (PLAY1)

#### 送信メッセージ

```python
def make_offer(self, give_resources: dict, get_resources: dict):
    """他のプレイヤーに交易を提案"""
    msg = build_message(
        "MAKEOFFER",
        game=self.current_game,
        # リソースの詳細を追加
    )
    write_java_utf(self.sock, msg)
```

**注意**: 交易提案の詳細な実装は、プレイヤー間の交渉が必要なため、ボットでは通常使用されません。

---

## ターン終了

### アクション: ENDTURN

**タイミング**: ゲーム状態20 (PLAY1) で、これ以上アクションを実行しない時

### 送信メッセージ

```python
def end_turn(self):
    """ターンを終了"""
    msg = build_message("ENDTURN", game=self.current_game)
    write_java_utf(self.sock, msg)
```

**メッセージ形式**:
```
ENDTURN:game=test
```

### 受信メッセージ

```
← CLEAROFFER:game=test|playerNumber=-1
← TURN:game=test|playerNumber=2|gameState=15
```

**次のプレイヤー**: `TURN`メッセージで次のプレイヤーのターンが開始されます。

---

## 盗賊移動

### アクション: MOVEROBBER

**タイミング**: ゲーム状態33 (PLACING_ROBBER) の時

### 送信メッセージ

```python
def move_robber(self, hex_coord: int):
    """盗賊を移動"""
    msg = build_message("MOVEROBBER", game=self.current_game, coord=str(hex_coord))
    write_java_utf(self.sock, msg)
```

**メッセージ形式**:
```
MOVEROBBER:game=test|coord=70a
```

### 受信メッセージ (プレイヤーから奪える場合)

```
← MOVEROBBER:game=test|coord=70a|pn=3
← GAMESTATE:game=test|state=51  // WAITING_FOR_ROBBER_OR_PIRATE
← CHOOSEPLAYERREQUEST:game=test|choices=1,2
```

**次のアクション**: `CHOOSEPLAYERREQUEST`を受信したら、`CHOOSEPLAYER`で奪うプレイヤーを選択

### プレイヤー選択

```python
def choose_player(self, player_num: int):
    """奪うプレイヤーを選択"""
    msg = build_message("CHOOSEPLAYER", game=self.current_game, choice=str(player_num))
    write_java_utf(self.sock, msg)
```

**メッセージ形式**:
```
CHOOSEPLAYER:game=test|choice=2
```

### 受信メッセージ

```
← PLAYERELEMENT:game=test|playerNum=3|actionType=GAIN|elementType=1|amount=1
← PLAYERELEMENT:game=test|playerNum=2|actionType=LOSE|elementType=1|amount=1
← GAMESTATE:game=test|state=20  // PLAY1
```

---

## カード破棄

### アクション: DISCARD

**タイミング**: ゲーム状態50 (WAITING_FOR_DISCARDS) で`DISCARDREQUEST`を受信した時

### 受信メッセージ

```
← DISCARDREQUEST:game=test|numDiscards=4
```

### 送信メッセージ

```python
def discard_cards(self, clay=0, ore=0, sheep=0, wheat=0, wood=0):
    """カードを破棄（合計はnumDiscardsと一致する必要がある）"""
    msg = build_message(
        "DISCARD",
        game=self.current_game,
        resources=f"clay={clay}|ore={ore}|sheep={sheep}|wheat={wheat}|wood={wood}|unknown=0"
    )
    write_java_utf(self.sock, msg)
```

**メッセージ形式例** (粘土2枚、羊2枚を破棄):
```
DISCARD:game=test|resources=clay=2|ore=0|sheep=2|wheat=0|wood=0|unknown=0
```

### 受信メッセージ

```
← DISCARD:game=test|resources=clay=2|ore=0|sheep=2|wheat=0|wood=0|unknown=0|pn=3
← PLAYERELEMENTS:game=test|playerNum=3|actionType=LOSE|e1=2,e3=2
```

すべてのプレイヤーが破棄を完了すると：
```
← GAMESTATE:game=test|state=33  // PLACING_ROBBER
```

---

## 完全な実装例

以下は、上記のアクションを統合した完全な実装例です：

```python
from utils import write_java_utf, build_message

class JSettlersBot:
    def __init__(self, host, port, nickname, cookie, agent):
        self.host = host
        self.port = port
        self.nickname = nickname
        self.cookie = cookie
        self.agent = agent
        self.sock = None
        self.current_game = None
        self.my_player_number = -1
        
    # サイコロを振る
    def roll_dice(self):
        msg = build_message("ROLLDICE", game=self.current_game)
        write_java_utf(self.sock, msg)
    
    # 道路建設（2段階）
    def build_road(self, coord: int):
        # ステップ1: 建設リクエスト
        msg = build_message("BUILDREQUEST", game=self.current_game, pieceType="0")
        write_java_utf(self.sock, msg)
        # 注: GAMESTATE:state=30を待ってから以下を実行
        
    def place_road(self, coord: int):
        # ステップ2: 配置
        msg = build_message(
            "PUTPIECE",
            game=self.current_game,
            playerNumber=str(self.my_player_number),
            pieceType="0",
            coord=str(coord)
        )
        write_java_utf(self.sock, msg)
    
    # 集落建設（2段階）
    def build_settlement(self, coord: int):
        msg = build_message("BUILDREQUEST", game=self.current_game, pieceType="1")
        write_java_utf(self.sock, msg)
        
    def place_settlement(self, coord: int):
        msg = build_message(
            "PUTPIECE",
            game=self.current_game,
            playerNumber=str(self.my_player_number),
            pieceType="1",
            coord=str(coord)
        )
        write_java_utf(self.sock, msg)
    
    # 都市建設（2段階）
    def build_city(self, coord: int):
        msg = build_message("BUILDREQUEST", game=self.current_game, pieceType="2")
        write_java_utf(self.sock, msg)
        
    def place_city(self, coord: int):
        msg = build_message(
            "PUTPIECE",
            game=self.current_game,
            playerNumber=str(self.my_player_number),
            pieceType="2",
            coord=str(coord)
        )
        write_java_utf(self.sock, msg)
    
    # 開発カード購入
    def buy_dev_card(self):
        msg = build_message("BUYDEVCARDREQUEST", game=self.current_game)
        write_java_utf(self.sock, msg)
    
    # 騎士カード使用
    def play_knight(self):
        msg = build_message("PLAYDEVCARDREQUEST", game=self.current_game, devCard="5")
        write_java_utf(self.sock, msg)
    
    # 盗賊移動
    def move_robber(self, hex_coord: str):
        msg = build_message("MOVEROBBER", game=self.current_game, coord=hex_coord)
        write_java_utf(self.sock, msg)
    
    # プレイヤー選択（盗賊で奪う）
    def choose_player(self, player_num: int):
        msg = build_message("CHOOSEPLAYER", game=self.current_game, choice=str(player_num))
        write_java_utf(self.sock, msg)
    
    # カード破棄
    def discard_cards(self, clay=0, ore=0, sheep=0, wheat=0, wood=0):
        resources = f"clay={clay}|ore={ore}|sheep={sheep}|wheat={wheat}|wood={wood}|unknown=0"
        msg = build_message("DISCARD", game=self.current_game, resources=resources)
        write_java_utf(self.sock, msg)
    
    # ターン終了
    def end_turn(self):
        msg = build_message("ENDTURN", game=self.current_game)
        write_java_utf(self.sock, msg)
```

---

## ゲーム状態とアクションのマッピング

| ゲーム状態 | 状態名 | 可能なアクション |
|----------|--------|----------------|
| 15 | ROLL_OR_CARD | ROLLDICE, PLAYDEVCARDREQUEST |
| 20 | PLAY1 | BUILDREQUEST, PUTPIECE, BUYDEVCARDREQUEST, PLAYDEVCARDREQUEST, BANKTRADE, MAKEOFFER, ENDTURN |
| 30 | PLACING_ROAD | PUTPIECE (pieceType=0) |
| 31 | PLACING_SETTLEMENT | PUTPIECE (pieceType=1) |
| 32 | PLACING_CITY | PUTPIECE (pieceType=2) |
| 33 | PLACING_ROBBER | MOVEROBBER |
| 40 | PLACING_FREE_ROAD1 | PUTPIECE (pieceType=0) |
| 41 | PLACING_FREE_ROAD2 | PUTPIECE (pieceType=0) |
| 50 | WAITING_FOR_DISCARDS | DISCARD |
| 51 | WAITING_FOR_ROB_CHOOSE_PLAYER | CHOOSEPLAYER |
| 52 | WAITING_FOR_DISCOVERY | PICKRESOURCES |
| 53 | WAITING_FOR_MONOPOLY | PICKRESOURCETYPE |

---

## トラブルシューティング

### 問題1: BUILDREQUESTの後にPUTPIECEが拒否される

**原因**: `GAMESTATE`メッセージを待たずに`PUTPIECE`を送信している

**解決方法**: `GAMESTATE:state=30`（または31、32）を受信してから`PUTPIECE`を送信

```python
def handle_message(self, message):
    parsed = parse_message(message)
    
    if parsed["type"] == "GAMESTATE":
        state = int(parsed.get("state", 0))
        
        if state == 30:  # PLACING_ROAD
            # ここで道路を配置
            self.place_road(self.next_coord)
```

### 問題2: リソース不足でアクションが拒否される

**原因**: リソースを確認せずにアクションを実行している

**解決方法**: アクション前にリソースを確認

```python
def can_build_road(self):
    """道路を建設できるか確認"""
    return (self.game_state.my_resources['clay'] >= 1 and
            self.game_state.my_resources['wood'] >= 1)

if self.can_build_road():
    self.build_road(coord)
```

### 問題3: 開発カードが使用できない

**原因**: すでに今ターン開発カードを使用している、または購入したターンに使用しようとしている

**解決方法**: `PLAYERELEMENT:elementType=19`（PLAYED_DEV_CARD_FLAG）を確認

---

## 参考資料

- **Message-Sequences-for-Game-Actions.md**: 完全なメッセージシーケンスの詳細（英語）
- **examples/python-bot/jsettlers_bot.py**: 実装例
- **src/main/java/soc/message/**: Javaのメッセージクラス定義

---

## まとめ

このガイドでは、JSettlers Pythonボットから各ゲームアクションを実行する方法を説明しました。

**重要なポイント**:
1. 建設アクションは`BUILDREQUEST` → `GAMESTATE` → `PUTPIECE`の順序
2. 開発カードは`PLAYDEVCARDREQUEST` → `GAMESTATE` → 追加アクション
3. 各アクションの後は`GAMESTATE`メッセージを待つ
4. リソースとゲーム状態を常に確認

詳細なメッセージシーケンスについては、[Message-Sequences-for-Game-Actions.md](Message-Sequences-for-Game-Actions.md)を参照してください。
