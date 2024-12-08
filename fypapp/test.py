from django.test import TestCase
from .models import TestModel

class TestModelTests(TestCase):
    def test_create_test_model(self):
        test_obj = TestModel.objects.create(
            name="Test 1", 
            description="This is a test description"
        )
        self.assertEqual(test_obj.name, "Test 1")