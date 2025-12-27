# Answers to Problem Statement

## Question 1: How to add the specified number of internal bots when creating a game

### Answer: The server adds them automatically

The JSettlers server **automatically places internal bots in empty seats** when a game becomes ready. You don't need to explicitly request bots from the client side.

### Implementation

The code in the problem statement is already correct:

```python
def run(self, game_name, mode="create", num_robots=3, num_games=1):
    """Main loop"""
    
    # num_robots parameter is for tracking purposes
    self.target_num_robots = num_robots 
    
    if mode == "create":
        self.create_game(current_game_name)
    
    # Server automatically adds internal bots to remaining seats
```

### How it works

1. **Game creation**: Create game with message `1013`
2. **Seat reservation**: Python bot takes a seat
3. **Auto-placement**: Server detects empty seats and requests internal bots to join (sends message `1023`)
4. **Game start**: Game starts when all seats are filled

### Key points

- `num_robots` parameter is used for **tracking purposes** only
- Server automatically fills empty seats with available internal bots
- No special bot request processing needed on client side

## Question 2: How to make the bot sit in a valid seat without conflicting with internal bots

### Answer: Use automatic seat assignment

Specify `-1` for the seat number, and the server will automatically assign an available seat.

### Implementation

Current code (from problem statement):
```python
def sit_down(self, game_name: str):
    """Request to sit (1012)"""
    msg = f"1012|{game_name},-,0,true"  # Always seat 0 (problematic)
    write_java_utf(self.sock, msg)
```

**Recommended improvement**:
```python
def sit_down(self, game_name: str, preferred_seat: int = -1):
    """
    Request to sit in a seat (1012)
    
    Args:
        game_name: Game name
        preferred_seat: Preferred seat number (-1 = auto-assign)
    """
    print(f"🪑 Requesting to sit in game: {game_name}, seat: {preferred_seat}")
    
    msg = f"1012|{game_name},-,{preferred_seat},true"
    
    write_java_utf(self.sock, msg)
    print(f"→ {msg}")
```

### Usage

```python
# Use auto-assignment in message handler
elif msg_type == "1013": # JOINGAME - someone joined
    args = parsed.get("args", [])
    if len(args) >= 1:
        name = args[0]
        
        if name == self.nickname and self.player_id == -1:
            print("🚀 Join complete. Requesting auto-seat assignment...")
            # Specify -1 for auto-assignment
            self.sit_down(self.current_game, preferred_seat=-1)
```

### Why this works

1. **Timing**: Python bot joins right after game creation and secures a seat first
2. **Auto-assignment**: Using `-1` lets the server choose an available seat
3. **Conflict avoidance**: Server never assigns an already-taken seat
4. **Bot placement**: After Python bot secures seat, server places internal bots in remaining seats

## Question 3: Details about internal bot types

### Answer: Two strategy types exist

JSettlers has two types of internal bot strategies:

### 1. FAST_STRATEGY (Fast Strategy)

**Characteristics**:
- Faster but simpler AI
- Quick decisions with basic logic
- Simple construction and trading only

**Percentage**: About 70% of internal bots

**Example names**:
- `dumb01`
- `dumb02`
- `dumb03`
- (up to 30 bots)

**Implementation**:
```java
// src/main/java/soc/robot/SOCRobotDM.java
public static final int FAST_STRATEGY = 1;
```

**Strategy overview**:
- Build immediately when resources are available
- No complex calculations, uses simple rule-based decisions
- Finishes turns quickly

### 2. SMART_STRATEGY (Smart Strategy)

**Characteristics**:
- Smarter but slower AI
- Calculates Win Game ETA (estimated turns to victory)
- More complex decision-making

**Percentage**: About 30% of internal bots

**Example names**:
- `robot 1`
- `robot 2`
- `robot 3`
- (up to 30 bots)

**Implementation**:
```java
// src/main/java/soc/robot/SOCRobotDM.java
public static final int SMART_STRATEGY = 0;
```

**Strategy overview**:
- Calculates Win Game ETA (WinGameETA) and plans most efficient construction
- Considers other players' strategies
- Uses development cards and special strategies
- Takes more time to choose optimal moves

### Server configuration

Enable internal bots when starting server:

```bash
java -jar JSettlersServer.jar \
    -Djsettlers.bots.cookie=your_cookie \
    -Djsettlers.startrobots=7
```

Options:
- `-Djsettlers.bots.cookie`: Cookie for bot authentication
- `-Djsettlers.startrobots`: Number of bots to start (recommended: 7+)

### Bot selection logic

Server selects bots using this logic:

```java
// src/main/java/soc/server/SOCServer.java
// 30% will be "smart" robots, the other 70% will be "fast" robots.
final int fast30 = (int) (rcount * 0.70f);  // 70% FAST
boolean loadSuccess = setupLocalRobots(fast30, rcount - fast30);  // 30% SMART
```

### Bot assignment

When game starts, server randomly selects from available bots and places them in appropriate ratio (70% FAST, 30% SMART).

### Client-side control

**Important**: You **cannot** specify bot types from the client side. The server automatically selects them in the appropriate ratio.

## Summary

### Recommended changes

For the code in the problem statement, we recommend these changes:

1. **Improve `sit_down()` method**
   ```python
   def sit_down(self, game_name: str, preferred_seat: int = -1):
       msg = f"1012|{game_name},-,{preferred_seat},true"
       write_java_utf(self.sock, msg)
   ```

2. **Use auto-assignment in message handler**
   ```python
   if name == self.nickname and self.player_id == -1:
       self.sit_down(self.current_game, preferred_seat=-1)
   ```

3. **Initialize `player_id`**
   ```python
   def __init__(self, ...):
       self.player_id = -1  # Initialize
   ```

### Adding internal bots

- **No manual operation needed**: Server adds them automatically
- **`num_robots` parameter**: Can be used for tracking, but doesn't affect server behavior
- **Important**: Must enable internal bots when starting server

### Bot types

- **FAST_STRATEGY** (70%): `dumb01`, `dumb02`, ... - Fast and simple
- **SMART_STRATEGY** (30%): `robot 1`, `robot 2`, ... - Smart but slower
- **Selection**: Server automatically selects in appropriate ratio

### Reference materials

- `INTERNAL_BOTS_GUIDE.md` - English overview
- `INTERNAL_BOTS.ja.md` - Japanese detailed guide
- `IMPLEMENTING_INTERNAL_BOTS.ja.md` - Implementation guide
- `example_internal_bots.py` - Usage examples

These documents contain more detailed information and implementation examples.
