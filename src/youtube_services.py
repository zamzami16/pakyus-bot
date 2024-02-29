import datetime
import zipfile
from typing import Tuple, List
from pytube import YouTube
from pytube.exceptions import VideoUnavailable
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    CommandHandler,
    ContextTypes,
    CallbackContext,
    CallbackQueryHandler,
)
from public import VIDEO_PATH
import logging, os, asyncio
import concurrent.futures
from src import utils

from src.command_handler_services import CommandHandlerServices

logger = logging.getLogger(__name__)

MAX_VIDEO_SIZE_MB = 50  # Maximum allowed video size in megabytes
SLICE_SIZE_MB = 45  # Size of each sliced part in megabytes


def _get_youtube_instance(url: str) -> Tuple[bool, YouTube, Exception]:
    try:
        yt = YouTube(url)
        if not yt.streams:
            raise ValueError("Invalid YouTube URL.")

        return True, yt, None

    except Exception as err:
        return False, None, err


def _download_video(url: str, user: str) -> str:
    try:
        exists, yt, err = _get_youtube_instance(url)
        if not exists:
            raise err
    except:
        logger.error(f"Failed to get YouTube instance: {err}")
        raise
    else:
        try:
            timestamp = datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
            filename_prefix = f"{user}_{timestamp}"
            mp4_path = yt.streams.get_highest_resolution().download(
                output_path=VIDEO_PATH,
                max_retries=2,
                filename_prefix=filename_prefix,
            )
            return mp4_path
        except Exception as err:
            logger.error(f"download video error. {err}")
            raise


def _download_audio_only(url: str, user: str) -> str:
    try:
        exists, yt, err = _get_youtube_instance(url)
        if not exists:
            raise err
    except:
        logger.error(f"Failed to get YouTube instance: {err}")
        raise
    else:
        try:
            timestamp = datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
            filename_prefix = f"{user}_{timestamp}"
            mp4_path = (
                yt.streams.filter(only_audio=True)
                .first()
                .download(
                    output_path=VIDEO_PATH,
                    max_retries=2,
                    filename_prefix=filename_prefix,
                )
            )
            return mp4_path
        except Exception as err:
            logger.error(f"download video error. {err}")
            raise


