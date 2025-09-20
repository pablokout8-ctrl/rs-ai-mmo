"""Asyncio based text networking layer."""

from __future__ import annotations

import asyncio
from typing import Optional

from .config import ServerConfig
from .player import Player
from .world import GameWorld


class ClientSession:
    """Single client connection handler."""

    def __init__(self, world: GameWorld, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        self.world = world
        self.reader = reader
        self.writer = writer
        self.player: Optional[Player] = None

    async def run(self) -> None:
        try:
            await self._send("Welcome to the offline RuneScape 618-inspired server!\n")
            username = await self._prompt("Enter username: ")
            if not username:
                return
            rights = "admin" if username.lower() in self.world.config.admin_usernames else "player"
            player = self.world.load_player(username=username, rights=rights)
            self.player = player
            self.world.register_player(player)
            await self._send(f"Hello {player.username}! Type ::help for commands.\n")
            await self._event_loop()
        finally:
            if self.player:
                self.world.remove_player(self.player.username)
            self.writer.close()
            await self.writer.wait_closed()

    async def _event_loop(self) -> None:
        assert self.player
        while True:
            if self.player.username.lower() not in self.world.players:
                break
            await self._flush_messages()
            await self._send("> ")
            try:
                data = await asyncio.wait_for(
                    self.reader.readline(), timeout=self.world.config.tick_duration * 5
                )
            except asyncio.TimeoutError:
                continue
            if not data:
                break
            message = data.decode().strip()
            response = self.world.handle_chat(self.player, message)
            if response:
                await self._send(response + "\n")
            await self._flush_messages()
            if self.player.username.lower() not in self.world.players:
                break

    async def _flush_messages(self) -> None:
        assert self.player
        for message in self.world.poll_messages(self.player.username):
            await self._send("[Server] " + message + "\n")

    async def _send(self, data: str) -> None:
        self.writer.write(data.encode())
        await self.writer.drain()

    async def _prompt(self, prompt: str) -> str:
        await self._send(prompt)
        data = await self.reader.readline()
        return data.decode().strip()


async def start_server(world: GameWorld, config: ServerConfig) -> None:
    server = await asyncio.start_server(lambda r, w: ClientSession(world, r, w).run(), config.host, config.port)
    addrs = ", ".join(str(sock.getsockname()) for sock in server.sockets or [])
    print(f"Server running on {addrs}")
    async with server:
        await server.serve_forever()
