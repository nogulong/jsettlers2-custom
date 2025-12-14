# JSettlers Examples

This directory contains example code for integrating with JSettlers.

## Available Examples

### Rust Bot (`rust-bot/`)

A minimal example of a Rust bot that can connect to a JSettlers server and play games.

**Features:**
- Connects to JSettlers server via TCP
- Implements Java UTF message format
- Authenticates as a robot client
- Joins games when requested
- Basic game play (rolling dice)

**See:** [rust-bot/README.md](rust-bot/README.md) for setup and usage instructions.

**Documentation:**
- [Rust Agent Integration Guide (Japanese)](../doc/Rust-Agent-Integration-Guide.ja.md)
- [Rust Agent Quick Start (Japanese)](../doc/Rust-Agent-Quick-Start.ja.md)

## Using These Examples

These examples are intended as starting points for your own bot development. You can:

1. Copy the example to your own project
2. Modify it to implement your own strategy
3. Integrate with your own game AI (like private-rust-catan)

## Java Examples

For Java-based bot examples, see:
- `src/main/java/soc/robot/sample3p/` - Sample third-party robot in Java
- `src/main/java/soc/robot/` - Standard robot implementation

## More Information

- Developer documentation: [../doc/Readme.developer.md](../doc/Readme.developer.md)
- Message protocol: [../doc/Message-Sequences-for-Game-Actions.md](../doc/Message-Sequences-for-Game-Actions.md)
- Main README: [../Readme.md](../Readme.md)
