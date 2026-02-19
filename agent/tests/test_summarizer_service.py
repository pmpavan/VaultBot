import unittest
from unittest.mock import MagicMock, patch
import json
import os
import sys

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../src'))

from agent.src.tools.summarizer.service import SummarizerService
from agent.src.tools.summarizer.types import SummarizerRequest

class TestSummarizerService(unittest.TestCase):
    def setUp(self):
        self.service = SummarizerService()
        # Mock the OpenAI client
        self.service.client = MagicMock()

    def test_generate_summary_success(self):
        # Mock successful LLM response
        mock_response = MagicMock()
        mock_response.choices[0].message.content = '{"summary": "A high-end sushi restaurant in Kyoto called Blue Note. Known for live jazz and seasonal omakase."}'
        self.service.client.chat.completions.create.return_value = mock_response

        request = SummarizerRequest(
            title="Blue Note Sushi",
            description="High-end sushi in Kyoto with live jazz."
        )
        result = self.service.generate_summary(request)

        self.assertIsNotNone(result)
        self.assertEqual(result, "A high-end sushi restaurant in Kyoto called Blue Note. Known for live jazz and seasonal omakase.")

    def test_generate_summary_empty_input(self):
        # Should return None if no content is provided
        request = SummarizerRequest()
        result = self.service.generate_summary(request)
        self.assertIsNone(result)

    def test_generate_summary_json_error(self):
        # Mock invalid JSON response
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "Not a JSON"
        self.service.client.chat.completions.create.return_value = mock_response

        request = SummarizerRequest(title="Test")
        result = self.service.generate_summary(request)

        self.assertIsNone(result)

    def test_generate_summary_validation_error(self):
        # Mock valid JSON but missing 'summary' field
        mock_response = MagicMock()
        mock_response.choices[0].message.content = '{"wrong_field": "test"}'
        self.service.client.chat.completions.create.return_value = mock_response

        request = SummarizerRequest(title="Test")
        result = self.service.generate_summary(request)

        self.assertIsNone(result)

    def test_generate_summary_too_many_sentences(self):
        # Mock response with 3 sentences
        mock_response = MagicMock()
        mock_response.choices[0].message.content = '{"summary": "Sentence one. Sentence two. Sentence three."}'
        self.service.client.chat.completions.create.return_value = mock_response

        request = SummarizerRequest(title="Test")
        result = self.service.generate_summary(request)

        # Should be truncated to 2 sentences
        self.assertEqual(result, "Sentence one. Sentence two.")

if __name__ == '__main__':
    unittest.main()
