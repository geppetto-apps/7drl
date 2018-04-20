import unittest
from components import Fighter

class TestStringMethods(unittest.TestCase):

    def test_level_is_one(self):
        f = Fighter()
        self.assertEqual(f.level(), 1)
        # HP_Base should be 30
        self.assertEqual(f.max_hp, 30)
        # Defense should be equal to level - 1
        self.assertEqual(f.defense, 0)
        # Power should be 3 + level
        self.assertEqual(f.power, 4)

    def test_level_two(self):
        f = Fighter(xp = 100)
        self.assertEqual(f.level(), 2)
        # HP_Base should be 30 + level * 10
        self.assertEqual(f.max_hp, 40)
        # Defense should be equal to level - 1
        self.assertEqual(f.defense, 1)
        # Power should be 3 + level
        self.assertEqual(f.power, 5)

    def test_level_three(self):
        f = Fighter(xp = 210)
        self.assertEqual(f.level(), 3)
        # HP_Base should be 30 + level * 10
        self.assertEqual(f.max_hp, 50)
        # Defense should be equal to level - 1
        self.assertEqual(f.defense, 2)
        # Power should be 3 + level
        self.assertEqual(f.power, 6)

    def test_level_four(self):
        f = Fighter(xp = 331)
        self.assertEqual(f.level(), 4)
        # HP_Base should be 30 + level * 10
        self.assertEqual(f.max_hp, 60)
        # Defense should be equal to level - 1
        self.assertEqual(f.defense, 3)
        # Power should be 3 + level
        self.assertEqual(f.power, 7)

    def test_override_hp_base(self):
        f = Fighter(hp_base = 10)
        self.assertEqual(f.max_hp, 10)
        f.grant_xp(100)
        self.assertEqual(f.max_hp, 20)

if __name__ == '__main__':
    unittest.main()
