import unittest
from unittest.mock import Mock
from gnggame import Arthur, Zombie, Plant, Eyeball, Platform

class TestZombie(unittest.TestCase):
    
    def setUp(self):
        self.arena = Mock()
        self.arena.size.return_value = (640, 480)
        self.arena.actors.return_value = []
        self.arena.is_dying.return_value = False

    def test_zombie_walk_right(self):
        zombie = Zombie((100, 200), 'right')
        zombie._state = 'walking'
        
        zombie._animation_counter = 9 
        
        initial_x = zombie.pos()[0]
        zombie.move(self.arena)
        
        self.assertTrue(zombie.pos()[0] > initial_x)

    def test_zombie_attack_arthur(self):
        zombie = Zombie((100, 200), 'right')
        zombie._state = 'walking'
        
        arthur = Mock(spec=Arthur)
        arthur.pos.return_value = (100, 200)
        arthur.size.return_value = (32, 32)
        
        self.arena.actors.return_value = [arthur]
        zombie.move(self.arena)
        arthur.hit.assert_called_with(self.arena)

class TestPlantAndProjectiles(unittest.TestCase):

    def setUp(self):
        self.arena = Mock()
        self.arena.size.return_value = (640, 480)
        self.arena.actors.return_value = []

    def test_plant_shoots(self):
        plant = Plant((100, 200), 'right')
        
        plant._state = "shooting"
        
        plant._animation_frame = 3 
        plant._animation_counter = 5 

        plant.move(self.arena)
        self.assertTrue(self.arena.spawn.called)

    def test_eyeball_hits_arthur(self):
        eyeball = Eyeball((100, 200), 'right')
        
        arthur = Mock(spec=Arthur)
        arthur.pos.return_value = (100, 200)
        arthur.size.return_value = (32, 32)
        
        self.arena.actors.return_value = [arthur]
        eyeball.move(self.arena)
        
        arthur.hit.assert_called_with(self.arena)
        self.arena.kill.assert_called_with(eyeball)
    
    def test_eyeball_hits_wall(self):
        eyeball = Eyeball((100, 200), 'right')
        platform = Mock(spec=Platform)
        platform.pos.return_value = (100, 200)
        platform.size.return_value = (50, 50)
        
        self.arena.actors.return_value = [platform]
        eyeball.move(self.arena)
        self.arena.kill.assert_called_with(eyeball)