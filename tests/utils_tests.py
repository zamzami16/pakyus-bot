import unittest
from unittest.mock import Mock
from src.utils import (
    get_commands,
    CommandHandlerServices,
    evaluate_arguments,
    html_to_markdown,
)


class Utils(unittest.TestCase):

    def test_get_commands(self):
        # Mock data for CommandHandlerServices
        mock_data = [
            CommandHandlerServices(
                name="hex2rgb", desc="convert hex to rgb", handler=Mock()
            ),
        ]

        # Call the function under test
        handlers, commands = get_commands(mock_data)

        # Assertions
        self.assertEqual(
            len(handlers), len(mock_data), "Number of handlers should match"
        )
        self.assertEqual(
            len(commands), len(mock_data), "Number of commands should match"
        )

        for i in range(len(mock_data)):
            self.assertEqual(
                handlers[i], mock_data[i].handler, "Handler should match"
            )
            self.assertEqual(
                commands[i]["command"],
                mock_data[i].name,
                "Command name should match",
            )
            self.assertEqual(
                commands[i]["description"],
                mock_data[i].description,
                "Command description should match",
            )

    def test_evaluate_arguments(self):
        args_str = '"SHOPEE EXPRESS" "YOUR AWB"'
        processed_args = evaluate_arguments(args_str)
        self.assertEqual(processed_args, ["SHOPEE EXPRESS", "YOUR AWB"])

    def test_evaluate_arguments_3(self):
        args_str = '"SHOPEE EXPRESS" "YOUR AWB" "AVB"'
        processed_args = evaluate_arguments(args_str)
        self.assertEqual(processed_args, ["SHOPEE EXPRESS", "YOUR AWB", "AVB"])

    def test_evaluate_arguments_empty(self):
        args_str = ""
        processed_args = evaluate_arguments(args_str)
        self.assertEqual(processed_args, [])

    def test_html_to_markdown(self):
        html_code = """
        <table class="table table-striped table-bordered table-hover">
          <tbody>
            <tr style="text-align: left">
              <th>Tanggal</th>
              <th>Keterangan</th>
            </tr>
            <tr>
              <td>28 Feb 2024 07:18</td>
              <td>Parcel menuju ke Hub (proses transit).</td>
            </tr>
            <tr>
              <td>27 Feb 2024 23:48</td>
              <td>Parcel sedang diproses di Hub </td>
            </tr>
            <!-- ... (other rows) ... -->
          </tbody>
        </table>
        """

        expected_markdown = (
            "| Tanggal            | Keterangan                              |\n"
            "| ------------------ | --------------------------------------- |\n"
            "| 28 Feb 2024 07:18  | Parcel menuju ke Hub (proses transit).   |\n"
            "| 27 Feb 2024 23:48  | Parcel sedang diproses di Hub             |"
        )

        markdown_table = html_to_markdown(html_code)
        self.assertEqual(markdown_table.strip(), expected_markdown.strip())


if __name__ == "__main__":
    unittest.main()
