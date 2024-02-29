from dotenv import load_dotenv
import logging
import os
from telegram import Update, InputTextMessageContent, InlineQueryResultArticle
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    InlineQueryHandler,
    filters,
)
from src import command_dispatcher
from src.color_services import COLOR_SERVICE_COMMAND_HANDLER
from src import utils
from src.expedition.cek_resi import CEK_RESI_SERVICE_COMMAND_HANDLER
from src.youtube_services import YOUTUBE_SERVICE_COMMAND_HANDLER

load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
LOG_FILE = os.path.join(os.getcwd(), os.getenv("LOG_FILE"))
DEBUG = os.getenv("DEBUG")


logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    filename=None if DEBUG else LOG_FILE,
)

logger = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id, text="I'm a bot, please talk to me!"
    )


async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id, text=update.message.text
    )


async def caps(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text_caps = " ".join(context.args).upper()
    await context.bot.send_message(
        chat_id=update.effective_chat.id, text=text_caps
    )


async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Sorry, I didn't understand that command.",
    )


async def inline_caps(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.inline_query.query
    if not query:
        return
    results = []
    results.append(
        InlineQueryResultArticle(
            id=query.upper(),
            title="Caps",
            input_message_content=InputTextMessageContent(query.upper()),
        )
    )
    await context.bot.answer_inline_query(update.inline_query.id, results)


def errors(update, context):
    logger.error(context.error)


def main():
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    start_handler = CommandHandler("start", start)
    echo_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), echo)
    caps_handler = CommandHandler("caps", caps)
    unknown_handler = MessageHandler(filters.COMMAND, unknown)
    inline_caps_handler = InlineQueryHandler(inline_caps)

    # color services
    color_service_handlers, cmd_color_service = utils.get_commands(
        COLOR_SERVICE_COMMAND_HANDLER
    )
    command_dispatcher.add_commands(cmd_color_service)
    application.add_handlers(color_service_handlers)

    # youtube service
    yt_service_handlers, cmd_yt_service = utils.get_commands(
        YOUTUBE_SERVICE_COMMAND_HANDLER
    )
    command_dispatcher.add_commands(cmd_yt_service)
    application.add_handlers(yt_service_handlers)

    # cek resi service
    cek_resi_service_handler, cmd_cek_resi_service = utils.get_commands(
        CEK_RESI_SERVICE_COMMAND_HANDLER
    )
    command_dispatcher.add_commands(cmd_cek_resi_service)
    application.add_handlers(cek_resi_service_handler)

    application.add_handler(start_handler)
    application.add_handler(caps_handler)
    application.add_handler(inline_caps_handler)

    application.add_handler(unknown_handler)

    # add available command
    command_dispatcher.set_token(TELEGRAM_TOKEN)
    command_dispatcher.add_command("caps", "uppercase text")

    command_dispatcher.update_command_to_bot_father()

    # add error handler
    application.add_error_handler(errors)

    application.run_polling()


if __name__ == "__main__":
    main()
