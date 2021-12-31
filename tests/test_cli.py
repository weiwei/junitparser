import unittest
from junitparser.cli import main, merge

class Test_Cli(unittest.TestCase):
    def test_main(self):
        result = main()
        self.assertEqual(result, 0)
