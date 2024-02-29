from playwright.async_api import async_playwright
from bs4 import BeautifulSoup, Tag, NavigableString
from typing import Tuple

import logging

from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from telegram.constants import ParseMode
from emoji import emojize
from src import utils

from src.command_handler_services import CommandHandlerServices
from src.constants import FOLDED_HANDS, SMILING_FACE
from src.exceptions import PakYusException
from markdownify import markdownify

logger = logging.getLogger(__name__)

EXPEDITION_SET_FUNCTION = {
    "JNE": "setExp('JNE');doCheckR()",
    "LION PARCEL": "setExp('LIONPARCEL');doCheckR()",
    "NINJA": "setExp('NINJA');doCheckR()",
    "ANTERAJA": "setExp('ANTERAJA');doCheckR()",
    "POS INDONESIA": "setExp('POS');doCheckR()",
    "SHOPEE EXPRESS": "setExp('SPX');doCheckR()",
    "CITYLINK EXPRESS": "setExp('CITYLINK');doCheckR()",
    "INDAH LOGISTIK CARGO": "setExp('INDAH');doCheckR()",
    "INDAH LOGISTIK CARGO 2": "(function(){ location.href='cek-resi-indah-cargo.php?noresi='+$('#noresi').val(); return false; })();",
    "SAP EXPRESS": "setExp('SAP');doCheckR()",
    "ZDEX ZALORA": "setExp('ZDEX');doCheckR()",
    "KERRY EXPRESS": "setExp('KERRY');doCheckR()",
    "SF EXPRESS": "setExp('SF');doCheckR()",
    "RCL RED CARPET LOGISTICS": "setExp('RCL');doCheckR()",
    "JET EXPRESS": "setExp('JETEXPRESS');doCheckR()",
    "QRIM EXPRESS": "setExp('QRIM');doCheckR()",
    "ARK XPRESS": "setExp('ARK');doCheckR()",
    "KGX PRESS": "setExp('KGX');doCheckR()",
    "REX INDONESIA": "setExp('REX');doCheckR()",
    "NSS EXPRESS": "setExp('NSS');doCheckR()",
    "STANDARD EXPRESS/LWE": "setExp('LWE');doCheckR()",
    "STANDARD EXPRESS/LWE 2": "(function(){ location.href='cek-resi-standard-express-lwe.php?noresi='+$('#noresi').val(); return false; })();",
    "KI8 EXPRESS": "(function(){ location.href='https://cekresi.com/cek/?kurir=KI&amp;noresi='+$('#noresi').val(); return false; })();",
    "OEXPRESS": "setExp('OEXPRESS');doCheckR()",
    "LUAR NEGERI/BEA CUKAI": "setExp('BEACUKAI');doCheckR()",
}


def get_available_expeditions_text():
    beautified_text = "\#\# Here are the available expeditions:\n\n"

    for key, val in EXPEDITION_SET_FUNCTION.items():
        beautified_text += f"\n\- **{key.capitalize()}**"

    return beautified_text


async def get_html_track_courier_shipment(
    awb_number: str, callback_expedition: str
) -> str:
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        context = await browser.new_context()
        page = await context.new_page()

        logger.info(
            f"get html cek resi requests: awb: {awb_number}. callback: {callback_expedition}"
        )

        try:
            await page.goto(f"https://cekresi.com/?noresi={awb_number}")
            await page.evaluate("dCek();")
            selexpid_selector = '#selexpid .hideContent:has-text("")'
            await page.wait_for_selector(selexpid_selector, timeout=10000)
            await page.evaluate(callback_expedition)
            table_selector = "#results .alert"
            await page.wait_for_selector(table_selector, timeout=10000)
            table_content = await page.content()
            return table_content

        except Exception as err:
            logger.error(f"{err}")
            raise PakYusException(
                "Error occured when requesting data from server"
            )

        finally:
            await context.close()


def check_expedition_exists(ekspedisi: str) -> bool:
    return ekspedisi.upper() in (key.upper() for key in EXPEDITION_SET_FUNCTION)


