from typing import Dict, Any, List
from pydantic import Field
from tools.normalizer.types import NormalizerResponse
from .core import VaultBotJsonSystemPrompt

class NormalizerSystemPrompt(VaultBotJsonSystemPrompt):
    """
    System prompt for the Data Normalizer Agent.
    """
    name: str = "normalizer_system"
    description: str = "System instructions for Data Normalizer tasks."

    normalizer_instructions: List[str] = Field(
        default=[
            "Analyze the unstructured content metadata.",
            "Choose the BEST Category from the allowed Enum.",
            "Determine the Price Range based on context ($ to $$$$). Use null if not applicable.",
            "Generate 3-7 high-quality semantic tags.",
            "Do not hallucinate info not present in the input."
        ],
        description="Specific instructions for normalization"
    )

    output_schema: Dict[str, Any] = Field(
        default_factory=NormalizerResponse.model_json_schema,
        description="The JSON schema the output must adhere to"
    )

    def compile(self, **kwargs) -> str:
        """
        Compiles the prompt into a JSON string including persona, rules, instructions, and schema.
        """
        return self.model_dump_json(include={
            "persona_role",
            "persona_goal",
            "persona_rules",
            "format_rules",
            "normalizer_instructions",
            "output_schema"
        })
