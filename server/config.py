"""Server configuration helpers."""

from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path
from typing import Iterable, Set


@dataclass(frozen=True)
class ServerConfig:
    """Immutable configuration for the offline server."""

    host: str = "127.0.0.1"
    port: int = 43594
    tick_rate: float = 0.6  # seconds per game tick (RS2 used ~0.6s)
    max_players: int = 2000
    admin_usernames: Set[str] = field(default_factory=set)
    motd: str = "Welcome to the offline 618-inspired world!"

    @property
    def tick_duration(self) -> float:
        """Duration of a single game tick in seconds."""

        return max(self.tick_rate, 0.1)

    @classmethod
    def load(cls, path: Path | str) -> "ServerConfig":
        """Load configuration from a JSON file."""

        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Configuration file not found: {path}")
        data = json.loads(path.read_text())
        admins: Iterable[str] = data.get("admin_usernames", [])
        return cls(
            host=data.get("host", cls.host),
            port=int(data.get("port", cls.port)),
            tick_rate=float(data.get("tick_rate", cls.tick_rate)),
            max_players=int(data.get("max_players", cls.max_players)),
            admin_usernames={name.lower() for name in admins},
            motd=data.get("motd", cls.motd),
        )

    def to_json(self) -> str:
        """Serialize the configuration to a JSON string."""

        data = {
            "host": self.host,
            "port": self.port,
            "tick_rate": self.tick_rate,
            "max_players": self.max_players,
            "admin_usernames": sorted(self.admin_usernames),
            "motd": self.motd,
        }
        return json.dumps(data, indent=2)
