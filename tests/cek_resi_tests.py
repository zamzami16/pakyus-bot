import unittest
from unittest.mock import AsyncMock, patch
from src.expedition.cek_resi import (
    get_available_expeditions_text,
    get_html_track_courier_shipment,
    check_expedition_exists,
    EXPEDITION_SET_FUNCTION,
)
from src.exceptions import PakYusException


class TestYourFunctions(unittest.IsolatedAsyncioTestCase):
    async def test_get_available_expeditions_text(self):
        expected_text = "\#\# Here are the available expeditions:\n\n"
        for key in EXPEDITION_SET_FUNCTION:
            expected_text += f"\n\- **{key.capitalize()}**"

        result = get_available_expeditions_text()
        self.assertEqual(result, expected_text)

    def test_check_expedition_exists(self):
        existing_expedition = list(EXPEDITION_SET_FUNCTION.keys())[0]
        non_existing_expedition = "NonExistingExpedition"

        result_existing = check_expedition_exists(existing_expedition)
        result_non_existing = check_expedition_exists(non_existing_expedition)

        self.assertTrue(result_existing)
        self.assertFalse(result_non_existing)


if __name__ == "__main__":
    unittest.main()