class CekResi:
    def __init__(self, awb: str, expedition_name: str) -> None:
        self._awb = awb
        self._expedition = expedition_name

    def get_expedition_name(self):
        return self._expedition

    def get_awb(self):
        return self._awb

    def set_awb(self, awb: str):
        self._awb = awb

    def set_expedition(self, expedition_name: str):
        self._expedition = expedition_name

    def get_status_alert(
        self, element: Tag | NavigableString
    ) -> Tuple[bool, str]:
        allert_success = element.find(class_="alert-success")
        if allert_success:
            inner_text = allert_success.get_text(strip=True)
            return True, inner_text

        allert_warning = element.find(class_="alert-warning")
        if allert_success:
            inner_text = allert_warning.get_text(strip=True)
            return False, inner_text

        return False, "Data Not Found."

    async def cek_resi(self) -> Tuple[bool, str]:
        if self._awb is None or self._expedition is None:
            raise PakYusException("Need AWB and expedition.")

        ekspedisi = self._expedition.upper().strip()
        ekspedisi = EXPEDITION_SET_FUNCTION.get(ekspedisi, None)

        if not ekspedisi:
            raise PakYusException("Ekspedisi tidak diketahui.")

        html = await get_html_track_courier_shipment(self._awb, ekspedisi)

        if not html:
            raise PakYusException("Error on get data resi.")

        soup = BeautifulSoup(html, "lxml")
        results_element = soup.find(id="results")

        isSuccess, msg_allert = self.get_status_alert(results_element)
        if not isSuccess:
            return False, msg_allert

        collapse_two_element = results_element.find(id="collapseTwo")
        table_element = collapse_two_element.find("table")
        if table_element:
            return True, str(table_element)

        return False, "Error occured while parsing data."


async def reply_list_expedition_exists(update: Update, first_line: str) -> None:
    if len(first_line) > 0:
        first_line = f"{first_line}\n\n"

    text = f"{first_line}{get_available_expeditions_text()}"
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN_V2)


async def cek_resi_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    try:
        logger.info(context.args)
        arguments = utils.evaluate_arguments(" ".join(context.args))
        if len(arguments) == 2:
            ekspedisi, awb = arguments
            cr = CekResi(awb=awb, expedition_name=ekspedisi)
            isSuccess, text = await cr.cek_resi()
            logger.info(f"html text: {text}")
            if isSuccess:
                markdown_text = markdownify(text)
                logger.info(f"markdownify: {markdown_text}")
                text = (
                    markdown_text.replace("|", "\|")
                    .replace("-", "\-")
                    .replace("(", "\(")
                    .replace(")", "\)")
                    .replace(".", "\.")
                )
                logger.info(f"markdownify: {text}")
                await update.message.reply_text(
                    text=text, parse_mode=ParseMode.MARKDOWN_V2
                )

            else:
                await update.message.reply_text(text=text)

        else:
            text = emojize(
                f"{FOLDED_HANDS} {FOLDED_HANDS} Accepted command is like:"
            )
            text += '\n\n/cek_resi "SHOPEE EXPRESS" "YOUR AWB"'
            await update.message.reply_text(text)

    except PakYusException as err:
        logger.error(f"{err}")
        await update.message.reply_text(f"Sorry, Error occured. {err}")

    except Exception as err:
        logger.error(f"{err}")
        await utils.send_default_error_message(update=update)


async def cek_resi_cek_ekspedisi_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    try:
        if len(context.args) > 0:
            ekspedisi = " ".join(context.args)
            isAvailable = check_expedition_exists(ekspedisi)
            if isAvailable:
                await update.message.reply_text(
                    emojize(f"Ekspedisi {ekspedisi} tersedia. :smiling_face:")
                )
            else:
                await reply_list_expedition_exists(
                    update=update,
                    first_line=emojize(
                        f"Sorry, Ekspedisi {ekspedisi} tidak tersedia. :folded_hand:"
                    ),
                )

        else:
            await reply_list_expedition_exists(update=update, first_line="")

    except Exception as err:
        logger.error(f"{err}")
        await utils.send_default_error_message(update=update)


cek_resi_ekspedisi_service = CommandHandlerServices(
    "cek_resi_cek_ekspedisi",
    CommandHandler("cek_resi_cek_ekspedisi", cek_resi_cek_ekspedisi_callback),
    "Cek ekspedisi tersedia",
)

cek_resi_service = CommandHandlerServices(
    "cek_resi",
    CommandHandler("cek_resi", cek_resi_callback),
    "Cek resi dari berbagai ekspedisi",
)

CEK_RESI_SERVICE_COMMAND_HANDLER = [
    cek_resi_ekspedisi_service,
    cek_resi_service,
]


if __name__ == "__main__":
    import asyncio

    print(get_available_expeditions_text())

    async def main():
        cr = CekResi("10008447322101", "ANTERAJA")
        # cr = CekResi("GATAU", "ANTERAJA")
        res = await cr.cek_resi()
        print(res)

    asyncio.run(main())
