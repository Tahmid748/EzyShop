"""Interpret structured AI actions; users never need to send slash commands."""

from dataclasses import dataclass
from typing import Any

from source.database.store import register_user


@dataclass
class CommandResult:
    message: str
    action: str | None = None


async def handle_commands(
    action: str | None, telegram_user_id: int, reply: str
) -> CommandResult:
    """Execute an allow-listed AI action and return the user-facing result."""
    if action == "REGISTER_USER":
        await register_user(telegram_user_id)
        return CommandResult(
            message=reply or "You're registered. Now add your business and inventory.",
            action="OPEN_ONBOARDING",
        )
    if action == "OPEN_ONBOARDING":
        return CommandResult(message=reply, action=action)
    return CommandResult(message=reply)