async def youtube_dl_video_internal(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    try:
        username = update.message.from_user.username
        logger.info(f"{username} requested to download a video from YouTube.")

        if len(context.args) == 0:
            raise ValueError("Please provide a valid YouTube URL.")

        url = context.args[0]

        with concurrent.futures.ThreadPoolExecutor() as executor:
            mp4_path = await asyncio.to_thread(_download_video, url, username)

        if not os.path.exists(mp4_path):
            raise Exception("Error occured when downloading video.")

        logger.info(f"file: {mp4_path} already downloaded.")
        logger.info(
            f"sending video: {mp4_path} to {update.message.from_user.username}"
        )

        # Check video size
        video_size_mb = os.path.getsize(mp4_path) / (
            1024 * 1024
        )  # Convert to megabytes

        if video_size_mb > MAX_VIDEO_SIZE_MB:
            logger.info("video size exceeded.")
            await handle_large_video(update, context, mp4_path)
        else:
            with open(mp4_path, "rb") as file:
                await update.message.reply_video(video=file.read())

    except VideoUnavailable as vu:
        logger.error(f"download video youtube error: {vu}")
        await update.message.reply_text("Video unavailable.")

    except Exception as err:
        logger.error(f"{err}")
        # reply with corresponse error
        await update.message.reply_text(f"Error: {err}")


async def handle_large_video(
    update: Update, context: ContextTypes.DEFAULT_TYPE, mp4_path: str
) -> None:
    try:
        logger.info("Handle larger video. ask user for process zip or not.")
        keyboard = [
            [
                InlineKeyboardButton("Yes", callback_data="yes"),
                InlineKeyboardButton("No", callback_data="no"),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        context.user_data["mp4_path"] = mp4_path
        context.user_data["next_command"] = "download video"
        logger.info(f"context data for continue download: {context}")
        await update.message.reply_text(
            "The video size exceeds the allowed limit. Do you want to receive the video in a zip format with sliced sizes?",
            reply_markup=reply_markup,
        )

    except Exception as e:
        print(f"An error occurred while handling large video: {e}")


async def create_sliced_video_in_each_zip_files(
    update: Update, mp4_path: str
) -> List[str]:
    try:
        sliced_zip = []
        # Create a zip file with sliced video parts
        logger.info("Process sending video in zip chunks.")
        CHUNK_SIZE_MB = SLICE_SIZE_MB
        total_chunks = (
            os.path.getsize(mp4_path) // (CHUNK_SIZE_MB * 1024 * 1024) + 1
        )
        # Create a temporary directory in the same directory as mp4_path to store video chunks
        temp_dir = os.path.join(os.path.dirname(mp4_path), "temp_video_chunks")
        os.makedirs(temp_dir, exist_ok=True)

        # Split the video into chunks
        with open(mp4_path, "rb") as video_file:
            for chunk_number in range(1, total_chunks + 1):
                chunk_file_path = os.path.join(
                    temp_dir, f"part{chunk_number}.mp4"
                )

                # Seek to the appropriate position in the video file
                video_file.seek(
                    (chunk_number - 1) * CHUNK_SIZE_MB * 1024 * 1024
                )

                # Read the chunk from the video file
                chunk = video_file.read(CHUNK_SIZE_MB * 1024 * 1024)
                if not chunk:
                    break

                # Write the chunk to the chunk file
                with open(chunk_file_path, "wb") as chunk_file:
                    chunk_file.write(chunk)

                # Create a zip file containing the current video chunk
                zip_file_path = os.path.join(
                    temp_dir, f"_part{chunk_number}.zip"
                )
                with zipfile.ZipFile(zip_file_path, "w") as zip_file:
                    zip_file.write(
                        chunk_file_path, os.path.basename(chunk_file_path)
                    )

                sliced_zip.append(zip_file_path)

                # Remove the temporary chunk file
                os.remove(chunk_file_path)

        return sliced_zip

    except Exception as err:
        logger.error(f"Error while sending video in slices: {err}")
        raise


async def youtube_dl_audio_internal(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    try:
        username = update.message.from_user.username

        if len(context.args) == 0:
            raise ValueError("Please provide a valid YouTube URL.")

        url = context.args[0]

        logger.info(
            f"{username} requested to download audio only from youtube. url: {url}"
        )
        mp4_path = _download_audio_only(url, username)

        if not os.path.exists(mp4_path):
            raise Exception("Error occured when downloading video.")

        # convert video file to audiofile using MoviePy
        mp3_path = mp4_path + ".mp3"
        mp3path = utils.convert_video_to_audio(
            mp4_path, mp3_path, raise_exception=True
        )

        if not mp3path:
            raise Exception(
                f"Download audio failed. Audio path does not exists."
            )

        logger.info("start sending audio")
        await update.message.reply_audio(
            audio=open(mp3path, "rb"),
            write_timeout=5 * 60,
            connect_timeout=5 * 60,
            pool_timeout=5 * 60,
            read_timeout=5 * 60,
        )
        logger.info("audio sent.")

    except Exception as err:
        logger.error(f"{err}")
        await update.message.reply_text(f"{err}")


async def youtube_btn_handle(update: Update, context: CallbackContext):
    try:
        logger.info(f"youtube button callback. context: {context}")
        query = update.callback_query
        user_choice = query.data
        STILL_UNDER_CONSTRUCTION = True

        if user_choice == "yes":
            await query.answer()
            logger.info("user choose yes.")
            next_command = context.user_data.get("next_command")
            if not next_command:
                return

            if STILL_UNDER_CONSTRUCTION:
                await query.edit_message_text(
                    text="Sorry, your video file size exceed. And slice featuter still under constructions.",
                    reply_markup=None,
                )
                return

            if next_command == "download video":
                mp4_path = context.user_data.get("mp4_path")
                if mp4_path:
                    await query.edit_message_text(
                        text="Here all zipped video.", reply_markup=None
                    )
                    zipped = await create_sliced_video_in_each_zip_files(
                        update, mp4_path
                    )

                    logger.info(f"preparing media for sends. media: {zipped}")
                    logger.info("send media.")
                    for zip in zipped:
                        await update.get_bot().send_document(
                            chat_id=update.effective_chat.id,
                            document=open(zip, "rb"),
                        )

                    for z in zipped:
                        os.remove(z)
                else:
                    await query.answer("Video path not found.")
                    await query.edit_message_text(
                        text="Sorry, video not found.", reply_markup=None
                    )

        elif user_choice == "no":
            logger.info("user choose no.")
            await query.answer("Okay, the video won't be sent.")
            await query.edit_message_text(
                text="Video will not sent.", reply_markup=None
            )

    except Exception as err:
        logger.error(f"{err}")


youtube_dl_video_service = CommandHandlerServices(
    "youtube_dl_video",
    CommandHandler("youtube_dl_video", youtube_dl_video_internal),
    "Download video from given youtube url",
)

youtube_dl_audio_service = CommandHandlerServices(
    "youtube_dl_audio",
    CommandHandler("youtube_dl_audio", youtube_dl_audio_internal),
    "Download audio from given youtube url",
)

youtube_btn_handler = CommandHandlerServices(
    "", CallbackQueryHandler(youtube_btn_handle), ""
)

YOUTUBE_SERVICE_COMMAND_HANDLER = [
    youtube_dl_video_service,
    youtube_btn_handler,
    youtube_dl_audio_service,
]
