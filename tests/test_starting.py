from unittest import TestCase
from manitobot.starting import shuffle_roles


class Test(TestCase):
    def test_shuffle_roles(self):
        roles = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j']
        shuffle_roles(roles)
        self.assertEquals(len(roles), 10)
        self.assertSetEqual(set(roles), {'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j'})
