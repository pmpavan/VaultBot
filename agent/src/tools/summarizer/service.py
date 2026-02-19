import os
import json
import logging
from typing import Optional
from openai import OpenAI

from .types import SummarizerRequest, SummarizerResponse
from prompts.summarizer import SummarizerSystemPrompt, SummarizerUserPrompt

logger = logging.getLogger(__name__)

class SummarizerService:
    def __init__(self):
        # Initialize OpenAI client (supports OpenRouter via base_url)
        api_key = os.environ.get("OPENROUTER_API_KEY") or os.environ.get("OPENAI_API_KEY")
        base_url = os.environ.get("OPENAI_BASE_URL", "https://openrouter.ai/api/v1")
        
        if not api_key:
            logger.warning("No API key found for SummarizerService. Summarization will be skipped.")
            self.client = None
        else:
            self.client = OpenAI(api_key=api_key, base_url=base_url)
            
        # Use gpt-4o-mini as specified in Story 2.7 AC
        self.model = os.environ.get("SUMMARIZER_MODEL", "openai/gpt-4o-mini")
        self.system_prompt = SummarizerSystemPrompt()
        self.user_prompt_template = SummarizerUserPrompt()

    def generate_summary(self, request: SummarizerRequest) -> Optional[str]:
        """
        Generate a concise 2-sentence summary of the content.
        Returns the summary string or None if it fails.
        """
        if not self.client:
            return None

        try:
            # Compile prompts
            system_content = self.system_prompt.compile()
            user_content = self.user_prompt_template.compile(
                title=request.title,
                description=request.description,
                vision_analysis=request.vision_analysis,
                transcript=request.transcript
            )

            # Check if we have anything to summarize
            if not any([request.title, request.description, request.vision_analysis, request.transcript]):
                 logger.warning("No metadata provided to SummarizerService. Skipping.")
                 return None

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_content},
                    {"role": "user", "content": user_content}
                ],
                response_format={"type": "json_object"},
                temperature=0.3 # Slightly more creative than normalizer but still strict
            )

            content = response.choices[0].message.content
            if not content:
                logger.error("Empty response from LLM summarizer")
                return None

            try:
                # Parse JSON response
                data = json.loads(content)
                summarized = SummarizerResponse(**data)
                return summarized.summary
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON from summarizer: {content}")
                return None
            except Exception as e:
                logger.error(f"Validation error in summarizer: {e}")
                # Fallback: if it's not JSON but looks like text, we might try to extract it,
                # but following the system pattern we expect structured output.
                return None

        except Exception as e:
            logger.error(f"Error calling summarizer LLM: {e}")
            return None
