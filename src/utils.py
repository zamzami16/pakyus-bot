from typing import Dict, List, Tuple, Optional
from telegram import Update
from telegram.ext import (
    BaseHandler,
    CallbackQueryHandler,
    CallbackContext,
)

from . import command_dispatcher as cd
from .command_handler_services import CommandHandlerServices
from emoji import emojize
from bs4 import BeautifulSoup

import asyncio, logging, os
import moviepy.editor as mp

logger = logging.getLogger(__name__)


def get_commands(
    commands_handler: List[CommandHandlerServices],
) -> Tuple[List[BaseHandler], List[Dict[str, str]]]:
    commands = []
    handlers = []
    for ch in commands_handler:
        if len(ch.name) > 0:
            commands.append(cd.create_command(ch.name, ch.description))

        handlers.append(ch.handler)

    return handlers, commands


async def wait_for_user_input(update: Update) -> str:
    try:
        response = await asyncio.Future()

        async def callback(update: Update, context: CallbackContext):
            response.set_result(update.callback_query.data)

        update.dispatcher.add_handler(CallbackQueryHandler(callback))

        # Wait for 10 seconds for user input
        await asyncio.wait_for(response, timeout=10)
        return response.result()

    except asyncio.TimeoutError:
        return "timeout"


async def send_default_error_message(update: Update) -> None:
    try:
        await update.message.reply_text(
            emojize(f"Sorry, Error occured. :folded_hands:")
        )
    except Exception as err:
        logger.error(f"General send error message error: {err}")


def convert_video_to_audio(
    video_path: str, audio_path: str, raise_exception: bool = False
) -> str | None:
    if video_path is None or audio_path is None:
        msg = "video or audio path null."
        logger.error(msg)
        if raise_exception:
            raise Exception(msg)
        return None

    try:
        new_file = mp.AudioFileClip(video_path)
        new_file.write_audiofile(audio_path)
        return audio_path
    except Exception as err:
        logger.error(f"{err}")
        if raise_exception:
            raise


def evaluate_arguments(arguments: str) -> List[str]:
    parts = [part.strip("\"'") for part in arguments.split('"') if part.strip()]
    return parts


def html_to_markdown(html: str):
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table")

    if not table:
        return ""

    headers = [header.get_text(strip=True) for header in table.find_all("th")]
    rows = []

    for row in table.find_all("tr")[1:]:  # Skip the header row
        cells = [
            cell.get_text(strip=True) for cell in row.find_all(["td", "th"])
        ]
        rows.append(cells)

    markdown_table = (
        f"| {' | '.join(headers)} |\n| {' | '.join(['---'] * len(headers))} |\n"
    )

    for row in rows:
        markdown_table += f"| {' | '.join(row)} |\n"

    return markdown_table
