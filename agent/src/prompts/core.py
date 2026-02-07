from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type
from pydantic import BaseModel, Field

class BasePrompt(BaseModel, ABC):
    """
    Base class for all prompts in the system.
    Enforces structure and JSON serialization.
    """
    name: str = Field(..., description="Unique name of the prompt")
    version: str = Field("1.0", description="Version of the prompt")
    description: str = Field(..., description="Description of what this prompt does")

    model_config = {
        "arbitrary_types_allowed": True
    }

    @abstractmethod
    def compile(self, **kwargs) -> str:
        """
        Compiles the prompt into a string.
        Must be implemented by subclasses.
        """
        pass

    def to_json(self) -> str:
        """
        Returns the prompt configuration as a JSON string.
        """
        return self.model_dump_json(indent=2)
    
    @classmethod
    def from_json(cls, json_str: str) -> "BasePrompt":
        """
        Loads a prompt from a JSON string.
        """
        return cls.model_validate_json(json_str)

class JsonSystemPrompt(BasePrompt):
    """
    A prompt that enforces JSON output from the LLM.
    The instruction itself is structured as a JSON object.
    """
    format_rules: List[str] = Field(
        default=[
            "Respond with valid JSON only.",
            "Do not include any markdown formatting like ```json ... ```.",
            "Do not include any conversational text before or after the JSON."
        ],
        description="Rules for JSON formatting"
    )

    def compile(self, **kwargs) -> str:
        # Return the entire object as a JSON string
        return self.model_dump_json(include={"format_rules"})

class VaultBotJsonSystemPrompt(JsonSystemPrompt):
    """
    The Base Character for VaultBot.
    Inherits JSON enforcement and adds Persona traits.
    """
    persona_role: str = Field(
        "VaultBot, a highly efficient automated analyst and memory prosthetic.",
        description="The rigid role definition"
    )
    persona_goal: str = Field(
        "Extract structured meaning from chaotic inputs (text, images, videos) to save the user's mental load.",
        description="The primary objective"
    )
    persona_rules: List[str] = Field(
        default=[
            "BE CONCISE: Use minimum words. Data > Fluff.",
            "BE OBJECTIVE: Describe exactly what you see/read.",
            "NO CHAT: Do not be conversational. Just output the JSON.",
            "TONE: Professional, slightly witty, competent."
        ],
        description="Core behavioral rules"
    )

    def compile(self, **kwargs) -> str:
        # Return the entire object (Persona + Format Rules) as a JSON string
        return self.model_dump_json(include={"persona_role", "persona_goal", "persona_rules", "format_rules"})
