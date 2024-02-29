from typing import List
import requests
import json
import logging

logger = logging.getLogger(__name__)


class AvailableCommands:
    def __init__(self, token: str, commands: list) -> None:
        self._commands = commands
        self._token = token

    def add_command(self, command: dict) -> None:
        self._commands.append(command)

    def add_command_by_values(self, command: str, description: str) -> None:
        cmd = {"command": command, "description": description}
        self.add_command(cmd)

    def update_command(self) -> requests.Response:
        try:
            logger.info(self._commands)
            send_text = (
                f"https://api.telegram.org/bot{self._token}/setMyCommands"
            )
            response = requests.post(
                send_text, json={"commands": self._commands}
            )

            if response.status_code == 200:
                logger.info("Set commands to BotFather successfully.")
            else:
                response.raise_for_status()

            return response
        except requests.RequestException as err:
            logger.error(f"Network error: {err}")
            return None
        except json.JSONDecodeError as err:
            logger.error(f"JSON decoding error: {err}")
            return None


_commands = []
_token = ""


def add_commands(commands: List[dict[str, str]]) -> None:
    _commands.extend(commands)


def create_command(command: str, description: str) -> dict:
    cmd = {"command": command, "description": description}
    return cmd


def add_command(command: str, description: str) -> None:
    cmd = {"command": command, "description": description}
    _commands.append(cmd)


def set_token(token: str) -> None:
    global _token
    _token = token


def update_command_to_bot_father() -> None:
    global _commands, _token

    if not _commands:
        return

    if not _token:
        return

    try:
        av = AvailableCommands(_token, _commands)
        av.update_command()
    except Exception as e:
        logger.error(f"An error occurred: {e}")
