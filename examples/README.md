# JSettlers Examples

This directory contains example code for integrating with JSettlers.

## Available Examples

### Python Bot (`python-bot/`)

**A pure Python bot for evaluating PyTorch agents with JSettlers.**

This is the recommended approach if your agent is implemented in Python.

**Features:**
- Connects to JSettlers server via TCP
- Implements Java UTF message format in Python
- Converts JSettlers messages to Observation format
- Uses PyTorch models for action prediction
- Sends actions back to JSettlers

**Use Case:**
- Evaluating trained PyTorch agents
- Testing Python-based reinforcement learning agents
- No Rust required - pure Python implementation

**See:** [python-bot/README.md](python-bot/README.md) for setup and usage instructions.

**Documentation:** [Python Bot Guide (Japanese)](../doc/Python-Bot-Guide.ja.md)

### Rust Bot (`rust-bot/`)

A minimal example of a Rust bot that can connect to a JSettlers server and play games.

**Features:**
- Connects to JSettlers server via TCP
- Implements Java UTF message format
- Authenticates as a robot client
- Basic game play (rolling dice)

**See:** [rust-bot/README.md](rust-bot/README.md) for setup and usage instructions.

**Documentation:**
- [Rust Agent Integration Guide (Japanese)](../doc/Rust-Agent-Integration-Guide.ja.md)
- [Rust Agent Quick Start (Japanese)](../doc/Rust-Agent-Quick-Start.ja.md)

## Which Example Should I Use?

- **Python agents** (PyTorch, TensorFlow, etc.) → Use `python-bot/`
- **Rust agents** → Use `rust-bot/`
- **Hybrid (Rust environment + Python NN)** → See [Python + Rust Hybrid Guide](../doc/Rust-Python-Hybrid-Guide.ja.md)

## Java Examples

For Java-based bot examples, see:
- `src/main/java/soc/robot/sample3p/` - Sample third-party robot in Java
- `src/main/java/soc/robot/` - Standard robot implementation

## More Information

- Developer documentation: [../doc/Readme.developer.md](../doc/Readme.developer.md)
- Message protocol: [../doc/Message-Sequences-for-Game-Actions.md](../doc/Message-Sequences-for-Game-Actions.md)
- Main README: [../Readme.md](../Readme.md)
