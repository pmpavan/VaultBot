import os
import json
import logging
from typing import Optional
from openai import OpenAI

from .types import NormalizerRequest, NormalizerResponse
from agent.src.prompts.normalizer import NormalizerSystemPrompt

logger = logging.getLogger(__name__)

class NormalizerService:
    def __init__(self):
        # Initialize OpenAI client (supports OpenRouter via base_url)
        api_key = os.environ.get("OPENROUTER_API_KEY") or os.environ.get("OPENAI_API_KEY")
        base_url = os.environ.get("OPENAI_BASE_URL", "https://openrouter.ai/api/v1")
        
        if not api_key:
            logger.warning("No API key found for NormalizerService. Normalization will be skipped.")
            self.client = None
        else:
            self.client = OpenAI(api_key=api_key, base_url=base_url)
            
        self.model = os.environ.get("NORMALIZER_MODEL", "openai/gpt-4o-mini")
        self.system_prompt = NormalizerSystemPrompt()

    def normalize(self, request: NormalizerRequest) -> Optional[NormalizerResponse]:
        """
        Normalize content metadata into structured fields.
        Returns None if client is not configured or normalization fails.
        """
        if not self.client:
            return None

        try:
            # Construct user message
            user_content = f"Title: {request.title}\n"
            if request.description:
                user_content += f"Description: {request.description}\n"
            if request.raw_content:
                # Truncate raw content to avoid token limits, just in case
                user_content += f"Raw Content: {request.raw_content[:2000]}\n"
            user_content += f"URL: {request.source_url}"

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt.compile()},
                    {"role": "user", "content": user_content}
                ],
                response_format={"type": "json_object"},
                temperature=0.1
            )

            content = response.choices[0].message.content
            if not content:
                logger.error("Empty response from LLM normalizer")
                return None

            try:
                # Parse and validate with Pydantic
                data = json.loads(content)
                normalized = NormalizerResponse(**data)
                return normalized
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON from normalizer: {content}")
                return None
            except Exception as e:
                logger.error(f"Validation error in normalizer: {e}")
                return None

        except Exception as e:
            logger.error(f"Error calling normalizer LLM: {e}")
            return None
