import tempfile
import unittest
from pathlib import Path

from server.config import ServerConfig
from server.player import Player
from server.world import GameWorld


class WorldTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.config = ServerConfig(admin_usernames={"admin"})
        self.world = GameWorld(self.config)
        self.world.saves_path = Path(self.tempdir.name)
        self.world.saves_path.mkdir(exist_ok=True)
        self.world.load()

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def test_admin_command(self) -> None:
        player = self.world.load_player("admin", "admin")
        self.world.register_player(player)
        response = self.world.handle_chat(player, "::tele 3200 3200")
        self.assertIn("Teleported", response)
        self.world.remove_player(player.username)

    def test_chat_broadcast(self) -> None:
        player = Player(username="Alice")
        self.world.register_player(player)
        response = self.world.handle_chat(player, "Hello world")
        self.assertEqual("Message sent.", response)
        messages = list(self.world.poll_messages(player.username))
        self.assertTrue(any("Hello world" in msg for msg in messages))
        self.world.remove_player(player.username)

    def test_admin_restriction(self) -> None:
        player = Player(username="Bob")
        self.world.register_player(player)
        response = self.world.handle_chat(player, "::tele 3200 3200")
        self.assertIn("admin", response.lower())
        self.world.remove_player(player.username)


if __name__ == "__main__":
    unittest.main()
