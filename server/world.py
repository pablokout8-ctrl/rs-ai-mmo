"""Core world state and update loop."""

from __future__ import annotations

import asyncio
from collections import deque
from dataclasses import dataclass
import json
from pathlib import Path
from typing import Dict, Iterable, Optional

from .commands import CommandDispatcher, create_default_dispatcher
from .config import ServerConfig
from .npc import NpcDefinition, NpcSpawn
from .player import Player, Position


@dataclass
class WorldEvent:
    tick: int
    message: str


class GameWorld:
    """Holds persistent state for the offline world."""

    def __init__(self, config: ServerConfig, data_path: Path | str | None = None) -> None:
        self.config = config
        self.data_path = Path(data_path or Path(__file__).resolve().parent / "data")
        self.players: Dict[str, Player] = {}
        self.npc_definitions: Dict[int, NpcDefinition] = {}
        self.npcs: Dict[int, NpcSpawn] = {}
        self.tick_counter = 0
        self.events: deque[WorldEvent] = deque(maxlen=200)
        self.logout_requests: set[str] = set()
        self.dispatcher: CommandDispatcher = create_default_dispatcher()
        self.saves_path = Path(__file__).resolve().parent / "saves"
        self.saves_path.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Loading & persistence
    # ------------------------------------------------------------------
    def load(self) -> None:
        self._load_npc_definitions()
        self._load_npc_spawns()

    def _load_npc_definitions(self) -> None:
        data_file = self.data_path / "npcs.json"
        for entry in self._read_json_array(data_file):
            definition = NpcDefinition.from_dict(entry)
            self.npc_definitions[definition.npc_id] = definition

    def _load_npc_spawns(self) -> None:
        data_file = self.data_path / "spawns.json"
        for entry in self._read_json_array(data_file):
            npc_id = int(entry["npc_id"])
            definition = self.npc_definitions.get(npc_id)
            if not definition:
                continue
            spawn = NpcSpawn(
                definition=definition,
                position=Position(int(entry.get("x", 0)), int(entry.get("y", 0)), int(entry.get("plane", 0))),
            )
            self.npcs[spawn.definition.npc_id] = spawn

    def _read_json_array(self, path: Path) -> Iterable[Dict]:
        if not path.exists():
            return []
        return json.loads(path.read_text())

    def _player_save_path(self, username: str) -> Path:
        return self.saves_path / f"{username.lower()}.json"

    def load_player(self, username: str, rights: str) -> Player:
        save_path = self._player_save_path(username)
        if save_path.exists():
            data = json.loads(save_path.read_text())
            player = Player.from_dict(data)
            player.rights = rights
            return player
        player = Player(username=username, rights=rights)
        return player

    def save_player(self, player: Player) -> None:
        path = self._player_save_path(player.username)
        path.write_text(json.dumps(player.to_dict(), indent=2))

    # ------------------------------------------------------------------
    # Player management
    # ------------------------------------------------------------------
    def register_player(self, player: Player) -> None:
        username = player.username.lower()
        if len(self.players) >= self.config.max_players:
            raise RuntimeError("World is full")
        self.players[username] = player
        self._log(f"{player.username} logged in.")

    def request_logout(self, username: str) -> None:
        self.logout_requests.add(username.lower())

    def remove_player(self, username: str) -> Optional[Player]:
        username = username.lower()
        player = self.players.pop(username, None)
        if player:
            self.save_player(player)
            self._log(f"{player.username} logged out.")
        return player

    # ------------------------------------------------------------------
    # World update loop
    # ------------------------------------------------------------------
    async def run(self) -> None:
        self.load()
        while True:
            await asyncio.sleep(self.config.tick_duration)
            self.process_tick()

    def process_tick(self) -> None:
        self.tick_counter += 1
        for npc in self.npcs.values():
            npc.tick()
        for username in list(self.logout_requests):
            if username in self.players:
                self.remove_player(username)
            self.logout_requests.discard(username)

    # ------------------------------------------------------------------
    # Player interaction helpers
    # ------------------------------------------------------------------
    def handle_chat(self, player: Player, message: str) -> str:
        message = message.strip()
        if not message:
            return ""
        if message.startswith("::"):
            command_text = message[2:]
            try:
                response = self.dispatcher.dispatch(self, player, command_text)
            except PermissionError as exc:  # from admin checks
                response = str(exc)
            except Exception as exc:  # pragma: no cover - defensive
                response = f"Command error: {exc}"
            return response
        broadcast = f"{player.username}: {message}"
        self.broadcast(broadcast)
        return "Message sent."

    def broadcast(self, message: str) -> None:
        for player in self.players.values():
            player.queue_message(message)
        self._log(message)

    def _log(self, message: str) -> None:
        self.events.append(WorldEvent(self.tick_counter, message))

    def poll_messages(self, username: str) -> Iterable[str]:
        player = self.players.get(username.lower())
        if not player:
            return []
        return player.pop_messages()
