# JSettlers ロボットの行動ルール

このドキュメントでは、JSettlersに組み込まれているロボット（AI）の行動ルールを包括的にまとめています。

## 目次

1. [概要](#概要)
2. [ロボットの構造](#ロボットの構造)
3. [初期配置戦略](#初期配置戦略)
4. [通常ターンの意思決定フロー](#通常ターンの意思決定フロー)
5. [建設計画の立案](#建設計画の立案)
6. [リソース獲得戦略](#リソース獲得戦略)
7. [開発カードの使用判断](#開発カードの使用判断)
8. [交易戦略](#交易戦略)
9. [盗賊配置戦略](#盗賊配置戦略)
10. [カード破棄戦略](#カード破棄戦略)
11. [独占カード戦略](#独占カード戦略)
12. [パラメータとチューニング](#パラメータとチューニング)
13. [制限事項と制約](#制限事項と制約)

---

## 概要

JSettlersのロボットAIは以下の主要コンポーネントで構成されています：

- **SOCRobotBrain**: メインの思考エンジン、ゲームループとメッセージ処理
- **SOCRobotDM (Decision Maker)**: 建設計画の立案と優先順位決定
- **SOCPlayerTracker**: 他プレイヤーの予測と追跡
- **SOCRobotNegotiator**: 交易の提案と応答
- **各種Strategy**: 盗賊、独占、カード破棄など特定状況の戦略

### 基本的な動作原理

1. **メッセージ駆動**: サーバーからのメッセージに反応して行動
2. **計画ベース**: 毎ターン建設計画（buildingPlan）を立てて実行
3. **状態管理**: 「待機中」フラグ（expectPLACING_ROAD等）で次の行動を制御
4. **タイムアウト**: 一定時間後に自動的にターン終了

---

## ロボットの構造

### 主要クラスの役割

#### SOCRobotBrain
- **役割**: ロボットのメインスレッド、すべての意思決定の中心
- **主要メソッド**:
  - `run()`: メインループ、メッセージ受信と処理
  - `planBuilding()`: 建設計画の立案
  - `planAndDoActionForPLAY1()`: 通常ターンのアクション実行
  - `buildOrGetResourceByTradeOrCard()`: リソース獲得または建設実行

#### SOCRobotDM (Decision Maker)
- **役割**: 何を建設するかの決定
- **主要メソッド**:
  - `planStuff(int strategyType)`: 建設計画の作成
  - `scorePossibleSettlements()`: 集落候補地のスコアリング
  - `scoreRoadsOrShips()`: 道路/船のスコアリング

#### SOCPlayerTracker
- **役割**: プレイヤーの状態追跡と予測
- **機能**:
  - 各プレイヤーの勝利点予測
  - 建設可能な場所の追跡
  - 最長交易路/最大騎士力の予測

#### Strategy クラス群
- **OpeningBuildStrategy**: 初期配置の決定
- **RobberStrategy**: 盗賊配置の決定
- **MonopolyStrategy**: 独占カードの使用判断
- **DiscardStrategy**: カード破棄の選択

---

## 初期配置戦略

### 第1集落の配置（OpeningBuildStrategy.planInitialSettlements）

#### 評価基準
1. **リソースの多様性**: 5種類のリソースをバランスよく獲得
2. **ダイスの出目確率**: 6と8が最良、2と12が最悪
3. **港へのアクセス**: 3:1港や2:1専門港が近い位置を優先
4. **拡張性**: 将来的な建設場所が多い位置

#### スコアリング計算
```
集落スコア = (リソース確率の合計) × (多様性ボーナス) + (港ボーナス)
```

**リソース確率**:
- 各隣接ヘックスのダイス目の確率を合計
- 6と8: 確率16.7%（5/36）
- 5と9: 確率11.1%（4/36）
- 4と10: 確率8.3%（3/36）
- 3と11: 確率5.6%（2/36）
- 2と12: 確率2.8%（1/36）

**多様性ボーナス**:
- 5種類すべて獲得可能: 大幅ボーナス
- 4種類: 中程度ボーナス
- 3種類以下: ボーナスなし

**港ボーナス**:
- 2:1専門港に隣接: +0.5
- 3:1汎用港に隣接: +0.3

### 第2集落の配置

#### 戦略の違い
- **SMART_STRATEGY**: バランス重視、第1集落で不足しているリソースを補完
- **FAST_STRATEGY**: 最高スコアの場所を選択、速度重視

#### 考慮事項
1. 第1集落との距離（最低2ノード離れる必要がある）
2. リソースの補完性
3. 拡張ルートの確保

### 初期道路の配置（planInitRoad）

#### 優先順位
1. **将来の集落候補地へのルート**: 2ノード先の良い集落位置に向かう
2. **港へのアクセス**: 港に近づく方向
3. **最長交易路の基礎**: 長いルートを作れる方向

---

## 通常ターンの意思決定フロー

### ターン開始時（SOCMessage.TURN受信）

1. **状態リセット**:
   - 建設計画のクリア
   - 交易フラグのリセット
   - 失敗カウンターのリセット
   - 待機フラグのクリア

2. **初期化**:
   - `expectROLL_OR_CARD = true`
   - `waitingForOurTurn = false`
   - `doneTrading = false`（交易が有効な場合）

### サイコロロールフェーズ（ROLL_OR_CARD状態）

#### 判断順序
1. **騎士カードの使用判断**（hasPlayedDevCard == false の場合）
   - 最大騎士力を獲得できる場合: 使用
   - シナリオ_SC_PIRI: 船を戦艦に変換できる場合使用

2. **サイコロを振る**
   - 一定時間待機後、自動的にロール

### メインアクションフェーズ（PLAY1状態）

#### planAndDoActionForPLAY1の実行フロー

```
1. 騎士カードの使用判断（まだ使用していない場合）
   └─> playKnightCardIfShould()

2. 建設計画の立案（計画が空で、リソースが2以上）
   └─> planBuilding()
       └─> decisionMaker.planStuff(strategyType)

3. 計画の実行または リソース獲得
   └─> buildOrGetResourceByTradeOrCard()
       ├─> 道路建設カードの使用判断
       ├─> 豊作カードの使用判断
       ├─> 独占カードの使用判断
       ├─> プレイヤー間交易の提案
       ├─> 銀行/港交易の実行
       └─> 建設リクエストの送信

4. シナリオ固有のアクション
   └─> considerScenarioTurnFinalActions()

5. ターン終了判断
   └─> endTurnActions()
```

---

## 建設計画の立案

### planStuff メソッドの詳細（SOCRobotDM.planStuff）

#### ステップ1: 現状分析

```java
// 各プレイヤーの状態を更新
for (SOCPlayerTracker tracker : playerTrackers) {
    tracker.updateWinGameETAs();
}

// 自分の勝利までのETA（Estimated Time to Arrival）を計算
// ETA = 必要な勝利点を獲得するまでのターン数推定
```

#### ステップ2: 建設可能なピースのスコアリング

**評価される建設物**:
1. 集落 (Settlement)
2. 都市 (City)
3. 道路/船 (Road/Ship)
4. 開発カード (Development Card)

**スコアリング要素**:

##### 集落のスコア
```
集落スコア = リソース生産性 + 拡張性 + 戦略的価値

要素:
- リソース生産性: 隣接ヘックスの期待値
- 港へのアクセス: 2:1港 > 3:1港
- 将来の都市化可能性
- 他プレイヤーの妨害度（adversarial factor）
```

##### 都市のスコア
```
都市スコア = 現集落のリソース生産性 × 2 + 勝利点

判断基準:
- リソース生産量が高い集落を優先
- 勝利が近い場合、勝利点獲得を優先
```

##### 道路/船のスコア
```
道路スコア = 将来の集落へのルート価値 + 最長交易路への貢献

判断基準:
- 良い集落候補地への最短ルート
- 最長交易路の獲得可能性
- 他プレイヤーの妨害
```

##### 開発カードのスコア
```
カードスコア = (期待される利益) × devCardMultiplier

利益:
- 騎士カード: 最大騎士力 + 盗賊による妨害
- 勝利点カード: 直接1点
- 進歩カード: リソース獲得または建設加速
```

#### ステップ3: 優先順位の決定

**戦略タイプによる違い**:

##### SMART_STRATEGY（デフォルト）
1. 勝利条件への最短ルートを計算
2. 他プレイヤーの脅威を考慮
3. バランスの取れた発展を重視

```
優先順位の決定:
if (勝利まで2ターン以内) {
    最速で10点到達する計画
} else if (他プレイヤーが勝利に近い) {
    妨害 + 自分の発展
} else {
    効率的なリソース基盤の構築
}
```

##### FAST_STRATEGY
1. 最高スコアの選択肢を即座に選択
2. 長期計画よりも短期利益を優先
3. 計算時間の短縮

#### ステップ4: 建設計画（buildingPlan）の作成

```
buildingPlan は Stack<SOCPossiblePiece> 型:

例: 集落を建設する計画
Stack: [道路1, 道路2, 集落]
      ^最初に建設  ^最後に建設

実行時は pop() で取り出して順番に建設
```

---

## リソース獲得戦略

### buildOrGetResourceByTradeOrCard の詳細

#### 判断の優先順位

```
1. 道路建設カードの使用
   条件:
   - 開発カードを今ターンまだ使用していない
   - 道路建設カードを所持
   - 建設計画の上位2つが道路
   - 道路が2本以上残っている

2. 豊作カード（Year of Plenty）の使用
   条件:
   - 開発カードを今ターンまだ使用していない
   - 豊作カードを所持
   - 必要なリソースが2種類以上不足
   
   リソース選択:
   - 建設目標に必要なリソースを優先
   - chooseFreeResourcesIfNeeded() で自動選択

3. 独占カード（Monopoly）の使用
   条件:
   - 開発カードを今ターンまだ使用していない
   - 独占カードを所持
   - monopolyStrategy.decidePlayMonopoly() が true
   
   リソース選択:
   - 他プレイヤーが最も多く持っているリソース
   - 自分が最も必要としているリソース
   - これらのバランスで決定

4. プレイヤー間交易の提案
   条件:
   - robotParameters.getTradeFlag() == 1
   - まだ交易していない (doneTrading == false)
   - 目標リソースを持っていない
   - 拒否回数が MAX_DENIED_PLAYER_TRADES_PER_TURN 未満
   
   交易内容:
   - makeOffer() で提案内容を計算
   - 必要なリソース vs 余剰リソース
   - 公平な交換レートを提案

5. 銀行/港交易の実行
   条件:
   - プレイヤー間交易が完了または失敗
   - 必要なリソースがある
   - 交換レートが許容範囲内
   
   交易パターン:
   - 4:1 汎用交易（基本）
   - 3:1 港交易（3:1港を所持）
   - 2:1 専門港交易（特定リソースの2:1港）

6. 建設リクエストの送信
   条件:
   - 必要なリソースをすべて所持
   - 建設計画の先頭のピースを建設可能
   
   送信メッセージ:
   - BUILDREQUEST または PUTPIECE
   - waitingForGameState = true
   - expectPLACING_* フラグをセット
```

### リソース不足時の対処

```
リソース獲得の試行回数制限:
- 銀行交易失敗: MAX_DENIED_BANK_TRADES_PER_TURN (9回)
- プレイヤー交易拒否: MAX_DENIED_PLAYER_TRADES_PER_TURN (9回)
- 建設リクエスト拒否: MAX_DENIED_BUILDING_PER_TURN (3回)

制限到達時の処理:
- doneTrading = true をセット
- 建設計画をクリア
- ターンを終了
```

---

## 開発カードの使用判断

### 騎士カード (Knight/Soldier)

#### 使用条件（playKnightCardIfShould）

```
使用する場合:
1. 最大騎士力を獲得できる場合
   - 現在のリーダーの騎士数 <= 自分の騎士数
   - または、最大騎士力ボーナスがまだ誰も獲得していない
   
2. シナリオ_SC_PIRI の場合
   - 船を戦艦に変換できる
   - 他プレイヤーがリソースを持っている
   - 自分の船が変換可能位置にある

使用しない場合:
- 今ターンすでに開発カードを使用済み
- 勝利がすぐそこで、他の行動を優先すべき
- 盗賊配置が自分に不利な状況を生む
```

### 豊作カード (Year of Plenty/Discovery)

#### 使用判断（chooseFreeResourcesIfNeeded）

```
リソース選択アルゴリズム:
1. 建設目標に必要なリソースをリストアップ
2. 現在不足しているリソースを特定
3. 不足量が最も大きいリソースから2つ選択

例:
目標: 集落建設 (木1, 粘土1, 羊1, 小麦1)
所持: 木0, 粘土1, 羊0, 小麦0
選択: 木1, 羊1 （または木1, 小麦1）
```

### 独占カード (Monopoly)

#### 使用判断（MonopolyStrategy.decidePlayMonopoly）

```java
boolean decidePlayMonopoly() {
    // 1. 各リソースについて、獲得予想量を計算
    for (resourceType : allResourceTypes) {
        expectedGain[resourceType] = 
            他プレイヤーの所持量推定の合計
    }
    
    // 2. 自分の必要度を計算
    for (resourceType : allResourceTypes) {
        need[resourceType] = 
            建設目標に必要な量 - 現在の所持量
    }
    
    // 3. スコアリング
    bestScore = -1
    for (resourceType : allResourceTypes) {
        score = expectedGain[resourceType] * need[resourceType]
        if (score > bestScore) {
            bestResource = resourceType
            bestScore = score
        }
    }
    
    // 4. 使用判断
    return (bestScore > threshold)
}
```

**使用基準**:
- 獲得予想量が3枚以上
- かつ、そのリソースが建設に必要
- または、獲得予想量が5枚以上（無条件で使用価値あり）

### 道路建設カード (Road Building)

#### 使用判断

```
使用条件:
1. 建設計画の上位2つが道路または船
2. 道路/船が2本以上残っている
3. 今ターン開発カードを未使用
4. 以前に拒否されていない

配置戦略:
- 計画された道路を順番に配置
- 1本目配置後、expectPLACING_FREE_ROAD1 = true
- 2本目配置後、expectPLACING_FREE_ROAD2 = true
- 最長交易路獲得を狙う場合もある
```

---

## 交易戦略

### プレイヤー間交易（SOCRobotNegotiator）

#### 交易提案の作成（makeOffer）

```java
// 提案内容の決定
void makeOffer(SOCBuildingPlan plan) {
    // 1. 目標リソースの特定
    SOCResourceSet targetResources = plan.getFirstPiece().getResourcesToBuild();
    SOCResourceSet ourResources = ourPlayerData.getResources();
    
    // 2. 不足リソースと余剰リソースの計算
    SOCResourceSet needed = targetResources - ourResources;
    SOCResourceSet surplus = ourResources - targetResources;
    
    // 3. 交易提案の構築
    offer.give = surplus（一部）
    offer.get = needed（一部）
    
    // 4. レート調整
    // - 1:1 は理想的だが稀
    // - 2:1 や 1:2 が一般的
    // - 状況により 3:1 や 1:3 も検討
}
```

#### 交易応答の判断（considerOffer）

```java
boolean considerOffer(SOCTradeOffer offer) {
    // 1. 提供リソースが現在の目標に必要か？
    if (!offer.getGetResourceSet().contains(ourTargetResources)) {
        return false; // 不要なリソースの提供
    }
    
    // 2. 要求リソースを渡せるか？
    if (!ourPlayerData.getResources().contains(offer.getGiveResourceSet())) {
        return false; // 所持していない
    }
    
    // 3. 交易レートは妥当か？
    float rate = offer.getGiveResourceSet().getTotal() / 
                 offer.getGetResourceSet().getTotal();
    if (rate > acceptableRate) {
        return false; // レートが悪すぎる
    }
    
    // 4. 他プレイヤーを有利にしすぎないか？
    if (wouldHelpOpponentWin(offer)) {
        return false; // 相手を勝たせる可能性
    }
    
    return true; // 受け入れる
}
```

#### 人間プレイヤーへの配慮

```
BOTS_PAUSE_FOR_HUMAN_TRADE = 8秒

人間が交易に参加している場合:
- ボットは8秒待ってから応答
- 人間プレイヤーに応答の機会を与える
- タイムアウト: TRADE_RESPONSE_TIMEOUT_SEC_HUMANS = 30秒

ボットのみの場合:
- すぐに応答
- タイムアウト: TRADE_RESPONSE_TIMEOUT_SEC_BOTS_ONLY = 5秒
```

### 銀行/港交易

#### 交易実行の判断

```java
boolean shouldBankTrade(SOCResourceSet target) {
    // 1. 交易可能なリソースのチェック
    for (resourceType : ourPlayerData.getResources()) {
        // 2. 交易レートの確認
        int tradeRate = getTradeRate(resourceType);
        // 4:1 (基本), 3:1 (港), 2:1 (専門港)
        
        if (ourPlayerData.getResources().getAmount(resourceType) >= tradeRate) {
            // 3. 必要なリソースへの交換価値を計算
            if (target.contains(desiredResource)) {
                return true; // 交易実行
            }
        }
    }
    return false;
}
```

#### 交易の優先順位

```
1. 2:1 専門港（最も効率的）
2. 3:1 汎用港
3. 4:1 銀行交易（最終手段）

交易するリソースの選択:
- 余剰リソース（目標に不要）を優先
- 生産量が多いリソース
- 将来も獲得しやすいリソース
```

---

## 盗賊配置戦略

### RobberStrategy.getBestRobberHex

#### 評価基準

```java
int scoreRobberHex(int hexCoord, SOCPlayer victim) {
    int score = 0;
    
    // 1. ヘックスの生産性
    score += hexProductivity(hexCoord);
    // - ダイス目の確率（6,8 > 5,9 > 4,10 > 3,11 > 2,12）
    // - リソースタイプの希少性
    
    // 2. 被害者の選択
    if (victim != null) {
        // リーダーを妨害
        if (victim == gameLeader) {
            score += leaderAdversarialFactor; // × 3.0
        }
        
        // 脅威となるプレイヤーを妨害
        if (victim.getTotalVP() >= 7) {
            score += adversarialFactor; // × 1.5
        }
        
        // 被害者のリソース量
        score += victim.getResources().getTotal() * 0.1;
    }
    
    // 3. 自分への影響を回避
    if (affectsOurSettlements(hexCoord)) {
        score -= 10; // 自分の集落に影響する場合は大幅減点
    }
    
    return score;
}
```

#### 配置手順

```
1. すべての陸地ヘックスを評価
2. 各ヘックスについて、影響を受けるプレイヤーを特定
3. スコアが最も高いヘックスを選択
4. そのヘックスで最も影響を受けるプレイヤーから奪う
```

#### 特殊ケース

```
シナリオ_SC_PIRI（海賊）:
- 海ヘックスに配置
- 船の航路を妨害
- 陸地の盗賊とは別ルール

7の目が出た場合:
- moveRobberOnSeven = true フラグ
- 必ず盗賊を移動
- 他プレイヤーからリソースを奪う
```

---

## カード破棄戦略

### DiscardStrategy.discard

#### 破棄するカードの選択アルゴリズム

```java
SOCResourceSet chooseDiscard(int numToDiscard) {
    SOCResourceSet toDiscard = new SOCResourceSet();
    SOCResourceSet ourResources = ourPlayerData.getResources();
    
    // 1. 各リソースの価値を計算
    Map<Integer, Float> resourceValue = new HashMap<>();
    for (resourceType : ALL_RESOURCES) {
        float value = 0;
        
        // 現在の建設計画で必要か？
        if (buildingPlan.needs(resourceType)) {
            value += 5.0; // 必要なリソースは高価値
        }
        
        // 生産レート
        value += ourPlayerData.getResourceRollStats(resourceType) * 2.0;
        
        // 港の所有
        if (has2to1Port(resourceType)) {
            value += 1.0; // 2:1港があれば価値アップ
        }
        
        resourceValue.put(resourceType, value);
    }
    
    // 2. 価値の低い順にソート
    List<ResourceType> sortedByValue = sortByValue(resourceValue);
    
    // 3. 価値の低いリソースから破棄
    for (resourceType : sortedByValue) {
        int available = ourResources.getAmount(resourceType);
        int toTake = Math.min(available, numToDiscard - toDiscard.getTotal());
        
        toDiscard.add(toTake, resourceType);
        
        if (toDiscard.getTotal() >= numToDiscard) {
            break;
        }
    }
    
    return toDiscard;
}
```

#### 破棄の優先順位

```
破棄する優先順位（低い方から）:
1. 建設計画に不要なリソース
2. 生産レートが高い（すぐ補充できる）リソース
3. 2:1港を持っているリソース（交換しやすい）
4. 所持量が多いリソース

保持する優先順位（高い方から）:
1. 建設計画に必要なリソース
2. 希少なリソース（生産レートが低い）
3. 港を持っていないリソース
4. 勝利に直結するリソース（都市建設用の鉱石・小麦）
```

---

## 独占カード戦略

### MonopolyStrategy の詳細

#### リソース選択の計算

```java
int chooseMonopolyResource() {
    int bestResource = -1;
    int bestScore = 0;
    
    for (resourceType : ALL_RESOURCES) {
        // 1. 他プレイヤーの所持量を推定
        int estimatedGain = 0;
        for (player : otherPlayers) {
            estimatedGain += estimateResourceAmount(player, resourceType);
        }
        
        // 2. 自分の必要度を計算
        int need = 0;
        if (buildingPlan.needs(resourceType)) {
            need = buildingPlan.getNeededAmount(resourceType);
        }
        
        // 3. スコア計算
        int score = estimatedGain * (1 + need);
        
        // 4. 調整
        // 少量しか獲得できない場合は減点
        if (estimatedGain < 3) {
            score = score / 2;
        }
        
        // 生産しやすいリソースは若干減点
        if (highProductionRate(resourceType)) {
            score = score * 0.9;
        }
        
        if (score > bestScore) {
            bestScore = score;
            bestResource = resourceType;
        }
    }
    
    return bestResource;
}
```

#### 使用判断基準

```
独占カードを使用する条件:
1. 推定獲得量が3枚以上
2. そのリソースが建設に必要
3. 他の方法（交易）では獲得困難

使用しない場合:
1. 獲得予想量が2枚以下
2. そのリソースが不要
3. 勝利直前で他の開発カードを優先
```

---

## パラメータとチューニング

### SOCRobotParameters

ロボットの行動をカスタマイズできる主要パラメータ:

```java
public class SOCRobotParameters {
    // 交易に関する設定
    int tradeFlag;  // 0: 交易しない, 1: 交易する
    
    // 戦略タイプ
    int strategyType;  // 0: SMART_STRATEGY, 1: FAST_STRATEGY
    
    // 建設の優先度調整
    float maxGameLength;        // ゲーム長の想定（デフォルト: 300ターン）
    float maxETA;               // ETA計算の最大値
    float etaBonusFactor;       // 早期完成ボーナス (0.8)
    float adversarialFactor;    // 妨害重視度 (1.5)
    float leaderAdversarialFactor;  // リーダー妨害重視度 (3.0)
    float devCardMultiplier;    // 開発カード価値倍率 (2.0)
    float threatMultiplier;     // 脅威評価倍率 (1.1)
}
```

### チューニング定数

#### タイミング関連
```java
// ボット専用ゲームでの高速化倍率
BOTS_ONLY_FAST_PAUSE_FACTOR = 0.25;  // 通常の1/4の待機時間

// 6人プレイで常に高速化
ALWAYS_PAUSE_FASTER = false;  // デフォルトは無効

// 人間との交易待機時間
BOTS_PAUSE_FOR_HUMAN_TRADE = 8秒;

// 交易応答タイムアウト
TRADE_RESPONSE_TIMEOUT_SEC_HUMANS = 30秒;      // 人間参加時
TRADE_RESPONSE_TIMEOUT_SEC_BOTS_ONLY = 5秒;   // ボットのみ
```

#### 制限値
```java
// ターンごとの失敗許容回数
MAX_DENIED_BUILDING_PER_TURN = 3;        // 建設拒否
MAX_DENIED_BANK_TRADES_PER_TURN = 9;     // 銀行交易拒否
MAX_DENIED_PLAYER_TRADES_PER_TURN = 9;   // プレイヤー交易拒否
```

#### 評価係数（SOCRobotDM）
```java
etaBonusFactor = 0.8;           // 早期完成ボーナス
adversarialFactor = 1.5;        // 通常の妨害重視度
leaderAdversarialFactor = 3.0;  // リーダーへの妨害重視度
devCardMultiplier = 2.0;        // 開発カード価値倍率
threatMultiplier = 1.1;         // 脅威認識倍率
```

---

## 制限事項と制約

### 実装上の制限

#### 1. 計算時間の制限
```
- 各決定は数秒以内に完了する必要がある
- 深い探索木は使用できない（ゲームが遅延する）
- ヒューリスティックベースの評価
```

#### 2. 情報の制約
```
完全情報:
- 盤面の状態（道路、集落、都市の位置）
- 各プレイヤーの勝利点
- 公開情報（最長交易路、最大騎士力）

不完全情報:
- 他プレイヤーの手札（推定のみ）
- 他プレイヤーの開発カード（一部推定）
- 将来のサイコロの目
```

#### 3. 交易の制約
```
制限:
- 複雑な交渉は不可（カウンターオファーは1回のみ）
- 将来の交易約束は不可
- 3者以上の交易は不可

実装:
- シンプルな1:1, 2:1, 1:2 の交換を提案
- 公平なレートでの提案
- 相手の状況を考慮した提案
```

#### 4. 長期計画の制約
```
- 2-3手先の計画が限界
- 複雑な条件分岐を含む計画は困難
- 動的な状況変化への適応が主
```

### 既知の弱点

#### 1. 序盤の配置
```
弱点:
- 機械的なスコアリングに依存
- 他プレイヤーの戦略を予測しない
- 港の価値を過小評価することがある

改善の余地:
- より動的な評価
- 相手の配置を見て調整
- ゲーム全体の流れを予測
```

#### 2. 交易の積極性
```
弱点:
- 保守的な交易判断
- 有利な交易機会を逃すことがある
- カウンターオファーが限定的

改善の余地:
- より柔軟な交易判断
- 複数回の交渉
- 戦略的な交易提案
```

#### 3. 盗賊の使用
```
弱点:
- 単純なスコアリング
- 長期的な妨害効果を考慮しない
- 心理的要素（威嚇）を使えない

改善の余地:
- より戦略的な配置
- 連続的な妨害計画
- タイミングの最適化
```

#### 4. 開発カードの使用
```
弱点:
- 決まったパターンで使用
- 騎士カードのタイミングが単純
- ブラフや心理戦が不可

改善の余地:
- より柔軟なタイミング
- 状況に応じた判断
- 複数カードの連携使用
```

---

## 拡張とカスタマイズ

### カスタムボットの作成方法

#### 1. SOCRobotBrain を継承
```java
public class MyCustomBrain extends SOCRobotBrain {
    public MyCustomBrain(SOCRobotClient rc, SOCRobotParameters params,
                         SOCGame ga, CappedQueue mq) {
        super(rc, params, ga, mq);
    }
    
    @Override
    protected void planBuilding() {
        // カスタム建設計画ロジック
        super.planBuilding();  // または完全に置き換え
    }
    
    @Override
    protected void buildOrGetResourceByTradeOrCard() {
        // カスタムリソース獲得ロジック
    }
}
```

#### 2. Strategy クラスを継承
```java
public class MyRobberStrategy extends RobberStrategy {
    @Override
    public int getBestRobberHex() {
        // カスタム盗賊配置ロジック
        return customHexChoice();
    }
}
```

#### 3. Factory メソッドのオーバーライド
```java
public class MyRobotClient extends SOCRobotClient {
    @Override
    public SOCRobotBrain createBrain(SOCRobotParameters params,
                                     SOCGame ga,
                                     CappedQueue mq) {
        return new MyCustomBrain(this, params, ga, mq);
    }
}
```

### デバッグとテスト

#### デバッグコマンド（ゲーム内）
```
プレイヤーがゲーム内で送信できるデバッグコマンド:

"*STATS*" - ロボットの統計情報を表示
"*PRINT*" - 現在の状態を出力
"*RESOURCES*" - リソース状態を表示
"*DEVCARD*" - 開発カード情報を表示

これらはSOCRobotClient.handleGAMETEXTMSG()で処理される
```

#### ログ出力
```java
// デバッグログの有効化
D.ebugPrintln("Your debug message");

// 詳細な脳の状態を出力
debugPrintBrainStatus(boolean includeResources);
```

---

## まとめ

### ロボットの特徴

**強み**:
1. 一貫した論理的判断
2. 高速な計算と応答
3. ミスのない基本プレイ
4. 公平な交易提案

**弱み**:
1. 予測可能なパターン
2. 柔軟性の欠如
3. 心理戦が不可
4. 複雑な長期戦略の欠如

### 学習のポイント

このロボットの行動ルールから学べること:
1. **優先順位付け**: 複数の選択肢を体系的に評価
2. **リソース管理**: 効率的な獲得と使用
3. **状態管理**: 複雑なゲーム状態の追跡
4. **適応性**: 状況に応じた戦略変更

### カスタマイズの指針

カスタムボットを作成する際の考慮点:
1. **計算時間**: ゲームの流れを妨げない
2. **公平性**: 他プレイヤーへの配慮
3. **堅牢性**: エラーハンドリング
4. **テスト**: 様々な状況での動作確認

---

## 参考資料

- **ソースコード**: `src/main/java/soc/robot/`
- **開発者向けドキュメント**: `Readme.developer.md`
- **メッセージシーケンス**: `doc/Message-Sequences-for-Game-Actions.md`
- **Python Bot Guide**: `doc/Python-Bot-Guide.ja.md`
- **Python Bot Actions Guide**: `doc/Python-Bot-Actions-Guide.ja.md`

このドキュメントは JSettlers 2.7.00 のコードベースに基づいています。
