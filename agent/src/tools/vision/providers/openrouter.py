import os
import json
from typing import Dict, Any, Optional
from openai import OpenAI
from ..types import VisionRequest, VisionResponse, VisionProviderError
from ...prompts import PromptFactory, VisionAnalyzePrompt, VisionSystemPrompt

class OpenRouterVisionAdapter:
    """
    Adapter for Vision tasks using OpenRouter API.
    Uses 'openai' SDK with OpenRouter base URL.
    """
    
    # Map friendly provider names to OpenRouter model IDs
    MODEL_MAP = {
        "openai": "openai/gpt-4o",
        "gemini": "google/gemini-pro-1.5" # Using pro 1.5 as standard vision capable model
    }

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY is not set.")
        
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=self.api_key
        )

    def analyze(self, request: VisionRequest) -> VisionResponse:
        """
        Sends an image analysis request to OpenRouter.
        """
        model_id = self.MODEL_MAP.get(request.model_provider)
        if not model_id:
            raise VisionProviderError(f"Unsupported provider: {request.model_provider}")

        # Construct System Prompt
        system_prompt = PromptFactory.create("vision_system")
        
        # Construct User Prompt
        # Use Factory to ensure JSON formatting via VisionAnalyzePrompt
        user_prompt = PromptFactory.create("vision_analyze", instruction=request.prompt)
        user_prompt_text = user_prompt.compile()
        
        # Prepare messages
        messages = [
            {"role": "system", "content": system_prompt.compile()},
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": user_prompt_text
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": request.image_input 
                        }
                    }
                ]
            }
        ]

        try:
            response = self.client.chat.completions.create(
                model=model_id,
                messages=messages,
                response_format={"type": "json_object"} # Enforce JSON mode
            )
            
            content = response.choices[0].message.content
            if not content:
                raise VisionProviderError("Empty response from OpenRouter")

            try:
                data = json.loads(content)
            except json.JSONDecodeError:
                 raise VisionProviderError(f"Invalid JSON response: {content}")

            return VisionResponse(
                analysis_data=data,
                provider_used=f"openrouter/{model_id}",
                usage_metadata=response.usage.model_dump() if response.usage else None,
                raw_response=response.model_dump()
            )

        except Exception as e:
            raise VisionProviderError(f"OpenRouter API call failed: {str(e)}") from e
