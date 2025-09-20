"""Text command handling for the offline server."""

from __future__ import annotations

from dataclasses import dataclass
import shlex
from typing import Callable, Dict, List, Tuple, TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - circular import safe-guard
    from .player import Player
    from .world import GameWorld


@dataclass
class CommandContext:
    world: "GameWorld"
    player: "Player"
    args: List[str]


CommandFunction = Callable[[CommandContext], str]


class CommandDispatcher:
    """Simple command registry and executor."""

    def __init__(self) -> None:
        self._commands: Dict[str, Tuple[CommandFunction, str]] = {}

    def register(self, name: str, handler: CommandFunction, description: str) -> None:
        self._commands[name.lower()] = (handler, description)

    def dispatch(self, world: "GameWorld", player: "Player", raw: str) -> str:
        parts = shlex.split(raw)
        if not parts:
            return ""
        name, *args = parts
        name = name.lower()
        if name not in self._commands:
            return f"Unknown command '{name}'. Use ::help for a list of commands."
        handler, _ = self._commands[name]
        return handler(CommandContext(world=world, player=player, args=args))

    def help_message(self) -> str:
        lines = ["Available commands:"]
        for name, (_, description) in sorted(self._commands.items()):
            lines.append(f"::{name} - {description}")
        return "\n".join(lines)


def create_default_dispatcher() -> CommandDispatcher:
    dispatcher = CommandDispatcher()

    def require_admin(ctx: CommandContext) -> None:
        if not ctx.player.is_admin():
            raise PermissionError("You must be an admin to use this command.")

    def cmd_help(ctx: CommandContext) -> str:
        return dispatcher.help_message()

    dispatcher.register("help", cmd_help, "Show this help message.")

    def cmd_coords(ctx: CommandContext) -> str:
        pos = ctx.player.position
        return f"You are at ({pos.x}, {pos.y}, plane {pos.plane})."

    dispatcher.register("coords", cmd_coords, "Show your current coordinates.")

    def cmd_players(ctx: CommandContext) -> str:
        names = ", ".join(sorted(ctx.world.players.keys())) or "none"
        return f"Online players: {names}"

    dispatcher.register("players", cmd_players, "List currently online players.")

    def cmd_motd(ctx: CommandContext) -> str:
        return ctx.world.config.motd

    dispatcher.register("motd", cmd_motd, "Show the message of the day.")

    def cmd_tele(ctx: CommandContext) -> str:
        require_admin(ctx)
        if len(ctx.args) < 2:
            return "Usage: ::tele <x> <y> [plane]"
        x, y = map(int, ctx.args[:2])
        plane = int(ctx.args[2]) if len(ctx.args) > 2 else 0
        ctx.player.teleport(x, y, plane)
        return f"Teleported to ({x}, {y}, plane {plane})."

    dispatcher.register("tele", cmd_tele, "Teleport to coordinates (admin only).")

    def cmd_setlevel(ctx: CommandContext) -> str:
        require_admin(ctx)
        if len(ctx.args) < 2:
            return "Usage: ::setlevel <skill> <level>"
        skill, level = ctx.args[0].lower(), int(ctx.args[1])
        if skill not in ctx.player.skills:
            return f"Unknown skill '{skill}'."
        ctx.player.skills[skill].level = max(1, min(level, 99))
        return f"Set {skill} level to {level}."

    dispatcher.register("setlevel", cmd_setlevel, "Set a skill level (admin only).")

    def cmd_addxp(ctx: CommandContext) -> str:
        require_admin(ctx)
        if len(ctx.args) < 2:
            return "Usage: ::addxp <skill> <amount>"
        skill, amount = ctx.args[0].lower(), int(ctx.args[1])
        try:
            ctx.player.gain_xp(skill, amount)
        except KeyError:
            return f"Unknown skill '{skill}'."
        return f"Added {amount} XP to {skill}."

    dispatcher.register("addxp", cmd_addxp, "Add experience to a skill (admin only).")

    def cmd_item(ctx: CommandContext) -> str:
        require_admin(ctx)
        if len(ctx.args) < 1:
            return "Usage: ::item <item_id> [amount]"
        item_id = int(ctx.args[0])
        amount = int(ctx.args[1]) if len(ctx.args) > 1 else 1
        if ctx.player.inventory.add_item(item_id, amount):
            return f"Added item {item_id} x{amount} to inventory."
        return "Inventory full."

    dispatcher.register("item", cmd_item, "Spawn an item in your inventory (admin only).")

    def cmd_save(ctx: CommandContext) -> str:
        ctx.world.save_player(ctx.player)
        return "Character saved."

    dispatcher.register("save", cmd_save, "Save your character to disk.")

    def cmd_logout(ctx: CommandContext) -> str:
        ctx.world.request_logout(ctx.player.username)
        return "Logging out..."

    dispatcher.register("logout", cmd_logout, "Log out of the server.")

    return dispatcher
