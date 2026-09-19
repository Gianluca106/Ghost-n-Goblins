import unittest
from unittest.mock import Mock
from gnggame import Arthur, Platform

class TestArthurMovement(unittest.TestCase):
    """Test parametrizzati per il movimento base di Arthur."""

    def setUp(self):
        self.arena = Mock()
        self.arena.size.return_value = (640, 480)
        self.arena.actors.return_value = []
        self.arena.is_dying.return_value = False
        self.arena.previous_keys.return_value = []

    def test_horizontal_movement(self):
        test_cases = [
            (100, "ArrowRight", 103),
            (100, "ArrowLeft", 97),
            (100, "Nothing", 100),
        ]
        for start_x, key, expected_x in test_cases:
            with self.subTest(key=key):
                arthur = Arthur((start_x, 200), self.arena)
                if key == "Nothing":
                    self.arena.current_keys.return_value = []
                else:
                    self.arena.current_keys.return_value = [key]
                arthur.move(self.arena)
                self.assertEqual(arthur.pos()[0], expected_x)

class TestArthurPhysics(unittest.TestCase):
    """Test fisica: gravità, salti e collisioni."""

    def setUp(self):
        self.arena = Mock()
        self.arena.size.return_value = (640, 480)
        self.arena.actors.return_value = []
        self.arena.is_dying.return_value = False
        self.arena.previous_keys.return_value = []
        self.arena.current_keys.return_value = []

    def test_gravity(self):
        arthur = Arthur((100, 100), self.arena)
        initial_y = arthur.pos()[1]
        arthur.move(self.arena)
        self.assertTrue(arthur.pos()[1] > initial_y)

    def test_jump(self):
        arthur = Arthur((100, 200), self.arena)
        arthur._on_ground = True
        arthur._jumps_remaining = 1
        self.arena.current_keys.return_value = ["ArrowUp"]
        arthur.move(self.arena)
        self.assertTrue(arthur.pos()[1] < 200)

    def test_landing_on_platform(self):
        arthur = Arthur((100, 168), self.arena)
        arthur._dy = 5
        
        platform = Mock(spec=Platform)
        platform.pos.return_value = (100, 200)
        platform.size.return_value = (100, 20)
        platform.is_semi_solid.return_value = False
        
        self.arena.actors.return_value = [platform]
        arthur.move(self.arena)
        
        self.assertEqual(arthur.pos()[1], 168)
        self.assertTrue(arthur._on_ground)