import unittest

from server.skills import SkillSet, xp_for_level, level_for_xp


class SkillTests(unittest.TestCase):
    def test_xp_level_roundtrip(self) -> None:
        for level in range(1, 100):
            xp = xp_for_level(level)
            self.assertGreaterEqual(level_for_xp(xp), level - 1)
            self.assertLessEqual(level_for_xp(xp + 1), level)

    def test_skill_progression(self) -> None:
        skills = SkillSet()
        attack = skills["attack"]
        self.assertEqual(attack.level, 1)
        attack.add_xp(15_000)
        self.assertGreater(attack.level, 1)


if __name__ == "__main__":
    unittest.main()
