use std::io::{Read, Write};
use std::net::TcpStream;

/// Write a string in Java DataOutputStream.writeUTF format
fn write_java_utf(stream: &mut TcpStream, msg: &str) -> std::io::Result<()> {
    let bytes = msg.as_bytes();
    let len = (bytes.len() as u16).to_be_bytes();
    stream.write_all(&len)?;
    stream.write_all(bytes)?;
    stream.flush()?;
    Ok(())
}

/// Read a string in Java DataInputStream.readUTF format
fn read_java_utf(stream: &mut TcpStream) -> std::io::Result<String> {
    let mut len_bytes = [0u8; 2];
    stream.read_exact(&mut len_bytes)?;
    let len = u16::from_be_bytes(len_bytes) as usize;
    
    let mut buf = vec![0u8; len];
    stream.read_exact(&mut buf)?;
    
    String::from_utf8(buf)
        .map_err(|e| std::io::Error::new(std::io::ErrorKind::InvalidData, e))
}

/// Extract a field value from a message
fn extract_field(msg: &str, field: &str) -> Option<String> {
    msg.split('|')
        .find(|part| part.starts_with(&format!("{}=", field)))
        .and_then(|part| part.split('=').nth(1))
        .map(|s| s.to_string())
}

struct RustBot {
    stream: TcpStream,
    nickname: String,
    current_game: Option<String>,
}

impl RustBot {
    fn new(stream: TcpStream, nickname: String) -> Self {
        Self {
            stream,
            nickname,
            current_game: None,
        }
    }
    
    /// Authenticate with the server
    fn authenticate(&mut self, cookie: &str) -> std::io::Result<()> {
        // Send VERSION message
        let version_msg = "VERSION:version=2.5.00,versionint=2500,locale=en_US,cliFeats=;6pl;sb;";
        println!("→ {}", version_msg);
        write_java_utf(&mut self.stream, version_msg)?;
        
        // Send IMAROBOT message
        let robot_msg = format!(
            "IMAROBOT:nickname={}|cookie={}|rbclass=rust.bot.RustAgent",
            self.nickname, cookie
        );
        println!("→ {}", robot_msg);
        write_java_utf(&mut self.stream, &robot_msg)?;
        
        Ok(())
    }
    
    /// Main message processing loop
    fn run(&mut self) -> std::io::Result<()> {
        loop {
            let msg = read_java_utf(&mut self.stream)?;
            println!("← {}", msg);
            
            if let Err(e) = self.handle_message(&msg) {
                eprintln!("Error handling message: {}", e);
            }
        }
    }
    
    /// Handle an incoming message
    fn handle_message(&mut self, msg: &str) -> std::io::Result<()> {
        // Extract message type (first part before ':')
        let msg_type = msg.split(':').next().unwrap_or("");
        
        match msg_type {
            "UPDATEROBOTPARAMS" => {
                println!("✓ Robot parameters updated");
            }
            "BOTJOINGAMEREQUEST" => {
                self.handle_join_request(msg)?;
            }
            "JOINGAMEAUTH" => {
                if let Some(game) = extract_field(msg, "game") {
                    self.current_game = Some(game.clone());
                    println!("✓ Joined game: {}", game);
                }
            }
            "TURN" => {
                self.handle_turn(msg)?;
            }
            "GAMESTATE" => {
                self.handle_game_state(msg)?;
            }
            "DICERESULT" => {
                if let Some(result) = extract_field(msg, "param") {
                    println!("🎲 Dice result: {}", result);
                }
            }
            _ => {
                // Other messages can be handled here
            }
        }
        
        Ok(())
    }
    
    /// Handle a bot join game request
    fn handle_join_request(&mut self, msg: &str) -> std::io::Result<()> {
        if let Some(game_name) = extract_field(msg, "game") {
            println!("📥 Join request for game: {}", game_name);
            
            let join_msg = format!(
                "JOINGAME:nickname={}|password=|host=-|game={}",
                self.nickname, game_name
            );
            println!("→ {}", join_msg);
            write_java_utf(&mut self.stream, &join_msg)?;
        }
        Ok(())
    }
    
    /// Handle turn message
    fn handle_turn(&mut self, msg: &str) -> std::io::Result<()> {
        if let Some(game) = &self.current_game {
            // In a real bot, check if it's our turn
            // For simplicity, we assume any TURN message means we should act
            println!("🎮 It's our turn!");
        }
        Ok(())
    }
    
    /// Handle game state changes
    fn handle_game_state(&mut self, msg: &str) -> std::io::Result<()> {
        if let (Some(game), Some(state)) = (
            extract_field(msg, "game"),
            extract_field(msg, "state")
        ) {
            println!("📊 Game {} state: {}", game, state);
            
            // State 15 = ROLL_OR_CARD (player should roll dice)
            if state == "15" && Some(game.clone()) == self.current_game {
                println!("🎲 Rolling dice...");
                let roll_msg = format!("ROLLDICE:game={}", game);
                println!("→ {}", roll_msg);
                write_java_utf(&mut self.stream, &roll_msg)?;
            }
        }
        Ok(())
    }
}

fn main() -> std::io::Result<()> {
    let args: Vec<String> = std::env::args().collect();
    
    if args.len() < 5 {
        eprintln!("Usage: {} <host> <port> <nickname> <cookie>", args[0]);
        eprintln!("Example: {} localhost 8880 mybot abc123def456", args[0]);
        eprintln!("");
        eprintln!("To get the cookie, start the server with:");
        eprintln!("  java -Djsettlers.bots.showcookie=Y -jar JSettlers.jar 8880");
        std::process::exit(1);
    }
    
    let host = &args[1];
    let port: u16 = args[2].parse()
        .expect("Invalid port number");
    let nickname = &args[3];
    let cookie = &args[4];
    
    println!("🤖 JSettlers Rust Bot");
    println!("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");
    println!("Connecting to {}:{}", host, port);
    println!("Nickname: {}", nickname);
    println!("");
    
    let stream = TcpStream::connect((host.as_str(), port))?;
    println!("✓ Connected to server");
    
    let mut bot = RustBot::new(stream, nickname.to_string());
    
    println!("🔐 Authenticating...");
    bot.authenticate(cookie)?;
    
    println!("✓ Authenticated");
    println!("⏳ Waiting for messages...");
    println!("");
    
    bot.run()?;
    
    Ok(())
}
