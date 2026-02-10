import unittest
from unittest.mock import MagicMock, patch
from agent.src.tools.normalizer.service import NormalizerService
from agent.src.tools.normalizer.types import NormalizerRequest, NormalizerResponse, CategoryEnum, PriceRangeEnum

class TestNormalizerService(unittest.TestCase):
    def setUp(self):
        self.service = NormalizerService()
        # Mock the OpenAI client
        self.service.client = MagicMock()

    def test_normalize_success(self):
        # Mock successful LLM response
        mock_response = MagicMock()
        mock_response.choices[0].message.content = '''
        {
            "category": "Food",
            "price_range": "$$",
            "tags": ["Sushi", "Dinner", "Tokyo"]
        }
        '''
        self.service.client.chat.completions.create.return_value = mock_response

        request = NormalizerRequest(
            title="Sushi Place",
            source_url="http://example.com"
        )
        result = self.service.normalize(request)

        self.assertIsNotNone(result)
        self.assertEqual(result.category, CategoryEnum.FOOD)
        self.assertEqual(result.price_range, PriceRangeEnum.MODERATE)
        self.assertEqual(result.tags, ["Sushi", "Dinner", "Tokyo"])

    def test_normalize_json_error(self):
        # Mock invalid JSON response
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "Invalid JSON"
        self.service.client.chat.completions.create.return_value = mock_response

        request = NormalizerRequest(title="Test", source_url="http://example.com")
        result = self.service.normalize(request)

        self.assertIsNone(result)

    def test_normalize_validation_error(self):
        # Mock valid JSON but invalid schema (missing required field 'category')
        mock_response = MagicMock()
        mock_response.choices[0].message.content = '''
        {
            "price_range": "$$",
            "tags": ["Tag"]
        }
        '''
        self.service.client.chat.completions.create.return_value = mock_response

        request = NormalizerRequest(title="Test", source_url="http://example.com")
        result = self.service.normalize(request)

        self.assertIsNone(result)

if __name__ == '__main__':
    unittest.main()
