import unittest
from src.color_services import hex_to_rgb


class TestHexToRgb(unittest.TestCase):

    def test_hex_to_rgb(self):
        # Test cases
        test_cases = [
            {"input": "#FF0000", "expected_output": (255, 0, 0)},
            {"input": "#00FF00", "expected_output": (0, 255, 0)},
            {"input": "#0000FF", "expected_output": (0, 0, 255)},
            # Add more test cases as needed
        ]

        # Perform tests
        for test_case in test_cases:
            with self.subTest(test_case=test_case):
                result = hex_to_rgb(test_case["input"])
                self.assertEqual(
                    result,
                    test_case["expected_output"],
                    f"Failed for input: {test_case['input']}",
                )

    def test_hex_to_rgb_invalid_length(self):
        # Test case for invalid length
        with self.assertRaises(IndexError):
            hex_to_rgb("#12345")


if __name__ == "__main__":
    unittest.main()
