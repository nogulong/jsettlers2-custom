# JSettlers Internal Bots Integration Guide

## Overview

This guide explains how to use JSettlers' built-in robot players (bots) with your Python bot implementation.

## Key Points

### 1. Internal Bot Types

JSettlers has two built-in robot strategies:

- **FAST_STRATEGY** (70% of bots)
  - Names: `dumb01`, `dumb02`, `dumb03`, ...
  - Faster but simpler AI
  - Basic construction and trading logic

- **SMART_STRATEGY** (30% of bots)
  - Names: `robot 1`, `robot 2`, ...
  - Smarter but slower AI
  - Calculates Win Game ETA (estimated turns to victory)
  - More complex decision-making

### 2. How Internal Bots are Added

**Important**: The JSettlers server **automatically** adds internal bots to fill empty seats when a game is ready. You don't need to explicitly request bots from the client side.

Server behavior:
1. Game is created
2. Players sit down
3. When game is ready, server automatically places internal bots in empty seats
4. Game starts when all seats are filled

### 3. Seat Selection

To avoid conflicts with internal bots, use **automatic seat assignment**:

```python
def sit_down(self, game_name: str, preferred_seat: int = -1):
    """Request to sit down (message 1012)"""
    msg = f"1012|{game_name},-,{preferred_seat},true"
    write_java_utf(self.sock, msg)
```

- Use `preferred_seat=-1` for automatic assignment (recommended)
- Server assigns an available seat
- Avoids conflicts with internal bots

## Implementation Changes

For the code provided in the problem statement, make these changes:

### Change 1: Update `sit_down()` method

```python
def sit_down(self, game_name: str, preferred_seat: int = -1):
    """Request to sit in a seat
    
    Args:
        game_name: Game name
        preferred_seat: Preferred seat number (-1 = auto-assign)
    """
    print(f"🪑 Requesting to sit in game: {game_name}, seat: {preferred_seat}")
    
    msg = f"1012|{game_name},-,{preferred_seat},true"
    
    write_java_utf(self.sock, msg)
    print(f"→ {msg}")
```

### Change 2: Update message handler

```python
elif msg_type == "1013": # JOINGAME
    args = parsed.get("args", [])
    if len(args) >= 1:
        name = args[0]
        
        # When we join, request a seat
        if name == self.nickname and self.player_id == -1:
            print("🚀 Join complete. Requesting auto-seat assignment...")
            # Use automatic assignment
            self.sit_down(self.current_game, preferred_seat=-1)
```

## Usage Example

```python
# Initialize bot
bot = JSettlersBot(
    host="localhost",
    port=8880,
    nickname="PyBot",
    cookie="your_robot_cookie",
    agent=agent
)

# Create game with 3 internal bots
bot.run(
    game_name="MyGame",
    mode="create",
    num_robots=3,  # Server will auto-add 3 internal bots
    num_games=1
)
```

Result:
- 1 Python bot (you)
- 3 internal bots (server auto-adds)
- Total: 4-player game

## Files Created

1. **INTERNAL_BOTS.ja.md** - Comprehensive guide in Japanese about the internal bot system
2. **IMPLEMENTING_INTERNAL_BOTS.ja.md** - Detailed implementation guide in Japanese
3. **example_internal_bots.py** - Example script showing how to use internal bots
4. **jsettler_utils.py** - Utility functions for the problem statement code

## Troubleshooting

### Internal bots don't join

**Cause**: Server doesn't have internal bots running

**Solution**: Start server with bots enabled:
```bash
java -jar JSettlersServer.jar \
    -Djsettlers.bots.cookie=your_cookie \
    -Djsettlers.startrobots=7
```

### Python bot can't get a seat

**Cause**: Timing issue or all seats taken

**Solution**:
1. Wait for join confirmation (message 1013) before requesting seat
2. Use automatic assignment (-1)
3. Initialize `player_id` properly

### Game doesn't start

**Cause**: Waiting for all seats to be filled

**Solution**:
- Check server logs
- Ensure `num_robots` is correct (e.g., for 4-player game: num_robots=3)

## Summary

Key changes needed for the problem statement code:

1. ✅ Add `preferred_seat` parameter to `sit_down()` method
2. ✅ Use automatic assignment (-1) in message handler
3. ✅ Properly initialize and manage `player_id`
4. ✅ Understand that server automatically adds bots

With these changes, the Python bot will properly sit in a valid seat without conflicting with internal bots.
