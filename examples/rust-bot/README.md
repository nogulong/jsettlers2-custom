# JSettlers Rust Bot Example

This is a minimal example of a Rust bot that can connect to a JSettlers server.

## Prerequisites

- Rust (https://rustup.rs/)
- JSettlers server running

## Building

```bash
cargo build --release
```

## Running

First, start the JSettlers server with a visible cookie:

```bash
java -Djsettlers.bots.showcookie=Y -jar /path/to/JSettlers.jar 8880
```

Note the robot cookie displayed, then run the bot:

```bash
cargo run -- localhost 8880 mybot <cookie>
```

Replace `<cookie>` with the actual cookie from the server.

## Next Steps

This is a minimal bot that:
- Connects to the server
- Authenticates as a robot
- Joins games when requested
- Rolls dice on its turn

To make it more intelligent, you can:
1. Add game state tracking
2. Implement building strategies
3. Add resource management
4. Integrate with your private-rust-catan agent

See the documentation in `../../doc/` for more detailed information:
- `Rust-Agent-Integration-Guide.ja.md` - Comprehensive guide (Japanese)
- `Rust-Agent-Quick-Start.ja.md` - Quick start guide (Japanese)
- `Readme.developer.md` - Developer documentation (English)
- `Message-Sequences-for-Game-Actions.md` - Message protocol reference
