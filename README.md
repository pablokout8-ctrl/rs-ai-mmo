# rs-ai-mmo

AI-driven, RuneScape-style MMO prototype.

## Offline 618-inspired server

The `server/` package included in this repository bootstraps a lightweight,
text-based RuneScape 618 inspired private server that can be run entirely
offline. The goal is to provide an easily hackable foundation for local
experimentation without requiring any proprietary assets.

### Features

* Asyncio-powered TCP server with configurable host/port.
* Persistent character saving to JSON files in `server/saves/`.
* Administrator auto-detection based on usernames listed in
  `server/config.json`.
* Basic skill system (level/XP) that follows RuneScape-style progression.
* Inventory management with stackable items.
* NPC definition and respawn tick simulation loaded from JSON data files.
* Built-in text commands such as `::tele`, `::setlevel`, `::item`, `::save`,
  and `::logout`.

### Requirements

* Python 3.10 or newer.

All dependencies are from the Python standard library, so no extra packages
need to be installed.

### Running the server

```bash
python -m server.main
```

By default the server listens on `127.0.0.1:43594` (the classic RuneScape
game port). Configuration can be changed via `server/config.json`.

### Connecting

Use a TCP client such as `telnet` or `nc` to connect to the server port. Enter
your desired username when prompted. Usernames listed in the
`admin_usernames` array within `server/config.json` are automatically granted
administrator privileges and have access to moderation commands.

### Command reference

Prefix commands with `::` when connected. Some example commands include:

| Command | Description |
| ------- | ----------- |
| `::help` | View the available commands. |
| `::players` | List currently online players. |
| `::coords` | Display your current coordinates. |
| `::tele <x> <y> [plane]` | Teleport to coordinates (admin only). |
| `::setlevel <skill> <level>` | Set a skill level (admin only). |
| `::addxp <skill> <amount>` | Grant XP to a skill (admin only). |
| `::item <id> [amount]` | Spawn an item into your inventory (admin only). |
| `::save` | Persist your character immediately. |
| `::logout` | Log out cleanly. |

The server saves character profiles automatically on logout and also keeps a
rolling log of world events in memory for debugging purposes.
