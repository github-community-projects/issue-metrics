"""Unit tests for the markdown_helpers module."""

import os
import unittest

from markdown_helpers import markdown_too_large_for_issue_body, split_markdown_file


class TestMarkdownHelpers(unittest.TestCase):
    """
    Unit tests for the markdown_helpers module.
    """

    def test_markdown_too_large_for_issue_body(self):
        """
        Test the markdown_too_large_for_issue_body function.
        """
        # Define a sample markdown file content
        max_char_count = 65535
        markdown_content = "a\n" * max_char_count

        # Write the markdown content to a temporary file
        with open("temp.md", "w", encoding="utf-8") as f:
            f.write(markdown_content)

        # Call the function with the temporary file
        result = markdown_too_large_for_issue_body("temp.md", max_char_count)

        # remove the temporary file
        os.remove("temp.md")

        # Assert that the function returns True
        self.assertTrue(result)

    def test_split_markdown_file(self):
        """
        Test the split_markdown_file function.
        """

        # Define a sample markdown file content with 4 times the maximum character count
        multiple_of_max = 4
        max_char_count = 65535
        repeated_content = "a\n"
        markdown_content = repeated_content * int(
            (max_char_count * multiple_of_max) / len(repeated_content)
        )

        # Write the markdown content to a temporary file
        with open("temp.md", "w", encoding="utf-8") as f:
            f.write(markdown_content)

        # Call the function with the temporary file
        split_markdown_file("temp.md", max_char_count)

        # Assert that the function creates two files
        self.assertTrue(os.path.exists("temp_0.md"))
        self.assertTrue(os.path.exists("temp_1.md"))
        self.assertTrue(os.path.exists("temp_2.md"))
        self.assertTrue(os.path.exists("temp_3.md"))

        # Assert that the all files have less than max characters
        for i in range(multiple_of_max):
            with open(f"temp_{i}.md", "r", encoding="utf-8") as f:
                self.assertLessEqual(len(f.read()), max_char_count)

        # remove the temporary files
        os.remove("temp.md")
        os.remove("temp_0.md")
        os.remove("temp_1.md")
        os.remove("temp_2.md")
        os.remove("temp_3.md")


if __name__ == "__main__":
    unittest.main()
