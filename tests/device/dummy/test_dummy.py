import pytest
from unittest import TestCase


pytestmark = pytest.mark.device


class TestDummy(TestCase):

    def test_unlock_screen(self):
       self.assertTrue(True)