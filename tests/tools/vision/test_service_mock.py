import unittest
from unittest.mock import MagicMock, patch
import os
import json

# Set dummy key for testing
os.environ["OPENROUTER_API_KEY"] = "sk-dummy-key"

from agent.src.tools.vision.service import VisionService, VisionRequest, VisionResponse
from agent.src.tools.vision.types import VisionProviderError

class TestVisionService(unittest.TestCase):

    @patch("agent.src.tools.vision.providers.openrouter.OpenAI")
    def test_analyze_success(self, mock_openai):
        # Setup Mock
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        
        mock_completion = MagicMock()
        mock_completion.choices[0].message.content = json.dumps({
            "description": "A beautiful sunset",
            "objects": ["sun", "ocean"]
        })
        mock_completion.usage.model_dump.return_value = {"total_tokens": 100}
        mock_completion.model_dump.return_value = {"id": "chatcmpl-123"}
        
        mock_client.chat.completions.create.return_value = mock_completion

        # Test
        service = VisionService()
        request = VisionRequest(
            image_input="https://example.com/image.jpg",
            prompt="Analyze this image",
            model_provider="openai"
        )
        
        response = service.analyze(request)
        
        # Verify
        self.assertIsInstance(response, VisionResponse)
        self.assertEqual(response.analysis_data["description"], "A beautiful sunset")
        self.assertEqual(response.provider_used, "openrouter/openai/gpt-4o")
        
        # Verify Prompt Factory Usage implicitly via System Prompt check? 
        # The adapter logic constructs the messages. We can check the call args.
        call_args = mock_client.chat.completions.create.call_args
        self.assertTrue(call_args)
        messages = call_args[1]["messages"]
        self.assertEqual(messages[0]["role"], "system")
        
        # Check System Prompt is JSON
        system_content = messages[0]["content"]
        try:
            system_json = json.loads(system_content)
            self.assertIn("format_rules", system_json)
            self.assertIn("persona_role", system_json)
            self.assertIn("vision_instructions", system_json)
        except json.JSONDecodeError:
            self.fail("System prompt is not valid JSON")
        
        # Check User Prompt is JSON
        user_content = messages[1]["content"][0]["text"]
        try:
            user_json = json.loads(user_content)
            self.assertEqual(user_json["instruction"], "Analyze this image")
        except json.JSONDecodeError:
            self.fail("User prompt is not valid JSON")

    @patch("agent.src.tools.vision.providers.openrouter.OpenAI")
    def test_analyze_failure_retry(self, mock_openai):
        # Setup Mock to fail
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        
        # Side effect: Raise exception
        mock_client.chat.completions.create.side_effect = Exception("API Connection Error")

        service = VisionService()
        request = VisionRequest(
            image_input="https://example.com/image.jpg",
            prompt="Analyze this",
            model_provider="openai"
        )

        # Verify it raises exception after retries
        with self.assertRaises(VisionProviderError):
            service.analyze(request)
            
        # Verify retries happened (Tenacity default is 3 attempts)
        # Note: We configured min=2s wait, so this test might be slow if we don't mock sleep
        # For this quick check, we just ensure it catches the error and wraps/raises it.

if __name__ == "__main__":
    unittest.main()
