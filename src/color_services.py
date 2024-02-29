from .command_handler_services import CommandHandlerServices
from telegram import Update
from telegram.ext import CommandHandler, ContextTypes
import logging

logger = logging.getLogger(__name__)


def hex_to_rgb(value: str) -> tuple:
    value = value.lstrip("#")
    lv = len(value)
    result = tuple(
        int(value[i : i + lv // 3], 16) for i in range(0, lv, lv // 3)
    )

    if len(result) != 3:
        raise IndexError()

    return result


async def hex2rgb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        hex_code = context.args[0]
        # Remove '#' if present
        hex_code = hex_code.lstrip("#")
        rgb_value = hex_to_rgb(hex_code)

        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"RGB value for #{hex_code}: {rgb_value}",
        )

    except IndexError as err:
        logger.error("IndexError: %s", err)
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Please provide a valid hexadecimal color code (e.g., #FFAABB or FFAABB).",
        )

    except Exception as err:
        logger.error("Error: %s", err)
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="An error occurred. Please try again later.",
        )


hex2rgb_service = CommandHandlerServices(
    "hex2rgb",
    CommandHandler("hex2rgb", hex2rgb),
    "convert hex color scheme to rgb",
)


COLOR_SERVICE_COMMAND_HANDLER = [
    hex2rgb_service,
]
