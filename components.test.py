import unittest
from components import Fighter

class TestStringMethods(unittest.TestCase):
    def test_level_is_one(self):
        f = Fighter(hp = 100, defense = 10, power = 10)
        self.assertEqual(f.level(), 1)

    def test_level_two(self):
        f = Fighter(hp = 100, defense = 10, power = 10, xp = 100)
        self.assertEqual(f.level(), 2)

    def test_level_three(self):
        f = Fighter(hp = 100, defense = 10, power = 10, xp = 210)
        self.assertEqual(f.level(), 3)

    def test_level_four(self):
        f = Fighter(hp = 100, defense = 10, power = 10, xp = 331)
        self.assertEqual(f.level(), 4)

if __name__ == '__main__':
    unittest.main()
