import unittest

from tidymd.export import render
from tidymd.fmt import format_text
from tidymd.lint import lint
from tidymd.stats import stats


class LintTest(unittest.TestCase):
    def rules(self, text, **kw):
        return [i.rule for i in lint(text, **kw)]

    def test_clean_file(self):
        self.assertEqual(self.rules("# Title\n\nSome text.\n"), [])

    def test_problems(self):
        text = "#Title\nbody  \n\n\n\tx\n" + "y" * 30
        self.assertEqual(sorted(self.rules(text, line_length=20)),
                         ["MD009", "MD010", "MD012", "MD013", "MD018", "MD047"])

    def test_code_blocks_are_skipped(self):
        self.assertEqual(self.rules("```\ntrailing  \n```\n"), [])


class FmtTest(unittest.TestCase):
    def test_format(self):
        self.assertEqual(format_text("#Title\ntext  \n\n\n\nmore\n\n"), "# Title\ntext\n\nmore\n")

    def test_idempotent(self):
        once = format_text("##  A\n\tb\n")
        self.assertEqual(format_text(once), once)


class StatsTest(unittest.TestCase):
    def test_counts(self):
        s = stats("# Head\n\nOne two [link](http://x).\n\n```\ncode\n```\n")
        self.assertEqual((s["headings"], s["links"], s["code_blocks"]), (1, 1, 1))
        self.assertEqual(s["reading_minutes"], 1)


class ExportTest(unittest.TestCase):
    def test_render(self):
        page = render("# Plan\n\nSome **bold** and `code`.\n\n- a\n- b\n")
        self.assertIn("<title>Plan</title>", page)
        self.assertIn("<h1>Plan</h1>", page)
        self.assertIn("<strong>bold</strong>", page)
        self.assertIn("<ul><li>a</li><li>b</li></ul>", page)

    def test_table(self):
        page = render("| a | b |\n|---|---|\n| 1 | 2 |\n")
        self.assertIn("<th>a</th><th>b</th>", page)
        self.assertIn("<td>1</td><td>2</td>", page)

    def test_escapes_html(self):
        self.assertIn("&lt;script&gt;", render("<script>\n"))


if __name__ == "__main__":
    unittest.main()
